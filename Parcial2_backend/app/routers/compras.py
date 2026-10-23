"""
=============================================================================
FASHIONSTORE - ROUTER DE COMPRAS (CU13)
Sistemas de Información II - UAGRM
-----------------------------------------------------------------------------
Endpoints REST para el procesamiento de compras de mercadería a proveedores:
registro transaccional atómico (cabecera + detalle + movimiento de inventario
con trigger PL/pgSQL), consulta histórica y detalle individual de compras.
=============================================================================
"""

from fastapi import APIRouter, Depends, Query, Request, status

from app.database import get_db
from app.schemas.compra import (
    CompraCrear,
    CompraDetalladaRespuesta,
    CompraRespuesta,
)
from app.services import compra_service as svc
from app.services.auth_service import get_current_user
from app.services.bitacora_service import obtener_ip_cliente

router = APIRouter(prefix="/compras", tags=["Compras (CU13)"])


@router.post(
    "/",
    response_model=CompraDetalladaRespuesta,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar una nueva compra de productos",
)
@router.post(
    "",
    response_model=CompraDetalladaRespuesta,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
def registrar_compra(
    datos: CompraCrear,
    request: Request,
    cursor=Depends(get_db),
    usuario=Depends(get_current_user),
):
    """Registra una compra completa bajo una estricta transacción atómica.

    Inserta cabecera en compra, líneas en detalle_compra, entradas en
    movimiento_inventario (disparando el trigger que incrementa el stock),
    calcula el 13% de IVA y audita en la bitácora inmutable.
    """
    ip_cliente = obtener_ip_cliente(request)
    id_usuario = usuario.get("id_usuario")
    return svc.registrar_compra(
        cursor=cursor,
        datos=datos,
        id_usuario=id_usuario,
        ip_address=ip_cliente,
    )


@router.get(
    "/",
    response_model=list[CompraRespuesta],
    summary="Listar compras realizadas",
)
@router.get(
    "",
    response_model=list[CompraRespuesta],
    include_in_schema=False,
)
def listar_compras(
    skip: int = Query(default=0, ge=0, description="Registros a omitir"),
    limit: int = Query(default=50, ge=1, le=100, description="Límite de registros"),
    id_proveedor: int | None = Query(default=None, description="Filtrar por proveedor"),
    id_sucursal: int | None = Query(default=None, description="Filtrar por sucursal receptora"),
    cursor=Depends(get_db),
    usuario=Depends(get_current_user),
):
    """Retorna el listado paginado de adquisiciones con subtotales e IVA resueltos."""
    return svc.listar_compras(
        cursor=cursor,
        skip=skip,
        limit=limit,
        id_proveedor=id_proveedor,
        id_sucursal=id_sucursal,
    )


@router.get(
    "/{id_compra}",
    response_model=CompraDetalladaRespuesta,
    summary="Obtener detalle completo de una compra",
)
def obtener_compra(
    id_compra: int,
    cursor=Depends(get_db),
    usuario=Depends(get_current_user),
):
    """Devuelve la información cabecera de la compra junto con todos sus ítems detallados."""
    return svc.obtener_compra_por_id(cursor, id_compra)
