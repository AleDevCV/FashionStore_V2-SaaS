import pytest
import psycopg2
from psycopg2.extras import RealDictCursor
from conftest import owner_connection

def app_conn():
    return psycopg2.connect(host='127.0.0.1',port=55432,dbname='fashionstore_p2_test',user='fashionstore_app',password='p2-test-app-only',cursor_factory=RealDictCursor)

def test_database_fails_closed_without_context(companies):
    with app_conn() as conn,conn.cursor() as cur:
        cur.execute('SELECT * FROM prenda');assert cur.fetchall()==[]
        cur.execute('SELECT rolsuper,rolbypassrls FROM pg_roles WHERE rolname=current_user');r=cur.fetchone()
        assert not r['rolsuper'] and not r['rolbypassrls']

def test_rls_and_cross_tenant_fk(companies):
    a,b=companies
    with app_conn() as conn,conn.cursor() as cur:
        cur.execute("SELECT set_config('app.tenant_id',%s,true)",(str(a['tenant']),))
        cur.execute('SELECT id_prenda FROM prenda');assert [x['id_prenda'] for x in cur.fetchall()]==[a['product']]
        with pytest.raises(psycopg2.IntegrityError):
            cur.execute("INSERT INTO variante_prenda(id_prenda,sku_variante) VALUES(%s,'CRUZADO')",(b['product'],))

def test_context_is_separated_in_reused_pool(client,companies,headers):
    for _ in range(5):
        for company,header in zip(companies,headers):
            r=client.get('/api/contexto',headers=header);assert r.status_code==200,r.text
            assert r.json()['empresa']['id_empresa']==company['tenant']
            assert [s['id_sucursal'] for s in r.json()['sucursales']]==[company['branch']]

def test_login_same_email_in_two_companies(client,companies):
    from app.services.auth_service import decodificar_token_acceso
    for company in companies:
        r=client.post('/api/login/',headers={'X-Empresa':company['slug']},json={'correo':'admin@example.com','password':'test-password-123'})
        assert r.status_code==200,r.text
        assert decodificar_token_acceso(r.json()['access_token'])['tenant_id']==company['tenant']

def test_logout_revokes_token(client,headers):
    assert client.post('/api/logout',headers=headers[0]).status_code==200
    assert client.get('/api/contexto',headers=headers[0]).status_code==401

def test_branch_limit_is_database_rule(companies):
    a=companies[0]
    with app_conn() as conn,conn.cursor() as cur:
        cur.execute("SELECT set_config('app.tenant_id',%s,true)",(str(a['tenant']),))
        cur.execute("INSERT INTO sucursal(nombre,direccion) VALUES('Segunda','Prueba')")
        with pytest.raises(psycopg2.errors.CheckViolation):
            cur.execute("INSERT INTO sucursal(nombre,direccion) VALUES('Tercera','Prueba')")

def test_tenant_cannot_administer_platform(client,headers):
    assert client.get('/api/empresas',headers=headers[0]).status_code==403
    assert client.patch('/api/planes/1',headers=headers[0],json={'max_sucursales':9,'reportes_ia':True}).status_code==403

def test_private_static_files_not_published(client,headers):
    assert client.get('/static/comprobantes/ajeno.pdf',headers=headers[0]).status_code==404
