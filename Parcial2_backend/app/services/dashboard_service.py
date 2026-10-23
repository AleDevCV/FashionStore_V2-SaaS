"""
=============================================================================
FASHIONSTORE - SERVICIO DE DASHBOARD Y KPIS (CU24)
Sistemas de Información II - UAGRM
-----------------------------------------------------------------------------
Agrega datos de ventas, reservas omnicanal, inventario y productos para
abastecer el panel gerencial ejecutivo.
=============================================================================
"""

from typing import Any
from decimal import Decimal

from app.schemas.dashboard import (
    DashboardKPIsRespuesta,
    DistribucionCanal,
    DistribucionMetodoPago,
    EstadoInventarioSucursal,
    KPISummary,
    SucursalReservaRendimiento,
    TopPrendaVendida,
    VentaPorPeriodo,
)


def obtener_dashboard_kpis(cursor: Any) -> DashboardKPIsRespuesta:
    """Ejecuta consultas de agregación sobre la base de datos y retorna

    el payload consolidado para el panel de indicadores (CU24).
    """

    # 1. Métricas de ventas agregadas
    cursor.execute(
        """
        SELECT 
            COALESCE(SUM(total), 0) AS ingresos_totales,
            COUNT(*) AS total_ventas
        FROM venta;
        """
    )
    fila_ventas = cursor.fetchone()
    ingresos_totales = float(fila_ventas["ingresos_totales"] or 0)
    total_ventas = int(fila_ventas["total_ventas"] or 0)
    ticket_promedio = (
        round(ingresos_totales / total_ventas, 2) if total_ventas > 0 else 0.0
    )

    # 2. Métricas de reservas omnicanal (CU16, CU17)
    cursor.execute(
        """
        SELECT 
            COUNT(*) AS total_reservas,
            COUNT(*) FILTER (WHERE estado = 'Atendido') AS reservas_atendidas
        FROM reserva;
        """
    )
    fila_reservas = cursor.fetchone()
    total_reservas = int(fila_reservas["total_reservas"] or 0)
    reservas_atendidas = int(fila_reservas["reservas_atendidas"] or 0)
    tasa_conversion_reservas = (
        round((reservas_atendidas / total_reservas) * 100, 1)
        if total_reservas > 0
        else 0.0
    )

    # 3. Métricas de inventario global
    cursor.execute(
        """
        SELECT 
            COALESCE(SUM(i.stock), 0) AS stock_total_piezas,
            COALESCE(SUM(i.stock * (p.precio_base + COALESCE(vp.precio_adicional, 0))), 0) AS valor_inventario_estimado
        FROM inventario i
        JOIN variante_prenda vp ON i.id_variante_prenda = vp.id_variante_prenda
        JOIN prenda p ON vp.id_prenda = p.id_prenda;
        """
    )
    fila_inventario = cursor.fetchone()
    stock_total_piezas = int(fila_inventario["stock_total_piezas"] or 0)
    valor_inventario_estimado = float(fila_inventario["valor_inventario_estimado"] or 0)

    resumen = KPISummary(
        ingresos_totales=ingresos_totales,
        total_ventas=total_ventas,
        ticket_promedio=ticket_promedio,
        total_reservas=total_reservas,
        reservas_atendidas=reservas_atendidas,
        tasa_conversion_reservas=tasa_conversion_reservas,
        stock_total_piezas=stock_total_piezas,
        valor_inventario_estimado=valor_inventario_estimado,
    )

    # 4. Tendencia cronológica (ventas recientes por fecha)
    cursor.execute(
        """
        SELECT 
            TO_CHAR(fecha_venta, 'YYYY-MM-DD') AS fecha,
            COALESCE(SUM(total), 0) AS total_ingresos,
            COUNT(*) AS cantidad_ventas
        FROM venta
        GROUP BY TO_CHAR(fecha_venta, 'YYYY-MM-DD')
        ORDER BY fecha ASC
        LIMIT 14;
        """
    )
    filas_cronologicas = cursor.fetchall()
    ventas_recientes = [
        VentaPorPeriodo(
            fecha=row["fecha"],
            total_ingresos=float(row["total_ingresos"] or 0),
            cantidad_ventas=int(row["cantidad_ventas"] or 0),
        )
        for row in filas_cronologicas
    ]

    # 5. Distribución por Canal (Presencial vs Online)
    cursor.execute(
        """
        SELECT 
            COALESCE(tipo_venta, 'Presencial') AS canal,
            COALESCE(SUM(total), 0) AS total_ingresos,
            COUNT(*) AS cantidad_ventas
        FROM venta
        GROUP BY tipo_venta
        ORDER BY total_ingresos DESC;
        """
    )
    filas_canales = cursor.fetchall()
    canales = []
    for row in filas_canales:
        subtotal = float(row["total_ingresos"] or 0)
        pct = round((subtotal / ingresos_totales) * 100, 1) if ingresos_totales > 0 else 0.0
        canales.append(
            DistribucionCanal(
                canal=row["canal"],
                total_ingresos=subtotal,
                cantidad_ventas=int(row["cantidad_ventas"] or 0),
                porcentaje=pct,
            )
        )

    # 6. Distribución por Método de Pago
    cursor.execute(
        """
        SELECT 
            COALESCE(metodo_pago, 'Otro') AS metodo_pago,
            COALESCE(SUM(total), 0) AS total_ingresos,
            COUNT(*) AS cantidad_ventas
        FROM venta
        GROUP BY metodo_pago
        ORDER BY total_ingresos DESC;
        """
    )
    filas_metodos = cursor.fetchall()
    metodos_pago = []
    for row in filas_metodos:
        subtotal = float(row["total_ingresos"] or 0)
        pct = round((subtotal / ingresos_totales) * 100, 1) if ingresos_totales > 0 else 0.0
        metodos_pago.append(
            DistribucionMetodoPago(
                metodo_pago=row["metodo_pago"],
                total_ingresos=subtotal,
                cantidad_ventas=int(row["cantidad_ventas"] or 0),
                porcentaje=pct,
            )
        )

    # 7. Rendimiento de reservas por sucursal física
    cursor.execute(
        """
        SELECT 
            s.id_sucursal,
            s.nombre AS sucursal,
            c.nombre AS ciudad,
            COUNT(r.id_reserva) AS total_reservas,
            COUNT(r.id_reserva) FILTER (WHERE r.estado = 'Atendido') AS atendidas,
            COUNT(r.id_reserva) FILTER (WHERE r.estado IN ('Pendiente', 'Preparado')) AS pendientes,
            COUNT(r.id_reserva) FILTER (WHERE r.estado = 'Cancelado') AS canceladas
        FROM sucursal s
        LEFT JOIN ciudad c ON s.id_ciudad = c.id_ciudad
        LEFT JOIN reserva r ON s.id_sucursal = r.id_sucursal
        GROUP BY s.id_sucursal, s.nombre, c.nombre
        ORDER BY total_reservas DESC, s.nombre ASC;
        """
    )
    filas_sucursales = cursor.fetchall()
    rendimiento_sucursales = []
    for row in filas_sucursales:
        tot = int(row["total_reservas"] or 0)
        atend = int(row["atendidas"] or 0)
        tasa = round((atend / tot) * 100, 1) if tot > 0 else 0.0
        rendimiento_sucursales.append(
            SucursalReservaRendimiento(
                id_sucursal=row["id_sucursal"],
                sucursal=row["sucursal"],
                ciudad=row["ciudad"],
                total_reservas=tot,
                atendidas=atend,
                pendientes=int(row["pendientes"] or 0),
                canceladas=int(row["canceladas"] or 0),
                tasa_efectividad=tasa,
            )
        )

    # 8. Top prendas más vendidas
    cursor.execute(
        """
        SELECT 
            p.id_prenda,
            p.nombre,
            cat.nombre AS categoria,
            COALESCE(SUM(dv.cantidad), 0) AS unidades_vendidas,
            COALESCE(SUM(dv.subtotal), 0) AS total_ingresos,
            (SELECT img.url_imagen FROM imagen_prenda img WHERE img.id_prenda = p.id_prenda LIMIT 1) AS url_imagen
        FROM detalle_venta dv
        JOIN variante_prenda vp ON dv.id_variante_prenda = vp.id_variante_prenda
        JOIN prenda p ON vp.id_prenda = p.id_prenda
        LEFT JOIN categoria cat ON p.id_categoria = cat.id_categoria
        GROUP BY p.id_prenda, p.nombre, cat.nombre
        ORDER BY unidades_vendidas DESC, total_ingresos DESC
        LIMIT 5;
        """
    )
    filas_top = cursor.fetchall()
    top_prendas = [
        TopPrendaVendida(
            id_prenda=row["id_prenda"],
            nombre=row["nombre"],
            categoria=row["categoria"],
            unidades_vendidas=int(row["unidades_vendidas"] or 0),
            total_ingresos=float(row["total_ingresos"] or 0),
            url_imagen=row["url_imagen"],
        )
        for row in filas_top
    ]

    # 9. Diagnóstico de salud de inventario por sucursal
    cursor.execute(
        """
        SELECT 
            s.id_sucursal,
            s.nombre AS sucursal,
            COALESCE(SUM(i.stock), 0) AS total_stock,
            COUNT(i.id_variante_prenda) FILTER (WHERE i.stock = 0) AS variantes_agotadas,
            COUNT(i.id_variante_prenda) FILTER (WHERE i.stock > 0 AND i.stock < 5) AS variantes_bajo_stock,
            COUNT(i.id_variante_prenda) FILTER (WHERE i.stock >= 5) AS variantes_optimas
        FROM sucursal s
        LEFT JOIN inventario i ON s.id_sucursal = i.id_sucursal
        GROUP BY s.id_sucursal, s.nombre
        ORDER BY s.id_sucursal ASC;
        """
    )
    filas_inv = cursor.fetchall()
    inventario_sucursales = [
        EstadoInventarioSucursal(
            id_sucursal=row["id_sucursal"],
            sucursal=row["sucursal"],
            total_stock=int(row["total_stock"] or 0),
            variantes_agotadas=int(row["variantes_agotadas"] or 0),
            variantes_bajo_stock=int(row["variantes_bajo_stock"] or 0),
            variantes_optimas=int(row["variantes_optimas"] or 0),
        )
        for row in filas_inv
    ]

    return DashboardKPIsRespuesta(
        resumen=resumen,
        ventas_recientes=ventas_recientes,
        canales=canales,
        metodos_pago=metodos_pago,
        rendimiento_sucursales=rendimiento_sucursales,
        top_prendas=top_prendas,
        inventario_sucursales=inventario_sucursales,
    )
