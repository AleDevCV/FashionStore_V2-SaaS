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
from pydantic import BaseModel, ConfigDict, Field


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
