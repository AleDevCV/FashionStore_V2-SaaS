"""Ciclo de pagos del SaaS. Importes de servidor, firmas e idempotencia."""
import os,base64,io,secrets
from datetime import datetime,timezone,timedelta
from decimal import Decimal
import stripe,qrcode
from fastapi import HTTPException
from psycopg2.extras import Json
from app.tenant import require_context
from app.services.commerce import authorized_branch,money

def sandbox():
    key=os.getenv('STRIPE_SECRET_KEY','')
    if not key.startswith('sk_test_'):raise HTTPException(503,'Configure Stripe en modo de prueba para este proyecto académico.')
    stripe.api_key=key

def reservation(cur,rid,customer=None):
    cur.execute('SELECT * FROM reserva WHERE id_reserva=%s FOR UPDATE',(rid,));row=cur.fetchone()
    if not row or (customer is not None and row['id_cliente']!=customer):raise HTTPException(404,'Reserva no disponible para esta cuenta.')
    if row['estado'] not in {'Pendiente','Preparado'}:raise HTTPException(409,'La reserva no está pendiente de pago.')
    expiry=row['fecha_limite'];expiry=expiry.replace(tzinfo=timezone.utc) if expiry.tzinfo is None else expiry
    if expiry<=datetime.now(timezone.utc):raise HTTPException(409,'La reserva venció. Genere una nueva reserva con disponibilidad actual.')
    authorized_branch(cur,row['id_sucursal'],allow_customer=True)
    return row,expiry

def checkout(cur,data,user_id,ip):
    sandbox();row,expiry=reservation(cur,data.id_reserva,data.id_cliente);now=datetime.now(timezone.utc)
    cur.execute("SELECT * FROM pago_transaccion WHERE id_reserva=%s AND pasarela='Stripe' AND estado_pago='Pendiente' ORDER BY id_pago DESC LIMIT 1 FOR UPDATE",(data.id_reserva,));previous=cur.fetchone()
    if previous and previous['vence'] and previous['vence']>now and previous['url_pago']:
        return {'url_pago':previous['url_pago'],'session_id':previous['transaccion_id'],'id_reserva':data.id_reserva,'monto':row['total']}
    if previous:
        cur.execute("UPDATE pago_transaccion SET estado_pago='Expirado' WHERE id_pago=%s",(previous['id_pago'],));cur.execute('UPDATE reserva SET checkout_generation=checkout_generation+1 WHERE id_reserva=%s RETURNING checkout_generation',(data.id_reserva,));generation=cur.fetchone()['checkout_generation']
    else:generation=row['checkout_generation']
    if expiry<now+timedelta(minutes=31):raise HTTPException(409,'La reserva está próxima a vencer. Cancele y cree otra antes de iniciar el pago.')
    base=os.getenv('FRONTEND_URL','http://localhost:8082').rstrip('/');tenant=require_context().tenant_id
    try:
        session=stripe.checkout.Session.create(mode='payment',payment_method_types=['card'],line_items=[{'quantity':1,'price_data':{'currency':'bob','unit_amount':int(money(row['total'])*100),'product_data':{'name':f'Pedido FashionStore {data.id_reserva}'}}}],expires_at=int((now+timedelta(minutes=30)).timestamp()),success_url=base+f'/pago/exitoso?reserva={data.id_reserva}&session_id={{CHECKOUT_SESSION_ID}}',cancel_url=base+f'/pago/cancelado?reserva={data.id_reserva}',metadata={'tenant_id':str(tenant),'id_reserva':str(data.id_reserva),'id_cliente':str(row['id_cliente'])},idempotency_key=f'checkout:{tenant}:{data.id_reserva}:{generation}')
    except Exception:raise HTTPException(502,'Stripe no pudo preparar el pago. La reserva se conserva; reintente.')
    cur.execute("INSERT INTO pago_transaccion(id_reserva,pasarela,transaccion_id,monto,estado_pago,url_pago,vence,payload_respuesta) VALUES(%s,'Stripe',%s,%s,'Pendiente',%s,%s,%s) ON CONFLICT(tenant_id,transaccion_id) DO UPDATE SET url_pago=excluded.url_pago RETURNING id_pago",(data.id_reserva,session.id,row['total'],session.url,datetime.fromtimestamp(session.expires_at,tz=timezone.utc),Json({'id_reserva':data.id_reserva,'session_id':session.id})))
    return {'url_pago':session.url,'session_id':session.id,'id_reserva':data.id_reserva,'monto':row['total']}

def qr(cur,data,user_id,ip):
    row,expiry=reservation(cur,data.id_reserva,data.id_cliente)
    if money(data.monto)!=money(row['total']):raise HTTPException(422,'El importe QR debe coincidir con el total calculado por el servidor.')
    reference='FS-'+secrets.token_hex(6).upper();text=f'FASHIONSTORE-DEMO|{reference}|{money(row["total"])}'
    image=qrcode.make(text);stream=io.BytesIO();image.save(stream,format='PNG');expires=min(expiry,datetime.now(timezone.utc)+timedelta(minutes=15))
    cur.execute("INSERT INTO pago_transaccion(id_reserva,pasarela,transaccion_id,monto,estado_pago,vence,payload_respuesta) VALUES(%s,'QR Bolivia',%s,%s,'Pendiente',%s,%s)",(data.id_reserva,reference,row['total'],expires,Json({'id_reserva':data.id_reserva,'concepto':data.concepto,'simulado':True})))
    return {'qr_base64':base64.b64encode(stream.getvalue()).decode(),'referencia':reference,'monto':row['total'],'id_reserva':data.id_reserva,'expira_en_minutos':15}

def confirm_qr(cur,data,user_id,ip):
    cur.execute("SELECT * FROM pago_transaccion WHERE transaccion_id=%s AND pasarela='QR Bolivia' FOR UPDATE",(data.referencia,));payment=cur.fetchone()
    if not payment or payment['id_reserva']!=data.id_reserva:raise HTTPException(404,'La referencia no corresponde a esta reserva.')
    cur.execute('SELECT id_cliente,id_sucursal,total FROM reserva WHERE id_reserva=%s',(data.id_reserva,));row=cur.fetchone()
    if not row or row['id_cliente']!=data.id_cliente or row['id_sucursal']!=data.id_sucursal or money(payment['monto'])!=money(row['total']):raise HTTPException(422,'Los datos de cobro no coinciden con la reserva.')
    authorized_branch(cur,row['id_sucursal'])
    if payment['estado_pago']=='Aprobado':
        from app.services.venta_service import obtener_venta_por_id
        return obtener_venta_por_id(cur,payment['id_venta'])
    if payment['estado_pago']!='Pendiente' or (payment['vence'] and payment['vence']<=datetime.now(timezone.utc)):raise HTTPException(409,'La referencia ya fue atendida o venció.')
    from app.schemas.venta import VentaConfirmarPeticion
    from app.services.venta_service import confirmar_venta
    data=VentaConfirmarPeticion(id_reserva=data.id_reserva,id_cliente=data.id_cliente,id_sucursal=data.id_sucursal,tipo_venta='Online',metodo_pago='QR',descuento=0)
    sale=confirmar_venta(cur,data,user_id,ip,payment_verified=True)
    cur.execute("UPDATE pago_transaccion SET id_venta=%s,estado_pago='Aprobado' WHERE id_pago=%s",(sale['id_venta'],payment['id_pago']));return sale

def webhook(cur,payload,signature,ip):
    secret=os.getenv('STRIPE_WEBHOOK_SECRET','')
    if not secret:raise HTTPException(503,'Webhook de pagos no configurado.')
    try:event=stripe.Webhook.construct_event(payload,signature,secret,tolerance=300);event=event.to_dict() if hasattr(event,'to_dict') else event
    except Exception:raise HTTPException(400,'Firma de webhook inválida.')
    session=event.get('data',{}).get('object',{});metadata=session.get('metadata',{});event_id=event.get('id')
    if str(metadata.get('tenant_id'))!=str(require_context().tenant_id) or event.get('livemode',False):raise HTTPException(400,'Contexto de empresa o ambiente de pago no válido.')
    # El identificador estable del evento se conserva; la venta tiene además unicidad por reserva.
    if event_id:
        cur.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,272026))',(event_id,));cur.execute('SELECT result FROM stripe_event WHERE event_id=%s',(event_id,));previous=cur.fetchone()
        if previous:return previous['result']
    kind=event.get('type');sid=session.get('id')
    if kind in {'checkout.session.expired','checkout.session.async_payment_failed'}:
        state='Expirado' if kind.endswith('expired') else 'Rechazado'
        cur.execute("UPDATE pago_transaccion SET estado_pago=%s,payload_respuesta=payload_respuesta||%s WHERE transaccion_id=%s AND estado_pago='Pendiente'",(state,Json({'evento':kind}),sid));result={'status':'ok','estado':state}
    elif kind not in {'checkout.session.completed','checkout.session.async_payment_succeeded'}:result={'status':'ignorado','tipo_evento':kind}
    elif metadata.get('tipo')=='cambio':
        if session.get('currency','bob').lower()!='bob':raise HTTPException(400,'Moneda incorrecta.')
        from app.services.exchanges import confirm_difference
        result=confirm_difference(cur,session)
    else:
        try:rid=int(metadata.get('id_reserva',0));cid=int(metadata.get('id_cliente',0));amount=money(Decimal(str(session['amount_total']))/100)
        except (ValueError,TypeError,KeyError):raise HTTPException(400,'Metadata o importe incompleto.')
        cur.execute('SELECT * FROM reserva WHERE id_reserva=%s FOR UPDATE',(rid,));reservation=cur.fetchone()
        if not reservation or reservation['id_cliente']!=cid or money(reservation['total'])!=amount or session.get('payment_status')!='paid' or session.get('currency','bob').lower()!='bob':raise HTTPException(400,'El pago no coincide con la reserva, moneda o importe esperado.')
        cur.execute("INSERT INTO pago_transaccion(id_reserva,pasarela,transaccion_id,monto,estado_pago,payload_respuesta) VALUES(%s,'Stripe',%s,%s,'Pendiente',%s) ON CONFLICT(tenant_id,transaccion_id) DO UPDATE SET payload_respuesta=excluded.payload_respuesta RETURNING id_pago",(rid,sid,amount,Json(dict(session))));pid=cur.fetchone()['id_pago']
        from app.schemas.venta import VentaConfirmarPeticion
        from app.services.venta_service import confirmar_venta
        data=VentaConfirmarPeticion(id_reserva=rid,id_cliente=cid,id_sucursal=reservation['id_sucursal'],tipo_venta='Online',metodo_pago='Tarjeta',descuento=0)
        cur.execute('SAVEPOINT paid_sale')
        try:
            sale=confirmar_venta(cur,data,None,ip,payment_verified=True);cur.execute('RELEASE SAVEPOINT paid_sale');cur.execute("UPDATE pago_transaccion SET id_venta=%s,estado_pago='Aprobado' WHERE id_pago=%s",(sale['id_venta'],pid));result={'status':'ok','id_venta':sale['id_venta']}
        except HTTPException as exc:
            cur.execute('ROLLBACK TO SAVEPOINT paid_sale');cur.execute('RELEASE SAVEPOINT paid_sale')
            if exc.status_code not in {403,404,409}:raise
            cur.execute("UPDATE pago_transaccion SET estado_pago='RequiereResolucion' WHERE id_pago=%s",(pid,));result={'status':'requiere_resolucion','id_pago':pid,'motivo':str(exc.detail)}
    if event_id:cur.execute('INSERT INTO stripe_event(event_id,event_type,result) VALUES(%s,%s,%s)',(event_id,kind,Json(result)))
    return result

def refund_unconfirmed(cur,payment_id):
    from app.permissions import require_permission
    require_permission(cur,'cambios.gestionar');sandbox()
    cur.execute('SELECT * FROM pago_transaccion WHERE id_pago=%s FOR UPDATE',(payment_id,));row=cur.fetchone()
    if not row:raise HTTPException(404,'Pago no disponible.')
    if row['estado_pago']=='Reembolsado':return {'id_pago':payment_id,'estado':'Reembolsado'}
    if row['estado_pago']!='RequiereResolucion' or row['pasarela']!='Stripe':raise HTTPException(409,'Este pago no requiere restitución sin venta.')
    intent=(row['payload_respuesta'] or {}).get('payment_intent')
    if not intent:raise HTTPException(409,'No existe referencia original de cobro; requiere conciliación administrativa.')
    try:refund=stripe.Refund.create(payment_intent=intent,amount=int(money(row['monto'])*100),idempotency_key=f'unconfirmed-refund:{require_context().tenant_id}:{payment_id}')
    except Exception:raise HTTPException(502,'No se pudo solicitar la devolución. El pago permanece pendiente de resolución.')
    cur.execute("UPDATE pago_transaccion SET estado_pago='Reembolsado',payload_respuesta=payload_respuesta||%s WHERE id_pago=%s",(Json({'refund_id':refund.id,'refund_status':refund.status}),payment_id))
    return {'id_pago':payment_id,'estado':'Reembolsado','estado_proveedor':refund.status}
