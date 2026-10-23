import json,hmac,hashlib,time

def test_unsigned_webhook_rejected_before_processing(client,monkeypatch):
    monkeypatch.setenv('STRIPE_WEBHOOK_SECRET','whsec_test_only')
    r=client.post('/api/pagos/stripe/webhook',json={'type':'checkout.session.completed','data':{'object':{}}})
    assert r.status_code==400

def test_signed_event_cannot_choose_another_tenant(client,companies,monkeypatch):
    secret='whsec_test_only';monkeypatch.setenv('STRIPE_WEBHOOK_SECRET',secret)
    # Firma correcta, pero reserva inexistente: no debe consolidar venta alguna.
    event={'id':'evt_unit_test','object':'event','type':'checkout.session.completed','data':{'object':{'id':'cs_unit_test','object':'checkout.session','metadata':{'tenant_id':str(companies[0]['tenant']),'id_reserva':'999999','id_cliente':str(companies[1]['customer'])},'payment_status':'paid','amount_total':5000}}}
    raw=json.dumps(event).encode();timestamp=int(time.time())
    signature=hmac.new(secret.encode(),str(timestamp).encode()+b'.'+raw,hashlib.sha256).hexdigest()
    r=client.post('/api/pagos/stripe/webhook',content=raw,headers={'Stripe-Signature':f't={timestamp},v1={signature}','Content-Type':'application/json'})
    assert r.status_code==400,r.text
