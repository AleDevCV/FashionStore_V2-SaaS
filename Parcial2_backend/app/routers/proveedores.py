"""
=============================================================================
FASHIONSTORE - ROUTER DE PROVEEDORES (CU12)
Sistemas de Información II - UAGRM
-----------------------------------------------------------------------------
Endpoints REST para el directorio y administración de proveedores de ropa:
consulta paginada, búsqueda por NIT o Razón Social, alta con validación de
duplicidad, modificación y borrado protegido contra compras existentes.
Auditoría inmutable de todas las mutaciones en la bitácora del sistema (CU25).
=============================================================================
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.database import get_db
from app.schemas.proveedor import (
    ProveedorActualizar,
    ProveedorCrear,
    ProveedorRespuesta,
)
from app.schemas.usuario import MensajeRespuesta
from app.services import proveedor_service as svc
from app.services.auth_service import get_current_user
from app.services.bitacora_service import obtener_ip_cliente

router = APIRouter(prefix="/proveedores", tags=["Proveedores (CU12)"])


@router.get(
    "/",
    response_model=list[ProveedorRespuesta],
    summary="Listar y buscar proveedores",
)
@router.get(
    "",
    response_model=list[ProveedorRespuesta],
    include_in_schema=False,
)
def listar_proveedores(
    busqueda: str | None = Query(
        default=None,
        description="Filtro opcional por NIT o Razón Social (búsqueda parcial)",
    ),
    skip: int = Query(default=0, ge=0, description="Registros a omitir"),
    limit: int = Query(default=50, ge=1, le=100, description="Límite de registros"),
    cursor=Depends(get_db),
    usuario=Depends(get_current_user),
):
    """Retorna el listado paginado de proveedores registrados.

    Permite filtrar mediante el parámetro `busqueda` que evalúa coincidencias
    insensibles a mayúsculas sobre las columnas `nit` y `razon_social`.
    """
    return svc.listar_proveedores(
        cursor=cursor,
        busqueda=busqueda,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{id_proveedor}",
    response_model=ProveedorRespuesta,
    summary="Obtener un proveedor por su ID",
)
def obtener_proveedor(
    id_proveedor: int,
    cursor=Depends(get_db),
    usuario=Depends(get_current_user),
):
    """Devuelve los datos de un proveedor específico identificado por su ID."""
    proveedor = svc.obtener_proveedor_por_id(cursor, id_proveedor)
    if not proveedor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El proveedor solicitado no existe",
        )
    return proveedor


@router.post(
    "/",
    response_model=ProveedorRespuesta,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un nuevo proveedor",
)
@router.post(
    "",
    response_model=ProveedorRespuesta,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
def crear_proveedor(
    datos: ProveedorCrear,
    request: Request,
    cursor=Depends(get_db),
    usuario=Depends(get_current_user),
):
    """Crea un nuevo proveedor en la plataforma asegurando la unicidad del NIT.

    Registra el evento en la bitácora con IP y usuario ejecutor.
    """
    ip_cliente = obtener_ip_cliente(request)
    return svc.crear_proveedor(
        cursor=cursor,
        datos=datos,
        usuario=usuario,
        ip_address=ip_cliente,
    )


@router.put(
    "/{id_proveedor}",
    response_model=ProveedorRespuesta,
    status_code=status.HTTP_200_OK,
    summary="Actualizar datos de un proveedor",
)
def actualizar_proveedor(
    id_proveedor: int,
    datos: ProveedorActualizar,
    request: Request,
    cursor=Depends(get_db),
    usuario=Depends(get_current_user),
):
    """Modifica total o parcialmente los datos de un proveedor existente.

    Valida que no se duplique el NIT con otro proveedor registrado y audita en bitácora.
    """
    ip_cliente = obtener_ip_cliente(request)
    return svc.actualizar_proveedor(
        cursor=cursor,
        id_proveedor=id_proveedor,
        datos=datos,
        usuario=usuario,
        ip_address=ip_cliente,
    )


@router.delete(
    "/{id_proveedor}",
    response_model=MensajeRespuesta,
    status_code=status.HTTP_200_OK,
    summary="Eliminar un proveedor",
)
def eliminar_proveedor(
    id_proveedor: int,
    request: Request,
    cursor=Depends(get_db),
    usuario=Depends(get_current_user),
):
    """Elimina físicamente un proveedor si no tiene historial de compras vinculadas.

    Si existen compras asociadas, retorna HTTP 409 (Conflicto de Integridad Referencial).
    """
    ip_cliente = obtener_ip_cliente(request)
    return svc.eliminar_proveedor(
        cursor=cursor,
        id_proveedor=id_proveedor,
        usuario=usuario,
        ip_address=ip_cliente,
    )
