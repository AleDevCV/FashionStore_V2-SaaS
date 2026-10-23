"""
=============================================================================
FASHIONSTORE - ESQUEMAS DE FICHAS DE CLIENTES (CU05)
Sistemas de Información II - UAGRM
-----------------------------------------------------------------------------
Contrato de datos del módulo de clientes.

NOTA SOBRE EL NOMBRE: la tabla `cliente` guarda un único campo
`nombre_completo VARCHAR(200)`, no un par nombre/apellido. Los esquemas
respetan esa estructura para no desalinear la API de la base de datos.
=============================================================================
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

# Estados admitidos por la restricción CHECK de `cliente.estado`.
EstadoCliente = Literal["Activo", "Inactivo"]


class ClienteCrear(BaseModel):
    """Datos para registrar la ficha de un cliente.

    Campos:
        ci: cédula de identidad o NIT. UNIQUE en la tabla; es la clave natural
            con la que el cajero identifica al comprador en el mostrador.
        nombre_completo: nombre y apellidos del cliente.
        telefono: celular de contacto, opcional.
        correo: correo electrónico, opcional pero UNIQUE si se envía.
        direccion_envio: dirección predeterminada para entregas de e-commerce.
    """

    ci: str = Field(..., min_length=4, max_length=20, examples=["9876543"])
    nombre_completo: str = Field(
        ..., min_length=3, max_length=200, examples=["María René Ortiz"]
    )
    telefono: str | None = Field(
        default=None,
        max_length=20,
        pattern=r"^[0-9+() -]*$",
        examples=["78911223"],
    )
    correo: EmailStr | None = Field(default=None, examples=["maria@gmail.com"])
    direccion_envio: str | None = Field(default=None, max_length=255)


class ClienteActualizar(BaseModel):
    """Datos para modificar una ficha de cliente.

    Todos los campos son opcionales (actualización parcial). Se incluye
    `estado` para poder reactivar una ficha dada de baja lógicamente.
    """

    ci: str | None = Field(default=None, min_length=4, max_length=20)
    nombre_completo: str | None = Field(default=None, min_length=3, max_length=200)
    telefono: str | None = Field(default=None, max_length=20, pattern=r"^[0-9+() -]*$")
    correo: EmailStr | None = Field(default=None)
    direccion_envio: str | None = Field(default=None, max_length=255)
    estado: EstadoCliente | None = Field(default=None)


class ClienteAutogestionActualizar(BaseModel):
    """Campos que un cliente puede actualizar en su propia ficha.

    El estado se excluye deliberadamente: la autogestión no concede la
    capacidad administrativa de inactivar o reactivar fichas.
    """

    model_config = ConfigDict(extra="forbid")

    ci: str | None = Field(default=None, min_length=4, max_length=20)
    nombre_completo: str | None = Field(default=None, min_length=3, max_length=200)
    telefono: str | None = Field(
        default=None,
        max_length=20,
        pattern=r"^[0-9+() -]*$",
    )
    correo: EmailStr | None = Field(default=None)
    direccion_envio: str | None = Field(default=None, max_length=255)


class ClienteRespuesta(BaseModel):
    """Ficha de cliente tal como la devuelve la API."""

    id_cliente: int
    ci: str
    nombre_completo: str
    telefono: str | None = None
    correo: str | None = None
    direccion_envio: str | None = None
    estado: str
    created_at: datetime | None = None


# =============================================================================
# AUTO-REGISTRO DE CLIENTES (CU05 / CU01)
# =============================================================================

class RegistroClientePeticion(BaseModel):
    """Datos enviados por un cliente para auto-registrarse en la plataforma."""

    nombre: str = Field(..., min_length=2, max_length=100, examples=["Claudia"])
    apellido: str = Field(..., min_length=2, max_length=100, examples=["Torrez"])
    ci: str = Field(..., min_length=4, max_length=20, examples=["8472911"])
    correo: EmailStr = Field(..., examples=["claudia.torrez@gmail.com"])
    password: str = Field(..., min_length=4, max_length=72, examples=["claveSegura123"])
    telefono: str | None = Field(
        default=None,
        max_length=20,
        pattern=r"^[0-9+() -]*$",
        examples=["77334455"],
    )
    direccion_envio: str | None = Field(default=None, max_length=255, examples=["Av. San Martín #123"])


class RegistroClienteRespuesta(BaseModel):
    """Respuesta tras completar exitosamente el registro del cliente."""

    mensaje: str
    id_cliente: int
    id_usuario: int
    nombre_completo: str
    correo: str
    rol: str = "Cliente"
    access_token: str
    token_type: str = "bearer"

