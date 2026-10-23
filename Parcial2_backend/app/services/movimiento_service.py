"""
=============================================================================
FASHIONSTORE - SERVICIO DE MOVIMIENTOS DE INVENTARIO (CU11)
Sistemas de Información II - UAGRM
-----------------------------------------------------------------------------
Lógica de negocio para el registro y consulta de movimientos de inventario:
Entrada, Salida y Traspaso. Delega la sincronización de existencias al
disparador PL/pgSQL trg_movimiento_inventario y captura excepciones de stock
insuficiente traduciéndolas a respuestas HTTP 400.
Audita inmutablemente en la tabla bitacora (CU25).
=============================================================================
"""

from datetime import datetime
from typing import Any
from fastapi import HTTPException, status
import psycopg2
from psycopg2 import errors as pg_errors

from app.schemas.movimiento import MovimientoCrear
from app.services.bitacora_service import (
    ACCION_INSERT,
    registrar_bitacora,
)


def obtener_stock_actual(
    cursor: Any,
    id_sucursal: int,
    id_variante_prenda: int,
) -> dict:
    """Consulta el stock físico registrado en inventario para una variante en una sucursal.

    Parámetros:
        cursor: cursor activo de PostgreSQL.
        id_sucursal: ID de la sucursal.
        id_variante_prenda: ID de la variante física.

    Retorna:
        dict: objeto con id_sucursal, id_variante_prenda y stock (entero >= 0).
    """
    cursor.execute(
        """
        SELECT COALESCE(stock, 0) AS stock
        FROM inventario
        WHERE id_sucursal = %s AND id_variante_prenda = %s;
        """,
        (id_sucursal, id_variante_prenda),
    )
    row = cursor.fetchone()
    stock = row["stock"] if row else 0
    return {
        "id_sucursal": id_sucursal,
        "id_variante_prenda": id_variante_prenda,
        "stock": stock,
    }


def obtener_movimiento_por_id(cursor: Any, id_movimiento: int) -> dict | None:
    """Obtiene un movimiento con su información relacionada (prenda, talla, color, etc.).

    Parámetros:
        cursor: cursor activo de PostgreSQL.
        id_movimiento: ID primario del movimiento.

    Retorna:
        dict | None: registro enriquecido o None.
    """
    cursor.execute(
        """
        SELECT 
            m.id_movimiento,
            m.id_sucursal,
            s.nombre AS sucursal_nombre,
            m.id_variante_prenda,
            v.sku_variante,
            p.nombre AS prenda_nombre,
            t.nombre AS talla,
            c.nombre AS color,
            m.tipo,
            m.cantidad,
            m.motivo,
            m.id_usuario,
            CONCAT(u.nombre, ' ', u.apellido) AS usuario_nombre,
            m.fecha,
            COALESCE(inv.stock, 0) AS stock_actual
        FROM movimiento_inventario m
        JOIN sucursal s ON m.id_sucursal = s.id_sucursal
        JOIN variante_prenda v ON m.id_variante_prenda = v.id_variante_prenda
        JOIN prenda p ON v.id_prenda = p.id_prenda
        JOIN talla t ON v.id_talla = t.id_talla
        JOIN color c ON v.id_color = c.id_color
        LEFT JOIN usuario u ON m.id_usuario = u.id_usuario
        LEFT JOIN inventario inv ON inv.id_sucursal = m.id_sucursal AND inv.id_variante_prenda = m.id_variante_prenda
        WHERE m.id_movimiento = %s;
        """,
        (id_movimiento,),
    )
    return cursor.fetchone()


def registrar_movimiento(
    cursor: Any,
    datos: MovimientoCrear,
    id_usuario: int | None,
    ip_address: str,
) -> dict:
    """Registra un movimiento en inventario delegando al trigger de PostgreSQL.

    Si el tipo es 'Salida' o 'Traspaso' y no hay stock disponible, el trigger
    actualizar_stock_por_movimiento() emite una excepción que aquí se traduce
    en HTTP 400.

    Parámetros:
        cursor: cursor activo de PostgreSQL.
        datos: datos del movimiento a registrar.
        id_usuario: ID del usuario autenticado que realiza la acción.
        ip_address: IP del cliente que realiza la petición.

    Retorna:
        dict: movimiento registrado con relaciones resueltas.

    Errores:
        HTTP 400: stock insuficiente o datos no válidos.
        HTTP 404: sucursal o variante inexistente.
    """
    # 1. Validar existencia de la sucursal
    cursor.execute(
        "SELECT 1 FROM sucursal WHERE id_sucursal = %s;",
        (datos.id_sucursal,),
    )
    if not cursor.fetchone():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La sucursal especificada no existe",
        )

    # 2. Validar existencia de la variante de prenda
    cursor.execute(
        "SELECT 1 FROM variante_prenda WHERE id_variante_prenda = %s;",
        (datos.id_variante_prenda,),
    )
    if not cursor.fetchone():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La variante de prenda especificada no existe",
        )

    # 3. Inserción con disparo de trigger de PostgreSQL
    try:
        cursor.execute(
            """
            INSERT INTO movimiento_inventario
                (id_sucursal, id_variante_prenda, tipo, cantidad, motivo, id_usuario)
            VALUES
                (%s, %s, %s, %s, %s, %s)
            RETURNING id_movimiento, id_sucursal, id_variante_prenda, tipo, cantidad, motivo, id_usuario, fecha;
            """,
            (
                datos.id_sucursal,
                datos.id_variante_prenda,
                datos.tipo,
                datos.cantidad,
                datos.motivo.strip(),
                id_usuario,
            ),
        )
        mov = cursor.fetchone()
    except (pg_errors.RaiseException, psycopg2.Error) as exc:
        err_msg = str(exc)
        if "Stock insuficiente" in err_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Stock insuficiente en la sucursal para realizar este movimiento.",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error en movimiento de inventario: {err_msg}",
        )

    # 4. Auditoría en bitácora inmutable
    registrar_bitacora(
        cursor=cursor,
        accion=ACCION_INSERT,
        tabla_afectada="movimiento_inventario",
        registro_id=mov["id_movimiento"],
        detalle=(
            f"Movimiento '{datos.tipo}' de {datos.cantidad} unidad(es) "
            f"en sucursal {datos.id_sucursal} (Variante {datos.id_variante_prenda}). "
            f"Motivo: {datos.motivo}"
        ),
        id_usuario=id_usuario,
        ip_address=ip_address,
    )

    # 5. Retornar movimiento enriquecido
    enriquecido = obtener_movimiento_por_id(cursor, mov["id_movimiento"])
    return enriquecido if enriquecido else mov


def listar_movimientos(
    cursor: Any,
    id_sucursal: int | None = None,
    id_variante_prenda: int | None = None,
    tipo: str | None = None,
    fecha_inicio: datetime | None = None,
    fecha_fin: datetime | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[dict]:
    """Consulta el historial de movimientos de inventario con filtros dinámicos.

    Parámetros:
        cursor: cursor activo de PostgreSQL.
        id_sucursal: filtro opcional por sucursal.
        id_variante_prenda: filtro opcional por variante.
        tipo: filtro opcional por tipo ('Entrada', 'Salida', 'Traspaso').
        fecha_inicio: inicio del rango de fechas.
        fecha_fin: fin del rango de fechas.
        skip: desplazamiento de paginación.
        limit: límite de registros.

    Retorna:
        list[dict]: registros enriquecidos de movimientos.
    """
    condiciones = ["1=1"]
    parametros: list[Any] = []

    if id_sucursal is not None:
        condiciones.append("m.id_sucursal = %s")
        parametros.append(id_sucursal)

    if id_variante_prenda is not None:
        condiciones.append("m.id_variante_prenda = %s")
        parametros.append(id_variante_prenda)

    if tipo is not None and tipo.strip():
        condiciones.append("m.tipo = %s")
        parametros.append(tipo.strip())

    if fecha_inicio is not None:
        condiciones.append("m.fecha >= %s")
        parametros.append(fecha_inicio)

    if fecha_fin is not None:
        condiciones.append("m.fecha <= %s")
        parametros.append(fecha_fin)

    parametros.append(limit)
    parametros.append(skip)

    sql = f"""
        SELECT 
            m.id_movimiento,
            m.id_sucursal,
            s.nombre AS sucursal_nombre,
            m.id_variante_prenda,
            v.sku_variante,
            p.nombre AS prenda_nombre,
            t.nombre AS talla,
            c.nombre AS color,
            m.tipo,
            m.cantidad,
            m.motivo,
            m.id_usuario,
            CONCAT(u.nombre, ' ', u.apellido) AS usuario_nombre,
            m.fecha,
            COALESCE(inv.stock, 0) AS stock_actual
        FROM movimiento_inventario m
        JOIN sucursal s ON m.id_sucursal = s.id_sucursal
        JOIN variante_prenda v ON m.id_variante_prenda = v.id_variante_prenda
        JOIN prenda p ON v.id_prenda = p.id_prenda
        JOIN talla t ON v.id_talla = t.id_talla
        JOIN color c ON v.id_color = c.id_color
        LEFT JOIN usuario u ON m.id_usuario = u.id_usuario
        LEFT JOIN inventario inv ON inv.id_sucursal = m.id_sucursal AND inv.id_variante_prenda = m.id_variante_prenda
        WHERE {" AND ".join(condiciones)}
        ORDER BY m.fecha DESC, m.id_movimiento DESC
        LIMIT %s OFFSET %s;
    """

    cursor.execute(sql, tuple(parametros))
    return cursor.fetchall()
