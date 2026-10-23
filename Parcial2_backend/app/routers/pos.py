"""
=============================================================================
FASHIONSTORE - ROUTER DE TERMINAL POS (CU19)
Sistemas de Información II - UAGRM
-----------------------------------------------------------------------------
Endpoints REST para la terminal de caja presencial:
- Catálogo rápido con stock por sucursal y búsqueda por código de barras/SKU.
- Carga de reservas físicas de probador (CU16, CU17).
- Procesamiento sincrónico de cobro presencial (Efectivo/Tarjeta/QR) con emisión de recibo.
=============================================================================
"""

from fastapi import APIRouter, Depends, Query, Request, status

from app.database import get_db
from app.schemas.pos import (
    POSProductoVariante,
    POSReservaCargadaRespuesta,
    POSVentaCrear,
    POSVentaRespuesta,
)
from app.services import pos_service as svc
from app.services.auth_service import get_current_user
from app.services.bitacora_service import obtener_ip_cliente

router = APIRouter(prefix="/pos", tags=["Terminal POS de Caja (CU19)"])


@router.get(
    "/productos",
    response_model=list[POSProductoVariante],
    summary="Catálogo rápido de variantes con stock para POS",
)
@router.get(
    "/productos/",
    response_model=list[POSProductoVariante],
    include_in_schema=False,
)
def listar_productos_pos_endpoint(
    id_sucursal: int = Query(..., description="ID de la sucursal activa de la caja"),
    q: str = Query(default="", description="Búsqueda por SKU / código de barras o nombre"),
    id_categoria: int | None = Query(default=None, description="Filtrar por categoría"),
    solo_stock: bool = Query(default=False, description="Mostrar solo variantes con existencias > 0"),
    cursor=Depends(get_db),
    usuario=Depends(get_current_user),
):
    """Retorna las variantes disponibles en la sucursal seleccionada para el cajero."""
    return svc.listar_productos_pos(
        cursor=cursor,
        id_sucursal=id_sucursal,
        query=q,
        id_categoria=id_categoria,
        solo_con_stock=solo_stock,
    )


@router.get(
    "/reserva/{codigo_o_id}",
    response_model=POSReservaCargadaRespuesta,
    summary="Cargar reserva de probador para facturación en caja",
)
def cargar_reserva_pos_endpoint(
    codigo_o_id: str,
    cursor=Depends(get_db),
    usuario=Depends(get_current_user),
):
    """Carga los ítems y datos del cliente de una reserva física para transferirlos al ticket de cobro."""
    return svc.cargar_reserva_pos(cursor=cursor, codigo_o_id=codigo_o_id)


@router.post(
    "/ventas",
    response_model=POSVentaRespuesta,
    status_code=status.HTTP_201_CREATED,
    summary="Consolidar venta presencial en terminal POS",
)
@router.post(
    "/ventas/",
    response_model=POSVentaRespuesta,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
def procesar_venta_pos_endpoint(
    datos: POSVentaCrear,
    request: Request,
    cursor=Depends(get_db),
    usuario=Depends(get_current_user),
):
    """Registra la venta presencial en caja:
    - Descuenta stock en la sucursal activa vía disparador PL/pgSQL.
    - Calcula vuelto o confirma transacción con tarjeta / QR.
    - Genera comprobante fiscal digital PDF en formato estándar.
    - Registra auditoría inmutable en bitácora.
    """
    ip = obtener_ip_cliente(request)
    id_usuario = usuario.get("id_usuario")
    return svc.procesar_venta_pos(
        cursor=cursor,
        datos=datos,
        id_usuario=id_usuario,
        ip_address=ip,
    )
