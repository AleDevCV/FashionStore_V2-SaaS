"""
=============================================================================
FASHIONSTORE - ROUTER DE DASHBOARD GERENCIAL Y KPIS (CU24)
Sistemas de Información II - UAGRM
-----------------------------------------------------------------------------
Expone endpoints analíticos para la visualización de indicadores clave de
desempeño (KPIs) en tiempo real: ventas, finanzas, uso de probadores,
top de demanda y monitoreo multisucursal.
=============================================================================
"""

from fastapi import APIRouter, Depends

from app.database import get_db
from app.schemas.dashboard import DashboardKPIsRespuesta
from app.services import dashboard_service as svc
from app.services.auth_service import get_current_user

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard de Indicadores y KPIs (CU24)"],
)


@router.get(
    "/kpis",
    response_model=DashboardKPIsRespuesta,
    summary="Obtiene las métricas consolidadas y KPIs para el dashboard gerencial",
)
@router.get(
    "/kpis/",
    response_model=DashboardKPIsRespuesta,
    include_in_schema=False,
)
def obtener_kpis(
    cursor=Depends(get_db),
    usuario=Depends(get_current_user),
):
    """Retorna el compendio analítico de KPIs ejecutivos, gráficos de tendencia,

    distribución de canales/pagos y salud del inventario.
    """
    return svc.obtener_dashboard_kpis(cursor)


# Router adicional o alias bajo /kpis para flexibilidad
kpis_router = APIRouter(
    prefix="/kpis",
    tags=["Dashboard de Indicadores y KPIs (CU24)"],
)


@kpis_router.get(
    "",
    response_model=DashboardKPIsRespuesta,
    summary="Alias de /api/dashboard/kpis",
)
@kpis_router.get(
    "/",
    response_model=DashboardKPIsRespuesta,
    include_in_schema=False,
)
def obtener_kpis_alias(
    cursor=Depends(get_db),
    usuario=Depends(get_current_user),
):
    """Alias para consultar los KPIs del sistema."""
    return svc.obtener_dashboard_kpis(cursor)
