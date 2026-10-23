from concurrent.futures import ThreadPoolExecutor
from conftest import owner_connection

def reserve_body(c,quantity=1,price=50):return dict(id_cliente=c['customer'],id_sucursal=c['branch'],items=[dict(id_variante_prenda=c['variant'],cantidad=quantity,precio_unitario=price)])
def pos_body(c,quantity=1,price=50):return dict(id_cliente=c['customer'],id_sucursal=c['branch'],metodo_pago='Efectivo',monto_recibido=quantity*price,items=[dict(id_variante_prenda=c['variant'],cantidad=quantity,precio_unitario=price)])
def stock(c):
    with owner_connection() as conn,conn.cursor() as cur:
        cur.execute('SELECT stock FROM inventario WHERE tenant_id=%s AND id_sucursal=%s AND id_variante_prenda=%s',(c['tenant'],c['branch'],c['variant']));return cur.fetchone()['stock']

def test_reserving_holds_availability_without_physical_movement(client,companies,headers):
    c=companies[0]
    r=client.post('/api/ventas/reserva',headers=headers[0],json=reserve_body(c,5));assert r.status_code==201,r.text
    assert stock(c)==5
    r=client.post('/api/pos/ventas',headers=headers[0],json=pos_body(c));assert r.status_code==409,r.text
    assert stock(c)==5

def test_cancellation_releases_hold_without_fictitious_entry(client,companies,headers):
    c=companies[0]
    r=client.post('/api/ventas/reserva',headers=headers[0],json=reserve_body(c,5));rid=r.json()['id_reserva']
    r=client.patch(f'/api/ventas/reservas-probador/{rid}/estado',headers=headers[0],json={'nuevo_estado':'Cancelado'});assert r.status_code==200,r.text
    assert stock(c)==5
    r=client.post('/api/pos/ventas',headers=headers[0],json=pos_body(c));assert r.status_code==201,r.text
    assert stock(c)==4

def test_cashier_cannot_forge_price_or_discount(client,companies,headers):
    c=companies[0]
    r=client.post('/api/pos/ventas',headers=headers[0],json=pos_body(c,price=1));assert r.status_code==409,r.text
    body=pos_body(c);body['descuento']=49
    assert client.post('/api/pos/ventas',headers=headers[0],json=body).status_code==422
    assert stock(c)==5

def test_two_devices_cannot_sell_last_unit(client,companies,headers):
    c=companies[0]
    with owner_connection() as conn,conn.cursor() as cur:
        cur.execute('UPDATE inventario SET stock=1 WHERE tenant_id=%s AND id_sucursal=%s AND id_variante_prenda=%s',(c['tenant'],c['branch'],c['variant']))
    def sell(_):return client.post('/api/pos/ventas',headers=headers[0],json=pos_body(c)).status_code
    with ThreadPoolExecutor(max_workers=2) as pool:codes=list(pool.map(sell,range(2)))
    assert sorted(codes)==[201,409],codes
    assert stock(c)==0

def test_attended_reservation_does_not_invent_cash_payment(client,companies,headers):
    c=companies[0]
    r=client.post('/api/ventas/reserva',headers=headers[0],json=reserve_body(c));rid=r.json()['id_reserva']
    r=client.patch(f'/api/ventas/reservas-probador/{rid}/estado',headers=headers[0],json={'nuevo_estado':'Atendido'});assert r.status_code==409,r.text
    with owner_connection() as conn,conn.cursor() as cur:
        cur.execute('SELECT count(*) AS n FROM venta WHERE id_reserva=%s',(rid,));assert cur.fetchone()['n']==0

def test_configuration_controls_real_reservation_prices(client,companies,headers):
    c=companies[0]
    r=client.put('/api/prendas/'+str(c['product']),headers=headers[0],json={'material':'Lino','precio_oferta':40,'oferta_inicio':'2026-01-01','oferta_fin':'2027-12-31'})
    assert r.status_code==200,r.text
    r=client.post('/api/ventas/reserva',headers=headers[0],json=reserve_body(c,price=50));assert r.status_code==409,r.text
    r=client.post('/api/ventas/reserva',headers=headers[0],json=reserve_body(c,price=40));assert r.status_code==201,r.text
    assert float(r.json()['total'])==40
