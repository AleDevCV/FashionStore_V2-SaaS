from fastapi import APIRouter,Depends,HTTPException
from app.database import get_db
from app.services.auth_service import get_current_user
from app.services.commerce import authorized_branch
from app.permissions import require_permission
from app.tenant import require_context
router=APIRouter(prefix='/ventas',tags=['Pago y entrega'])
@router.get('/reserva/{reservation_id}/estado-pago')
def payment_status(reservation_id:int,_=Depends(get_current_user),cur=Depends(get_db)):
    cur.execute('SELECT id_reserva FROM reserva WHERE id_reserva=%s',(reservation_id,))
    if not cur.fetchone():raise HTTPException(404,'Reserva no disponible.')
    cur.execute('SELECT id_venta,fecha_entrega FROM venta WHERE id_reserva=%s',(reservation_id,));sale=cur.fetchone()
    if sale:
        from app.services.venta_service import obtener_venta_por_id
        return {'pagada':True,'entregada':sale['fecha_entrega'] is not None,'venta':obtener_venta_por_id(cur,sale['id_venta'])}
    cur.execute('SELECT estado_pago FROM pago_transaccion WHERE id_reserva=%s ORDER BY id_pago DESC LIMIT 1',(reservation_id,));attempt=cur.fetchone()
    return {'pagada':False,'estado':attempt['estado_pago'] if attempt else 'Sin intento de pago','venta':None}

@router.post('/reserva/{reservation_id}/cancelar')
def cancel(reservation_id:int,_=Depends(get_current_user),cur=Depends(get_db)):
    cur.execute('SELECT * FROM reserva WHERE id_reserva=%s FOR UPDATE',(reservation_id,));row=cur.fetchone()
    if not row:raise HTTPException(404,'Reserva no disponible.')
    authorized_branch(cur,row['id_sucursal'],allow_customer=True)
    if require_context().role!='Cliente':require_permission(cur,'pos.vender')
    cur.execute('SELECT 1 FROM venta WHERE id_reserva=%s',(reservation_id,))
    if cur.fetchone():raise HTTPException(409,'La reserva ya está pagada. Gestione la devolución mediante atención al cliente.')
    cur.execute('DELETE FROM retencion WHERE id_reserva=%s',(reservation_id,));cur.execute("UPDATE reserva SET estado='Cancelado' WHERE id_reserva=%s",(reservation_id,));return {'cancelada':True}

@router.post('/{sale_id}/entregar')
def deliver(sale_id:int,_=Depends(get_current_user),cur=Depends(get_db)):
    require_permission(cur,'pos.vender');cur.execute('SELECT * FROM venta WHERE id_venta=%s FOR UPDATE',(sale_id,));row=cur.fetchone()
    if not row:raise HTTPException(404,'Venta no disponible.')
    authorized_branch(cur,row['id_sucursal'])
    if not row['fecha_entrega']:cur.execute('UPDATE venta SET fecha_entrega=now() WHERE id_venta=%s',(sale_id,))
    if row['id_reserva']:cur.execute("UPDATE reserva SET estado='Atendido' WHERE id_reserva=%s",(row['id_reserva'],))
    return {'id_venta':sale_id,'entregada':True}

@router.get('/entregas/pendientes')
def pending(_=Depends(get_current_user),cur=Depends(get_db)):
    require_permission(cur,'pos.vender');cur.execute('SELECT v.id_venta,v.id_reserva,v.total,v.fecha_venta,v.id_sucursal,s.nombre AS sucursal,c.nombre_completo AS cliente FROM venta v JOIN sucursal s USING(id_sucursal) JOIN cliente c USING(id_cliente) WHERE v.fecha_entrega IS NULL ORDER BY v.fecha_venta LIMIT 100');return cur.fetchall()
