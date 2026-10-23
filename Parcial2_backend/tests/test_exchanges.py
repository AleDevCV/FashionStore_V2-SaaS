from conftest import owner_connection
from test_commerce import pos_body,stock

def request(client,c,h):
    sale=client.post('/api/pos/ventas',headers=h,json=pos_body(c));assert sale.status_code==201,sale.text
    body={'id_venta':sale.json()['id_venta'],'id_variante_prenda':c['variant'],'cantidad':1,'motivo':'Cambio por talla'}
    response=client.post('/api/cambios',headers=h,json=body);assert response.status_code==201,response.text
    return response.json(),body

def test_request_receive_deliver_are_separate_and_idempotent(client,companies,headers):
    c=companies[0];h=headers[0]
    change,body=request(client,c,h);cid=change['id_cambio'];assert stock(c)==4
    assert client.post('/api/cambios',headers=h,json=body).status_code==409
    for _ in range(2):assert client.post(f'/api/cambios/{cid}/recibir',headers=h,json={'aceptada':True}).status_code==200
    assert stock(c)==5
    assert client.put(f'/api/cambios/{cid}/reemplazo',headers=h,json={'id_variante_prenda':c['variant']}).json()['estado']=='Listo'
    assert stock(c)==5
    for _ in range(2):assert client.post(f'/api/cambios/{cid}/entregar',headers=h).status_code==200
    assert stock(c)==4
    assert client.get(f'/api/cambios/{cid}',headers=headers[1]).status_code==404

def test_change_after_seven_days_rejected(client,companies,headers):
    c=companies[0];h=headers[0]
    sale=client.post('/api/pos/ventas',headers=h,json=pos_body(c)).json()
    with owner_connection() as conn,conn.cursor() as cur:cur.execute("UPDATE venta SET fecha_entrega=now()-interval '8 days' WHERE id_venta=%s",(sale['id_venta'],))
    assert client.post('/api/cambios',headers=h,json={'id_venta':sale['id_venta'],'id_variante_prenda':c['variant'],'cantidad':1,'motivo':'Cambio tardío'}).status_code==422

def test_cancel_received_item_refunds_credit_once(client,companies,headers):
    c=companies[0];h=headers[0];change,_=request(client,c,h);cid=change['id_cambio']
    client.post(f'/api/cambios/{cid}/recibir',headers=h,json={'aceptada':True})
    assert client.post(f'/api/cambios/{cid}/cancelar',headers=h).json()['estado']=='ReembolsoPendiente'
    assert client.post(f'/api/cambios/{cid}/reembolsar',headers=h,json={}).status_code==422
    for _ in range(2):
        r=client.post(f'/api/cambios/{cid}/reembolsar',headers=h,json={'confirmar_restitucion':True,'referencia':'CAJA-DEMO-1'});assert r.status_code==200,r.text
    with owner_connection() as conn,conn.cursor() as cur:
        cur.execute('SELECT count(*) AS n,sum(importe) AS total FROM ajuste_monetario WHERE id_cambio=%s',(cid,));row=cur.fetchone();assert row['n']==1 and float(row['total'])==50
    assert stock(c)==5

def test_more_expensive_replacement_cannot_be_delivered_unpaid(client,companies,headers):
    c=companies[0];h=headers[0];change,_=request(client,c,h);cid=change['id_cambio']
    client.post(f'/api/cambios/{cid}/recibir',headers=h,json={'aceptada':True})
    with owner_connection() as conn,conn.cursor() as cur:cur.execute('UPDATE prenda SET precio_base=70 WHERE id_prenda=%s',(c['product'],))
    r=client.put(f'/api/cambios/{cid}/reemplazo',headers=h,json={'id_variante_prenda':c['variant']});assert r.status_code==200,r.text
    assert float(r.json()['diferencia'])==20 and r.json()['estado']=='PagoPendiente'
    assert client.post(f'/api/cambios/{cid}/entregar',headers=h).status_code==409
