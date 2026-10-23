"""
=============================================================================
FASHIONSTORE - ESQUEMAS DE PRENDAS Y VARIANTES (CU08)
Sistemas de Información II - UAGRM
-----------------------------------------------------------------------------
Contrato de datos del catálogo maestro.

MODELO DE DATOS (tres tablas):
  prenda          -> el diseño maestro (SKU, nombre, precio, categoría...)
  variante_prenda -> la combinación física Prenda + Talla + Color
  imagen_prenda   -> las fotografías asociadas al diseño

La foto se guarda en `imagen_prenda` y no como columna de `prenda`, porque el
esquema admite varias imágenes por diseño.
=============================================================================
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

# Valores admitidos por las restricciones CHECK de la tabla `prenda`.
GeneroPrenda = Literal["Dama", "Caballero", "Unisex", "Nino"]
EstadoPrenda = Literal["Activo", "Inactivo", "Borrador"]


class VarianteCrear(BaseModel):
    """Combinación física de talla y color que se dará de alta para la prenda.

    Campos:
        id_talla: FK a la tabla `talla`.
        id_color: FK a la tabla `color`.
        stock_inicial: unidades con las que arranca la variante EN CADA
                       SUCURSAL. El backend crea una fila de `inventario` por
                       sucursal existente con este valor; no lo reparte entre
                       ellas. Con 2 sucursales y stock_inicial = 10, el stock
                       consolidado de la variante será 20.
        precio_adicional: recargo sobre el precio base (ej: una talla XL).
    """

    id_talla: int = Field(..., ge=1)
    id_color: int = Field(..., ge=1)
    color_ids: list[int] = Field(default_factory=list,max_length=10)
    stock_inicial: int = Field(default=0, ge=0)
    precio_adicional: Decimal = Field(default=Decimal("0.00"), ge=0)


class VarianteRespuesta(BaseModel):
    """Variante con los nombres de talla y color ya resueltos por JOIN."""

    id_variante_prenda: int
    id_talla: int
    talla: str | None = None
    id_color: int
    color_ids: list[int] = Field(default_factory=list)
    color: str | None = None
    codigo_hex: str | None = None
    sku_variante: str
    precio_adicional: Decimal = Decimal("0.00")
    stock_total: int = 0


class ComercialFields(BaseModel):
    admite_cambio: bool = True
    material: str | None = Field(default=None, max_length=300)
    medidas: str | None = Field(default=None, max_length=500)
    precio_mayorista: Decimal | None = Field(default=None, ge=0)
    umbral_mayorista: int | None = Field(default=None, gt=0)
    precio_oferta: Decimal | None = Field(default=None, ge=0)
    oferta_inicio: date | None = None
    oferta_fin: date | None = None


class PrendaCrear(ComercialFields):
    """Datos maestros para dar de alta una prenda en el catálogo.

    Campos:
        sku: código único del diseño. UNIQUE en la tabla `prenda`.
        nombre: nombre comercial.
        descripcion: ficha técnica de tela y costura.
        marca: marca asociada; por defecto la propia FashionStore.
        genero: público objetivo, usado como filtro del catálogo (CU14).
        precio_base: precio del diseño sin recargos de variante.
        id_categoria: FK a la tabla `categoria`.
        url_imagen: fotografía principal; se guarda en `imagen_prenda` con
                    es_principal = TRUE.
        variantes: matriz de combinaciones talla/color a crear en la misma
                   transacción que la prenda.
    """

    sku: str = Field(..., min_length=2, max_length=50, examples=["CHQ-JEAN-001"])
    nombre: str = Field(..., min_length=2, max_length=150, examples=["Chaqueta de Jean"])
    descripcion: str | None = Field(default=None)
    marca: str | None = Field(default="FashionStore", max_length=100)
    genero: GeneroPrenda = Field(default="Unisex")
    precio_base: Decimal = Field(..., ge=0, examples=[Decimal("349.90")])
    id_categoria: int = Field(..., ge=1)
    id_temporada: int | None = Field(
        default=None,
        ge=1,
        description="Identificador de la temporada comercial asignada",
    )
    url_imagen: str | None = Field(default=None, max_length=255)
    variantes: list[VarianteCrear] = Field(default_factory=list)


class PrendaActualizar(ComercialFields):
    """Datos para modificar una prenda (actualización parcial).

    Las variantes NO se tocan por esta vía: alterarlas afectaría al inventario
    ya existente. Se gestionan con su propio endpoint de variantes.
    """

    sku: str | None = Field(default=None, min_length=2, max_length=50)
    nombre: str | None = Field(default=None, min_length=2, max_length=150)
    descripcion: str | None = Field(default=None)
    marca: str | None = Field(default=None, max_length=100)
    genero: GeneroPrenda | None = Field(default=None)
    precio_base: Decimal | None = Field(default=None, ge=0)
    id_categoria: int | None = Field(default=None, ge=1)
    id_temporada: int | None = Field(
        default=None,
        ge=1,
        description="Identificador de la temporada comercial asignada (None para desasociar)",
    )
    url_imagen: str | None = Field(default=None, max_length=255)
    estado: EstadoPrenda | None = Field(default=None)


class ImagenPrendaRespuesta(BaseModel):
    """URL persistente obtenida despues de subir una imagen."""

    url_imagen: str


class PrendaRespuesta(ComercialFields):
    """Prenda con su categoría, temporada, su imagen principal y sus variantes."""

    id_prenda: int
    sku: str
    nombre: str
    descripcion: str | None = None
    marca: str | None = None
    genero: str | None = None
    precio_base: Decimal
    id_categoria: int | None = None
    categoria: str | None = None
    id_temporada: int | None = None
    nombre_temporada: str | None = None
    temporada: str | None = None
    estado: str
    url_imagen: str | None = None
    stock_total: int = 0
    variantes: list[VarianteRespuesta] = Field(default_factory=list)
    created_at: datetime | None = None
