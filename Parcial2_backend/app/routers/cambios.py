from fastapi import APIRouter,Depends,HTTPException,Query
from pydantic import BaseModel,Field
from app.database import get_db
from app.services.auth_service import get_current_user,requiere_rol
from app.services import exchanges as service
from app.tenant import require_context

router=APIRouter(tags=['Cambios y notificaciones'])
staff=requiere_rol(['Administrador','Encargado de Sucursal','Cajero (POS)'])
class RequestChange(BaseModel):
    id_venta:int=Field(gt=0)
    id_variante_prenda:int=Field(gt=0)
    cantidad:int=Field(gt=0,le=1000)
    motivo:str=Field(min_length=4,max_length=1000)
class Receive(BaseModel):aceptada:bool
class Replacement(BaseModel):id_variante_prenda:int=Field(gt=0)
class Refund(BaseModel):
    confirmar_restitucion:bool=False
    referencia:str=Field(default='',max_length=100)
class Device(BaseModel):token:str=Field(min_length=20,max_length=4096)

def public(row):
    result=dict(row);result['diferencia_pagada']=bool(result.pop('pago_diferencia',None));return result

@router.post('/cambios',status_code=201)
def request_change(data:RequestChange,_=Depends(get_current_user),cur=Depends(get_db)):
    return public(service.request_change(cur,data))

@router.get('/cambios')
def changes(limit:int=Query(default=50,ge=1,le=100),offset:int=Query(default=0,ge=0),_=Depends(get_current_user),cur=Depends(get_db)):
    cur.execute('SELECT * FROM cambio ORDER BY id_cambio DESC LIMIT %s OFFSET %s',(limit,offset));return [public(r) for r in cur.fetchall()]

@router.get('/cambios/elegibles')
def eligible(_=Depends(get_current_user),cur=Depends(get_db)):
    cur.execute('''SELECT v.id_venta,v.id_sucursal,d.id_variante_prenda,p.nombre,t.nombre AS talla,c.nombre AS color,d.cantidad,d.precio_unitario,v.fecha_entrega
    FROM venta v JOIN detalle_venta d USING(id_venta) JOIN variante_prenda vp USING(id_variante_prenda)
    JOIN prenda p USING(id_prenda) LEFT JOIN talla t USING(id_talla) LEFT JOIN color c USING(id_color)
    WHERE v.fecha_entrega>=now()-interval '7 days' AND p.admite_cambio
    ORDER BY v.id_venta DESC LIMIT 100''');return cur.fetchall()

@router.get('/cambios/reemplazos/{branch_id}')
def replacement_options(branch_id:int,_=Depends(staff),cur=Depends(get_db)):
    from app.services.commerce import authorized_branch
    authorized_branch(cur,branch_id)
    cur.execute('''SELECT v.id_variante_prenda,p.nombre,t.nombre AS talla,c.nombre AS color,i.stock
    FROM inventario_catalogo i JOIN variante_prenda v USING(id_variante_prenda) JOIN prenda p USING(id_prenda)
    LEFT JOIN talla t USING(id_talla) LEFT JOIN color c USING(id_color)
    WHERE i.id_sucursal=%s AND i.stock>0 AND p.estado='Activo' ORDER BY p.nombre LIMIT 200''',(branch_id,));return cur.fetchall()

@router.get('/cambios/{change_id}')
def get_change(change_id:int,_=Depends(get_current_user),cur=Depends(get_db)):return public(service.get_change(cur,change_id))

@router.post('/cambios/{change_id}/recibir')
def receive(change_id:int,data:Receive,_=Depends(staff),cur=Depends(get_db)):return public(service.receive(cur,change_id,data.aceptada))

@router.put('/cambios/{change_id}/reemplazo')
def replacement(change_id:int,data:Replacement,_=Depends(staff),cur=Depends(get_db)):return public(service.replacement(cur,change_id,data.id_variante_prenda))

@router.post('/cambios/{change_id}/pago')
def pay(change_id:int,_=Depends(get_current_user),cur=Depends(get_db)):return service.payment_session(cur,change_id)

@router.post('/cambios/{change_id}/cancelar')
def cancel(change_id:int,_=Depends(get_current_user),cur=Depends(get_db)):return public(service.cancel(cur,change_id))

@router.post('/cambios/{change_id}/reembolsar')
def refund(change_id:int,data:Refund,_=Depends(staff),cur=Depends(get_db)):return public(service.refund(cur,change_id,data.confirmar_restitucion,data.referencia))

@router.post('/cambios/{change_id}/entregar')
def deliver(change_id:int,_=Depends(staff),cur=Depends(get_db)):return public(service.deliver(cur,change_id))

@router.get('/notificaciones')
def notifications(_=Depends(get_current_user),cur=Depends(get_db)):
    cur.execute('SELECT id_notificacion,titulo,mensaje,id_cambio,leida,created_at FROM notificacion ORDER BY id_notificacion DESC LIMIT 100');return cur.fetchall()

@router.patch('/notificaciones/{notification_id}/leida')
def read_notification(notification_id:int,_=Depends(get_current_user),cur=Depends(get_db)):
    cur.execute('UPDATE notificacion SET leida=true WHERE id_notificacion=%s RETURNING id_notificacion',(notification_id,));row=cur.fetchone()
    if not row:raise HTTPException(404,'Notificación no encontrada.')
    return row

@router.post('/dispositivos/push')
def register_device(data:Device,_=Depends(get_current_user),cur=Depends(get_db)):
    cur.execute('SELECT bind_push_device(%s)',(data.token,));return {'registrado':True}

@router.delete('/dispositivos/push')
def delete_device(data:Device,_=Depends(get_current_user),cur=Depends(get_db)):
    cur.execute('DELETE FROM dispositivo_push WHERE id_usuario=%s AND token=%s',(require_context().user_id,data.token));return {'retirado':True}
