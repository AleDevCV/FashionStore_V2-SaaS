import hashlib,hmac,json,time
from datetime import datetime,timezone
from types import SimpleNamespace
from conftest import owner_connection
from test_commerce import reserve_body,stock

def reserve(client,c,h):
    r=client.post('/api/ventas/reserva',headers=h,json=reserve_body(c));assert r.status_code==201,r.text
    return r.json()['id_reserva']

def event(client,c,rid,monkeypatch,kind='checkout.session.completed',sid='cs_test_lifecycle'):
    secret='whsec_isolated_tests';monkeypatch.setenv('STRIPE_WEBHOOK_SECRET',secret)
    payload={'id':'evt_'+kind.replace('.','_')+'_'+sid,'type':kind,'livemode':False,'data':{'object':{'id':sid,'metadata':{'tenant_id':str(c['tenant']),'id_reserva':str(rid),'id_cliente':str(c['customer'])},'amount_total':5000,'currency':'bob','payment_status':'paid','payment_intent':'pi_test_unit'}}}
    raw=json.dumps(payload).encode();stamp=int(time.time());sig=hmac.new(secret.encode(),str(stamp).encode()+b'.'+raw,hashlib.sha256).hexdigest()
    return client.post('/api/pagos/stripe/webhook',content=raw,headers={'Content-Type':'application/json','Stripe-Signature':f't={stamp},v1={sig}'})

def test_checkout_reuses_session_and_ignores_client_return_urls(client,companies,headers,monkeypatch):
    from app.services import payments
    c=companies[0];rid=reserve(client,c,headers[0]);monkeypatch.setenv('STRIPE_SECRET_KEY','sk_test_fake_for_mock');calls=[]
    def create(**kw):calls.append(kw);return SimpleNamespace(id='cs_test_checkout',url='https://checkout.stripe.com/c/pay/cs_test_checkout',expires_at=int(time.time())+1800)
    monkeypatch.setattr(payments.stripe.checkout.Session,'create',create)
    body={'id_reserva':rid,'id_cliente':c['customer'],'url_exito':'https://attacker.invalid/trap','url_cancelacion':'https://attacker.invalid/trap'}
    first=client.post('/api/pagos/stripe/crear-sesion',headers=headers[0],json=body);second=client.post('/api/pagos/stripe/crear-sesion',headers=headers[0],json=body)
    assert first.status_code==second.status_code==201,first.text
    assert first.json()==second.json() and len(calls)==1
    assert 'attacker.invalid' not in calls[0]['success_url'] and calls[0]['line_items'][0]['price_data']['unit_amount']==5000

def test_qr_cannot_choose_a_smaller_amount_or_other_reservation(client,companies,headers):
    c=companies[0];rid=reserve(client,c,headers[0]);body={'id_reserva':rid,'id_cliente':c['customer'],'monto':1}
    assert client.post('/api/pagos/qr/generar',headers=headers[0],json=body).status_code==422
    body['monto']=50;r=client.post('/api/pagos/qr/generar',headers=headers[0],json=body);assert r.status_code==201,r.text
    other=reserve(client,c,headers[0]);confirm={'referencia':r.json()['referencia'],'id_reserva':other,'id_cliente':c['customer'],'id_sucursal':c['branch']}
    assert client.post('/api/pagos/qr/confirmar',headers=headers[0],json=confirm).status_code==404
    confirm['id_reserva']=rid
    a=client.post('/api/pagos/qr/confirmar',headers=headers[0],json=confirm);b=client.post('/api/pagos/qr/confirmar',headers=headers[0],json=confirm)
    assert a.status_code==b.status_code==200,a.text
    assert a.json()['id_venta']==b.json()['id_venta'] and stock(c)==4

def test_successful_webhook_repeated_has_single_sale(client,companies,headers,monkeypatch):
    c=companies[0];rid=reserve(client,c,headers[0]);a=event(client,c,rid,monkeypatch);b=event(client,c,rid,monkeypatch)
    assert a.status_code==b.status_code==200,a.text
    assert a.json()==b.json() and a.json()['id_venta']>0 and stock(c)==4

def test_paid_cancelled_reservation_is_recorded_for_restitution(client,companies,headers,monkeypatch):
    c=companies[0];rid=reserve(client,c,headers[0]);client.patch(f'/api/ventas/reservas-probador/{rid}/estado',headers=headers[0],json={'nuevo_estado':'Cancelado'})
    r=event(client,c,rid,monkeypatch);assert r.status_code==200,r.text
    assert r.json()['status']=='requiere_resolucion' and stock(c)==5
    with owner_connection() as conn,conn.cursor() as cur:
        cur.execute('SELECT estado_pago,id_venta FROM pago_transaccion WHERE id_pago=%s',(r.json()['id_pago'],));row=cur.fetchone();assert row['estado_pago']=='RequiereResolucion' and row['id_venta'] is None

def test_expired_and_rejected_webhooks_update_only_pending_payment(client,companies,headers,monkeypatch):
    c=companies[0];rid=reserve(client,c,headers[0])
    for kind,state,sid in [('checkout.session.expired','Expirado','cs_expire'),('checkout.session.async_payment_failed','Rechazado','cs_reject')]:
        with owner_connection() as conn,conn.cursor() as cur:
            cur.execute("INSERT INTO pago_transaccion(tenant_id,id_reserva,pasarela,transaccion_id,monto,estado_pago) VALUES(%s,%s,'Stripe',%s,50,'Pendiente')",(c['tenant'],rid,sid))
        r=event(client,c,rid,monkeypatch,kind,sid);assert r.status_code==200,r.text
        with owner_connection() as conn,conn.cursor() as cur:
            cur.execute('SELECT estado_pago FROM pago_transaccion WHERE tenant_id=%s AND transaccion_id=%s',(c['tenant'],sid));assert cur.fetchone()['estado_pago']==state

def test_push_installation_is_rebound_without_cross_tenant_disclosure(client,companies,headers):
    token='test-installation-identifier-long-enough'
    assert client.post('/api/dispositivos/push',headers=headers[0],json={'token':token}).status_code==200
    assert client.post('/api/dispositivos/push',headers=headers[1],json={'token':token}).status_code==200
    with owner_connection() as conn,conn.cursor() as cur:
        cur.execute('SELECT tenant_id,id_usuario FROM dispositivo_push WHERE token=%s',(token,));rows=cur.fetchall()
    assert len(rows)==1 and rows[0]['tenant_id']==companies[1]['tenant']

def test_payment_and_physical_delivery_are_separate_and_idempotent(client,companies,headers,monkeypatch):
    c=companies[0];rid=reserve(client,c,headers[0]);r=event(client,c,rid,monkeypatch);assert r.status_code==200,r.text
    sid=r.json()['id_venta'];before=client.get(f'/api/ventas/reserva/{rid}/estado-pago',headers=headers[0]).json()
    assert before['pagada'] and not before['entregada']
    assert client.post(f'/api/ventas/reserva/{rid}/cancelar',headers=headers[0]).status_code==409
    for _ in range(2):assert client.post(f'/api/ventas/{sid}/entregar',headers=headers[0]).status_code==200
    after=client.get(f'/api/ventas/reserva/{rid}/estado-pago',headers=headers[0]).json();assert after['pagada'] and after['entregada']
    assert client.get(f'/api/ventas/reserva/{rid}/estado-pago',headers=headers[1]).status_code==404
    assert stock(c)==4
