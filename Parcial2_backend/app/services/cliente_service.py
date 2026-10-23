"""
=============================================================================
FASHIONSTORE - SERVICIO DE FICHAS DE CLIENTES (CU05)
Sistemas de Información II - UAGRM
-----------------------------------------------------------------------------
Todo el SQL del módulo de clientes maestros.
=============================================================================
"""

from typing import Any

# Proyección compartida por las lecturas de cliente.
_SELECT_CLIENTE = """
    SELECT  id_cliente,
            ci,
            nombre_completo,
            telefono,
            correo,
            direccion_envio,
            estado,
            created_at
    FROM cliente
"""


def listar_clientes(
    cursor,
    busqueda: str | None = None,
    estado: str | None = None,
) -> list[dict[str, Any]]:
    """Devuelve las fichas de cliente, con buscador y filtro de estado.

    El buscador es insensible a mayúsculas y actúa sobre la cédula y el nombre
    completo, que son los dos datos con los que el cajero identifica a un
    comprador en el mostrador.

    Parámetros:
        cursor: cursor de PostgreSQL.
        busqueda: texto libre a buscar en `ci` o `nombre_completo`.
        estado: 'Activo' o 'Inactivo' para acotar el listado.

    Retorna:
        list[dict]: clientes ordenados por nombre.
    """
    condiciones: list[str] = []
    valores: list[Any] = []

    if busqueda:
        # ILIKE es la comparación insensible a mayúsculas de PostgreSQL.
        condiciones.append("(ci ILIKE %s OR nombre_completo ILIKE %s)")
        patron = f"%{busqueda}%"
        valores.extend([patron, patron])

    if estado:
        condiciones.append("estado = %s")
        valores.append(estado)

    sql = _SELECT_CLIENTE
    if condiciones:
        sql += " WHERE " + " AND ".join(condiciones)
    sql += " ORDER BY nombre_completo;"

    cursor.execute(sql, tuple(valores))
    return [dict(f) for f in cursor.fetchall()]


def obtener_cliente(cursor, id_cliente: int) -> dict[str, Any] | None:
    """Recupera una ficha de cliente por su identificador.

    Parámetros:
        cursor: cursor de PostgreSQL.
        id_cliente: clave primaria buscada.

    Retorna:
        dict | None: la ficha, o None si no existe.
    """
    cursor.execute(_SELECT_CLIENTE + " WHERE id_cliente = %s;", (id_cliente,))
    fila = cursor.fetchone()
    return dict(fila) if fila else None


def obtener_cliente_por_correo(cursor, correo: str) -> dict[str, Any] | None:
    """Recupera la ficha vinculada al correo de una cuenta de cliente.

    La base actual no posee una clave foránea entre ``usuario`` y ``cliente``.
    El auto-registro crea ambos registros con el mismo correo, por lo que esta
    es la relación existente que permite resolver la ficha sin aceptar un
    ``id_cliente`` proporcionado por el navegador.
    """
    cursor.execute(
        _SELECT_CLIENTE + " WHERE LOWER(correo) = LOWER(%s);",
        (correo,),
    )
    fila = cursor.fetchone()
    return dict(fila) if fila else None


def existe_ci(cursor, ci: str, excluir_id: int | None = None) -> bool:
    """Comprueba si una cédula ya está asignada a otro cliente.

    Implementa la excepción A del CU05. El parámetro `excluir_id` permite
    reutilizar la función al editar: un cliente puede conservar su propia
    cédula sin que se considere duplicada.

    Parámetros:
        cursor: cursor de PostgreSQL.
        ci: cédula a comprobar.
        excluir_id: identificador del cliente que se está editando.

    Retorna:
        bool: True si la cédula pertenece a otro cliente.
    """
    if excluir_id is None:
        cursor.execute("SELECT 1 FROM cliente WHERE ci = %s;", (ci,))
    else:
        cursor.execute(
            "SELECT 1 FROM cliente WHERE ci = %s AND id_cliente <> %s;",
            (ci, excluir_id),
        )
    return cursor.fetchone() is not None


def existe_correo(cursor, correo: str, excluir_id: int | None = None) -> bool:
    """Comprueba si un correo ya está registrado por otro cliente.

    La columna `correo` es UNIQUE en la tabla, así que conviene validarla antes
    de intentar el INSERT.

    Parámetros:
        cursor: cursor de PostgreSQL.
        correo: correo a comprobar.
        excluir_id: identificador del cliente que se está editando.

    Retorna:
        bool: True si el correo pertenece a otro cliente.
    """
    if excluir_id is None:
        cursor.execute("SELECT 1 FROM cliente WHERE correo = %s;", (correo,))
    else:
        cursor.execute(
            "SELECT 1 FROM cliente WHERE correo = %s AND id_cliente <> %s;",
            (correo, excluir_id),
        )
    return cursor.fetchone() is not None


def crear_cliente(cursor, datos: dict[str, Any]) -> int:
    """Inserta una ficha de cliente y devuelve su identificador.

    Parámetros:
        cursor: cursor de PostgreSQL.
        datos: ci, nombre_completo, telefono, correo y direccion_envio.

    Retorna:
        int: id_cliente de la fila creada.
    """
    cursor.execute(
        """
        INSERT INTO cliente (ci, nombre_completo, telefono, correo, direccion_envio)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id_cliente;
        """,
        (
            datos["ci"],
            datos["nombre_completo"],
            datos.get("telefono"),
            datos.get("correo"),
            datos.get("direccion_envio"),
        ),
    )
    return cursor.fetchone()["id_cliente"]


def actualizar_cliente(cursor, id_cliente: int, cambios: dict[str, Any]) -> None:
    """Aplica una actualización parcial sobre una ficha de cliente.

    Parámetros:
        cursor: cursor de PostgreSQL.
        id_cliente: ficha a modificar.
        cambios: columnas a actualizar.

    Retorna:
        None
    """
    columnas = [f"{col} = %s" for col in cambios]
    valores = list(cambios.values())

    columnas.append("updated_at = CURRENT_TIMESTAMP")
    valores.append(id_cliente)

    cursor.execute(
        f"UPDATE cliente SET {', '.join(columnas)} WHERE id_cliente = %s;",
        tuple(valores),
    )


def inhabilitar_cliente(cursor, id_cliente: int) -> None:
    """Da de baja lógica a un cliente cambiando su estado a 'Inactivo'.

    NO se ejecuta un DELETE físico: la tabla `cliente` está referenciada por
    `venta` y `reserva`, y borrarla rompería el historial comercial.

    Parámetros:
        cursor: cursor de PostgreSQL.
        id_cliente: ficha a inhabilitar.

    Retorna:
        None
    """
    cursor.execute(
        """
        UPDATE cliente
        SET estado = 'Inactivo', updated_at = CURRENT_TIMESTAMP
        WHERE id_cliente = %s;
        """,
        (id_cliente,),
    )


def existe_correo_usuario(
    cursor,
    correo: str,
    excluir_id_usuario: int | None = None,
) -> bool:
    """Comprueba si un correo ya está registrado en otra cuenta de usuario."""
    if excluir_id_usuario is None:
        cursor.execute(
            "SELECT 1 FROM usuario WHERE LOWER(correo) = LOWER(%s);",
            (correo,),
        )
    else:
        cursor.execute(
            """
            SELECT 1
            FROM usuario
            WHERE LOWER(correo) = LOWER(%s) AND id_usuario <> %s;
            """,
            (correo, excluir_id_usuario),
        )
    return cursor.fetchone() is not None


def sincronizar_contacto_usuario(
    cursor,
    id_usuario: int,
    cambios_cliente: dict[str, Any],
) -> None:
    """Mantiene el correo/teléfono de la cuenta alineados con su propia ficha.

    Solo se usa en autogestión, una vez que el backend ya resolvió la
    propiedad. Mantener el correo alineado es imprescindible porque, ante la
    ausencia de una FK, ese dato es la vinculación disponible entre tablas.
    """
    campos_sincronizables = {
        campo: cambios_cliente[campo]
        for campo in ("correo", "telefono")
        if campo in cambios_cliente
    }
    if not campos_sincronizables:
        return

    columnas = [f"{campo} = %s" for campo in campos_sincronizables]
    valores = list(campos_sincronizables.values())
    columnas.append("updated_at = CURRENT_TIMESTAMP")
    valores.append(id_usuario)
    cursor.execute(
        f"UPDATE usuario SET {', '.join(columnas)} WHERE id_usuario = %s;",
        tuple(valores),
    )


def auto_registrar_cliente(cursor, datos: dict[str, Any], ip_cliente: str | None = None) -> dict[str, Any]:
    """Crea la cuenta de usuario (rol Cliente) y la ficha de cliente en una sola transacción atómica."""
    from app.services.auth_service import crear_token_acceso, generar_hash_password
    from app.services.bitacora_service import ACCION_INSERT, registrar_bitacora

    ci = str(datos["ci"]).strip()
    correo = str(datos["correo"]).strip().lower()
    nombre = str(datos["nombre"]).strip()
    apellido = str(datos["apellido"]).strip()
    nombre_completo = f"{nombre} {apellido}".strip()
    telefono = datos.get("telefono")
    if telefono:
        telefono = str(telefono).strip()
    direccion_envio = datos.get("direccion_envio")
    if direccion_envio:
        direccion_envio = str(direccion_envio).strip()
    password = str(datos["password"])

    # 1. Obtener id_rol de 'Cliente'
    cursor.execute("SELECT id_rol FROM rol WHERE LOWER(nombre) = 'cliente';")
    fila_rol = cursor.fetchone()
    id_rol_cliente = fila_rol["id_rol"] if fila_rol else 4

    # 2. Hashear password
    password_hash = generar_hash_password(password)

    # 3. Insertar usuario
    cursor.execute(
        """
        INSERT INTO usuario (nombre, apellido, correo, password_hash, telefono, estado, id_role)
        VALUES (%s, %s, %s, %s, %s, 'Activo', %s)
        RETURNING id_usuario;
        """,
        (nombre, apellido, correo, password_hash, telefono, id_rol_cliente),
    )
    id_usuario = cursor.fetchone()["id_usuario"]

    # 4. Insertar cliente
    cursor.execute(
        """
        INSERT INTO cliente (ci, nombre_completo, telefono, correo, direccion_envio, estado)
        VALUES (%s, %s, %s, %s, %s, 'Activo')
        RETURNING id_cliente;
        """,
        (ci, nombre_completo, telefono, correo, direccion_envio),
    )
    id_cliente = cursor.fetchone()["id_cliente"]

    # 5. Registrar en bitacora (CU25)
    registrar_bitacora(
        cursor=cursor,
        accion=ACCION_INSERT,
        tabla_afectada="cliente",
        id_usuario=id_usuario,
        registro_id=id_cliente,
        detalle=f"Auto-registro de nuevo cliente: {nombre_completo} ({correo}) con CI {ci}",
        ip_address=ip_cliente,
    )

    # 6. Generar token de acceso
    token = crear_token_acceso({
        "id_usuario": id_usuario,
        "correo": correo,
        "nombre": nombre_completo,
        "rol": "Cliente",
        "sub": str(id_usuario),
    })

    return {
        "mensaje": "Cliente registrado exitosamente",
        "id_cliente": id_cliente,
        "id_usuario": id_usuario,
        "nombre_completo": nombre_completo,
        "correo": correo,
        "rol": "Cliente",
        "access_token": token,
        "token_type": "bearer",
    }

