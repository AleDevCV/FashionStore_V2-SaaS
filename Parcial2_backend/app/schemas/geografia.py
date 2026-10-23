"""
=============================================================================
FASHIONSTORE - ESQUEMAS DE CIUDADES Y SUCURSALES (CU06)
Sistemas de Información II - UAGRM
-----------------------------------------------------------------------------
Contrato de datos del módulo geográfico. Refleja exactamente las columnas de
las tablas `ciudad` y `sucursal` de PostgreSQL.
=============================================================================
"""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


# -----------------------------------------------------------------------------
# CIUDAD
# -----------------------------------------------------------------------------

class CiudadCrear(BaseModel):
    """Datos para registrar una ciudad de cobertura.

    Campos:
        nombre: nombre de la ciudad. La tabla lo declara UNIQUE, por lo que dos
                ciudades no pueden repetirse.
    """

    nombre: str = Field(..., min_length=2, max_length=100, examples=["Tarija"])


class CiudadRespuesta(BaseModel):
    """Ciudad tal como la devuelve la API.

    Campos:
        id_ciudad: clave primaria.
        nombre: nombre de la ciudad.
        total_sucursales: cuántas sucursales físicas operan en ella. Se calcula
                          con un COUNT en la consulta, no es una columna.
    """

    id_ciudad: int
    nombre: str
    total_sucursales: int = 0


# -----------------------------------------------------------------------------
# SUCURSAL
# -----------------------------------------------------------------------------

class SucursalCrear(BaseModel):
    """Datos para registrar una sucursal física.

    Campos:
        nombre: nombre comercial de la tienda.
        direccion: dirección física detallada.
        telefono: teléfono de contacto, opcional.
        id_ciudad: ciudad donde se ubica (FK a `ciudad`).
        id_encargado: usuario responsable (FK a `usuario`). Es opcional porque
                      una sucursal puede registrarse antes de asignar personal.
    """

    nombre: str = Field(..., min_length=2, max_length=100, examples=["Sucursal Norte"])
    direccion: str = Field(..., min_length=3, max_length=255)
    telefono: str | None = Field(default=None, max_length=20)
    id_ciudad: int = Field(..., ge=1)
    id_encargado: int | None = Field(default=None, ge=1)


class SucursalActualizar(BaseModel):
    """Datos para modificar una sucursal.

    Todos los campos son opcionales: el endpoint aplica actualización parcial y
    solo toca las columnas realmente enviadas.
    """

    nombre: str | None = Field(default=None, min_length=2, max_length=100)
    direccion: str | None = Field(default=None, min_length=3, max_length=255)
    telefono: str | None = Field(default=None, max_length=20)
    id_ciudad: int | None = Field(default=None, ge=1)
    id_encargado: int | None = Field(default=None, ge=1)


class SucursalRespuesta(BaseModel):
    """Sucursal con su ciudad y su encargado ya resueltos por JOIN.

    Los campos `ciudad` y `encargado` no son columnas: provienen del cruce con
    las tablas `ciudad` y `usuario`, y evitan que el frontend tenga que hacer
    peticiones adicionales para mostrar nombres en lugar de identificadores.
    """

    id_sucursal: int
    nombre: str
    direccion: str
    telefono: str | None = None
    id_ciudad: int | None = None
    ciudad: str | None = None
    id_encargado: int | None = None
    encargado: str | None = None
    created_at: datetime | None = None
