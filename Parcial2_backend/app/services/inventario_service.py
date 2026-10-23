"""
=============================================================================
FASHIONSTORE - SERVICIO DE ANALÍTICA Y MONITOREO DE INVENTARIO (CU10)
Sistemas de Información II - UAGRM
-----------------------------------------------------------------------------
Consultas SQL analíticas agregadas multisucursal, cálculo dinámico de KPIs
y clasificación de salud de inventario (Óptimo, Bajo, Agotado).
=============================================================================
"""

from typing import Any


def obtener_resumen_inventario(
    cursor,
    id_sucursal: int | None = None,
    id_categoria: int | None = None,
    id_temporada: int | None = None,
    busqueda: str | None = None,
) -> dict[str, Any]:
    """Calcula totales agregados de existencias y desglose por sucursal física."""
    condiciones: list[str] = []
    valores: list[Any] = []

    if id_sucursal is not None:
        condiciones.append("i.id_sucursal = %s")
        valores.append(id_sucursal)

    if id_categoria is not None:
        condiciones.append("p.id_categoria = %s")
        valores.append(id_categoria)

    if id_temporada is not None:
        condiciones.append("p.id_temporada = %s")
        valores.append(id_temporada)

    if busqueda:
        condiciones.append("(p.sku ILIKE %s OR p.nombre ILIKE %s OR v.sku_variante ILIKE %s)")
        patron = f"%{busqueda.strip()}%"
        valores.extend([patron, patron, patron])

    where_clause = ""
    if condiciones:
        where_clause = " WHERE " + " AND ".join(condiciones)

    # 1. Consulta consolidada global
    sql_global = f"""
        WITH items_base AS (
            SELECT 
                i.id_sucursal,
                s.nombre AS sucursal,
                ci.nombre AS ciudad,
                v.id_variante_prenda,
                p.id_prenda,
                COALESCE(i.stock, 0) AS stock,
                CASE 
                    WHEN COALESCE(i.stock, 0) >= 5 THEN 'Optimo'
                    WHEN COALESCE(i.stock, 0) BETWEEN 1 AND 4 THEN 'Bajo'
                    ELSE 'Agotado'
                END AS estado_stock
            FROM inventario i
            JOIN sucursal s ON i.id_sucursal = s.id_sucursal
            JOIN ciudad ci ON s.id_ciudad = ci.id_ciudad
            JOIN variante_prenda v ON i.id_variante_prenda = v.id_variante_prenda
            JOIN prenda p ON v.id_prenda = p.id_prenda
            LEFT JOIN categoria c ON p.id_categoria = c.id_categoria
            LEFT JOIN temporada t ON p.id_temporada = t.id_temporada
            {where_clause}
        )
        SELECT 
            COALESCE(SUM(stock), 0)::int AS total_stock,
            COUNT(DISTINCT id_prenda)::int AS total_prendas,
            COUNT(DISTINCT id_variante_prenda)::int AS total_variantes,
            COUNT(*) FILTER (WHERE estado_stock = 'Optimo')::int AS total_optimo,
            COUNT(*) FILTER (WHERE estado_stock = 'Bajo')::int AS total_bajo,
            COUNT(*) FILTER (WHERE estado_stock = 'Agotado')::int AS total_agotado
        FROM items_base;
    """
    cursor.execute(sql_global, tuple(valores))
    fila_global = cursor.fetchone()
    resumen = dict(fila_global) if fila_global else {
        "total_stock": 0,
        "total_prendas": 0,
        "total_variantes": 0,
        "total_optimo": 0,
        "total_bajo": 0,
        "total_agotado": 0,
    }

    # 2. Desglose por sucursal
    sql_sucursales = f"""
        WITH items_base AS (
            SELECT 
                i.id_sucursal,
                s.nombre AS sucursal,
                ci.nombre AS ciudad,
                v.id_variante_prenda,
                p.id_prenda,
                COALESCE(i.stock, 0) AS stock,
                CASE 
                    WHEN COALESCE(i.stock, 0) >= 5 THEN 'Optimo'
                    WHEN COALESCE(i.stock, 0) BETWEEN 1 AND 4 THEN 'Bajo'
                    ELSE 'Agotado'
                END AS estado_stock
            FROM inventario i
            JOIN sucursal s ON i.id_sucursal = s.id_sucursal
            JOIN ciudad ci ON s.id_ciudad = ci.id_ciudad
            JOIN variante_prenda v ON i.id_variante_prenda = v.id_variante_prenda
            JOIN prenda p ON v.id_prenda = p.id_prenda
            LEFT JOIN categoria c ON p.id_categoria = c.id_categoria
            LEFT JOIN temporada t ON p.id_temporada = t.id_temporada
            {where_clause}
        )
        SELECT 
            id_sucursal,
            sucursal,
            ciudad,
            COALESCE(SUM(stock), 0)::int AS total_stock,
            COUNT(DISTINCT id_variante_prenda)::int AS total_variantes,
            COUNT(*) FILTER (WHERE estado_stock = 'Optimo')::int AS total_optimo,
            COUNT(*) FILTER (WHERE estado_stock = 'Bajo')::int AS total_bajo,
            COUNT(*) FILTER (WHERE estado_stock = 'Agotado')::int AS total_agotado
        FROM items_base
        GROUP BY id_sucursal, sucursal, ciudad
        ORDER BY id_sucursal;
    """
    cursor.execute(sql_sucursales, tuple(valores))
    resumen["por_sucursal"] = [dict(f) for f in cursor.fetchall()]
    return resumen


def obtener_monitoreo_inventario(
    cursor,
    id_sucursal: int | None = None,
    id_categoria: int | None = None,
    id_temporada: int | None = None,
    busqueda: str | None = None,
    estado_stock: str | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """Devuelve el listado detallado de existencias con clasificación cromática de stock."""
    condiciones: list[str] = []
    valores: list[Any] = []

    if id_sucursal is not None:
        condiciones.append("i.id_sucursal = %s")
        valores.append(id_sucursal)

    if id_categoria is not None:
        condiciones.append("p.id_categoria = %s")
        valores.append(id_categoria)

    if id_temporada is not None:
        condiciones.append("p.id_temporada = %s")
        valores.append(id_temporada)

    if busqueda:
        condiciones.append("(p.sku ILIKE %s OR p.nombre ILIKE %s OR v.sku_variante ILIKE %s)")
        patron = f"%{busqueda.strip()}%"
        valores.extend([patron, patron, patron])

    if estado_stock:
        st = estado_stock.strip().capitalize()
        if st == "Optimo":
            condiciones.append("COALESCE(i.stock, 0) >= 5")
        elif st == "Bajo":
            condiciones.append("COALESCE(i.stock, 0) BETWEEN 1 AND 4")
        elif st == "Agotado":
            condiciones.append("COALESCE(i.stock, 0) <= 0")

    where_clause = ""
    if condiciones:
        where_clause = " WHERE " + " AND ".join(condiciones)

    sql = f"""
        SELECT 
            i.id_sucursal,
            s.nombre AS sucursal,
            ci.nombre AS ciudad,
            p.id_prenda,
            p.sku AS prenda_sku,
            p.nombre AS prenda_nombre,
            p.id_categoria,
            c.nombre AS categoria,
            p.id_temporada,
            t.nombre AS temporada,
            v.id_variante_prenda,
            v.sku_variante,
            talla.nombre AS talla,
            col.nombre AS color,
            col.codigo_hex,
            p.precio_base,
            v.precio_adicional,
            COALESCE(i.stock, 0) AS stock,
            CASE 
                WHEN COALESCE(i.stock, 0) >= 5 THEN 'Optimo'
                WHEN COALESCE(i.stock, 0) BETWEEN 1 AND 4 THEN 'Bajo'
                ELSE 'Agotado'
            END AS estado_stock,
            CASE 
                WHEN COALESCE(i.stock, 0) >= 5 THEN 'verde'
                WHEN COALESCE(i.stock, 0) BETWEEN 1 AND 4 THEN 'amarillo'
                ELSE 'rojo'
            END AS color_badge
        FROM inventario i
        JOIN sucursal s ON i.id_sucursal = s.id_sucursal
        JOIN ciudad ci ON s.id_ciudad = ci.id_ciudad
        JOIN variante_prenda v ON i.id_variante_prenda = v.id_variante_prenda
        JOIN prenda p ON v.id_prenda = p.id_prenda
        LEFT JOIN categoria c ON p.id_categoria = c.id_categoria
        LEFT JOIN temporada t ON p.id_temporada = t.id_temporada
        LEFT JOIN talla ON v.id_talla = talla.id_talla
        LEFT JOIN color col ON v.id_color = col.id_color
        {where_clause}
        ORDER BY s.id_sucursal, p.id_prenda, v.id_variante_prenda
        LIMIT %s OFFSET %s;
    """
    valores.extend([limit, skip])

    cursor.execute(sql, tuple(valores))
    return [dict(f) for f in cursor.fetchall()]
