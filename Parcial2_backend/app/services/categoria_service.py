"""
=============================================================================
FASHIONSTORE - SERVICIO DE CATEGORÍAS DE PRENDAS (CU07)
Sistemas de Información II - UAGRM
-----------------------------------------------------------------------------
SQL de la clasificación jerárquica del catálogo. La tabla `categoria` se une
consigo misma para resolver el nombre de la categoría padre.
=============================================================================
"""

from typing import Any

# El LEFT JOIN de la tabla contra sí misma (alias p) resuelve el nombre del
# padre; el subselect cuenta cuántas prendas activas cuelgan de la categoría,
# dato que el frontend usa para advertir antes de inhabilitarla.
_SELECT_CATEGORIA = """
    SELECT  c.id_categoria,
            c.nombre,
            c.descripcion,
            c.id_categoria_padre,
            p.nombre AS categoria_padre,
            c.estado,
            (SELECT COUNT(*)::int FROM prenda pr
              WHERE pr.id_categoria = c.id_categoria) AS total_prendas
    FROM categoria c
    LEFT JOIN categoria p ON c.id_categoria_padre = p.id_categoria
"""


def listar_categorias(cursor, estado: str | None = None) -> list[dict[str, Any]]:
    """Devuelve el árbol de categorías.

    El orden coloca primero las raíces y después sus hijas, de modo que el
    frontend puede dibujar la jerarquía recorriendo la lista una sola vez.

    Parámetros:
        cursor: cursor de PostgreSQL.
        estado: 'Activo' o 'Inactivo' para acotar el listado.

    Retorna:
        list[dict]: categorías con su padre y su conteo de prendas.
    """
    sql = _SELECT_CATEGORIA
    valores: tuple = ()

    if estado:
        sql += " WHERE c.estado = %s"
        valores = (estado,)

    # NULLS FIRST agrupa las categorías raíz al principio del listado.
    sql += " ORDER BY c.id_categoria_padre NULLS FIRST, c.nombre;"

    cursor.execute(sql, valores)
    return [dict(f) for f in cursor.fetchall()]


def obtener_categoria(cursor, id_categoria: int) -> dict[str, Any] | None:
    """Recupera una categoría concreta.

    Parámetros:
        cursor: cursor de PostgreSQL.
        id_categoria: clave primaria buscada.

    Retorna:
        dict | None: la categoría, o None si no existe.
    """
    cursor.execute(_SELECT_CATEGORIA + " WHERE c.id_categoria = %s;", (id_categoria,))
    fila = cursor.fetchone()
    return dict(fila) if fila else None


def existe_nombre(cursor, nombre: str, excluir_id: int | None = None) -> bool:
    """Comprueba si el nombre de categoría ya está en uso.

    La columna es UNIQUE; validarlo antes permite devolver un mensaje legible
    en vez de dejar estallar la restricción de la base.

    Parámetros:
        cursor: cursor de PostgreSQL.
        nombre: nombre a comprobar.
        excluir_id: categoría que se está editando (conserva su propio nombre).

    Retorna:
        bool: True si el nombre pertenece a otra categoría.
    """
    if excluir_id is None:
        cursor.execute(
            "SELECT 1 FROM categoria WHERE LOWER(nombre) = LOWER(%s);", (nombre,)
        )
    else:
        cursor.execute(
            "SELECT 1 FROM categoria WHERE LOWER(nombre) = LOWER(%s) AND id_categoria <> %s;",
            (nombre, excluir_id),
        )
    return cursor.fetchone() is not None


def existe_categoria(cursor, id_categoria: int) -> bool:
    """Verifica que una categoría exista (usado al validar el padre y en CU08).

    Parámetros:
        cursor: cursor de PostgreSQL.
        id_categoria: identificador a comprobar.

    Retorna:
        bool: True si existe.
    """
    cursor.execute(
        "SELECT 1 FROM categoria WHERE id_categoria = %s;", (id_categoria,)
    )
    return cursor.fetchone() is not None


def crear_categoria(cursor, datos: dict[str, Any]) -> int:
    """Inserta una categoría y devuelve su identificador.

    Parámetros:
        cursor: cursor de PostgreSQL.
        datos: nombre, descripcion e id_categoria_padre.

    Retorna:
        int: id_categoria de la fila creada.
    """
    cursor.execute(
        """
        INSERT INTO categoria (nombre, descripcion, id_categoria_padre)
        VALUES (%s, %s, %s)
        RETURNING id_categoria;
        """,
        (datos["nombre"], datos.get("descripcion"), datos.get("id_categoria_padre")),
    )
    return cursor.fetchone()["id_categoria"]


def actualizar_categoria(cursor, id_categoria: int, cambios: dict[str, Any]) -> None:
    """Aplica una actualización parcial sobre una categoría.

    Parámetros:
        cursor: cursor de PostgreSQL.
        id_categoria: categoría a modificar.
        cambios: columnas a actualizar.

    Retorna:
        None
    """
    columnas = [f"{col} = %s" for col in cambios]
    valores = list(cambios.values())
    valores.append(id_categoria)

    cursor.execute(
        f"UPDATE categoria SET {', '.join(columnas)} WHERE id_categoria = %s;",
        tuple(valores),
    )


def inhabilitar_categoria(cursor, id_categoria: int) -> None:
    """Da de baja lógica a una categoría.

    No se borra físicamente porque `prenda.id_categoria` la referencia con
    ON DELETE RESTRICT: un DELETE fallaría en cuanto exista una sola prenda
    clasificada en ella.

    Parámetros:
        cursor: cursor de PostgreSQL.
        id_categoria: categoría a inhabilitar.

    Retorna:
        None
    """
    cursor.execute(
        "UPDATE categoria SET estado = 'Inactivo' WHERE id_categoria = %s;",
        (id_categoria,),
    )


def tiene_subcategorias(cursor, id_categoria: int) -> bool:
    """Indica si una categoría tiene hijas colgando de ella.

    Se comprueba antes de inhabilitarla: dejar subcategorías activas bajo una
    categoría inactiva produciría un árbol incoherente en el catálogo.

    Parámetros:
        cursor: cursor de PostgreSQL.
        id_categoria: categoría a comprobar.

    Retorna:
        bool: True si tiene al menos una subcategoría activa.
    """
    cursor.execute(
        """
        SELECT 1 FROM categoria
        WHERE id_categoria_padre = %s AND estado = 'Activo'
        LIMIT 1;
        """,
        (id_categoria,),
    )
    return cursor.fetchone() is not None
