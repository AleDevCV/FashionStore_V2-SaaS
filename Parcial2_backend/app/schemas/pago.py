"""
=============================================================================
FASHIONSTORE - ESQUEMAS PYDANTIC DE PAGOS (CU20)
Sistemas de Información II - UAGRM
-----------------------------------------------------------------------------
Modelos para la integración con Stripe y el generador de QR boliviano.
Cubre la creación de sesiones de pago, webhooks y confirmación manual de QR.
=============================================================================
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


# ─────────────────────────────────────────────────────────────────────────────
# STRIPE (CU20)
# ─────────────────────────────────────────────────────────────────────────────

class StripeCheckoutPeticion(BaseModel):
    """Payload para crear una sesión de pago en Stripe Checkout."""

    id_reserva: int = Field(..., gt=0, description="Reserva que se va a pagar")
    id_cliente: int = Field(..., gt=0)
    url_exito: str = Field(
        default="http://localhost:4200/pago/exitoso",
        description="URL de redirección al éxito del pago",
    )
    url_cancelacion: str = Field(
        default="http://localhost:4200/pago/cancelado",
        description="URL de redirección si el cliente cancela",
    )
    nit_ci: str | None = Field(default=None, description="NIT o CI para el comprobante")
    razon_social: str | None = Field(default=None, description="Razón social para el comprobante")
    enviar_email: bool = Field(default=False, description="Si se debe enviar el comprobante por email")


class StripeCheckoutRespuesta(BaseModel):
    """Respuesta con la URL de Stripe Checkout para redirigir al cliente."""

    url_pago: str
    session_id: str
    id_reserva: int
    monto: Decimal


# ─────────────────────────────────────────────────────────────────────────────
# QR BOLIVIANO (CU20)
# ─────────────────────────────────────────────────────────────────────────────

class QRGenerarPeticion(BaseModel):
    """Payload para generar un código QR de pago boliviano."""

    id_reserva: int = Field(..., gt=0)
    id_cliente: int = Field(..., gt=0)
    monto: Decimal = Field(..., gt=0)
    concepto: str = Field(
        default="Pago FashionStore",
        max_length=100,
        description="Descripción del pago para el QR",
    )


class QRGenerarRespuesta(BaseModel):
    """Respuesta con la imagen QR codificada en base64."""

    qr_base64: str = Field(..., description="Imagen QR en formato base64 PNG")
    referencia: str = Field(..., description="Código único de referencia del pago")
    monto: Decimal
    id_reserva: int
    expira_en_minutos: int = Field(default=15)


class QRConfirmarPeticion(BaseModel):
    """Payload para confirmar manualmente un pago QR boliviano."""

    referencia: str = Field(..., description="Código de referencia del QR generado")
    id_reserva: int = Field(..., gt=0)
    id_cliente: int = Field(..., gt=0)
    id_sucursal: int = Field(..., gt=0)


# ─────────────────────────────────────────────────────────────────────────────
# PAGO TRANSACCIÓN (historial)
# ─────────────────────────────────────────────────────────────────────────────

class PagoTransaccionRespuesta(BaseModel):
    """Registro de transacción de pago almacenado en la BD."""

    id_pago: int
    id_venta: int | None = None
    pasarela: str
    transaccion_id: str
    monto: Decimal
    estado_pago: str
    fecha: datetime

    model_config = ConfigDict(from_attributes=True)
