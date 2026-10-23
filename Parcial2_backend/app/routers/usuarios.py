"""
=============================================================================
FASHIONSTORE - ROUTER DE ADMINISTRACIÓN DE USUARIOS (CU02)
Sistemas de Información II - UAGRM
-----------------------------------------------------------------------------
Implementa el CRUD de cuentas de usuario y la asignación de roles jerárquicos.

TODOS los endpoints de este router están cerrados al rol "Administrador"
mediante la dependencia `requiere_rol`, cumpliendo el RF02 (control de accesos
basado en roles) y la precondición del CU02.

Cada operación de escritura deja rastro en la tabla `bitacora` (CU25).
=============================================================================
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from psycopg2 import errors as pg_errors

from app.database import get_db
from app.schemas.usuario import (
    MensajeRespuesta,
    RolRespuesta,
    UsuarioActualizar,
    UsuarioCrear,
    UsuarioRespuesta,
)
from app.services.auth_service import generar_hash_password, requiere_rol
from app.services.bitacora_service import (
    ACCION_INACTIVAR,
    ACCION_INSERT,
    ACCION_UPDATE,
    obtener_ip_cliente,
    registrar_bitacora,
)

router = APIRouter(
    prefix="/usuarios",
    tags=["Usuarios y Roles (CU02)"],
)

# Dependencia reutilizada por todos los endpoints: exige sesión activa (CU01) y
# rol "Administrador". Se declara una sola vez para no repetir la lista de roles
# en cada ruta y evitar que un descuido deje un endpoint abierto.
solo_administrador = requiere_rol(["Administrador"])


# -----------------------------------------------------------------------------
# CONSULTA
# -----------------------------------------------------------------------------

@router.get(
    "/",
    response_model=list[UsuarioRespuesta],
    summary="Listar todos los usuarios del sistema",
)
def listar_usuarios(
    cursor=Depends(get_db),
    administrador=Depends(solo_administrador),
):
    """Devuelve el listado completo de usuarios con su rol asociado.

    Corresponde a los pasos 2 y 3 del flujo principal del CU02: el frontend
    Angular pide la lista con el token en la cabecera y renderiza la tabla.

    El `SELECT` enumera las columnas de forma explícita en lugar de usar `*`,
    de modo que `password_hash` nunca sale de la base de datos (RNF01).

    Parámetros:
        cursor: cursor de PostgreSQL inyectado por `get_db`.
        administrador: datos del administrador solicitante; su presencia obliga
                       a FastAPI a ejecutar antes el guardián de rol.

    Retorna:
        list[UsuarioRespuesta]: usuarios ordenados por su identificador.
    """
    cursor.execute(
        """
        SELECT  u.id_usuario,
                u.nombre,
                u.apellido,
                u.correo,
                u.telefono,
                u.estado,
                u.id_role,
                r.nombre AS rol,
                u.created_at
        FROM usuario u
        LEFT JOIN rol r ON u.id_role = r.id_rol
        ORDER BY u.id_usuario;
        """
    )
    return [dict(fila) for fila in cursor.fetchall()]


@router.get(
    "/roles",
    response_model=list[RolRespuesta],
    summary="Listar los roles disponibles",
)
def listar_roles(
    cursor=Depends(get_db),
    administrador=Depends(solo_administrador),
):
    """Devuelve los roles definidos en la tabla `rol`.

    Alimenta el menú desplegable de rol del formulario de alta descrito en el
    prototipo de interfaz del CU02.

    NOTA DE ENRUTADO: esta ruta se declara ANTES que `/{id_usuario}` a
    propósito. FastAPI evalúa las rutas en orden de declaración; si estuviera
    después, la palabra "roles" se interpretaría como un id de usuario y la
    petición fallaría con un error de validación.

    Parámetros:
        cursor: cursor de PostgreSQL inyectado por `get_db`.
        administrador: administrador autenticado.

    Retorna:
        list[RolRespuesta]: roles ordenados por identificador.
    """
    cursor.execute(
        "SELECT id_rol, nombre, descripcion FROM rol ORDER BY id_rol;"
    )
    return [dict(fila) for fila in cursor.fetchall()]


@router.get(
    "/{id_usuario}",
    response_model=UsuarioRespuesta,
    summary="Consultar un usuario por su identificador",
)
def obtener_usuario(
    id_usuario: int,
    cursor=Depends(get_db),
    administrador=Depends(solo_administrador),
):
    """Recupera la ficha de un usuario concreto.

    Parámetros:
        id_usuario: clave primaria del usuario buscado.
        cursor: cursor de PostgreSQL inyectado por `get_db`.
        administrador: administrador autenticado.

    Retorna:
        UsuarioRespuesta: datos públicos del usuario.

    Errores:
        HTTP 404: no existe ningún usuario con ese identificador.
    """
    usuario = _buscar_usuario(cursor, id_usuario)
    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El usuario solicitado no existe",
        )
    return usuario


# -----------------------------------------------------------------------------
# ALTA
# -----------------------------------------------------------------------------

@router.post(
    "/",
    response_model=UsuarioRespuesta,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un nuevo usuario",
)
def crear_usuario(
    datos: UsuarioCrear,
    request: Request,
    cursor=Depends(get_db),
    administrador=Depends(solo_administrador),
):
    """Da de alta un usuario y le asigna un rol jerárquico.

    Corresponde a los pasos 7, 8 y 9 del flujo principal del CU02.

    Lógica y controles aplicados:
      1. Se comprueba que el rol indicado exista, para devolver un mensaje
         claro en lugar de un error de clave foránea de PostgreSQL.
      2. Se verifica que el correo no esté ya registrado (excepción A del CU02).
      3. La contraseña se convierte a hash bcrypt ANTES de tocar la base: en
         ningún momento se escribe en texto plano.
      4. El INSERT del usuario y su registro en `bitacora` comparten la misma
         transacción, de modo que ambos se confirman o se revierten juntos.

    Parámetros:
        datos: cuerpo JSON validado por Pydantic.
        request: petición HTTP, usada para obtener la IP del cliente.
        cursor: cursor de PostgreSQL inyectado por `get_db`.
        administrador: administrador que ejecuta el alta; queda auditado.

    Retorna:
        UsuarioRespuesta: el usuario recién creado, con código HTTP 201.

    Errores:
        HTTP 400: el rol no existe o el correo ya está registrado.
    """
    # --- 1. El rol debe existir ---------------------------------------------
    cursor.execute("SELECT id_rol FROM rol WHERE id_rol = %s;", (datos.id_role,))
    if cursor.fetchone() is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El rol indicado no existe en el sistema",
        )

    # --- 2. El correo no puede estar duplicado (excepción A del CU02) -------
    cursor.execute("SELECT id_usuario FROM usuario WHERE correo = %s;", (datos.correo,))
    if cursor.fetchone() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo electrónico ya se encuentra registrado",
        )

    # --- 3. Hash de la contraseña -------------------------------------------
    password_hash = generar_hash_password(datos.password)

    # --- 4. Inserción -------------------------------------------------------
    try:
        cursor.execute(
            """
            INSERT INTO usuario
                (nombre, apellido, correo, password_hash, telefono, estado, id_role)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id_usuario;
            """,
            (
                datos.nombre,
                datos.apellido,
                datos.correo,
                password_hash,
                datos.telefono,
                datos.estado,
                datos.id_role,
            ),
        )
        nuevo_id = cursor.fetchone()["id_usuario"]

    except pg_errors.UniqueViolation:
        # Red de seguridad ante una condición de carrera: dos altas simultáneas
        # con el mismo correo podrían superar ambas la comprobación del paso 2.
        # La restricción UNIQUE de PostgreSQL es la garantía definitiva.
        # `get_db` revierte la transacción al propagarse esta excepción.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo electrónico ya se encuentra registrado",
        )

    # --- Auditoría (paso 9 del CU02) ----------------------------------------
    registrar_bitacora(
        cursor=cursor,
        accion=ACCION_INSERT,
        tabla_afectada="usuario",
        registro_id=nuevo_id,
        detalle=(
            f"Alta de usuario '{datos.nombre} {datos.apellido}' "
            f"({datos.correo}) con rol id={datos.id_role}."
        ),
        id_usuario=administrador["id_usuario"],
        ip_address=obtener_ip_cliente(request),
    )

    return _buscar_usuario(cursor, nuevo_id)


# -----------------------------------------------------------------------------
# MODIFICACIÓN
# -----------------------------------------------------------------------------

@router.put(
    "/{id_usuario}",
    response_model=UsuarioRespuesta,
    summary="Actualizar los datos de un usuario",
)
def actualizar_usuario(
    id_usuario: int,
    datos: UsuarioActualizar,
    request: Request,
    cursor=Depends(get_db),
    administrador=Depends(solo_administrador),
):
    """Modifica los datos de perfil, el estado o el rol de un usuario.

    La actualización es PARCIAL: se construye dinámicamente la lista de
    columnas a partir de los campos realmente enviados
    (`exclude_unset=True`), de modo que omitir un campo lo deja intacto en
    lugar de sobrescribirlo con NULL.

    SEGURIDAD DEL SQL DINÁMICO: solo los NOMBRES de columna se concatenan, y
    provienen de las claves del modelo de Pydantic, nunca de texto libre del
    usuario. Los VALORES siempre viajan como parámetros (%s), por lo que no hay
    superficie de inyección SQL.

    Parámetros:
        id_usuario: clave primaria del usuario a modificar.
        datos: campos a actualizar; todos opcionales.
        request: petición HTTP, usada para obtener la IP del cliente.
        cursor: cursor de PostgreSQL inyectado por `get_db`.
        administrador: administrador que ejecuta el cambio; queda auditado.

    Retorna:
        UsuarioRespuesta: el usuario ya actualizado.

    Errores:
        HTTP 400: no se envió ningún campo, el rol no existe, o el
                  administrador intenta inhabilitar su propia cuenta.
        HTTP 404: el usuario no existe.
    """
    usuario_actual = _buscar_usuario(cursor, id_usuario)
    if usuario_actual is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El usuario solicitado no existe",
        )

    cambios = datos.model_dump(exclude_unset=True)
    if not cambios:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe enviar al menos un campo para actualizar",
        )

    # Un administrador que se inhabilita a sí mismo perdería el acceso al panel
    # de inmediato (get_current_user rechaza las cuentas inactivas) y podría
    # dejar al sistema sin ningún administrador operativo.
    if (
        cambios.get("estado") == "Inactivo"
        and id_usuario == administrador["id_usuario"]
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puede inhabilitar su propia cuenta de administrador",
        )

    # El rol nuevo, si se envía, debe existir.
    if "id_role" in cambios:
        cursor.execute("SELECT id_rol FROM rol WHERE id_rol = %s;", (cambios["id_role"],))
        if cursor.fetchone() is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El rol indicado no existe en el sistema",
            )

    # Construcción de la cláusula SET a partir de los campos enviados.
    columnas = [f"{columna} = %s" for columna in cambios]
    valores = list(cambios.values())

    # `updated_at` se refresca siempre: la tabla solo tiene un DEFAULT para el
    # alta, no un trigger que lo mantenga al actualizar.
    columnas.append("updated_at = CURRENT_TIMESTAMP")
    valores.append(id_usuario)

    cursor.execute(
        f"UPDATE usuario SET {', '.join(columnas)} WHERE id_usuario = %s;",
        tuple(valores),
    )

    # --- Auditoría ----------------------------------------------------------
    resumen = ", ".join(f"{clave}={valor}" for clave, valor in cambios.items())
    registrar_bitacora(
        cursor=cursor,
        accion=ACCION_UPDATE,
        tabla_afectada="usuario",
        registro_id=id_usuario,
        detalle=(
            f"Modificación del usuario '{usuario_actual['correo']}'. "
            f"Campos actualizados: {resumen}."
        ),
        id_usuario=administrador["id_usuario"],
        ip_address=obtener_ip_cliente(request),
    )

    return _buscar_usuario(cursor, id_usuario)


# -----------------------------------------------------------------------------
# BAJA LÓGICA
# -----------------------------------------------------------------------------

@router.delete(
    "/{id_usuario}",
    response_model=MensajeRespuesta,
    summary="Inhabilitar un usuario (borrado lógico)",
)
def inhabilitar_usuario(
    id_usuario: int,
    request: Request,
    cursor=Depends(get_db),
    administrador=Depends(solo_administrador),
):
    """Inhabilita un usuario cambiando su estado a 'Inactivo'.

    NO se ejecuta un DELETE físico. La tabla `usuario` está referenciada por
    `venta`, `movimiento_inventario`, `sucursal.id_encargado` y `bitacora`;
    borrarla físicamente rompería la integridad referencial o, peor, borraría
    en cascada el historial de operaciones del negocio.

    El efecto es inmediato: `get_current_user` consulta el estado en cada
    petición, de modo que la sesión del usuario inhabilitado deja de funcionar
    aunque su token JWT siga vigente.

    Parámetros:
        id_usuario: clave primaria del usuario a inhabilitar.
        request: petición HTTP, usada para obtener la IP del cliente.
        cursor: cursor de PostgreSQL inyectado por `get_db`.
        administrador: administrador que ejecuta la baja; queda auditado.

    Retorna:
        MensajeRespuesta: confirmación de la inhabilitación.

    Errores:
        HTTP 400: el administrador intenta inhabilitarse a sí mismo.
        HTTP 404: el usuario no existe.
        HTTP 409: el usuario ya estaba inactivo.
    """
    usuario = _buscar_usuario(cursor, id_usuario)
    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El usuario solicitado no existe",
        )

    # Evita que el administrador se bloquee a sí mismo fuera del sistema.
    if id_usuario == administrador["id_usuario"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puede inhabilitar su propia cuenta de administrador",
        )

    if usuario["estado"] == "Inactivo":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El usuario ya se encuentra inhabilitado",
        )

    cursor.execute(
        """
        UPDATE usuario
        SET estado = 'Inactivo', updated_at = CURRENT_TIMESTAMP
        WHERE id_usuario = %s;
        """,
        (id_usuario,),
    )

    registrar_bitacora(
        cursor=cursor,
        accion=ACCION_INACTIVAR,
        tabla_afectada="usuario",
        registro_id=id_usuario,
        detalle=(
            f"Baja lógica del usuario '{usuario['correo']}': "
            f"estado cambiado de 'Activo' a 'Inactivo'."
        ),
        id_usuario=administrador["id_usuario"],
        ip_address=obtener_ip_cliente(request),
    )

    return MensajeRespuesta(
        mensaje=f"El usuario {usuario['correo']} fue inhabilitado correctamente."
    )


# -----------------------------------------------------------------------------
# AUXILIAR INTERNO
# -----------------------------------------------------------------------------

def _buscar_usuario(cursor, id_usuario: int) -> dict | None:
    """Lee un usuario por su identificador, con el nombre de su rol resuelto.

    Se centraliza aquí porque tres endpoints necesitan devolver exactamente la
    misma proyección de columnas, y repetir el SELECT invitaría a que en algún
    punto se colara `password_hash` en la consulta.

    Parámetros:
        cursor: cursor de PostgreSQL activo.
        id_usuario: clave primaria a buscar.

    Retorna:
        dict | None: datos públicos del usuario, o None si no existe.
    """
    cursor.execute(
        """
        SELECT  u.id_usuario,
                u.nombre,
                u.apellido,
                u.correo,
                u.telefono,
                u.estado,
                u.id_role,
                r.nombre AS rol,
                u.created_at
        FROM usuario u
        LEFT JOIN rol r ON u.id_role = r.id_rol
        WHERE u.id_usuario = %s;
        """,
        (id_usuario,),
    )
    fila = cursor.fetchone()
    return dict(fila) if fila else None
