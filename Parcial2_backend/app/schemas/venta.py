"""
=============================================================================
FASHIONSTORE - ESQUEMAS PYDANTIC DE VENTAS Y CARRITO (CU15)
Sistemas de Información II - UAGRM
-----------------------------------------------------------------------------
Modelos para el carrito de compras, checkout digital, reservas y ventas
del flujo e-commerce de la Iteración 3.
=============================================================================
"""

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


# ─────────────────────────────────────────────────────────────────────────────
# CARRITO (localStorage / SharedPreferences — no persiste en BD)
# ─────────────────────────────────────────────────────────────────────────────

class CarritoItem(BaseModel):
    """Ítem individual del carrito de compras del cliente."""

    id_variante_prenda: int = Field(..., gt=0)
    sku_variante: str | None = None
    prenda_nombre: str | None = None
    talla: str | None = None
    color: str | None = None
    precio_unitario: Decimal = Field(..., ge=0)
    cantidad: int = Field(..., gt=0)

    @property
    def subtotal(self) -> Decimal:
        return self.precio_unitario * self.cantidad


class ValidarCarritoPeticion(BaseModel):
    """Petición para validar disponibilidad de stock del carrito."""

    items: list[CarritoItem] = Field(..., min_length=1)
    id_sucursal: int = Field(..., gt=0)


class ValidarCarritoRespuesta(BaseModel):
    """Resultado de validación de stock del carrito."""

    valido: bool
    items_sin_stock: list[int] = Field(default_factory=list)
    mensaje: str | None = None


# ─────────────────────────────────────────────────────────────────────────────
# RESERVA (CU15 — primer momento de persistencia en BD)
# ─────────────────────────────────────────────────────────────────────────────

class DetalleReservaPeticion(BaseModel):
    """Ítem a reservar."""

    id_variante_prenda: int = Field(..., gt=0)
    cantidad: int = Field(..., gt=0)
    precio_unitario: Decimal = Field(..., ge=0)


class ReservaPeticion(BaseModel):
    """Payload para crear una reserva desde el checkout."""

    id_cliente: int = Field(..., gt=0)
    id_sucursal: int = Field(..., gt=0)
    items: list[DetalleReservaPeticion] = Field(..., min_length=1)


class DetalleReservaRespuesta(BaseModel):
    """Ítem de reserva retornado por la API."""

    id_variante_prenda: int
    sku_variante: str | None = None
    prenda_nombre: str | None = None
    talla: str | None = None
    color: str | None = None
    cantidad: int
    precio_unitario: Decimal
    subtotal: Decimal

    model_config = ConfigDict(from_attributes=True)


class ReservaRespuesta(BaseModel):
    """Reserva completa retornada al cliente tras el checkout."""

    id_reserva: int
    id_cliente: int
    id_sucursal: int
    sucursal_nombre: str | None = None
    fecha_reserva: datetime
    fecha_limite: datetime
    estado: str
    total: Decimal
    items: list[DetalleReservaRespuesta] = Field(default_factory=list)
    id_venta: int | None = Field(default=None, description="ID de la venta si la reserva ya fue atendida")

    model_config = ConfigDict(from_attributes=True)


# ─────────────────────────────────────────────────────────────────────────────
# RESERVA PARA PROBADOR FÍSICO (CU16, CU17 — Omnicanal)
# ─────────────────────────────────────────────────────────────────────────────

class ReservaProbadorCrear(BaseModel):
    """Payload para reservar prendas para prueba física en sucursal (CU16)."""

    id_cliente: int = Field(..., gt=0)
    id_sucursal: int = Field(..., gt=0)
    items: list[DetalleReservaPeticion] = Field(..., min_length=1)
    horas_vigencia: int = Field(default=2, ge=1, le=24, description="Horas antes de expirar")


EstadoReservaProbador = Literal["Pendiente", "Preparado", "Atendido", "Cancelado"]


class ReservaProbadorEstadoActualizar(BaseModel):
    """Payload para actualizar el estado de atención en sucursal (CU17)."""

    nuevo_estado: EstadoReservaProbador
    motivo: str | None = Field(default=None, max_length=200)


class TicketReservaRespuesta(BaseModel):
    """Ticket digital omnicanal con código QR para atención en probador."""

    id_reserva: int
    codigo_ticket: str
    qr_base64: str
    id_cliente: int
    cliente_nombre: str | None = None
    id_sucursal: int
    sucursal_nombre: str | None = None
    fecha_reserva: datetime
    fecha_limite: datetime
    estado: str
    total: Decimal
    items: list[DetalleReservaRespuesta] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# ─────────────────────────────────────────────────────────────────────────────
# VENTA (CU15 — se crea al confirmar el pago)
# ─────────────────────────────────────────────────────────────────────────────

TipoVenta = Literal["Presencial", "Online"]
MetodoPago = Literal["Efectivo", "Tarjeta", "QR", "Transferencia"]


class VentaConfirmarPeticion(BaseModel):
    """Payload para confirmar una venta tras la confirmación del pago."""

    id_reserva: int = Field(..., gt=0, description="Reserva que origina la venta")
    id_cliente: int | None = Field(default=None, gt=0)
    id_sucursal: int = Field(..., gt=0)
    tipo_venta: TipoVenta = Field(default="Online")
    metodo_pago: MetodoPago = Field(default="QR")
    descuento: Decimal = Field(default=Decimal("0.00"), ge=0)


class DetalleVentaRespuesta(BaseModel):
    """Línea de venta con datos completos de variante."""

    id_variante_prenda: int
    sku_variante: str | None = None
    prenda_nombre: str | None = None
    talla: str | None = None
    color: str | None = None
    cantidad: int
    precio_unitario: Decimal
    subtotal: Decimal

    model_config = ConfigDict(from_attributes=True)


class VentaRespuesta(BaseModel):
    """Cabecera de venta retornada por la API."""

    id_venta: int
    id_cliente: int | None = None
    cliente_nombre: str | None = None
    id_sucursal: int | None = None
    sucursal_nombre: str | None = None
    tipo_venta: str
    metodo_pago: str
    subtotal: Decimal
    descuento: Decimal
    total: Decimal
    fecha_venta: datetime

    model_config = ConfigDict(from_attributes=True)


class VentaDetalladaRespuesta(VentaRespuesta):
    """Venta completa con desglose de ítems."""

    items: list[DetalleVentaRespuesta] = Field(default_factory=list)
