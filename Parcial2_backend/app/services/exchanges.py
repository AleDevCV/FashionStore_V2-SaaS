"""CU 24 y 25: crédito original, recepción, reemplazo y movimientos separados."""
import os
from datetime import datetime,timedelta,timezone
from decimal import Decimal
from fastapi import HTTPException
from psycopg2.extras import Json
from app.tenant import require_context
from app.services.commerce import authorized_branch,money,quote,reserve

def get_change(cur,change_id,lock=False):
    cur.execute('SELECT * FROM cambio WHERE id_cambio=%s'+(' FOR UPDATE' if lock else ''),(change_id,));row=cur.fetchone()
    if not row:raise HTTPException(404,'Cambio no encontrado.')
    return dict(row)

def notify(cur,change,title,message):
    cur.execute('INSERT INTO notificacion(id_cliente,id_cambio,titulo,mensaje) VALUES(%s,%s,%s,%s)',(change['id_cliente'],change['id_cambio'],title,message))

def request_change(cur,data):
    ctx=require_context()
    cur.execute('SELECT * FROM venta WHERE id_venta=%s FOR UPDATE',(data.id_venta,));sale=cur.fetchone()
    if not sale:raise HTTPException(404,'Compra no encontrada.')
    if ctx.role!='Cliente':authorized_branch(cur,sale['id_sucursal'])
    delivered=sale['fecha_entrega']
    if delivered is None or datetime.now(timezone.utc)>delivered+timedelta(days=7):raise HTTPException(422,'La compra no está entregada o excede siete días.')
    cur.execute('SELECT d.*,p.admite_cambio FROM detalle_venta d JOIN variante_prenda v USING(id_variante_prenda) JOIN prenda p USING(id_prenda) WHERE d.id_venta=%s AND d.id_variante_prenda=%s',(data.id_venta,data.id_variante_prenda));line=cur.fetchone()
    if not line or not line['admite_cambio']:raise HTTPException(422,'La unidad no es elegible para cambio.')
    cur.execute("SELECT COALESCE(sum(cantidad),0) AS n FROM cambio WHERE id_venta=%s AND id_variante_original=%s AND estado<>'Rechazado' AND (estado<>'Cancelado' OR recibido_at IS NOT NULL)",(data.id_venta,data.id_variante_prenda));used=cur.fetchone()['n']
    if used+data.cantidad>line['cantidad']:raise HTTPException(409,'La cantidad ya fue solicitada o cambiada.')
    credit=money(line['precio_unitario']*data.cantidad)
    cur.execute('INSERT INTO cambio(id_venta,id_cliente,id_sucursal,id_variante_original,cantidad,motivo,credito) VALUES(%s,%s,%s,%s,%s,%s,%s) RETURNING *',(data.id_venta,sale['id_cliente'],sale['id_sucursal'],data.id_variante_prenda,data.cantidad,data.motivo,credit))
    change=dict(cur.fetchone());notify(cur,change,'Solicitud registrada','Su solicitud está pendiente de inspección de la prenda.');return change

def receive(cur,change_id,accepted):
    change=get_change(cur,change_id,True);authorized_branch(cur,change['id_sucursal'])
    if change['estado']!='Solicitado':return change
    if not accepted:
        cur.execute("UPDATE cambio SET estado='Rechazado' WHERE id_cambio=%s",(change_id,))
        notify(cur,change,'Solicitud rechazada','La inspección no aceptó la prenda para cambio.');return get_change(cur,change_id)
    cur.execute("INSERT INTO movimiento_inventario(id_sucursal,id_variante_prenda,tipo,cantidad,motivo,id_usuario) VALUES(%s,%s,'Entrada',%s,%s,%s)",(change['id_sucursal'],change['id_variante_original'],change['cantidad'],f'Recepción de cambio {change_id}',require_context().user_id))
    cur.execute("UPDATE cambio SET recibido_at=now(),estado='Recibido' WHERE id_cambio=%s",(change_id,));notify(cur,change,'Prenda recibida','Crédito disponible para seleccionar reemplazo.');return get_change(cur,change_id)

def replacement(cur,change_id,variant_id):
    change=get_change(cur,change_id,True);authorized_branch(cur,change['id_sucursal'])
    if change['estado']!='Recibido':raise HTTPException(409,'El reemplazo se selecciona tras recibir la prenda y antes de cobrar.')
    cur.execute('SELECT p.*,v.precio_adicional FROM variante_prenda v JOIN prenda p USING(id_prenda) WHERE id_variante_prenda=%s',(variant_id,));product=cur.fetchone()
    if not product:raise HTTPException(404,'Reemplazo no disponible.')
    from app.services.commerce import price_for
    unit=price_for(product,change['cantidad'])
    rid=reserve(cur,change['id_cliente'],change['id_sucursal'],[dict(id_variante_prenda=variant_id,cantidad=change['cantidad'],precio_unitario=unit)],require_context().user_id)
    difference=money(unit*change['cantidad']-change['credito'])
    state='PagoPendiente' if difference>0 else 'ReembolsoPendiente' if difference<0 else 'Listo'
    cur.execute('UPDATE cambio SET id_reserva_reemplazo=%s,diferencia=%s,estado=%s WHERE id_cambio=%s',(rid,difference,state,change_id))
    notify(cur,change,'Reemplazo disponible',f'Diferencia: Bs {difference:.2f}. Revise su solicitud antes de la entrega.');return get_change(cur,change_id)

def payment_session(cur,change_id):
    change=get_change(cur,change_id,True)
    if change['estado']!='PagoPendiente' or change['cancelar']:raise HTTPException(409,'No hay diferencia pendiente de pago.')
    import stripe
    key=os.getenv('STRIPE_SECRET_KEY','')
    if not key.startswith('sk_test_'):raise HTTPException(503,'Configure Stripe sandbox para el prototipo académico.')
    stripe.api_key=key
    ctx=require_context();base=os.getenv('FRONTEND_URL','http://localhost:8082')
    try:
        session=stripe.checkout.Session.create(mode='payment',line_items=[{'quantity':1,'price_data':{'currency':'bob','unit_amount':int(change['diferencia']*100),'product_data':{'name':f'Diferencia de cambio {change_id}'}}}],success_url=base+'/cambios?resultado=pago',cancel_url=base+'/cambios?resultado=cancelado',metadata={'tipo':'cambio','tenant_id':str(ctx.tenant_id),'id_cambio':str(change_id)},idempotency_key=f'change:{ctx.tenant_id}:{change_id}:checkout')
    except Exception:raise HTTPException(502,'No se pudo iniciar el pago. La solicitud se conserva.')
    return {'url_pago':session.url,'id_sesion':session.id}

def confirm_difference(cur,session):
    change=get_change(cur,int(session['metadata']['id_cambio']),True)
    if str(session['metadata'].get('tenant_id'))!=str(require_context().tenant_id):raise HTTPException(400,'Empresa del pago incorrecta.')
    if change['pago_diferencia']:return {'status':'ok','id_cambio':change['id_cambio']}
    if (change['estado']!='PagoPendiente' and not change['cancelar']) or session.get('payment_status')!='paid' or money(Decimal(session['amount_total'])/100)!=change['diferencia']:raise HTTPException(400,'La confirmación no coincide con la diferencia pendiente.')
    cur.execute("INSERT INTO ajuste_monetario(id_cambio,tipo,importe,origen,referencia) VALUES(%s,'Cobro',%s,'Diferencia Stripe',%s)",(change['id_cambio'],change['diferencia'],session['id']))
    cur.execute("UPDATE cambio SET estado=%s,pago_diferencia=%s WHERE id_cambio=%s",('ReembolsoPendiente' if change['cancelar'] else 'Listo',Json(dict(session)),change['id_cambio']))
    notify(cur,change,'Pago confirmado','Se recibió el pago después de la cancelación; su restitución está pendiente.' if change['cancelar'] else 'Su reemplazo está pagado y pendiente de entrega.');return {'status':'ok','id_cambio':change['id_cambio']}

def cancel(cur,change_id):
    change=get_change(cur,change_id,True)
    if change['estado'] in {'Entregado','Reembolsado','Rechazado'}:raise HTTPException(409,'La solicitud ya está finalizada.')
    if change['estado']=='Cancelado':return change
    if change['id_reserva_reemplazo']:
        cur.execute('DELETE FROM retencion WHERE id_reserva=%s',(change['id_reserva_reemplazo'],))
        cur.execute("UPDATE reserva SET estado='Cancelado' WHERE id_reserva=%s",(change['id_reserva_reemplazo'],))
    state='ReembolsoPendiente' if change['recibido_at'] else 'Cancelado'
    cur.execute('UPDATE cambio SET cancelar=true,estado=%s WHERE id_cambio=%s',(state,change_id));notify(cur,change,'Cancelación registrada','Puede consultar la restitución de su crédito cuando corresponda.');return get_change(cur,change_id)

def refund(cur,change_id,cash_confirmed,manual_reference):
    change=get_change(cur,change_id,True);authorized_branch(cur,change['id_sucursal'])
    if change['estado'] in {'Listo','Reembolsado'}:return change
    if change['estado']!='ReembolsoPendiente':raise HTTPException(409,'No existe reembolso pendiente.')
    cur.execute('SELECT * FROM venta WHERE id_venta=%s',(change['id_venta'],));sale=cur.fetchone()
    original_target=change['credito'] if change['cancelar'] else -change['diferencia']
    diff_target=change['diferencia'] if change['cancelar'] and change['pago_diferencia'] else Decimal(0)
    import stripe
    stripe.api_key=os.getenv('STRIPE_SECRET_KEY','')
    for origin,target,payment in [('Original',original_target,None),('Diferencia',diff_target,change['pago_diferencia'])]:
        if target<=0:continue
        cur.execute("SELECT COALESCE(sum(importe),0) AS total FROM ajuste_monetario WHERE id_cambio=%s AND tipo='Reembolso' AND origen=%s",(change_id,origin));already=cur.fetchone()['total'];amount=money(target-already)
        if amount<=0:continue
        reference=f'refund:{require_context().tenant_id}:{change_id}:{origin}:{target}'
        if origin=='Original' and sale['metodo_pago'] in {'Efectivo','QR','Transferencia'}:
            if not cash_confirmed or not manual_reference:raise HTTPException(422,'Confirme la restitución por el medio original e indique su referencia de caja o transferencia.')
            provider_ref=reference+':'+manual_reference
        else:
            if payment is None:
                cur.execute('SELECT payload_respuesta FROM pago_transaccion WHERE id_venta=%s ORDER BY id_pago DESC LIMIT 1',(change['id_venta'],));row=cur.fetchone();payment=row['payload_respuesta'] if row else None
            intent=(payment or {}).get('payment_intent')
            if not intent or not str(stripe.api_key).startswith('sk_test_'):raise HTTPException(409,'El pago original necesita conciliación: falta referencia sandbox de la pasarela.')
            try:provider_ref=stripe.Refund.create(payment_intent=intent,amount=int(amount*100),idempotency_key=reference).id
            except Exception:raise HTTPException(502,'La pasarela no confirmó la devolución; reintente con la misma solicitud.')
        cur.execute("INSERT INTO ajuste_monetario(id_cambio,tipo,importe,origen,referencia) VALUES(%s,'Reembolso',%s,%s,%s)",(change_id,amount,origin,provider_ref))
    state='Reembolsado' if change['cancelar'] else 'Listo'
    cur.execute('UPDATE cambio SET estado=%s WHERE id_cambio=%s',(state,change_id));notify(cur,change,'Reembolso registrado','Se registró la restitución por el medio de pago correspondiente.');return get_change(cur,change_id)

def deliver(cur,change_id):
    change=get_change(cur,change_id,True);authorized_branch(cur,change['id_sucursal'])
    if change['estado']=='Entregado':return change
    if change['estado']!='Listo' or not change['id_reserva_reemplazo']:raise HTTPException(409,'Complete el pago o reembolso antes de entregar.')
    cur.execute('SELECT id_variante_prenda,cantidad,precio_unitario FROM detalle_reserva WHERE id_reserva=%s',(change['id_reserva_reemplazo'],));lines=[dict(x) for x in cur.fetchall()]
    quote(cur,lines,change['id_sucursal'],exclude_reservation=change['id_reserva_reemplazo'])
    for line in lines:cur.execute("INSERT INTO movimiento_inventario(id_sucursal,id_variante_prenda,tipo,cantidad,motivo,id_usuario) VALUES(%s,%s,'Salida',%s,%s,%s)",(change['id_sucursal'],line['id_variante_prenda'],line['cantidad'],f'Entrega reemplazo de cambio {change_id}',require_context().user_id))
    cur.execute('DELETE FROM retencion WHERE id_reserva=%s',(change['id_reserva_reemplazo'],))
    cur.execute("UPDATE reserva SET estado='Atendido' WHERE id_reserva=%s",(change['id_reserva_reemplazo'],))
    cur.execute("UPDATE cambio SET estado='Entregado',entregado_at=now() WHERE id_cambio=%s",(change_id,));notify(cur,change,'Cambio entregado','La entrega del reemplazo quedó registrada.');return get_change(cur,change_id)
