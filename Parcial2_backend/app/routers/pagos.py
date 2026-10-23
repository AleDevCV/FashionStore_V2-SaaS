"""
=============================================================================
FASHIONSTORE - ROUTER DE PAGOS (CU20)
Sistemas de Información II - UAGRM
-----------------------------------------------------------------------------
Endpoints REST para la integración con pasarelas de pago:
- Stripe Checkout Session (tarjeta internacional).
- Webhook de Stripe (sin JWT — autenticado por firma criptográfica).
- Generador de QR boliviano (pago local).
- Confirmación manual de pago QR.
- Historial de transacciones por venta.
=============================================================================
"""

from fastapi import APIRouter, Depends, Request, status

from app.database import get_db
from app.schemas.pago import (
    PagoTransaccionRespuesta,
    QRConfirmarPeticion,
    QRGenerarPeticion,
    QRGenerarRespuesta,
    StripeCheckoutPeticion,
    StripeCheckoutRespuesta,
)
from app.services import pago_service as svc
from app.services.auth_service import get_current_user, requiere_rol
from app.services.bitacora_service import obtener_ip_cliente

router = APIRouter(prefix="/pagos", tags=["Pagos (CU20)"])


# ─────────────────────────────────────────────────────────────────────────────
# STRIPE
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/stripe/crear-sesion",
    response_model=StripeCheckoutRespuesta,
    status_code=status.HTTP_201_CREATED,
    summary="Crear sesión de pago en Stripe Checkout",
)
def crear_sesion_stripe(
    datos: StripeCheckoutPeticion,
    request: Request,
    cursor=Depends(get_db),
    usuario=Depends(get_current_user),
):
    """Crea una sesión de Stripe Checkout para la reserva especificada.

    Devuelve la URL de pago a la que el frontend debe redirigir al cliente.
    Stripe llama al webhook /stripe/webhook al confirmar el pago.
    """
    ip = obtener_ip_cliente(request)
    id_usuario = usuario.get("id_usuario")
    return svc.crear_sesion_stripe(cursor=cursor, datos=datos, id_usuario=id_usuario, ip_address=ip)


@router.post(
    "/stripe/webhook",
    status_code=status.HTTP_200_OK,
    summary="Webhook de Stripe (sin JWT — autenticado por firma)",
)
async def stripe_webhook(request: Request, cursor=Depends(get_db)):
    """Procesa eventos de Stripe enviados automáticamente al confirmar un pago.

    La autenticación se realiza mediante la firma criptográfica de Stripe
    (Stripe-Signature header), no por JWT de FashionStore.
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")
    ip = obtener_ip_cliente(request)
    return svc.procesar_webhook_stripe(
        cursor=cursor,
        payload=payload,
        sig_header=sig_header,
        ip_address=ip,
    )


# ─────────────────────────────────────────────────────────────────────────────
# QR BOLIVIANO
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/qr/generar",
    response_model=QRGenerarRespuesta,
    status_code=status.HTTP_201_CREATED,
    summary="Generar código QR de pago boliviano",
)
def generar_qr(
    datos: QRGenerarPeticion,
    request: Request,
    cursor=Depends(get_db),
    usuario=Depends(get_current_user),
):
    """Genera un código QR con los datos de pago de la reserva.

    El QR contiene: FASHIONSTORE|<referencia>|<monto>|<concepto>.
    Válido por 15 minutos. La confirmación se realiza en /qr/confirmar.
    """
    ip = obtener_ip_cliente(request)
    id_usuario = usuario.get("id_usuario")
    return svc.generar_qr_boliviano(cursor=cursor, datos=datos, id_usuario=id_usuario, ip_address=ip)


@router.post(
    "/qr/confirmar",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Confirmar pago QR manualmente",
)
def confirmar_qr(
    datos: QRConfirmarPeticion,
    request: Request,
    cursor=Depends(get_db),
    usuario=Depends(requiere_rol(["Administrador", "Encargado de Sucursal", "Cajero (POS)"])),
):
    """Confirma manualmente un pago QR boliviano validando la referencia.

    Al confirmar, la reserva se convierte en venta y el inventario se actualiza.
    """
    ip = obtener_ip_cliente(request)
    id_usuario = usuario.get("id_usuario")
    return svc.confirmar_pago_qr(cursor=cursor, datos=datos, id_usuario=id_usuario, ip_address=ip)


# ─────────────────────────────────────────────────────────────────────────────
# HISTORIAL DE PAGOS
# ─────────────────────────────────────────────────────────────────────────────

@router.get('/pendientes')
def pending_payments(_=Depends(requiere_rol(['Administrador','Encargado de Sucursal','Cajero (POS)'])),cursor=Depends(get_db)):
    cursor.execute("SELECT p.id_pago,p.id_reserva,p.pasarela,p.transaccion_id,p.monto,p.estado_pago,p.vence,r.id_cliente,r.id_sucursal FROM pago_transaccion p JOIN reserva r ON r.id_reserva=p.id_reserva WHERE p.estado_pago IN ('Pendiente','RequiereResolucion') ORDER BY p.id_pago DESC LIMIT 100")
    return cursor.fetchall()

@router.post('/intentos/{payment_id}/reembolsar')
def refund_payment(payment_id:int,_=Depends(requiere_rol(['Administrador','Encargado de Sucursal'])),cursor=Depends(get_db)):
    from app.services.payments import refund_unconfirmed
    return refund_unconfirmed(cursor,payment_id)

@router.get(
    "/{id_venta}",
    response_model=list[PagoTransaccionRespuesta],
    summary="Historial de transacciones de pago de una venta",
)
def pagos_por_venta(
    id_venta: int,
    cursor=Depends(get_db),
    usuario=Depends(get_current_user),
):
    """Devuelve todas las transacciones de pago registradas para una venta."""
    return svc.obtener_pagos_por_venta(cursor, id_venta)
