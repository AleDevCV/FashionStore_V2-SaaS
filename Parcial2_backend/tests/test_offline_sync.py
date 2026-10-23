from datetime import datetime,timezone
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor
import pytest
from conftest import owner_connection
from test_commerce import stock

def operation(client,c,h,quantity=1):
    r=client.get('/api/offline/catalogo',params={'branch_id':c['branch']},headers=h);assert r.status_code==200,r.text
    snapshot=r.json()
    op=dict(operation_id=str(uuid4()),version=1,tenant_id=c['tenant'],author_id=c['user'],branch_id=c['branch'],device_id=str(uuid4()),kind='venta',occurred_at=datetime.now(timezone.utc).isoformat(),lease=snapshot['lease'],customer_id=c['customer'],cash_received=str(quantity*50),items=[dict(id_variante_prenda=c['variant'],cantidad=quantity,precio_unitario='50.00')])
    return op,snapshot

def send(client,op,h):
    r=client.post('/api/sincronizacion/lote',headers=h,json={'operations':[op]});assert r.status_code==200,r.text
    return r.json()['results'][0]

def test_twenty_retries_have_one_sale_and_movement(client,companies,headers):
    c=companies[0];h=headers[0];op,_=operation(client,c,h)
    results=[send(client,op,h) for _ in range(20)]
    assert all(r==results[0] for r in results) and results[0]['state']=='CONFIRMADA'
    assert stock(c)==4
    with owner_connection() as conn,conn.cursor() as cur:
        cur.execute("SELECT count(*) AS n FROM movimiento_inventario WHERE tenant_id=%s AND tipo='Salida'",(c['tenant'],));assert cur.fetchone()['n']==1
        cur.execute('SELECT count(*) AS n FROM venta WHERE tenant_id=%s',(c['tenant'],));assert cur.fetchone()['n']==1

def test_semantically_equal_money_does_not_change_hash(client,companies,headers):
    op,_=operation(client,companies[0],headers[0]);first=send(client,op,headers[0])
    op['items'][0]['precio_unitario']=50;op['cash_received']=50.0
    assert send(client,op,headers[0])==first

def test_changed_payload_is_rejected_without_changing_original_receipt(client,companies,headers):
    c=companies[0];op,_=operation(client,c,headers[0]);first=send(client,op,headers[0])
    op['items'][0]['cantidad']=2
    assert send(client,op,headers[0])['state']=='RECHAZADA'
    assert client.get('/api/sincronizacion/operaciones/'+op['operation_id'],headers=headers[0]).json()==first
    assert client.get('/api/sincronizacion/operaciones/'+op['operation_id'],headers=headers[1]).status_code==404
    assert stock(c)==4

def test_one_failed_operation_does_not_rollback_valid_batch_item(client,companies,headers):
    c=companies[0];bad,_=operation(client,c,headers[0],6);good,_=operation(client,c,headers[0])
    r=client.post('/api/sincronizacion/lote',headers=headers[0],json={'operations':[bad,good]});assert r.status_code==200,r.text
    assert [x['state'] for x in r.json()['results']]==['EN_CONFLICTO','CONFIRMADA']
    assert stock(c)==4

def test_concurrent_offline_devices_cannot_sell_last_unit(client,companies,headers):
    c=companies[0]
    with owner_connection() as conn,conn.cursor() as cur:cur.execute('UPDATE inventario SET stock=1 WHERE tenant_id=%s AND id_sucursal=%s AND id_variante_prenda=%s',(c['tenant'],c['branch'],c['variant']))
    ops=[operation(client,c,headers[0])[0] for _ in range(2)]
    with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(lambda op:send(client,op,headers[0]),ops))
    assert sorted(r['state'] for r in results)==['CONFIRMADA','EN_CONFLICTO']
    assert stock(c)==0

def test_offline_lease_is_not_an_api_session(client,companies,headers):
    op,snapshot=operation(client,companies[0],headers[0])
    assert client.get('/api/contexto',headers={'Authorization':'Bearer '+snapshot['lease']}).status_code==401
    op['tenant_id']=companies[1]['tenant']
    assert send(client,op,headers[0])['state']=='RECHAZADA'
    assert stock(companies[0])==stock(companies[1])==5

def test_expired_subscription_returns_durable_conflict(client,companies,headers):
    c=companies[0];op,_=operation(client,c,headers[0])
    with owner_connection() as conn,conn.cursor() as cur:cur.execute("UPDATE suscripcion SET inicio=now()-interval '40 days',vencimiento=now()-interval '1 day' WHERE tenant_id=%s",(c['tenant'],))
    first=send(client,op,headers[0]);assert first['state']=='EN_CONFLICTO'
    assert send(client,op,headers[0])==first and stock(c)==5

def test_failure_after_business_before_commit_rolls_back_and_can_retry(client,companies,headers,monkeypatch):
    c=companies[0];op,_=operation(client,c,headers[0])
    from app.services import pos_service
    original=pos_service.procesar_venta_pos
    def fail(*a,**kw):original(*a,**kw);raise RuntimeError('Fallo controlado antes del commit')
    with monkeypatch.context() as patch:
        patch.setattr(pos_service,'procesar_venta_pos',fail)
        with pytest.raises(RuntimeError):send(client,op,headers[0])
    assert stock(c)==5
    assert send(client,op,headers[0])['state']=='CONFIRMADA' and stock(c)==4

def test_malformed_operation_does_not_block_valid_batch_and_rejection_is_durable(client,companies,headers):
    bad,_=operation(client,companies[0],headers[0]);bad['items'][0]['cantidad']=-1
    good,_=operation(client,companies[0],headers[0])
    r=client.post('/api/sincronizacion/lote',headers=headers[0],json={'operations':[bad,good]});assert r.status_code==200,r.text
    results=r.json()['results'];assert [x['state'] for x in results]==['RECHAZADA','CONFIRMADA']
    assert send(client,bad,headers[0])==results[0]
    assert client.get('/api/sincronizacion/operaciones/'+bad['operation_id'],headers=headers[0]).json()==results[0]
