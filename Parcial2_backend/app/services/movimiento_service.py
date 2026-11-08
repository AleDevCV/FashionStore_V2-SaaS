"""
=============================================================================
FASHIONSTORE - SERVICIO DE MOVIMIENTOS DE INVENTARIO (CU11)
Sistemas de Información II - UAGRM
-----------------------------------------------------------------------------
Lógica de negocio para el registro y consulta de movimientos de inventario:
Entrada y Salida delegan existencias al disparador trg_movimiento_inventario.
Traspaso valida disponibilidad y agrupa ambas patas, auditoría y resultado
idempotente en una transacción; conflictos de disponibilidad retornan 409.
Audita inmutablemente en la tabla bitacora (CU25).
=============================================================================
"""

from datetime import datetime
import hashlib
import json
from typing import Any
from fastapi import HTTPException, status
from fastapi.encoders import jsonable_encoder
import psycopg2
from psycopg2 import errors as pg_errors
from psycopg2.extras import Json

from app.schemas.movimiento import MovimientoCrear, TraspasoRespuesta
from app.services import idempotency
from app.services.commerce import authorized_branch
from app.tenant import require_context
from app.services.bitacora_service import (
    ACCION_INSERT,
    registrar_bitacora,
)


def obtener_stock_actual(
    cursor: Any,
    id_sucursal: int,
    id_variante_prenda: int,
    disponible: bool = False,
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
    if disponible:
        cursor.execute('SELECT coalesce(sum(cantidad),0) AS held FROM retencion WHERE id_sucursal=%s AND id_variante_prenda=%s AND vence>now()',
                       (id_sucursal,id_variante_prenda))
        stock = max(stock-int(cursor.fetchone()['held']),0)
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

    Entrada/Salida conservan su trigger. Traspaso ejecuta ambas patas con el
    mismo cursor y la misma transacción, sin confirmar por separado.

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
    if datos.tipo == 'Traspaso':
        return registrar_traspaso(cursor, datos, id_usuario, ip_address)

    authorized_branch(cursor, datos.id_sucursal)
    key = datos.operation_id
    if key:
        payload = datos.model_dump(exclude={'operation_id'})
        payload['motivo'] = datos.motivo.strip()
        digest, previous = idempotency.replay(cursor, 'movimiento', key, payload)
        if previous is not None:
            return previous

    # 2. Validar existencia de la variante de prenda
    cursor.execute(
        "SELECT 1 FROM variante_prenda WHERE id_variante_prenda = %s FOR UPDATE;",
        (datos.id_variante_prenda,),
    )
    if not cursor.fetchone():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La variante de prenda especificada no existe",
        )

    if datos.tipo in {'Salida', 'Ajuste'}:
        cursor.execute('SELECT stock FROM inventario WHERE id_sucursal=%s AND id_variante_prenda=%s FOR UPDATE',
                       (datos.id_sucursal, datos.id_variante_prenda))
        row = cursor.fetchone()
        stock = row['stock'] if row else 0
        cursor.execute('''SELECT coalesce(sum(cantidad),0) AS held FROM retencion
                          WHERE id_sucursal=%s AND id_variante_prenda=%s AND vence>now()''',
                       (datos.id_sucursal, datos.id_variante_prenda))
        final = datos.cantidad if datos.tipo == 'Ajuste' else stock - datos.cantidad
        if final < cursor.fetchone()['held']:
            raise HTTPException(400, 'El movimiento dejaría stock insuficiente para las reservas vigentes.')

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
        id_sucursal=datos.id_sucursal,
        operation_id=key,
    )

    # 5. Retornar movimiento enriquecido
    enriquecido = obtener_movimiento_por_id(cursor, mov["id_movimiento"])
    result = enriquecido if enriquecido else mov
    if key:
        idempotency.remember(cursor, 'movimiento', key, digest, result)
    return result


def registrar_traspaso(cursor, datos: MovimientoCrear, id_usuario: int | None, ip_address: str) -> dict:
    """Una operación lógica online, dos movimientos y un resultado idempotente."""
    ctx = require_context()
    if ctx.platform or ctx.role not in {'Administrador', 'Encargado de Sucursal'} or id_usuario != ctx.user_id:
        raise HTTPException(403, 'No tiene autorización para registrar este traspaso.')
    # Defensa también para llamadas internas: nunca aceptar el contrato antiguo.
    if datos.operation_id is None or datos.id_sucursal_destino is None or datos.id_sucursal == datos.id_sucursal_destino:
        raise HTTPException(422, 'Traspaso requiere origen, destino distinto y UUID.')
    origin, destination = datos.id_sucursal, datos.id_sucursal_destino
    payload = datos.model_dump(mode='json')
    payload['motivo'] = datos.motivo.strip()
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()
    oid = str(datos.operation_id)
    try:
        # Autorización actual, incluso en reintentos; no confiar en el UUID.
        for branch in sorted([origin, destination]):
            authorized_branch(cursor, branch)
        cursor.execute('SELECT id_sucursal FROM sucursal WHERE id_sucursal=ANY(%s) AND activa ORDER BY id_sucursal FOR SHARE', ([origin, destination],))
        if len(cursor.fetchall()) != 2:
            raise HTTPException(404, 'Sucursal no disponible.')
        cursor.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,0))', (f'transfer:{ctx.tenant_id}:{oid}',))
        cursor.execute("SELECT 1 FROM operacion_idempotente WHERE tenant_id=%s AND tipo='movimiento' AND operation_id=%s",
                       (ctx.tenant_id, oid))
        if cursor.fetchone():
            raise HTTPException(409, 'El UUID pertenece a un movimiento directo.')
        cursor.execute('SELECT payload_hash,result FROM traspaso_inventario WHERE tenant_id=%s AND operation_id=%s', (ctx.tenant_id, oid))
        existing = cursor.fetchone()
        if existing:
            if existing['payload_hash'] != digest:
                raise HTTPException(409, 'UUID de traspaso reutilizado con datos diferentes.')
            return existing['result']

        # Mismo orden que POS/reservas: variante, luego existencias.
        cursor.execute('SELECT id_variante_prenda FROM variante_prenda WHERE id_variante_prenda=%s FOR UPDATE', (datos.id_variante_prenda,))
        if not cursor.fetchone():
            raise HTTPException(404, 'La variante de prenda especificada no existe')
        cursor.execute('SELECT id_sucursal,stock FROM inventario WHERE id_sucursal=ANY(%s) AND id_variante_prenda=%s ORDER BY id_sucursal FOR UPDATE',
                       ([origin, destination], datos.id_variante_prenda))
        stocks = {row['id_sucursal']:row['stock'] for row in cursor.fetchall()}
        cursor.execute('SELECT coalesce(sum(cantidad),0) AS held FROM retencion WHERE id_sucursal=%s AND id_variante_prenda=%s AND vence>now()',
                       (origin, datos.id_variante_prenda))
        held = int(cursor.fetchone()['held'])
        if stocks.get(origin, 0) - held < datos.cantidad:
            raise HTTPException(409, 'Stock disponible insuficiente para el traspaso completo.')
        if stocks.get(destination, 0) + datos.cantidad > 2147483647:
            raise HTTPException(409, 'El stock de destino excedería el rango permitido.')
        legs = []
        for branch, kind in [(origin, 'Salida'), (destination, 'Entrada')]:
            leg = MovimientoCrear(id_sucursal=branch, id_variante_prenda=datos.id_variante_prenda,
                                  tipo=kind, cantidad=datos.cantidad, motivo=datos.motivo.strip())
            legs.append(registrar_movimiento(cursor, leg, id_usuario, ip_address))
        result = jsonable_encoder(TraspasoRespuesta(operation_id=datos.operation_id,
            id_sucursal_origen=origin, id_sucursal_destino=destination,
            id_variante_prenda=datos.id_variante_prenda, cantidad=datos.cantidad,
            motivo=datos.motivo.strip(), id_usuario=id_usuario, fecha=legs[0]['fecha'],
            movimiento_salida=legs[0], movimiento_entrada=legs[1]))
        cursor.execute('''INSERT INTO traspaso_inventario(operation_id,id_sucursal_origen,id_sucursal_destino,
            id_variante_prenda,cantidad,id_usuario,id_movimiento_salida,id_movimiento_entrada,payload_hash,result)
            VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
            (oid, origin, destination, datos.id_variante_prenda, datos.cantidad, id_usuario,
             legs[0]['id_movimiento'], legs[1]['id_movimiento'], digest, Json(result)))
        registrar_bitacora(cursor=cursor, accion=ACCION_INSERT, tabla_afectada='traspaso_inventario',
            registro_id=legs[0]['id_movimiento'], id_usuario=id_usuario, ip_address=ip_address,
            detalle=json.dumps({'operation_id':oid, 'origen':origin, 'destino':destination,
                'salida':legs[0]['id_movimiento'], 'entrada':legs[1]['id_movimiento']}, sort_keys=True))
        return result
    except psycopg2.Error as exc:
        # get_db hará rollback completo; no convertir un error SQL en éxito.
        raise HTTPException(409, 'No se confirmó el traspaso. Reintente con el mismo UUID.') from exc


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
        condiciones.append("(m.tipo = %s OR tr.operation_id IS NOT NULL)" if tipo.strip() == 'Traspaso' else "m.tipo = %s")
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
            ,tr.operation_id,tr.id_sucursal_origen,tr.id_sucursal_destino,
            tr.id_movimiento_salida,tr.id_movimiento_entrada
        FROM movimiento_inventario m
        JOIN sucursal s ON m.id_sucursal = s.id_sucursal
        JOIN variante_prenda v ON m.id_variante_prenda = v.id_variante_prenda
        JOIN prenda p ON v.id_prenda = p.id_prenda
        JOIN talla t ON v.id_talla = t.id_talla
        JOIN color c ON v.id_color = c.id_color
        LEFT JOIN usuario u ON m.id_usuario = u.id_usuario
        LEFT JOIN inventario inv ON inv.id_sucursal = m.id_sucursal AND inv.id_variante_prenda = m.id_variante_prenda
        LEFT JOIN traspaso_inventario tr ON tr.tenant_id=m.tenant_id
            AND m.id_movimiento IN (tr.id_movimiento_salida,tr.id_movimiento_entrada)
        WHERE {" AND ".join(condiciones)}
        ORDER BY m.fecha DESC, m.id_movimiento DESC
        LIMIT %s OFFSET %s;
    """

    cursor.execute(sql, tuple(parametros))
    return cursor.fetchall()
