"""
=============================================================================
FASHIONSTORE - ESQUEMAS PYDANTIC DE PROVEEDORES (CU12)
Sistemas de Información II - UAGRM
-----------------------------------------------------------------------------
Modelos de validación para la gestión de proveedores (cadena de suministro).
Valida unicidad y formato de NIT, razón social, teléfonos y correos de
contacto comercial.
=============================================================================
"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ProveedorBase(BaseModel):
    """Atributos comunes para la entidad Proveedor."""

    nit: str = Field(
        ...,
        min_length=3,
        max_length=30,
        description="Número de Identificación Tributaria del proveedor",
    )
    razon_social: str = Field(
        ...,
        min_length=2,
        max_length=150,
        description="Razón social o denominación comercial de la empresa",
    )
    contacto: str | None = Field(
        default=None,
        max_length=100,
        description="Nombre y apellido de la persona de contacto",
    )
    telefono: str | None = Field(
        default=None,
        max_length=20,
        description="Teléfono fijo o celular del proveedor",
    )
    correo: EmailStr | str | None = Field(
        default=None,
        max_length=150,
        description="Correo electrónico corporativo o de contacto",
    )
    direccion: str | None = Field(
        default=None,
        max_length=255,
        description="Dirección física del establecimiento o depósito",
    )


class ProveedorCrear(ProveedorBase):
    """Esquema para la creación de un nuevo proveedor."""

    pass


class ProveedorActualizar(BaseModel):
    """Esquema para la actualización parcial o total de un proveedor existente."""

    nit: str | None = Field(
        default=None,
        min_length=3,
        max_length=30,
        description="Nuevo NIT si corresponde actualizar",
    )
    razon_social: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
        description="Nueva razón social",
    )
    contacto: str | None = Field(
        default=None,
        max_length=100,
        description="Nueva persona de contacto",
    )
    telefono: str | None = Field(
        default=None,
        max_length=20,
        description="Nuevo teléfono de contacto",
    )
    correo: EmailStr | str | None = Field(
        default=None,
        max_length=150,
        description="Nuevo correo electrónico",
    )
    direccion: str | None = Field(
        default=None,
        max_length=255,
        description="Nueva dirección física",
    )


class ProveedorRespuesta(ProveedorBase):
    """Esquema devuelto por los endpoints con los datos completos del proveedor."""

    id_proveedor: int
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
