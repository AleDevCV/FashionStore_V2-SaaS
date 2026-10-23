"""
=============================================================================
FASHIONSTORE - ESQUEMAS PYDANTIC DE COMPROBANTES (CU21)
Sistemas de Información II - UAGRM
-----------------------------------------------------------------------------
Modelos para la generación y consulta de comprobantes fiscales digitales
en formato PDF con código QR de verificación.
=============================================================================
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ComprobanteGenerarPeticion(BaseModel):
    """Payload para generar un comprobante digital de venta."""

    id_venta: int = Field(..., gt=0, description="Venta para la que se emite el comprobante")
    nit_ci: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="NIT o CI del comprador para la factura",
    )
    razon_social: str = Field(
        ...,
        min_length=2,
        max_length=150,
        description="Nombre o razón social del comprador",
    )
    enviar_email: bool = Field(
        default=True,
        description="Enviar el comprobante al correo del cliente",
    )


class ComprobanteRespuesta(BaseModel):
    """Comprobante digital generado y almacenado."""

    id_comprobante: int
    id_venta: int
    numero_comprobante: str
    nit_ci: str
    razon_social: str
    fecha_emision: datetime
    url_pdf: str | None = None

    model_config = ConfigDict(from_attributes=True)
