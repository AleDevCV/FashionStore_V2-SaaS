"""
=============================================================================
FASHIONSTORE - SERVICIO DE TEMPORADAS Y COLECCIONES (CU09)
Sistemas de Información II - UAGRM
-----------------------------------------------------------------------------
Capa de servicio para la gestión de temporadas y colecciones comerciales:
consultas SQL parametrizadas nativas (%s), validación de unicidad de nombre,
coherencia de rangos de fechas, y registro de auditoría inmutable en bitácora (CU25).
=============================================================================
"""

from typing import Any
from fastapi import HTTPException, status

from app.schemas.temporada import TemporadaActualizar, TemporadaCrear
from app.services.bitacora_service import (
    ACCION_DELETE,
    ACCION_INSERT,
    ACCION_UPDATE,
    registrar_bitacora,
)


def existe_nombre_temporada(cursor, nombre: str, excluir_id: int | None = None) -> bool:
    """Verifica si ya existe una temporada registrada con el mismo nombre.

    La comprobación es insensible a mayúsculas y espacios marginales.
    """
    if excluir_id is None:
        cursor.execute(
            "SELECT 1 FROM temporada WHERE LOWER(TRIM(nombre)) = LOWER(TRIM(%s));",
            (nombre,),
        )
    else:
        cursor.execute(
            """
            SELECT 1 FROM temporada 
            WHERE LOWER(TRIM(nombre)) = LOWER(TRIM(%s)) 
              AND id_temporada <> %s;
            """,
            (nombre, excluir_id),
        )
    return cursor.fetchone() is not None


def listar_temporadas(
    cursor,
    busqueda: str | None = None,
    estado: bool | None = None,
    vigencia: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Obtiene el listado de temporadas con filtros de búsqueda, estado y vigencia.

    Incluye la cantidad consolidada de prendas asignadas mediante un LEFT JOIN.
    """
    condiciones: list[str] = []
    valores: list[Any] = []

    if busqueda:
        condiciones.append("(t.nombre ILIKE %s OR t.descripcion ILIKE %s)")
        patron = f"%{busqueda.strip()}%"
        valores.extend([patron, patron])

    if estado is not None:
        condiciones.append("t.estado = %s")
        valores.append(estado)

    if vigencia:
        v_clean = vigencia.strip().capitalize()
        if v_clean == "Activa":
            condiciones.append("CURRENT_DATE >= t.fecha_inicio AND CURRENT_DATE <= t.fecha_fin")
        elif v_clean == "Proxima":
            condiciones.append("CURRENT_DATE < t.fecha_inicio")
        elif v_clean == "Pasada":
            condiciones.append("CURRENT_DATE > t.fecha_fin")

    sql = """
        SELECT 
            t.id_temporada,
            t.nombre,
            t.descripcion,
            t.fecha_inicio,
            t.fecha_fin,
            t.estado,
            t.created_at,
            COUNT(p.id_prenda)::int AS total_prendas
        FROM temporada t
        LEFT JOIN prenda p ON p.id_temporada = t.id_temporada
    """

    if condiciones:
        sql += " WHERE " + " AND ".join(condiciones)

    sql += """
        GROUP BY t.id_temporada
        ORDER BY t.fecha_inicio DESC, t.id_temporada DESC
        LIMIT %s OFFSET %s;
    """
    valores.extend([limit, skip])

    cursor.execute(sql, tuple(valores))
    return [dict(fila) for fila in cursor.fetchall()]


def obtener_temporada_por_id(cursor, id_temporada: int) -> dict[str, Any] | None:
    """Devuelve los datos de una temporada específica y el conteo de sus prendas."""
    cursor.execute(
        """
        SELECT 
            t.id_temporada,
            t.nombre,
            t.descripcion,
            t.fecha_inicio,
            t.fecha_fin,
            t.estado,
            t.created_at,
            COUNT(p.id_prenda)::int AS total_prendas
        FROM temporada t
        LEFT JOIN prenda p ON p.id_temporada = t.id_temporada
        WHERE t.id_temporada = %s
        GROUP BY t.id_temporada;
        """,
        (id_temporada,),
    )
    fila = cursor.fetchone()
    return dict(fila) if fila else None


def crear_temporada(
    cursor,
    datos: TemporadaCrear,
    usuario: dict[str, Any],
    ip_address: str,
) -> dict[str, Any]:
    """Crea una nueva temporada asegurando unicidad de nombre y coherencia de fechas.

    Registra el evento de forma atómica e inmutable en la bitácora del sistema (CU25).
    """
    if datos.fecha_inicio > datos.fecha_fin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La fecha de inicio no puede ser posterior a la fecha de fin",
        )

    if existe_nombre_temporada(cursor, datos.nombre):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe una temporada registrada con ese nombre",
        )

    cursor.execute(
        """
        INSERT INTO temporada (nombre, descripcion, fecha_inicio, fecha_fin, estado)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id_temporada, nombre, descripcion, fecha_inicio, fecha_fin, estado, created_at;
        """,
        (
            datos.nombre.strip(),
            datos.descripcion.strip() if datos.descripcion else None,
            datos.fecha_inicio,
            datos.fecha_fin,
            datos.estado,
        ),
    )
    nueva = dict(cursor.fetchone())
    nueva["total_prendas"] = 0

    registrar_bitacora(
        cursor=cursor,
        accion=ACCION_INSERT,
        tabla_afectada="temporada",
        registro_id=nueva["id_temporada"],
        detalle=(
            f"Alta de la temporada '{nueva['nombre']}' "
            f"({nueva['fecha_inicio']} a {nueva['fecha_fin']})."
        ),
        id_usuario=usuario.get("id_usuario"),
        ip_address=ip_address,
    )

    return nueva


def actualizar_temporada(
    cursor,
    id_temporada: int,
    datos: TemporadaActualizar,
    usuario: dict[str, Any],
    ip_address: str,
) -> dict[str, Any]:
    """Actualiza una temporada validando que no colisione su nombre ni su rango de fechas."""
    actual = obtener_temporada_por_id(cursor, id_temporada)
    if not actual:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La temporada solicitada no existe",
        )

    cambios = datos.model_dump(exclude_unset=True)
    if "activo" in cambios and "estado" not in cambios:
        cambios["estado"] = cambios["activo"]
    cambios.pop("activo", None)

    if not cambios:
        return actual

    # 1. Validar nombre único
    if "nombre" in cambios and cambios["nombre"]:
        nuevo_nombre = cambios["nombre"].strip()
        if existe_nombre_temporada(cursor, nuevo_nombre, excluir_id=id_temporada):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe una temporada registrada con ese nombre",
            )
        cambios["nombre"] = nuevo_nombre

    # 2. Validar coherencia de fechas combinadas (nuevas o preexistentes)
    nueva_inicio = cambios.get("fecha_inicio", actual["fecha_inicio"])
    nueva_fin = cambios.get("fecha_fin", actual["fecha_fin"])
    if nueva_inicio > nueva_fin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La fecha de inicio no puede ser posterior a la fecha de fin",
        )

    # 3. Construir query UPDATE dinámica
    set_clauses: list[str] = []
    valores: list[Any] = []
    for col, val in cambios.items():
        set_clauses.append(f"{col} = %s")
        valores.append(val)

    valores.append(id_temporada)
    sql = f"UPDATE temporada SET {', '.join(set_clauses)} WHERE id_temporada = %s;"
    cursor.execute(sql, tuple(valores))

    # 4. Registrar en bitácora
    resumen = ", ".join(f"{k}={v}" for k, v in cambios.items())
    registrar_bitacora(
        cursor=cursor,
        accion=ACCION_UPDATE,
        tabla_afectada="temporada",
        registro_id=id_temporada,
        detalle=f"Modificación de la temporada ID {id_temporada} ('{actual['nombre']}'). Campos: {resumen}.",
        id_usuario=usuario.get("id_usuario"),
        ip_address=ip_address,
    )

    return obtener_temporada_por_id(cursor, id_temporada)


def eliminar_temporada(
    cursor,
    id_temporada: int,
    usuario: dict[str, Any],
    ip_address: str,
) -> dict[str, str]:
    """Elimina una temporada del sistema.

    Las prendas asociadas desvinculan su temporada a NULL de forma automática
    gracias a la restricción ON DELETE SET NULL.
    """
    actual = obtener_temporada_por_id(cursor, id_temporada)
    if not actual:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La temporada solicitada no existe",
        )

    cursor.execute("DELETE FROM temporada WHERE id_temporada = %s;", (id_temporada,))

    registrar_bitacora(
        cursor=cursor,
        accion=ACCION_DELETE,
        tabla_afectada="temporada",
        registro_id=id_temporada,
        detalle=f"Eliminación de la temporada '{actual['nombre']}' (ID {id_temporada}).",
        id_usuario=usuario.get("id_usuario"),
        ip_address=ip_address,
    )

    return {"mensaje": "Temporada eliminada correctamente"}
