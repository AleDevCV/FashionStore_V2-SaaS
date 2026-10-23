"""
=============================================================================
FASHIONSTORE - ESQUEMAS DE BITÁCORA DE AUDITORÍA (CU25)
Sistemas de Información II - UAGRM
=============================================================================
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class BitacoraItem(BaseModel):
    """Representa una entrada individual de auditoría en la bitácora."""

    model_config = ConfigDict(from_attributes=True)

    id_bitacora: int
    id_usuario: Optional[int] = None
    nombre_usuario: Optional[str] = None
    correo_usuario: Optional[str] = None
    rol_usuario: Optional[str] = None
    accion: str
    tabla_afectada: Optional[str] = None
    registro_id: Optional[int] = None
    detalle: str
    ip_address: Optional[str] = None
    fecha: datetime


class BitacoraListadoRespuesta(BaseModel):
    """Paginación y listado de eventos de bitácora para el panel administrativo."""

    model_config = ConfigDict(from_attributes=True)

    total: int
    pagina: int
    limite: int
    items: List[BitacoraItem]
