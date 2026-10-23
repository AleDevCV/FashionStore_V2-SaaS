"""
=============================================================================
FASHIONSTORE - SERVICIO DE SEGURIDAD Y AUTENTICACIÓN (CU01)
Sistemas de Información II - UAGRM
-----------------------------------------------------------------------------
Concentra toda la criptografía del sistema, separada de los routers para
cumplir el RNF06 (mantenibilidad por capas):

  - Verificación de contraseñas contra los hashes bcrypt de PostgreSQL.
  - Generación de hashes para nuevas contraseñas (se usará en el CU02).
  - Firma y validación de los tokens JWT que autorizan cada petición.

RNF01 (Seguridad de la Información): las contraseñas NUNCA se guardan ni se
comparan en texto plano; solo se contrasta el hash bcrypt almacenado.
=============================================================================
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from dotenv import load_dotenv

from app.database import get_db

load_dotenv()

# -----------------------------------------------------------------------------
# CONFIGURACIÓN CRIPTOGRÁFICA
# -----------------------------------------------------------------------------

# Clave con la que se firman los tokens. Se lee del .env y jamás se escribe en
# el código fuente. Si cambia, todas las sesiones emitidas quedan invalidadas.
SECRET_KEY = os.getenv("SECRET_KEY", "")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))

# Falla al arrancar en lugar de firmar tokens con una clave vacía, que sería
# trivial de falsificar por un atacante.
if not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY no está definida en el archivo .env. "
        "Genere una con: python -c \"import secrets; print(secrets.token_urlsafe(48))\""
    )

# Contexto de hashing de passlib.
#   schemes=["bcrypt"] -> algoritmo de hash lento y con sal, resistente a
#                         ataques de fuerza bruta por GPU.
#   deprecated="auto"  -> marca como obsoleto cualquier esquema antiguo si en
#                         el futuro se migra a otro algoritmo (ej: argon2).
#
# NOTA DE COMPATIBILIDAD: passlib 1.7.4 solo funciona con bcrypt < 5.0. La
# versión está fijada en requirements.txt; ver el aviso de ese archivo.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# -----------------------------------------------------------------------------
# GESTIÓN DE CONTRASEÑAS
# -----------------------------------------------------------------------------

def verificar_password(password_plano: str, password_hash: str) -> bool:
    """Compara una contraseña en texto plano contra su hash bcrypt.

    passlib extrae la sal y el factor de coste incrustados en el propio hash,
    vuelve a derivar la contraseña recibida con esos mismos parámetros y
    compara ambos resultados en tiempo constante, evitando filtrar información
    mediante ataques de temporización.

    Parámetros:
        password_plano: contraseña tal como la escribió el usuario en el login.
        password_hash: hash bcrypt almacenado en `usuario.password_hash`.

    Retorna:
        bool: True si la contraseña corresponde al hash; False en caso contrario.
              También devuelve False si el hash está corrupto o tiene un formato
              que passlib no reconoce, de modo que un registro dañado en la base
              de datos nunca provoque un error 500 en el endpoint de login.
    """
    try:
        return pwd_context.verify(password_plano, password_hash)
    except ValueError:
        # El hash guardado no es un bcrypt válido (registro manipulado o semilla
        # mal generada). Se trata como credencial inválida, no como fallo del
        # servidor.
        return False


def generar_hash_password(password_plano: str) -> str:
    """Genera el hash bcrypt de una contraseña nueva.

    Se usará al registrar usuarios desde el CU02 y al restablecer contraseñas
    en el CU04. passlib genera una sal aleatoria distinta en cada llamada, por
    lo que dos usuarios con la misma contraseña producen hashes diferentes.

    Parámetros:
        password_plano: contraseña elegida por el administrador o el usuario.

    Retorna:
        str: hash bcrypt listo para guardarse en la columna `password_hash`.
    """
    return pwd_context.hash(password_plano)


# -----------------------------------------------------------------------------
# GESTIÓN DE TOKENS JWT
# -----------------------------------------------------------------------------

def crear_token_acceso(
    datos: dict[str, Any],
    expiracion_minutos: int | None = None,
) -> str:
    """Firma un token JWT con los datos de la sesión del usuario.

    El token se compone de tres partes codificadas en Base64Url y separadas por
    puntos: cabecera, carga útil (claims) y firma HMAC-SHA256. Cualquier
    modificación del payload por parte del cliente invalida la firma, por lo
    que el contenido es legible pero NO manipulable.

    Parámetros:
        datos: claims propios de la aplicación (id_usuario, correo, nombre, rol).
        expiracion_minutos: vigencia del token. Si se omite, usa el valor de
                            ACCESS_TOKEN_EXPIRE_MINUTES del .env (8 horas).

    Retorna:
        str: token JWT firmado, listo para enviarse al frontend de Angular.
    """
    claims = datos.copy()
    claims.setdefault('token_use', 'access')
    from app.tenant import require_context
    ctx = require_context()
    claims['tenant_id'] = ctx.tenant_id
    claims.setdefault('token_version', 0)

    minutos = expiracion_minutos or ACCESS_TOKEN_EXPIRE_MINUTES

    # Se usa UTC explícito: si se usara la hora local del contenedor, el token
    # expiraría antes o después de lo previsto según la zona horaria del host.
    emitido_en = datetime.now(timezone.utc)
    expira_en = emitido_en + timedelta(minutes=minutos)

    # Claims estándar del RFC 7519. `exp` e `iat` viajan como enteros Unix en
    # SEGUNDOS, que es lo que espera el AuthService de Angular.
    claims.update({
        "exp": int(expira_en.timestamp()),
        "iat": int(emitido_en.timestamp()),
    })

    return jwt.encode(claims, SECRET_KEY, algorithm=JWT_ALGORITHM)


def decodificar_token_acceso(token: str) -> dict[str, Any] | None:
    """Verifica la firma de un token JWT y devuelve sus claims.

    A diferencia del frontend (que solo lee el payload sin comprobar nada),
    aquí SÍ se valida criptográficamente la firma y la fecha de expiración.
    Esta función será la base de la dependencia `get_current_user` que protegerá
    los endpoints del CU02 en adelante.

    Parámetros:
        token: cadena JWT recibida en la cabecera `Authorization: Bearer <token>`.

    Retorna:
        dict | None: los claims del token si la firma es válida y no ha
                     expirado; None si el token fue manipulado, está mal
                     formado o ya venció.
    """
    try:
        claims = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return claims if claims.get('token_use', 'access') == 'access' else None
    except JWTError:
        # Cubre firma inválida, algoritmo no permitido y token expirado.
        return None


# =============================================================================
# DEPENDENCIAS DE SEGURIDAD DE FASTAPI (GUARDIANES DE RUTA)
# -----------------------------------------------------------------------------
# A partir de aquí se definen las dependencias que protegen los endpoints del
# CU02 en adelante. Se declaran en este mismo módulo para que toda la lógica de
# autenticación y autorización viva en un único lugar.
#
# Cadena de protección de un endpoint privado:
#   Petición -> HTTPBearer (extrae el token de la cabecera)
#            -> get_current_user (verifica firma, expiración y estado en BD)
#            -> requiere_rol (comprueba el rol jerárquico)
#            -> función del endpoint
# =============================================================================

# auto_error=False: si falta la cabecera Authorization, HTTPBearer devuelve None
# en lugar de lanzar su propio 403. Así se controla el error manualmente y se
# responde 401, que es el código semánticamente correcto para "no autenticado"
# y el que el interceptor de Angular usa para cerrar la sesión y redirigir.
esquema_bearer = HTTPBearer(auto_error=False, description="Token JWT del login")


def get_current_user(
    credenciales: HTTPAuthorizationCredentials | None = Depends(esquema_bearer),
    cursor=Depends(get_db),
) -> dict[str, Any]:
    """Identifica al usuario dueño del token JWT de la petición.

    Es el guardián de autenticación: cualquier endpoint que lo declare como
    dependencia queda cerrado a peticiones sin un token válido.

    Validaciones aplicadas, en orden:
      1. Que la cabecera `Authorization: Bearer <token>` esté presente.
      2. Que la firma del token sea auténtica y no haya expirado (se delega en
         `decodificar_token_acceso`, que verifica criptográficamente con la
         SECRET_KEY del servidor).
      3. Que el usuario del token SIGA EXISTIENDO en la base de datos. Un token
         es autocontenido y sobrevive a cambios en la base: sin esta consulta,
         un usuario eliminado conservaría acceso hasta que su token caducara.
      4. Que su cuenta siga en estado 'Activo'. Esto permite que inhabilitar a
         un usuario desde el CU02 le corte el acceso de inmediato, sin esperar
         las 8 horas de vigencia del token.

    Parámetros:
        credenciales: token extraído de la cabecera por HTTPBearer.
        cursor: cursor de PostgreSQL inyectado por `get_db`.

    Retorna:
        dict: datos frescos del usuario leídos de la base de datos
              (id_usuario, nombre, apellido, correo, estado, rol).

    Errores:
        HTTP 401: falta el token, es inválido, expiró o el usuario ya no existe.
        HTTP 403: el usuario existe pero su cuenta está inactiva.
    """
    # --- 1. Presencia del token ---------------------------------------------
    if credenciales is None or not credenciales.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado. Debe iniciar sesión.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # --- 2. Validez criptográfica y vigencia --------------------------------
    claims = decodificar_token_acceso(credenciales.credentials)
    if claims is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesión inválida o expirada. Vuelva a iniciar sesión.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    id_usuario = claims.get("id_usuario")
    if id_usuario is None:
        # Token firmado por este servidor pero sin el claim esperado: podría
        # provenir de una versión antigua de la API.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesión inválida o expirada. Vuelva a iniciar sesión.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # --- 3. El usuario debe seguir existiendo -------------------------------
    cursor.execute(
        """
        SELECT  u.id_usuario,
                u.nombre,
                u.apellido,
                u.correo,
                u.estado,
                u.id_role,
                r.nombre AS rol
        FROM usuario u
        LEFT JOIN rol r ON u.id_role = r.id_rol
        WHERE u.id_usuario = %s;
        """,
        (id_usuario,),
    )
    usuario = cursor.fetchone()

    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesión inválida o expirada. Vuelva a iniciar sesión.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # --- 4. La cuenta debe seguir activa ------------------------------------
    if usuario["estado"] != "Activo":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Su cuenta se encuentra suspendida temporalmente",
        )

    result = dict(usuario)
    from app.tenant import require_context
    result['tenant_id'] = require_context().tenant_id
    return result


def requiere_rol(roles_permitidos: list[str]):
    """Construye una dependencia que restringe un endpoint a ciertos roles.

    Implementa el control de acceso basado en roles (RBAC) exigido por el RF02.
    Es una fábrica de dependencias: se invoca al declarar la ruta y devuelve la
    función que FastAPI ejecutará en cada petición.

    Uso en un router:
        @router.get("/", dependencies=[Depends(requiere_rol(["Administrador"]))])

    O bien, cuando el endpoint necesita saber quién es el solicitante:
        def listar(admin = Depends(requiere_rol(["Administrador"]))): ...

    Parámetros:
        roles_permitidos: nombres de rol autorizados, tal como figuran en la
                          columna `rol.nombre` (ej: ["Administrador"]).

    Retorna:
        Callable: dependencia que devuelve los datos del usuario si su rol está
                  autorizado.

    Errores:
        HTTP 401: propagado por `get_current_user` si no hay sesión válida.
        HTTP 403: el usuario está autenticado pero su rol no está en la lista.
                  Se distingue del 401 a propósito: el interceptor de Angular
                  solo cierra la sesión ante un 401, y una sesión válida sin
                  permisos no debe expulsar al usuario del sistema.
    """
    def verificador_de_rol(
        usuario: dict[str, Any] = Depends(get_current_user),
    ) -> dict[str, Any]:
        """Comprueba el rol del usuario autenticado contra la lista permitida.

        Parámetros:
            usuario: datos del usuario resueltos por `get_current_user`.

        Retorna:
            dict: los mismos datos del usuario, si su rol está autorizado.
        """
        if usuario.get("rol") not in roles_permitidos:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para realizar esta acción",
            )
        return usuario

    return verificador_de_rol


def requiere_permiso(codigo_permiso: str):
    """Construye una dependencia que verifica un permiso granular (RBAC - CU03).

    Si el usuario tiene el rol 'Administrador', se concede acceso inmediato
    (bypass omnipotente). Para otros roles, consulta la base de datos verificando
    que el `id_role` del usuario tenga asignado el permiso con el `codigo_permiso`.

    Parámetros:
        codigo_permiso: código único del permiso (ej. "roles.asignar", "usuarios.ver").

    Retorna:
        Callable: dependencia de FastAPI que devuelve los datos del usuario autenticado.

    Errores:
        HTTP 401: no autenticado o sesión vencida (propagado por `get_current_user`).
        HTTP 403: usuario sin rol asignado o sin el permiso solicitado.
    """
    def verificador_permiso(
        usuario: dict[str, Any] = Depends(get_current_user),
        cursor=Depends(get_db),
    ) -> dict[str, Any]:
        # El rol 'Administrador' posee omnipotencia en FashionStore
        if usuario.get("rol") == "Administrador":
            return usuario

        id_rol = usuario.get("id_role")
        if not id_rol:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="El usuario no tiene un rol asignado",
            )

        cursor.execute(
            """
            SELECT 1 
            FROM rol_permiso rp
            JOIN permiso p ON rp.id_permiso = p.id_permiso
            WHERE rp.id_rol = %s AND p.codigo = %s;
            """,
            (id_rol, codigo_permiso),
        )
        if cursor.fetchone() is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"No tiene el permiso requerido para esta acción ({codigo_permiso})",
            )

        return usuario

    return verificador_permiso

