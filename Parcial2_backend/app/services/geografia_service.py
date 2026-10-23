"""
=============================================================================
FASHIONSTORE - SERVICIO DE CIUDADES Y SUCURSALES (CU06)
Sistemas de Información II - UAGRM
-----------------------------------------------------------------------------
Concentra todo el SQL del módulo geográfico. Los routers quedan como una capa
delgada que solo valida permisos y traduce errores a códigos HTTP.

Todas las consultas son parametrizadas (%s): los valores viajan aparte de la
sentencia, de modo que no existe superficie de inyección SQL.
=============================================================================
"""

from typing import Any


# -----------------------------------------------------------------------------
# CIUDADES
# -----------------------------------------------------------------------------

def listar_ciudades(cursor) -> list[dict[str, Any]]:
    """Devuelve todas las ciudades con su número de sucursales.

    El LEFT JOIN con `sucursal` permite que una ciudad recién creada, todavía
    sin tiendas, aparezca en el listado con total_sucursales = 0.

    Parámetros:
        cursor: cursor de PostgreSQL inyectado por `get_db`.

    Retorna:
        list[dict]: ciudades ordenadas alfabéticamente.
    """
    cursor.execute(
        """
        SELECT  c.id_ciudad,
                c.nombre,
                COUNT(s.id_sucursal)::int AS total_sucursales
        FROM ciudad c
        LEFT JOIN sucursal s ON s.id_ciudad = c.id_ciudad
        GROUP BY c.id_ciudad, c.nombre
        ORDER BY c.nombre;
        """
    )
    return [dict(f) for f in cursor.fetchall()]


def existe_ciudad_por_nombre(cursor, nombre: str) -> bool:
    """Comprueba si ya hay una ciudad registrada con ese nombre.

    Se consulta antes del INSERT para devolver un mensaje claro en lugar de
    dejar que estalle la restricción UNIQUE de la tabla.

    Parámetros:
        cursor: cursor de PostgreSQL.
        nombre: nombre a comprobar (comparación insensible a mayúsculas).

    Retorna:
        bool: True si el nombre ya está en uso.
    """
    cursor.execute(
        "SELECT 1 FROM ciudad WHERE LOWER(nombre) = LOWER(%s);", (nombre,)
    )
    return cursor.fetchone() is not None


def crear_ciudad(cursor, nombre: str) -> dict[str, Any]:
    """Inserta una ciudad y devuelve la fila creada.

    Parámetros:
        cursor: cursor de PostgreSQL.
        nombre: nombre de la ciudad.

    Retorna:
        dict: la ciudad recién creada, con total_sucursales en 0.
    """
    cursor.execute(
        "INSERT INTO ciudad (nombre) VALUES (%s) RETURNING id_ciudad, nombre;",
        (nombre,),
    )
    fila = dict(cursor.fetchone())
    fila["total_sucursales"] = 0
    return fila


def existe_ciudad(cursor, id_ciudad: int) -> bool:
    """Verifica que una ciudad exista antes de asociarle una sucursal.

    Parámetros:
        cursor: cursor de PostgreSQL.
        id_ciudad: identificador a comprobar.

    Retorna:
        bool: True si la ciudad existe.
    """
    cursor.execute("SELECT 1 FROM ciudad WHERE id_ciudad = %s;", (id_ciudad,))
    return cursor.fetchone() is not None


# -----------------------------------------------------------------------------
# SUCURSALES
# -----------------------------------------------------------------------------

# Proyección compartida por todas las lecturas de sucursal. Se define una sola
# vez para que los tres endpoints devuelvan exactamente las mismas columnas.
_SELECT_SUCURSAL = """
    SELECT  s.id_sucursal,
            s.nombre,
            s.direccion,
            s.telefono,
            s.id_ciudad,
            c.nombre AS ciudad,
            s.id_encargado,
            CASE WHEN u.id_usuario IS NULL THEN NULL
                 ELSE u.nombre || ' ' || u.apellido END AS encargado,
            s.created_at
    FROM sucursal s
    LEFT JOIN ciudad c ON s.id_ciudad = c.id_ciudad
    LEFT JOIN usuario u ON s.id_encargado = u.id_usuario
"""


def listar_sucursales(cursor, id_ciudad: int | None = None) -> list[dict[str, Any]]:
    """Devuelve las sucursales, opcionalmente filtradas por ciudad.

    Parámetros:
        cursor: cursor de PostgreSQL.
        id_ciudad: si se indica, limita el resultado a esa ciudad.

    Retorna:
        list[dict]: sucursales con ciudad y encargado resueltos.
    """
    if id_ciudad is not None:
        cursor.execute(
            _SELECT_SUCURSAL + " WHERE s.id_ciudad = %s ORDER BY s.nombre;",
            (id_ciudad,),
        )
    else:
        cursor.execute(_SELECT_SUCURSAL + " ORDER BY c.nombre, s.nombre;")

    return [dict(f) for f in cursor.fetchall()]


def obtener_sucursal(cursor, id_sucursal: int) -> dict[str, Any] | None:
    """Recupera una sucursal concreta.

    Parámetros:
        cursor: cursor de PostgreSQL.
        id_sucursal: clave primaria buscada.

    Retorna:
        dict | None: la sucursal, o None si no existe.
    """
    cursor.execute(_SELECT_SUCURSAL + " WHERE s.id_sucursal = %s;", (id_sucursal,))
    fila = cursor.fetchone()
    return dict(fila) if fila else None


def crear_sucursal(cursor, datos: dict[str, Any]) -> int:
    """Inserta una sucursal y devuelve su identificador.

    Parámetros:
        cursor: cursor de PostgreSQL.
        datos: diccionario con nombre, direccion, telefono, id_ciudad e
               id_encargado.

    Retorna:
        int: id_sucursal de la fila creada.
    """
    cursor.execute(
        """
        INSERT INTO sucursal (nombre, direccion, telefono, id_ciudad, id_encargado)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id_sucursal;
        """,
        (
            datos["nombre"],
            datos["direccion"],
            datos.get("telefono"),
            datos["id_ciudad"],
            datos.get("id_encargado"),
        ),
    )
    return cursor.fetchone()["id_sucursal"]


def actualizar_sucursal(cursor, id_sucursal: int, cambios: dict[str, Any]) -> None:
    """Aplica una actualización parcial sobre una sucursal.

    La cláusula SET se arma dinámicamente a partir de las claves recibidas.
    Los NOMBRES de columna provienen del modelo de Pydantic (nunca de texto
    libre del usuario) y los VALORES viajan como parámetros, por lo que no hay
    riesgo de inyección.

    Parámetros:
        cursor: cursor de PostgreSQL.
        id_sucursal: sucursal a modificar.
        cambios: columnas a actualizar; las omitidas quedan intactas.

    Retorna:
        None
    """
    columnas = [f"{col} = %s" for col in cambios]
    valores = list(cambios.values())

    # La tabla solo tiene DEFAULT para el alta, sin trigger de actualización.
    columnas.append("updated_at = CURRENT_TIMESTAMP")
    valores.append(id_sucursal)

    cursor.execute(
        f"UPDATE sucursal SET {', '.join(columnas)} WHERE id_sucursal = %s;",
        tuple(valores),
    )
