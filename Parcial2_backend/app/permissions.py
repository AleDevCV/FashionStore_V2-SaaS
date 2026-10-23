"""Autorización granular reutilizable por los módulos nuevos."""
from fastapi import HTTPException
from app.tenant import require_context

PERMISSIONS={
'usuarios.ver':'Ver usuarios','usuarios.crear':'Crear usuarios','usuarios.editar':'Editar usuarios','usuarios.inactivar':'Inactivar usuarios',
'roles.ver':'Ver roles','roles.asignar':'Asignar permisos','clientes.ver':'Ver clientes','clientes.crear':'Crear clientes','clientes.editar':'Editar clientes','clientes.inactivar':'Inactivar clientes',
'geografia.ver':'Ver sucursales','ciudades.gestionar':'Gestionar ciudades','sucursales.gestionar':'Gestionar sucursales',
'categorias.ver':'Ver categorías','categorias.gestionar':'Gestionar categorías','prendas.ver':'Ver prendas','prendas.gestionar':'Gestionar prendas',
'pos.vender':'Registrar ventas','ventas.ver':'Consultar ventas','bitacora.ver':'Consultar auditoría',
'offline.operar':'Operar offline','conflictos.resolver':'Resolver conflictos','reportes.ver':'Consultar reportes','reportes.ia':'Solicitar reportes IA','cambios.gestionar':'Atender cambios'}
DEFAULTS={
'Encargado de Sucursal': ['clientes.ver','clientes.crear','geografia.ver','categorias.ver','prendas.ver','prendas.gestionar','pos.vender','ventas.ver','offline.operar','conflictos.resolver','reportes.ver','reportes.ia','cambios.gestionar'],
'Cajero (POS)':['clientes.ver','clientes.crear','geografia.ver','categorias.ver','prendas.ver','pos.vender','ventas.ver','offline.operar','cambios.gestionar']}

def allowed(cur,code):
    ctx=require_context()
    if not ctx.user_id:return False
    if ctx.role=='Administrador' and not ctx.platform:return True
    cur.execute('SELECT 1 FROM usuario u JOIN rol_permiso rp ON rp.id_rol=u.id_role JOIN permiso p USING(id_permiso) WHERE u.id_usuario=%s AND p.codigo=%s',(ctx.user_id,code));return cur.fetchone() is not None

def require_permission(cur,code):
    if not allowed(cur,code):raise HTTPException(403,'No tiene permiso para esta operación.')

def provision_permissions(cur,role_ids):
    for code,name in PERMISSIONS.items():cur.execute('INSERT INTO permiso(nombre,codigo,modulo) VALUES(%s,%s,%s) ON CONFLICT(codigo) DO NOTHING',(name,code,code.split('.')[0]))
    for name,rid in role_ids.items():
        codes=list(PERMISSIONS) if name=='Administrador' else DEFAULTS.get(name,[])
        cur.execute('INSERT INTO rol_permiso(id_rol,id_permiso) SELECT %s,id_permiso FROM permiso WHERE codigo=ANY(%s) ON CONFLICT DO NOTHING',(rid,codes))
