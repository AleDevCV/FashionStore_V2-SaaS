"""Sequences CU01-CU05, traced to the current Python, Angular, Flutter and SQL."""
from pathlib import Path
import hashlib
import json
import re
from sequence_diagrams import Diagram, M, R, C, O, L, A

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT/'docs/diagramas_secuencia/CU01_CU05'


def P(*rows):
    return [tuple(row.split('|')) for row in rows]


def cu01():
    p=P('actor|Usuario / Cliente|actor',
        'ui|:Acceso y cuenta\nAngular / Flutter|boundary',
        'api|:API de acceso\nauth.py · saas.py|control',
        'id|:identity.py\nauth_service.py|control',
        'cg|:cuenta_global|entity',
        'u|:usuario|entity',
        'e|:empresa|entity',
        'rec|:cuenta_recuperacion|entity',
        'audit|:auditoria_identidad|entity',
        'mail|:email_service.py\nSMTP|external')
    body=[
      M('actor','ui','Solicitar una operación de acceso o cuenta'),
      A(
        ('registrar una cuenta de cliente',[
          M('ui','api','POST /api/auth/registro → register(datos)'),
          M('api','id','generar_hash_password(password)'),
          R('id','api','password_hash'),
          M('api','cg','SQL identity_register(datos con hash)'),
          A(('correo ya registrado',[R('cg','api','UniqueViolation'),R('api','ui','409: iniciar sesión o recuperar contraseña')]),
            ('registro aceptado',[
              M('cg','audit','identity_register(): INSERT evento REGISTRO'),
              R('cg','api','id de cuenta creada'),
              C('api','id','lookup(account_id) → token(account)','JWT de cliente global, sin tienda'),
              R('api','ui','201: cuenta creada y access_token'),
              M('ui','ui','Guardar JWT y abrir selección de tiendas')]))
        ]),
        ('iniciar sesión',[
          M('ui','api','POST /api/login → iniciar_sesion(correo, password)'),
          A(('ocho intentos fallidos dentro de un minuto',[
              R('api','ui','429 + Retry-After: 60')]),
            ('intentos disponibles',[
              C('api','id','lookup(email normalizado)','cuenta y perfil, o cuenta ausente'),
              C('id','cg','SQL identity_lookup(correo, NULL)\nJOIN usuario, rol y empresa','identidad global y contexto del personal'),
              C('api','id','verificar_password(password, hash real o señuelo)','válido / inválido'),
              A(('cuenta ausente o contraseña incorrecta',[
                  C('api','audit','SQL identity_event(account_id, LOGIN_FALLIDO)','evento registrado'),
                  R('api','ui','401: Credenciales incorrectas')]),
                ('credenciales válidas, cuenta o empresa inactiva',[
                  R('api','ui','403: Cuenta o empresa no disponible')]),
                ('credenciales y estado válidos',[
                  C('api','audit','SQL identity_event(account_id, LOGIN_EXITOSO)','evento registrado'),
                  C('api','id','token(account) → crear_token_acceso(claims)','JWT firmado con tipo, rol y ámbito'),
                  R('api','ui','200: access_token'),
                  M('ui','ui','Guardar JWT y resolver navegación por tipo de cuenta'),
                  M('ui','api','GET /api/contexto'),
                  A(('cliente todavía sin tienda',[
                      R('api','ui','unbound_context(): seleccionar_tienda=true')]),
                    ('personal o plataforma con empresa',[
                      C('api','u','get_current_user(): SELECT usuario JOIN rol','usuario activo'),
                      C('api','e','session_context(): SELECT empresa,\nsuscripción y sucursales autorizadas','contexto y offline_hasta'),
                      R('api','ui','200: contexto de empresa o plataforma')]))
                ]))
            ]))
        ]),
        ('recuperar contraseña',[
          M('ui','api','POST /api/auth/recuperar-password\nsolicitar_recuperacion_password(correo)'),
          C('api','id','lookup(email)','cuenta o ausencia'),
          O('cuenta encontrada y activa',
            C('api','rec','SQL identity_reset_issue(account_id, SHA256(token))\ninvalidar anteriores y guardar nuevo hash','token temporal persistido'),
            M('rec','audit','identity_reset_issue(): SOLICITUD_RECUPERACION'),
            C('api','mail','enviar_correo_recuperacion(destinatario, nombre, token)','despachado o no disponible')),
          R('api','ui','200: respuesta uniforme, exista o no la cuenta'),
          O('usuario presenta un enlace de recuperación',
            M('actor','ui','Abrir enlace y escribir nueva contraseña'),
            C('ui','api','POST /api/auth/verificar-token-recuperacion','valido y correo enmascarado'),
            C('api','rec','SQL identity_reset_lookup(SHA256(token))','vigente, no usado y cuenta activa'),
            M('ui','api','POST /api/auth/restablecer-password\nrestablecer_password(token, nueva_password)'),
            C('api','id','generar_hash_password(nueva_password)','nuevo hash'),
            M('api','rec','SQL identity_reset_apply(hash_token, hash_password)'),
            A(('token inválido, usado o vencido',[R('rec','api','false'),R('api','ui','400: token no disponible')]),
              ('token válido; bloqueo FOR UPDATE',
               [M('rec','cg','identity_reset_apply(): UPDATE hash y token_version + 1'),
                M('rec','u','UPDATE perfiles: hash y token_version + 1'),
                M('rec','rec','Marcar tokens de la cuenta como usados'),
                M('rec','audit','INSERT PASSWORD_RESTABLECIDA'),
                R('rec','api','true, transacción confirmada'),
                R('api','ui','200: iniciar sesión con la nueva contraseña')])) )
        ]),
        ('consultar la cuenta autenticada',[
          M('ui','api','GET /api/cuenta/perfil'),
          C('api','id','validate_claims(claims) → lookup(account_id)','estado y versión actuales'),
          A(('JWT inválido o identidad revocada',[R('api','ui','401: sesión no disponible')]),
            ('sesión vigente',[R('api','ui','200: datos permitidos de la cuenta global')]))])
      ),
      O('sesión de cliente válida y desea seleccionar una tienda',
        C('ui','api','GET /api/tiendas → stores()','tiendas activas, sin empresa de plataforma'),
        C('api','e','SELECT empresas activas y no plataforma','listado público de tiendas'),
        M('actor','ui','Elegir tienda'),
        M('ui','api','POST /api/auth/seleccionar-tienda → choose_store(empresa)'),
        M('api','id','select_store(account, slug)'),
        C('id','e','SELECT empresa activa por slug','empresa o ausencia'),
        A(('no es cliente o tienda no disponible',[
            R('id','api','403 / 404'),R('api','ui','Acceso o tienda no disponibles')]),
          ('cliente y tienda habilitados',[
            C('id','u','SQL identity_customer_profile(account_id, tenant_id)\ncrear usuario y ficha cliente solo si faltan','perfil activo o InsufficientPrivilege'),
            A(('perfil de la tienda desactivado o no disponible',[
                R('id','api','403: cuenta o tienda no disponible'),
                R('api','ui','403: selección rechazada')]),
              ('perfil habilitado',[
                C('id','id','token(account, profile)','JWT con empresa elegida'),
                R('id','api','access_token del perfil'),
                R('api','ui','200: token de la tienda'),
                M('ui','ui','Sustituir JWT y contexto; abrir catálogo')]))]))),
      O('usuario autenticado solicita cerrar sesión',
        M('actor','ui','Cerrar sesión'),
        O('hay conectividad y token disponible',
          M('ui','api','POST /api/logout'),
          C('api','cg','SQL identity_revoke(account_id)\ntoken_version + 1','cuenta revocada'),
          M('cg','audit','identity_revoke(): INSERT LOGOUT'),
          O('JWT vinculado a una empresa',
            C('api','u','saas.logout(): UPDATE token_version + 1','sesión empresarial revocada')),
          R('api','ui','200: sesiones revocadas')),
        M('ui','ui','Eliminar token y selección activa;\nconservar IndexedDB / SQLite y pendientes'),
        R('ui','actor','Pantalla de acceso'))
    ]
    return Diagram('CU01','Gestionar acceso y cuenta',p,body,[
      'Parcial2_backend/app/routers/auth.py','Parcial2_backend/app/routers/saas.py',
      'Parcial2_backend/app/services/identity.py','Parcial2_backend/app/services/auth_service.py',
      'Parcial2_backend/app/services/email_service.py','Parcial2_backend/app/tenant_middleware.py',
      'Parcial2_backend/database/migrations/017_global_identity.sql',
      'Parcial2_frontend-web/src/app/core/services/auth.service.ts',
      'Parcial2_mobile/lib/services/auth_service.dart'])


def cu02():
    p=P('actor|Superadministrador SaaS /\nAdministrador de empresa|actor',
        'ui|:Saas\nsaas.ts|boundary','api|:saas.py|control',
        'e|:empresa|entity','plan|:plan|entity','sub|:suscripcion|entity',
        'rol|:rol|entity','perm|:permiso|entity','rp|:rol_permiso|entity',
        'u|:usuario|entity','cg|:cuenta_global|entity','cli|:cliente|entity',
        'suc|:sucursal|entity','audit|:bitacora|entity')
    body=[
      M('actor','ui','Consultar la administración SaaS'),
      M('ui','api','load(): GET /api/contexto'),
      C('api','e','session_context(): SELECT empresa y contexto autorizado','contexto empresarial o de plataforma'),
      R('api','ui','200: contexto'),
      M('ui','api','GET /api/planes'),
      C('api','plan','plans(): SELECT planes','planes configurados'),
      R('api','ui','200: planes'),
      O('contexto de plataforma',
        M('ui','api','GET /api/empresas → companies()'),
        C('api','e','SELECT empresas ORDER BY id_empresa','listado de empresas'),
        R('api','ui','200: empresas no plataforma')),
      A(
        ('superadministrador registra una empresa',[
          M('ui','api','createCompany(): POST /api/empresas → create_company(datos)'),
          M('api','api','platform_user(): validar administrador de plataforma'),
          C('api','plan','SELECT plan por id_plan','plan o ausencia'),
          C('api','e','SELECT empresa por slug','slug libre u ocupado'),
          A(('plan inexistente o slug ocupado',[R('api','ui','404 plan / 409 identificador utilizado')]),
            ('alta válida',[
              C('api','e','INSERT empresa(nombre, slug) RETURNING id_empresa','tenant_id'),
              M('e','audit','audit_business_row(): INSERT empresa'),
              M('api','api','initialize_company(): SET LOCAL app.tenant_id'),
              C('api','sub','INSERT suscripción al plan, vigente por 30 días','suscripción inicial'),
              L('cada uno de los cuatro roles iniciales',
                C('api','rol','INSERT rol(nombre, descripción)','id_rol')),
              M('api','api','provision_permissions(cur, role_ids)'),
              L('cada permiso definido',
                C('api','perm','INSERT permiso ON CONFLICT DO NOTHING','catálogo de permisos')),
              L('cada rol y su selección de permisos',
                C('api','rp','INSERT rol_permiso SELECT permisos predeterminados','asignación inicial')),
              M('api','api','generar_hash_password(password_admin)'),
              C('api','u','INSERT usuario administrador RETURNING id_usuario','administrador de empresa'),
              C('api','cg','index_user(): SQL identity_index_user(id_usuario)','cuenta global o conflicto'),
              A(('correo del administrador ya pertenece a una cuenta global',[
                  R('api','ui','409: ROLLBACK del alta completa de empresa')]),
                ('identidad del administrador admitida',[
                  C('api','cli',"INSERT cliente con CI='MOSTRADOR'",'ficha de mostrador'),
                  R('api','ui','201: id_empresa, id_admin y slug; COMMIT'),
                  M('ui','ui','Vaciar contraseña del formulario y ejecutar load()')]))]))
        ]),
        ('superadministrador modifica un plan',[
          M('ui','api','savePlan(): PATCH /api/planes/{id} → edit_plan()'),
          M('api','api','platform_user()'),
          C('api','plan','SELECT plan FOR UPDATE','plan bloqueado o ausencia'),
          A(('plan inexistente',[R('api','ui','404: Plan no encontrado')]),
            ('plan existente',[
              C('api','plan','UPDATE max_sucursales y reportes_ia RETURNING *','plan actualizado'),
              M('plan','audit','audit_business_row(): UPDATE plan'),
              R('api','ui','200: plan actualizado; COMMIT')]))
        ]),
        ('superadministrador renueva o cambia una suscripción',[
          M('ui','api','saveSubscription(): PUT /api/suscripciones/{empresa}\nedit_subscription(datos)'),
          M('api','api','platform_user(); validar fechas con zona horaria'),
          A(('fechas inválidas',[R('api','ui','422: vencimiento posterior al inicio requerido')]),
            ('fechas válidas',[
              C('api','e','SELECT empresa no plataforma FOR UPDATE','empresa bloqueada o ausencia'),
              A(('empresa inexistente',[R('api','ui','404: Empresa no encontrada')]),
                ('empresa encontrada',[
                  C('api','plan','SELECT max_sucursales FOR SHARE','plan y cupo, o ausencia'),
                  A(('plan inexistente',[R('api','ui','404: Plan no encontrado')]),
                    ('plan encontrado',[
                      M('api','api','SET LOCAL app.tenant_id = empresa objetivo'),
                      C('api','suc','SELECT count(*) WHERE activa','sucursales activas'),
                      A(('sucursales activas superan el nuevo cupo',[
                          R('api','ui','409: desactivar sucursales antes de reducir el plan; ROLLBACK')]),
                        ('cupo admitido',[
                          C('api','sub','INSERT ... ON CONFLICT(tenant_id) DO UPDATE\nplan, inicio y vencimiento','suscripción actualizada'),
                          M('sub','audit','audit_business_row(): INSERT / UPDATE suscripcion'),
                          R('api','ui','200: suscripción vigente según las fechas; COMMIT')]))
                    ]))
                ]))
            ]))
        ]),
        ('superadministrador cambia el estado de una empresa',[
          M('ui','api','toggleCompany(): PATCH /api/empresas/{id}?activa=...'),
          C('api','e','company_state(): UPDATE activa WHERE NOT plataforma','empresa actualizada o ausencia'),
          A(('empresa no encontrada',[R('api','ui','404: Empresa no encontrada')]),
            ('empresa encontrada',[
              M('e','audit','audit_business_row(): UPDATE empresa'),
              R('api','ui','200: id_empresa y estado; COMMIT')]))
        ]),
        ('consultar una suscripción',[
          M('ui','api','GET /api/suscripciones/{empresa} → get_subscription()'),
          A(('plataforma administradora o administrador de su propia empresa',[
              O('actor de plataforma',M('api','api','SET LOCAL app.tenant_id = empresa objetivo')),
              C('api','sub','SELECT suscripcion JOIN plan para la empresa','suscripción o ausencia'),
              R('api','ui','200: suscripción / 404: no encontrada')]),
            ('otro ámbito o rol',[R('api','ui','403: Acceso no autorizado')]))
        ])
      ),
      R('ui','actor','Mostrar resultado y actualizar datos visibles')
    ]
    return Diagram('CU02','Administrar empresas, planes y suscripciones',p,body,[
      'Parcial2_backend/app/routers/saas.py','Parcial2_backend/app/permissions.py',
      'Parcial2_backend/app/services/identity.py','Parcial2_backend/app/database.py',
      'Parcial2_backend/database/migrations/002_saas.sql',
      'Parcial2_backend/database/migrations/007_transactional_audit.sql',
      'Parcial2_backend/database/migrations/017_global_identity.sql',
      'Parcial2_frontend-web/src/app/features/saas/saas.ts'])


def cu03():
    p=P('actor|Administrador de empresa|actor',
        'ui|:Usuarios / RolesPermisos\nAngular|boundary',
        'api|:usuarios.py · roles.py\nadministracion_ext.py|control',
        'id|:identity.py|control','u|:usuario|entity','rol|:rol|entity',
        'perm|:permiso|entity','rp|:rol_permiso|entity','suc|:sucursal|entity',
        'us|:usuario_sucursal|entity','cg|:cuenta_global|entity','audit|:bitacora|entity')
    body=[
      M('actor','ui','Abrir administración de personal y permisos'),
      M('ui','api','GET /api/usuarios/ y GET /api/roles'),
      M('api','api','requiere_rol([Administrador]) / requiere_permiso(roles.ver)'),
      C('api','u','listar_usuarios(): SELECT usuario JOIN rol bajo RLS','usuarios de la empresa'),
      C('api','rol','listar_roles(): SELECT roles','roles de la empresa'),
      R('api','ui','200: datos de administración'),
      A(
        ('crear personal',[
          M('ui','api','POST /api/usuarios/ → crear_usuario(datos)'),
          C('api','rol','SELECT rol por id_role','rol de la empresa o ausencia'),
          C('api','u','SELECT usuario por correo','correo libre o duplicado'),
          A(('rol inexistente o correo empresarial duplicado',[R('api','ui','400: rol o correo inválido')]),
            ('validación inicial correcta',[
              M('api','api','generar_hash_password(password)'),
              C('api','u','INSERT usuario con rol y hash RETURNING id_usuario','id_usuario'),
              C('api','id','index_user(cur, id_usuario)','identidad vinculada o conflicto'),
              C('id','cg','SQL identity_index_user(id_usuario)','id de cuenta global'),
              A(('correo global ocupado o identidad de cliente protegida',[
                  R('api','ui','409 / 403: ROLLBACK del alta')]),
                ('identidad admitida',[
                  M('api','audit','registrar_bitacora(INSERT, usuario)'),
                  C('api','u','_buscar_usuario(id_usuario)','personal y rol'),
                  R('api','ui','201: personal creado; COMMIT')]))
            ]))
        ]),
        ('actualizar personal',[
          M('ui','api','PUT /api/usuarios/{id} → actualizar_usuario()'),
          C('api','u','_buscar_usuario(id_usuario)','usuario actual o ausencia'),
          O('usuario encontrado y se solicita cambiar rol',
            C('api','rol','SELECT rol del nuevo id_role','rol de empresa o ausencia')),
          A(('ausente, cambios vacíos, rol inválido o autoinhabilitación',[
              R('api','ui','404 / 400: operación rechazada')]),
            ('usuario y cambios válidos',[
              C('api','u','UPDATE campos; token_version + 1\nsi cambia rol o estado','usuario actualizado'),
              C('api','id','index_user(cur, id_usuario)','sincronización de identidad o error'),
              C('id','cg','SQL identity_index_user(id_usuario)\nproteger identidad global del cliente','cuenta sincronizada o 403 / 409'),
              A(('identidad global rechaza el cambio',[R('api','ui','403 / 409; ROLLBACK de la actualización')]),
                ('sincronización aceptada',[
                  M('api','audit','registrar_bitacora(UPDATE, usuario)'),
                  R('api','ui','200: usuario actualizado; COMMIT')]))
            ]))
        ]),
        ('inhabilitar personal',[
          M('ui','api','DELETE /api/usuarios/{id} → inhabilitar_usuario()'),
          C('api','u','_buscar_usuario(id_usuario)','usuario actual o ausencia'),
          A(('no existe, es el propio administrador o ya está inactivo',[
              R('api','ui','404 / 400 / 409')]),
            ('inhabilitación permitida',[
              C('api','u',"UPDATE estado='Inactivo' (baja lógica)",'usuario inactivo'),
              M('api','audit','registrar_bitacora(INACTIVAR, usuario)'),
              R('api','ui','200: baja lógica confirmada; COMMIT')]))
        ]),
        ('crear un rol de empresa',[
          M('ui','api','POST /api/roles → create_role(datos)'),
          C('api','rol','SELECT rol por nombre','nombre disponible o duplicado'),
          A(('rol duplicado',[R('api','ui','409: El rol ya existe en esta empresa')]),
            ('nombre disponible',[
              C('api','rol','INSERT rol(nombre, descripcion)','rol creado'),
              M('rol','audit','audit_business_row(): INSERT rol'),
              R('api','ui','201: rol creado; COMMIT')]))
        ]),
        ('consultar o modificar la matriz de permisos',[
          M('ui','api','GET /api/permisos y GET /api/roles/{id}/permisos'),
          C('api','perm','SELECT catálogo de permisos','permisos disponibles'),
          C('api','rp','SELECT permisos WHERE id_rol','asignaciones actuales'),
          R('api','ui','200: rol y permisos / 404: rol ausente'),
          O('administrador guarda una nueva selección',
            M('ui','api','PUT /api/roles/{id}/permisos\nactualizar_permisos_de_rol(permisos_ids)'),
            C('api','rol','SELECT rol bajo RLS','rol o ausencia'),
            O('rol encontrado',
              C('api','perm','Eliminar duplicados y SELECT permisos WHERE id=ANY(ids)','permisos encontrados')),
            A(('rol o permisos inexistentes',[R('api','ui','404 / 400; sin reemplazar la matriz')]),
              ('identificadores válidos',[
                C('api','rp','DELETE rol_permiso WHERE id_rol','asignaciones anteriores retiradas'),
                L('cada id_permiso único seleccionado',
                  C('api','rp','INSERT rol_permiso(id_rol, id_permiso)','permiso asignado')),
                M('api','audit','registrar_bitacora(UPDATE, rol_permiso)'),
                R('api','ui','200: total de permisos; COMMIT')])) )
        ]),
        ('asignar sucursales al personal',[
          M('ui','api','PUT /api/usuarios/{id}/sucursales → assign_branches()'),
          A(('ids no positivos o duplicados',[R('api','ui','422: selección inválida')]),
            ('ids válidos',[
              C('api','u','SELECT usuario FOR UPDATE','usuario de la empresa o ausencia'),
              A(('usuario no encontrado',[R('api','ui','404: Usuario no encontrado')]),
                ('usuario encontrado',[
                  C('api','suc','SELECT sucursales por ids, activas y bajo RLS','sucursales encontradas'),
                  A(('alguna sucursal no está disponible',[R('api','ui','404; conservar asignación anterior')]),
                    ('todas las sucursales disponibles',[
                      C('api','us','DELETE usuario_sucursal WHERE id_usuario','asignaciones anteriores retiradas'),
                      L('cada sucursal seleccionada',
                        C('api','us','INSERT usuario_sucursal(id_usuario, id_sucursal)','sucursal asignada')),
                      R('api','ui','200: sucursales asignadas; COMMIT')]))
                ]))
            ]))
        ])
      ),
      R('ui','actor','Mostrar resultado y recargar personal, roles o asignaciones')
    ]
    return Diagram('CU03','Administrar personal, roles y permisos',p,body,[
      'Parcial2_backend/app/routers/usuarios.py','Parcial2_backend/app/routers/roles.py',
      'Parcial2_backend/app/routers/administracion_ext.py','Parcial2_backend/app/services/identity.py',
      'Parcial2_backend/app/services/auth_service.py','Parcial2_backend/app/tenant_middleware.py',
      'Parcial2_backend/database/migrations/017_global_identity.sql',
      'Parcial2_frontend-web/src/app/features/usuarios/usuarios.ts',
      'Parcial2_frontend-web/src/app/features/admin/roles-permisos/roles-permisos.ts'])


def cu04():
    p=P('actor|Administrador de empresa|actor',
        'ui|:Sucursales / SucursalModal\nGeografiaService|boundary',
        'api|:geografia.py\nadministracion_ext.py|control',
        'svc|:geografia_service.py|control','city|:ciudad|entity',
        'suc|:sucursal|entity','u|:usuario|entity','e|:empresa|entity',
        'sub|:suscripcion|entity','plan|:plan|entity','audit|:bitacora|entity')
    def save(success, code, origin):
        accepted = [
          M('suc','audit','audit_business_row(): cambio de sucursal'),
          R('suc',origin,success),
          *([R('svc','api',success),
             M('api','audit','registrar_bitacora(INSERT / UPDATE, sucursal)'),
             C('api','svc','obtener_sucursal(cursor, id_sucursal)','sucursal con ciudad y encargado'),
             C('svc','suc','SELECT sucursal JOIN ciudad y usuario','datos actualizados')]
            if origin=='svc' else []),
          R('api','ui',code+'; COMMIT')]
        if origin=='svc':
            accepted = [
              O('encargado informado o modificado',
                C('suc','u','Validar FK(tenant_id, id_encargado)','referencia válida o violación')),
              A(('referencia de encargado inválida',[
                  R('suc','svc','ForeignKeyViolation'),
                  R('svc','api','Error de referencia del encargado'),
                  R('api','ui','400 / 422: integridad; ROLLBACK')]),
                ('referencias válidas',accepted))]
        return [
          O('alta activa o transición de inactiva a activa',
            M('suc','suc','check_branch_limit() — trigger BEFORE'),
            C('suc','e','SELECT empresa FOR UPDATE','bloqueo por empresa'),
            C('suc','sub','SELECT suscripción vigente JOIN plan','capacidad o suscripción no vigente'),
            C('sub','plan','JOIN plan USING(id_plan): max_sucursales','límite contratado'),
            C('suc','suc','SELECT count(*) de sucursales activas','cupo utilizado')),
          A(('alta/reactivación sin vigencia o sin cupo',[
              R('suc',origin,'CheckViolation (23514)'),
              *([R('svc','api','IntegrityError: propagar al manejador global')] if origin=='svc' else []),
              R('api','ui','422: límite del plan o integridad; ROLLBACK')]),
            ('cupo admitido o la operación no consume cupo',accepted))]
    body=[
      M('actor','ui','Consultar ciudades y sucursales'),
      M('ui','api','GET /api/ciudades y GET /api/sucursales?id_ciudad=...'),
      C('api','svc','listar_ciudades() / listar_sucursales(id_ciudad)','ciudades y sucursales visibles'),
      C('svc','city','SELECT ciudad LEFT JOIN sucursal, agrupado','ciudades con total_sucursales'),
      C('svc','suc','SELECT sucursal JOIN ciudad y encargado, bajo RLS','sucursales de la empresa'),
      R('api','ui','200: estructura operativa'),
      O('necesita una nueva ciudad',
        M('ui','api','POST /api/ciudades → crear_ciudad(nombre)'),
        C('api','svc','existe_ciudad_por_nombre(nombre)','existe / no existe'),
        A(('nombre duplicado',[R('api','ui','400: ciudad ya registrada')]),
          ('nombre disponible',[
            C('api','svc','crear_ciudad(cursor, nombre)','ciudad creada'),
            C('svc','city','INSERT ciudad RETURNING id_ciudad, nombre','ciudad persistida'),
            M('api','audit','registrar_bitacora(INSERT, ciudad)'),
            R('api','ui','201: ciudad creada; COMMIT')])) ),
      A(
        ('registrar una sucursal',[
          M('ui','api','POST /api/sucursales → crear_sucursal(datos)'),
          C('api','svc','existe_ciudad(id_ciudad)','ciudad visible o ausencia'),
          A(('ciudad inexistente o de otra empresa',[R('api','ui','400: ciudad no disponible')]),
            ('ciudad válida',[
              M('api','svc','crear_sucursal(cursor, datos)'),
              M('svc','suc','INSERT sucursal(nombre, dirección, ciudad, encargado)'),
              *save('id_sucursal','201: sucursal creada','svc')
            ]))
        ]),
        ('actualizar los datos de una sucursal',[
          M('ui','api','PUT /api/sucursales/{id} → actualizar_sucursal()'),
          C('api','svc','obtener_sucursal(id_sucursal)','sucursal bajo RLS o ausencia'),
          O('sucursal encontrada y se solicita cambiar ciudad',
            C('api','svc','existe_ciudad(nuevo_id)','ciudad disponible o ausencia')),
          A(('no existe, cambios vacíos o ciudad no disponible',[R('api','ui','404 / 400')]),
            ('sucursal y cambios disponibles',[
              M('api','svc','actualizar_sucursal(cursor, id_sucursal, cambios)'),
              M('svc','suc','UPDATE campos enviados y updated_at'),
              *save('sucursal actualizada','200: sucursal actualizada','svc')
            ]))
        ]),
        ('suspender o reactivar una sucursal',[
          M('ui','api','PATCH /api/sucursales/{id}/estado?activa=...\nbranch_state()'),
          M('api','suc','UPDATE activa RETURNING id_sucursal, nombre, activa'),
          A(('sucursal no visible o inexistente',[R('api','ui','404: Sucursal no encontrada')]),
            ('sucursal existente',save('sucursal con nuevo estado','200: estado actualizado','api')))
        ])
      ),
      R('ui','actor','Mostrar resultado y actualizar la estructura operativa')
    ]
    return Diagram('CU04','Gestionar ciudades y sucursales',p,body,[
      'Parcial2_backend/app/routers/geografia.py','Parcial2_backend/app/services/geografia_service.py',
      'Parcial2_backend/app/routers/administracion_ext.py','Parcial2_backend/app/main.py',
      'Parcial2_backend/database/migrations/001_baseline.sql',
      'Parcial2_backend/database/migrations/002_saas.sql',
      'Parcial2_backend/database/migrations/007_transactional_audit.sql',
      'Parcial2_frontend-web/src/app/core/services/geografia.service.ts',
      'Parcial2_frontend-web/src/app/features/sucursales/sucursales.ts'])


def cu05():
    p=P('actor|Personal autorizado / Cliente|actor',
        'ui|:Clientes / Ficha propia\nAngular|boundary','api|:clientes.py / auth.py|control',
        'svc|:cliente_service.py\nidentity.py|control','cli|:cliente|entity',
        'u|:usuario|entity','e|:empresa|entity','sale|:venta|entity','audit|:bitacora|entity')
    body=[
      M('actor','ui','Consultar o mantener información comercial del cliente'),
      A(
        ('personal con permisos sobre fichas de su empresa',[
          M('ui','api','GET /api/clientes/?busqueda=...&estado=...'),
          M('api','api','requiere_permiso(clientes.ver)'),
          C('api','svc','listar_clientes(cursor, busqueda, estado)','fichas visibles'),
          C('svc','cli','SELECT con ILIKE(ci, nombre) y filtro de estado, bajo RLS','fichas de la empresa'),
          R('api','ui','200: resultados de búsqueda'),
          A(
            ('crear ficha',[
              M('ui','api','POST /api/clientes/ → crear_cliente(datos)'),
              M('api','api','requiere_permiso(clientes.crear)'),
              C('api','svc','existe_ci(ci) y existe_correo(correo)','duplicidad en la empresa o datos libres'),
              A(('CI o correo duplicado',[R('api','ui','400: ficha duplicada')]),
                ('datos válidos',[
                  M('api','svc','crear_cliente(cursor, datos)'),
                  C('svc','cli','INSERT cliente RETURNING id_cliente','ficha creada o UniqueViolation'),
                  A(('duplicación concurrente',[R('api','ui','400; ROLLBACK')]),
                    ('inserción aceptada',[
                      M('api','audit','registrar_bitacora(INSERT, cliente)'),
                      R('api','ui','201: ficha creada; COMMIT')]))
                ]))
            ]),
            ('actualizar ficha',[
              M('ui','api','PUT /api/clientes/{id} → actualizar_cliente()'),
              M('api','api','requiere_permiso(clientes.editar)'),
              C('api','svc','obtener_cliente(id_cliente)','ficha bajo RLS o ausencia'),
              O('ficha encontrada y hay cambios',
                C('api','svc','existe_ci / existe_correo excluyendo id_cliente','identificadores disponibles o duplicados')),
              A(('ficha ausente, cambios vacíos o duplicados',[R('api','ui','404 / 400')]),
                ('cambios válidos',[
                  M('api','svc','actualizar_cliente(cursor, id_cliente, cambios)'),
                  C('svc','cli','actualizar_cliente(): UPDATE campos enviados','ficha actualizada'),
                  R('svc','api','actualización completada'),
                  M('api','audit','registrar_bitacora(UPDATE, cliente)'),
                  R('api','ui','200: ficha actualizada; COMMIT')]))
            ]),
            ('inhabilitar ficha',[
              M('ui','api','DELETE /api/clientes/{id} → inhabilitar_cliente()'),
              M('api','api','requiere_permiso(clientes.inactivar)'),
              C('api','svc','obtener_cliente(id_cliente)','ficha y estado'),
              A(('no existe o ya está inactiva',[R('api','ui','404 / 409')]),
                ('baja lógica permitida',[
                  M('api','svc','inhabilitar_cliente(cursor, id_cliente)'),
                  C('svc','cli',"inhabilitar_cliente(): UPDATE estado='Inactivo'",'historial conservado'),
                  R('svc','api','baja lógica completada'),
                  M('api','audit','registrar_bitacora(INACTIVAR, cliente)'),
                  R('api','ui','200: ficha inhabilitada; COMMIT')]))
            ]),
            ('consultar detalle de una ficha',[
              M('ui','api','GET /api/clientes/{id} → obtener_cliente()'),
              C('api','svc','obtener_cliente(id_cliente)','ficha autorizada o ausencia'),
              R('api','ui','200: ficha / 404: no visible')])
          )
        ]),
        ('cliente consulta su propia ficha',[
          M('ui','api','GET /api/clientes/me → obtener_mi_ficha()'),
          M('api','api','requiere_rol([Cliente]); _obtener_ficha_propia()'),
          C('api','svc','obtener_cliente_por_correo(usuario.correo)','ficha propia o ausencia'),
          C('svc','cli','SELECT por correo autenticado y empresa actual','ficha propia'),
          R('api','ui','200: ficha propia / 404: no vinculada'),
          O('ficha propia encontrada y cliente desea actualizarla',
            M('ui','api','PUT /api/clientes/me → actualizar_mi_ficha()'),
            C('api','svc','Resolver ficha propia; validar campos, CI y correo','validación empresarial'),
            A(('sin campos, datos nulos o duplicados',[R('api','ui','400: datos no admitidos')]),
              ('campos inicialmente válidos',[
                C('api','svc','actualizar_cliente(cursor, id_propio, cambios)','ficha modificada en la transacción'),
                C('svc','cli','UPDATE datos comerciales','actualización pendiente de COMMIT'),
                M('api','svc','sincronizar_contacto_usuario(id_usuario, cambios)'),
                A(('intenta cambiar el correo de acceso global',[
                    R('svc','api','400: identidad global protegida'),
                    R('api','ui','400; ROLLBACK de la ficha y del contacto')]),
                  ('correo global conservado',[
                    O('se informa teléfono u otro contacto sincronizable',
                      C('svc','u','UPDATE contacto permitido del usuario propio','contacto sincronizado')),
                    R('svc','api','contacto validado'),
                    M('api','audit','registrar_bitacora(UPDATE, cliente propio)'),
                    R('api','ui','200: ficha propia actualizada; COMMIT')]))
              ])) )
        ]),
        ('cliente consulta su historial entre tiendas',[
          M('ui','api','GET /api/cuenta/compras → purchases(request)'),
          M('api','svc','identity.purchases(account autenticado)'),
          C('svc','e','SELECT empresas ORDER BY id_empresa LIMIT 500','empresas a recorrer'),
          L('cada empresa del listado',
            M('svc','svc','Fijar TenantContext de la empresa,\nrol Cliente, correo y account_id del titular'),
            C('svc','u',"SELECT perfil WHERE account_id y estado='Activo'",'perfil o ausencia'),
            O('existe perfil activo',
              C('svc','sale','SELECT venta JOIN cliente por correo del titular\nORDER BY fecha DESC LIMIT 100, bajo RLS','compras propias de esa tienda'),
              M('svc','svc','Acumular compras con slug y nombre de tienda')),
            M('svc','svc','Restaurar el contexto anterior')),
          R('svc','api','historial de ventas propias entre tiendas'),
          R('api','ui','200: compras del titular')])
      ),
      R('ui','actor','Mostrar ficha, historial o motivo del rechazo')
    ]
    return Diagram('CU05','Gestionar fichas de clientes',p,body,[
      'Parcial2_backend/app/routers/clientes.py','Parcial2_backend/app/services/cliente_service.py',
      'Parcial2_backend/app/routers/auth.py','Parcial2_backend/app/services/identity.py',
      'Parcial2_backend/app/services/auth_service.py','Parcial2_backend/database/migrations/003_customer_ownership.sql',
      'Parcial2_frontend-web/src/app/features/clientes/clientes.ts',
      'Parcial2_frontend-web/src/app/core/services/cliente.service.ts'])


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    results=[]
    for factory in [cu01,cu02,cu03,cu04,cu05]:
        diagram=factory()
        result=diagram.render(OUT)
        result['fuentes_sha256']={src:hashlib.sha256((ROOT/src).read_bytes()).hexdigest() for src in result['fuentes']}
        results.append(result)
        print(result['cu'],result['mensajes'],'messages',result['fragmentos'],f"{result['ancho']}x{result['alto']}")
    (OUT/'TRAZABILIDAD_Y_VALIDACION.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')


if __name__=='__main__':
    main()
