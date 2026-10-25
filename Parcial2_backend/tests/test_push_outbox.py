from types import SimpleNamespace
from conftest import owner_connection
from app.services import push

def test_delivery_result_persists_and_prevents_repeat_send(client,companies,headers,monkeypatch):
    c=companies[0]
    with owner_connection() as conn,conn.cursor() as cur:
        cur.execute("SELECT set_config('app.tenant_id',%s,true)",(str(c['tenant']),))
        cur.execute('UPDATE cliente SET correo=%s WHERE id_cliente=%s',(c['email'],c['customer']))
        cur.execute("INSERT INTO notificacion(id_cliente,titulo,mensaje) VALUES(%s,'Reemplazo disponible','Diferencia de prueba') RETURNING id_notificacion",(c['customer'],));nid=cur.fetchone()['id_notificacion']
    assert client.post('/api/dispositivos/push',headers=headers[0],json={'token':'mock-installation-target-123456'}).status_code==200
    calls=[]
    def send(title,tokens,identifier):calls.append((title,len(tokens),identifier));return [SimpleNamespace(success=True,exception=None)]
    monkeypatch.setattr(push,'send',send)
    push.tenant_batch(c['tenant']);push.tenant_batch(c['tenant'])
    assert len(calls)==1 and calls[0][2]==nid
    with owner_connection() as conn,conn.cursor() as cur:
        cur.execute('SELECT push_enviado FROM notificacion WHERE id_notificacion=%s',(nid,));assert cur.fetchone()['push_enviado']
