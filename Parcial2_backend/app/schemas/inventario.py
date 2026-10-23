"""
=============================================================================
FASHIONSTORE - ESQUEMAS DE MONITOREO Y ANALÍTICA DE INVENTARIO (CU10)
Sistemas de Información II - UAGRM
-----------------------------------------------------------------------------
Modelos Pydantic v2 para consultas de agregación multisucursal, resumen de KPIs
y matriz detallada de monitoreo con clasificación cromática de stock.
=============================================================================
"""

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

EstadoStock = Literal["Optimo", "Bajo", "Agotado"]
ColorBadge = Literal["verde", "amarillo", "rojo"]


class ResumenSucursal(BaseModel):
    """Métricas consolidadas de inventario para una sucursal física individual."""

    model_config = ConfigDict(from_attributes=True)

    id_sucursal: int
    sucursal: str = Field(..., description="Nombre comercial de la sucursal")
    nombre_sucursal: str | None = None
    ciudad: str
    total_stock: int
    total_variantes: int = 0
    total_optimo: int = 0
    total_bajo: int = 0
    total_agotado: int = 0
    variantes_optimo: int = 0
    variantes_bajo: int = 0
    variantes_agotadas: int = 0

    @model_validator(mode="after")
    def sincronizar_alias(self):
        """Sincroniza nombres de campos para compatibilidad con Web y Mobile."""
        if not self.nombre_sucursal:
            self.nombre_sucursal = self.sucursal
        if not self.variantes_optimo:
            self.variantes_optimo = self.total_optimo
        if not self.variantes_bajo:
            self.variantes_bajo = self.total_bajo
        if not self.variantes_agotadas:
            self.variantes_agotadas = self.total_agotado
        return self


class ResumenInventarioRespuesta(BaseModel):
    """Métricas globales agregadas de inventario y desglose por sucursal."""

    model_config = ConfigDict(from_attributes=True)

    total_stock: int = Field(..., description="Suma global de unidades físicas en stock")
    total_stock_global: int | None = None
    total_prendas: int = Field(..., description="Cantidad de diseños maestros distintos")
    total_prendas_distintas: int | None = None
    total_variantes: int = Field(..., description="Cantidad de combinaciones talla/color")
    total_optimo: int = Field(..., description="Conteo de registros con stock >= 5")
    total_bajo: int = Field(..., description="Conteo de registros con stock entre 1 y 4")
    total_agotado: int = Field(..., description="Conteo de registros con stock 0")
    variantes_optimo: int | None = None
    variantes_bajo_stock: int | None = None
    variantes_agotadas: int | None = None
    por_sucursal: list[ResumenSucursal] = Field(default_factory=list)
    sucursales: list[ResumenSucursal] = Field(default_factory=list)

    @model_validator(mode="after")
    def sincronizar_alias(self):
        """Puebla alias de compatibilidad para contratos Web y Mobile."""
        if self.total_stock_global is None:
            self.total_stock_global = self.total_stock
        if self.total_prendas_distintas is None:
            self.total_prendas_distintas = self.total_prendas
        if self.variantes_optimo is None:
            self.variantes_optimo = self.total_optimo
        if self.variantes_bajo_stock is None:
            self.variantes_bajo_stock = self.total_bajo
        if self.variantes_agotadas is None:
            self.variantes_agotadas = self.total_agotado
        if not self.sucursales and self.por_sucursal:
            self.sucursales = self.por_sucursal
        elif not self.por_sucursal and self.sucursales:
            self.por_sucursal = self.sucursales
        return self


class MonitoreoItemRespuesta(BaseModel):
    """Fila detallada de la grilla de monitoreo multisucursal con badge cromático."""

    model_config = ConfigDict(from_attributes=True)

    id_inventario: int | None = None
    id_sucursal: int
    sucursal: str
    nombre_sucursal: str | None = None
    ciudad: str
    id_prenda: int
    prenda_sku: str
    sku_prenda: str | None = None
    prenda_nombre: str
    nombre_prenda: str | None = None
    id_categoria: int | None = None
    categoria: str | None = None
    nombre_categoria: str | None = None
    id_temporada: int | None = None
    temporada: str | None = None
    nombre_temporada: str | None = None
    id_variante_prenda: int
    sku_variante: str
    sku: str | None = None
    talla: str | None = None
    color: str | None = None
    codigo_hex: str | None = None
    precio_base: Decimal
    precio_adicional: Decimal = Decimal("0.00")
    precio: Decimal | None = None
    stock: int
    estado_stock: EstadoStock
    color_badge: ColorBadge

    @model_validator(mode="after")
    def sincronizar_alias(self):
        """Sincroniza propiedades y calcula precio consolidado si no está establecido."""
        if not self.nombre_sucursal:
            self.nombre_sucursal = self.sucursal
        if not self.sku_prenda:
            self.sku_prenda = self.prenda_sku
        if not self.nombre_prenda:
            self.nombre_prenda = self.prenda_nombre
        if not self.nombre_categoria:
            self.nombre_categoria = self.categoria
        if not self.nombre_temporada:
            self.nombre_temporada = self.temporada
        if not self.sku:
            self.sku = self.sku_variante
        if self.precio is None:
            self.precio = self.precio_base + self.precio_adicional
        return self
