"""
=============================================================================
FASHIONSTORE - ROUTER DE CATEGORÍAS DE PRENDAS (CU07)
Sistemas de Información II - UAGRM
-----------------------------------------------------------------------------
CRUD de la clasificación jerárquica del catálogo.

SEGURIDAD
  La consulta administrativa exige ``categorias.ver`` y las operaciones de
  alta, edición e inactivación exigen ``categorias.gestionar``. El catálogo
  público utiliza /api/catalogo/filtros y no depende de este router.
=============================================================================
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from psycopg2 import errors as pg_errors

from app.database import get_db
from app.schemas.categoria import (
    CategoriaActualizar,
    CategoriaCrear,
    CategoriaRespuesta,
)
from app.schemas.usuario import MensajeRespuesta
from app.services import categoria_service as svc
from app.services.auth_service import requiere_permiso
from app.services.bitacora_service import (
    ACCION_INACTIVAR,
    ACCION_INSERT,
    ACCION_UPDATE,
    obtener_ip_cliente,
    registrar_bitacora,
)

router = APIRouter(prefix="/categorias", tags=["Categorías (CU07)"])

puede_ver_categorias = requiere_permiso("categorias.ver")
puede_gestionar_categorias = requiere_permiso("categorias.gestionar")


@router.get(
    "/",
    response_model=list[CategoriaRespuesta],
    summary="Listar el árbol de categorías",
)
def listar_categorias(
    estado: str | None = Query(default=None, description="Activo o Inactivo"),
    cursor=Depends(get_db),
    usuario=Depends(puede_ver_categorias),
):
    """Devuelve la jerarquía de categorías con su categoría padre resuelta.

    Parámetros:
        estado: acota el listado por estado.
        cursor: cursor de PostgreSQL.
        usuario: sesión activa.

    Retorna:
        list[CategoriaRespuesta]: categorías raíz primero, luego sus hijas.
    """
    return svc.listar_categorias(cursor, estado)


@router.post(
    "/",
    response_model=CategoriaRespuesta,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar una categoría",
)
def crear_categoria(
    datos: CategoriaCrear,
    request: Request,
    cursor=Depends(get_db),
    usuario=Depends(puede_gestionar_categorias),
):
    """Registra una categoría, opcionalmente colgando de otra.

    Validaciones aplicadas:
      1. El nombre no puede repetirse (la columna es UNIQUE).
      2. Si se indica una categoría padre, debe existir; así se devuelve un
         mensaje claro en vez de un error de clave foránea.

    Parámetros:
        datos: nombre, descripción y categoría padre.
        request: petición HTTP, para la IP del cliente.
        cursor: cursor de PostgreSQL.
        usuario: quien registra; queda auditado.

    Retorna:
        CategoriaRespuesta: la categoría creada, con código HTTP 201.

    Errores:
        HTTP 400: nombre duplicado o categoría padre inexistente.
    """
    if svc.existe_nombre(cursor, datos.nombre):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe una categoría con ese nombre",
        )

    if datos.id_categoria_padre and not svc.existe_categoria(
        cursor, datos.id_categoria_padre
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La categoría padre indicada no existe",
        )

    try:
        id_categoria = svc.crear_categoria(cursor, datos.model_dump())
    except pg_errors.UniqueViolation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe una categoría con ese nombre",
        )

    registrar_bitacora(
        cursor=cursor,
        accion=ACCION_INSERT,
        tabla_afectada="categoria",
        registro_id=id_categoria,
        detalle=f"Alta de la categoría '{datos.nombre}'.",
        id_usuario=usuario["id_usuario"],
        ip_address=obtener_ip_cliente(request),
    )

    return svc.obtener_categoria(cursor, id_categoria)


@router.put(
    "/{id_categoria}",
    response_model=CategoriaRespuesta,
    summary="Actualizar una categoría",
)
def actualizar_categoria(
    id_categoria: int,
    datos: CategoriaActualizar,
    request: Request,
    cursor=Depends(get_db),
    usuario=Depends(puede_gestionar_categorias),
):
    """Modifica una categoría existente.

    Además de las validaciones habituales, se impide que una categoría se
    asigne a sí misma como padre: eso crearía un ciclo en el árbol y las
    consultas jerárquicas quedarían en bucle infinito.

    Parámetros:
        id_categoria: categoría a modificar.
        datos: campos a actualizar, todos opcionales.
        request: petición HTTP, para la IP del cliente.
        cursor: cursor de PostgreSQL.
        usuario: quien realiza el cambio; queda auditado.

    Retorna:
        CategoriaRespuesta: la categoría ya actualizada.

    Errores:
        HTTP 400: sin campos, nombre duplicado, padre inexistente o ciclo.
        HTTP 404: la categoría no existe.
    """
    actual = svc.obtener_categoria(cursor, id_categoria)
    if actual is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La categoría solicitada no existe",
        )

    cambios = datos.model_dump(exclude_unset=True)
    if not cambios:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe enviar al menos un campo para actualizar",
        )

    if "nombre" in cambios and svc.existe_nombre(
        cursor, cambios["nombre"], excluir_id=id_categoria
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe una categoría con ese nombre",
        )

    if "id_categoria_padre" in cambios and cambios["id_categoria_padre"] is not None:
        if cambios["id_categoria_padre"] == id_categoria:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Una categoría no puede ser su propia categoría padre",
            )
        if not svc.existe_categoria(cursor, cambios["id_categoria_padre"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La categoría padre indicada no existe",
            )

    svc.actualizar_categoria(cursor, id_categoria, cambios)

    resumen = ", ".join(f"{k}={v}" for k, v in cambios.items())
    registrar_bitacora(
        cursor=cursor,
        accion=ACCION_UPDATE,
        tabla_afectada="categoria",
        registro_id=id_categoria,
        detalle=f"Modificación de la categoría '{actual['nombre']}'. Campos: {resumen}.",
        id_usuario=usuario["id_usuario"],
        ip_address=obtener_ip_cliente(request),
    )

    return svc.obtener_categoria(cursor, id_categoria)


@router.delete(
    "/{id_categoria}",
    response_model=MensajeRespuesta,
    summary="Inhabilitar una categoría (borrado lógico)",
)
def inhabilitar_categoria(
    id_categoria: int,
    request: Request,
    cursor=Depends(get_db),
    usuario=Depends(puede_gestionar_categorias),
):
    """Retira una categoría del catálogo mediante baja lógica.

    No se borra físicamente porque `prenda.id_categoria` la referencia con
    ON DELETE RESTRICT: un DELETE fallaría en cuanto exista una sola prenda
    clasificada en ella.

    Se bloquea además si la categoría tiene subcategorías activas colgando: un
    árbol con hijas activas bajo un padre inactivo sería incoherente.

    Parámetros:
        id_categoria: categoría a inhabilitar.
        request: petición HTTP, para la IP del cliente.
        cursor: cursor de PostgreSQL.
        usuario: quien realiza la baja; queda auditado.

    Retorna:
        MensajeRespuesta: confirmación de la inhabilitación.

    Errores:
        HTTP 404: la categoría no existe.
        HTTP 409: ya estaba inactiva, o tiene subcategorías activas.
    """
    categoria = svc.obtener_categoria(cursor, id_categoria)
    if categoria is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La categoría solicitada no existe",
        )

    if categoria["estado"] == "Inactivo":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La categoría ya se encuentra inhabilitada",
        )

    if svc.tiene_subcategorias(cursor, id_categoria):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "No se puede inhabilitar: la categoría tiene subcategorías "
                "activas. Inhabilítelas primero."
            ),
        )

    svc.inhabilitar_categoria(cursor, id_categoria)

    registrar_bitacora(
        cursor=cursor,
        accion=ACCION_INACTIVAR,
        tabla_afectada="categoria",
        registro_id=id_categoria,
        detalle=(
            f"Baja lógica de la categoría '{categoria['nombre']}' "
            f"({categoria['total_prendas']} prenda(s) asociadas)."
        ),
        id_usuario=usuario["id_usuario"],
        ip_address=obtener_ip_cliente(request),
    )

    return MensajeRespuesta(
        mensaje=f"La categoría {categoria['nombre']} fue inhabilitada correctamente."
    )
