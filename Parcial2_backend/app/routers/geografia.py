"""
=============================================================================
FASHIONSTORE - ROUTER DE CIUDADES Y SUCURSALES (CU06)
Sistemas de Información II - UAGRM
-----------------------------------------------------------------------------
Expone la cobertura geográfica de la cadena. Capa delgada: valida permisos,
delega el SQL en `geografia_service` y traduce los errores a códigos HTTP.

SEGURIDAD
  Lectura   -> exige sesión activa (get_current_user).
  Escritura -> exige además el rol "Administrador" (requiere_rol).
=============================================================================
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from psycopg2 import errors as pg_errors

from app.database import get_db
from app.schemas.geografia import (
    CiudadCrear,
    CiudadRespuesta,
    SucursalActualizar,
    SucursalCrear,
    SucursalRespuesta,
)
from app.services import geografia_service as svc
from app.services.auth_service import get_current_user, requiere_rol
from app.services.bitacora_service import (
    ACCION_INSERT,
    ACCION_UPDATE,
    obtener_ip_cliente,
    registrar_bitacora,
)

router = APIRouter(tags=["Ciudades y Sucursales (CU06)"])

# Solo el Administrador define la cobertura geográfica de la cadena.
solo_administrador = requiere_rol(["Administrador"])


# =============================================================================
# CIUDADES
# =============================================================================

@router.get(
    "/ciudades",
    response_model=list[CiudadRespuesta],
    summary="Listar las ciudades de cobertura",
)
def listar_ciudades(cursor=Depends(get_db), usuario=Depends(get_current_user)):
    """Devuelve todas las ciudades con su número de sucursales.

    Parámetros:
        cursor: cursor de PostgreSQL inyectado por `get_db`.
        usuario: sesión activa; su presencia obliga a validar el token.

    Retorna:
        list[CiudadRespuesta]: ciudades ordenadas alfabéticamente.
    """
    return svc.listar_ciudades(cursor)


@router.post(
    "/ciudades",
    response_model=CiudadRespuesta,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar una ciudad",
)
def crear_ciudad(
    datos: CiudadCrear,
    request: Request,
    cursor=Depends(get_db),
    administrador=Depends(solo_administrador),
):
    """Registra una nueva ciudad de cobertura.

    Lógica transaccional: se comprueba que el nombre no exista (la columna es
    UNIQUE) y, en la MISMA transacción, se inserta la ciudad y su registro de
    auditoría. Si algo falla, ambos se revierten juntos.

    Parámetros:
        datos: nombre de la ciudad.
        request: petición HTTP, usada para obtener la IP del cliente.
        cursor: cursor de PostgreSQL.
        administrador: administrador autenticado; queda auditado.

    Retorna:
        CiudadRespuesta: la ciudad creada, con código HTTP 201.

    Errores:
        HTTP 400: ya existe una ciudad con ese nombre.
    """
    if svc.existe_ciudad_por_nombre(cursor, datos.nombre):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe una ciudad registrada con ese nombre",
        )

    try:
        ciudad = svc.crear_ciudad(cursor, datos.nombre)
    except pg_errors.UniqueViolation:
        # Red de seguridad ante dos altas simultáneas con el mismo nombre.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe una ciudad registrada con ese nombre",
        )

    registrar_bitacora(
        cursor=cursor,
        accion=ACCION_INSERT,
        tabla_afectada="ciudad",
        registro_id=ciudad["id_ciudad"],
        detalle=f"Alta de la ciudad '{datos.nombre}'.",
        id_usuario=administrador["id_usuario"],
        ip_address=obtener_ip_cliente(request),
    )

    return ciudad


# =============================================================================
# SUCURSALES
# =============================================================================

@router.get(
    "/sucursales",
    response_model=list[SucursalRespuesta],
    summary="Listar las sucursales físicas",
)
def listar_sucursales(
    id_ciudad: int | None = Query(default=None, description="Filtrar por ciudad"),
    cursor=Depends(get_db),
    usuario=Depends(get_current_user),
):
    """Devuelve las sucursales con su ciudad y su encargado resueltos.

    Parámetros:
        id_ciudad: filtro opcional por ciudad.
        cursor: cursor de PostgreSQL.
        usuario: sesión activa.

    Retorna:
        list[SucursalRespuesta]: sucursales ordenadas por ciudad y nombre.
    """
    return svc.listar_sucursales(cursor, id_ciudad)


@router.post(
    "/sucursales",
    response_model=SucursalRespuesta,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar una sucursal",
)
def crear_sucursal(
    datos: SucursalCrear,
    request: Request,
    cursor=Depends(get_db),
    administrador=Depends(solo_administrador),
):
    """Registra una sucursal física y la asocia a una ciudad.

    Lógica transaccional:
      1. Se valida que la ciudad exista, para devolver un mensaje claro en
         lugar de un error crudo de clave foránea.
      2. Se inserta la sucursal.
      3. Se audita el alta en la misma transacción.

    Parámetros:
        datos: nombre, dirección, teléfono, ciudad y encargado.
        request: petición HTTP, para la IP del cliente.
        cursor: cursor de PostgreSQL.
        administrador: administrador autenticado.

    Retorna:
        SucursalRespuesta: la sucursal creada, con código HTTP 201.

    Errores:
        HTTP 400: la ciudad indicada no existe.
    """
    if not svc.existe_ciudad(cursor, datos.id_ciudad):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La ciudad indicada no existe en el sistema",
        )

    try:
        id_sucursal = svc.crear_sucursal(cursor, datos.model_dump())
    except pg_errors.ForeignKeyViolation:
        # Cubre un id_encargado que no corresponde a ningún usuario.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El encargado indicado no existe en el sistema",
        )

    registrar_bitacora(
        cursor=cursor,
        accion=ACCION_INSERT,
        tabla_afectada="sucursal",
        registro_id=id_sucursal,
        detalle=(
            f"Alta de la sucursal '{datos.nombre}' en la ciudad "
            f"id={datos.id_ciudad}."
        ),
        id_usuario=administrador["id_usuario"],
        ip_address=obtener_ip_cliente(request),
    )

    return svc.obtener_sucursal(cursor, id_sucursal)


@router.put(
    "/sucursales/{id_sucursal}",
    response_model=SucursalRespuesta,
    summary="Actualizar una sucursal",
)
def actualizar_sucursal(
    id_sucursal: int,
    datos: SucursalActualizar,
    request: Request,
    cursor=Depends(get_db),
    administrador=Depends(solo_administrador),
):
    """Modifica los datos de una sucursal existente.

    La actualización es parcial: solo se tocan las columnas enviadas
    (`exclude_unset`), de modo que omitir un campo lo deja intacto en lugar de
    sobrescribirlo con NULL.

    Parámetros:
        id_sucursal: sucursal a modificar.
        datos: campos a actualizar, todos opcionales.
        request: petición HTTP, para la IP del cliente.
        cursor: cursor de PostgreSQL.
        administrador: administrador autenticado.

    Retorna:
        SucursalRespuesta: la sucursal ya actualizada.

    Errores:
        HTTP 400: no se envió ningún campo, o la ciudad indicada no existe.
        HTTP 404: la sucursal no existe.
    """
    actual = svc.obtener_sucursal(cursor, id_sucursal)
    if actual is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La sucursal solicitada no existe",
        )

    cambios = datos.model_dump(exclude_unset=True)
    if not cambios:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe enviar al menos un campo para actualizar",
        )

    if "id_ciudad" in cambios and not svc.existe_ciudad(cursor, cambios["id_ciudad"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La ciudad indicada no existe en el sistema",
        )

    try:
        svc.actualizar_sucursal(cursor, id_sucursal, cambios)
    except pg_errors.ForeignKeyViolation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El encargado indicado no existe en el sistema",
        )

    resumen = ", ".join(f"{k}={v}" for k, v in cambios.items())
    registrar_bitacora(
        cursor=cursor,
        accion=ACCION_UPDATE,
        tabla_afectada="sucursal",
        registro_id=id_sucursal,
        detalle=f"Modificación de la sucursal '{actual['nombre']}'. Campos: {resumen}.",
        id_usuario=administrador["id_usuario"],
        ip_address=obtener_ip_cliente(request),
    )

    return svc.obtener_sucursal(cursor, id_sucursal)
