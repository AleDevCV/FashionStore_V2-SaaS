"""
=============================================================================
FASHIONSTORE - SERVICIO DE VESTIDOR VIRTUAL FOTOREALISTA CON IA (FASE 2)
Sistemas de Información II - UAGRM
-----------------------------------------------------------------------------
Pipeline híbrido fotorealista de Virtual Try-On:
  1. Decodificación y normalización de imagen de usuario (Base64 / Data URI).
  2. Resolución de prenda PNG transparente (Catálogo DB o URL externa con caché LRU).
  3. Detección de puntos de anclaje anatómicos (hombros, torso, cuello).
  4. Warping perspectivo y afín tridimensional adaptado a orientación corporal.
  5. Sombra suave de contacto (Drop Shadow por desenfoque Gaussiano).
  6. Ecualización ambiental de iluminación y color en espacio HSV.
  7. Refinamiento multimodal con Google Gemini Vision (gemini-3.1-flash-image / gemini-3.8-flash) y
     respaldo instantáneo al motor de warping local (Dual-Engine).
=============================================================================
"""

import base64
import logging
import os
import re
import tempfile
import threading
import time
from io import BytesIO
from typing import Any
import httpx
import numpy as np
from PIL import Image, ImageFilter
from fastapi import HTTPException, status
from decart import DecartClient
from google import genai
from google.genai import types

import cv2
from app.schemas.ia import MetadatosCalce, TryOnPeticion, TryOnRespuesta

logger = logging.getLogger(__name__)

# Caché en memoria para imágenes de catálogo (evita descargas de red redundantes) con sincronización de hilos
_GARMENT_CACHE: dict[str, np.ndarray] = {}
_CACHE_LOCK = threading.Lock()


def limpiar_base64(cadena_b64: str) -> bytes:
    """Extrae y decodifica los bytes reales de una imagen en Base64,

    removiendo prefijos comunes como 'data:image/...;base64,'.
    """
    if not cadena_b64 or not isinstance(cadena_b64, str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La imagen del usuario no fue proporcionada o no es una cadena válida",
        )

    if len(cadena_b64)>12_000_000:raise HTTPException(413,'La imagen supera el límite admitido.')
    # Eliminar posibles encabezados MIME
    if "," in cadena_b64:
        cadena_b64 = cadena_b64.split(",", 1)[1]

    # Limpiar saltos de línea o espacios en blanco
    cadena_b64 = re.sub(r"\s+", "", cadena_b64)

    try:
        datos_bytes = base64.b64decode(cadena_b64, validate=True)
        if len(datos_bytes) < 16:
            raise ValueError("Longitud insuficiente de datos binarios")
        from app.services.safe_images import validate_image
        validate_image(datos_bytes)
        return datos_bytes
    except Exception as e:
        logger.warning("Error decodificando imagen en Base64: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de imagen inválido o Base64 corrupto",
        ) from e


class TryOnService:
    """Servicio para el procesamiento del vestidor virtual fotorealista."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self._client: genai.Client | None = None
        self._decart_backup_active = False
        if self.api_key:
            try:
                self._client = genai.Client(
                    api_key=self.api_key,
                    http_options=types.HttpOptions(timeout=15),
                )
            except Exception as e:
                logger.warning("No fue posible inicializar genai.Client en TryOnService: %s", e)
                self._client = None

    def get_client(self) -> genai.Client | None:
        """Devuelve el cliente de Gemini o intenta instanciarlo con la clave actual."""
        if self._client is not None:
            return self._client
        api_key = self.api_key or os.getenv("GEMINI_API_KEY")
        if api_key:
            try:
                self._client = genai.Client(
                    api_key=api_key,
                    http_options=types.HttpOptions(timeout=15),
                )
                return self._client
            except Exception as e:
                logger.warning("Error al inicializar genai.Client en TryOn: %s", e)
                return None
        return None

    # -------------------------------------------------------------------------
    # 1. RESOLUCIÓN DE IMAGEN DE PRENDA
    # -------------------------------------------------------------------------

    def _resolver_prenda_imagen(
        self,
        cursor: Any,
        id_prenda: int | None,
        url_prenda: str | None,
        id_variante_prenda: int | None = None,
    ) -> tuple[np.ndarray, str, int | None]:
        """Obtiene la imagen RGBA de la prenda desde la base de datos o URL.

        Retorna:
            tuple (garment_rgba_np, nombre_prenda, resolved_id_prenda)
        """
        nombre_prenda = "Prenda de Colección"
        resolved_id = None
        target_url = None

        # Si se especificó id_variante_prenda pero no id_prenda, resolver desde catálogo PostgreSQL
        if id_prenda is None and id_variante_prenda is not None:
            if cursor is not None and hasattr(cursor, "execute"):
                cursor.execute(
                    """
                    SELECT vp.id_prenda, p.nombre
                    FROM variante_prenda vp
                    JOIN prenda p ON vp.id_prenda = p.id_prenda
                    WHERE vp.id_variante_prenda = %s
                    LIMIT 1;
                    """,
                    (id_variante_prenda,),
                )
                fila_var = cursor.fetchone()
                if not fila_var:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Variante de prenda con ID {id_variante_prenda} no encontrada en el catálogo",
                    )
                if isinstance(fila_var, dict):
                    id_prenda = fila_var.get("id_prenda")
                    nombre_prenda = fila_var.get("nombre") or nombre_prenda
                elif isinstance(fila_var, (list, tuple)):
                    id_prenda = fila_var[0]
                    if len(fila_var) > 1 and fila_var[1]:
                        nombre_prenda = fila_var[1]
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No se dispone de conexión a base de datos para resolver la variante de prenda",
                )

        if id_prenda is not None:
            resolved_id = id_prenda
            if cursor is not None and hasattr(cursor, "execute"):
                cursor.execute(
                    """
                    SELECT p.nombre, ip.url_imagen
                    FROM prenda p
                    LEFT JOIN imagen_prenda ip ON p.id_prenda = ip.id_prenda
                    WHERE p.id_prenda = %s
                    ORDER BY ip.es_principal DESC NULLS LAST, ip.id_imagen ASC
                    LIMIT 1;
                    """,
                    (id_prenda,),
                )
                fila = cursor.fetchone()
                if not fila:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Prenda con ID {id_prenda} no encontrada en el catálogo",
                    )
                if isinstance(fila, dict):
                    nombre_prenda = fila.get("nombre") or nombre_prenda
                    target_url = fila.get("url_imagen")
                elif isinstance(fila, (list, tuple)):
                    nombre_prenda = fila[0] or nombre_prenda
                    target_url = fila[1] if len(fila) > 1 else None

                if not target_url:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"La prenda '{nombre_prenda}' (ID {id_prenda}) no tiene imágenes registradas",
                    )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No se dispone de conexión a base de datos para resolver la prenda por ID",
                )
        elif url_prenda:
            target_url = url_prenda.strip()
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Debe proporcionar id_prenda o url_prenda para procesar el Try-On",
            )

        # Cargar la imagen desde URL o Base64
        garment_rgba = self._obtener_prenda_rgba(target_url)
        return garment_rgba, nombre_prenda, resolved_id

    def _obtener_prenda_rgba(self, url_o_b64: str) -> np.ndarray:
        """Carga y decodifica la imagen de la prenda asegurando canal alfa (RGBA)."""
        # Si ya está en caché (acceso sincronizado para evitar condiciones de carrera)
        with _CACHE_LOCK:
            if url_o_b64 in _GARMENT_CACHE:
                return _GARMENT_CACHE[url_o_b64].copy()

        # Si es una URL externa (HTTP/HTTPS)
        if url_o_b64.startswith(("http://","https://","/api/catalogo/imagenes/")):
            from app.services.safe_images import fetch_image
            raw_bytes,_=fetch_image(url_o_b64)

        else:
            # Viene en Data URI o Base64 directo (con o sin prefijo)
            raw_bytes = limpiar_base64(url_o_b64)

        # Decodificar con OpenCV conservando canal alfa
        nparr = np.frombuffer(raw_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)

        if img is None:
            # Intentar fallback con PIL
            try:
                pil_img = Image.open(BytesIO(raw_bytes)).convert("RGBA")
                img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGBA2BGRA)
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El archivo de la prenda no es una imagen válida",
                ) from e

        if img is None or img.size == 0 or img.shape[0] == 0 or img.shape[1] == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El archivo de la prenda no es una imagen válida o tiene dimensiones nulas",
            )

        # Asegurar 4 canales (BGRA)
        if img.ndim == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGRA)
        elif img.shape[2] == 3:
            # Si no tiene canal alfa, generar transparencia a partir del fondo blanco/claro
            b, g, r = cv2.split(img)
            # Fondo blanco típico de catálogo (> 240 en los 3 canales)
            alpha = np.where((b > 240) & (g > 240) & (r > 240), 0, 255).astype(np.uint8)
            img = cv2.merge([b, g, r, alpha])
        elif img.shape[2] == 4:
            # Detectar canal alfa corrupto (todos los píxeles en 0 / totalmente transparente)
            alpha = img[:, :, 3]
            if np.all(alpha == 0):
                logger.warning("Canal alfa de la prenda completamente transparente (corrupto). Sintetizando desde fondo.")
                b, g, r = img[:, :, 0], img[:, :, 1], img[:, :, 2]
                alpha_sintetico = np.where((b > 240) & (g > 240) & (r > 240), 0, 255).astype(np.uint8)
                img[:, :, 3] = alpha_sintetico

        # Guardar en caché si es una URL externa (con límite de tamaño sincronizado para evitar fugas y carreras)
        if url_o_b64.startswith("http://") or url_o_b64.startswith("https://"):
            with _CACHE_LOCK:
                if len(_GARMENT_CACHE) >= 100:
                    primer_clave = next(iter(_GARMENT_CACHE), None)
                    if primer_clave is not None:
                        _GARMENT_CACHE.pop(primer_clave, None)
                _GARMENT_CACHE[url_o_b64] = img.copy()

        return img

    # -------------------------------------------------------------------------
    # 2. DETECCIÓN ANATÓMICA DE PUNTOS DE ANCLAJE
    # -------------------------------------------------------------------------

    def _estimar_anclajes_anatomicos(
        self,
        user_bgr: np.ndarray,
        ajuste_holgura: float = 1.0,
    ) -> dict[str, Any]:
        """Detecta hombros, cuello y proporciones del torso del usuario.

        Utiliza segmentación cromática YCrCb/HSV para contornos corporales
        y heurística anatómica áurea proporcional para máxima robustez.
        """
        h_img, w_img = user_bgr.shape[:2]

        # 1. Segmentación en espacio YCrCb para detección de tonos de piel/silueta
        ycrcb = cv2.cvtColor(user_bgr, cv2.COLOR_BGR2YCrCb)
        # Rango típico de piel en YCrCb
        skin_mask = cv2.inRange(
            ycrcb,
            np.array([0, 133, 77], dtype=np.uint8),
            np.array([255, 173, 127], dtype=np.uint8),
        )

        # Enfoque en la mitad superior de la imagen (donde está el rostro y hombros)
        h_corte = max(1, int(h_img * 0.65))
        mitad_superior = skin_mask[:h_corte, :]
        if mitad_superior.shape[0] >= 7 and mitad_superior.shape[1] >= 7:
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
            mitad_superior = cv2.morphologyEx(mitad_superior, cv2.MORPH_CLOSE, kernel)
            contours, _ = cv2.findContours(mitad_superior, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        else:
            contours = []

        cabeza_detectada = False
        hx, hy, hw, hh = 0, 0, 0, 0

        if contours:
            # Filtrar por área mínima relevante (> 1.5% del área superior)
            area_min = (w_img * h_img * 0.65) * 0.015
            grandes = [c for c in contours if cv2.contourArea(c) > area_min]
            if grandes:
                # El contorno más representativo
                c_max = max(grandes, key=cv2.contourArea)
                hx, hy, hw, hh = cv2.boundingRect(c_max)
                # Validar proporciones razonables de rostro/cabeza (no debe ocupar toda la imagen)
                if 0.6 <= (hh / max(hw, 1)) <= 2.2 and hw <= (w_img * 0.65) and hh <= (h_img * 0.50):
                    cabeza_detectada = True

        if cabeza_detectada:
            centro_x = hx + hw // 2
            # Hombros inician debajo del cuello
            hombro_y = min(int(hy + hh * 1.12), int(h_img * 0.38))
            # El ancho de hombros estándar es aprox 2.6 a 3.0 veces el ancho del rostro
            ancho_hombros = int(hw * 2.80 * ajuste_holgura)
            alto_torso = int(hh * 3.3)
        else:
            # Modelo anatómico áureo / fotométrico por defecto (Golden Ratio)
            centro_x = w_img // 2
            hombro_y = int(h_img * 0.22)
            ancho_hombros = int(w_img * 0.54 * ajuste_holgura)
            alto_torso = int(h_img * 0.52)

        # Delimitar dentro del encuadre
        ancho_hombros = max(2, max(int(w_img * 0.30), min(ancho_hombros, int(w_img * 0.95))))
        hombro_izq_x = max(0, centro_x - ancho_hombros // 2)
        hombro_der_x = min(w_img - 1, centro_x + ancho_hombros // 2)
        if hombro_der_x <= hombro_izq_x:
            hombro_der_x = min(w_img - 1, hombro_izq_x + 1)
        waist_y = min(h_img - 1, max(hombro_y + 1, hombro_y + alto_torso))

        return {
            "centro_x": int(centro_x),
            "hombro_y": int(hombro_y),
            "hombro_izq_x": int(hombro_izq_x),
            "hombro_der_x": int(hombro_der_x),
            "ancho_hombros": int(ancho_hombros),
            "alto_torso": int(alto_torso),
            "cintura_y": int(waist_y),
            "cabeza_detectada": cabeza_detectada,
        }

    # -------------------------------------------------------------------------
    # 3. WARPING PERSPECTIVO Y AFÍN TRIDIMENSIONAL
    # -------------------------------------------------------------------------

    def _warping_perspectiva(
        self,
        garment_rgba: np.ndarray,
        user_shape: tuple[int, int],
        anclaje: dict[str, Any],
        ajuste_holgura: float = 1.0,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Aplica transformación homográfica tridimensional adaptando la prenda

        al cuadrilátero anatómico del torso del usuario.
        """
        user_h, user_w = user_shape
        gh, gw = garment_rgba.shape[:2]

        centro_x = anclaje["centro_x"]
        hombro_y = anclaje["hombro_y"]
        ancho_hombros = anclaje["ancho_hombros"]
        waist_y = anclaje["cintura_y"]

        # Geometría del torso: hombros más anchos, cintura con ligera convergencia (88%)
        ancho_cintura = int(ancho_hombros * 0.88 * ajuste_holgura)
        hombro_izq = (max(0, centro_x - ancho_hombros // 2), hombro_y)
        hombro_der = (min(user_w - 1, centro_x + ancho_hombros // 2), hombro_y)
        cintura_der = (min(user_w - 1, centro_x + ancho_cintura // 2), waist_y)
        cintura_izq = (max(0, centro_x - ancho_cintura // 2), waist_y)

        # Cuadrilátero origen (prenda plana) y destino (torso tridimensional)
        src_pts = np.float32([[0, 0], [gw, 0], [gw, gh], [0, gh]])
        dst_pts = np.float32([hombro_izq, hombro_der, cintura_der, cintura_izq])

        matriz_perspectiva = cv2.getPerspectiveTransform(src_pts, dst_pts)
        warped = cv2.warpPerspective(
            garment_rgba,
            matriz_perspectiva,
            (user_w, user_h),
            flags=cv2.INTER_LANCZOS4,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=(0, 0, 0, 0),
        )

        warped_bgr = warped[:, :, :3]
        warped_alpha = warped[:, :, 3]
        return warped_bgr, warped_alpha

    # -------------------------------------------------------------------------
    # 4. SOMBRA SUAVE DE CONTACTO (DROP SHADOW)
    # -------------------------------------------------------------------------

    def _aplicar_drop_shadow(
        self,
        user_bgr: np.ndarray,
        warped_alpha: np.ndarray,
        dx: int = 3,
        dy: int = 9,
        opacidad_sombra: float = 0.32,
    ) -> np.ndarray:
        """Genera una sombra de contacto suave proyectada sobre el cuerpo

        mediante traslación y desenfoque gaussiano del canal alfa.
        """
        h, w = user_bgr.shape[:2]

        # Matriz de traslación para la sombra
        m_traslacion = np.float32([[1, 0, dx], [0, 1, dy]])
        sombra_desplazada = cv2.warpAffine(
            warped_alpha,
            m_traslacion,
            (w, h),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=0,
        )

        # Desenfoque gaussiano suave
        sombra_blur = cv2.GaussianBlur(sombra_desplazada, (21, 21), 6.5)

        # Excluir sombra debajo de la propia prenda para que no oscurezca el borde interno
        sombra_efectiva = cv2.subtract(sombra_blur, warped_alpha)

        # Multiplicación tonal sobre el usuario
        sombra_factor = 1.0 - (sombra_efectiva.astype(np.float32) / 255.0) * opacidad_sombra
        sombra_factor = np.expand_dims(sombra_factor, axis=-1)

        user_con_sombra = (user_bgr.astype(np.float32) * sombra_factor).astype(np.uint8)
        return user_con_sombra

    # -------------------------------------------------------------------------
    # 5. ECUALIZACIÓN AMBIENTAL DE COLOR E ILUMINACIÓN (HSV)
    # -------------------------------------------------------------------------

    def _ecualizar_luz_y_fusion(
        self,
        user_bgr: np.ndarray,
        warped_bgr: np.ndarray,
        warped_alpha: np.ndarray,
        anclaje: dict[str, Any],
    ) -> tuple[np.ndarray, dict[str, Any]]:
        """Ecualiza la luminancia (V) y saturación (S) de la prenda según la

        iluminación ambiental del usuario y realiza fusión alfa con suavizado de bordes.
        """
        # Muestreo ambiental del torso del usuario
        user_hsv = cv2.cvtColor(user_bgr, cv2.COLOR_BGR2HSV).astype(np.float32)
        hy = anclaje["hombro_y"]
        wy = anclaje["cintura_y"]
        hx1 = anclaje["hombro_izq_x"]
        hx2 = anclaje["hombro_der_x"]

        torso_roi = user_hsv[hy:wy, hx1:hx2]
        if torso_roi.size > 0:
            mean_v_user = float(np.mean(torso_roi[:, :, 2]))
            mean_s_user = float(np.mean(torso_roi[:, :, 1]))
        else:
            mean_v_user = float(np.mean(user_hsv[:, :, 2]))
            mean_s_user = float(np.mean(user_hsv[:, :, 1]))

        # Muestreo de la prenda en píxeles no transparentes
        garment_hsv = cv2.cvtColor(warped_bgr, cv2.COLOR_BGR2HSV).astype(np.float32)
        mask_prenda = warped_alpha > 30

        if np.any(mask_prenda):
            mean_v_garment = float(np.mean(garment_hsv[mask_prenda, 2]))
            mean_s_garment = float(np.mean(garment_hsv[mask_prenda, 1]))
        else:
            mean_v_garment = 128.0
            mean_s_garment = 128.0

        # Ratios acotados para evitar sobreexposición o lavado de color
        ratio_v = np.clip(mean_v_user / (mean_v_garment + 1e-5), 0.78, 1.25)
        ratio_s = np.clip((mean_s_user / (mean_s_garment + 1e-5)) ** 0.5, 0.82, 1.18)

        garment_hsv[:, :, 2] = np.clip(garment_hsv[:, :, 2] * ratio_v, 0, 255)
        garment_hsv[:, :, 1] = np.clip(garment_hsv[:, :, 1] * ratio_s, 0, 255)

        garment_ecualizada_bgr = cv2.cvtColor(garment_hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

        # Suavizado de bordes (Feathering) en la máscara alfa para eliminar escalonamiento
        feathered_alpha = cv2.GaussianBlur(warped_alpha, (5, 5), 1.2).astype(np.float32) / 255.0
        feathered_alpha = np.expand_dims(feathered_alpha, axis=-1)

        # Composición final
        resultado_bgr = (
            garment_ecualizada_bgr.astype(np.float32) * feathered_alpha
            + user_bgr.astype(np.float32) * (1.0 - feathered_alpha)
        ).astype(np.uint8)

        metricas_luz = {
            "luminancia_usuario_v": round(mean_v_user, 1),
            "luminancia_prenda_v": round(mean_v_garment, 1),
            "ajuste_v_ratio": round(float(ratio_v), 3),
            "ajuste_s_ratio": round(float(ratio_s), 3),
        }
        return resultado_bgr, metricas_luz

    # -------------------------------------------------------------------------
    # 6. GENERACIÓN Y EDICIÓN VISUAL MULTIMODAL CON GOOGLE GEMINI
    # -------------------------------------------------------------------------

    def _extraer_imagen_bytes_de_respuesta(self, response: Any) -> bytes | None:
        """Extrae bytes binarios de imagen de la respuesta del SDK google-genai."""
        if response is None:
            return None

        # 1. response.parts
        try:
            parts = getattr(response, "parts", None)
            if parts:
                for part in parts:
                    inline = getattr(part, "inline_data", None)
                    if inline and getattr(inline, "data", None):
                        d = inline.data
                        if isinstance(d, str):
                            try:
                                return base64.b64decode(d)
                            except Exception:
                                pass
                        elif isinstance(d, bytes) and len(d) > 0:
                            return d
                    if hasattr(part, "as_image"):
                        try:
                            pil_img = part.as_image()
                            if pil_img:
                                buf = BytesIO()
                                pil_img.save(buf, format="JPEG")
                                return buf.getvalue()
                        except Exception:
                            pass
        except Exception:
            pass

        # 2. response.candidates[].content.parts[]
        try:
            candidates = getattr(response, "candidates", None)
            if candidates:
                for cand in candidates:
                    content = getattr(cand, "content", None)
                    cand_parts = getattr(content, "parts", None) if content else None
                    if cand_parts:
                        for part in cand_parts:
                            inline = getattr(part, "inline_data", None)
                            if inline and getattr(inline, "data", None):
                                d = inline.data
                                if isinstance(d, str):
                                    try:
                                        return base64.b64decode(d)
                                    except Exception:
                                        pass
                                elif isinstance(d, bytes) and len(d) > 0:
                                    return d
                            if hasattr(part, "as_image"):
                                try:
                                    pil_img = part.as_image()
                                    if pil_img:
                                        buf = BytesIO()
                                        pil_img.save(buf, format="JPEG")
                                        return buf.getvalue()
                                except Exception:
                                    pass
        except Exception:
            pass

        # 3. response.output_image (convenience property en SDK)
        try:
            output_image = getattr(response, "output_image", None)
            if output_image:
                img_bytes = getattr(output_image, "image_bytes", None)
                if isinstance(img_bytes, bytes) and len(img_bytes) > 0:
                    return img_bytes
                d = getattr(output_image, "data", None)
                if isinstance(d, str):
                    try:
                        return base64.b64decode(d)
                    except Exception:
                        pass
                elif isinstance(d, bytes) and len(d) > 0:
                    return d
        except Exception:
            pass

        # 4. response.generated_images (Imagen API)
        try:
            generated_images = getattr(response, "generated_images", None)
            if generated_images:
                for gen_img in generated_images:
                    img_obj = getattr(gen_img, "image", None)
                    if img_obj and hasattr(img_obj, "image_bytes") and img_obj.image_bytes:
                        return img_obj.image_bytes
        except Exception:
            pass

        return None

    def _generar_con_gemini_multimodal(
        self,
        user_jpeg_bytes: bytes,
        garment_rgba: np.ndarray,
        nombre_prenda: str,
    ) -> tuple[bytes | None, str | None, bool]:
        """Invoca Google Gemini mediante el SDK oficial google-genai para generar

        la composición visual fotorealista de la persona vistiendo la prenda.
        Retorna:
            (imagen_bytes_o_none, mensaje_texto_o_none, es_fallback)
        """
        client = self.get_client()
        if not client:
            return None, None, True

        try:
            # Codificar prenda con canal alfa a PNG transparente
            ok_garment, buf_garment = cv2.imencode(".png", garment_rgba)
            if not ok_garment:
                return None, None, True
            garment_png_bytes = buf_garment.tobytes()

            part_user = types.Part.from_bytes(
                data=user_jpeg_bytes,
                mime_type="image/jpeg",
            )
            part_garment = types.Part.from_bytes(
                data=garment_png_bytes,
                mime_type="image/png",
            )

            prompt = (
                f"Virtual Try-On fotorealista para FashionStore: "
                f"Adapta la prenda '{nombre_prenda}' (imagen 2 con transparencia recortada) "
                f"sobre el cuerpo de la persona en la fotografía (imagen 1). "
                f"Instrucciones de adaptación fotorealista: "
                f"1. Ajuste anatómico natural y ceñido al torso, cuello, hombros y cintura según la complexión y postura. "
                f"2. Caída natural del tejido, drapeado textil orgánico, pliegues y arrugas realistas de costura. "
                f"3. Sombras de contacto suaves e integración lumínica con el entorno y tono de piel. "
                f"4. Preservar intactos el rostro, cabello, cuello, extremidades y fondo original de la persona."
            )

            model_name = os.getenv("GEMINI_TRYON_MODEL", "gemini-3.1-flash-image")

            config = types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                http_options=types.HttpOptions(timeout=15),
            )

            response = client.models.generate_content(
                model=model_name,
                contents=[part_user, part_garment, prompt],
                config=config,
            )

            # Extraer bytes de imagen de la respuesta
            img_bytes = self._extraer_imagen_bytes_de_respuesta(response)
            if img_bytes and len(img_bytes) > 64:
                try:
                    pil_check = Image.open(BytesIO(img_bytes))
                    pil_check.verify()
                    texto_resp = None
                    try:
                        texto_resp = getattr(response, "text", None)
                    except Exception:
                        pass
                    return img_bytes, texto_resp, False
                except Exception as ex_ver:
                    logger.warning("Bytes devueltos por Gemini no son una imagen válida: %s", ex_ver)

            # Si no devolvió imagen válida: verificar si devolvió texto
            texto = None
            try:
                texto = getattr(response, "text", None)
            except Exception:
                texto = None

            # Detectar rechazos explícitos, bloqueos de seguridad o errores devueltos como texto
            palabras_negativas = [
                "unable", "cannot", "no puedo", "no es posible", "safety",
                "policy", "bloquead", "rechazad", "fallo", "falló", "no se pudo",
                "error", "failed", "violation", "violación"
            ]
            if texto and any(neg in str(texto).lower() for neg in palabras_negativas):
                logger.warning("Gemini retornó un rechazo o política de seguridad: %s. Activando fallback OpenCV.", texto)
                return None, None, True

            # Distinguir entre evaluación estilística exitosa (legacy mock) y negativa/error
            if texto and ("calce" in str(texto).lower() or "hombro" in str(texto).lower() or "silueta" in str(texto).lower() or "combinación" in str(texto).lower()):
                return None, str(texto).strip(), False

            logger.warning("Gemini no retornó imagen generada ni contenido válido. Activando fallback OpenCV.")
            return None, None, True

        except Exception as e:
            logger.warning(
                "Excepción o cuota agotada (429) en generación visual con Gemini: %s. Fallback automático a OpenCV.",
                e,
            )
            return None, None, True

    def _refinar_con_gemini_vision(
        self,
        imagen_jpeg_bytes: bytes,
        nombre_prenda: str,
    ) -> tuple[str, bool]:
        """Método de compatibilidad con análisis de vestidor virtual."""
        client = self.get_client()
        if not client:
            return (
                f"Composición fotorealista adaptada con precisión anatómica para {nombre_prenda}.",
                True,
            )

        try:
            part_imagen = types.Part.from_bytes(
                data=imagen_jpeg_bytes,
                mime_type="image/jpeg",
            )
            prompt = (
                f"Eres el asesor de vestidor virtual de alta costura de FashionStore. "
                f"Analiza la composición fotográfica generada de la prenda '{nombre_prenda}' sobre el usuario. "
                f"Proporciona en exactamente 2 oraciones elegantes: "
                f"1) Evaluación del calce y caída en hombros y silueta. "
                f"2) Consejo de combinación y ocasión ideal."
            )

            response = client.models.generate_content(
                model=os.getenv("GEMINI_VISION_MODEL", "gemini-3.8-flash"),
                contents=[part_imagen, prompt],
                config=types.GenerateContentConfig(
                    http_options=types.HttpOptions(timeout=10),
                ),
            )
            if response and response.text:
                return response.text.strip(), False

            return (
                f"Composición fotorealista adaptada con precisión anatómica para {nombre_prenda}.",
                True,
            )
        except Exception as e:
            logger.warning("Falla o timeout en refinamiento con Gemini Vision: %s. Activando fallback.", e)
            return (
                f"Composición fotorealista generada mediante warping anatómico y ecualización lumínica HSV para {nombre_prenda}.",
                True,
            )

    # -------------------------------------------------------------------------
    # MOTOR DE IA PRINCIPAL: IDM-VTON (REPLICATE DIFFUSION MODEL)
    # -------------------------------------------------------------------------

    @staticmethod
    def _es_error_creditos_decart(error: Exception) -> bool:
        """Reconoce falta de saldo sin confundirla con errores de red o autenticacion."""
        datos = getattr(error, "data", None)
        codigo_http = datos.get("status") if isinstance(datos, dict) else None
        mensaje = str(error).casefold()
        return str(codigo_http) == "402" or any(
            marca in mensaje for marca in (
                "insufficient_credits",
                "insufficient credits",
                "not enough credits",
                "out of credits",
                "credit balance",
                "no credits",
            )
        )

    async def create_realtime_token(self, use_backup: bool = False) -> dict:
        """Crea un token efimero; usa la segunda cuenta si la primera se queda sin saldo."""
        principal = (os.getenv("DECART_API_KEY") or "").strip()
        respaldo = (os.getenv("DECART_API_KEY_BACKUP") or "").strip()
        if not principal and not respaldo:
            logger.error("No hay claves Decart configuradas para Realtime VTON")
            raise HTTPException(status_code=503, detail="El probador IA no esta disponible temporalmente.")

        usar_respaldo = use_backup or self._decart_backup_active or not principal
        if usar_respaldo:
            if not respaldo:
                raise HTTPException(status_code=503, detail="El probador IA no esta disponible temporalmente.")
            candidatos = [("respaldo", respaldo)]
        else:
            candidatos = [("principal", principal)]

        for nombre, clave in candidatos:
            try:
                async with DecartClient(api_key=clave) as client:
                    token = await client.tokens.create(
                        expires_in=600,
                        allowed_models=["lucy-vton-latest"],
                    )
                return {
                    "apiKey": token.api_key,
                    "expiresAt": token.expires_at,
                    "usandoRespaldo": nombre == "respaldo",
                }
            except Exception as error:
                if nombre == "principal" and respaldo and self._es_error_creditos_decart(error):
                    logger.warning("La cuenta Decart principal no tiene creditos; activando respaldo")
                    self._decart_backup_active = True
                    return await self.create_realtime_token(use_backup=True)
                logger.error("No se pudo crear token Decart con cuenta %s (%s)", nombre, type(error).__name__)
                raise HTTPException(
                    status_code=503,
                    detail="El probador IA no esta disponible temporalmente.",
                ) from error

    def _generar_con_replicate_idm_vton(
        self,
        user_jpeg_bytes: bytes,
        garment_rgba: np.ndarray,
        nombre_prenda: str,
        categoria: str = "upper_body",
    ) -> tuple[bytes | None, str | None, bool]:
        """Invoca el modelo de difusión IDM-VTON alojado en Replicate (cuuupid/idm-vton)

        para componer fotorealistamente la persona con la prenda.
        Requiere la variable de entorno REPLICATE_API_TOKEN.
        Retorna:
            (imagen_bytes_o_none, mensaje_texto_o_none, es_fallback)
        """
        replicate_token = (os.getenv("REPLICATE_API_TOKEN") or "").strip()
        if not replicate_token:
            logger.warning("REPLICATE_API_TOKEN no configurado: IDM-VTON no disponible. Activando fallback.")
            return None, None, True

        try:
            # Codificar la prenda con canal alfa a PNG transparente
            ok_garment, buf_garment = cv2.imencode(".png", garment_rgba)
            if not ok_garment:
                return None, None, True

            garment_b64 = "data:image/png;base64," + base64.b64encode(buf_garment.tobytes()).decode("utf-8")
            person_b64 = "data:image/jpeg;base64," + base64.b64encode(user_jpeg_bytes).decode("utf-8")

            # Normalizar categoría según lo que espera IDM-VTON ("upper_body", "lower_body", "dresses")
            cat_lower = (categoria or "upper_body").lower()
            if "vestido" in cat_lower or "dress" in cat_lower:
                vton_category = "dresses"
            elif any(k in cat_lower for k in ["pantalon", "short", "falda", "lower"]):
                vton_category = "lower_body"
            else:
                vton_category = "upper_body"

            headers = {
                "Authorization": f"Bearer {replicate_token}",
                "Content-Type": "application/json",
                "Prefer": "wait=60",
            }

            payload = {
                "version": "0513734a452173b8173e907e3a59d19a36266e55b48528559432bd21c7d7e985",
                "input": {
                    "human_img": person_b64,
                    "garm_img": garment_b64,
                    "garment_des": nombre_prenda or "Clothing garment",
                    "category": vton_category,
                    "crop": False,
                    "steps": 30,
                    "seed": 42,
                },
            }

            logger.info("Enviando predicción de Virtual Try-On a Replicate (cuuupid/idm-vton)...")
            with httpx.Client(timeout=120.0) as http_client:
                resp = http_client.post(
                    "https://api.replicate.com/v1/predictions",
                    headers=headers,
                    json=payload,
                )
                if resp.status_code not in (200, 201):
                    logger.warning(
                        "Replicate API devolvió HTTP %s: %s. Activando fallback.",
                        resp.status_code,
                        resp.text[:300],
                    )
                    return None, None, True

                pred = resp.json()
                poll_url = pred.get("urls", {}).get("get")
                estado = pred.get("status")

                # Si aún está procesando, hacer polling
                max_polls = 40
                polls = 0
                while estado in ("starting", "processing") and poll_url and polls < max_polls:
                    time.sleep(2.5)
                    polls += 1
                    poll_resp = http_client.get(poll_url, headers=headers)
                    if poll_resp.status_code == 200:
                        pred = poll_resp.json()
                        estado = pred.get("status")
                    else:
                        break

                if estado != "succeeded":
                    logger.warning(
                        "Predicción Replicate IDM-VTON finalizó con estado: %s. Error: %s. Activando fallback.",
                        estado,
                        pred.get("error"),
                    )
                    return None, None, True

                output_url = pred.get("output")
                if not output_url:
                    logger.warning("Replicate IDM-VTON no retornó output URL. Activando fallback.")
                    return None, None, True

                img_resp = http_client.get(output_url, timeout=30.0)
                if img_resp.status_code != 200:
                    logger.warning("Error descargando imagen resultado de Replicate: %s", img_resp.status_code)
                    return None, None, True

                img_bytes = img_resp.content
                if not img_bytes or len(img_bytes) < 128:
                    logger.warning("Bytes devueltos por Replicate vacíos o corruptos.")
                    return None, None, True

                # Validar integridad
                try:
                    pil_check = Image.open(BytesIO(img_bytes))
                    pil_check.verify()
                except Exception as ex_ver:
                    logger.warning("Imagen devuelta por Replicate corrupta: %s", ex_ver)
                    return None, None, True

                mensaje = (
                    f"Composición fotorealista generada exitosamente con IDM-VTON (IA de Difusión) "
                    f"para {nombre_prenda}."
                )
                return img_bytes, mensaje, False

        except Exception as e:
            logger.warning("Excepción en llamada a Replicate IDM-VTON: %s. Activando fallback.", e)
            return None, None, True

    # -------------------------------------------------------------------------
    # MOTOR DE IA ALTERNATIVO: FASHN VTON v1.5 (HUGGING FACE SPACES / ZEROGPU)
    # -------------------------------------------------------------------------

    def _generar_con_fashn_vton(
        self,
        user_jpeg_bytes: bytes,
        garment_rgba: np.ndarray,
        nombre_prenda: str,
    ) -> tuple[bytes | None, str | None, bool]:
        """Invoca el Space de Hugging Face 'fashn-ai/fashn-vton-1.5' (motor de

        difusión FASHN VTON v1.5) para componer fotorealistamente la persona
        con la prenda.
        Requiere la variable de entorno HF_TOKEN (cuenta gratuita, cuota
        ZeroGPU limitada a ~5 minutos diarios).
        Retorna:
            (imagen_bytes_o_none, mensaje_texto_o_none, es_fallback)
        """
        hf_token = (os.getenv("HF_TOKEN") or "").strip()
        if not hf_token:
            logger.warning(
                "HF_TOKEN no configurado: FASHN VTON no disponible. Activando fallback."
            )
            return None, None, True

        # Importación diferida: si la imagen Docker no trae gradio_client, el
        # servicio no debe romperse; simplemente se cae al motor de respaldo.
        try:
            from gradio_client import Client, handle_file
        except Exception as e:
            logger.warning(
                "gradio_client no está disponible para FASHN VTON: %s. Activando fallback.", e
            )
            return None, None, True

        ruta_persona: str | None = None
        ruta_prenda: str | None = None
        try:
            # Codificar la prenda con canal alfa a PNG transparente
            ok_garment, buf_garment = cv2.imencode(".png", garment_rgba)
            if not ok_garment:
                return None, None, True

            # El Space solo acepta rutas de archivo: materializar ambos insumos
            # en disco temporal. Se limpian siempre en el bloque finally.
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp_persona:
                tmp_persona.write(user_jpeg_bytes)
                ruta_persona = tmp_persona.name

            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_prenda:
                tmp_prenda.write(buf_garment.tobytes())
                ruta_prenda = tmp_prenda.name

            # Timeout holgado: en ZeroGPU el encolado + inferencia tarda ~20-60 s
            client = Client(
                "fashn-ai/fashn-vton-1.5",
                token=hf_token,
                verbose=False,
                httpx_kwargs={"timeout": 120.0},
            )

            resultado = client.predict(
                person_image=handle_file(ruta_persona),
                garment_image=handle_file(ruta_prenda),
                category="tops",              # default seguro (prendas superiores)
                garment_photo_type="flat-lay",
                num_timesteps=30,             # reducido de 50 a 30 por latencia
                guidance_scale=1.5,
                seed=42,
                segmentation_free=True,       # sin máscara, totalmente automático
                api_name="/try_on",
            )

            # El retorno puede variar según la versión de gradio_client: cadena
            # con la ruta descargada, diccionario {'path': ...} o lista con uno.
            ruta_resultado: str | None = None
            if isinstance(resultado, str):
                ruta_resultado = resultado
            elif isinstance(resultado, dict):
                ruta_resultado = resultado.get("path")
            elif isinstance(resultado, (list, tuple)) and resultado:
                primero = resultado[0]
                if isinstance(primero, str):
                    ruta_resultado = primero
                elif isinstance(primero, dict):
                    ruta_resultado = primero.get("path")

            if not ruta_resultado or not os.path.exists(ruta_resultado):
                logger.warning(
                    "FASHN VTON no devolvió una ruta de imagen válida: %s", resultado
                )
                return None, None, True

            with open(ruta_resultado, "rb") as archivo_resultado:
                img_bytes = archivo_resultado.read()

            if not img_bytes or len(img_bytes) <= 64:
                logger.warning("FASHN VTON devolvió una imagen vacía o demasiado pequeña.")
                return None, None, True

            # Validar integridad de la imagen generada antes de entregarla
            try:
                pil_check = Image.open(BytesIO(img_bytes))
                pil_check.verify()
            except Exception as ex_ver:
                logger.warning(
                    "Bytes devueltos por FASHN VTON no son una imagen válida: %s", ex_ver
                )
                return None, None, True

            texto = (
                f"Composición fotorealista generada exitosamente con FASHN VTON v1.5 "
                f"(IA de difusión) para {nombre_prenda}."
            )
            return img_bytes, texto, False

        except Exception as e:
            logger.warning(
                "Excepción, cuota ZeroGPU agotada o timeout en generación visual con FASHN VTON: %s. "
                "Activando fallback.",
                e,
            )
            return None, None, True
        finally:
            # Limpieza garantizada de los archivos temporales de entrada
            for ruta in (ruta_persona, ruta_prenda):
                if ruta:
                    try:
                        os.unlink(ruta)
                    except Exception:
                        pass

    # -------------------------------------------------------------------------
    # MÉTODO PRINCIPAL: PROCESAR VESTIDOR VIRTUAL
    # -------------------------------------------------------------------------

    def procesar_tryon(
        self,
        cursor: Any,
        peticion: TryOnPeticion,
    ) -> TryOnRespuesta:
        """Ejecuta el pipeline integral del vestidor virtual fotorealista."""
        inicio_tiempo = time.perf_counter()

        # 1. Ingestión y normalización de la imagen del usuario con soporte EXIF
        user_bytes = limpiar_base64(peticion.foto_usuario)
        try:
            from PIL import ImageOps
            pil_img = Image.open(BytesIO(user_bytes))
            pil_img = ImageOps.exif_transpose(pil_img)
            pil_img = pil_img.convert("RGB")
            user_bgr = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        except Exception:
            nparr_user = np.frombuffer(user_bytes, np.uint8)
            user_bgr = cv2.imdecode(nparr_user, cv2.IMREAD_COLOR)

        if user_bgr is None or user_bgr.size == 0 or user_bgr.shape[0] == 0 or user_bgr.shape[1] == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se pudo decodificar la imagen del usuario",
            )

        # Redimensionar si la resolución es masiva para mantener latencia contenida
        max_dim = 1200
        uh, uw = user_bgr.shape[:2]
        if max(uh, uw) > max_dim:
            escala = max_dim / float(max(uh, uw))
            user_bgr = cv2.resize(
                user_bgr,
                (int(uw * escala), int(uh * escala)),
                interpolation=cv2.INTER_AREA,
            )

        # Preparar versión JPEG optimizada del usuario para envío a Gemini
        ok_usr, buf_usr = cv2.imencode(".jpg", user_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
        user_jpeg_bytes = buf_usr.tobytes() if ok_usr else user_bytes

        # 2. Resolución de imagen de prenda desde catálogo DB o URL
        garment_rgba, nombre_prenda, resolved_id = self._resolver_prenda_imagen(
            cursor=cursor,
            id_prenda=peticion.id_prenda,
            url_prenda=peticion.url_prenda,
            id_variante_prenda=peticion.id_variante_prenda,
        )

        # Acotar resolución de prenda si es masiva para controlar latencia y memoria
        gh, gw = garment_rgba.shape[:2]
        if max(gh, gw) > max_dim:
            escala_g = max_dim / float(max(gh, gw))
            garment_rgba = cv2.resize(
                garment_rgba,
                (int(gw * escala_g), int(gh * escala_g)),
                interpolation=cv2.INTER_AREA,
            )

        ajuste_holgura = float(peticion.ajuste_holgura or 1.0)

        # 3. Estimación anatómica de puntos de anclaje (hombros, cuello, torso)
        anclaje = self._estimar_anclajes_anatomicos(user_bgr, ajuste_holgura=ajuste_holgura)

        # 4. Pipeline local OpenCV (Homografía + Drop Shadow + Ecualización HSV)
        # Se ejecuta como base y como motor de fallback instantáneo
        warped_bgr, warped_alpha = self._warping_perspectiva(
            garment_rgba=garment_rgba,
            user_shape=user_bgr.shape[:2],
            anclaje=anclaje,
            ajuste_holgura=ajuste_holgura,
        )

        user_con_sombra = self._aplicar_drop_shadow(
            user_bgr=user_bgr,
            warped_alpha=warped_alpha,
            dx=3,
            dy=8,
            opacidad_sombra=0.32,
        )

        resultado_opencv_bgr, metricas_luz = self._ecualizar_luz_y_fusion(
            user_bgr=user_con_sombra,
            warped_bgr=warped_bgr,
            warped_alpha=warped_alpha,
            anclaje=anclaje,
        )

        ok_local, buffer_local = cv2.imencode(".jpg", resultado_opencv_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
        if not ok_local:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al codificar la imagen resultante local",
            )
        imagen_local_b64 = "data:image/jpeg;base64," + base64.b64encode(buffer_local.tobytes()).decode("utf-8")

        # 5. Generación visual con Google Gemini o conmutación resiliente a OpenCV
        imagen_resultado_b64 = imagen_local_b64
        metodo = "warping_hsv_local"
        metodo_usado = "opencv_homography_warp"
        es_fallback = False
        es_generativo = False
        mensaje = f"Composición fotorealista generada exitosamente para {nombre_prenda}."

        if peticion.usar_ia_generativa:
            # Motor de IA configurable por entorno: replicate | huggingface / fashn | gemini | cascade
            engine = os.getenv("TRYON_ENGINE", "replicate").strip().lower()
            if engine in ("huggingface", "hf"):
                engine = "fashn"
            elif engine not in ("replicate", "gemini", "fashn", "cascade"):
                logger.warning(
                    "TRYON_ENGINE='%s' no reconocido. Se asume 'replicate'.", engine
                )
                engine = "replicate"

            ia_img_bytes: bytes | None = None
            ia_texto: str | None = None
            ia_fallback = True
            motor_efectivo: str | None = None

            if engine == "replicate":
                ia_img_bytes, ia_texto, ia_fallback = self._generar_con_replicate_idm_vton(
                    user_jpeg_bytes=user_jpeg_bytes,
                    garment_rgba=garment_rgba,
                    nombre_prenda=nombre_prenda,
                )
                motor_efectivo = "replicate"
            elif engine == "fashn":
                ia_img_bytes, ia_texto, ia_fallback = self._generar_con_fashn_vton(
                    user_jpeg_bytes=user_jpeg_bytes,
                    garment_rgba=garment_rgba,
                    nombre_prenda=nombre_prenda,
                )
                motor_efectivo = "fashn"
            elif engine == "gemini":
                ia_img_bytes, ia_texto, ia_fallback = self._generar_con_gemini_multimodal(
                    user_jpeg_bytes=user_jpeg_bytes,
                    garment_rgba=garment_rgba,
                    nombre_prenda=nombre_prenda,
                )
                motor_efectivo = "gemini"
            else:
                # Cascade: primero Replicate IDM-VTON, si falla se intenta FASHN (HF),
                # luego Gemini y finalmente el motor local OpenCV.
                ia_img_bytes, ia_texto, ia_fallback = self._generar_con_replicate_idm_vton(
                    user_jpeg_bytes=user_jpeg_bytes,
                    garment_rgba=garment_rgba,
                    nombre_prenda=nombre_prenda,
                )
                motor_efectivo = "replicate"

                if ia_fallback:
                    logger.info(
                        "Replicate IDM-VTON no disponible (TRYON_ENGINE=cascade). Intentando FASHN VTON (Hugging Face)."
                    )
                    ia_img_bytes, ia_texto, ia_fallback = self._generar_con_fashn_vton(
                        user_jpeg_bytes=user_jpeg_bytes,
                        garment_rgba=garment_rgba,
                        nombre_prenda=nombre_prenda,
                    )
                    motor_efectivo = "fashn"

                if ia_fallback:
                    logger.info(
                        "FASHN VTON no disponible (TRYON_ENGINE=cascade). Intentando Gemini multimodal."
                    )
                    ia_img_bytes, ia_texto, ia_fallback = self._generar_con_gemini_multimodal(
                        user_jpeg_bytes=user_jpeg_bytes,
                        garment_rgba=garment_rgba,
                        nombre_prenda=nombre_prenda,
                    )
                    motor_efectivo = "gemini"

            if not ia_fallback and ia_img_bytes:
                # La IA generó exitosamente la imagen fotorealista (Replicate, FASHN o Gemini)
                # Normalizar a JPEG estándar para garantizar máxima compatibilidad con clientes y esquemas
                try:
                    pil_check = Image.open(BytesIO(ia_img_bytes))
                    if pil_check.format != "JPEG":
                        buf_jpg = BytesIO()
                        pil_check.convert("RGB").save(buf_jpg, format="JPEG", quality=92)
                        ia_img_bytes = buf_jpg.getvalue()
                except Exception:
                    pass
                imagen_resultado_b64 = "data:image/jpeg;base64," + base64.b64encode(ia_img_bytes).decode("utf-8")
                if motor_efectivo == "replicate":
                    metodo = "replicate_idm_vton"
                    metodo_usado = "replicate_idm_vton"
                elif motor_efectivo == "fashn":
                    metodo = "fashn_vton_ai"
                    metodo_usado = "fashn_vton_ai"
                else:
                    metodo = "gemini_multimodal_tryon"
                    metodo_usado = "gemini_multimodal_tryon"
                es_fallback = False
                es_generativo = True
                mensaje = (
                    ia_texto
                    if ia_texto
                    else f"Composición fotorealista generada exitosamente con IA para {nombre_prenda}."
                )
            elif not ia_fallback and ia_texto:
                # Caso de evaluación estilística / mock sobre composición local OpenCV
                imagen_resultado_b64 = imagen_local_b64
                metodo = "gemini_vision"
                metodo_usado = "opencv_homography_warp"
                es_fallback = False
                es_generativo = False
                mensaje = ia_texto
            else:
                # Fallback automático e instantáneo a OpenCV ante cuota agotada, timeout, error o falta de imagen
                imagen_resultado_b64 = imagen_local_b64
                metodo = "warping_hsv_local"
                metodo_usado = "opencv_homography_warp"
                es_fallback = True
                es_generativo = False
                mensaje = f"Composición fotorealista generada mediante motor local OpenCV (fallback) para {nombre_prenda}."
        else:
            # Petición explícita sin IA generativa: motor local directo
            imagen_resultado_b64 = imagen_local_b64
            metodo = "warping_hsv_local"
            metodo_usado = "opencv_homography_warp"
            es_fallback = False
            es_generativo = False
            mensaje = f"Composición fotorealista generada exitosamente para {nombre_prenda}."

        tiempo_total_ms = round((time.perf_counter() - inicio_tiempo) * 1000, 2)

        metadatos = MetadatosCalce(
            metodo=metodo,
            metodo_usado=metodo_usado,
            anclaje_torso={
                "centro_x": anclaje["centro_x"],
                "hombro_y": anclaje["hombro_y"],
                "ancho_hombros": anclaje["ancho_hombros"],
                "alto_torso": anclaje["alto_torso"],
                "cabeza_detectada": anclaje["cabeza_detectada"],
            },
            ajuste_luz=metricas_luz,
            prenda_id=resolved_id,
            es_fallback=es_fallback,
            tiempo_procesamiento_ms=tiempo_total_ms,
        )

        return TryOnRespuesta(
            estado="exito",
            imagen_resultado=imagen_resultado_b64,
            imagen_resultado_b64=imagen_resultado_b64,
            metodo_usado=metodo_usado,
            tiempo_procesamiento_ms=tiempo_total_ms,
            metadatos_calce=metadatos,
            mensaje=mensaje,
            es_generativo=es_generativo,
        )


# Instancia singleton del servicio para inyección en routers
tryon_service = TryOnService()
