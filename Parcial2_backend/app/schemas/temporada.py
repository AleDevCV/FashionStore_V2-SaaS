"""
=============================================================================
FASHIONSTORE - ESQUEMAS DE TEMPORADAS Y COLECCIONES (CU09)
Sistemas de Información II - UAGRM
-----------------------------------------------------------------------------
Modelos Pydantic v2 para validación y serialización de temporadas comerciales
del catálogo maestro.

Soporta:
  - Validación de coherencia temporal (fecha_inicio <= fecha_fin).
  - Compatibilidad bidireccional entre 'estado' (BD) y 'activo' (Frontend).
  - Cálculo dinámico de la vigencia: "Activa", "Proxima" o "Pasada".
=============================================================================
"""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

VigenciaTemporada = Literal["Activa", "Proxima", "Pasada"]


class TemporadaBase(BaseModel):
    """Atributos comunes de una temporada comercial."""

    nombre: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Nombre identificador único de la temporada o colección",
        examples=["Primavera 2026", "Colección Floral Verano 2026"],
    )
    descripcion: str | None = Field(
        default=None,
        max_length=255,
        description="Descripción opcional o detalles conceptuales de la colección",
        examples=["Moda de temporada media para climas cálidos"],
    )
    fecha_inicio: date = Field(
        ...,
        description="Fecha de inicio de vigencia comercial (YYYY-MM-DD)",
        examples=["2026-09-01"],
    )
    fecha_fin: date = Field(
        ...,
        description="Fecha de fin de vigencia comercial (YYYY-MM-DD)",
        examples=["2026-11-30"],
    )
    estado: bool = Field(
        default=True,
        description="Indica si la temporada está habilitada en el sistema",
    )


class TemporadaCrear(TemporadaBase):
    """Datos requeridos para dar de alta una nueva temporada comercial.

    Permite enviar 'activo' como alias de 'estado' para facilitar la integración
    con clientes Angular y Flutter.
    """

    activo: bool | None = Field(
        default=None,
        description="Alias de compatibilidad con 'estado'",
    )

    @model_validator(mode="after")
    def validar_fechas_y_alias(self):
        """Valida que la fecha de inicio no sea posterior a la fecha de fin y sincroniza activo/estado."""
        if self.fecha_inicio > self.fecha_fin:
            raise ValueError("La fecha de inicio no puede ser posterior a la fecha de fin")
        if self.activo is not None:
            self.estado = self.activo
        return self


class TemporadaActualizar(BaseModel):
    """Datos para modificación total o parcial de una temporada existente."""

    nombre: str | None = Field(default=None, min_length=2, max_length=100)
    descripcion: str | None = Field(default=None, max_length=255)
    fecha_inicio: date | None = None
    fecha_fin: date | None = None
    estado: bool | None = None
    activo: bool | None = None

    @model_validator(mode="after")
    def validar_fechas_y_alias(self):
        """Valida coherencia si se envían ambas fechas y sincroniza activo con estado."""
        if self.fecha_inicio is not None and self.fecha_fin is not None:
            if self.fecha_inicio > self.fecha_fin:
                raise ValueError("La fecha de inicio no puede ser posterior a la fecha de fin")
        if self.activo is not None and self.estado is None:
            self.estado = self.activo
        return self


class TemporadaRespuesta(BaseModel):
    """Representación completa de una temporada con vigencia calculada y conteo de prendas."""

    model_config = ConfigDict(from_attributes=True)

    id_temporada: int
    nombre: str
    descripcion: str | None = None
    fecha_inicio: date
    fecha_fin: date
    estado: bool
    activo: bool = True
    vigencia: VigenciaTemporada | None = None
    total_prendas: int = 0
    created_at: datetime | None = None

    @model_validator(mode="after")
    def calcular_vigencia_y_alias(self):
        """Calcula el estado temporal dinámico frente a la fecha actual."""
        self.activo = self.estado
        hoy = date.today()
        if hoy < self.fecha_inicio:
            self.vigencia = "Proxima"
        elif self.fecha_inicio <= hoy <= self.fecha_fin:
            self.vigencia = "Activa"
        else:
            self.vigencia = "Pasada"
        return self
