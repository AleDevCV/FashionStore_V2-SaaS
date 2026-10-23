"""
=============================================================================
FASHIONSTORE - ROUTER DE AUTENTICACIÓN (CU01)
Sistemas de Información II - UAGRM
-----------------------------------------------------------------------------
Implementa el flujo principal del CU01 "Gestionar Inicio y Cierre de Sesión":
recibe las credenciales, las contrasta contra la tabla `usuario` de PostgreSQL
y devuelve un token JWT firmado con el rol jerárquico del usuario.

El cierre de sesión no requiere endpoint: el JWT no guarda estado en el
servidor, por lo que basta con que el frontend destruya el token (paso 10 del
flujo principal del caso de uso).
=============================================================================
"""

import secrets
import hashlib
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.database import get_db
from app.schemas.auth import (
    RespuestaRecuperarPassword,
    RespuestaRestablecerPassword,
    RespuestaToken,
    RespuestaVerificarToken,
    SolicitudLogin,
    SolicitudRecuperarPassword,
    SolicitudRestablecerPassword,
    SolicitudVerificarToken,
)
from app.services.auth_service import (
    crear_token_acceso,
    generar_hash_password,
    verificar_password,
)
from app.services.bitacora_service import (
    ACCION_LOGIN_EXITOSO,
    ACCION_LOGIN_FALLIDO,
    ACCION_RESTABLECER_PASSWORD_EXITOSO,
    ACCION_SOLICITUD_RECUPERACION,
    obtener_ip_cliente,
    registrar_bitacora,
)
from app.services.email_service import enviar_correo_recuperacion

router = APIRouter(tags=["Autenticación (CU01)"])

# Hash bcrypt de una contraseña arbitraria, usado como señuelo cuando el correo
# no existe. Permite ejecutar siempre una verificación bcrypt real y así igualar
# el tiempo de respuesta entre "correo inexistente" y "contraseña incorrecta".
# Sin esto, un atacante podría medir la latencia para deducir qué correos están
# registrados en el sistema (enumeración de usuarios).
_HASH_SEÑUELO = "$2b$12$zZo3V7AI.OyS0Nr3B.46Rev0BJawpm/pc9jSjS4u5anr.uEAleZX6"


@router.post(
    "/login/",
    response_model=RespuestaToken,
    status_code=status.HTTP_200_OK,
    summary="Iniciar sesión y obtener un token JWT",
)
def iniciar_sesion(
    credenciales: SolicitudLogin,
    request: Request,
    cursor=Depends(get_db),
):
    """Autentica a un usuario y emite su token de acceso.

    Lógica de seguridad aplicada, en orden:

      1. Se busca el correo en la tabla `usuario`, uniéndola con `rol` para
         recuperar el nombre textual del rol jerárquico en la misma consulta.
         La consulta es parametrizada (%s), lo que impide inyección SQL.
      2. Si el correo no existe, igualmente se ejecuta una verificación bcrypt
         contra un hash señuelo para no delatar por tiempo qué correos existen.
      3. Se compara la contraseña recibida con el hash bcrypt almacenado. Un
         fallo devuelve 401 sin precisar si falló el correo o la contraseña,
         para no dar pistas a un atacante.
      4. Solo después de validar las credenciales se comprueba el estado de la
         cuenta: una cuenta inactiva responde 403 (excepción B del CU01).
      5. Se firma el JWT con los claims que el frontend necesita pintar en la
         interfaz: id_usuario, correo, nombre completo y rol.

      6. Todo intento, exitoso o fallido, queda registrado en la tabla
         `bitacora` junto con la IP de origen (paso 9 del flujo del CU01).

    Parámetros:
        credenciales: cuerpo JSON validado por Pydantic con `correo` y `password`.
        request: petición HTTP, usada para obtener la IP real del cliente.
        cursor: cursor de PostgreSQL inyectado por la dependencia `get_db`.

    Retorna:
        RespuestaToken: objeto con `access_token` (JWT) y `token_type` ("bearer").

    Errores:
        HTTP 401: correo inexistente o contraseña incorrecta.
        HTTP 403: credenciales válidas pero cuenta en estado 'Inactivo'.
    """
    ip_cliente = obtener_ip_cliente(request)
    # --- 1. Búsqueda del usuario y su rol -----------------------------------
    # LEFT JOIN: un usuario sin rol asignado debe poder autenticarse igualmente,
    # aunque quede sin privilegios en el panel.
    cursor.execute(
        """
        SELECT  u.id_usuario,
                u.nombre,
                u.apellido,
                u.correo,
                u.password_hash,
                u.token_version,
                u.estado,
                r.nombre AS rol
        FROM usuario u
        LEFT JOIN rol r ON u.id_role = r.id_rol
        WHERE u.correo = %s;
        """,
        (credenciales.correo,),
    )
    usuario = cursor.fetchone()

    # --- 2 y 3. Verificación de la contraseña -------------------------------
    # El hash a comparar es el real si el usuario existe, o el señuelo si no.
    # De este modo la operación bcrypt (deliberadamente lenta) se ejecuta
    # siempre y ambos caminos tardan lo mismo.
    hash_almacenado = usuario["password_hash"] if usuario else _HASH_SEÑUELO
    password_valida = verificar_password(credenciales.password, hash_almacenado)

    if usuario is None or not password_valida:
        # AUDITORÍA DEL INTENTO FALLIDO.
        # Se pasa confirmar=True porque la HTTPException que se lanza justo
        # debajo hace que `get_db` revierta la transacción de esta petición;
        # sin el COMMIT inmediato, el rastro del intento fallido se perdería.
        # El motivo exacto (correo inexistente vs. contraseña incorrecta) sí se
        # detalla aquí: la bitácora es interna y esa precisión es justo lo que
        # necesita el auditor para detectar un ataque de fuerza bruta.
        motivo = (
            "correo no registrado" if usuario is None else "contraseña incorrecta"
        )
        registrar_bitacora(
            cursor=cursor,
            accion=ACCION_LOGIN_FALLIDO,
            tabla_afectada="usuario",
            # Si el correo existe se guarda su id; si no, queda NULL.
            id_usuario=usuario["id_usuario"] if usuario else None,
            registro_id=usuario["id_usuario"] if usuario else None,
            detalle=(
                f"Intento de inicio de sesión fallido para el correo: "
                f"{credenciales.correo} ({motivo})."
            ),
            ip_address=ip_cliente,
            confirmar=True,
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            # Cabecera exigida por el estándar HTTP para respuestas 401.
            headers={"WWW-Authenticate": "Bearer"},
        )

    # --- 4. Estado de la cuenta (excepción B del CU01) ----------------------
    # Se comprueba DESPUÉS de validar la contraseña: informar de una cuenta
    # suspendida a quien no conoce la clave sería filtrar información.
    if usuario["estado"] != "Activo":
        registrar_bitacora(
            cursor=cursor,
            accion=ACCION_LOGIN_FALLIDO,
            tabla_afectada="usuario",
            id_usuario=usuario["id_usuario"],
            registro_id=usuario["id_usuario"],
            detalle=(
                f"Intento de inicio de sesión rechazado para el correo: "
                f"{credenciales.correo} (cuenta en estado "
                f"'{usuario['estado']}')."
            ),
            ip_address=ip_cliente,
            confirmar=True,
        )

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Su cuenta se encuentra suspendida temporalmente",
        )

    # --- 5. Emisión del token -----------------------------------------------
    # El nombre viaja ya concatenado para que el frontend lo muestre tal cual
    # en la cabecera del panel, sin tener que componerlo.
    nombre_completo = f"{usuario['nombre']} {usuario['apellido']}".strip()

    token = crear_token_acceso({
        "id_usuario": usuario["id_usuario"],
        "correo": usuario["correo"],
        "nombre": nombre_completo,
        # Un usuario sin rol asignado recibe una etiqueta explícita en lugar de
        # un valor nulo, que rompería el tipado del frontend.
        "rol": usuario["rol"] or "Sin rol asignado",
        # `sub` (subject) es el claim estándar del RFC 7519 para identificar al
        # titular del token; debe ser una cadena.
        "sub": str(usuario["id_usuario"]),
        "token_version": usuario["token_version"],
    })

    # --- 6. Auditoría del acceso concedido (paso 9 del CU01) ----------------
    # Aquí NO se fuerza el commit: la petición termina sin excepción, por lo que
    # `get_db` consolida la transacción de forma natural al cerrarse.
    registrar_bitacora(
        cursor=cursor,
        accion=ACCION_LOGIN_EXITOSO,
        tabla_afectada="usuario",
        id_usuario=usuario["id_usuario"],
        registro_id=usuario["id_usuario"],
        detalle=(
            f"Inicio de sesión exitoso de '{nombre_completo}' "
            f"({usuario['correo']}) con rol "
            f"'{usuario['rol'] or 'Sin rol asignado'}'."
        ),
        ip_address=ip_cliente,
    )

    return RespuestaToken(access_token=token, token_type="bearer")


# -----------------------------------------------------------------------------
# ALIAS SIN BARRA FINAL
# -----------------------------------------------------------------------------
# FastAPI redirige /api/login hacia /api/login/ con un 307, pero un redirect en
# una petición POST con CORS puede fallar en algunos navegadores. Registrar la
# ruta explícitamente evita ese riesgo. Se oculta de Swagger (include_in_schema)
# para no duplicar la misma operación en la documentación.
@router.post(
    "/login",
    response_model=RespuestaToken,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
def iniciar_sesion_sin_barra(
    credenciales: SolicitudLogin,
    request: Request,
    cursor=Depends(get_db),
):
    """Alias de `iniciar_sesion` para la ruta sin barra final.

    Parámetros:
        credenciales: mismo cuerpo JSON que el endpoint principal.
        request: petición HTTP, usada para obtener la IP del cliente.
        cursor: cursor de PostgreSQL inyectado por `get_db`.

    Retorna:
        RespuestaToken: idéntica a la del endpoint /api/login/.
    """
    return iniciar_sesion(credenciales, request, cursor)


# =============================================================================
# CU04 - RECUPERACIÓN DE CONTRASEÑAS
# =============================================================================

@router.post(
    "/auth/recuperar-password",
    response_model=RespuestaRecuperarPassword,
    status_code=status.HTTP_200_OK,
    summary="Solicitar recuperación de contraseña por correo",
    tags=["Recuperación de Contraseña (CU04)"],
)
def solicitar_recuperacion_password(
    solicitud: SolicitudRecuperarPassword,
    request: Request,
    cursor=Depends(get_db),
):
    """Genera un token temporal de 30 min y despacha correo o log de recuperación.

    Invalida tokens previos pendientes del usuario y registra la solicitud
    en la tabla `bitacora` (CU25). Devuelve una respuesta uniforme para mitigar
    la enumeración de usuarios.
    """
    ip_cliente = obtener_ip_cliente(request)

    cursor.execute(
        """
        SELECT id_usuario, nombre, apellido, correo, estado
        FROM usuario
        WHERE correo = %s;
        """,
        (solicitud.correo,),
    )
    usuario = cursor.fetchone()

    if usuario and usuario["estado"] == "Activo":
        id_usuario = usuario["id_usuario"]

        # 1. Invalidar tokens no usados previos de este usuario
        cursor.execute(
            """
            UPDATE usuario_token
            SET usado = TRUE
            WHERE id_usuario = %s AND usado = FALSE;
            """,
            (id_usuario,),
        )

        # 2. Generar token criptográfico único con caducidad estricta de 30 minutos
        token = secrets.token_urlsafe(32)
        expiracion = datetime.now(timezone.utc) + timedelta(minutes=30)

        cursor.execute(
            """
            INSERT INTO usuario_token (id_usuario, token_recuperacion, expiracion, usado)
            VALUES (%s, %s, %s, FALSE)
            RETURNING id_token;
            """,
            (id_usuario, hashlib.sha256(token.encode()).hexdigest(), expiracion),
        )
        fila_token = cursor.fetchone()
        id_token = fila_token["id_token"] if fila_token else None

        # 3. Registrar auditoría inmutable en bitácora (CU25)
        registrar_bitacora(
            cursor=cursor,
            accion=ACCION_SOLICITUD_RECUPERACION,
            tabla_afectada="usuario_token",
            id_usuario=id_usuario,
            registro_id=id_token,
            detalle=f"Solicitud de recuperación de contraseña para el correo: {usuario['correo']}.",
            ip_address=ip_cliente,
        )

        # 4. Despachar correo electrónico o fallback seguro a logger
        nombre_completo = f"{usuario['nombre']} {usuario['apellido']}".strip()
        enviar_correo_recuperacion(usuario["correo"], nombre_completo, token)

    return RespuestaRecuperarPassword(
        mensaje="Si el correo existe en el sistema, se ha enviado un enlace de recuperación."
    )


@router.post(
    "/auth/recuperar-password/",
    response_model=RespuestaRecuperarPassword,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
def solicitar_recuperacion_password_alias(
    solicitud: SolicitudRecuperarPassword,
    request: Request,
    cursor=Depends(get_db),
):
    """Alias con barra final para solicitar_recuperacion_password."""
    return solicitar_recuperacion_password(solicitud, request, cursor)


@router.post(
    "/auth/verificar-token-recuperacion",
    response_model=RespuestaVerificarToken,
    status_code=status.HTTP_200_OK,
    summary="Verificar validez y vigencia del token de recuperación",
    tags=["Recuperación de Contraseña (CU04)"],
)
def verificar_token_recuperacion(
    solicitud: SolicitudVerificarToken,
    cursor=Depends(get_db),
):
    """Valida la existencia, no-uso y vigencia temporal (<30 min) del token.

    Retorna 200 OK con el correo enmascarado si el token es válido.
    Retorna 400 si el token no existe, ya fue usado o ha expirado.
    """
    token_str = hashlib.sha256(solicitud.token.strip().encode()).hexdigest()
    if not token_str:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token no proporcionado",
        )

    cursor.execute(
        """
        SELECT ut.id_token, ut.id_usuario, ut.token_recuperacion, ut.expiracion, ut.usado,
               u.correo, u.estado
        FROM usuario_token ut
        JOIN usuario u ON ut.id_usuario = u.id_usuario
        WHERE ut.token_recuperacion = %s FOR UPDATE OF ut;
        """,
        (token_str,),
    )
    registro = cursor.fetchone()

    if not registro:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token de recuperación no válido o inexistente",
        )

    if registro["usado"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El token de recuperación ya ha sido utilizado",
        )

    exp = registro["expiracion"]
    ahora = datetime.now(timezone.utc)
    if exp.tzinfo is None:
        ahora = ahora.replace(tzinfo=None)

    if exp < ahora:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El token de recuperación ha expirado",
        )

    if registro["estado"] != "Activo":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La cuenta asociada al token se encuentra inactiva",
        )

    correo_real = registro["correo"]
    partes = correo_real.split("@")
    user_part = partes[0]
    dom_part = partes[1] if len(partes) > 1 else ""
    if len(user_part) <= 2:
        enmascarado = user_part[0] + "***"
    else:
        enmascarado = user_part[:2] + "***"
    correo_ofuscado = f"{enmascarado}@{dom_part}" if dom_part else correo_real

    return RespuestaVerificarToken(
        valido=True,
        correo=correo_ofuscado,
        mensaje="Token válido y vigente",
    )


@router.post(
    "/auth/verificar-token-recuperacion/",
    response_model=RespuestaVerificarToken,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
def verificar_token_recuperacion_alias(
    solicitud: SolicitudVerificarToken,
    cursor=Depends(get_db),
):
    """Alias con barra final para verificar_token_recuperacion."""
    return verificar_token_recuperacion(solicitud, cursor)


@router.post(
    "/auth/restablecer-password",
    response_model=RespuestaRestablecerPassword,
    status_code=status.HTTP_200_OK,
    summary="Restablecer contraseña con token de recuperación",
    tags=["Recuperación de Contraseña (CU04)"],
)
def restablecer_password(
    solicitud: SolicitudRestablecerPassword,
    request: Request,
    cursor=Depends(get_db),
):
    """Actualiza la contraseña del usuario tras comprobar la validez del token.

    Genera el nuevo hash bcrypt, marca el token utilizado, invalida tokens
    pendientes y audita inmutablemente la operación en `bitacora` (CU25).
    """
    ip_cliente = obtener_ip_cliente(request)
    token_str = hashlib.sha256(solicitud.token.strip().encode()).hexdigest()

    cursor.execute(
        """
        SELECT ut.id_token, ut.id_usuario, ut.expiracion, ut.usado, u.correo, u.estado
        FROM usuario_token ut
        JOIN usuario u ON ut.id_usuario = u.id_usuario
        WHERE ut.token_recuperacion = %s FOR UPDATE OF ut;
        """,
        (token_str,),
    )
    registro = cursor.fetchone()

    if not registro:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token de recuperación no válido o inexistente",
        )

    if registro["usado"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El token de recuperación ya ha sido utilizado",
        )

    exp = registro["expiracion"]
    ahora = datetime.now(timezone.utc)
    if exp.tzinfo is None:
        ahora = ahora.replace(tzinfo=None)

    if exp < ahora:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El token de recuperación ha expirado",
        )

    if registro["estado"] != "Activo":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La cuenta asociada al token se encuentra inactiva",
        )

    id_usuario = registro["id_usuario"]
    id_token = registro["id_token"]

    # 1. Hashear y actualizar nueva contraseña en usuario
    nuevo_hash = generar_hash_password(solicitud.nueva_password)
    cursor.execute(
        """
        UPDATE usuario
        SET password_hash = %s, token_version = token_version + 1, updated_at = CURRENT_TIMESTAMP
        WHERE id_usuario = %s;
        """,
        (nuevo_hash, id_usuario),
    )

    # 2. Marcar token como usado e invalidar cualquier otro pendiente del usuario
    cursor.execute(
        """
        UPDATE usuario_token
        SET usado = TRUE
        WHERE id_token = %s;
        """,
        (id_token,),
    )
    cursor.execute(
        """
        UPDATE usuario_token
        SET usado = TRUE
        WHERE id_usuario = %s AND usado = FALSE;
        """,
        (id_usuario,),
    )

    # 3. Auditoría inmutable en bitácora (CU25)
    registrar_bitacora(
        cursor=cursor,
        accion=ACCION_RESTABLECER_PASSWORD_EXITOSO,
        tabla_afectada="usuario",
        id_usuario=id_usuario,
        registro_id=id_usuario,
        detalle=f"Restablecimiento exitoso de contraseña para la cuenta '{registro['correo']}' (ID: {id_usuario}).",
        ip_address=ip_cliente,
    )

    return RespuestaRestablecerPassword(
        mensaje="Contraseña restablecida exitosamente."
    )


@router.post(
    "/auth/restablecer-password/",
    response_model=RespuestaRestablecerPassword,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
def restablecer_password_alias(
    solicitud: SolicitudRestablecerPassword,
    request: Request,
    cursor=Depends(get_db),
):
    """Alias con barra final para restablecer_password."""
    return restablecer_password(solicitud, request, cursor)


# =============================================================================
# AUTO-REGISTRO DE CLIENTES (CU05 / CU01)
# =============================================================================

from app.schemas.cliente import RegistroClientePeticion, RegistroClienteRespuesta
from app.services import cliente_service as cli_svc


@router.post(
    "/auth/registro",
    response_model=RegistroClienteRespuesta,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un nuevo cliente en la plataforma (CU05)",
    tags=["Clientes (CU05)"],
)
@router.post(
    "/auth/registro/",
    response_model=RegistroClienteRespuesta,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
@router.post(
    "/auth/registro-cliente",
    response_model=RegistroClienteRespuesta,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
def registrar_cliente(
    solicitud: RegistroClientePeticion,
    request: Request,
    cursor=Depends(get_db),
):
    """Permite el auto-registro autónomo de clientes desde la web o app móvil (CU05).

    Crea la cuenta en `usuario` (con rol Cliente) y la ficha en `cliente` de forma
    atómica, audita en bitácora (CU25) y devuelve el token JWT para inicio de sesión
    inmediato en la plataforma.
    """
    # 1. Validar unicidad de CI
    if cli_svc.existe_ci(cursor, solicitud.ci):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La cédula de identidad ingresada ya se encuentra registrada.",
        )

    # 2. Validar unicidad de correo
    if cli_svc.existe_correo_usuario(cursor, solicitud.correo):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo electrónico ingresado ya se encuentra registrado.",
        )

    if cli_svc.existe_correo(cursor, solicitud.correo):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo electrónico ya está registrado por otro cliente.",
        )

    ip_cliente = obtener_ip_cliente(request)
    return cli_svc.auto_registrar_cliente(cursor, solicitud.model_dump(), ip_cliente=ip_cliente)


