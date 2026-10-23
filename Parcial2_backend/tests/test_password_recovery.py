import hashlib
from conftest import owner_connection

def test_reset_is_tenant_scoped_one_time_and_revokes_sessions(client,companies,headers,monkeypatch):
    sent=[]
    monkeypatch.setattr('app.routers.auth.enviar_correo_recuperacion',lambda email,name,token: sent.append(token))
    a,b=companies
    r=client.post('/api/auth/recuperar-password',headers={'X-Empresa':a['slug']},json={'correo':'admin@example.com'})
    assert r.status_code==200 and len(sent)==1
    raw=sent[0]
    with owner_connection() as conn,conn.cursor() as cur:
        cur.execute('SELECT token_recuperacion FROM usuario_token WHERE tenant_id=%s',(a['tenant'],));saved=cur.fetchone()['token_recuperacion']
        assert saved==hashlib.sha256(raw.encode()).hexdigest() and saved!=raw
    body={'token':raw,'nueva_password':'changed-password-123'}
    assert client.post('/api/auth/restablecer-password',headers={'X-Empresa':b['slug']},json=body).status_code==400
    assert client.post('/api/auth/restablecer-password',headers={'X-Empresa':a['slug']},json=body).status_code==200
    assert client.post('/api/auth/restablecer-password',headers={'X-Empresa':a['slug']},json=body).status_code==400
    assert client.get('/api/contexto',headers=headers[0]).status_code==401
    assert client.get('/api/contexto',headers=headers[1]).status_code==200
