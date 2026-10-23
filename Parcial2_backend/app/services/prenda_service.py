"""
=============================================================================
FASHIONSTORE - SERVICIO DE PRENDAS Y VARIANTES (CU08)
Sistemas de Información II - UAGRM
-----------------------------------------------------------------------------
SQL del catálogo maestro. Es el módulo con la lógica transaccional más densa:
dar de alta una prenda toca CUATRO tablas en una sola transacción.

    prenda           -> el diseño maestro
    imagen_prenda    -> la fotografía principal
    variante_prenda  -> una fila por combinación talla + color
    inventario       -> una fila por (variante, sucursal) con su stock inicial

Todo ocurre bajo la transacción que abre `get_db`: si cualquier paso falla, se
revierte el conjunto y no queda una prenda a medio crear.
=============================================================================
"""

from typing import Any

# Proyección maestra de prenda. `stock_total` se calcula con un subselect que
# suma el inventario de todas las variantes en todas las sucursales.
_SELECT_PRENDA = """
    SELECT  p.id_prenda,
            p.sku,
            p.nombre,
            p.descripcion,
            p.marca,
            p.genero,
            p.admite_cambio, p.precio_base, p.material, p.medidas, p.precio_mayorista, p.umbral_mayorista, p.precio_oferta, p.oferta_inicio, p.oferta_fin,
            p.id_categoria,
            c.nombre AS categoria,
            p.id_temporada,
            t.nombre AS nombre_temporada,
            t.nombre AS temporada,
            p.estado,
            p.created_at,
            (SELECT i.url_imagen FROM imagen_prenda i
              WHERE i.id_prenda = p.id_prenda
              ORDER BY i.es_principal DESC, i.id_imagen
              LIMIT 1) AS url_imagen,
            COALESCE((
                SELECT SUM(inv.stock)::int
                FROM variante_prenda v
                JOIN inventario inv ON inv.id_variante_prenda = v.id_variante_prenda
                WHERE v.id_prenda = p.id_prenda
            ), 0) AS stock_total
    FROM prenda p
    LEFT JOIN categoria c ON p.id_categoria = c.id_categoria
    LEFT JOIN temporada t ON p.id_temporada = t.id_temporada
"""


# -----------------------------------------------------------------------------
# LECTURA
# -----------------------------------------------------------------------------

def listar_prendas(
    cursor,
    busqueda: str | None = None,
    id_categoria: int | None = None,
    genero: str | None = None,
    estado: str | None = None,
    id_temporada: int | None = None,
) -> list[dict[str, Any]]:
    """Devuelve las prendas del catálogo con sus filtros administrativos.

    Parámetros:
        cursor: cursor de PostgreSQL.
        busqueda: texto libre sobre el SKU o el nombre de la prenda.
        id_categoria: acota a una categoría concreta.
        genero: acota al público objetivo.
        estado: 'Activo', 'Inactivo' o 'Borrador'.
        id_temporada: acota a una temporada comercial concreta.

    Retorna:
        list[dict]: prendas SIN sus variantes. El detalle con variantes se
                    obtiene con `obtener_prenda`, para no disparar una consulta
                    por fila al pintar la tabla.
    """
    condiciones: list[str] = []
    valores: list[Any] = []

    if busqueda:
        condiciones.append("(p.sku ILIKE %s OR p.nombre ILIKE %s)")
        patron = f"%{busqueda}%"
        valores.extend([patron, patron])

    if id_categoria:
        condiciones.append("p.id_categoria = %s")
        valores.append(id_categoria)

    if genero:
        condiciones.append("p.genero = %s")
        valores.append(genero)

    if estado:
        condiciones.append("p.estado = %s")
        valores.append(estado)

    if id_temporada:
        condiciones.append("p.id_temporada = %s")
        valores.append(id_temporada)

    sql = _SELECT_PRENDA
    if condiciones:
        sql += " WHERE " + " AND ".join(condiciones)
    sql += " ORDER BY p.created_at DESC, p.id_prenda DESC;"

    cursor.execute(sql, tuple(valores))
    return [dict(f) for f in cursor.fetchall()]


def obtener_prenda(cursor, id_prenda: int, con_variantes: bool = True) -> dict | None:
    """Recupera una prenda y, opcionalmente, sus variantes.

    Parámetros:
        cursor: cursor de PostgreSQL.
        id_prenda: clave primaria buscada.
        con_variantes: si es True, adjunta la lista de combinaciones físicas.

    Retorna:
        dict | None: la prenda, o None si no existe.
    """
    cursor.execute(_SELECT_PRENDA + " WHERE p.id_prenda = %s;", (id_prenda,))
    fila = cursor.fetchone()

    if fila is None:
        return None

    prenda = dict(fila)
    prenda["variantes"] = listar_variantes(cursor, id_prenda) if con_variantes else []
    return prenda


def listar_variantes(cursor, id_prenda: int) -> list[dict[str, Any]]:
    """Devuelve las variantes de una prenda con su stock consolidado.

    El LEFT JOIN con `inventario` es deliberado: una variante recién creada en
    una instalación sin sucursales no tendría filas de inventario y, con un
    JOIN normal, desaparecería del resultado.

    Parámetros:
        cursor: cursor de PostgreSQL.
        id_prenda: prenda cuyas variantes se listan.

    Retorna:
        list[dict]: variantes con talla, color y stock_total.
    """
    cursor.execute(
        """
        SELECT  v.id_variante_prenda,
                v.id_talla,
                t.nombre AS talla,
                v.id_color, v.color_ids,
                variant_color_label(v.id_variante_prenda) AS color,
                col.codigo_hex,
                v.sku_variante,
                v.precio_adicional,
                COALESCE(SUM(inv.stock), 0)::int AS stock_total
        FROM variante_prenda v
        LEFT JOIN talla t ON v.id_talla = t.id_talla
        LEFT JOIN color col ON v.id_color = col.id_color
        LEFT JOIN inventario inv ON inv.id_variante_prenda = v.id_variante_prenda
        WHERE v.id_prenda = %s
        GROUP BY v.id_variante_prenda, v.id_talla, t.nombre,
                 v.id_color, col.nombre, col.codigo_hex,
                 v.sku_variante, v.precio_adicional
        -- Se ordena por v.id_talla y no por t.id_talla: al haber GROUP BY,
        -- PostgreSQL solo admite en ORDER BY columnas agrupadas o agregadas.
        ORDER BY v.id_talla, col.nombre;
        """,
        (id_prenda,),
    )
    return [dict(f) for f in cursor.fetchall()]


def existe_sku(cursor, sku: str, excluir_id: int | None = None) -> bool:
    """Comprueba si un SKU maestro ya está en uso.

    Parámetros:
        cursor: cursor de PostgreSQL.
        sku: código a comprobar.
        excluir_id: prenda que se está editando (conserva su propio SKU).

    Retorna:
        bool: True si el SKU pertenece a otra prenda.
    """
    if excluir_id is None:
        cursor.execute("SELECT 1 FROM prenda WHERE sku = %s;", (sku,))
    else:
        cursor.execute(
            "SELECT 1 FROM prenda WHERE sku = %s AND id_prenda <> %s;",
            (sku, excluir_id),
        )
    return cursor.fetchone() is not None


def existe_temporada(cursor, id_temporada: int) -> bool:
    """Comprueba si una temporada existe en el catálogo maestro.

    Parámetros:
        cursor: cursor de PostgreSQL.
        id_temporada: identificador de la temporada a verificar.

    Retorna:
        bool: True si la temporada existe.
    """
    cursor.execute("SELECT 1 FROM temporada WHERE id_temporada = %s;", (id_temporada,))
    return cursor.fetchone() is not None


# -----------------------------------------------------------------------------
# ESCRITURA
# -----------------------------------------------------------------------------

def crear_prenda(cursor, datos: dict[str, Any]) -> int:
    """Da de alta una prenda completa en una única transacción.

    Secuencia:
      1. INSERT en `prenda` con los datos maestros (incluyendo id_temporada opcional).
      2. INSERT en `imagen_prenda` si se envió una URL de fotografía.
      3. Por cada variante recibida:
           a. INSERT en `variante_prenda` con un SKU de variante derivado.
           b. INSERT en `inventario` con su stock inicial, para CADA sucursal
              registrada en el sistema.

    IMPORTANTE SOBRE EL STOCK: `stock_inicial` se aplica A CADA SUCURSAL, no se
    reparte entre ellas. Con dos sucursales y stock_inicial = 10, el stock
    consolidado de esa variante será 20. Es la lectura más predecible para el
    administrador y evita repartos con decimales.

    Parámetros:
        cursor: cursor de PostgreSQL.
        datos: cuerpo validado del endpoint POST /api/prendas.

    Retorna:
        int: id_prenda de la prenda creada.
    """
    # --- 1. Prenda maestra ---------------------------------------------------
    cursor.execute(
        """
        INSERT INTO prenda
            (sku, nombre, descripcion, marca, genero, precio_base, id_categoria, id_temporada)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id_prenda;
        """,
        (
            datos["sku"],
            datos["nombre"],
            datos.get("descripcion"),
            datos.get("marca") or "FashionStore",
            datos.get("genero") or "Unisex",
            datos["precio_base"],
            datos["id_categoria"],
            datos.get("id_temporada"),
        ),
    )
    id_prenda = cursor.fetchone()["id_prenda"]
    commercial = {k: datos[k] for k in ('admite_cambio','material','medidas','precio_mayorista','umbral_mayorista','precio_oferta','oferta_inicio','oferta_fin') if datos.get(k) is not None}
    if commercial:
        from psycopg2 import sql
        query = sql.SQL('UPDATE prenda SET {} WHERE id_prenda=%s').format(sql.SQL(',').join(sql.SQL('{}=%s').format(sql.Identifier(k)) for k in commercial))
        cursor.execute(query, [*commercial.values(), id_prenda])


    # --- 2. Fotografía principal --------------------------------------------
    if datos.get("url_imagen"):
        cursor.execute(
            """
            INSERT INTO imagen_prenda (id_prenda, url_imagen, es_principal)
            VALUES (%s, %s, TRUE);
            """,
            (id_prenda, datos["url_imagen"]),
        )

    # --- 3. Variantes e inventario ------------------------------------------
    # Se leen las sucursales UNA sola vez fuera del bucle, en lugar de repetir
    # la consulta por cada variante.
    sucursales = _listar_ids_sucursales(cursor)

    for variante in datos.get("variantes", []):
        _crear_variante(cursor, id_prenda, datos["sku"], variante, sucursales)

    return id_prenda


def _crear_variante(
    cursor,
    id_prenda: int,
    sku_prenda: str,
    variante: dict[str, Any],
    sucursales: list[int],
) -> int:
    """Inserta una variante física y su inventario inicial.

    El SKU de variante se deriva del SKU maestro más los identificadores de
    talla y color (ej: CHQ-JEAN-001-T2-C1). Como la tabla ya declara UNIQUE
    sobre (id_prenda, id_talla, id_color), esta composición no puede colisionar.

    Parámetros:
        cursor: cursor de PostgreSQL.
        id_prenda: prenda propietaria.
        sku_prenda: SKU maestro, base del SKU de variante.
        variante: id_talla, id_color, stock_inicial y precio_adicional.
        sucursales: identificadores de todas las sucursales registradas.

    Retorna:
        int: id_variante_prenda creado.
    """
    colors=sorted(set([variante['id_color'],*variante.get('color_ids',[])]))
    sku_variante=f"{sku_prenda}-T{variante['id_talla']}-C"+'-'.join(str(c) for c in colors)

    cursor.execute(
        """
        INSERT INTO variante_prenda
            (id_prenda, id_talla, id_color, sku_variante, precio_adicional, color_ids)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id_variante_prenda;
        """,
        (
            id_prenda,
            variante["id_talla"],
            variante["id_color"],
            sku_variante,
            variante.get("precio_adicional", 0), colors,
        ),
    )
    id_variante = cursor.fetchone()["id_variante_prenda"]

    # Inventario inicial en cada sucursal existente. ON CONFLICT protege ante
    # una hipotética repetición de la clave compuesta (id_sucursal, id_variante).
    stock = int(variante.get("stock_inicial", 0) or 0)
    for id_sucursal in sucursales:
        cursor.execute(
            """
            INSERT INTO inventario (id_sucursal, id_variante_prenda, stock)
            VALUES (%s, %s, %s)
            ON CONFLICT (id_sucursal, id_variante_prenda) DO NOTHING;
            """,
            (id_sucursal, id_variante, 0),
        )

        if stock>0:
            from app.tenant import require_context
            cursor.execute("INSERT INTO movimiento_inventario(id_sucursal,id_variante_prenda,tipo,cantidad,motivo,id_usuario) VALUES(%s,%s,'Entrada',%s,'Existencia inicial de variante',%s)",(id_sucursal,id_variante,stock,require_context().user_id))
    return id_variante


def _listar_ids_sucursales(cursor) -> list[int]:
    """Devuelve los identificadores de todas las sucursales registradas.

    Parámetros:
        cursor: cursor de PostgreSQL.

    Retorna:
        list[int]: ids de sucursal; lista vacía si aún no hay ninguna.
    """
    cursor.execute("SELECT id_sucursal FROM sucursal WHERE activa AND branch_visible(id_sucursal) ORDER BY id_sucursal;")
    return [f["id_sucursal"] for f in cursor.fetchall()]


def actualizar_prenda(cursor, id_prenda: int, cambios: dict[str, Any]) -> None:
    """Aplica una actualización parcial sobre los datos maestros de la prenda.

    La URL de imagen se trata aparte porque no es una columna de `prenda`, sino
    una fila de `imagen_prenda`.

    Parámetros:
        cursor: cursor de PostgreSQL.
        id_prenda: prenda a modificar.
        cambios: columnas a actualizar.

    Retorna:
        None
    """
    # La imagen se extrae del diccionario para no intentar escribirla como
    # columna inexistente de `prenda`.
    url_imagen = cambios.pop("url_imagen", None)

    if cambios:
        columnas = [f"{col} = %s" for col in cambios]
        valores = list(cambios.values())
        columnas.append("updated_at = CURRENT_TIMESTAMP")
        valores.append(id_prenda)

        cursor.execute(
            f"UPDATE prenda SET {', '.join(columnas)} WHERE id_prenda = %s;",
            tuple(valores),
        )

    if url_imagen is not None:
        _reemplazar_imagen_principal(cursor, id_prenda, url_imagen)


def _reemplazar_imagen_principal(cursor, id_prenda: int, url_imagen: str) -> None:
    """Sustituye la fotografía principal de una prenda.

    Se degradan las imágenes anteriores a secundarias en lugar de borrarlas,
    de modo que el historial de fotos del diseño se conserva.

    Parámetros:
        cursor: cursor de PostgreSQL.
        id_prenda: prenda afectada.
        url_imagen: nueva URL principal.

    Retorna:
        None
    """
    cursor.execute(
        """
        SELECT url_imagen
        FROM imagen_prenda
        WHERE id_prenda = %s AND es_principal = TRUE
        ORDER BY id_imagen
        LIMIT 1;
        """,
        (id_prenda,),
    )
    imagen_actual = cursor.fetchone()
    if imagen_actual and imagen_actual["url_imagen"] == url_imagen:
        return

    cursor.execute(
        "UPDATE imagen_prenda SET es_principal = FALSE WHERE id_prenda = %s;",
        (id_prenda,),
    )
    cursor.execute(
        """
        INSERT INTO imagen_prenda (id_prenda, url_imagen, es_principal)
        VALUES (%s, %s, TRUE);
        """,
        (id_prenda, url_imagen),
    )


def inhabilitar_prenda(cursor, id_prenda: int) -> None:
    """Retira una prenda del catálogo mediante baja lógica.

    No se borra físicamente: `variante_prenda` cuelga de ella en CASCADE y esas
    variantes están referenciadas por `inventario`, `detalle_venta` y
    `detalle_reserva` con ON DELETE RESTRICT. Un DELETE destruiría el historial
    comercial o fallaría.

    Parámetros:
        cursor: cursor de PostgreSQL.
        id_prenda: prenda a retirar.

    Retorna:
        None
    """
    cursor.execute(
        """
        UPDATE prenda
        SET estado = 'Inactivo', updated_at = CURRENT_TIMESTAMP
        WHERE id_prenda = %s;
        """,
        (id_prenda,),
    )


def listar_tallas(cursor) -> list[dict[str, Any]]:
    """Devuelve el catálogo de tallas para poblar el formulario del CU08.

    Parámetros:
        cursor: cursor de PostgreSQL.

    Retorna:
        list[dict]: tallas ordenadas por identificador.
    """
    cursor.execute(
        "SELECT id_talla, nombre, descripcion FROM talla ORDER BY id_talla;"
    )
    return [dict(f) for f in cursor.fetchall()]


def listar_colores(cursor) -> list[dict[str, Any]]:
    """Devuelve el catálogo de colores para poblar el formulario del CU08.

    Parámetros:
        cursor: cursor de PostgreSQL.

    Retorna:
        list[dict]: colores con su código hexadecimal.
    """
    cursor.execute(
        "SELECT id_color, nombre, codigo_hex FROM color ORDER BY nombre;"
    )
    return [dict(f) for f in cursor.fetchall()]
