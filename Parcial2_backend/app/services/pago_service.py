from app.tenant import require_context
"""
=============================================================================
FASHIONSTORE - SERVICIO DE PAGOS (CU20)
Sistemas de Información II - UAGRM
-----------------------------------------------------------------------------
Lógica de integración con pasarelas de pago:
1. Stripe Checkout Session: crea sesión de pago y gestiona webhook de confirmación.
2. QR Dinámico Bolivia: genera imagen QR con datos del pago (sin banco real).
3. Registro en pago_transaccion con payload completo.
4. Auditoría en bitácora (CU25).
=============================================================================
"""

import base64
import io
import logging
import os
import secrets
import string
from decimal import Decimal
from typing import Any

logger = logging.getLogger(__name__)

import qrcode
import stripe
from fastapi import HTTPException, Request, status

from app.schemas.comprobante import ComprobanteGenerarPeticion
from app.schemas.pago import (
    PagoTransaccionRespuesta,
    QRConfirmarPeticion,
    QRGenerarPeticion,
    QRGenerarRespuesta,
    StripeCheckoutPeticion,
)
from app.schemas.venta import VentaConfirmarPeticion
from app.services.bitacora_service import ACCION_INSERT, ACCION_UPDATE, registrar_bitacora
from app.services.comprobante_service import generar_comprobante
from app.services.venta_service import confirmar_venta


# Configurar Stripe con la clave del entorno (modo test si empieza con sk_test_)
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:4200")


# ─────────────────────────────────────────────────────────────────────────────
# STRIPE (CU20)
# ─────────────────────────────────────────────────────────────────────────────

def crear_sesion_stripe(
    cursor: Any,
    datos: StripeCheckoutPeticion,
    id_usuario: int | None,
    ip_address: str,
) -> dict:
    from app.services.payments import checkout
    return checkout(cursor,datos,id_usuario,ip_address)


def procesar_webhook_stripe(
    cursor: Any,
    payload: bytes,
    sig_header: str,
    ip_address: str,
) -> dict:
    from app.services.payments import webhook
    return webhook(cursor,payload,sig_header,ip_address)


# ─────────────────────────────────────────────────────────────────────────────
# QR BOLIVIANO (CU20)
# ─────────────────────────────────────────────────────────────────────────────

def _generar_referencia() -> str:
    """Genera un código alfanumérico único de 12 caracteres para el pago QR."""
    alfabeto = string.ascii_uppercase + string.digits
    return "FS-" + "".join(secrets.choice(alfabeto) for _ in range(9))


def generar_qr_boliviano(
    cursor: Any,
    datos: QRGenerarPeticion,
    id_usuario: int | None,
    ip_address: str,
) -> dict:
    from app.services.payments import qr
    return qr(cursor,datos,id_usuario,ip_address)


def confirmar_pago_qr(
    cursor: Any,
    datos: QRConfirmarPeticion,
    id_usuario: int | None,
    ip_address: str,
) -> dict:
    from app.services.payments import confirm_qr
    return confirm_qr(cursor,datos,id_usuario,ip_address)


def obtener_pagos_por_venta(cursor: Any, id_venta: int) -> list[dict]:
    """Lista todas las transacciones de pago asociadas a una venta."""
    cursor.execute(
        """
        SELECT id_pago, id_venta, pasarela, transaccion_id, monto, estado_pago, fecha
        FROM pago_transaccion
        WHERE id_venta = %s
        ORDER BY fecha DESC;
        """,
        (id_venta,),
    )
    return cursor.fetchall()
