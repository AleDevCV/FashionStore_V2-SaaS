"""
=============================================================================
FASHIONSTORE - ROUTER DE BITÁCORA DE AUDITORÍA (CU25)
Sistemas de Información II - UAGRM
=============================================================================
"""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

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
    fecha_inicio: date | None = None,
    fecha_fin: date | None = None,
    usuario_id: int | None = Query(default=None, gt=0),
    uuid: UUID | None = None,
    cursor=Depends(get_db),
    usuario=Depends(requiere_rol(["Administrador", "Encargado de Sucursal"])),
):
    """Permite al Administrador consultar y auditar todos los eventos

    registrados en la bitácora del sistema (CU25).
    """
    if fecha_inicio and fecha_fin and fecha_inicio > fecha_fin:
        raise HTTPException(422, 'La fecha inicial debe ser anterior o igual a la final.')
    return svc.listar_bitacora(
        cursor=cursor,
        pagina=pagina,
        limite=limite,
        accion=accion,
        tabla_afectada=tabla_afectada,
        busqueda=busqueda,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        usuario_id=usuario_id,
        operation_id=uuid,
    )
