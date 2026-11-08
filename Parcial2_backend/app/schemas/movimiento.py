"""
=============================================================================
FASHIONSTORE - ESQUEMAS PYDANTIC DE MOVIMIENTOS DE INVENTARIO (CU11)
Sistemas de Información II - UAGRM
-----------------------------------------------------------------------------
Modelos para registrar y consultar movimientos físicos en almacén y sucursales:
Entrada, Salida y Traspaso.
=============================================================================
"""

from datetime import datetime
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class MovimientoCrear(BaseModel):
    """Datos para registrar un nuevo movimiento de inventario."""

    id_sucursal: int = Field(
        ...,
        gt=0,
        description="Identificador de la sucursal física afectada",
    )
    id_variante_prenda: int = Field(
        ...,
        gt=0,
        description="Identificador de la variante de prenda afectada",
    )
    tipo: str = Field(
        ...,
        pattern="^(Entrada|Salida|Traspaso)$",
        description="Tipo de operación física: 'Entrada', 'Salida' o 'Traspaso'",
    )
    cantidad: int = Field(
        ...,
        gt=0,
        description="Cantidad física de unidades (debe ser estrictamente positiva)",
    )
    motivo: str = Field(
        ...,
        min_length=3,
        max_length=255,
        description="Motivo o justificación del movimiento en kardex",
    )
    id_sucursal_destino: int | None = Field(default=None, gt=0, description='Destino obligatorio y distinto para Traspaso.')
    operation_id: UUID | None = Field(default=None, description='UUID obligatorio para Traspaso; reutilizarlo en reintentos idénticos.')

    @field_validator('cantidad', mode='before')
    @classmethod
    def cantidad_entera_traspaso(cls, value, info):
        if info.data.get('tipo') == 'Traspaso' and (isinstance(value, bool) or not isinstance(value, int)):
            raise ValueError('La cantidad de traspaso debe ser un entero positivo.')
        return value

    @model_validator(mode='after')
    def validar_traspaso(self):
        if self.tipo == 'Traspaso':
            if self.id_sucursal_destino is None or self.operation_id is None:
                raise ValueError('Traspaso requiere sucursal de destino y UUID operation_id.')
            if self.id_sucursal_destino == self.id_sucursal:
                raise ValueError('Origen y destino deben ser sucursales distintas.')
            if self.cantidad > 2147483647:
                raise ValueError('La cantidad excede el rango de inventario.')
            self.motivo = self.motivo.strip()
            if len(self.motivo) < 3:
                raise ValueError('Indique un motivo válido para el traspaso.')
        return self


MovimientoInventarioCrear = MovimientoCrear


class MovimientoRespuesta(BaseModel):
    """Representación detallada de un movimiento de inventario con relaciones resueltas."""

    id_movimiento: int
    id_sucursal: int
    sucursal_nombre: str | None = None
    id_variante_prenda: int
    sku_variante: str | None = None
    prenda_nombre: str | None = None
    talla: str | None = None
    color: str | None = None
    tipo: str
    cantidad: int
    motivo: str
    id_usuario: int | None = None
    usuario_nombre: str | None = None
    fecha: datetime
    stock_actual: int | None = None

    model_config = ConfigDict(from_attributes=True)


MovimientoInventarioRespuesta = MovimientoRespuesta


class MovimientoVinculadoRespuesta(MovimientoRespuesta):
    """Pata física de un traspaso visible en ambas sucursales autorizadas."""
    operation_id: UUID
    id_sucursal_origen: int
    id_sucursal_destino: int
    id_movimiento_salida: int
    id_movimiento_entrada: int


class TraspasoRespuesta(BaseModel):
    """Operación lógica online; las patas conservan sus tipos Salida/Entrada."""
    tipo: Literal['Traspaso'] = 'Traspaso'
    operation_id: UUID
    id_sucursal_origen: int
    id_sucursal_destino: int
    id_variante_prenda: int
    cantidad: int
    motivo: str
    id_usuario: int
    fecha: datetime
    movimiento_salida: MovimientoRespuesta
    movimiento_entrada: MovimientoRespuesta


class MovimientoFiltro(BaseModel):
    """Parámetros de filtrado para el historial de movimientos."""

    id_sucursal: int | None = None
    id_variante_prenda: int | None = None
    tipo: str | None = None
    fecha_inicio: datetime | None = None
    fecha_fin: datetime | None = None
    skip: int = 0
    limit: int = 50


class StockRespuesta(BaseModel):
    """Consulta rápida de stock físico actual para una variante en sucursal."""

    id_sucursal: int
    id_variante_prenda: int
    stock: int

    model_config = ConfigDict(from_attributes=True)
