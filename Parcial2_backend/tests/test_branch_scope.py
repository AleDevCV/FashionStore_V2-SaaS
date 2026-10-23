from conftest import owner_connection
from app.permissions import provision_permissions
from app.tenant import TenantContext,context
from app.database import get_connection
from test_commerce import pos_body

def test_current_role_and_branch_scope_apply_to_reads_and_writes(client,companies,headers):
    c=companies[0]
    with owner_connection() as conn,conn.cursor() as cur:
        cur.execute("SELECT set_config('app.tenant_id',%s,true)",(str(c['tenant']),))
        cur.execute('SELECT id_ciudad FROM sucursal WHERE id_sucursal=%s',(c['branch'],));city=cur.fetchone()['id_ciudad']
        cur.execute("INSERT INTO sucursal(nombre,direccion,id_ciudad) VALUES('Restringida','Otra dirección',%s) RETURNING id_sucursal",(city,));other=cur.fetchone()['id_sucursal']
        cur.execute('INSERT INTO inventario(id_sucursal,id_variante_prenda,stock) VALUES(%s,%s,5)',(other,c['variant']))
        cur.execute("INSERT INTO rol(nombre) VALUES('Cajero (POS)') RETURNING id_rol");role=cur.fetchone()['id_rol'];provision_permissions(cur,{'Cajero (POS)':role})
        cur.execute('UPDATE usuario SET id_role=%s WHERE id_usuario=%s',(role,c['user']));cur.execute('INSERT INTO usuario_sucursal(tenant_id,id_usuario,id_sucursal) VALUES(%s,%s,%s)',(c['tenant'],c['user'],c['branch']))
    allowed=client.post('/api/pos/ventas',headers=headers[0],json=pos_body(c));assert allowed.status_code==201,allowed.text
    bad=pos_body(c);bad['id_sucursal']=other
    assert client.post('/api/pos/ventas',headers=headers[0],json=bad).status_code==403
    marker=context.set(TenantContext(c['tenant'],user_id=c['user'],role='Cajero (POS)',email='admin@example.com'))
    try:
        with get_connection() as conn,conn.cursor() as cur:
            cur.execute('SELECT DISTINCT id_sucursal FROM inventario');assert [r[0] for r in cur.fetchall()]==[c['branch']]
    finally:context.reset(marker)
    # El JWT anterior decía Administrador, pero la API ya aplica el rol revocado en PostgreSQL.
    assert client.get('/api/usuarios',headers=headers[0]).status_code==403
