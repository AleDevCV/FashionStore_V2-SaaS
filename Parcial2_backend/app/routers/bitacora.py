"""
=============================================================================
FASHIONSTORE - ROUTER DE BITÁCORA DE AUDITORÍA (CU25)
Sistemas de Información II - UAGRM
=============================================================================
"""

from fastapi import APIRouter, Depends, Query

from app.database import get_db
from app.schemas.bitacora import BitacoraListadoRespuesta
from app.services import bitacora_service as svc
from app.services.auth_service import requiere_rol

router = APIRouter(
    prefix="/bitacora",
    tags=["Auditoría y Bitácora (CU25)"],
)


@router.get(
    "",
    response_model=BitacoraListadoRespuesta,
    summary="Listar eventos de la bitácora de auditoría",
)
@router.get(
    "/",
    response_model=BitacoraListadoRespuesta,
    include_in_schema=False,
)
def listar_eventos_bitacora(
    pagina: int = Query(default=1, ge=1, description="Número de página"),
    limite: int = Query(default=50, ge=1, le=200, description="Registros por página"),
    accion: str | None = Query(default=None, description="Filtro por acción"),
    tabla_afectada: str | None = Query(default=None, description="Filtro por tabla"),
    busqueda: str | None = Query(default=None, description="Término de búsqueda"),
    cursor=Depends(get_db),
    usuario=Depends(requiere_rol(["Administrador"])),
):
    """Permite al Administrador consultar y auditar todos los eventos

    registrados en la bitácora del sistema (CU25).
    """
    return svc.listar_bitacora(
        cursor=cursor,
        pagina=pagina,
        limite=limite,
        accion=accion,
        tabla_afectada=tabla_afectada,
        busqueda=busqueda,
    )
