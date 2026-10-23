"""
=============================================================================
FASHIONSTORE - ROUTER DE COMPROBANTES (CU21)
Sistemas de Información II - UAGRM
-----------------------------------------------------------------------------
Endpoints REST para la generación y consulta de comprobantes fiscales digitales:
- Generar comprobante PDF tras una venta confirmada.
- Consultar comprobante por venta o número único.
- Verificar autenticidad de un comprobante (QR público, sin JWT).
=============================================================================
"""

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import FileResponse

from app.database import get_db
from app.schemas.comprobante import ComprobanteGenerarPeticion, ComprobanteRespuesta
from app.services import comprobante_service as svc
from app.services.auth_service import get_current_user
from app.services.bitacora_service import obtener_ip_cliente

router = APIRouter(prefix="/comprobantes", tags=["Comprobantes (CU21)"])


@router.post(
    "/generar",
    response_model=ComprobanteRespuesta,
    status_code=status.HTTP_201_CREATED,
    summary="Generar comprobante fiscal PDF de una venta",
)
@router.post("/generar/", response_model=ComprobanteRespuesta, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def generar_comprobante(
    datos: ComprobanteGenerarPeticion,
    request: Request,
    cursor=Depends(get_db),
    usuario=Depends(get_current_user),
):
    """Genera el comprobante digital PDF de una venta confirmada.

    Crea el PDF con desglose de ítems, QR de verificación y datos fiscales.
    Guarda la URL en la BD y envía el PDF al correo del cliente si se indicó.
    Solo se puede generar un comprobante por venta.
    """
    ip = obtener_ip_cliente(request)
    id_usuario = usuario.get("id_usuario")
    return svc.generar_comprobante(
        cursor=cursor,
        datos=datos,
        id_usuario=id_usuario,
        ip_address=ip,
    )


@router.get(
    "/venta/{id_venta}",
    response_model=ComprobanteRespuesta,
    summary="Obtener comprobante de una venta",
)
def comprobante_por_venta(
    id_venta: int,
    cursor=Depends(get_db),
    usuario=Depends(get_current_user),
):
    """Devuelve el comprobante asociado a una venta específica."""
    return svc.obtener_comprobante_por_venta(cursor, id_venta)


@router.get(
    "/verificar/{numero}",
    summary="Verificar autenticidad de un comprobante (público — sin JWT)",
)
def verificar_comprobante(
    numero: str,
    cursor=Depends(get_db),
):
    """Endpoint público (sin JWT) para verificar si un comprobante es auténtico.

    Este endpoint es el destino del QR embebido en el PDF.
    Devuelve los datos básicos del comprobante sin información fiscal sensible.
    """
    comp = svc.obtener_comprobante_por_numero(cursor, numero)
    return {
        "valido": True,
        "numero_comprobante": comp["numero_comprobante"],
        "fecha_emision": comp["fecha_emision"],
        "id_venta": comp["id_venta"],
    }


@router.get(
    "/{numero}",
    response_model=ComprobanteRespuesta,
    summary="Obtener comprobante por número único",
)
def comprobante_por_numero(
    numero: str,
    cursor=Depends(get_db),
    usuario=Depends(get_current_user),
):
    """Devuelve el comprobante buscado por su número único (FS-YYYY-NNNNNN)."""
    return svc.obtener_comprobante_por_numero(cursor, numero)


@router.get('/{numero}/pdf', response_class=FileResponse)
def descargar_pdf_autorizado(numero: str, cursor=Depends(get_db), usuario=Depends(get_current_user)):
    from fastapi import HTTPException
    from app.tenant import require_context
    import re
    if not re.fullmatch(r'FS-[0-9]{4}-[0-9]+', numero):
        raise HTTPException(404, 'Comprobante no encontrado.')
    cursor.execute('SELECT id_comprobante FROM comprobante WHERE numero_comprobante=%s', (numero,))
    if not cursor.fetchone():
        raise HTTPException(404, 'Comprobante no encontrado.')
    path = svc.STATIC_DIR / str(require_context().tenant_id) / (numero + '.pdf')
    if not path.is_file():
        raise HTTPException(404, 'Archivo no disponible; solicite regeneración autorizada.')
    return FileResponse(path, media_type='application/pdf', filename=numero + '.pdf', headers={'Cache-Control': 'no-store'})
