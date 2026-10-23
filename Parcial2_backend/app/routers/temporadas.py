"""
=============================================================================
FASHIONSTORE - ROUTER DE TEMPORADAS Y COLECCIONES (CU09)
Sistemas de Información II - UAGRM
-----------------------------------------------------------------------------
Endpoints REST para el ciclo de vida de temporadas comerciales:
consulta paginada con filtros de estado y vigencia temporal, alta con
validaciones estrictas de unicidad y fechas, actualización y baja con
desasociación automática en prendas. Trazabilidad forense en bitácora (CU25).
=============================================================================
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.database import get_db
from app.schemas.temporada import (
    TemporadaActualizar,
    TemporadaCrear,
    TemporadaRespuesta,
)
from app.schemas.usuario import MensajeRespuesta
from app.services import temporada_service as svc
from app.services.auth_service import get_current_user
from app.services.bitacora_service import obtener_ip_cliente

router = APIRouter(prefix="/temporadas", tags=["Temporadas y Colecciones (CU09)"])


@router.get(
    "/",
    response_model=list[TemporadaRespuesta],
    summary="Listar temporadas con filtros de búsqueda y vigencia",
)
@router.get(
    "",
    response_model=list[TemporadaRespuesta],
    include_in_schema=False,
)
def listar_temporadas(
    busqueda: str | None = Query(
        default=None,
        description="Búsqueda por texto en nombre o descripción de la temporada",
    ),
    estado: bool | None = Query(
        default=None,
        description="Filtro por estado booleano (true=activa/habilitada, false=deshabilitada)",
    ),
    vigencia: str | None = Query(
        default=None,
        description="Filtro por vigencia temporal: 'Activa', 'Proxima' o 'Pasada'",
    ),
    skip: int = Query(default=0, ge=0, description="Número de registros a omitir"),
    limit: int = Query(default=50, ge=1, le=100, description="Límite de registros"),
    cursor=Depends(get_db),
    usuario=Depends(get_current_user),
):
    """Devuelve las temporadas comerciales registradas con filtros opcionales."""
    return svc.listar_temporadas(
        cursor=cursor,
        busqueda=busqueda,
        estado=estado,
        vigencia=vigencia,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{id_temporada}",
    response_model=TemporadaRespuesta,
    summary="Obtener detalle de una temporada por ID",
)
def obtener_temporada(
    id_temporada: int,
    cursor=Depends(get_db),
    usuario=Depends(get_current_user),
):
    """Devuelve la ficha detallada de una temporada con su total de prendas asociadas."""
    temporada = svc.obtener_temporada_por_id(cursor, id_temporada)
    if not temporada:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La temporada solicitada no existe",
        )
    return temporada


@router.post(
    "/",
    response_model=TemporadaRespuesta,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una nueva temporada comercial",
)
@router.post(
    "",
    response_model=TemporadaRespuesta,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
def crear_temporada(
    datos: TemporadaCrear,
    request: Request,
    cursor=Depends(get_db),
    usuario=Depends(get_current_user),
):
    """Da de alta una nueva temporada asegurando unicidad de nombre y rango válido de fechas."""
    ip_cliente = obtener_ip_cliente(request)
    return svc.crear_temporada(
        cursor=cursor,
        datos=datos,
        usuario=usuario,
        ip_address=ip_cliente,
    )


@router.put(
    "/{id_temporada}",
    response_model=TemporadaRespuesta,
    status_code=status.HTTP_200_OK,
    summary="Actualizar una temporada existente",
)
def actualizar_temporada(
    id_temporada: int,
    datos: TemporadaActualizar,
    request: Request,
    cursor=Depends(get_db),
    usuario=Depends(get_current_user),
):
    """Actualiza los datos de una temporada validando que no colisionen fechas ni nombre."""
    ip_cliente = obtener_ip_cliente(request)
    return svc.actualizar_temporada(
        cursor=cursor,
        id_temporada=id_temporada,
        datos=datos,
        usuario=usuario,
        ip_address=ip_cliente,
    )


@router.delete(
    "/{id_temporada}",
    response_model=MensajeRespuesta,
    status_code=status.HTTP_200_OK,
    summary="Eliminar una temporada",
)
def eliminar_temporada(
    id_temporada: int,
    request: Request,
    cursor=Depends(get_db),
    usuario=Depends(get_current_user),
):
    """Elimina físicamente una temporada desasociando automáticamente las prendas vinculadas."""
    ip_cliente = obtener_ip_cliente(request)
    return svc.eliminar_temporada(
        cursor=cursor,
        id_temporada=id_temporada,
        usuario=usuario,
        ip_address=ip_cliente,
    )
