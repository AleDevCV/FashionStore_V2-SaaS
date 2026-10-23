"""
=============================================================================
FASHIONSTORE - ROUTER DEL CATÁLOGO PÚBLICO (CU14)
Sistemas de Información II - UAGRM
-----------------------------------------------------------------------------
Vitrina de consulta que alimentan el portal web (Angular) y la app móvil
(Flutter), más la comprobación de disponibilidad por sucursal física.

SEGURIDAD — ACCESO PÚBLICO A PROPÓSITO
  Ningún endpoint de este router exige token: un visitante debe poder explorar
  el catálogo antes de registrarse. Por eso todas las consultas filtran por
  estado 'Activo' y NO devuelven costos, márgenes ni datos internos: solo lo
  que puede verse en la tienda.
=============================================================================
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.database import get_db
from app.schemas.catalogo import (
    FiltrosDisponibles,
    PrendaCatalogo,
    RespuestaCatalogo,
    StockSucursal,
)
from app.services import catalogo_service as svc

router = APIRouter(prefix="/catalogo", tags=["Catálogo Público (CU14)"])

@router.get('/imagenes/{slug}/{name}')
def catalogue_image(slug:str,name:str):
    from fastapi.responses import FileResponse
    from app.services.local_images import file
    return FileResponse(file(slug,name),media_type='image/webp',headers={'Cache-Control':'public, max-age=86400'})


@router.get(
    "/filtros",
    response_model=FiltrosDisponibles,
    summary="Opciones disponibles para filtrar el catálogo",
)
def obtener_filtros(cursor=Depends(get_db)):
    """Devuelve categorías, tallas, colores, géneros y rango de precios.

    Se entregan en una sola llamada para que el frontend no dispare cinco
    peticiones al abrir el catálogo (RNF02).

    Solo se ofrecen opciones que realmente devuelven resultados: una talla sin
    prendas publicadas no aparece, porque un filtro que deja la cuadrícula
    vacía solo confunde al comprador.

    NOTA DE ENRUTADO: se declara antes que /{id_prenda} para que FastAPI no
    interprete la palabra "filtros" como un identificador numérico.

    Parámetros:
        cursor: cursor de PostgreSQL inyectado por `get_db`.

    Retorna:
        FiltrosDisponibles: opciones para la barra de filtros.
    """
    return svc.obtener_filtros_disponibles(cursor)


@router.get(
    "/",
    response_model=RespuestaCatalogo,
    summary="Consultar el catálogo con filtros y paginación",
)
def consultar_catalogo(
    busqueda: str | None = Query(default=None, description="Palabra clave"),
    id_categoria: int | None = Query(default=None),
    genero: str | None = Query(default=None, description="Dama, Caballero, Unisex o Nino"),
    id_talla: int | None = Query(default=None),
    id_color: int | None = Query(default=None),
    precio_min: float | None = Query(default=None, ge=0),
    precio_max: float | None = Query(default=None, ge=0),
    limite: int = Query(default=24, ge=1, le=100),
    desplazamiento: int = Query(default=0, ge=0),
    cursor=Depends(get_db),
):
    """Devuelve una página del catálogo activo aplicando los filtros del CU14.

    Los filtros de talla y color se resuelven con EXISTS sobre
    `variante_prenda`: así una prenda aparece si TIENE esa talla, sin que el
    cruce multiplique sus filas ni obligue a un DISTINCT posterior.

    El desglose de stock por sucursal NO viaja en el listado: se obtiene al
    abrir la ficha con GET /api/catalogo/{id_prenda}. Adjuntarlo aquí
    dispararía una consulta por variante de cada tarjeta de la cuadrícula.

    Parámetros:
        busqueda: palabra clave sobre nombre, descripción, SKU o marca.
        id_categoria, genero, id_talla, id_color: filtros exactos.
        precio_min / precio_max: rango de precio base.
        limite: tamaño de página (máximo 100).
        desplazamiento: cuántas prendas saltar.
        cursor: cursor de PostgreSQL.

    Retorna:
        RespuestaCatalogo: total de coincidencias y la página de prendas.

    Errores:
        HTTP 400: el precio mínimo es mayor que el máximo.
    """
    if (
        precio_min is not None
        and precio_max is not None
        and precio_min > precio_max
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El precio mínimo no puede ser mayor que el precio máximo",
        )

    return svc.consultar_catalogo(
        cursor,
        busqueda=busqueda,
        id_categoria=id_categoria,
        genero=genero,
        id_talla=id_talla,
        id_color=id_color,
        precio_min=precio_min,
        precio_max=precio_max,
        limite=limite,
        desplazamiento=desplazamiento,
        con_disponibilidad=False,
    )


@router.get(
    "/{id_prenda}",
    response_model=PrendaCatalogo,
    summary="Ficha de una prenda con disponibilidad por sucursal",
)
def obtener_ficha(id_prenda: int, cursor=Depends(get_db)):
    """Devuelve la ficha completa de una prenda con su stock por sucursal.

    Es la consulta del paso 10 del flujo principal del CU14: cruza `sucursal`,
    `inventario` y `variante_prenda` filtrando por stock > 0, de modo que solo
    se listan las tiendas donde el cliente encontrará la prenda de verdad.

    Una prenda retirada responde 404 igual que una inexistente: el catálogo
    público no debe revelar qué había en el catálogo interno.

    Parámetros:
        id_prenda: prenda solicitada.
        cursor: cursor de PostgreSQL.

    Retorna:
        PrendaCatalogo: ficha con variantes y disponibilidad desglosada.

    Errores:
        HTTP 404: la prenda no existe o no está publicada.
    """
    prenda = svc.obtener_ficha_publica(cursor, id_prenda)
    if prenda is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La prenda solicitada no está disponible en el catálogo",
        )
    return prenda


@router.get(
    "/variantes/{id_variante_prenda}/disponibilidad",
    response_model=list[StockSucursal],
    summary="Disponibilidad de una variante por sucursal",
)
def consultar_disponibilidad(id_variante_prenda: int, cursor=Depends(get_db)):
    """Devuelve en qué sucursales hay stock de una combinación talla/color.

    Corresponde al paso 9 del CU14: el cliente ya eligió talla y color y quiere
    saber a qué tienda ir a probárselo.

    Parámetros:
        id_variante_prenda: variante consultada.
        cursor: cursor de PostgreSQL.

    Retorna:
        list[StockSucursal]: sucursales con existencias, su ciudad, su
                             dirección y las unidades disponibles. La lista
                             vacía significa que no hay stock en ninguna tienda.
    """
    return svc.consultar_disponibilidad(cursor, id_variante_prenda)
