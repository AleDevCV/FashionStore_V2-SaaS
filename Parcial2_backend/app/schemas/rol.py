"""
=============================================================================
FASHIONSTORE - ESQUEMAS DE ROLES Y PERMISOS (CU03)
Sistemas de Información II - UAGRM
-----------------------------------------------------------------------------
Modelos Pydantic v2 que definen los contratos para el control de acceso
basado en roles (RBAC) y la matriz de permisos por rol.
=============================================================================
"""

from pydantic import BaseModel, Field


class PermisoResponse(BaseModel):
    """Esquema de un permiso individual del catálogo del sistema."""

    id_permiso: int = Field(..., description="Identificador único del permiso.")
    nombre: str = Field(..., description="Nombre descriptivo legible.")
    codigo: str = Field(..., description="Código técnico para evaluación de permisos.")
    modulo: str = Field(..., description="Módulo funcional al que pertenece.")
    descripcion: str | None = Field(None, description="Descripción detallada del alcance.")


class RolResponse(BaseModel):
    """Esquema para listar roles del sistema."""

    id_rol: int = Field(..., description="Identificador único del rol.")
    nombre: str = Field(..., description="Nombre del rol.")
    descripcion: str | None = Field(None, description="Descripción del alcance del rol.")


class RolPermisosResponse(BaseModel):
    """Esquema que detalla los IDs de permisos asociados a un rol específico."""

    id_rol: int = Field(..., description="Identificador único del rol.")
    rol: str = Field(..., description="Nombre textual del rol.")
    permisos: list[int] = Field(..., description="Arreglo de IDs de permisos asignados al rol.")


class UpdateRolPermisosRequest(BaseModel):
    """Petición para sincronizar/actualizar los permisos asignados a un rol."""

    permisos_ids: list[int] = Field(
        ...,
        description="Lista completa de IDs de permisos que quedarán vinculados al rol.",
        examples=[[1, 2, 3, 5]],
    )


class UpdateRolPermisosResponse(BaseModel):
    """Respuesta de confirmación tras actualizar los permisos de un rol."""

    mensaje: str = Field(..., description="Mensaje de resultado de la operación.")
    id_rol: int = Field(..., description="Identificador del rol modificado.")
    total_permisos: int = Field(..., description="Cantidad total de permisos asignados tras la sincronización.")
