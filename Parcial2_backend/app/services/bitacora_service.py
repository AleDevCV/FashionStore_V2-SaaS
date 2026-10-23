"""
=============================================================================
FASHIONSTORE - SERVICIO DE AUDITORÍA / BITÁCORA (CU25)
Sistemas de Información II - UAGRM
-----------------------------------------------------------------------------
Centraliza la escritura en la tabla `bitacora`, que deja rastro de toda
operación sensible del sistema: inicios de sesión, altas, modificaciones e
inactivaciones de usuarios.

Se aísla en su propio módulo para que cualquier caso de uso futuro (compras,
ventas, inventario) audite con la misma función y el mismo formato.
=============================================================================
"""

from typing import Any

from fastapi import Request

# Acciones normalizadas. Usar constantes en lugar de cadenas sueltas evita que
# la bitácora acabe con variantes como "login", "LOGIN" y "Login" que romperían
# los filtros de los reportes de auditoría del CU25.
ACCION_LOGIN_EXITOSO = "LOGIN_EXITOSO"
ACCION_LOGIN_FALLIDO = "LOGIN_FALLIDO"
ACCION_INSERT = "INSERT"
ACCION_UPDATE = "UPDATE"
ACCION_INACTIVAR = "INACTIVAR"
ACCION_DELETE = "DELETE"
ACCION_SOLICITUD_RECUPERACION = "SOLICITUD_RECUPERACION_PASSWORD"
ACCION_RESTABLECER_PASSWORD_EXITOSO = "RESTABLECER_PASSWORD_EXITOSO"
ACCION_IA_RECOMENDACION = "IA_RECOMENDACION"
ACCION_IA_ANALITICA_VOZ = "IA_ANALITICA_VOZ"
ACCION_IA_TRYON = "IA_TRYON"



def obtener_ip_cliente(request: Request) -> str:
    """Determina la dirección IP real del cliente que hizo la petición.

    Dentro de Docker, `request.client.host` devuelve la IP de la red interna
    del contenedor, no la del usuario. Cuando la API se despliegue en la nube
    detrás de un proxy inverso (Nginx, Traefik o el balanceador del proveedor),
    la IP verdadera llega en la cabecera `X-Forwarded-For`, por lo que esta se
    consulta primero.

    Parámetros:
        request: objeto Request de FastAPI con los datos de la conexión.

    Retorna:
        str: dirección IP del cliente, o "desconocida" si no puede determinarse.
             Se recorta a 45 caracteres, que es el ancho de la columna
             `bitacora.ip_address` (suficiente para una IPv6 completa).
    """
    reenviada = request.headers.get("x-forwarded-for")
    if reenviada:
        # X-Forwarded-For puede traer una cadena de proxies: "cliente, proxy1,
        # proxy2". El primer elemento es el cliente original.
        return reenviada.split(",")[0].strip()[:45]

    if request.client and request.client.host:
        return request.client.host[:45]

    return "desconocida"


def registrar_bitacora(
    cursor: Any,
    accion: str,
    tabla_afectada: str,
    detalle: str,
    id_usuario: int | None = None,
    registro_id: int | None = None,
    ip_address: str | None = None,
    confirmar: bool = False,
) -> None:
    """Inserta un registro de auditoría en la tabla `bitacora`.

    Parámetros:
        cursor: cursor de PostgreSQL inyectado por la dependencia `get_db`.
        accion: tipo de operación; usar las constantes ACCION_* de este módulo.
        tabla_afectada: nombre de la tabla sobre la que se operó.
        detalle: texto descriptivo legible del evento para el auditor.
        id_usuario: autor de la operación. Queda NULL si no se pudo identificar
                    (por ejemplo, un intento de login con un correo inexistente).
        registro_id: clave primaria de la fila afectada, si aplica.
        ip_address: IP de origen, obtenida con `obtener_ip_cliente`.
        confirmar: si es True, hace COMMIT inmediato de la transacción.

    Retorna:
        None

    SOBRE EL PARÁMETRO `confirmar`:
        `get_db` abre una transacción por petición y hace ROLLBACK automático si
        el endpoint lanza una excepción. Eso es correcto para el CRUD, pero
        destruiría el rastro de los INTENTOS FALLIDOS de login, que terminan
        precisamente lanzando un HTTP 401.
        En esos casos se pasa `confirmar=True` para consolidar el registro antes
        de que se propague la excepción. Para operaciones exitosas debe dejarse
        en False, de modo que la auditoría viaje en la MISMA transacción que el
        cambio auditado: si el INSERT del usuario se revierte, su registro de
        bitácora también, y nunca queda constancia de algo que no ocurrió.
    """
    cursor.execute(
        """
        INSERT INTO bitacora
            (id_usuario, accion, tabla_afectada, registro_id, detalle, ip_address)
        VALUES (%s, %s, %s, %s, %s, %s);
        """,
        (id_usuario, accion, tabla_afectada, registro_id, detalle, ip_address),
    )

    if confirmar:
        # `cursor.connection` es la conexión del pool asociada a este cursor.
        cursor.connection.commit()


def listar_bitacora(
    cursor: Any,
    pagina: int = 1,
    limite: int = 50,
    accion: str | None = None,
    tabla_afectada: str | None = None,
    busqueda: str | None = None,
) -> dict:
    """Consulta los eventos registrados en la bitácora de auditoría (CU25)

    con soporte de paginación y filtros de búsqueda para el Administrador.
    """
    offset = (max(pagina, 1) - 1) * limite
    filtros = []
    params: list[Any] = []

    if accion:
        filtros.append("b.accion = %s")
        params.append(accion)

    if tabla_afectada:
        filtros.append("b.tabla_afectada = %s")
        params.append(tabla_afectada)

    if busqueda:
        filtros.append(
            "(b.detalle ILIKE %s OR b.ip_address ILIKE %s OR u.nombre ILIKE %s OR u.correo ILIKE %s)"
        )
        termino = f"%{busqueda}%"
        params.extend([termino, termino, termino, termino])

    where_clause = f"WHERE {' AND '.join(filtros)}" if filtros else ""

    # Conteo total
    query_count = f"""
        SELECT COUNT(*) AS total
        FROM bitacora b
        LEFT JOIN usuario u ON b.id_usuario = u.id_usuario
        {where_clause};
    """
    cursor.execute(query_count, params)
    fila_count = cursor.fetchone()
    total = int(fila_count["total"] or 0)

    # Consulta de registros paginados
    query_items = f"""
        SELECT 
            b.id_bitacora,
            b.id_usuario,
            TRIM(CONCAT(u.nombre, ' ', COALESCE(u.apellido, ''))) AS nombre_usuario,
            u.correo AS correo_usuario,
            r.nombre AS rol_usuario,
            b.accion,
            b.tabla_afectada,
            b.registro_id,
            b.detalle,
            b.ip_address,
            b.fecha
        FROM bitacora b
        LEFT JOIN usuario u ON b.id_usuario = u.id_usuario
        LEFT JOIN rol r ON u.id_role = r.id_rol
        {where_clause}
        ORDER BY b.id_bitacora DESC
        LIMIT %s OFFSET %s;
    """
    params_items = list(params) + [limite, offset]
    cursor.execute(query_items, params_items)
    items = cursor.fetchall()

    return {
        "total": total,
        "pagina": pagina,
        "limite": limite,
        "items": items,
    }
