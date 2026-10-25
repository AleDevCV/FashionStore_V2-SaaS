import hashlib
import secrets
import pytest
from conftest import owner_connection
from test_saas import app_conn


def register(client, email=None):
    email=email or 'cliente-'+secrets.token_hex(5)+'@example.com'
    response=client.post('/api/auth/registro',json={'nombre':'Cliente','apellido':'Global','ci':'1234567','correo':email,'password':'customer-password-123'})
    assert response.status_code==201,response.text
    return {'Authorization':'Bearer '+response.json()['access_token']},email


def choose(client,header,company):
    response=client.post('/api/auth/seleccionar-tienda',headers=header,json={'empresa':company['slug']})
    assert response.status_code==200,response.text
    return {'Authorization':'Bearer '+response.json()['access_token']}


@pytest.fixture
def customer_companies(companies):
    with owner_connection() as conn,conn.cursor() as cur:
        for company in companies:
            cur.execute("SELECT set_config('app.tenant_id',%s,true)",(str(company['tenant']),))
            cur.execute("INSERT INTO rol(nombre) VALUES('Cliente')")
    return companies


def test_login_uses_email_and_ignores_claimed_company(client,companies):
    a,b=companies
    response=client.post('/api/login',headers={'X-Empresa':b['slug']},json={'correo':a['email'].upper(),'password':'test-password-123'})
    assert response.status_code==200,response.text
    header={'Authorization':'Bearer '+response.json()['access_token']}
    assert client.get('/api/contexto',headers=header).json()['empresa']['slug']==a['slug']
    assert client.post('/api/auth/seleccionar-tienda',headers=header,json={'empresa':b['slug']}).status_code==403


def test_global_email_uniqueness_is_case_insensitive(client):
    _,email=register(client)
    result=client.post('/api/auth/registro',headers={'X-Empresa':'irrelevante'},json={'nombre':'Otra','apellido':'Persona','ci':'1234567','correo':email.upper(),'password':'another-password'})
    assert result.status_code==409


def test_customer_has_no_company_until_store_selection(client):
    header,email=register(client)
    data=client.get('/api/contexto',headers=header).json()
    assert data['empresa'] is None and data['seleccionar_tienda']
    assert data['usuario']['rol']=='Cliente'
    assert client.get('/api/usuarios/',headers=header).status_code==409


def test_one_customer_uses_two_stores_with_distinct_local_profiles(client,customer_companies):
    header,email=register(client)
    profiles=[]
    for company in customer_companies:
        local=choose(client,header,company)
        ctx=client.get('/api/contexto',headers=local).json()
        assert ctx['empresa']['slug']==company['slug'] and ctx['usuario']['rol']=='Cliente'
        assert ctx['usuario']['correo']==email
        profiles.append(ctx['usuario']['id_usuario'])
        catalog=client.get('/api/offline/catalogo',headers=local,params={'branch_id':company['branch']})
        assert catalog.status_code==200,catalog.text
        assert catalog.json()['tenant_id']==company['tenant']
        assert client.get('/api/empresas',headers=local).status_code==403
    assert profiles[0]!=profiles[1]
    repeated=choose(client,header,customer_companies[0])
    assert client.get('/api/contexto',headers=repeated).json()['usuario']['id_usuario']==profiles[0]


def test_global_logout_revokes_every_store_session(client,customer_companies):
    header,_=register(client)
    a,b=[choose(client,header,company) for company in customer_companies]
    assert client.post('/api/logout',headers=b).status_code==200
    for session in (header,a,b):assert client.get('/api/contexto',headers=session).status_code==401


def test_company_admin_cannot_promote_global_customer(client,customer_companies,headers):
    customer,email=register(client)
    local=choose(client,customer,customer_companies[0])
    user=client.get('/api/contexto',headers=local).json()['usuario']['id_usuario']
    result=client.put(f'/api/usuarios/{user}',headers=headers[0],json={'id_role':customer_companies[0]['role']})
    assert result.status_code==403,result.text
    assert client.get('/api/contexto',headers=local).json()['usuario']['rol']=='Cliente'


def test_block_in_one_store_does_not_block_global_account(client,customer_companies,headers):
    header,email=register(client)
    a=choose(client,header,customer_companies[0])
    uid=client.get('/api/contexto',headers=a).json()['usuario']['id_usuario']
    assert client.delete(f'/api/usuarios/{uid}',headers=headers[0]).status_code==200
    assert client.get('/api/contexto',headers=a).status_code==401
    b=choose(client,header,customer_companies[1])
    assert client.get('/api/contexto',headers=b).status_code==200


def test_global_password_recovery_revokes_all_stores(client,customer_companies,monkeypatch):
    sent=[]
    monkeypatch.setattr('app.routers.auth.enviar_correo_recuperacion',lambda email,name,token:sent.append(token))
    header,email=register(client)
    sessions=[choose(client,header,company) for company in customer_companies]
    assert client.post('/api/auth/recuperar-password',json={'correo':email}).status_code==200
    raw=sent[0]
    with owner_connection() as conn,conn.cursor() as cur:
        cur.execute('SELECT token_hash FROM cuenta_recuperacion WHERE token_hash=%s',(hashlib.sha256(raw.encode()).hexdigest(),))
        assert cur.fetchone()['token_hash']!=raw
    assert client.post('/api/auth/verificar-token-recuperacion',json={'token':raw}).json()['valido']
    body={'token':raw,'nueva_password':'changed-global-password'}
    assert client.post('/api/auth/restablecer-password',json=body).status_code==200
    assert client.post('/api/auth/restablecer-password',json=body).status_code==400
    for session in sessions:assert client.get('/api/contexto',headers=session).status_code==401
    assert client.post('/api/login',json={'correo':email,'password':'changed-global-password'}).status_code==200


def test_identity_directory_is_not_readable_as_application(client):
    with app_conn() as conn,conn.cursor() as cur:
        for table in ('cuenta_global','cuenta_recuperacion','auditoria_identidad'):
            cur.execute('SELECT * FROM '+table)
            assert cur.fetchall()==[]


def test_email_prefix_does_not_grant_privileges(client):
    header,_=register(client,'admin-'+secrets.token_hex(5)+'@fashionstore.com')
    assert client.get('/api/cuenta/perfil',headers=header).json()['tipo']=='CLIENTE'
    assert client.get('/api/planes',headers=header).status_code==409


def test_global_purchase_history_contains_only_own_sales_across_stores(client,customer_companies,headers):
    from test_commerce import pos_body
    account,email=register(client)
    other,_=register(client)
    expected=set()
    for company,admin in zip(customer_companies,headers):
        local=choose(client,account,company)
        choose(client,other,company)
        with owner_connection() as conn,conn.cursor() as cur:
            cur.execute('SELECT id_cliente FROM cliente WHERE tenant_id=%s AND correo=%s',(company['tenant'],email))
            customer=cur.fetchone()['id_cliente']
        sale=client.post('/api/pos/ventas',headers=admin,json=pos_body({**company,'customer':customer}))
        assert sale.status_code==201,sale.text
        expected.add(sale.json()['id_venta'])
        assert client.post('/api/pos/ventas',headers=admin,json=pos_body(company)).status_code==201
    history=client.get('/api/cuenta/compras',headers=account)
    assert history.status_code==200,history.text
    assert {row['id_venta'] for row in history.json()}==expected
    assert {row['empresa'] for row in history.json()}=={c['slug'] for c in customer_companies}
    assert client.get('/api/cuenta/compras',headers=other).json()==[]
