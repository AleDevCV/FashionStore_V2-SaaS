"""
=============================================================================
FASHIONSTORE - SERVICIO DEL CATÁLOGO PÚBLICO (CU14)
Sistemas de Información II - UAGRM
-----------------------------------------------------------------------------
Consultas de solo lectura que alimentan la vitrina del portal web y de la app
móvil, y la comprobación de disponibilidad por sucursal.

Es el único módulo que se sirve SIN token, por lo que sus consultas filtran
siempre por estado 'Activo': un cliente jamás debe ver una prenda retirada.
=============================================================================
"""

from typing import Any


def _construir_filtros(
    busqueda: str | None,
    id_categoria: int | None,
    genero: str | None,
    id_talla: int | None,
    id_color: int | None,
    precio_min: float | None,
    precio_max: float | None,
) -> tuple[list[str], list[Any]]:
    """Arma la lista de condiciones WHERE del catálogo y sus valores.

    Se centraliza aquí porque la consulta de conteo y la de datos deben aplicar
    exactamente los mismos filtros; duplicar la lógica haría que el total del
    paginador dejara de coincidir con las prendas mostradas.

    Parámetros:
        busqueda: palabra clave sobre nombre, descripción, SKU o marca.
        id_categoria: categoría exacta.
        genero: público objetivo.
        id_talla / id_color: exigen que la prenda TENGA una variante con ese
                             atributo (se resuelven con EXISTS).
        precio_min / precio_max: rango sobre `precio_base`.

    Retorna:
        tuple: (lista de condiciones SQL, lista de valores parametrizados).
    """
    # La prenda debe estar activa y su categoría también: si el administrador
    # inhabilita una categoría, sus prendas dejan de exhibirse.
    condiciones: list[str] = [
        "p.estado = 'Activo'",
        "(c.estado IS NULL OR c.estado = 'Activo')",
    ]
    valores: list[Any] = []

    if busqueda:
        condiciones.append(
            "(p.nombre ILIKE %s OR p.descripcion ILIKE %s"
            " OR p.sku ILIKE %s OR p.marca ILIKE %s)"
        )
        patron = f"%{busqueda}%"
        valores.extend([patron, patron, patron, patron])

    if id_categoria:
        condiciones.append("p.id_categoria = %s")
        valores.append(id_categoria)

    if genero:
        condiciones.append("p.genero = %s")
        valores.append(genero)

    # Un unico EXISTS obliga a que talla y color pertenezcan a la misma
    # variante. Tambien evita duplicar prendas, como ocurriria con un JOIN.
    filtros_variante: list[str] = []
    if id_talla:
        filtros_variante.append("v.id_talla = %s")
        valores.append(id_talla)
    if id_color:
        filtros_variante.append("EXISTS(SELECT 1 FROM variante_color vc WHERE vc.id_variante_prenda=v.id_variante_prenda AND vc.id_color=%s)")
        valores.append(id_color)
    if filtros_variante:
        condiciones.append(
            "EXISTS (SELECT 1 FROM variante_prenda v"
            " WHERE v.id_prenda = p.id_prenda AND "
            + " AND ".join(filtros_variante)
            + ")"
        )

    if precio_min is not None:
        condiciones.append("p.precio_base >= %s")
        valores.append(precio_min)

    if precio_max is not None:
        condiciones.append("p.precio_base <= %s")
        valores.append(precio_max)

    return condiciones, valores


def consultar_catalogo(
    cursor,
    busqueda: str | None = None,
    id_categoria: int | None = None,
    genero: str | None = None,
    id_talla: int | None = None,
    id_color: int | None = None,
    precio_min: float | None = None,
    precio_max: float | None = None,
    limite: int = 24,
    desplazamiento: int = 0,
    con_disponibilidad: bool = False,
) -> dict[str, Any]:
    """Devuelve una página del catálogo activo aplicando los filtros del CU14.

    Parámetros:
        cursor: cursor de PostgreSQL.
        busqueda, id_categoria, genero, id_talla, id_color, precio_min,
        precio_max: filtros descritos en `_construir_filtros`.
        limite: tamaño de página.
        desplazamiento: cuántas prendas saltar (paginación).
        con_disponibilidad: si es True, cada variante incluye además el
                            desglose de stock por sucursal. Se deja apagado en
                            el listado en cuadrícula porque multiplicaría las
                            consultas sin que el cliente lo esté mirando (RNF02).

    Retorna:
        dict: total, limite, desplazamiento y la lista de prendas.
    """
    condiciones, valores = _construir_filtros(
        busqueda, id_categoria, genero, id_talla, id_color, precio_min, precio_max
    )
    where = " WHERE " + " AND ".join(condiciones)

    # --- Conteo total (para el paginador del frontend) ----------------------
    cursor.execute(
        """
        SELECT COUNT(*)::int AS total
        FROM prenda p
        LEFT JOIN categoria c ON p.id_categoria = c.id_categoria
        """
        + where,
        tuple(valores),
    )
    total = cursor.fetchone()["total"]

    # --- Página de resultados -----------------------------------------------
    cursor.execute(
        """
        SELECT  p.id_prenda,
                p.sku,
                p.nombre,
                p.descripcion,
                p.marca,
                p.genero,
                p.precio_base, p.material, p.medidas, p.precio_mayorista, p.umbral_mayorista, p.precio_oferta, p.oferta_inicio, p.oferta_fin,
                p.id_categoria,
                c.nombre AS categoria,
                (SELECT i.url_imagen FROM imagen_prenda i
                  WHERE i.id_prenda = p.id_prenda
                  ORDER BY i.es_principal DESC, i.id_imagen
                  LIMIT 1) AS url_imagen,
                COALESCE((
                    SELECT SUM(inv.stock)::int
                    FROM variante_prenda v
                    JOIN inventario_catalogo inv ON inv.id_variante_prenda = v.id_variante_prenda
                    WHERE v.id_prenda = p.id_prenda
                ), 0) AS stock_total
        FROM prenda p
        LEFT JOIN categoria c ON p.id_categoria = c.id_categoria
        """
        + where
        + " ORDER BY p.nombre LIMIT %s OFFSET %s;",
        tuple(valores + [limite, desplazamiento]),
    )
    prendas = [dict(f) for f in cursor.fetchall()]

    # --- Variantes de cada prenda de la página ------------------------------
    for prenda in prendas:
        prenda["variantes"] = listar_variantes_catalogo(
            cursor,
            prenda["id_prenda"],
            prenda["precio_base"],
            con_disponibilidad=con_disponibilidad,
            id_talla=id_talla,
            id_color=id_color,
        )

    return {
        "total": total,
        "limite": limite,
        "desplazamiento": desplazamiento,
        "prendas": prendas,
    }


def listar_variantes_catalogo(
    cursor,
    id_prenda: int,
    precio_base,
    con_disponibilidad: bool = False,
    id_talla: int | None = None,
    id_color: int | None = None,
) -> list[dict[str, Any]]:
    """Devuelve las variantes de una prenda con su precio final y su stock.

    El precio final de cada variante es `precio_base + precio_adicional`: así
    una talla XL o un color especial pueden costar más sin duplicar el diseño.

    Parámetros:
        cursor: cursor de PostgreSQL.
        id_prenda: prenda consultada.
        precio_base: precio maestro sobre el que se aplica el recargo.
        con_disponibilidad: adjunta el desglose de stock por sucursal.

    Retorna:
        list[dict]: variantes con talla, color, precio y stock.
    """
    condiciones_variante = ["v.id_prenda = %s"]
    valores_variante: list[Any] = [id_prenda]
    if id_talla:
        condiciones_variante.append("v.id_talla = %s")
        valores_variante.append(id_talla)
    if id_color:
        condiciones_variante.append("EXISTS(SELECT 1 FROM variante_color vc WHERE vc.id_variante_prenda=v.id_variante_prenda AND vc.id_color=%s)")
        valores_variante.append(id_color)

    cursor.execute(
        """
        SELECT  v.id_variante_prenda,
                v.id_talla,
                t.nombre AS talla,
                v.id_color,
                variant_color_label(v.id_variante_prenda) AS color,
                col.codigo_hex,
                v.precio_adicional,
                COALESCE(SUM(inv.stock), 0)::int AS stock_total
        FROM variante_prenda v
        LEFT JOIN talla t ON v.id_talla = t.id_talla
        LEFT JOIN color col ON v.id_color = col.id_color
        LEFT JOIN inventario_catalogo inv ON inv.id_variante_prenda = v.id_variante_prenda
        WHERE """
        + " AND ".join(condiciones_variante)
        + """
        GROUP BY v.id_variante_prenda, v.id_talla, t.nombre,
                 v.id_color, col.nombre, col.codigo_hex, v.precio_adicional
        ORDER BY v.id_talla, col.nombre;
        """,
        tuple(valores_variante),
    )

    filas_variantes=cursor.fetchall()
    from app.services.commerce import price_for
    cursor.execute('SELECT * FROM prenda WHERE id_prenda=%s',(id_prenda,));commercial=dict(cursor.fetchone())
    variantes: list[dict[str, Any]] = []

    for fila in filas_variantes:
        variante = dict(fila)
        variante["precio"] = price_for({**commercial,"precio_adicional":variante.pop("precio_adicional") or 0},1)
        variante["disponibilidad"] = []
        variantes.append(variante)

    if con_disponibilidad:
        for variante in variantes:
            variante["disponibilidad"] = consultar_disponibilidad(
                cursor, variante["id_variante_prenda"]
            )

    return variantes


def consultar_disponibilidad(cursor, id_variante_prenda: int) -> list[dict[str, Any]]:
    """Devuelve en qué sucursales hay stock de una variante concreta.

    Corresponde al paso 10 del flujo principal del CU14: el cruce entre
    `sucursal`, `inventario` y `variante_prenda` filtrando por stock > 0.

    Solo se devuelven las tiendas con existencias reales: mostrar una sucursal
    con cero unidades haría que el cliente viajara en vano.

    Parámetros:
        cursor: cursor de PostgreSQL.
        id_variante_prenda: combinación talla/color consultada.

    Retorna:
        list[dict]: sucursales con stock, su ciudad, dirección y unidades.
    """
    cursor.execute(
        """
        SELECT  s.id_sucursal,
                s.nombre AS sucursal,
                ciu.nombre AS ciudad,
                s.direccion,
                inv.stock
        FROM inventario_catalogo inv
        JOIN sucursal s ON inv.id_sucursal = s.id_sucursal
        LEFT JOIN ciudad ciu ON s.id_ciudad = ciu.id_ciudad
        WHERE inv.id_variante_prenda = %s AND inv.stock > 0
        ORDER BY ciu.nombre, s.nombre;
        """,
        (id_variante_prenda,),
    )
    return [dict(f) for f in cursor.fetchall()]


def obtener_ficha_publica(cursor, id_prenda: int) -> dict[str, Any] | None:
    """Devuelve la ficha completa de una prenda con disponibilidad por sucursal.

    Es la consulta que dispara el cliente al pulsar una tarjeta del catálogo.
    Solo entrega prendas activas: una prenda retirada responde como inexistente
    para no filtrar información del catálogo interno.

    Parámetros:
        cursor: cursor de PostgreSQL.
        id_prenda: prenda solicitada.

    Retorna:
        dict | None: la ficha con todas sus variantes y su stock desglosado,
                     o None si no existe o está inactiva.
    """
    cursor.execute(
        """
        SELECT  p.id_prenda,
                p.sku,
                p.nombre,
                p.descripcion,
                p.marca,
                p.genero,
                p.precio_base, p.material, p.medidas, p.precio_mayorista, p.umbral_mayorista, p.precio_oferta, p.oferta_inicio, p.oferta_fin,
                p.id_categoria,
                c.nombre AS categoria,
                (SELECT i.url_imagen FROM imagen_prenda i
                  WHERE i.id_prenda = p.id_prenda
                  ORDER BY i.es_principal DESC, i.id_imagen
                  LIMIT 1) AS url_imagen,
                COALESCE((
                    SELECT SUM(inv.stock)::int
                    FROM variante_prenda v
                    JOIN inventario_catalogo inv ON inv.id_variante_prenda = v.id_variante_prenda
                    WHERE v.id_prenda = p.id_prenda
                ), 0) AS stock_total
        FROM prenda p
        LEFT JOIN categoria c ON p.id_categoria = c.id_categoria
        WHERE p.id_prenda = %s AND p.estado = 'Activo';
        """,
        (id_prenda,),
    )
    fila = cursor.fetchone()

    if fila is None:
        return None

    prenda = dict(fila)
    prenda["variantes"] = listar_variantes_catalogo(
        cursor, id_prenda, prenda["precio_base"], con_disponibilidad=True
    )
    return prenda


def obtener_filtros_disponibles(cursor) -> dict[str, Any]:
    """Devuelve las opciones con las que el frontend arma su barra de filtros.

    Se entregan en una sola llamada (categorías, tallas, colores, géneros y
    rango de precios) para evitar cinco peticiones al abrir el catálogo.

    Parámetros:
        cursor: cursor de PostgreSQL.

    Retorna:
        dict: listas de opciones y el rango real de precios del catálogo.
    """
    # Solo categorías activas que ya tengan al menos una prenda publicada: un
    # filtro que no devuelve resultados solo confunde al comprador.
    cursor.execute(
        """
        SELECT DISTINCT c.id_categoria, c.nombre
        FROM categoria c
        JOIN prenda p ON p.id_categoria = c.id_categoria AND p.estado = 'Activo'
        WHERE c.estado = 'Activo'
        ORDER BY c.nombre;
        """
    )
    categorias = [dict(f) for f in cursor.fetchall()]

    cursor.execute(
        """
        SELECT DISTINCT t.id_talla, t.nombre
        FROM talla t
        JOIN variante_prenda v ON v.id_talla = t.id_talla
        JOIN prenda p ON p.id_prenda = v.id_prenda AND p.estado = 'Activo'
        ORDER BY t.id_talla;
        """
    )
    tallas = [dict(f) for f in cursor.fetchall()]

    cursor.execute(
        """
        SELECT DISTINCT col.id_color, col.nombre, col.codigo_hex
        FROM color col
        JOIN variante_color vc ON vc.id_color=col.id_color JOIN variante_prenda v ON v.id_variante_prenda=vc.id_variante_prenda
        JOIN prenda p ON p.id_prenda = v.id_prenda AND p.estado = 'Activo'
        ORDER BY col.nombre;
        """
    )
    colores = [dict(f) for f in cursor.fetchall()]

    cursor.execute(
        """
        SELECT DISTINCT genero FROM prenda
        WHERE estado = 'Activo' AND genero IS NOT NULL
        ORDER BY genero;
        """
    )
    generos = [f["genero"] for f in cursor.fetchall()]

    cursor.execute(
        """
        SELECT COALESCE(MIN(precio_base), 0) AS precio_minimo,
               COALESCE(MAX(precio_base), 0) AS precio_maximo
        FROM prenda WHERE estado = 'Activo';
        """
    )
    rango = cursor.fetchone()

    return {
        "categorias": categorias,
        "tallas": tallas,
        "colores": colores,
        "generos": generos,
        "precio_minimo": rango["precio_minimo"],
        "precio_maximo": rango["precio_maximo"],
    }
