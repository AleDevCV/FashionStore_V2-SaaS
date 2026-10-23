"""
=============================================================================
FASHIONSTORE - SERVICIO DE VENTAS Y RESERVAS (CU15)
Sistemas de Información II - UAGRM
-----------------------------------------------------------------------------
Lógica de negocio para el carrito de compras y checkout digital:
1. Validación de stock disponible en sucursal.
2. Creación de reserva (bloquea artículos hasta 24h o hasta confirmación).
3. Conversión de reserva en venta confirmada (descuenta stock vía trigger).
4. Listado e historial de ventas para clientes y administradores.
5. Registro en bitácora inmutable (CU25).
=============================================================================
"""

import base64
import io
import qrcode
from decimal import Decimal, ROUND_HALF_UP
from typing import Any
from datetime import datetime, timedelta

from fastapi import HTTPException, status

from app.schemas.venta import (
    ReservaPeticion,
    ReservaProbadorCrear,
    ReservaProbadorEstadoActualizar,
    TicketReservaRespuesta,
    VentaConfirmarPeticion,
)
from app.services.bitacora_service import ACCION_INSERT, ACCION_UPDATE, registrar_bitacora


# ─────────────────────────────────────────────────────────────────────────────
# VALIDACIÓN DE STOCK (carrito pre-checkout)
# ─────────────────────────────────────────────────────────────────────────────

def validar_stock_carrito(
    cursor: Any,
    items: list[dict],
    id_sucursal: int,
) -> dict:
    """Verifica si cada variante del carrito tiene stock suficiente en la sucursal.

    Parámetros:
        cursor: cursor activo de PostgreSQL.
        items: lista de dicts con id_variante_prenda y cantidad.
        id_sucursal: sucursal donde se realizará la venta.

    Retorna:
        dict: {valido: bool, items_sin_stock: list[int], mensaje: str|None}
    """
    items_sin_stock = []

    for item in items:
        cursor.execute(
            """
            SELECT COALESCE(stock, 0) AS stock
            FROM inventario
            WHERE id_variante_prenda = %s AND id_sucursal = %s;
            """,
            (item["id_variante_prenda"], id_sucursal),
        )
        row = cursor.fetchone()
        stock_disponible = row["stock"] if row else 0

        if stock_disponible < item["cantidad"]:
            items_sin_stock.append(item["id_variante_prenda"])

    valido = len(items_sin_stock) == 0
    return {
        "valido": valido,
        "items_sin_stock": items_sin_stock,
        "mensaje": None if valido else "Algunos productos no tienen stock suficiente",
    }


# ─────────────────────────────────────────────────────────────────────────────
# RESERVA (CU15)
# ─────────────────────────────────────────────────────────────────────────────

def crear_reserva(cursor, datos, id_usuario, ip_address):
    from app.services.commerce import reserve
    rid = reserve(cursor, datos.id_cliente, datos.id_sucursal, [x.model_dump() for x in datos.items], id_usuario)
    return obtener_reserva_por_id(cursor, rid)


def obtener_reserva_por_id(cursor: Any, id_reserva: int) -> dict:
    """Recupera una reserva completa con sus ítems detallados."""
    cursor.execute(
        """
        SELECT r.*, s.nombre AS sucursal_nombre, v.id_venta
        FROM reserva r
        JOIN sucursal s ON r.id_sucursal = s.id_sucursal
        LEFT JOIN venta v ON r.id_reserva = v.id_reserva
        WHERE r.id_reserva = %s;
        """,
        (id_reserva,),
    )
    cabecera = cursor.fetchone()
    if not cabecera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La reserva solicitada no existe",
        )

    cursor.execute(
        """
        SELECT
            dr.id_variante_prenda,
            v.sku_variante,
            p.nombre AS prenda_nombre,
            t.nombre AS talla,
            c.nombre AS color,
            dr.cantidad,
            dr.precio_unitario,
            (dr.cantidad * dr.precio_unitario) AS subtotal
        FROM detalle_reserva dr
        JOIN variante_prenda v ON dr.id_variante_prenda = v.id_variante_prenda
        JOIN prenda p ON v.id_prenda = p.id_prenda
        JOIN talla t ON v.id_talla = t.id_talla
        JOIN color c ON v.id_color = c.id_color
        WHERE dr.id_reserva = %s
        ORDER BY dr.id_variante_prenda;
        """,
        (id_reserva,),
    )
    items = cursor.fetchall()

    resultado = dict(cabecera)
    resultado["items"] = items
    return resultado


# ─────────────────────────────────────────────────────────────────────────────
# VENTA (CU15 — post-pago confirmado)
# ─────────────────────────────────────────────────────────────────────────────

def confirmar_venta(cursor, datos, id_usuario, ip_address, payment_verified=False):
    from app.services.commerce import confirm_reservation
    vid = confirm_reservation(cursor, datos, id_usuario, payment_verified)
    return obtener_venta_por_id(cursor, vid)


def obtener_venta_por_id(cursor: Any, id_venta: int) -> dict:
    """Recupera una venta completa con sus ítems detallados."""
    cursor.execute(
        """
        SELECT
            v.id_venta, v.id_cliente,
            CONCAT(c.nombre_completo) AS cliente_nombre,
            v.id_sucursal, s.nombre AS sucursal_nombre,
            v.tipo_venta, v.metodo_pago,
            v.subtotal, v.descuento, v.total, v.fecha_venta
        FROM venta v
        LEFT JOIN cliente c ON v.id_cliente = c.id_cliente
        LEFT JOIN sucursal s ON v.id_sucursal = s.id_sucursal
        WHERE v.id_venta = %s;
        """,
        (id_venta,),
    )
    cabecera = cursor.fetchone()
    if not cabecera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La venta solicitada no existe",
        )

    cursor.execute(
        """
        SELECT
            dv.id_variante_prenda,
            vp.sku_variante,
            p.nombre AS prenda_nombre,
            t.nombre AS talla,
            col.nombre AS color,
            dv.cantidad,
            dv.precio_unitario,
            dv.subtotal
        FROM detalle_venta dv
        JOIN variante_prenda vp ON dv.id_variante_prenda = vp.id_variante_prenda
        JOIN prenda p ON vp.id_prenda = p.id_prenda
        JOIN talla t ON vp.id_talla = t.id_talla
        JOIN color col ON vp.id_color = col.id_color
        WHERE dv.id_venta = %s
        ORDER BY dv.id_variante_prenda;
        """,
        (id_venta,),
    )
    items = cursor.fetchall()

    resultado = dict(cabecera)
    resultado["items"] = items
    return resultado


def listar_ventas(
    cursor: Any,
    id_cliente: int | None = None,
    id_sucursal: int | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[dict]:
    """Lista el historial de ventas con filtros opcionales."""
    condiciones = ["1=1"]
    parametros: list[Any] = []

    if id_cliente is not None:
        condiciones.append("v.id_cliente = %s")
        parametros.append(id_cliente)
    if id_sucursal is not None:
        condiciones.append("v.id_sucursal = %s")
        parametros.append(id_sucursal)

    parametros.extend([limit, skip])

    cursor.execute(
        f"""
        SELECT
            v.id_venta, v.id_cliente,
            CONCAT(c.nombre_completo) AS cliente_nombre,
            v.id_sucursal, s.nombre AS sucursal_nombre,
            v.tipo_venta, v.metodo_pago,
            v.subtotal, v.descuento, v.total, v.fecha_venta
        FROM venta v
        LEFT JOIN cliente c ON v.id_cliente = c.id_cliente
        LEFT JOIN sucursal s ON v.id_sucursal = s.id_sucursal
        WHERE {" AND ".join(condiciones)}
        ORDER BY v.fecha_venta DESC, v.id_venta DESC
        LIMIT %s OFFSET %s;
        """,
        tuple(parametros),
    )
    return cursor.fetchall()


def listar_reservas_cliente(cursor: Any, id_cliente: int) -> list[dict]:
    """Lista todas las reservas de un cliente con su estado actual."""
    cursor.execute(
        """
        SELECT
            r.id_reserva, r.id_sucursal, s.nombre AS sucursal_nombre,
            r.fecha_reserva, r.fecha_limite, r.estado, r.total
        FROM reserva r
        JOIN sucursal s ON r.id_sucursal = s.id_sucursal
        WHERE r.id_cliente = %s
        ORDER BY r.fecha_reserva DESC;
        """,
        (id_cliente,),
    )
    return cursor.fetchall()


# ─────────────────────────────────────────────────────────────────────────────
# RESERVAS PARA PROBADOR FÍSICO Y ATENCIÓN EN SUCURSAL (CU16, CU17)
# ─────────────────────────────────────────────────────────────────────────────

def _generar_qr_ticket(id_reserva: int, codigo_ticket: str, sucursal_nombre: str) -> str:
    """Genera imagen QR codificada en base64 para el ticket de reserva."""
    contenido = f"FASHIONSTORE|RESERVA|{id_reserva}|{codigo_ticket}|{sucursal_nombre}"
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=2,
    )
    qr.add_data(contenido)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def crear_reserva_probador(cursor, datos, id_usuario, ip_address):
    from app.services.commerce import reserve
    rid = reserve(cursor, datos.id_cliente, datos.id_sucursal, [x.model_dump() for x in datos.items], id_usuario)
    return obtener_ticket_reserva_qr(cursor, rid)


def obtener_ticket_reserva_qr(cursor: Any, id_o_codigo: str | int) -> dict:
    """Recupera el ticket de reserva completo con QR y desglose de prendas."""
    id_reserva: int | None = None
    if isinstance(id_o_codigo, int) or (isinstance(id_o_codigo, str) and id_o_codigo.isdigit()):
        id_reserva = int(id_o_codigo)
    elif isinstance(id_o_codigo, str) and id_o_codigo.upper().startswith("TKT-"):
        try:
            id_reserva = int(id_o_codigo.upper().replace("TKT-", ""))
        except ValueError:
            id_reserva = None

    if id_reserva is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Identificador o código de ticket de reserva inválido",
        )

    cursor.execute(
        """
        SELECT
            r.id_reserva, r.id_cliente,
            CONCAT(c.nombre_completo) AS cliente_nombre,
            r.id_sucursal, s.nombre AS sucursal_nombre,
            r.fecha_reserva, r.fecha_limite, r.estado, r.total
        FROM reserva r
        JOIN sucursal s ON r.id_sucursal = s.id_sucursal
        LEFT JOIN cliente c ON r.id_cliente = c.id_cliente
        WHERE r.id_reserva = %s;
        """,
        (id_reserva,),
    )
    cabecera = cursor.fetchone()
    if not cabecera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró la reserva con ticket #{id_reserva}",
        )

    cursor.execute(
        """
        SELECT
            dr.id_variante_prenda,
            v.sku_variante,
            p.nombre AS prenda_nombre,
            t.nombre AS talla,
            c.nombre AS color,
            dr.cantidad,
            dr.precio_unitario,
            (dr.cantidad * dr.precio_unitario) AS subtotal
        FROM detalle_reserva dr
        JOIN variante_prenda v ON dr.id_variante_prenda = v.id_variante_prenda
        JOIN prenda p ON v.id_prenda = p.id_prenda
        JOIN talla t ON v.id_talla = t.id_talla
        JOIN color c ON v.id_color = c.id_color
        WHERE dr.id_reserva = %s
        ORDER BY dr.id_variante_prenda;
        """,
        (id_reserva,),
    )
    items = cursor.fetchall()

    codigo_ticket = f"TKT-{id_reserva:06d}"
    sucursal_nom = cabecera["sucursal_nombre"] or "Sucursal"
    qr_base64 = _generar_qr_ticket(id_reserva, codigo_ticket, sucursal_nom)

    resultado = dict(cabecera)
    resultado["codigo_ticket"] = codigo_ticket
    resultado["qr_base64"] = qr_base64
    resultado["items"] = items
    return resultado


def actualizar_estado_reserva_probador(cursor, id_reserva, datos, id_usuario, ip_address):
    from app.services.commerce import transition_reservation
    transition_reservation(cursor, id_reserva, datos.nuevo_estado)
    return obtener_ticket_reserva_qr(cursor, id_reserva)


def listar_reservas_sucursal(
    cursor: Any,
    id_sucursal: int | None = None,
    estado: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[dict]:
    """Lista las reservas asignadas a una sucursal para la atención en probador (CU17)."""
    condiciones = ["1=1"]
    parametros: list[Any] = []

    if id_sucursal is not None:
        condiciones.append("r.id_sucursal = %s")
        parametros.append(id_sucursal)

    if estado is not None and estado.strip():
        condiciones.append("r.estado = %s")
        parametros.append(estado.strip())

    parametros.extend([limit, skip])

    cursor.execute(
        f"""
        SELECT
            r.id_reserva, r.id_cliente,
            CONCAT(c.nombre_completo) AS cliente_nombre,
            c.telefono AS cliente_telefono,
            r.id_sucursal, s.nombre AS sucursal_nombre,
            r.fecha_reserva, r.fecha_limite, r.estado, r.total,
            (SELECT COUNT(*) FROM detalle_reserva dr WHERE dr.id_reserva = r.id_reserva) AS total_prendas
        FROM reserva r
        JOIN sucursal s ON r.id_sucursal = s.id_sucursal
        LEFT JOIN cliente c ON r.id_cliente = c.id_cliente
        WHERE {" AND ".join(condiciones)}
        ORDER BY 
            CASE 
                WHEN r.estado = 'Pendiente' THEN 1
                WHEN r.estado = 'Preparado' THEN 2
                ELSE 3 
            END,
            r.fecha_reserva DESC
        LIMIT %s OFFSET %s;
        """,
        tuple(parametros),
    )
    return cursor.fetchall()
