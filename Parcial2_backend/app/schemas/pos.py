"""
=============================================================================
FASHIONSTORE - ESQUEMAS PYDANTIC DE TERMINAL POS (CU19)
Sistemas de Información II - UAGRM
-----------------------------------------------------------------------------
Modelos para la terminal de caja presencial multisucursal:
- Búsqueda rápida de productos por SKU/código de barras o descripción.
- Carga de reservas de probador (CU16, CU17) para cobro en mostrador.
- Cobro presencial multimoneda/multimétodo con cálculo de cambio/vuelto.
- Emisión inmediata de comprobante fiscal digital PDF.
=============================================================================
"""

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


# ─────────────────────────────────────────────────────────────────────────────
# CATÁLOGO RÁPIDO PARA TERMINAL POS
# ─────────────────────────────────────────────────────────────────────────────

class POSProductoVariante(BaseModel):
    """Variante individual con disponibilidad en la sucursal de la caja."""

    id_variante_prenda: int
    sku: str
    id_prenda: int
    prenda_nombre: str
    categoria_nombre: str | None = None
    talla: str
    color: str
    precio_unitario: Decimal
    stock_disponible: int
    imagen_url: str | None = None

    model_config = ConfigDict(from_attributes=True)


# ─────────────────────────────────────────────────────────────────────────────
# CARGA DE RESERVA DE PROBADOR EN POS
# ─────────────────────────────────────────────────────────────────────────────

class POSItemReserva(BaseModel):
    """Ítem incluido en una reserva de probador para cobro."""

    id_variante_prenda: int
    sku: str
    prenda_nombre: str
    talla: str
    color: str
    cantidad: int
    precio_unitario: Decimal
    subtotal: Decimal


class POSReservaCargadaRespuesta(BaseModel):
    """Datos de una reserva de probador lista para facturación en caja."""

    id_reserva: int
    codigo_ticket: str
    id_cliente: int
    cliente_nombre: str
    cliente_ci: str
    id_sucursal: int
    sucursal_nombre: str
    estado: str
    total: Decimal
    items: list[POSItemReserva]

    model_config = ConfigDict(from_attributes=True)


# ─────────────────────────────────────────────────────────────────────────────
# TRANSACCIÓN DE VENTA PRESENCIAL (POS)
# ─────────────────────────────────────────────────────────────────────────────

MetodoPagoPOS = Literal["Efectivo", "Tarjeta", "QR", "Transferencia"]


class POSItemVenta(BaseModel):
    """Línea de venta en el ticket de caja."""

    id_variante_prenda: int = Field(..., gt=0)
    cantidad: int = Field(..., gt=0)
    precio_unitario: Decimal = Field(..., ge=0)


class POSVentaCrear(BaseModel):
    """Payload enviado por la terminal POS al confirmar el cobro."""

    id_sucursal: int = Field(..., gt=0, description="Sucursal donde opera la caja")
    id_cliente: int | None = Field(default=None, description="Cliente registrado o None para mostrador")
    id_reserva: int | None = Field(default=None, description="ID de reserva si proviene de probador")
    metodo_pago: MetodoPagoPOS = Field(default="Efectivo")
    monto_recibido: Decimal | None = Field(
        default=None,
        ge=0,
        description="Monto entregado por el cliente (obligatorio si Efectivo)",
    )
    descuento: Decimal = Field(default=Decimal("0.00"), ge=0)
    nit_ci: str = Field(default="0", max_length=20, description="NIT o CI para factura")
    razon_social: str = Field(
        default="Sin Nombre",
        max_length=150,
        description="Razón social o nombre para factura",
    )
    enviar_email: bool = Field(default=False, description="Enviar comprobante por correo")
    items: list[POSItemVenta] = Field(..., min_length=1, description="Artículos del ticket")

    @model_validator(mode="after")
    def validar_efectivo_y_cambio(self) -> "POSVentaCrear":
        subtotal = sum(it.precio_unitario * it.cantidad for it in self.items)
        total = max(Decimal("0.00"), subtotal - self.descuento)
        if self.metodo_pago == "Efectivo":
            if self.monto_recibido is None:
                self.monto_recibido = total
            elif self.monto_recibido < total:
                raise ValueError(
                    f"El monto recibido (Bs {self.monto_recibido:.2f}) es insuficiente para cubrir el total (Bs {total:.2f})"
                )
        return self


class POSItemVentaRespuesta(BaseModel):
    """Detalle de ítem vendido retornado en la respuesta."""

    id_variante_prenda: int
    sku: str | None = None
    prenda_nombre: str | None = None
    talla: str | None = None
    color: str | None = None
    cantidad: int
    precio_unitario: Decimal
    subtotal: Decimal

    model_config = ConfigDict(from_attributes=True)


class POSVentaRespuesta(BaseModel):
    """Respuesta completa tras consolidar la venta presencial en caja."""

    id_venta: int
    id_sucursal: int
    sucursal_nombre: str
    id_cliente: int
    cliente_nombre: str
    cajero_nombre: str | None = None
    id_reserva: int | None = None
    tipo_venta: str = "Presencial"
    metodo_pago: str
    subtotal: Decimal
    descuento: Decimal
    total: Decimal
    monto_recibido: Decimal | None = None
    cambio_vuelto: Decimal | None = None
    fecha_venta: datetime
    id_comprobante: int | None = None
    numero_comprobante: str | None = None
    url_pdf: str | None = None
    items: list[POSItemVentaRespuesta] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
