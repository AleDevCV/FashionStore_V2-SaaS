import hashlib
from conftest import owner_connection

def test_reset_is_global_one_time_and_revokes_only_owner_sessions(client,companies,headers,monkeypatch):
    sent=[]
    monkeypatch.setattr('app.routers.auth.enviar_correo_recuperacion',lambda email,name,token: sent.append(token))
    a,b=companies
    r=client.post('/api/auth/recuperar-password',json={'correo':a['email']})
    assert r.status_code==200 and len(sent)==1
    raw=sent[0]
    with owner_connection() as conn,conn.cursor() as cur:
        cur.execute('SELECT token_hash FROM cuenta_recuperacion WHERE account_id=(SELECT account_id FROM usuario WHERE id_usuario=%s)',(a['user'],));saved=cur.fetchone()['token_hash']
        assert saved==hashlib.sha256(raw.encode()).hexdigest() and saved!=raw
    body={'token':raw,'nueva_password':'changed-password-123'}
    assert client.post('/api/auth/restablecer-password',json=body).status_code==200
    assert client.post('/api/auth/restablecer-password',headers={'X-Empresa':a['slug']},json=body).status_code==400
    assert client.get('/api/contexto',headers=headers[0]).status_code==401
    assert client.get('/api/contexto',headers=headers[1]).status_code==200
