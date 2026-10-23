"""
=============================================================================
FASHIONSTORE - ESQUEMAS DE CATEGORÍAS DE PRENDAS (CU07)
Sistemas de Información II - UAGRM
-----------------------------------------------------------------------------
Contrato de datos de la clasificación jerárquica del catálogo.

La tabla `categoria` es RECURSIVA: `id_categoria_padre` apunta a la propia
tabla, lo que permite árboles como Damas -> Blusas.
=============================================================================
"""

from typing import Literal

from pydantic import BaseModel, Field

EstadoCategoria = Literal["Activo", "Inactivo"]


class CategoriaCrear(BaseModel):
    """Datos para registrar una categoría del catálogo.

    Campos:
        nombre: nombre de la categoría. UNIQUE en toda la tabla.
        descripcion: texto descriptivo, opcional.
        id_categoria_padre: categoría contenedora. Si es null, la categoría
                            queda como raíz del árbol (ej: "Damas").
    """

    nombre: str = Field(..., min_length=2, max_length=100, examples=["Chaquetas"])
    descripcion: str | None = Field(default=None, max_length=255)
    id_categoria_padre: int | None = Field(default=None, ge=1)


class CategoriaActualizar(BaseModel):
    """Datos para modificar una categoría (actualización parcial)."""

    nombre: str | None = Field(default=None, min_length=2, max_length=100)
    descripcion: str | None = Field(default=None, max_length=255)
    id_categoria_padre: int | None = Field(default=None, ge=1)
    estado: EstadoCategoria | None = Field(default=None)


class CategoriaRespuesta(BaseModel):
    """Categoría con el nombre de su padre ya resuelto por JOIN.

    `categoria_padre` no es una columna: se obtiene con un LEFT JOIN de la
    tabla consigo misma, para que el frontend pueda dibujar el árbol sin
    peticiones adicionales.
    """

    id_categoria: int
    nombre: str
    descripcion: str | None = None
    id_categoria_padre: int | None = None
    categoria_padre: str | None = None
    estado: str
    total_prendas: int = 0
