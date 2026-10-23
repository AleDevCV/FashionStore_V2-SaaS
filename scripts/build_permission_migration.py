from pathlib import Path
import importlib.util
ROOT=Path(__file__).resolve().parents[1]
# Solo se leen constantes de la fuente; no se importa FastAPI ni su configuración.
import ast
tree=ast.parse((ROOT/'Parcial2_backend/app/permissions.py').read_text(encoding='utf-8'))
values={}
for n in tree.body:
 if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in {'PERMISSIONS','DEFAULTS'}:values[n.targets[0].id]=ast.literal_eval(n.value)
def q(s):return "'"+s.replace("'","''")+"'"
out=['-- Catálogo de permisos y asignación inicial por rol de empresa.']
for code,name in values['PERMISSIONS'].items():out.append(f'INSERT INTO permiso(nombre,codigo,modulo) VALUES({q(name)},{q(code)},{q(code.split(".")[0])}) ON CONFLICT(codigo) DO NOTHING;')
for name,codes in {'Administrador':list(values['PERMISSIONS']),**values['DEFAULTS']}.items():
 out.append(f'INSERT INTO rol_permiso(tenant_id,id_rol,id_permiso) SELECT r.tenant_id,r.id_rol,p.id_permiso FROM rol r CROSS JOIN permiso p WHERE r.nombre={q(name)} AND p.codigo IN ({",".join(q(c) for c in codes)}) ON CONFLICT DO NOTHING;')
(ROOT/'Parcial2_backend/database/migrations/008_permissions.sql').write_text('\n'.join(out)+'\n',encoding='utf-8')
p=ROOT/'Parcial2_backend/app/routers/saas.py';s=p.read_text(encoding='utf-8')
if 'provision_permissions' not in s:s=s.replace("    cur.execute(\"INSERT INTO usuario(nombre", "    from app.permissions import provision_permissions\n    provision_permissions(cur,dict(zip(roles,role_ids)))\n    cur.execute(\"INSERT INTO usuario(nombre",1)
p.write_text(s,encoding='utf-8')
print('Permisos iniciales definidos para empresas existentes y nuevas.')
