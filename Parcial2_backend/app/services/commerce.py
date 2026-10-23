"""Reglas centrales de precios, disponibilidad y reservas compartidas con offline."""
from collections import Counter
from datetime import datetime,timedelta,timezone
from decimal import Decimal,ROUND_HALF_UP
from fastapi import HTTPException
from app.tenant import require_context

CENT=Decimal('0.01')
def money(value):return Decimal(str(value)).quantize(CENT,rounding=ROUND_HALF_UP)

def authorized_branch(cur,branch_id,allow_customer=False):
    ctx=require_context()
    cur.execute('SELECT id_sucursal FROM sucursal WHERE id_sucursal=%s AND activa',(branch_id,))
    if not cur.fetchone():raise HTTPException(404,'Sucursal no disponible.')
    if ctx.role=='Administrador' or (allow_customer and ctx.role=='Cliente'):return
    cur.execute('SELECT 1 FROM usuario_sucursal WHERE id_usuario=%s AND id_sucursal=%s',(ctx.user_id,branch_id))
    if not cur.fetchone():raise HTTPException(403,'No está autorizado en esta sucursal.')

def price_for(row,quantity):
    candidates=[money(row['precio_base'])]
    if row.get('precio_mayorista') is not None and quantity>=(row.get('umbral_mayorista') or 6):candidates.append(money(row['precio_mayorista']))
    today=datetime.now(timezone.utc).date()
    if row.get('precio_oferta') is not None and (row.get('oferta_inicio') is None or row['oferta_inicio']<=today) and (row.get('oferta_fin') is None or row['oferta_fin']>=today):candidates.append(money(row['precio_oferta']))
    return money(min(candidates)+money(row.get('precio_adicional') or 0))

def quote(cur,items,branch_id,exclude_reservation=None,check_known_prices=False):
    """Bloquea variantes en orden estable antes de comprobar stock y retenciones."""
    if not items:raise HTTPException(422,'La operación debe tener detalles.')
    ids=[int(i['id_variante_prenda']) for i in items]
    if len(set(ids))!=len(ids) or any(int(i['cantidad'])<=0 for i in items):raise HTTPException(422,'Variantes únicas y cantidades positivas requeridas.')
    cur.execute('SELECT v.id_variante_prenda,v.id_prenda,v.precio_adicional,p.* FROM variante_prenda v JOIN prenda p USING(id_prenda) WHERE v.id_variante_prenda=ANY(%s) AND p.estado=\'Activo\'',(ids,))
    products={r['id_variante_prenda']:dict(r) for r in cur.fetchall()}
    if len(products)!=len(ids):raise HTTPException(404,'Una variante no está disponible en esta empresa.')
    quantities=Counter()
    for item in items:quantities[products[item['id_variante_prenda']]['id_prenda']]+=item['cantidad']
    result=[]
    for item in sorted(items,key=lambda i:i['id_variante_prenda']):
        vid=item['id_variante_prenda'];row=products[vid]
        cur.execute('SELECT stock FROM inventario WHERE id_sucursal=%s AND id_variante_prenda=%s FOR UPDATE',(branch_id,vid));stock=cur.fetchone()
        cur.execute('SELECT COALESCE(sum(cantidad),0) AS n FROM retencion WHERE id_sucursal=%s AND id_variante_prenda=%s AND vence>now() AND (%s IS NULL OR id_reserva<>%s)',(branch_id,vid,exclude_reservation,exclude_reservation));held=int(cur.fetchone()['n'])
        available=(stock['stock'] if stock else 0)-held
        if available<item['cantidad']:raise HTTPException(409,'Stock disponible insuficiente para la operación completa.')
        price=price_for(row,quantities[row['id_prenda']])
        if check_known_prices and price!=money(item['precio_unitario']):raise HTTPException(409,'El precio cambió. Revise y confirme una nueva operación.')
        result.append(dict(id_variante_prenda=vid,cantidad=item['cantidad'],precio_unitario=price,subtotal=money(price*item['cantidad'])))
    if sum(x['subtotal'] for x in result)>Decimal('99999999.99'):raise HTTPException(422,'El total excede el límite monetario del prototipo.')
    return result

def reserve(cur,customer_id,branch_id,items,user_id):
    authorized_branch(cur,branch_id,allow_customer=True)
    ctx=require_context()
    cur.execute('SELECT id_cliente,correo FROM cliente WHERE id_cliente=%s AND estado=\'Activo\'',(customer_id,));customer=cur.fetchone()
    if not customer or (ctx.role=='Cliente' and (customer['correo'] or '').lower()!=ctx.email.lower()):raise HTTPException(404,'Cliente no disponible.')
    lines=quote(cur,items,branch_id,check_known_prices=True)
    expires=datetime.now(timezone.utc)+timedelta(hours=24)
    total=sum(i['subtotal'] for i in lines)
    cur.execute("INSERT INTO reserva(id_cliente,id_sucursal,fecha_limite,estado,total) VALUES(%s,%s,%s,'Pendiente',%s) RETURNING id_reserva",(customer_id,branch_id,expires,total));rid=cur.fetchone()['id_reserva']
    for line in lines:
        cur.execute('INSERT INTO detalle_reserva(id_reserva,id_variante_prenda,cantidad,precio_unitario) VALUES(%s,%s,%s,%s)',(rid,line['id_variante_prenda'],line['cantidad'],line['precio_unitario']))
        cur.execute('INSERT INTO retencion(id_reserva,id_sucursal,id_variante_prenda,cantidad,vence) VALUES(%s,%s,%s,%s,%s)',(rid,branch_id,line['id_variante_prenda'],line['cantidad'],expires))
    cur.execute("INSERT INTO bitacora(id_usuario,accion,tabla_afectada,registro_id,detalle) VALUES(%s,'RESERVAR','reserva',%s,'Reserva con retención central de 24 horas')",(user_id,rid))
    return rid

def transition_reservation(cur,rid,new_state):
    cur.execute('SELECT * FROM reserva WHERE id_reserva=%s FOR UPDATE',(rid,));row=cur.fetchone()
    if not row:raise HTTPException(404,'Reserva no encontrada.')
    authorized_branch(cur,row['id_sucursal'])
    if row['estado']==new_state:return
    cur.execute('SELECT 1 FROM venta WHERE id_reserva=%s',(rid,))
    if cur.fetchone():raise HTTPException(409,'Reserva cobrada. La entrega se gestiona desde la venta y la restitución desde atención al cliente.')
    if row['estado'] in {'Cancelado','Atendido'}:raise HTTPException(409,'Reserva ya finalizada.')
    if new_state=='Atendido':raise HTTPException(409,'La entrega se confirma después del cobro en POS o pasarela.')
    if new_state not in {'Preparado','Cancelado'}:raise HTTPException(422,'Transición no permitida.')
    if new_state=='Cancelado':cur.execute('DELETE FROM retencion WHERE id_reserva=%s',(rid,))
    cur.execute('UPDATE reserva SET estado=%s,updated_at=now() WHERE id_reserva=%s',(new_state,rid))

def confirm_reservation(cur,data,user_id,payment_verified=False):
    ctx=require_context()
    if not payment_verified and (ctx.role=='Cliente' or data.metodo_pago!='Efectivo'):
        raise HTTPException(403,'La venta requiere cobro autorizado o confirmación de pasarela.')
    cur.execute('SELECT * FROM reserva WHERE id_reserva=%s FOR UPDATE',(data.id_reserva,));reservation=cur.fetchone()
    if not reservation:raise HTTPException(404,'Reserva no encontrada.')
    cur.execute('SELECT id_venta FROM venta WHERE id_reserva=%s',(data.id_reserva,));existing=cur.fetchone()
    if existing:return existing['id_venta']
    if reservation['estado'] not in {'Pendiente','Preparado'}:raise HTTPException(409,'Reserva no disponible para cobro.')
    expires=reservation['fecha_limite']
    if expires.tzinfo is None:expires=expires.replace(tzinfo=timezone.utc)
    if expires<datetime.now(timezone.utc):raise HTTPException(409,'La reserva venció; requiere resolución del cobro.')
    if not payment_verified:authorized_branch(cur,reservation['id_sucursal'])
    cur.execute('SELECT id_variante_prenda,cantidad,precio_unitario FROM detalle_reserva WHERE id_reserva=%s',(data.id_reserva,));lines=[dict(x) for x in cur.fetchall()]
    quote(cur,lines,reservation['id_sucursal'],exclude_reservation=data.id_reserva)
    total=sum(money(x['precio_unitario'])*x['cantidad'] for x in lines)
    if money(getattr(data,'descuento',0))!=0:raise HTTPException(422,'Los descuentos se aplican mediante precios configurados.')
    kind='Online' if payment_verified and data.tipo_venta=='Online' else 'Presencial'
    cur.execute('INSERT INTO venta(id_cliente,id_sucursal,id_cajero,id_reserva,tipo_venta,metodo_pago,subtotal,total,fecha_entrega) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id_venta',(reservation['id_cliente'],reservation['id_sucursal'],user_id,data.id_reserva,kind,data.metodo_pago,total,total,None if kind=='Online' else datetime.now(timezone.utc)));vid=cur.fetchone()['id_venta']
    for line in lines:
        cur.execute('INSERT INTO detalle_venta(id_venta,id_variante_prenda,cantidad,precio_unitario,subtotal) VALUES(%s,%s,%s,%s,%s)',(vid,line['id_variante_prenda'],line['cantidad'],line['precio_unitario'],money(line['precio_unitario'])*line['cantidad']))
        cur.execute("INSERT INTO movimiento_inventario(id_sucursal,id_variante_prenda,tipo,cantidad,motivo,id_usuario) VALUES(%s,%s,'Salida',%s,%s,%s)",(reservation['id_sucursal'],line['id_variante_prenda'],line['cantidad'],f'Venta confirmada {vid}',user_id))
    cur.execute('DELETE FROM retencion WHERE id_reserva=%s',(data.id_reserva,))
    cur.execute("UPDATE reserva SET estado=%s,updated_at=now() WHERE id_reserva=%s",('Preparado' if kind=='Online' else 'Atendido',data.id_reserva))
    return vid

def prepare_pos(cur,data):
    authorized_branch(cur,data.id_sucursal)
    if money(data.descuento)!=0:raise HTTPException(422,'Los descuentos se aplican mediante precios configurados.')
    if data.id_reserva:
        cur.execute('SELECT * FROM reserva WHERE id_reserva=%s FOR UPDATE',(data.id_reserva,));reservation=cur.fetchone()
        if not reservation or reservation['estado'] not in {'Pendiente','Preparado'} or reservation['id_sucursal']!=data.id_sucursal:raise HTTPException(409,'Reserva no disponible para esta venta.')
        cur.execute('SELECT id_variante_prenda,cantidad FROM detalle_reserva WHERE id_reserva=%s',(data.id_reserva,))
        expected={r['id_variante_prenda']:r['cantidad'] for r in cur.fetchall()}
        if expected!={x.id_variante_prenda:x.cantidad for x in data.items}:raise HTTPException(409,'Los detalles no corresponden a la reserva.')
        data.id_cliente=reservation['id_cliente']
    quote(cur,[x.model_dump() for x in data.items],data.id_sucursal,exclude_reservation=data.id_reserva,check_known_prices=True)
