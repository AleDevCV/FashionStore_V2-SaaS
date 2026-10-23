"""
=============================================================================
FASHIONSTORE - ROUTER DE FICHAS DE CLIENTES (CU05)
Sistemas de Información II - UAGRM
-----------------------------------------------------------------------------
CRUD de los datos maestros de los compradores.

SEGURIDAD
  Las operaciones administrativas usan los permisos granulares existentes
  ``clientes.ver``, ``clientes.crear``, ``clientes.editar`` y
  ``clientes.inactivar``. El Cliente no recibe ninguno de ellos: consulta y
  actualiza su propia ficha exclusivamente mediante ``/me``.
=============================================================================
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from psycopg2 import errors as pg_errors

from app.database import get_db
from app.schemas.cliente import (
    ClienteActualizar,
    ClienteAutogestionActualizar,
    ClienteCrear,
    ClienteRespuesta,
)
from app.schemas.usuario import MensajeRespuesta
from app.services import cliente_service as svc
from app.services.auth_service import requiere_permiso, requiere_rol
from app.services.bitacora_service import (
    ACCION_INACTIVAR,
    ACCION_INSERT,
    ACCION_UPDATE,
    obtener_ip_cliente,
    registrar_bitacora,
)

router = APIRouter(prefix="/clientes", tags=["Clientes (CU05)"])

puede_ver_clientes = requiere_permiso("clientes.ver")
puede_crear_clientes = requiere_permiso("clientes.crear")
puede_editar_clientes = requiere_permiso("clientes.editar")
puede_inactivar_clientes = requiere_permiso("clientes.inactivar")
solo_cliente = requiere_rol(["Cliente"])


@router.get(
    "/",
    response_model=list[ClienteRespuesta],
    summary="Listar y buscar fichas de clientes",
)
def listar_clientes(
    busqueda: str | None = Query(default=None, description="Busca por CI o nombre"),
    estado: str | None = Query(default=None, description="Activo o Inactivo"),
    cursor=Depends(get_db),
    usuario=Depends(puede_ver_clientes),
):
    """Devuelve las fichas de cliente, con buscador y filtro de estado.

    El buscador se resuelve en la base con ILIKE sobre `ci` y `nombre_completo`,
    no en memoria: así el filtrado sigue siendo rápido cuando la tabla crezca.

    Parámetros:
        busqueda: texto libre sobre cédula o nombre.
        estado: acota el listado por estado de la ficha.
        cursor: cursor de PostgreSQL.
        usuario: sesión activa.

    Retorna:
        list[ClienteRespuesta]: clientes ordenados por nombre.
    """
    return svc.listar_clientes(cursor, busqueda, estado)


def _obtener_ficha_propia(cursor, usuario: dict) -> dict:
    """Resuelve la ficha desde la identidad autenticada, nunca desde la URL."""
    cliente = svc.obtener_cliente_por_correo(cursor, usuario["correo"])
    if cliente is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No existe una ficha de cliente vinculada a su cuenta",
        )
    return cliente


@router.get(
    "/me",
    response_model=ClienteRespuesta,
    summary="Consultar la ficha propia del cliente autenticado",
)
def obtener_mi_ficha(
    cursor=Depends(get_db),
    usuario=Depends(solo_cliente),
):
    """Devuelve únicamente la ficha vinculada a la cuenta autenticada."""
    return _obtener_ficha_propia(cursor, usuario)


@router.put(
    "/me",
    response_model=ClienteRespuesta,
    summary="Actualizar la ficha propia del cliente autenticado",
)
def actualizar_mi_ficha(
    datos: ClienteAutogestionActualizar,
    request: Request,
    cursor=Depends(get_db),
    usuario=Depends(solo_cliente),
):
    """Actualiza datos personales sin aceptar un identificador de propiedad."""
    actual = _obtener_ficha_propia(cursor, usuario)
    cambios = datos.model_dump(exclude_unset=True)
    if not cambios:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe enviar al menos un campo para actualizar",
        )

    campos_obligatorios_vacios = [
        campo
        for campo in ("ci", "nombre_completo", "correo")
        if campo in cambios and cambios[campo] is None
    ]
    if campos_obligatorios_vacios:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CI, nombre completo y correo no pueden quedar vacíos",
        )

    id_cliente = actual["id_cliente"]
    if "ci" in cambios and svc.existe_ci(cursor, cambios["ci"], excluir_id=id_cliente):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La cédula ingresada ya está asignada a otro cliente",
        )

    if cambios.get("correo"):
        if svc.existe_correo(cursor, cambios["correo"], excluir_id=id_cliente):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El correo electrónico ya está registrado por otro cliente",
            )
        if svc.existe_correo_usuario(
            cursor,
            cambios["correo"],
            excluir_id_usuario=usuario["id_usuario"],
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El correo electrónico ya está registrado por otro usuario",
            )

    svc.actualizar_cliente(cursor, id_cliente, cambios)
    svc.sincronizar_contacto_usuario(cursor, usuario["id_usuario"], cambios)

    resumen = ", ".join(cambios)
    registrar_bitacora(
        cursor=cursor,
        accion=ACCION_UPDATE,
        tabla_afectada="cliente",
        registro_id=id_cliente,
        detalle=f"Autogestión de ficha propia. Campos: {resumen}.",
        id_usuario=usuario["id_usuario"],
        ip_address=obtener_ip_cliente(request),
    )
    return svc.obtener_cliente(cursor, id_cliente)


@router.get(
    "/{id_cliente}",
    response_model=ClienteRespuesta,
    summary="Consultar una ficha de cliente",
)
def obtener_cliente(
    id_cliente: int,
    cursor=Depends(get_db),
    usuario=Depends(puede_ver_clientes),
):
    """Recupera la ficha de un cliente concreto.

    Parámetros:
        id_cliente: clave primaria buscada.
        cursor: cursor de PostgreSQL.
        usuario: sesión activa.

    Retorna:
        ClienteRespuesta: la ficha del cliente.

    Errores:
        HTTP 404: no existe ningún cliente con ese identificador.
    """
    cliente = svc.obtener_cliente(cursor, id_cliente)
    if cliente is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El cliente solicitado no existe",
        )
    return cliente


@router.post(
    "/",
    response_model=ClienteRespuesta,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar una ficha de cliente",
)
def crear_cliente(
    datos: ClienteCrear,
    request: Request,
    cursor=Depends(get_db),
    usuario=Depends(puede_crear_clientes),
):
    """Registra la ficha maestra de un comprador.

    Lógica transaccional y validaciones:
      1. La cédula no puede estar repetida (excepción A del CU05): la columna
         `ci` es UNIQUE en la tabla.
      2. El correo tampoco, porque también está declarado UNIQUE.
      3. El INSERT y su registro de auditoría comparten transacción.

    Parámetros:
        datos: cuerpo JSON validado por Pydantic.
        request: petición HTTP, para la IP del cliente.
        cursor: cursor de PostgreSQL.
        usuario: quien registra la ficha; queda auditado.

    Retorna:
        ClienteRespuesta: la ficha creada, con código HTTP 201.

    Errores:
        HTTP 400: la cédula o el correo ya están registrados.
    """
    if svc.existe_ci(cursor, datos.ci):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La cédula ingresada ya está asignada a otro cliente",
        )

    if datos.correo and svc.existe_correo(cursor, datos.correo):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo electrónico ya está registrado por otro cliente",
        )

    try:
        id_cliente = svc.crear_cliente(cursor, datos.model_dump())
    except pg_errors.UniqueViolation:
        # Red de seguridad ante una condición de carrera entre dos altas.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La cédula ingresada ya está asignada a otro cliente",
        )

    registrar_bitacora(
        cursor=cursor,
        accion=ACCION_INSERT,
        tabla_afectada="cliente",
        registro_id=id_cliente,
        detalle=f"Alta del cliente '{datos.nombre_completo}' (CI {datos.ci}).",
        id_usuario=usuario["id_usuario"],
        ip_address=obtener_ip_cliente(request),
    )

    return svc.obtener_cliente(cursor, id_cliente)


@router.put(
    "/{id_cliente}",
    response_model=ClienteRespuesta,
    summary="Actualizar una ficha de cliente",
)
def actualizar_cliente(
    id_cliente: int,
    datos: ClienteActualizar,
    request: Request,
    cursor=Depends(get_db),
    usuario=Depends(puede_editar_clientes),
):
    """Modifica los datos de una ficha existente.

    Actualización parcial: solo se escriben las columnas enviadas. Si se cambia
    la cédula o el correo, se revalida la unicidad excluyendo al propio cliente
    (de lo contrario, guardar sin cambios daría un falso duplicado).

    Parámetros:
        id_cliente: ficha a modificar.
        datos: campos a actualizar, todos opcionales.
        request: petición HTTP, para la IP del cliente.
        cursor: cursor de PostgreSQL.
        usuario: quien realiza el cambio; queda auditado.

    Retorna:
        ClienteRespuesta: la ficha ya actualizada.

    Errores:
        HTTP 400: sin campos que actualizar, o cédula/correo duplicados.
        HTTP 404: el cliente no existe.
    """
    actual = svc.obtener_cliente(cursor, id_cliente)
    if actual is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El cliente solicitado no existe",
        )

    cambios = datos.model_dump(exclude_unset=True)
    if not cambios:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe enviar al menos un campo para actualizar",
        )

    if "ci" in cambios and svc.existe_ci(cursor, cambios["ci"], excluir_id=id_cliente):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La cédula ingresada ya está asignada a otro cliente",
        )

    if (
        cambios.get("correo")
        and svc.existe_correo(cursor, cambios["correo"], excluir_id=id_cliente)
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo electrónico ya está registrado por otro cliente",
        )

    svc.actualizar_cliente(cursor, id_cliente, cambios)

    resumen = ", ".join(f"{k}={v}" for k, v in cambios.items())
    registrar_bitacora(
        cursor=cursor,
        accion=ACCION_UPDATE,
        tabla_afectada="cliente",
        registro_id=id_cliente,
        detalle=f"Modificación del cliente CI {actual['ci']}. Campos: {resumen}.",
        id_usuario=usuario["id_usuario"],
        ip_address=obtener_ip_cliente(request),
    )

    return svc.obtener_cliente(cursor, id_cliente)


@router.delete(
    "/{id_cliente}",
    response_model=MensajeRespuesta,
    summary="Inhabilitar una ficha de cliente (borrado lógico)",
)
def inhabilitar_cliente(
    id_cliente: int,
    request: Request,
    cursor=Depends(get_db),
    usuario=Depends(puede_inactivar_clientes),
):
    """Da de baja lógica a un cliente cambiando su estado a 'Inactivo'.

    NO se ejecuta un DELETE físico: la tabla `cliente` está referenciada por
    `venta` y `reserva`, de modo que borrarla destruiría el historial comercial
    o fallaría por integridad referencial.

    Parámetros:
        id_cliente: ficha a inhabilitar.
        request: petición HTTP, para la IP del cliente.
        cursor: cursor de PostgreSQL.
        usuario: quien realiza la baja; queda auditado.

    Retorna:
        MensajeRespuesta: confirmación de la inhabilitación.

    Errores:
        HTTP 404: el cliente no existe.
        HTTP 409: la ficha ya estaba inactiva.
    """
    cliente = svc.obtener_cliente(cursor, id_cliente)
    if cliente is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El cliente solicitado no existe",
        )

    if cliente["estado"] == "Inactivo":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El cliente ya se encuentra inhabilitado",
        )

    svc.inhabilitar_cliente(cursor, id_cliente)

    registrar_bitacora(
        cursor=cursor,
        accion=ACCION_INACTIVAR,
        tabla_afectada="cliente",
        registro_id=id_cliente,
        detalle=(
            f"Baja lógica del cliente '{cliente['nombre_completo']}' "
            f"(CI {cliente['ci']})."
        ),
        id_usuario=usuario["id_usuario"],
        ip_address=obtener_ip_cliente(request),
    )

    return MensajeRespuesta(
        mensaje=f"El cliente {cliente['nombre_completo']} fue inhabilitado correctamente."
    )
