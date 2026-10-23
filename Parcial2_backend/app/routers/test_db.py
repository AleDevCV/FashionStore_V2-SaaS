"""
=============================================================================
FASHIONSTORE - ROUTER DE DIAGNÓSTICO DE BASE DE DATOS
Sistemas de Información II - UAGRM
-----------------------------------------------------------------------------
Router temporal de infraestructura (NO corresponde a ningún Caso de Uso del
examen). Su única finalidad es comprobar que el pool de conexiones definido en
app/database.py logra conectarse al contenedor de PostgreSQL y leer las tablas
creadas por database/db_scheme.sql.

Se recomienda eliminar o proteger este router antes del despliegue final en la
nube, ya que expone información de la estructura interna de la base de datos.
=============================================================================
"""

from fastapi import APIRouter, Depends, HTTPException
from psycopg2 import Error as Psycopg2Error

from app.database import get_db

# -----------------------------------------------------------------------------
# Definición del router.
#   prefix -> todas las rutas de este archivo cuelgan de /api/test-db
#   tags   -> agrupa los endpoints bajo un título propio en el Swagger (/docs)
# -----------------------------------------------------------------------------
router = APIRouter(
    prefix="/api/test-db",
    tags=["Diagnóstico de Base de Datos"],
)


@router.get("/", summary="Verificar la conexión con PostgreSQL")
def verificar_conexion(cursor=Depends(get_db)):
    """Comprueba que la API se conecta al contenedor de PostgreSQL.

    Ejecuta tres consultas de diagnóstico: la versión del motor, la base de
    datos y usuario activos, y el número de filas de la tabla `usuario`. Si las
    tres responden, el pool de conexiones de app/database.py está operativo y
    el script db_scheme.sql se ejecutó correctamente al levantar el contenedor.

    Parámetros:
        cursor: cursor de PostgreSQL inyectado por la dependencia `get_db`.
                Devuelve las filas como diccionarios (RealDictCursor).

    Retorna:
        dict: estado de la conexión, versión del motor, base de datos, usuario
              conectado y cantidad de registros en la tabla `usuario`.

    Errores:
        HTTP 500: si el motor rechaza la conexión o la tabla `usuario` no existe
                  (señal de que el script db_scheme.sql no llegó a ejecutarse).
    """
    try:
        # 1) Versión del motor: confirma que efectivamente es PostgreSQL 16.
        cursor.execute("SELECT version() AS version;")
        version = cursor.fetchone()["version"]

        # 2) Base de datos y usuario con los que la API quedó autenticada.
        cursor.execute(
            "SELECT current_database() AS base_datos, current_user AS usuario_conectado;"
        )
        conexion = cursor.fetchone()

        # 3) Conteo de la tabla `usuario`: valida que los seeders corrieron.
        cursor.execute("SELECT COUNT(*) AS total FROM usuario;")
        total_usuarios = cursor.fetchone()["total"]

        return {
            "estado": "conexion_exitosa",
            "mensaje": "El pool de conexiones se comunica correctamente con PostgreSQL.",
            "motor": version.split(",")[0],
            "base_datos": conexion["base_datos"],
            "usuario_conectado": conexion["usuario_conectado"],
            "total_usuarios_registrados": total_usuarios,
        }

    except Psycopg2Error as error:
        # Se captura el error de psycopg2 y se traduce a una respuesta HTTP
        # legible, en lugar de dejar que FastAPI devuelva un stacktrace crudo.
        raise HTTPException(
            status_code=500,
            detail=f"Fallo la conexion con PostgreSQL: {error}",
        )


@router.get("/usuarios", summary="Listar usuarios registrados en la BD")
def listar_usuarios(cursor=Depends(get_db)):
    """Devuelve los usuarios de la tabla `usuario` junto con su rol.

    Consulta de prueba de lectura real sobre el esquema: cruza `usuario` con
    `rol` mediante la clave foránea `id_role` para confirmar que las relaciones
    del script db_scheme.sql quedaron bien construidas.

    IMPORTANTE: la columna `password_hash` se excluye deliberadamente del SELECT
    para no exponer los hashes bcrypt en la respuesta HTTP (RNF01 - Seguridad).

    Parámetros:
        cursor: cursor de PostgreSQL inyectado por la dependencia `get_db`.

    Retorna:
        dict: cantidad de usuarios encontrados y la lista de sus datos públicos
              (id, nombre, apellido, correo, teléfono, estado y nombre del rol).

    Errores:
        HTTP 500: si la consulta falla o las tablas `usuario`/`rol` no existen.
    """
    try:
        # LEFT JOIN para que un usuario sin rol asignado siga apareciendo en la
        # lista en lugar de desaparecer del resultado.
        cursor.execute(
            """
            SELECT  u.id_usuario,
                    u.nombre,
                    u.apellido,
                    u.correo,
                    u.telefono,
                    u.estado,
                    r.nombre AS rol
            FROM usuario u
            LEFT JOIN rol r ON u.id_role = r.id_rol
            ORDER BY u.id_usuario;
            """
        )
        usuarios = cursor.fetchall()

        return {
            "estado": "consulta_exitosa",
            "total": len(usuarios),
            # fetchall() con RealDictCursor devuelve RealDictRow; se convierten a
            # dict plano para que FastAPI los serialice a JSON sin problemas.
            "usuarios": [dict(fila) for fila in usuarios],
        }

    except Psycopg2Error as error:
        raise HTTPException(
            status_code=500,
            detail=f"No se pudo consultar la tabla usuario: {error}",
        )


@router.get("/tablas", summary="Listar las tablas creadas por db_scheme.sql")
def listar_tablas(cursor=Depends(get_db)):
    """Enumera las tablas del esquema `public` de la base de datos.

    Sirve para verificar de un vistazo que las 27 tablas del script
    db_scheme.sql se crearon al inicializar el contenedor de PostgreSQL.

    Parámetros:
        cursor: cursor de PostgreSQL inyectado por la dependencia `get_db`.

    Retorna:
        dict: cantidad de tablas y sus nombres en orden alfabético.

    Errores:
        HTTP 500: si no se puede leer el catálogo de sistema information_schema.
    """
    try:
        cursor.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_type = 'BASE TABLE'
            ORDER BY table_name;
            """
        )
        tablas = [fila["table_name"] for fila in cursor.fetchall()]

        return {
            "estado": "consulta_exitosa",
            "total_tablas": len(tablas),
            "tablas": tablas,
        }

    except Psycopg2Error as error:
        raise HTTPException(
            status_code=500,
            detail=f"No se pudo leer el esquema de la base de datos: {error}",
        )
