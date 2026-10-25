from datetime import datetime,timezone,timedelta
from conftest import owner_connection

def make_platform_headers():
    from app.tenant import context,TenantContext
    from app.services.auth_service import crear_token_acceso,generar_hash_password
    with owner_connection() as conn,conn.cursor() as cur:
        cur.execute("SELECT id_empresa FROM empresa WHERE plataforma");tid=cur.fetchone()['id_empresa']
        cur.execute("SELECT set_config('app.tenant_id',%s,true)",(str(tid),))
        cur.execute("INSERT INTO rol(nombre) VALUES('Administrador') ON CONFLICT(tenant_id,nombre) DO UPDATE SET nombre=excluded.nombre RETURNING id_rol");rid=cur.fetchone()['id_rol']
        cur.execute("INSERT INTO usuario(nombre,apellido,correo,password_hash,id_role) VALUES('Plataforma','Test','platform@example.com',%s,%s) ON CONFLICT(tenant_id,correo) DO UPDATE SET estado='Activo' RETURNING id_usuario",(generar_hash_password('test-password-123'),rid));uid=cur.fetchone()['id_usuario']
    marker=context.set(TenantContext(tid))
    try:token=crear_token_acceso(dict(id_usuario=uid,rol='Administrador',correo='platform@example.com'))
    finally:context.reset(marker)
    return {'Authorization':'Bearer '+token}

def test_provision_company_is_atomic_and_login_works(client):
    import secrets
    h=make_platform_headers();slug='new-'+secrets.token_hex(5)
    email=slug+'@example.com'
    r=client.post('/api/empresas',headers=h,json=dict(nombre='Nueva empresa',slug=slug,correo_admin=email,password_admin='new-password-123',id_plan=1))
    assert r.status_code==201,r.text
    r=client.post('/api/login/',headers={'X-Empresa':slug},json=dict(correo=email,password='new-password-123'));assert r.status_code==200,r.text
    r=client.get('/api/contexto',headers={'Authorization':'Bearer '+r.json()['access_token']});assert r.json()['suscripcion']['max_sucursales']==2

def test_downgrade_refuses_active_branch_excess(client,companies):
    b=companies[1]
    with owner_connection() as conn,conn.cursor() as cur:
        cur.execute("SELECT set_config('app.tenant_id',%s,true)",(str(b['tenant']),))
        cur.execute("INSERT INTO sucursal(nombre,direccion) VALUES('Dos','Prueba'),('Tres','Prueba')")
    now=datetime.now(timezone.utc)
    r=client.put('/api/suscripciones/'+str(b['tenant']),headers=make_platform_headers(),json=dict(id_plan=1,inicio=now.isoformat(),vencimiento=(now+timedelta(days=30)).isoformat()))
    assert r.status_code==409,r.text

def test_expired_subscription_preserves_read_access(client,companies,headers):
    a=companies[0]
    with owner_connection() as conn,conn.cursor() as cur:
        cur.execute("UPDATE suscripcion SET inicio=now()-interval '40 days', vencimiento=now()-interval '1 day' WHERE tenant_id=%s",(a['tenant'],))
    assert client.get('/api/contexto',headers=headers[0]).status_code==200
    assert client.post('/api/categorias/',headers=headers[0],json={'nombre':'No permitida'}).status_code==403
