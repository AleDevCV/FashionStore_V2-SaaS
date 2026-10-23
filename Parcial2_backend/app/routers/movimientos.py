"""
=============================================================================
FASHIONSTORE - ROUTER DE MOVIMIENTOS DE INVENTARIO (CU11)
Sistemas de Información II - UAGRM
-----------------------------------------------------------------------------
Endpoints REST para el registro de movimientos físicos (Entrada, Salida,
Traspaso) y consulta histórica del kardex de almacén. Expone tanto la ruta
canónica /movimientos-inventario como su alias /inventario/movimientos.
=============================================================================
"""

from datetime import datetime
from fastapi import APIRouter, Depends, Query, Request, status

from app.database import get_db
from app.schemas.movimiento import (
    MovimientoCrear,
    MovimientoRespuesta,
    StockRespuesta,
)
from app.services import movimiento_service as svc
from app.services.auth_service import get_current_user
from app.services.bitacora_service import obtener_ip_cliente

router = APIRouter(tags=["Movimientos de Inventario (CU11)"])


# -----------------------------------------------------------------------------
# CONSULTA DE STOCK ACTUAL
# Se declara antes de rutas con parámetros para evitar colisiones de ruta.
# -----------------------------------------------------------------------------

@router.get(
    "/movimientos-inventario/stock",
    response_model=StockRespuesta,
    summary="Consultar stock físico disponible",
)
@router.get(
    "/inventario/movimientos/stock",
    response_model=StockRespuesta,
    include_in_schema=False,
)
def consultar_stock(
    id_sucursal: int = Query(..., gt=0, description="ID de la sucursal"),
    id_variante_prenda: int = Query(..., gt=0, description="ID de la variante de prenda"),
    cursor=Depends(get_db),
    usuario=Depends(get_current_user),
):
    """Retorna las existencias físicas actuales de una variante en una sucursal específica."""
    return svc.obtener_stock_actual(
        cursor=cursor,
        id_sucursal=id_sucursal,
        id_variante_prenda=id_variante_prenda,
    )


# -----------------------------------------------------------------------------
# REGISTRO DE MOVIMIENTOS
# -----------------------------------------------------------------------------

@router.post(
    "/movimientos-inventario/",
    response_model=MovimientoRespuesta,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un movimiento de inventario",
)
@router.post(
    "/movimientos-inventario",
    response_model=MovimientoRespuesta,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
@router.post(
    "/inventario/movimientos/",
    response_model=MovimientoRespuesta,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
@router.post(
    "/inventario/movimientos",
    response_model=MovimientoRespuesta,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
def registrar_movimiento(
    datos: MovimientoCrear,
    request: Request,
    cursor=Depends(get_db),
    usuario=Depends(get_current_user),
):
    """Registra una operación en almacén (Entrada, Salida o Traspaso).

    El disparador de PostgreSQL actualiza el stock automáticamente. Si se trata
    de una Salida o Traspaso con existencias insuficientes, se retorna HTTP 400.
    """
    ip_cliente = obtener_ip_cliente(request)
    id_usuario = usuario.get("id_usuario")
    return svc.registrar_movimiento(
        cursor=cursor,
        datos=datos,
        id_usuario=id_usuario,
        ip_address=ip_cliente,
    )


# -----------------------------------------------------------------------------
# CONSULTA HISTÓRICA DE MOVIMIENTOS
# -----------------------------------------------------------------------------

@router.get(
    "/movimientos-inventario/",
    response_model=list[MovimientoRespuesta],
    summary="Listar historial de movimientos de inventario",
)
@router.get(
    "/movimientos-inventario",
    response_model=list[MovimientoRespuesta],
    include_in_schema=False,
)
@router.get(
    "/inventario/movimientos/",
    response_model=list[MovimientoRespuesta],
    include_in_schema=False,
)
@router.get(
    "/inventario/movimientos",
    response_model=list[MovimientoRespuesta],
    include_in_schema=False,
)
def listar_movimientos(
    id_sucursal: int | None = Query(default=None, description="Filtrar por sucursal"),
    id_variante_prenda: int | None = Query(default=None, description="Filtrar por variante"),
    tipo: str | None = Query(default=None, description="Filtrar por tipo: Entrada, Salida, Traspaso"),
    fecha_inicio: datetime | None = Query(default=None, description="Fecha inicial"),
    fecha_fin: datetime | None = Query(default=None, description="Fecha final"),
    skip: int = Query(default=0, ge=0, description="Desplazamiento"),
    limit: int = Query(default=50, ge=1, le=100, description="Límite de registros"),
    cursor=Depends(get_db),
    usuario=Depends(get_current_user),
):
    """Retorna el kardex histórico de movimientos con información detallada de prendas."""
    return svc.listar_movimientos(
        cursor=cursor,
        id_sucursal=id_sucursal,
        id_variante_prenda=id_variante_prenda,
        tipo=tipo,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        skip=skip,
        limit=limit,
    )
