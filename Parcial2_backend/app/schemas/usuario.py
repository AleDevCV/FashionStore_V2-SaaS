"""
=============================================================================
FASHIONSTORE - ESQUEMAS DE VALIDACIÓN DE USUARIOS (CU02)
Sistemas de Información II - UAGRM
-----------------------------------------------------------------------------
Modelos de Pydantic del módulo "Administrar Usuarios y Asignar Roles".

Se definen modelos separados para crear, actualizar y responder porque los
campos no coinciden entre operaciones: la contraseña solo entra (nunca sale),
el rol se recibe como id numérico pero se devuelve también como texto, y en la
actualización todos los campos son opcionales.
=============================================================================
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field

# Estados admitidos por la restricción CHECK de la columna `usuario.estado`.
# Declararlos como Literal hace que Pydantic rechace cualquier otro valor con un
# error 422 antes de que PostgreSQL tenga que abortar la transacción.
EstadoUsuario = Literal["Activo", "Inactivo"]


class UsuarioCrear(BaseModel):
    """Datos para dar de alta un usuario (POST /api/usuarios/).

    Campos:
        nombre: nombre de pila del usuario.
        apellido: apellido del usuario.
        correo: correo electrónico; debe ser único en toda la tabla `usuario`.
        password: contraseña temporal en texto plano. Solo viaja de entrada:
                  el backend la convierte de inmediato a un hash bcrypt y jamás
                  la devuelve en ninguna respuesta (RNF01).
        telefono: teléfono de contacto, opcional.
        id_role: clave foránea hacia `rol.id_rol` que define sus privilegios.
        estado: estado inicial de la cuenta; por defecto queda 'Activo'.
    """

    nombre: str = Field(..., min_length=1, max_length=100, examples=["Camila"])
    apellido: str = Field(..., min_length=1, max_length=100, examples=["Rojas"])
    correo: EmailStr = Field(..., examples=["camila.rojas@fashionstore.com"])
    password: str = Field(
        ...,
        min_length=6,
        max_length=72,  # Límite estructural del algoritmo bcrypt (72 bytes)
        description="Contraseña temporal; se almacena únicamente como hash bcrypt.",
        examples=["temporal123"],
    )
    telefono: str | None = Field(default=None, max_length=20, examples=["77712345"])
    id_role: int = Field(..., ge=1, description="Rol jerárquico.", examples=[3])
    estado: EstadoUsuario = Field(default="Activo")


class UsuarioActualizar(BaseModel):
    """Datos para modificar un usuario (PUT /api/usuarios/{id_usuario}).

    Todos los campos son opcionales: el endpoint aplica una actualización
    parcial y solo toca las columnas que realmente se envían.

    El `correo` y la `password` se excluyen a propósito. El correo es la
    identidad de acceso del usuario y cambiarlo merece su propio flujo
    auditado; la contraseña se restablece mediante el CU04.

    Campos:
        nombre, apellido, telefono: datos de perfil.
        estado: permite reactivar una cuenta inhabilitada.
        id_role: permite reasignar el rol jerárquico del usuario.
    """

    nombre: str | None = Field(default=None, min_length=1, max_length=100)
    apellido: str | None = Field(default=None, min_length=1, max_length=100)
    telefono: str | None = Field(default=None, max_length=20)
    estado: EstadoUsuario | None = Field(default=None)
    id_role: int | None = Field(default=None, ge=1)


class UsuarioRespuesta(BaseModel):
    """Representación pública de un usuario.

    IMPORTANTE (RNF01): este modelo NO declara `password_hash`. Como FastAPI
    serializa la respuesta usando exactamente los campos aquí definidos, el hash
    bcrypt queda excluido de forma estructural aunque la consulta SQL llegara a
    seleccionarlo por descuido.

    Campos:
        id_usuario: clave primaria.
        nombre, apellido, correo, telefono: datos de perfil.
        estado: 'Activo' o 'Inactivo'.
        id_role: clave foránea del rol.
        rol: nombre textual del rol, resuelto por JOIN con la tabla `rol`.
        created_at: fecha de alta del registro.
    """

    id_usuario: int
    nombre: str
    apellido: str
    correo: EmailStr
    telefono: str | None = None
    estado: str
    id_role: int | None = None
    rol: str | None = None
    created_at: datetime | None = None


class RolRespuesta(BaseModel):
    """Rol disponible para poblar el menú desplegable del formulario del CU02.

    Campos:
        id_rol: clave primaria del rol.
        nombre: nombre textual (ej: "Cajero (POS)").
        descripcion: descripción de las funciones del rol.
    """

    id_rol: int
    nombre: str
    descripcion: str | None = None


class MensajeRespuesta(BaseModel):
    """Respuesta simple para operaciones que no devuelven una entidad.

    Campos:
        mensaje: texto de confirmación legible para el usuario final.
    """

    mensaje: str
