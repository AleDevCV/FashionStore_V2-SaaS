"""
=============================================================================
FASHIONSTORE - ROUTER DE MONITOREO DE INVENTARIO (CU10)
Sistemas de Información II - UAGRM
-----------------------------------------------------------------------------
Endpoints REST analíticos para supervisión y monitoreo de existencias:
resumen agregado global con KPIs y desglose por sucursal física (/resumen),
y matriz consolidada de variantes con clasificación cromática de stock (/monitoreo).
=============================================================================
"""

from fastapi import APIRouter, Depends, Query

from app.database import get_db
from app.schemas.inventario import (
    EstadoStock,
    MonitoreoItemRespuesta,
    ResumenInventarioRespuesta,
)
from app.services import inventario_service as svc
from app.services.auth_service import get_current_user

router = APIRouter(
    prefix="/inventario",
    tags=["Monitoreo de Inventario Multisucursal (CU10)"],
)


@router.get(
    "/resumen",
    response_model=ResumenInventarioRespuesta,
    summary="Resumen agregado de existencias y desglose por sucursal",
)
@router.get(
    "/resumen/",
    response_model=ResumenInventarioRespuesta,
    include_in_schema=False,
)
def obtener_resumen_inventario(
    id_sucursal: int | None = Query(
        default=None,
        description="Filtro opcional por sucursal física",
    ),
    id_categoria: int | None = Query(
        default=None,
        description="Filtro opcional por categoría",
    ),
    id_temporada: int | None = Query(
        default=None,
        description="Filtro opcional por temporada comercial",
    ),
    busqueda: str | None = Query(
        default=None,
        description="Búsqueda por SKU, nombre de prenda o SKU variante",
    ),
    cursor=Depends(get_db),
    usuario=Depends(get_current_user),
):
    """Devuelve las métricas consolidadas de inventario y el desglose analítico por sucursal."""
    return svc.obtener_resumen_inventario(
        cursor=cursor,
        id_sucursal=id_sucursal,
        id_categoria=id_categoria,
        id_temporada=id_temporada,
        busqueda=busqueda,
    )


@router.get(
    "/monitoreo",
    response_model=list[MonitoreoItemRespuesta],
    summary="Monitoreo detallado de inventario con badges de estado",
)
@router.get(
    "/monitoreo/",
    response_model=list[MonitoreoItemRespuesta],
    include_in_schema=False,
)
def obtener_monitoreo_inventario(
    id_sucursal: int | None = Query(
        default=None,
        description="Filtro opcional por sucursal física",
    ),
    id_categoria: int | None = Query(
        default=None,
        description="Filtro opcional por categoría",
    ),
    id_temporada: int | None = Query(
        default=None,
        description="Filtro opcional por temporada comercial",
    ),
    busqueda: str | None = Query(
        default=None,
        description="Búsqueda libre por SKU o nombre",
    ),
    estado_stock: EstadoStock | None = Query(
        default=None,
        description="Filtro por estado: 'Optimo' (>=5), 'Bajo' (1-4) o 'Agotado' (0)",
    ),
    skip: int = Query(default=0, ge=0, description="Registros a omitir"),
    limit: int = Query(default=100, ge=1, le=200, description="Límite de registros"),
    cursor=Depends(get_db),
    usuario=Depends(get_current_user),
):
    """Retorna la matriz consolidada de variantes con su nivel de existencias y semáforo cromático."""
    return svc.obtener_monitoreo_inventario(
        cursor=cursor,
        id_sucursal=id_sucursal,
        id_categoria=id_categoria,
        id_temporada=id_temporada,
        busqueda=busqueda,
        estado_stock=estado_stock,
        skip=skip,
        limit=limit,
    )
