"""
=============================================================================
FASHIONSTORE - SERVICIO DE PROVEEDORES (CU12)
Sistemas de Información II - UAGRM
-----------------------------------------------------------------------------
Lógica de negocio para la gestión de proveedores: altas, bajas, modificaciones
y consultas con validación de unicidad de NIT, verificación de compras asociadas
para borrado protegido y auditoría forense inmutable en la bitácora.
=============================================================================
"""

from typing import Any
from fastapi import HTTPException, status
from psycopg2 import errors as pg_errors

from app.schemas.proveedor import ProveedorActualizar, ProveedorCrear
from app.services.bitacora_service import (
    ACCION_DELETE,
    ACCION_INSERT,
    ACCION_UPDATE,
    registrar_bitacora,
)


def listar_proveedores(
    cursor: Any,
    busqueda: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[dict]:
    """Lista proveedores con paginación y búsqueda opcional por NIT o Razón Social.

    Parámetros:
        cursor: cursor activo de PostgreSQL inyectado por get_db.
        busqueda: término de búsqueda por NIT o razón social (ILIKE).
        skip: desplazamiento para paginación.
        limit: cantidad máxima de registros a retornar.

    Retorna:
        list[dict]: lista de registros de proveedores.
    """
    if busqueda and busqueda.strip():
        patron = f"%{busqueda.strip()}%"
        cursor.execute(
            """
            SELECT id_proveedor, nit, razon_social, contacto, telefono, correo, direccion, created_at
            FROM proveedor
            WHERE nit ILIKE %s OR razon_social ILIKE %s
            ORDER BY id_proveedor DESC
            LIMIT %s OFFSET %s;
            """,
            (patron, patron, limit, skip),
        )
    else:
        cursor.execute(
            """
            SELECT id_proveedor, nit, razon_social, contacto, telefono, correo, direccion, created_at
            FROM proveedor
            ORDER BY id_proveedor DESC
            LIMIT %s OFFSET %s;
            """,
            (limit, skip),
        )
    return cursor.fetchall()


def obtener_proveedor_por_id(cursor: Any, id_proveedor: int) -> dict | None:
    """Busca un proveedor por su identificador primario.

    Parámetros:
        cursor: cursor activo de PostgreSQL.
        id_proveedor: ID primario del proveedor.

    Retorna:
        dict | None: registro del proveedor o None si no existe.
    """
    cursor.execute(
        """
        SELECT id_proveedor, nit, razon_social, contacto, telefono, correo, direccion, created_at
        FROM proveedor
        WHERE id_proveedor = %s;
        """,
        (id_proveedor,),
    )
    return cursor.fetchone()


def obtener_proveedor_por_nit(cursor: Any, nit: str) -> dict | None:
    """Busca un proveedor por su NIT.

    Parámetros:
        cursor: cursor activo de PostgreSQL.
        nit: NIT exacto a verificar.

    Retorna:
        dict | None: registro del proveedor o None si no existe.
    """
    cursor.execute(
        """
        SELECT id_proveedor, nit, razon_social, contacto, telefono, correo, direccion, created_at
        FROM proveedor
        WHERE nit = %s;
        """,
        (nit,),
    )
    return cursor.fetchone()


def crear_proveedor(
    cursor: Any,
    datos: ProveedorCrear,
    usuario: dict,
    ip_address: str,
) -> dict:
    """Registra un nuevo proveedor validando unicidad de NIT y auditando la operación.

    Parámetros:
        cursor: cursor activo de PostgreSQL.
        datos: datos validados del proveedor a crear.
        usuario: sesión activa del usuario autenticado.
        ip_address: IP del cliente que originó la petición.

    Retorna:
        dict: datos completos del proveedor registrado.

    Errores:
        HTTP 400: NIT duplicado.
    """
    # Verificación preventiva de duplicidad de NIT
    existente = obtener_proveedor_por_nit(cursor, datos.nit.strip())
    if existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El número de NIT ya se encuentra registrado para otro proveedor",
        )

    try:
        cursor.execute(
            """
            INSERT INTO proveedor (nit, razon_social, contacto, telefono, correo, direccion)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id_proveedor, nit, razon_social, contacto, telefono, correo, direccion, created_at;
            """,
            (
                datos.nit.strip(),
                datos.razon_social.strip(),
                datos.contacto.strip() if datos.contacto else None,
                datos.telefono.strip() if datos.telefono else None,
                datos.correo.strip() if datos.correo else None,
                datos.direccion.strip() if datos.direccion else None,
            ),
        )
        proveedor = cursor.fetchone()
    except pg_errors.UniqueViolation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El número de NIT ya se encuentra registrado para otro proveedor",
        )

    # Auditoría forense inmutable en bitácora
    registrar_bitacora(
        cursor=cursor,
        accion=ACCION_INSERT,
        tabla_afectada="proveedor",
        registro_id=proveedor["id_proveedor"],
        detalle=f"Alta del proveedor '{proveedor['razon_social']}' (NIT {proveedor['nit']}).",
        id_usuario=usuario.get("id_usuario"),
        ip_address=ip_address,
    )

    return proveedor


def actualizar_proveedor(
    cursor: Any,
    id_proveedor: int,
    datos: ProveedorActualizar,
    usuario: dict,
    ip_address: str,
) -> dict:
    """Actualiza datos de un proveedor existente comprobando unicidad de NIT y auditando.

    Parámetros:
        cursor: cursor activo de PostgreSQL.
        id_proveedor: ID primario del proveedor a editar.
        datos: datos a actualizar (parciales o totales).
        usuario: sesión activa del usuario autenticado.
        ip_address: IP del cliente que originó la petición.

    Retorna:
        dict: datos completos del proveedor actualizado.

    Errores:
        HTTP 404: el proveedor no existe.
        HTTP 400: NIT duplicado en otro proveedor.
    """
    proveedor = obtener_proveedor_por_id(cursor, id_proveedor)
    if not proveedor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El proveedor solicitado no existe",
        )

    cambios = datos.model_dump(exclude_unset=True)
    if not cambios:
        return proveedor

    # Si se intenta cambiar el NIT, comprobar que no colisione con otro proveedor
    if "nit" in cambios and cambios["nit"]:
        nuevo_nit = cambios["nit"].strip()
        cursor.execute(
            """
            SELECT id_proveedor FROM proveedor
            WHERE nit = %s AND id_proveedor != %s;
            """,
            (nuevo_nit, id_proveedor),
        )
        if cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El número de NIT ya se encuentra registrado para otro proveedor",
            )
        cambios["nit"] = nuevo_nit

    # Limpiar cadenas vacías o con espacios en blanco
    for campo in ["razon_social", "contacto", "telefono", "correo", "direccion"]:
        if campo in cambios and isinstance(cambios[campo], str):
            cambios[campo] = cambios[campo].strip()

    # Construir consulta dinámica segura
    columnas = []
    valores = []
    for k, v in cambios.items():
        columnas.append(f"{k} = %s")
        valores.append(v)
    valores.append(id_proveedor)

    sql = f"""
        UPDATE proveedor
        SET {", ".join(columnas)}
        WHERE id_proveedor = %s
        RETURNING id_proveedor, nit, razon_social, contacto, telefono, correo, direccion, created_at;
    """

    try:
        cursor.execute(sql, tuple(valores))
        actualizado = cursor.fetchone()
    except pg_errors.UniqueViolation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El número de NIT ya se encuentra registrado para otro proveedor",
        )

    # Registro en bitácora
    registrar_bitacora(
        cursor=cursor,
        accion=ACCION_UPDATE,
        tabla_afectada="proveedor",
        registro_id=id_proveedor,
        detalle=f"Actualización de datos del proveedor '{actualizado['razon_social']}' (NIT {actualizado['nit']}).",
        id_usuario=usuario.get("id_usuario"),
        ip_address=ip_address,
    )

    return actualizado


def eliminar_proveedor(
    cursor: Any,
    id_proveedor: int,
    usuario: dict,
    ip_address: str,
) -> dict:
    """Elimina físicamente un proveedor si no tiene historial de compras vinculadas.

    Parámetros:
        cursor: cursor activo de PostgreSQL.
        id_proveedor: ID primario del proveedor a eliminar.
        usuario: sesión activa del usuario autenticado.
        ip_address: IP del cliente que originó la petición.

    Retorna:
        dict: mensaje de confirmación de eliminación.

    Errores:
        HTTP 404: el proveedor no existe.
        HTTP 409: el proveedor tiene compras asociadas (borrado protegido).
    """
    proveedor = obtener_proveedor_por_id(cursor, id_proveedor)
    if not proveedor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El proveedor solicitado no existe",
        )

    # Protección de integridad referencial: validar si existen compras registradas
    cursor.execute(
        "SELECT 1 FROM compra WHERE id_proveedor = %s LIMIT 1;",
        (id_proveedor,),
    )
    if cursor.fetchone():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No es posible eliminar el proveedor porque posee historial de compras registradas",
        )

    cursor.execute("DELETE FROM proveedor WHERE id_proveedor = %s;", (id_proveedor,))

    # Registrar en bitácora
    registrar_bitacora(
        cursor=cursor,
        accion=ACCION_DELETE,
        tabla_afectada="proveedor",
        registro_id=id_proveedor,
        detalle=f"Eliminación física del proveedor '{proveedor['razon_social']}' (NIT {proveedor['nit']}).",
        id_usuario=usuario.get("id_usuario"),
        ip_address=ip_address,
    )

    return {"mensaje": "Proveedor eliminado exitosamente"}
