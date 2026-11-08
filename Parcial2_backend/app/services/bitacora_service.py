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

from datetime import date
from typing import Any
from uuid import UUID

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
    id_sucursal: int | None = None,
    operation_id: UUID | None = None,
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
            (id_usuario, accion, tabla_afectada, registro_id, detalle, ip_address, id_sucursal, operation_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
        """,
        (id_usuario, accion, tabla_afectada, registro_id, detalle, ip_address,
         id_sucursal, str(operation_id) if operation_id else None),
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
    fecha_inicio: date | None = None,
    fecha_fin: date | None = None,
    usuario_id: int | None = None,
    operation_id: UUID | None = None,
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
            "(b.detalle ILIKE %s OR b.ip_address ILIKE %s OR b.nombre_usuario ILIKE %s OR b.correo_usuario ILIKE %s)"
        )
        termino = f"%{busqueda}%"
        params.extend([termino, termino, termino, termino])
    if fecha_inicio:
        filtros.append('b.fecha >= %s::date')
        params.append(fecha_inicio)
    if fecha_fin:
        filtros.append('b.fecha < %s::date + 1')
        params.append(fecha_fin)
    if usuario_id:
        filtros.append('b.id_usuario = %s')
        params.append(usuario_id)
    if operation_id:
        filtros.append('b.operation_id = %s::uuid')
        params.append(str(operation_id))

    where_clause = f"WHERE {' AND '.join(filtros)}" if filtros else ""

    events = """
        WITH business AS (
            SELECT b.id_bitacora,b.id_usuario,
                   NULLIF(TRIM(CONCAT(u.nombre,' ',u.apellido)),'') AS nombre_usuario,
                   u.correo AS correo_usuario,r.nombre AS rol_usuario,
                   b.accion,b.tabla_afectada,b.registro_id,COALESCE(b.detalle,'') AS detalle,b.ip_address,
                   b.fecha AT TIME ZONE current_setting('TimeZone') AS fecha,
                   COALESCE(b.id_sucursal,CASE b.tabla_afectada
                       WHEN 'sucursal' THEN b.registro_id
                       WHEN 'venta' THEN (SELECT v.id_sucursal FROM venta v WHERE v.id_venta=b.registro_id)
                       WHEN 'compra' THEN (SELECT c.id_sucursal FROM compra c WHERE c.id_compra=b.registro_id)
                       WHEN 'movimiento_inventario' THEN (SELECT m.id_sucursal FROM movimiento_inventario m WHERE m.id_movimiento=b.registro_id)
                       WHEN 'cambio' THEN (SELECT c.id_sucursal FROM cambio c WHERE c.id_cambio=b.registro_id)
                   END) AS id_sucursal,
                   COALESCE(b.operation_id,CASE WHEN b.tabla_afectada IN ('operacion_sync','traspaso_inventario','reporte_resultado')
                     THEN substring(b.detalle FROM '(?i)[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}')::uuid
                   END) AS operation_id
            FROM bitacora b
            LEFT JOIN usuario u ON b.id_usuario=u.id_usuario
            LEFT JOIN rol r ON u.id_role=r.id_rol
        ), events AS (
            SELECT * FROM business b WHERE current_setting('app.role',true)='Administrador'
                OR EXISTS (SELECT 1 FROM usuario_sucursal us WHERE us.id_sucursal=b.id_sucursal
                           AND us.id_usuario=NULLIF(current_setting('app.user_id',true),'')::integer)
            UNION ALL
            SELECT -event_id,local_user,account_name,account_email,account_role,event_action,
                   'auditoria_identidad',NULL,event_action,NULL,event_date,NULL,NULL
            FROM audit_identity_events()
        )
    """
    cursor.execute(f"{events} SELECT COUNT(*) AS total FROM events b {where_clause}", params)
    fila_count = cursor.fetchone()
    total = int(fila_count["total"] or 0)

    query_items = f"""
        {events}
        SELECT b.id_bitacora,b.id_usuario,b.nombre_usuario,b.correo_usuario,b.rol_usuario,b.accion,
               b.tabla_afectada,b.registro_id,b.detalle,b.ip_address,b.fecha,b.id_sucursal,
               b.operation_id::text AS operation_id
        FROM events b
        {where_clause}
        ORDER BY b.fecha DESC,b.id_bitacora DESC
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
