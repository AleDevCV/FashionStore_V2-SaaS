"""
=============================================================================
FASHIONSTORE - SERVICIO DE COMPRAS (CU13)
Sistemas de Información II - UAGRM
-----------------------------------------------------------------------------
Lógica de negocio para el procesamiento atómico de adquisición de productos:
1. Inserción de cabecera en `compra`.
2. Inserción de ítems en `detalle_compra`.
3. Inserción de movimientos tipo 'Entrada' en `movimiento_inventario` que
   disparan automáticamente la actualización física de `inventario.stock`.
4. Cálculo financiero con 13% IVA (Bolivia).
5. Garantía estricta de rollback transaccional ante cualquier excepción.
6. Registro inmutable en la bitácora del sistema (CU25).
=============================================================================
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Any
from fastapi import HTTPException, status
import psycopg2
from psycopg2 import errors as pg_errors

from app.schemas.compra import CompraCrear
from app.services.bitacora_service import (
    ACCION_INSERT,
    registrar_bitacora,
)


def registrar_compra(
    cursor: Any,
    datos: CompraCrear,
    id_usuario: int | None,
    ip_address: str,
) -> dict:
    """Registra una adquisición completa bajo una estricta transacción atómica.

    Parámetros:
        cursor: cursor activo de PostgreSQL inyectado por get_db.
        datos: cabecera e ítems de la compra.
        id_usuario: ID del usuario autenticado que registra la compra.
        ip_address: dirección IP del cliente.

    Retorna:
        dict: estructura completa de la compra registrada con ítems y totales.

    Errores:
        HTTP 400: detalle vacío, cantidades <= 0, costos < 0, o variantes repetidas.
        HTTP 404: proveedor, sucursal o variantes inexistentes.
    """
    items = datos.items or datos.detalles
    if not items or len(items) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La compra debe tener al menos un detalle de producto",
        )

    # 1. Validar integridad de los ítems
    variantes_vistas = set()
    for item in items:
        if item.cantidad <= 0 or item.costo_unitario < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La cantidad debe ser mayor a cero y el costo unitario no negativo",
            )
        if item.id_variante_prenda in variantes_vistas:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se puede incluir la misma variante múltiples veces en la misma compra",
            )
        variantes_vistas.add(item.id_variante_prenda)

    # 2. Validar existencia del proveedor
    cursor.execute(
        "SELECT id_proveedor, razon_social FROM proveedor WHERE id_proveedor = %s;",
        (datos.id_proveedor,),
    )
    proveedor = cursor.fetchone()
    if not proveedor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El proveedor especificado no existe",
        )

    # 3. Validar existencia de la sucursal
    cursor.execute(
        "SELECT id_sucursal, nombre FROM sucursal WHERE id_sucursal = %s;",
        (datos.id_sucursal,),
    )
    sucursal = cursor.fetchone()
    if not sucursal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La sucursal especificada no existe",
        )

    # 4. Validar existencia de todas las variantes
    ids_variantes = list(variantes_vistas)
    cursor.execute(
        "SELECT id_variante_prenda FROM variante_prenda WHERE id_variante_prenda = ANY(%s);",
        (ids_variantes,),
    )
    variantes_encontradas = cursor.fetchall()
    if len(variantes_encontradas) != len(ids_variantes):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Una o más variantes de prenda especificadas no existen",
        )

    # 5. Cálculo tributario y financiero (13% IVA Bolivia)
    subtotal = Decimal("0.00")
    for item in items:
        subtotal += Decimal(str(item.cantidad)) * Decimal(str(item.costo_unitario))

    subtotal = subtotal.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    iva = (subtotal * Decimal("0.13")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    total = (subtotal + iva).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # 6. Inserción de cabecera en `compra`
    try:
        cursor.execute(
            """
            INSERT INTO compra (id_proveedor, id_sucursal, total, id_usuario)
            VALUES (%s, %s, %s, %s)
            RETURNING id_compra, fecha;
            """,
            (datos.id_proveedor, datos.id_sucursal, total, id_usuario),
        )
        compra_row = cursor.fetchone()
        id_compra = compra_row["id_compra"]
        fecha_compra = compra_row["fecha"]

        # 7. Inserción de cada ítem en `detalle_compra` y en `movimiento_inventario`
        for item in items:
            cursor.execute(
                """
                INSERT INTO detalle_compra (id_compra, id_variante_prenda, cantidad, costo_unitario)
                VALUES (%s, %s, %s, %s);
                """,
                (id_compra, item.id_variante_prenda, item.cantidad, item.costo_unitario),
            )

            # Movimiento de inventario que disparará el trigger trg_movimiento_inventario
            motivo_mov = f"Adquisición por compra #{id_compra} CU13"
            cursor.execute(
                """
                INSERT INTO movimiento_inventario
                    (id_sucursal, id_variante_prenda, tipo, cantidad, motivo, id_usuario)
                VALUES
                    (%s, %s, 'Entrada', %s, %s, %s);
                """,
                (
                    datos.id_sucursal,
                    item.id_variante_prenda,
                    item.cantidad,
                    motivo_mov,
                    id_usuario,
                ),
            )

        # 8. Registro de auditoría inmutable en `bitacora`
        registrar_bitacora(
            cursor=cursor,
            accion=ACCION_INSERT,
            tabla_afectada="compra",
            registro_id=id_compra,
            detalle=(
                f"Registro de compra #{id_compra} a proveedor {datos.id_proveedor} "
                f"('{proveedor['razon_social']}') en sucursal {datos.id_sucursal} "
                f"por un total de {total} Bs (Subtotal: {subtotal}, IVA 13%: {iva}) "
                f"con {len(items)} ítems."
            ),
            id_usuario=id_usuario,
            ip_address=ip_address,
        )

    except (psycopg2.Error, Exception) as exc:
        # Cualquier fallo aborta la transacción automáticamente al salir del bloque
        if isinstance(exc, HTTPException):
            raise exc
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al procesar la compra: {str(exc)}",
        )

    # 9. Retornar la compra completa detallada
    return obtener_compra_por_id(cursor, id_compra)


def listar_compras(
    cursor: Any,
    skip: int = 0,
    limit: int = 50,
    id_proveedor: int | None = None,
    id_sucursal: int | None = None,
) -> list[dict]:
    """Lista el historial de compras con filtros opcionales y cálculo desglosado.

    Parámetros:
        cursor: cursor activo de PostgreSQL.
        skip: desplazamiento de paginación.
        limit: límite de registros.
        id_proveedor: filtro opcional por proveedor.
        id_sucursal: filtro opcional por sucursal receptora.

    Retorna:
        list[dict]: lista de compras registradas.
    """
    condiciones = ["1=1"]
    parametros: list[Any] = []

    if id_proveedor is not None:
        condiciones.append("c.id_proveedor = %s")
        parametros.append(id_proveedor)

    if id_sucursal is not None:
        condiciones.append("c.id_sucursal = %s")
        parametros.append(id_sucursal)

    parametros.append(limit)
    parametros.append(skip)

    sql = f"""
        SELECT 
            c.id_compra,
            c.id_proveedor,
            p.razon_social AS proveedor_razon_social,
            c.id_sucursal,
            s.nombre AS sucursal_nombre,
            c.fecha,
            ROUND(c.total / 1.13, 2) AS subtotal,
            ROUND(c.total - (c.total / 1.13), 2) AS iva,
            c.total,
            c.id_usuario,
            CONCAT(u.nombre, ' ', u.apellido) AS usuario_nombre,
            (SELECT COUNT(*) FROM detalle_compra dc WHERE dc.id_compra = c.id_compra) AS total_items
        FROM compra c
        JOIN proveedor p ON c.id_proveedor = p.id_proveedor
        JOIN sucursal s ON c.id_sucursal = s.id_sucursal
        LEFT JOIN usuario u ON c.id_usuario = u.id_usuario
        WHERE {" AND ".join(condiciones)}
        ORDER BY c.fecha DESC, c.id_compra DESC
        LIMIT %s OFFSET %s;
    """

    cursor.execute(sql, tuple(parametros))
    return cursor.fetchall()


def obtener_compra_por_id(cursor: Any, id_compra: int) -> dict:
    """Recupera la cabecera y el detalle de una compra específica.

    Parámetros:
        cursor: cursor activo de PostgreSQL.
        id_compra: ID primario de la compra.

    Retorna:
        dict: estructura completa de la compra con sus ítems.

    Errores:
        HTTP 404: si la compra no existe.
    """
    cursor.execute(
        """
        SELECT 
            c.id_compra,
            c.id_proveedor,
            p.razon_social AS proveedor_razon_social,
            c.id_sucursal,
            s.nombre AS sucursal_nombre,
            c.fecha,
            ROUND(c.total / 1.13, 2) AS subtotal,
            ROUND(c.total - (c.total / 1.13), 2) AS iva,
            c.total,
            c.id_usuario,
            CONCAT(u.nombre, ' ', u.apellido) AS usuario_nombre,
            (SELECT COUNT(*) FROM detalle_compra dc WHERE dc.id_compra = c.id_compra) AS total_items
        FROM compra c
        JOIN proveedor p ON c.id_proveedor = p.id_proveedor
        JOIN sucursal s ON c.id_sucursal = s.id_sucursal
        LEFT JOIN usuario u ON c.id_usuario = u.id_usuario
        WHERE c.id_compra = %s;
        """,
        (id_compra,),
    )
    cabecera = cursor.fetchone()
    if not cabecera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La compra solicitada no existe",
        )

    # Obtener el detalle de ítems con información completa de prendas
    cursor.execute(
        """
        SELECT 
            dc.id_variante_prenda,
            v.sku_variante,
            pr.nombre AS prenda_nombre,
            t.nombre AS talla,
            col.nombre AS color,
            dc.cantidad,
            dc.costo_unitario,
            (dc.cantidad * dc.costo_unitario) AS subtotal_item
        FROM detalle_compra dc
        JOIN variante_prenda v ON dc.id_variante_prenda = v.id_variante_prenda
        JOIN prenda pr ON v.id_prenda = pr.id_prenda
        JOIN talla t ON v.id_talla = t.id_talla
        JOIN color col ON v.id_color = col.id_color
        WHERE dc.id_compra = %s
        ORDER BY dc.id_variante_prenda ASC;
        """,
        (id_compra,),
    )
    detalles = cursor.fetchall()

    resultado = dict(cabecera)
    resultado["items"] = detalles
    resultado["detalles"] = detalles
    return resultado
