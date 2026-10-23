"""
=============================================================================
FASHIONSTORE - SERVICIO CENTRAL DE INTELIGENCIA ARTIFICIAL (CU22, CU23, CU25)
Sistemas de Información II - UAGRM
-----------------------------------------------------------------------------
Integra modelos de lenguaje Google Gemini mediante el SDK
oficial `google-genai` para:
  - CU22: Asistente y Recomendador Virtual de Outfits con estricta validación
          anti-alucinación contra existencias reales en PostgreSQL y fallback.
  - CU23: Consultas Analíticas Ejecutivas por Voz y Reportes PDF con fpdf2.
  - CU25: Registro inmutable de cada interacción en la tabla `bitacora`.
=============================================================================
"""

import base64
import json
import logging
import os
import re
from typing import Any
from datetime import datetime

from fpdf import FPDF
from google import genai
from google.genai import types

from app.schemas.ia import (
    AnaliticaVozPeticion,
    AnaliticaVozRespuesta,
    ParametrosAnalitica,
    PrendaRecomendada,
    RecomendacionIAPeticion,
    RecomendacionIARespuesta,
    ResultadoFila,
)
from app.services.bitacora_service import (
    ACCION_IA_ANALITICA_VOZ,
    ACCION_IA_RECOMENDACION,
    registrar_bitacora,
)

logger = logging.getLogger("fashionstore.ia")


class ExecutiveReportPDF(FPDF):
    """Generador de reportes analíticos ejecutivos en formato PDF para CU23."""

    def header(self):
        self.set_font("Helvetica", "B", 15)
        self.set_text_color(18, 24, 38)
        self.cell(0, 8, "FASHIONSTORE - REPORTE ANALÍTICO EJECUTIVO", new_x="LMARGIN", new_y="NEXT", align="C")
        self.set_font("Helvetica", "I", 9)
        self.set_text_color(100, 100, 100)
        self.cell(0, 5, "Consultas Inteligentes Generativas por Voz (CU23) | Módulo IA", new_x="LMARGIN", new_y="NEXT", align="C")
        self.ln(4)
        self.set_draw_color(210, 215, 225)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(140, 140, 140)
        self.cell(0, 10, f"Página {self.page_no()}/{{nb}} - FashionStore Retail Inteligente", align="C")


class GeminiAIService:
    """Servicio centralizado para la orquestación de capacidades de IA Generativa."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.client: genai.Client | None = None
        if self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.warning("No fue posible inicializar genai.Client al arranque: %s", e)
                self.client = None

    def get_client(self) -> genai.Client | None:
        """Devuelve el cliente de Gemini o intenta instanciarlo con la clave actual."""
        if self.client is not None:
            return self.client
        api_key = self.api_key or os.getenv("GEMINI_API_KEY")
        if api_key:
            try:
                self.client = genai.Client(api_key=api_key)
                return self.client
            except Exception as e:
                logger.warning("Error al inicializar genai.Client: %s", e)
                return None
        return None

    # =========================================================================
    # CU22: ASISTENTE Y RECOMENDADOR VIRTUAL DE PRENDAS / OUTFITS
    # =========================================================================

    def _obtener_catalogo_activo_con_stock(self, cursor: Any) -> list[dict[str, Any]]:
        """Consulta en PostgreSQL las prendas activas que cuentan con existencias reales (stock > 0)."""
        cursor.execute(
            """
            SELECT 
                p.id_prenda,
                p.nombre,
                p.descripcion,
                p.genero,
                p.precio_base AS precio,
                c.nombre AS categoria,
                t.nombre AS temporada,
                (
                    SELECT i.url_imagen FROM imagen_prenda i
                    WHERE i.id_prenda = p.id_prenda
                    ORDER BY i.es_principal DESC, i.id_imagen
                    LIMIT 1
                ) AS imagen_url,
                SUM(inv.stock)::int AS stock_total,
                STRING_AGG(DISTINCT tal.nombre, ', ') AS tallas_disponibles,
                STRING_AGG(DISTINCT variant_color_label(vp.id_variante_prenda), ', ') AS colores_disponibles
            FROM prenda p
            JOIN categoria c ON p.id_categoria = c.id_categoria
            LEFT JOIN temporada t ON p.id_temporada = t.id_temporada
            JOIN variante_prenda vp ON p.id_prenda = vp.id_prenda
            JOIN inventario inv ON vp.id_variante_prenda = inv.id_variante_prenda
            LEFT JOIN talla tal ON vp.id_talla = tal.id_talla
            LEFT JOIN color col ON vp.id_color = col.id_color
            WHERE p.estado = 'Activo' AND inv.stock > 0
            GROUP BY p.id_prenda, p.nombre, p.descripcion, p.genero, p.precio_base, c.nombre, t.nombre
            HAVING SUM(inv.stock) > 0
            ORDER BY stock_total DESC, p.id_prenda ASC;
            """
        )
        return cursor.fetchall()

    def _ejecutar_fallback_recomendacion(
        self,
        catalogo_db: list[dict[str, Any]],
        limite: int,
        razon: str = "",
    ) -> tuple[str, list[PrendaRecomendada]]:
        """Genera una respuesta de recomendación basada en los artículos más populares/disponibles."""
        logger.info("Activando mecanismo de fallback para recomendaciones. Razón: %s", razon)
        prendas_fallback: list[PrendaRecomendada] = []
        seleccion = catalogo_db[:limite]
        for prenda in seleccion:
            prendas_fallback.append(
                PrendaRecomendada(
                    id_prenda=prenda["id_prenda"],
                    nombre=prenda["nombre"],
                    precio=float(prenda["precio"]),
                    stock_total=int(prenda["stock_total"]),
                    imagen_url=prenda["imagen_url"],
                    categoria=prenda["categoria"],
                    justificacion=(
                        "Prenda imprescindible de nuestra colección comercial seleccionada por su alta "
                        f"disponibilidad ({prenda['stock_total']} unidades) y diseño contemporáneo versátil."
                    ),
                )
            )
        mensaje = (
            "Te presentamos una selección destacada de prendas de alta demanda y disponibilidad inmediata "
            "en nuestras tiendas para complementar tu estilo."
        )
        return mensaje, prendas_fallback

    def recomendar_outfit(
        self,
        cursor: Any,
        peticion: RecomendacionIAPeticion,
        id_usuario: int | None = None,
        ip_address: str | None = None,
    ) -> RecomendacionIARespuesta:
        """Genera recomendaciones de prendas basadas en IA con validación anti-alucinación y auditoría."""
        catalogo_db = self._obtener_catalogo_activo_con_stock(cursor)
        if not catalogo_db:
            mensaje = "Actualmente no existen prendas activas con existencias disponibles en tienda."
            respuesta = RecomendacionIARespuesta(
                mensaje_estilista=mensaje,
                es_fallback=True,
                prendas=[],
            )
            registrar_bitacora(
                cursor=cursor,
                accion=ACCION_IA_RECOMENDACION,
                tabla_afectada="inventario",
                detalle="Consulta recomendador IA: Catálogo sin stock físico disponible.",
                id_usuario=id_usuario,
                ip_address=ip_address,
            )
            return respuesta

        catalogo_dict = {item["id_prenda"]: item for item in catalogo_db}
        client = self.get_client()

        es_fallback = False
        modelo_usado: str | None = None
        mensaje_estilista = ""
        prendas_recomendadas: list[PrendaRecomendada] = []

        if client is None:
            mensaje_estilista, prendas_recomendadas = self._ejecutar_fallback_recomendacion(
                catalogo_db, peticion.limite, razon="Gemini API Client no configurado o sin API Key"
            )
            es_fallback = True
        else:
            catalogo_resumen = [
                {
                    "id_prenda": p["id_prenda"],
                    "nombre": p["nombre"],
                    "precio": float(p["precio"]),
                    "categoria": p["categoria"],
                    "genero": p["genero"],
                    "temporada": p["temporada"] or "Atemporal",
                    "tallas": p.get("tallas_disponibles") or "",
                    "stock_total": p["stock_total"],
                }
                for p in catalogo_db
            ]

            system_instruction = (
                "Eres un estilista y consultor de moda experto para FashionStore.\n"
                "Tu objetivo es sugerir combinaciones de ropa y outfits armónicos basados en las preferencias del usuario.\n"
                "REGLAS OBLIGATORIAS:\n"
                "1. Selecciona EXCLUSIVAMENTE prendas que pertenezcan a la lista provista en 'CATÁLOGO DISPONIBLE'.\n"
                "2. NO inventes jamás identificadores (id_prenda). Cada id_prenda debe ser un número entero que exista en la lista.\n"
                "3. Para cada prenda, provee una justificación comercial de estilo clara y convincente.\n"
                "4. Debes devolver la respuesta en formato JSON estrictamente válido."
            )

            user_prompt = (
                f"Preferencias del cliente:\n"
                f"- Estilo: {peticion.estilo or 'No especificado'}\n"
                f"- Ocasión: {peticion.ocasion or 'No especificada'}\n"
                f"- Género: {peticion.genero or 'Todos'}\n"
                f"- Talla: {peticion.talla or 'No especificada'}\n"
                f"- Temporada / Clima: {peticion.temporada or 'General'} / {peticion.clima or 'Templado'}\n"
                f"- Máximo de prendas sugeridas: {peticion.limite}\n\n"
                f"CATÁLOGO DISPONIBLE (CON STOCK FÍSICO):\n"
                f"{json.dumps(catalogo_resumen, ensure_ascii=False)}\n\n"
                f"Formato JSON requerido:\n"
                f"{{\n"
                f'  "mensaje_estilista": "Explicación integral del concepto del outfit y sugerencias de uso.",\n'
                f'  "recomendaciones": [\n'
                f'    {{"id_prenda": 4, "justificacion": "Aporta un estilo vanguardista..."}}\n'
                f"  ]\n"
                f"}}"
            )

            modelos = [
                modelo.strip()
                for modelo in os.getenv(
                    "GEMINI_RECOMMENDATION_MODELS",
                    "gemini-3.5-flash-lite,gemini-3.1-flash-lite",
                ).split(",")
                if modelo.strip()
            ]
            for modelo in modelos:
                try:
                    response = client.models.generate_content(
                        model=modelo,
                        contents=user_prompt,
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction,
                            response_mime_type="application/json",
                            temperature=0.2,
                            http_options=types.HttpOptions(
                                timeout=30000,
                                retry_options=types.HttpRetryOptions(attempts=1),
                            ),
                        ),
                    )
                    data = json.loads(response.text or "{}")
                    candidatos = data.get("recomendaciones") or []
                    seleccion: list[PrendaRecomendada] = []
                    ids_vistos: set[int] = set()

                    # Solo se admiten prendas reales con stock; el modelo nunca fija precio ni imagen.
                    for item in candidatos:
                        if not isinstance(item, dict):
                            continue
                        try:
                            id_candidato = int(item.get("id_prenda"))
                        except (TypeError, ValueError):
                            continue
                        if id_candidato not in catalogo_dict or id_candidato in ids_vistos:
                            logger.warning("ID de prenda %s de %s descartado por no existir o duplicado.", id_candidato, modelo)
                            continue
                        prenda_db = catalogo_dict[id_candidato]
                        ids_vistos.add(id_candidato)
                        seleccion.append(
                            PrendaRecomendada(
                                id_prenda=id_candidato,
                                nombre=prenda_db["nombre"],
                                precio=float(prenda_db["precio"]),
                                stock_total=int(prenda_db["stock_total"]),
                                imagen_url=prenda_db["imagen_url"],
                                categoria=prenda_db["categoria"],
                                justificacion=item.get("justificacion")
                                or "Excelente combinación para el conjunto seleccionado.",
                            )
                        )
                        if len(seleccion) >= peticion.limite:
                            break

                    if not seleccion:
                        raise ValueError("El modelo no devolvió prendas válidas del catálogo")
                    mensaje_estilista = data.get("mensaje_estilista") or "Sugerencia personalizada de estilismo."
                    prendas_recomendadas = seleccion
                    modelo_usado = modelo
                    break
                except Exception as exc:
                    logger.warning("Fallo del modelo %s en recomendar_outfit: %s", modelo, exc)

            if not prendas_recomendadas:
                mensaje_estilista, prendas_recomendadas = self._ejecutar_fallback_recomendacion(
                    catalogo_db, peticion.limite, razon="Ningún modelo Gemini produjo recomendaciones válidas"
                )
                es_fallback = True

        # CU25: Registro inmutable en bitácora
        primer_id = prendas_recomendadas[0].id_prenda if prendas_recomendadas else None
        modo_str = "Fallback Catálogo" if es_fallback else modelo_usado
        detalle_bitacora = (
            f"Recomendación IA ({modo_str}): {len(prendas_recomendadas)} prendas sugeridas para "
            f"estilo '{peticion.estilo or 'General'}' y ocasión '{peticion.ocasion or 'General'}'."
        )
        registrar_bitacora(
            cursor=cursor,
            accion=ACCION_IA_RECOMENDACION,
            tabla_afectada="inventario",
            detalle=detalle_bitacora,
            id_usuario=id_usuario,
            registro_id=primer_id,
            ip_address=ip_address,
        )

        return RecomendacionIARespuesta(
            mensaje_estilista=mensaje_estilista,
            es_fallback=es_fallback,
            prendas=prendas_recomendadas,
        )

    # =========================================================================
    # CU23: CONSULTAS ANALÍTICAS GENERATIVAS POR VOZ Y REPORTES PDF
    # =========================================================================

    def _extraer_parametros_semanticos(self, texto_voz: str) -> ParametrosAnalitica:
        """Extrae parámetros estructurados usando Gemini con respaldo heurístico."""
        client = self.get_client()
        if client is not None:
            prompt = (
                "Analiza la siguiente transcripción de voz de una consulta ejecutiva para FashionStore "
                "y extrae los parámetros de consulta estructurados:\n"
                f'"{texto_voz}"\n\n'
                "Instrucciones:\n"
                "- metrica: Uno de 'ventas_total' (ventas/ingresos/facturación), "
                "'inventario_stock' (existencias/stock/unidades), "
                "'compras_total' (compras a proveedores/adquisiciones). Si no queda claro usa 'ventas_total'.\n"
                "- sucursal: Nombre de la sucursal mencionada (ej: 'Central', 'Equipetrol', 'Tarija', etc.) o null.\n"
                "- temporada: Nombre de la temporada mencionada (ej: 'Verano 2026', 'Invierno', etc.) o null.\n"
                "- fecha_inicio: Fecha YYYY-MM-DD si se menciona un período inicial, o null.\n"
                "- fecha_fin: Fecha YYYY-MM-DD si se menciona un período final, o null.\n\n"
                "Devuelve ÚNICAMENTE un objeto JSON válido con este formato:\n"
                "{\n"
                '  "metrica": "ventas_total",\n'
                '  "sucursal": null,\n'
                '  "temporada": null,\n'
                '  "fecha_inicio": null,\n'
                '  "fecha_fin": null\n'
                "}"
            )
            modelos = [
                modelo.strip()
                for modelo in os.getenv(
                    "GEMINI_ANALYTICS_MODELS",
                    "gemini-3.5-flash-lite,gemini-3.1-flash-lite",
                ).split(",")
                if modelo.strip()
            ]
            for modelo in modelos:
                try:
                    response = client.models.generate_content(
                        model=modelo,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            temperature=0.1,
                            http_options=types.HttpOptions(
                                timeout=30000,
                                retry_options=types.HttpRetryOptions(attempts=1),
                            ),
                        ),
                    )
                    data = json.loads(response.text or "{}")
                    metrica = data.get("metrica")
                    if metrica not in ("ventas_total", "inventario_stock", "compras_total"):
                        raise ValueError(f"Métrica inválida: {metrica!r}")
                    parametros = ParametrosAnalitica(
                        metrica=metrica,
                        sucursal=data.get("sucursal"),
                        temporada=data.get("temporada"),
                        fecha_inicio=data.get("fecha_inicio"),
                        fecha_fin=data.get("fecha_fin"),
                    )
                    logger.info("Interpretación analítica generada por %s", modelo)
                    return parametros
                except Exception as exc:
                    logger.warning("Fallo del modelo %s en extracción analítica: %s", modelo, exc)

            logger.warning("Ningún modelo Gemini interpretó la consulta. Utilizando extractor determinista.")

        # Respaldo heurístico determinista
        texto_lower = texto_voz.lower()
        if any(k in texto_lower for k in ("inventario", "stock", "existencia", "disponib")):
            metrica = "inventario_stock"
        elif any(k in texto_lower for k in ("compra", "adquisici", "proveedor", "costo")):
            metrica = "compras_total"
        else:
            metrica = "ventas_total"

        sucursal_match = None
        for palabra in ("central", "centro", "equipetrol", "tarija", "norte", "sur"):
            if palabra in texto_lower:
                sucursal_match = palabra.capitalize()
                break

        temporada_match = None
        for temp in ("verano", "invierno", "otono", "otoño", "primavera"):
            if temp in texto_lower:
                temporada_match = temp.capitalize()
                break

        return ParametrosAnalitica(
            metrica=metrica,
            sucursal=sucursal_match,
            temporada=temporada_match,
            fecha_inicio=None,
            fecha_fin=None,
        )

    def _ejecutar_consulta_sql_estadistica(
        self,
        cursor: Any,
        params: ParametrosAnalitica,
    ) -> tuple[str, list[ResultadoFila], str]:
        """Ejecuta consultas agregadas parametrizadas sobre PostgreSQL con datos 100% reales."""
        metrica = params.metrica or "ventas_total"
        filas: list[ResultadoFila] = []
        sql_ejecutada = ""
        resumen_ejecutivo = ""

        if metrica == "inventario_stock":
            if params.sucursal:
                sql_ejecutada = (
                    "SELECT COALESCE(c.nombre, 'Sin Categoría') AS etiqueta, "
                    "COALESCE(SUM(inv.stock), 0)::float AS valor, "
                    "COUNT(DISTINCT vp.id_prenda)::int AS cantidad_operaciones "
                    "FROM inventario inv "
                    "JOIN sucursal s ON inv.id_sucursal = s.id_sucursal "
                    "JOIN variante_prenda vp ON inv.id_variante_prenda = vp.id_variante_prenda "
                    "JOIN prenda p ON vp.id_prenda = p.id_prenda "
                    "JOIN categoria c ON p.id_categoria = c.id_categoria "
                    "WHERE s.nombre ILIKE %s "
                    "GROUP BY c.nombre ORDER BY valor DESC;"
                )
                cursor.execute(sql_ejecutada, (f"%{params.sucursal}%",))
            else:
                sql_ejecutada = (
                    "SELECT COALESCE(s.nombre, 'Sin Sucursal') AS etiqueta, "
                    "COALESCE(SUM(inv.stock), 0)::float AS valor, "
                    "COUNT(DISTINCT inv.id_variante_prenda)::int AS cantidad_operaciones "
                    "FROM inventario inv "
                    "JOIN sucursal s ON inv.id_sucursal = s.id_sucursal "
                    "GROUP BY s.nombre ORDER BY valor DESC;"
                )
                cursor.execute(sql_ejecutada)

            db_filas = cursor.fetchall()
            for r in db_filas:
                filas.append(
                    ResultadoFila(
                        etiqueta=str(r["etiqueta"]),
                        valor=float(r["valor"]),
                        cantidad_operaciones=int(r["cantidad_operaciones"]),
                    )
                )

            total_unidades = sum(f.valor for f in filas)
            total_ops = sum(f.cantidad_operaciones for f in filas)
            sucursal_str = f" en la sucursal {params.sucursal}" if params.sucursal else " a nivel multisucursal"
            resumen_ejecutivo = (
                f"Existencias físicas consolidadas: {int(total_unidades)} unidades distribuidas en "
                f"{total_ops} variantes/categorías{sucursal_str}."
            )

        elif metrica == "compras_total":
            if params.sucursal:
                sql_ejecutada = (
                    "SELECT COALESCE(prov.razon_social, 'Proveedor general') AS etiqueta, "
                    "COALESCE(SUM(c.total), 0)::float AS valor, "
                    "COUNT(c.id_compra)::int AS cantidad_operaciones "
                    "FROM compra c "
                    "JOIN sucursal s ON c.id_sucursal = s.id_sucursal "
                    "JOIN proveedor prov ON c.id_proveedor = prov.id_proveedor "
                    "WHERE s.nombre ILIKE %s "
                    "GROUP BY prov.razon_social ORDER BY valor DESC;"
                )
                cursor.execute(sql_ejecutada, (f"%{params.sucursal}%",))
            else:
                sql_ejecutada = (
                    "SELECT COALESCE(s.nombre, 'Todas las sucursales') AS etiqueta, "
                    "COALESCE(SUM(c.total), 0)::float AS valor, "
                    "COUNT(c.id_compra)::int AS cantidad_operaciones "
                    "FROM compra c "
                    "JOIN sucursal s ON c.id_sucursal = s.id_sucursal "
                    "GROUP BY s.nombre ORDER BY valor DESC;"
                )
                cursor.execute(sql_ejecutada)

            db_filas = cursor.fetchall()
            for r in db_filas:
                filas.append(
                    ResultadoFila(
                        etiqueta=str(r["etiqueta"]),
                        valor=float(r["valor"]),
                        cantidad_operaciones=int(r["cantidad_operaciones"]),
                    )
                )

            total_monto = sum(f.valor for f in filas)
            total_ops = sum(f.cantidad_operaciones for f in filas)
            sucursal_str = f" en la sucursal {params.sucursal}" if params.sucursal else " global"
            resumen_ejecutivo = (
                f"Inversión total en compras a proveedores: Bs {total_monto:,.2f} a través de "
                f"{total_ops} adquisiciones registradas{sucursal_str}."
            )

        else:  # ventas_total
            if params.sucursal:
                sql_ejecutada = (
                    "SELECT COALESCE(TO_CHAR(v.fecha_venta, 'YYYY-MM'), 'Ventas') AS etiqueta, "
                    "COALESCE(SUM(v.total), 0)::float AS valor, "
                    "COUNT(v.id_venta)::int AS cantidad_operaciones "
                    "FROM venta v "
                    "JOIN sucursal s ON v.id_sucursal = s.id_sucursal "
                    "WHERE s.nombre ILIKE %s "
                    "GROUP BY TO_CHAR(v.fecha_venta, 'YYYY-MM') ORDER BY etiqueta ASC;"
                )
                cursor.execute(sql_ejecutada, (f"%{params.sucursal}%",))
            else:
                sql_ejecutada = (
                    "SELECT COALESCE(s.nombre, 'Todas las sucursales') AS etiqueta, "
                    "COALESCE(SUM(v.total), 0)::float AS valor, "
                    "COUNT(v.id_venta)::int AS cantidad_operaciones "
                    "FROM venta v "
                    "JOIN sucursal s ON v.id_sucursal = s.id_sucursal "
                    "GROUP BY s.nombre ORDER BY valor DESC;"
                )
                cursor.execute(sql_ejecutada)

            db_filas = cursor.fetchall()
            for r in db_filas:
                filas.append(
                    ResultadoFila(
                        etiqueta=str(r["etiqueta"]),
                        valor=float(r["valor"]),
                        cantidad_operaciones=int(r["cantidad_operaciones"]),
                    )
                )

            total_monto = sum(f.valor for f in filas)
            total_ops = sum(f.cantidad_operaciones for f in filas)
            sucursal_str = f" para la sucursal {params.sucursal}" if params.sucursal else " global"
            if total_ops == 0:
                resumen_ejecutivo = (
                    f"No se registraron ventas en el sistema para los parámetros solicitados{sucursal_str} "
                    "(Monto acumulado: Bs 0.00)."
                )
            else:
                resumen_ejecutivo = (
                    f"Recaudación total por ventas: Bs {total_monto:,.2f} en un total de "
                    f"{total_ops} transacciones comerciales{sucursal_str}."
                )

        return sql_ejecutada, filas, resumen_ejecutivo

    def _generar_reporte_pdf_base64(
        self,
        texto_voz: str,
        params: ParametrosAnalitica,
        resultados: list[ResultadoFila],
        resumen_ejecutivo: str,
    ) -> str:
        """Construye un documento PDF ejecutivo en memoria y lo serializa a Base64."""
        pdf = ExecutiveReportPDF(orientation="P", unit="mm", format="A4")
        pdf.add_page()

        # Metadata de consulta
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(30, 41, 59)
        pdf.cell(0, 7, "1. Parámetros de la Consulta por Voz", new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(71, 85, 105)
        pdf.multi_cell(0, 5, f'Transcripción original: "{texto_voz}"')
        pdf.ln(2)

        pdf.cell(45, 5, f"Métrica: {params.metrica or 'N/A'}")
        pdf.cell(45, 5, f"Sucursal: {params.sucursal or 'Todas'}")
        pdf.cell(45, 5, f"Temporada: {params.temporada or 'Todas'}")
        pdf.cell(45, 5, f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M')}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

        # Resumen Ejecutivo
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(30, 41, 59)
        pdf.cell(0, 7, "2. Síntesis y Resumen Ejecutivo", new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("Helvetica", "", 10)
        pdf.set_fill_color(241, 245, 249)
        pdf.set_text_color(15, 23, 42)
        pdf.multi_cell(0, 6, resumen_ejecutivo, fill=True)
        pdf.ln(4)

        # Tabla de Datos Estadísticos
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(30, 41, 59)
        pdf.cell(0, 7, "3. Desglose Estadístico Detallado", new_x="LMARGIN", new_y="NEXT")

        # Cabecera de tabla
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_fill_color(30, 41, 59)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(100, 7, "Segmento / Etiqueta", border=1, fill=True)
        pdf.cell(50, 7, "Monto (Bs) / Cantidad", border=1, fill=True, align="R")
        pdf.cell(40, 7, "Operaciones", border=1, fill=True, align="R", new_x="LMARGIN", new_y="NEXT")

        # Filas de la tabla
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(51, 65, 85)
        fill = False
        total_monto = 0.0
        total_ops = 0

        for r in resultados:
            pdf.set_fill_color(248, 250, 252) if fill else pdf.set_fill_color(255, 255, 255)
            pdf.cell(100, 6, r.etiqueta[:45], border=1, fill=fill)
            valor_fmt = f"{r.valor:,.2f}" if "stock" not in (params.metrica or "") else f"{int(r.valor)}"
            pdf.cell(50, 6, valor_fmt, border=1, fill=fill, align="R")
            pdf.cell(40, 6, str(r.cantidad_operaciones), border=1, fill=fill, align="R", new_x="LMARGIN", new_y="NEXT")
            total_monto += r.valor
            total_ops += r.cantidad_operaciones
            fill = not fill

        # Fila de totales
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_fill_color(226, 232, 240)
        pdf.cell(100, 7, "TOTAL CONSOLIDADO", border=1, fill=True)
        total_fmt = f"{total_monto:,.2f}" if "stock" not in (params.metrica or "") else f"{int(total_monto)}"
        pdf.cell(50, 7, total_fmt, border=1, fill=True, align="R")
        pdf.cell(40, 7, str(total_ops), border=1, fill=True, align="R", new_x="LMARGIN", new_y="NEXT")

        pdf_bytes = bytes(pdf.output())
        return base64.b64encode(pdf_bytes).decode("utf-8")

    def analizar_voz(
        self,
        cursor: Any,
        peticion: AnaliticaVozPeticion,
        id_usuario: int | None = None,
        ip_address: str | None = None,
    ) -> AnaliticaVozRespuesta:
        """Procesa una consulta dictada por voz, extrae parámetros semánticos, ejecuta SQL y audita."""
        params = self._extraer_parametros_semanticos(peticion.texto_voz)
        sql_ejecutada, resultados, resumen_ejecutivo = self._ejecutar_consulta_sql_estadistica(cursor, params)

        pdf_base64 = None
        if peticion.generar_pdf:
            pdf_base64 = self._generar_reporte_pdf_base64(
                texto_voz=peticion.texto_voz,
                params=params,
                resultados=resultados,
                resumen_ejecutivo=resumen_ejecutivo,
            )

        # CU25: Registro de auditoría
        tabla_afectada = (
            "venta"
            if params.metrica == "ventas_total"
            else ("compra" if params.metrica == "compras_total" else "inventario")
        )
        detalle_bitacora = (
            f"Analítica por voz CU23: '{peticion.texto_voz[:80]}' -> Métrica '{params.metrica}', "
            f"Resultados={len(resultados)}, PDF={peticion.generar_pdf}."
        )
        registrar_bitacora(
            cursor=cursor,
            accion=ACCION_IA_ANALITICA_VOZ,
            tabla_afectada=tabla_afectada,
            detalle=detalle_bitacora,
            id_usuario=id_usuario,
            registro_id=None,
            ip_address=ip_address,
        )

        return AnaliticaVozRespuesta(
            interpretacion=params,
            consulta_sql_ejecutada=sql_ejecutada,
            resultados=resultados,
            resumen_ejecutivo=resumen_ejecutivo,
            pdf_base64=pdf_base64,
        )


# Instancia única reutilizable para inyección de dependencias
ai_service = GeminiAIService()
