"""
=============================================================================
FASHIONSTORE - ROUTER DE PRENDAS DEL CATÁLOGO (CU08)
Sistemas de Información II - UAGRM
-----------------------------------------------------------------------------
Administración del catálogo maestro de ropa.

SEGURIDAD
  Lectura   -> exige sesión activa (get_current_user).
  Escritura -> exige además el rol "Administrador" (requiere_rol).
=============================================================================
"""

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
from psycopg2 import errors as pg_errors

from app.database import get_db
from app.schemas.prenda import (
    ImagenPrendaRespuesta,
    PrendaActualizar,
    PrendaCrear,
    PrendaRespuesta,
)
from app.schemas.usuario import MensajeRespuesta
from app.services import categoria_service as cat_svc
from app.services import prenda_service as svc
from app.services.image_storage_service import subir_imagen_prenda as almacenar_imagen_prenda
from app.services.auth_service import get_current_user, requiere_rol
from app.services.bitacora_service import (
    ACCION_INACTIVAR,
    ACCION_INSERT,
    ACCION_UPDATE,
    obtener_ip_cliente,
    registrar_bitacora,
)

router = APIRouter(prefix="/prendas", tags=["Prendas del Catálogo (CU08)"])

# El catálogo maestro solo lo edita el Administrador.
solo_administrador = requiere_rol(["Administrador"])


# -----------------------------------------------------------------------------
# CATÁLOGOS AUXILIARES DEL FORMULARIO
# -----------------------------------------------------------------------------
# Se declaran ANTES que /{id_prenda}: FastAPI evalúa las rutas en orden y, si
# estuvieran después, "tallas" se interpretaría como un identificador.

@router.get("/tallas", summary="Listar las tallas disponibles")
def listar_tallas(cursor=Depends(get_db), usuario=Depends(get_current_user)):
    """Devuelve el catálogo de tallas para el constructor de variantes.

    Parámetros:
        cursor: cursor de PostgreSQL.
        usuario: sesión activa.

    Retorna:
        list[dict]: tallas ordenadas por identificador.
    """
    return svc.listar_tallas(cursor)


@router.get("/colores", summary="Listar los colores disponibles")
def listar_colores(cursor=Depends(get_db), usuario=Depends(get_current_user)):
    """Devuelve el catálogo de colores con su código hexadecimal.

    Parámetros:
        cursor: cursor de PostgreSQL.
        usuario: sesión activa.

    Retorna:
        list[dict]: colores ordenados alfabéticamente.
    """
    return svc.listar_colores(cursor)


@router.post(
    "/imagenes",
    response_model=ImagenPrendaRespuesta,
    status_code=status.HTTP_201_CREATED,
    summary="Subir una imagen de prenda",
)
async def subir_imagen(
    archivo: UploadFile = File(...),
    administrador=Depends(solo_administrador),
):
    """Valida y almacena una imagen; solo esta disponible para Administradores."""
    url_imagen = await almacenar_imagen_prenda(archivo)
    return ImagenPrendaRespuesta(url_imagen=url_imagen)


# -----------------------------------------------------------------------------
# CONSULTA
# -----------------------------------------------------------------------------

@router.get(
    "/",
    response_model=list[PrendaRespuesta],
    summary="Listar las prendas del catálogo",
)
def listar_prendas(
    busqueda: str | None = Query(default=None, description="Busca por SKU o nombre"),
    id_categoria: int | None = Query(default=None),
    genero: str | None = Query(default=None),
    estado: str | None = Query(default=None),
    id_temporada: int | None = Query(default=None, description="Filtro opcional por temporada"),
    cursor=Depends(get_db),
    usuario=Depends(get_current_user),
):
    """Devuelve las prendas con sus filtros administrativos.

    El listado NO incluye las variantes de cada prenda: adjuntarlas obligaría a
    una consulta por fila y encarecería la carga de la tabla (RNF02). El
    detalle con variantes se obtiene con GET /api/prendas/{id_prenda}.

    Parámetros:
        busqueda: texto libre sobre SKU o nombre.
        id_categoria, genero, estado, id_temporada: filtros exactos.
        cursor: cursor de PostgreSQL.
        usuario: sesión activa.

    Retorna:
        list[PrendaRespuesta]: prendas ordenadas de la más reciente a la más antigua.
    """
    return svc.listar_prendas(cursor, busqueda, id_categoria, genero, estado, id_temporada)


@router.get(
    "/{id_prenda}",
    response_model=PrendaRespuesta,
    summary="Consultar una prenda con sus variantes",
)
def obtener_prenda(
    id_prenda: int,
    cursor=Depends(get_db),
    usuario=Depends(get_current_user),
):
    """Recupera la ficha completa de una prenda, con todas sus variantes.

    Parámetros:
        id_prenda: clave primaria buscada.
        cursor: cursor de PostgreSQL.
        usuario: sesión activa.

    Retorna:
        PrendaRespuesta: la prenda con su matriz de talla/color y stock.

    Errores:
        HTTP 404: la prenda no existe.
    """
    prenda = svc.obtener_prenda(cursor, id_prenda)
    if prenda is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La prenda solicitada no existe",
        )
    return prenda


# -----------------------------------------------------------------------------
# ALTA
# -----------------------------------------------------------------------------

@router.post(
    "/",
    response_model=PrendaRespuesta,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar una prenda con sus variantes",
)
def crear_prenda(
    datos: PrendaCrear,
    request: Request,
    cursor=Depends(get_db),
    administrador=Depends(solo_administrador),
):
    """Da de alta una prenda, sus variantes y su inventario inicial.

    LÓGICA TRANSACCIONAL — la operación toca cuatro tablas y todas viajan en la
    MISMA transacción abierta por `get_db`, de modo que un fallo en cualquier
    punto revierte el conjunto y no deja una prenda a medio crear:

        prenda           -> el diseño maestro
        imagen_prenda    -> la fotografía principal (si se envió URL)
        variante_prenda  -> una fila por combinación talla + color
        inventario       -> una fila por (variante, sucursal) con su stock

    Validaciones previas:
      1. El SKU maestro no puede repetirse (columna UNIQUE).
      2. La categoría debe existir (evita un error crudo de clave foránea).
      3. No pueden enviarse dos variantes con la misma talla y color, porque la
         tabla declara UNIQUE (id_prenda, id_talla, id_color).

    Parámetros:
        datos: cuerpo JSON con los datos maestros y la matriz de variantes.
        request: petición HTTP, para la IP del cliente.
        cursor: cursor de PostgreSQL.
        administrador: administrador autenticado; queda auditado.

    Retorna:
        PrendaRespuesta: la prenda creada con sus variantes, código HTTP 201.

    Errores:
        HTTP 400: SKU duplicado, categoría inexistente, variantes repetidas o
                  talla/color inexistentes.
    """
    # --- 1. SKU único --------------------------------------------------------
    if svc.existe_sku(cursor, datos.sku):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe una prenda registrada con ese SKU",
        )

    # --- 2. Categoría existente ---------------------------------------------
    if not cat_svc.existe_categoria(cursor, datos.id_categoria):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La categoría indicada no existe en el sistema",
        )

    # --- 3. Temporada existente (si se envía) -------------------------------
    if datos.id_temporada is not None and not svc.existe_temporada(cursor, datos.id_temporada):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La temporada indicada no existe en el sistema",
        )

    # --- 4. Sin variantes repetidas -----------------------------------------
    combinaciones = [(v.id_talla, tuple(sorted(set([v.id_color,*v.color_ids])))) for v in datos.variantes]
    if len(combinaciones) != len(set(combinaciones)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puede repetir la misma combinación de talla y color",
        )

    try:
        id_prenda = svc.crear_prenda(cursor, datos.model_dump())
    except pg_errors.ForeignKeyViolation:
        # Alguna talla o color de la matriz de variantes no existe.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Alguna talla o color indicado no existe en el sistema",
        )
    except pg_errors.UniqueViolation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe una prenda registrada con ese SKU",
        )

    registrar_bitacora(
        cursor=cursor,
        accion=ACCION_INSERT,
        tabla_afectada="prenda",
        registro_id=id_prenda,
        detalle=(
            f"Alta de la prenda '{datos.nombre}' (SKU {datos.sku}) con "
            f"{len(datos.variantes)} variante(s)."
        ),
        id_usuario=administrador["id_usuario"],
        ip_address=obtener_ip_cliente(request),
    )

    return svc.obtener_prenda(cursor, id_prenda)


# -----------------------------------------------------------------------------
# MODIFICACIÓN Y BAJA
# -----------------------------------------------------------------------------

@router.put(
    "/{id_prenda}",
    response_model=PrendaRespuesta,
    summary="Actualizar los datos maestros de una prenda",
)
def actualizar_prenda(
    id_prenda: int,
    datos: PrendaActualizar,
    request: Request,
    cursor=Depends(get_db),
    administrador=Depends(solo_administrador),
):
    """Modifica los datos maestros de una prenda.

    Las VARIANTES no se tocan por esta vía: alterarlas afectaría al inventario
    ya registrado en cada sucursal. Si se envía una nueva `url_imagen`, la
    fotografía anterior se degrada a secundaria en lugar de borrarse.

    Parámetros:
        id_prenda: prenda a modificar.
        datos: campos a actualizar, todos opcionales.
        request: petición HTTP, para la IP del cliente.
        cursor: cursor de PostgreSQL.
        administrador: administrador autenticado.

    Retorna:
        PrendaRespuesta: la prenda ya actualizada.

    Errores:
        HTTP 400: sin campos, SKU duplicado o categoría inexistente.
        HTTP 404: la prenda no existe.
    """
    actual = svc.obtener_prenda(cursor, id_prenda, con_variantes=False)
    if actual is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La prenda solicitada no existe",
        )

    cambios = datos.model_dump(exclude_unset=True)
    if not cambios:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe enviar al menos un campo para actualizar",
        )

    if "sku" in cambios and svc.existe_sku(cursor, cambios["sku"], excluir_id=id_prenda):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe una prenda registrada con ese SKU",
        )

    if "id_categoria" in cambios and not cat_svc.existe_categoria(
        cursor, cambios["id_categoria"]
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La categoría indicada no existe en el sistema",
        )

    if (
        "id_temporada" in cambios
        and cambios["id_temporada"] is not None
        and not svc.existe_temporada(cursor, cambios["id_temporada"])
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La temporada indicada no existe en el sistema",
        )

    # El resumen se arma ANTES de llamar al servicio, porque este extrae
    # `url_imagen` del diccionario para tratarla en su propia tabla.
    resumen = ", ".join(f"{k}={v}" for k, v in cambios.items())
    svc.actualizar_prenda(cursor, id_prenda, cambios)

    registrar_bitacora(
        cursor=cursor,
        accion=ACCION_UPDATE,
        tabla_afectada="prenda",
        registro_id=id_prenda,
        detalle=f"Modificación de la prenda SKU {actual['sku']}. Campos: {resumen}.",
        id_usuario=administrador["id_usuario"],
        ip_address=obtener_ip_cliente(request),
    )

    return svc.obtener_prenda(cursor, id_prenda)


@router.delete(
    "/{id_prenda}",
    response_model=MensajeRespuesta,
    summary="Retirar una prenda del catálogo (borrado lógico)",
)
def inhabilitar_prenda(
    id_prenda: int,
    request: Request,
    cursor=Depends(get_db),
    administrador=Depends(solo_administrador),
):
    """Retira una prenda del catálogo cambiando su estado a 'Inactivo'.

    No se borra físicamente: sus variantes están referenciadas por
    `inventario`, `detalle_venta` y `detalle_reserva`. Un DELETE destruiría el
    historial comercial o fallaría por integridad referencial.

    Efecto inmediato: el catálogo público (CU14) solo publica prendas activas,
    de modo que deja de exhibirse al instante.

    Parámetros:
        id_prenda: prenda a retirar.
        request: petición HTTP, para la IP del cliente.
        cursor: cursor de PostgreSQL.
        administrador: administrador autenticado.

    Retorna:
        MensajeRespuesta: confirmación de la retirada.

    Errores:
        HTTP 404: la prenda no existe.
        HTTP 409: la prenda ya estaba inactiva.
    """
    prenda = svc.obtener_prenda(cursor, id_prenda, con_variantes=False)
    if prenda is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La prenda solicitada no existe",
        )

    if prenda["estado"] == "Inactivo":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La prenda ya se encuentra retirada del catálogo",
        )

    svc.inhabilitar_prenda(cursor, id_prenda)

    registrar_bitacora(
        cursor=cursor,
        accion=ACCION_INACTIVAR,
        tabla_afectada="prenda",
        registro_id=id_prenda,
        detalle=(
            f"Baja lógica de la prenda '{prenda['nombre']}' (SKU {prenda['sku']})."
        ),
        id_usuario=administrador["id_usuario"],
        ip_address=obtener_ip_cliente(request),
    )

    return MensajeRespuesta(
        mensaje=f"La prenda {prenda['nombre']} fue retirada del catálogo."
    )
