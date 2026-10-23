"""
=============================================================================
FASHIONSTORE - ESQUEMAS DEL CATÁLOGO PÚBLICO (CU14)
Sistemas de Información II - UAGRM
-----------------------------------------------------------------------------
Contrato de datos de la consulta de catálogo y disponibilidad por sucursal.

A diferencia del CU08 (administrativo), estos esquemas son de SOLO LECTURA y
se sirven sin token: son los que consumen el portal web y la app móvil.
=============================================================================
"""

from decimal import Decimal

from pydantic import BaseModel, Field


class StockSucursal(BaseModel):
    """Existencias de una variante concreta en una sucursal física.

    Es la respuesta al paso 9 del flujo del CU14: el cliente elige talla y
    color y quiere saber en qué tienda puede probárselo.
    """

    id_sucursal: int
    sucursal: str
    ciudad: str | None = None
    direccion: str | None = None
    stock: int


class VarianteCatalogo(BaseModel):
    """Variante talla/color con su disponibilidad desglosada por sucursal."""

    id_variante_prenda: int
    id_talla: int
    talla: str | None = None
    id_color: int
    color: str | None = None
    codigo_hex: str | None = None
    precio: Decimal
    stock_total: int = 0
    disponibilidad: list[StockSucursal] = Field(default_factory=list)


from app.schemas.prenda import ComercialFields

class PrendaCatalogo(ComercialFields):
    """Ficha de una prenda tal como se muestra en la cuadrícula del catálogo."""

    id_prenda: int
    sku: str
    nombre: str
    descripcion: str | None = None
    marca: str | None = None
    genero: str | None = None
    precio_base: Decimal
    id_categoria: int | None = None
    categoria: str | None = None
    url_imagen: str | None = None
    stock_total: int = 0
    variantes: list[VarianteCatalogo] = Field(default_factory=list)


class RespuestaCatalogo(BaseModel):
    """Página de resultados del catálogo.

    Campos:
        total: cantidad de prendas que cumplen los filtros, sin paginar. Es lo
               que permite al frontend dibujar el paginador.
        limite / desplazamiento: parámetros de paginación aplicados.
        prendas: la página actual de resultados.
    """

    total: int
    limite: int
    desplazamiento: int
    prendas: list[PrendaCatalogo] = Field(default_factory=list)


class FiltrosDisponibles(BaseModel):
    """Opciones para construir la barra de filtros del catálogo.

    Se entregan en una sola llamada para que el frontend no tenga que pedir
    categorías, tallas y colores por separado.
    """

    categorias: list[dict] = Field(default_factory=list)
    tallas: list[dict] = Field(default_factory=list)
    colores: list[dict] = Field(default_factory=list)
    generos: list[str] = Field(default_factory=list)
    precio_minimo: Decimal = Decimal("0.00")
    precio_maximo: Decimal = Decimal("0.00")
