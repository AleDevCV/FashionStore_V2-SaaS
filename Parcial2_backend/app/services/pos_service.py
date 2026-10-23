"""
=============================================================================
FASHIONSTORE - SERVICIO DE TERMINAL POS (CU19)
Sistemas de Información II - UAGRM
-----------------------------------------------------------------------------
Lógica de negocio para la terminal de caja presencial:
1. Búsqueda ágil de artículos por SKU / código de barras / descripción con stock en tiempo real.
2. Carga y vinculación de reservas de probador (CU16, CU17).
3. Transacción atómica de cobro presencial (Efectivo/Tarjeta/QR/Transferencia).
4. Descuento de stock en sucursal vía disparador de movimiento_inventario.
5. Emisión automática de comprobante fiscal digital PDF con ReportLab + QR (CU21).
6. Auditoría inmutable en bitácora del sistema (CU25).
=============================================================================
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Any
from fastapi import HTTPException, status

from app.schemas.comprobante import ComprobanteGenerarPeticion
from app.schemas.pos import POSVentaCrear
from app.services import comprobante_service
from app.services.bitacora_service import ACCION_INSERT, registrar_bitacora


def listar_productos_pos(
    cursor: Any,
    id_sucursal: int,
    query: str = "",
    id_categoria: int | None = None,
    solo_con_stock: bool = False,
) -> list[dict]:
    """Retorna el catálogo de variantes para la terminal POS con existencias en la sucursal activa.

    Permite búsqueda exacta o parcial por SKU (código de barras) o nombre de prenda.
    """
    sql = """
        SELECT 
            vp.id_variante_prenda,
            COALESCE(vp.sku_variante, p.sku) AS sku,
            p.id_prenda,
            p.nombre AS prenda_nombre,
            c.nombre AS categoria_nombre,
            COALESCE(t.nombre, 'Única') AS talla,
            COALESCE(col.nombre, 'Estándar') AS color,
            (p.precio_base + COALESCE(vp.precio_adicional, 0.00)) AS precio_unitario,
            COALESCE(inv.stock, 0) AS stock_disponible,
            (
                SELECT ip.url_imagen 
                FROM imagen_prenda ip 
                WHERE ip.id_prenda = p.id_prenda 
                ORDER BY ip.es_principal DESC, ip.id_imagen ASC 
                LIMIT 1
            ) AS imagen_url
        FROM variante_prenda vp
        JOIN prenda p ON vp.id_prenda = p.id_prenda
        JOIN categoria c ON p.id_categoria = c.id_categoria
        LEFT JOIN talla t ON vp.id_talla = t.id_talla
        LEFT JOIN color col ON vp.id_color = col.id_color
        LEFT JOIN inventario inv ON (inv.id_variante_prenda = vp.id_variante_prenda AND inv.id_sucursal = %s)
        WHERE p.estado = 'Activo'
    """
    params: list[Any] = [id_sucursal]

    if query:
        q_clean = query.strip()
        sql += """
            AND (
                vp.sku_variante ILIKE %s 
                OR p.sku ILIKE %s
                OR p.nombre ILIKE %s 
                OR c.nombre ILIKE %s
                OR col.nombre ILIKE %s
            )
        """
        like_pattern = f"%{q_clean}%"
        params.extend([like_pattern, like_pattern, like_pattern, like_pattern, like_pattern])

    if id_categoria:
        sql += " AND p.id_categoria = %s"
        params.append(id_categoria)

    if solo_con_stock:
        sql += " AND COALESCE(inv.stock, 0) > 0"

    sql += " ORDER BY p.nombre ASC, t.nombre ASC, col.nombre ASC LIMIT 100;"

    cursor.execute(sql, tuple(params))
    return cursor.fetchall()


def cargar_reserva_pos(cursor: Any, codigo_o_id: str) -> dict:
    """Recupera los datos de una reserva (apartado o probador) para cargarla directamente al carrito POS.

    Parámetros:
        cursor: conexión activa a PostgreSQL.
        codigo_o_id: ID numérico o código de ticket TKT-YYYY-NNNNNN.
    """
    codigo_limpio = codigo_o_id.strip()

    if codigo_limpio.isdigit():
        sql_header = """
            SELECT r.id_reserva, r.id_cliente, c.nombre_completo AS cliente_nombre,
                   c.ci AS cliente_ci, r.id_sucursal, s.nombre AS sucursal_nombre,
                   r.estado, r.total, r.fecha_reserva
            FROM reserva r
            JOIN cliente c ON r.id_cliente = c.id_cliente
            JOIN sucursal s ON r.id_sucursal = s.id_sucursal
            WHERE r.id_reserva = %s;
        """
        cursor.execute(sql_header, (int(codigo_limpio),))
    else:
        # Extraer ID del formato TKT-YYYY-XXXXXX
        try:
            partes = codigo_limpio.split("-")
            id_reserva_num = int(partes[-1])
            sql_header = """
                SELECT r.id_reserva, r.id_cliente, c.nombre_completo AS cliente_nombre,
                       c.ci AS cliente_ci, r.id_sucursal, s.nombre AS sucursal_nombre,
                       r.estado, r.total, r.fecha_reserva
                FROM reserva r
                JOIN cliente c ON r.id_cliente = c.id_cliente
                JOIN sucursal s ON r.id_sucursal = s.id_sucursal
                WHERE r.id_reserva = %s;
            """
            cursor.execute(sql_header, (id_reserva_num,))
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Formato de ticket o ID de reserva inválido: '{codigo_o_id}'",
            )

    header = cursor.fetchone()
    if not header:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró ninguna reserva con el código o ID '{codigo_o_id}'",
        )

    if header["estado"] not in ("Pendiente", "Preparado"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"La reserva tiene estado '{header['estado']}' y ya no puede ser cobrada.",
        )

    id_res = header["id_reserva"]
    cursor.execute(
        """
        SELECT 
            dr.id_variante_prenda,
            COALESCE(vp.sku_variante, p.sku) AS sku,
            p.nombre AS prenda_nombre,
            COALESCE(t.nombre, 'Única') AS talla,
            COALESCE(col.nombre, 'Estándar') AS color,
            dr.cantidad,
            dr.precio_unitario,
            (dr.cantidad * dr.precio_unitario) AS subtotal
        FROM detalle_reserva dr
        JOIN variante_prenda vp ON dr.id_variante_prenda = vp.id_variante_prenda
        JOIN prenda p ON vp.id_prenda = p.id_prenda
        LEFT JOIN talla t ON vp.id_talla = t.id_talla
        LEFT JOIN color col ON vp.id_color = col.id_color
        WHERE dr.id_reserva = %s;
        """,
        (id_res,),
    )
    items = cursor.fetchall()

    anio = 2026
    if header.get("fecha_reserva") and hasattr(header["fecha_reserva"], "year"):
        anio = header["fecha_reserva"].year
    codigo_ticket = f"TKT-{anio}-{id_res:06d}"

    return {
        "id_reserva": id_res,
        "codigo_ticket": codigo_ticket,
        "id_cliente": header["id_cliente"],
        "cliente_nombre": header["cliente_nombre"],
        "cliente_ci": header["cliente_ci"],
        "id_sucursal": header["id_sucursal"],
        "sucursal_nombre": header["sucursal_nombre"],
        "estado": header["estado"],
        "total": header["total"],
        "items": items,
    }


def procesar_venta_pos(
    cursor: Any,
    datos: POSVentaCrear,
    id_usuario: int | None,
    ip_address: str,
) -> dict:
    """Ejecuta la transacción de venta presencial en caja POS (CU19):
    1. Resuelve o valida el cliente (o asigna cliente genérico de mostrador).
    2. Valida existencias físicas en la sucursal.
    3. Registra cabecera y detalle de venta.
    4. Genera movimientos de inventario ('Salida') para actualizar stock.
    5. Si proviene de reserva, transiciona estado a 'Atendido'.
    6. Emite comprobante fiscal digital PDF (CU21).
    7. Registra auditoría inmutable en bitácora (CU25).
    """
    from app.services.commerce import prepare_pos
    prepare_pos(cursor, datos)

    # 1. Validar o resolver cliente
    id_cliente = datos.id_cliente
    if not id_cliente:
        # Buscar cliente genérico de mostrador
        cursor.execute(
            "SELECT id_cliente, nombre_completo, ci FROM cliente WHERE ci = 'MOSTRADOR' LIMIT 1;"
        )
        cliente_row = cursor.fetchone()
        if cliente_row:
            id_cliente = cliente_row["id_cliente"]
        else:
            raise HTTPException(409, "Configure el cliente mostrador de la empresa antes de vender.")
    else:
        cursor.execute("SELECT id_cliente, nombre_completo, ci FROM cliente WHERE id_cliente = %s;", (id_cliente,))
        cliente_row = cursor.fetchone()
        if not cliente_row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"El cliente con ID {id_cliente} no existe.",
            )

    # 2. Validar sucursal
    cursor.execute("SELECT id_sucursal, nombre FROM sucursal WHERE id_sucursal = %s;", (datos.id_sucursal,))
    sucursal_row = cursor.fetchone()
    if not sucursal_row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"La sucursal con ID {datos.id_sucursal} no existe.",
        )

    # 3. Validar stock disponible para cada variante en la sucursal
    for it in datos.items:
        cursor.execute(
            """
            SELECT inv.stock, COALESCE(vp.sku_variante, p.sku) AS sku, p.nombre AS prenda_nombre
            FROM variante_prenda vp
            JOIN prenda p ON vp.id_prenda = p.id_prenda
            LEFT JOIN inventario inv ON (inv.id_variante_prenda = vp.id_variante_prenda AND inv.id_sucursal = %s)
            WHERE vp.id_variante_prenda = %s;
            """,
            (datos.id_sucursal, it.id_variante_prenda),
        )
        variante_info = cursor.fetchone()
        if not variante_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"La variante de prenda {it.id_variante_prenda} no existe.",
            )
        stock_actual = variante_info["stock"] if variante_info["stock"] is not None else 0
        if stock_actual < it.cantidad:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"Stock insuficiente para '{variante_info['prenda_nombre']}' ({variante_info['sku']}). "
                    f"Disponible: {stock_actual}, Solicitado: {it.cantidad}"
                ),
            )

    # 4. Calcular importes
    subtotal = sum(
        Decimal(str(it.precio_unitario)) * it.cantidad for it in datos.items
    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    
    descuento = Decimal(str(datos.descuento)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    total = max(Decimal("0.00"), subtotal - descuento).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    monto_recibido: Decimal | None = None
    cambio_vuelto: Decimal | None = None

    if datos.metodo_pago == "Efectivo":
        monto_recibido = Decimal(str(datos.monto_recibido if datos.monto_recibido is not None else total)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        if monto_recibido < total:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"El monto recibido (Bs {monto_recibido:.2f}) es menor al total a pagar (Bs {total:.2f}).",
            )
        cambio_vuelto = (monto_recibido - total).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    else:
        monto_recibido = total
        cambio_vuelto = Decimal("0.00")

    # 5. Insertar cabecera de Venta
    cursor.execute(
        """
        INSERT INTO venta (
            id_cliente, id_sucursal, id_cajero, id_reserva, tipo_venta,
            metodo_pago, subtotal, descuento, total
        )
        VALUES (%s, %s, %s, %s, 'Presencial', %s, %s, %s, %s)
        RETURNING id_venta, fecha_venta;
        """,
        (
            id_cliente,
            datos.id_sucursal,
            id_usuario,
            datos.id_reserva,
            datos.metodo_pago,
            subtotal,
            descuento,
            total,
        ),
    )
    venta_creada = cursor.fetchone()
    id_venta = venta_creada["id_venta"]
    fecha_venta = venta_creada["fecha_venta"]

    # 6. Insertar detalle de venta y registrar movimiento de inventario (Salida)
    items_respuesta: list[dict] = []
    for it in datos.items:
        subtotal_item = (Decimal(str(it.precio_unitario)) * it.cantidad).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        cursor.execute(
            """
            INSERT INTO detalle_venta (id_venta, id_variante_prenda, cantidad, precio_unitario, subtotal)
            VALUES (%s, %s, %s, %s, %s);
            """,
            (id_venta, it.id_variante_prenda, it.cantidad, it.precio_unitario, subtotal_item),
        )

        # Movimiento de inventario para activar el trigger de descuento
        cursor.execute(
            """
            INSERT INTO movimiento_inventario (id_sucursal, id_variante_prenda, tipo, cantidad, motivo, id_usuario)
            VALUES (%s, %s, 'Salida', %s, %s, %s);
            """,
            (
                datos.id_sucursal,
                it.id_variante_prenda,
                it.cantidad,
                f"Venta presencial POS #{id_venta} CU19",
                id_usuario,
            ),
        )

        # Obtener datos para la respuesta
        cursor.execute(
            """
            SELECT COALESCE(vp.sku_variante, p.sku) AS sku, p.nombre AS prenda_nombre, 
                   COALESCE(t.nombre, 'Única') AS talla, COALESCE(col.nombre, 'Estándar') AS color
            FROM variante_prenda vp
            JOIN prenda p ON vp.id_prenda = p.id_prenda
            LEFT JOIN talla t ON vp.id_talla = t.id_talla
            LEFT JOIN color col ON vp.id_color = col.id_color
            WHERE vp.id_variante_prenda = %s;
            """,
            (it.id_variante_prenda,),
        )
        info_vp = cursor.fetchone()

        items_respuesta.append({
            "id_variante_prenda": it.id_variante_prenda,
            "sku": info_vp["sku"] if info_vp else None,
            "prenda_nombre": info_vp["prenda_nombre"] if info_vp else None,
            "talla": info_vp["talla"] if info_vp else None,
            "color": info_vp["color"] if info_vp else None,
            "cantidad": it.cantidad,
            "precio_unitario": it.precio_unitario,
            "subtotal": subtotal_item,
        })

    # 7. Si proviene de reserva, transicionar estado a 'Atendido'
    if datos.id_reserva:
        cursor.execute(
            "UPDATE reserva SET estado = 'Atendido', updated_at = NOW() WHERE id_reserva = %s;",
            (datos.id_reserva,),
        )

    if datos.id_reserva:
        cursor.execute("DELETE FROM retencion WHERE id_reserva=%s", (datos.id_reserva,))
    cursor.execute("UPDATE venta SET fecha_entrega=now() WHERE id_venta=%s", (id_venta,))

    # 8. Generar comprobante fiscal digital PDF (CU21)
    nit_ci = (datos.nit_ci or "0").strip()
    razon_social = (datos.razon_social or "Sin Nombre").strip()
    
    comprobante_res = None
    cursor.execute("SAVEPOINT receipt_optional")
    try:
        req_comp = ComprobanteGenerarPeticion(
            id_venta=id_venta,
            nit_ci=nit_ci,
            razon_social=razon_social,
            enviar_email=datos.enviar_email,
        )
        comprobante_res = comprobante_service.generar_comprobante(
            cursor=cursor,
            datos=req_comp,
            id_usuario=id_usuario,
            ip_address=ip_address,
        )
    except Exception as exc:
        import logging
        logging.getLogger(__name__).error('No fue posible generar el comprobante de la venta %s (%s)', id_venta, type(exc).__name__)
        cursor.execute("ROLLBACK TO SAVEPOINT receipt_optional")
    finally:
        cursor.execute("RELEASE SAVEPOINT receipt_optional")

    # 9. Obtener nombre del cajero para la respuesta
    cajero_nombre = "Cajero de Sucursal"
    if id_usuario:
        cursor.execute(
            "SELECT CONCAT(nombre, ' ', COALESCE(apellido, '')) AS nombre_completo FROM usuario WHERE id_usuario = %s;",
            (id_usuario,),
        )
        u_row = cursor.fetchone()
        if u_row and u_row["nombre_completo"].strip():
            cajero_nombre = u_row["nombre_completo"].strip()

    # 10. Auditoría inmutable en bitácora (CU25)
    registrar_bitacora(
        cursor=cursor,
        accion=ACCION_INSERT,
        tabla_afectada="venta",
        registro_id=id_venta,
        detalle=(
            f"Venta presencial POS #{id_venta} registrada en sucursal '{sucursal_row['nombre']}'. "
            f"Método de pago: {datos.metodo_pago}. Total: Bs {total}. "
            f"Recibido: Bs {monto_recibido:.2f}, Cambio: Bs {cambio_vuelto:.2f}. "
            f"Comprobante: {comprobante_res['numero_comprobante'] if comprobante_res else 'N/A'}."
        ),
        id_usuario=id_usuario,
        ip_address=ip_address,
    )

    return {
        "id_venta": id_venta,
        "id_sucursal": datos.id_sucursal,
        "sucursal_nombre": sucursal_row["nombre"],
        "id_cliente": id_cliente,
        "cliente_nombre": cliente_row["nombre_completo"],
        "cajero_nombre": cajero_nombre,
        "id_reserva": datos.id_reserva,
        "tipo_venta": "Presencial",
        "metodo_pago": datos.metodo_pago,
        "subtotal": subtotal,
        "descuento": descuento,
        "total": total,
        "monto_recibido": monto_recibido,
        "cambio_vuelto": cambio_vuelto,
        "fecha_venta": fecha_venta,
        "id_comprobante": comprobante_res["id_comprobante"] if comprobante_res else None,
        "numero_comprobante": comprobante_res["numero_comprobante"] if comprobante_res else None,
        "url_pdf": comprobante_res["url_pdf"] if comprobante_res else None,
        "items": items_respuesta,
    }
