"""
=============================================================================
FASHIONSTORE - ESQUEMAS PYDANTIC DE COMPRAS (CU13)
Sistemas de Información II - UAGRM
-----------------------------------------------------------------------------
Modelos para la adquisición transaccional de productos a proveedores,
con cálculo de 13% IVA y desglose de variantes físicas ingresadas.
=============================================================================
"""

from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, model_validator


class DetalleCompraItem(BaseModel):
    """Ítem individual dentro del comprobante de compra."""

    id_variante_prenda: int = Field(
        ...,
        gt=0,
        description="Identificador de la variante física de prenda a ingresar",
    )
    cantidad: int = Field(
        ...,
        gt=0,
        description="Cantidad de unidades compradas (debe ser mayor a cero)",
    )
    costo_unitario: Decimal = Field(
        ...,
        ge=0,
        description="Costo unitario neto pactado con el proveedor",
    )


DetalleCompraCrear = DetalleCompraItem


class CompraCrear(BaseModel):
    """Payload para registrar una nueva compra de mercadería."""

    id_proveedor: int = Field(
        ...,
        gt=0,
        description="Proveedor emisor de la factura / remisión",
    )
    id_sucursal: int = Field(
        ...,
        gt=0,
        description="Sucursal física receptora del lote",
    )
    items: list[DetalleCompraItem] | None = Field(
        default=None,
        description="Lista de variantes y cantidades adquiridas",
    )
    detalles: list[DetalleCompraItem] | None = Field(
        default=None,
        description="Alias de items para compatibilidad con distintos clientes",
    )

    @model_validator(mode="after")
    def validar_detalles(self):
        """Asegura que exista al menos un detalle y sincroniza items y detalles."""
        lista = self.items or self.detalles
        if not lista or len(lista) == 0:
            raise ValueError("La compra debe tener al menos un detalle de producto")
        if self.items is None:
            self.items = lista
        if self.detalles is None:
            self.detalles = lista
        return self


class DetalleCompraRespuesta(BaseModel):
    """Información completa de cada ítem de una compra con datos de prenda."""

    id_variante_prenda: int
    sku_variante: str | None = None
    prenda_nombre: str | None = None
    talla: str | None = None
    color: str | None = None
    cantidad: int
    costo_unitario: Decimal
    subtotal_item: Decimal

    model_config = ConfigDict(from_attributes=True)


class CompraRespuesta(BaseModel):
    """Cabecera de compra con totales calculados y datos de auditoría."""

    id_compra: int
    id_proveedor: int
    proveedor_razon_social: str | None = None
    id_sucursal: int
    sucursal_nombre: str | None = None
    fecha: datetime
    subtotal: Decimal | None = None
    iva: Decimal | None = None
    total: Decimal
    id_usuario: int | None = None
    usuario_nombre: str | None = None
    total_items: int | None = None

    model_config = ConfigDict(from_attributes=True)


class CompraDetalladaRespuesta(CompraRespuesta):
    """Compra completa incluyendo cabecera y el desglose de todos los ítems."""

    items: list[DetalleCompraRespuesta] = Field(default_factory=list)
    detalles: list[DetalleCompraRespuesta] = Field(default_factory=list)

    @model_validator(mode="after")
    def sincronizar_listas(self):
        """Sincroniza items y detalles para responder adecuadamente a ambos formatos."""
        if not self.items and self.detalles:
            self.items = self.detalles
        elif not self.detalles and self.items:
            self.detalles = self.items
        return self


CompraDetalleRespuesta = CompraDetalladaRespuesta
