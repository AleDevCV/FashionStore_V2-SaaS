"""
=============================================================================
FASHIONSTORE - ROUTER DE ROLES Y PERMISOS (CU03)
Sistemas de Información II - UAGRM
-----------------------------------------------------------------------------
Gestiona la consulta del catálogo de permisos, la visualización de la matriz
de permisos por rol y la actualización transaccional de los permisos asignados.
Audita inmutablemente cada cambio en la tabla `bitacora` (CU25).
=============================================================================
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.database import get_db
from app.schemas.rol import (
    PermisoResponse,
    RolPermisosResponse,
    RolResponse,
    UpdateRolPermisosRequest,
    UpdateRolPermisosResponse,
)
from app.services.auth_service import get_current_user, requiere_permiso, requiere_rol
from app.services.bitacora_service import (
    ACCION_UPDATE,
    obtener_ip_cliente,
    registrar_bitacora,
)

router = APIRouter(tags=["Roles y Permisos (CU03)"])


@router.get(
    "/permisos",
    response_model=list[PermisoResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar catálogo completo de permisos del sistema",
)
def listar_permisos(
    _usuario=Depends(requiere_permiso("roles.ver")),
    cursor=Depends(get_db),
):
    """Retorna todos los permisos disponibles en la plataforma agrupados y ordenados por módulo.

    Requiere permiso `roles.ver` o rol 'Administrador'.
    """
    cursor.execute("""
        SELECT id_permiso, nombre, codigo, COALESCE(modulo, 'General') AS modulo, descripcion
        FROM permiso
        ORDER BY modulo ASC, id_permiso ASC;
    """)
    return cursor.fetchall()


@router.get(
    "/roles",
    response_model=list[RolResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar roles del sistema",
)
def listar_roles(
    _usuario=Depends(requiere_permiso("roles.ver")),
    cursor=Depends(get_db),
):
    """Lista todos los roles definidos en la tabla `rol`."""
    cursor.execute("""
        SELECT id_rol, nombre, descripcion
        FROM rol
        ORDER BY id_rol ASC;
    """)
    return cursor.fetchall()


@router.get(
    "/roles/{id_rol}/permisos",
    response_model=RolPermisosResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener la lista de permisos asignados a un rol específico",
)
def obtener_permisos_de_rol(
    id_rol: int,
    _usuario=Depends(requiere_permiso("roles.ver")),
    cursor=Depends(get_db),
):
    """Retorna los identificadores de permisos asignados a un rol específico."""
    cursor.execute(
        "SELECT id_rol, nombre FROM rol WHERE id_rol = %s;",
        (id_rol,),
    )
    rol = cursor.fetchone()
    if rol is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rol con ID {id_rol} no encontrado",
        )

    cursor.execute(
        """
        SELECT id_permiso
        FROM rol_permiso
        WHERE id_rol = %s
        ORDER BY id_permiso ASC;
        """,
        (id_rol,),
    )
    filas = cursor.fetchall()
    permisos_ids = [fila["id_permiso"] for fila in filas]

    return RolPermisosResponse(
        id_rol=rol["id_rol"],
        rol=rol["nombre"],
        permisos=permisos_ids,
    )


@router.put(
    "/roles/{id_rol}/permisos",
    response_model=UpdateRolPermisosResponse,
    status_code=status.HTTP_200_OK,
    summary="Sincronizar la matriz de permisos de un rol",
)
def actualizar_permisos_de_rol(
    id_rol: int,
    datos: UpdateRolPermisosRequest,
    request: Request,
    usuario=Depends(requiere_rol(["Administrador"])),
    cursor=Depends(get_db),
):
    """Reemplaza atómicamente la lista de permisos asignados al rol especificado.

    Valida la existencia del rol y que todos los permisos solicitados existan.
    Registra el evento en la tabla `bitacora` con IP real y usuario autor.
    """
    ip_cliente = obtener_ip_cliente(request)

    # 1. Validar que el rol exista
    cursor.execute(
        "SELECT id_rol, nombre FROM rol WHERE id_rol = %s;",
        (id_rol,),
    )
    rol = cursor.fetchone()
    if rol is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rol con ID {id_rol} no encontrado",
        )

    # 2. Deduplicar IDs de permisos
    ids_unicos = list(dict.fromkeys(datos.permisos_ids))

    # 3. Validar que todos los permisos existan en la tabla `permiso`
    if ids_unicos:
        cursor.execute(
            """
            SELECT id_permiso
            FROM permiso
            WHERE id_permiso = ANY(%s);
            """,
            (ids_unicos,),
        )
        encontrados = {fila["id_permiso"] for fila in cursor.fetchall()}
        inexistentes = [p_id for p_id in ids_unicos if p_id not in encontrados]
        if inexistentes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Los siguientes permisos no existen en el sistema: {inexistentes}",
            )

    # 4. Transacción atómica: eliminar relaciones previas e insertar nuevas
    cursor.execute(
        "DELETE FROM rol_permiso WHERE id_rol = %s;",
        (id_rol,),
    )

    if ids_unicos:
        for p_id in ids_unicos:
            cursor.execute(
                """
                INSERT INTO rol_permiso (id_rol, id_permiso)
                VALUES (%s, %s);
                """,
                (id_rol, p_id),
            )

    # 5. Auditoría inmutable en bitácora (CU25)
    registrar_bitacora(
        cursor=cursor,
        accion=ACCION_UPDATE,
        tabla_afectada="rol_permiso",
        id_usuario=usuario["id_usuario"],
        registro_id=id_rol,
        detalle=(
            f"Se actualizaron los permisos del rol '{rol['nombre']}' "
            f"(ID: {id_rol}). Total asignados: {len(ids_unicos)}."
        ),
        ip_address=ip_cliente,
    )

    return UpdateRolPermisosResponse(
        mensaje="Permisos actualizados exitosamente",
        id_rol=id_rol,
        total_permisos=len(ids_unicos),
    )
