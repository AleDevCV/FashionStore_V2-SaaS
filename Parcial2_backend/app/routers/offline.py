from uuid import UUID
from fastapi import APIRouter,Depends,HTTPException,Query
from psycopg2.extras import Json
from app.database import get_db
from app.schemas.offline import Batch,Resolution
from app.services.auth_service import get_current_user
from app.services import synchronization as sync
from app.services.commerce import authorized_branch
from app.tenant import require_context,authenticated_context
from app.permissions import allowed,require_permission

router=APIRouter(tags=['Offline y sincronización'])

@router.get('/offline/catalogo')
def snapshot(branch_id:int=Query(gt=0),limit:int=Query(default=200,ge=1,le=500),operation_ids:list[UUID]=Query(default=[],max_length=50),_=Depends(get_current_user),cur=Depends(get_db)):
    ctx=require_context()
    if ctx.platform:raise HTTPException(403,'Seleccione una empresa comercial.')
    if ctx.role!='Cliente':require_permission(cur,'offline.operar')
    authorized_branch(cur,branch_id,allow_customer=True)
    lease,claims=sync.issue_lease(cur,branch_id)
    cur.execute('SELECT result,resolved_at,resolution,compensation FROM operacion_sync WHERE operation_id=ANY(%s::uuid[]) AND author_id=%s',([str(x) for x in operation_ids],ctx.user_id))
    known_results=[resolved_result(row) for row in cur.fetchall()]
    cur.execute('''SELECT v.id_variante_prenda,v.id_prenda,v.sku_variante,v.precio_adicional,p.sku,p.nombre,p.material,p.medidas,p.precio_base,p.precio_mayorista,p.umbral_mayorista,p.precio_oferta,p.oferta_inicio,p.oferta_fin,
    t.nombre AS talla,variant_color_label(v.id_variante_prenda) AS color,i.stock FROM inventario_catalogo i JOIN variante_prenda v USING(id_variante_prenda) JOIN prenda p USING(id_prenda)
    LEFT JOIN talla t USING(id_talla) LEFT JOIN color c USING(id_color)
    WHERE i.id_sucursal=%s AND p.estado='Activo' ORDER BY v.id_variante_prenda LIMIT %s''',(branch_id,limit));products=cur.fetchall()
    if ctx.role=='Cliente':cur.execute('SELECT id_cliente,nombre_completo,telefono FROM cliente WHERE lower(correo)=lower(%s) AND estado=\'Activo\'',(ctx.email,))
    else:cur.execute("SELECT id_cliente,nombre_completo,telefono FROM cliente WHERE estado='Activo' ORDER BY id_cliente LIMIT 200")
    customers=cur.fetchall()
    cur.execute('SELECT id_sucursal,nombre FROM sucursal WHERE id_sucursal=%s',(branch_id,));branch=cur.fetchone()
    from datetime import datetime,timezone
    return {'tenant_id':ctx.tenant_id,'author_id':ctx.user_id,'empresa':ctx.slug,'usuario':ctx.email,'lease':lease,'lease_expires':claims['exp'],'can_sell':claims['can_sell'],'branch':branch,'products':products,'customers':customers,'subset':True,'operation_results':known_results,'downloaded_at':datetime.now(timezone.utc)}

@router.post('/sincronizacion/lote')
def synchronize(data:Batch,_=Depends(authenticated_context)):
    return {'results':[sync.process_raw(op,data.supervision_reason) for op in data.operations]}

@router.get('/sincronizacion/operaciones/{operation_id}')
def operation_result(operation_id:UUID,_=Depends(get_current_user),cur=Depends(get_db)):
    cur.execute('SELECT author_id,result,resolved_at,resolution,compensation FROM operacion_sync WHERE operation_id=%s',(str(operation_id),));row=cur.fetchone()
    if not row or (row['author_id']!=require_context().user_id and not allowed(cur,'conflictos.resolver')):raise HTTPException(404,'Operación no encontrada.')
    return resolved_result(row)

def resolved_result(row):
    result=dict(row['result'])
    if row['resolved_at']:result.update(resolved=True,resolution=row['resolution'],compensation=row['compensation'])
    return result

@router.get('/conflictos')
def conflicts(_=Depends(get_current_user),cur=Depends(get_db)):
    require_permission(cur,'conflictos.resolver')
    cur.execute("SELECT operation_id,author_id,branch_id,kind,state,result,created_at,resolution,resolved_at FROM operacion_sync WHERE state IN ('EN_CONFLICTO','RECHAZADA') ORDER BY created_at DESC LIMIT 100");return cur.fetchall()

@router.post('/conflictos/{operation_id}/compensar')
def compensate(operation_id:UUID,data:Resolution,_=Depends(get_current_user),cur=Depends(get_db)):
    require_permission(cur,'conflictos.resolver')
    cur.execute('SELECT * FROM operacion_sync WHERE operation_id=%s FOR UPDATE',(str(operation_id),));row=cur.fetchone()
    if not row:raise HTTPException(404,'Operación no encontrada.')
    if row['state']=='CONFIRMADA':raise HTTPException(409,'Una operación confirmada se corrige mediante cambio o devolución.')
    if row['resolved_at'] is not None:raise HTTPException(409,'El conflicto ya fue resuelto.')
    from decimal import Decimal
    required=Decimal(str(row['envelope'].get('cash_received') or 0)) if row['kind']=='venta' else Decimal(0)
    if data.compensacion!=required:raise HTTPException(422,'La compensación debe restituir íntegramente el efectivo registrado; una reserva no tiene efectivo recibido.')
    if row['branch_id'] is not None:authorized_branch(cur,row['branch_id'])
    cur.execute('UPDATE operacion_sync SET resolved_by=%s,resolution=%s,compensation=%s,resolved_at=now() WHERE operation_id=%s',(require_context().user_id,data.motivo,data.compensacion,str(operation_id)))
    cur.execute("INSERT INTO bitacora(id_usuario,accion,tabla_afectada,detalle) VALUES(%s,'COMPENSAR','operacion_sync',%s)",(require_context().user_id,str(operation_id)))
    return {'operation_id':operation_id,'resuelto':True,'compensacion':data.compensacion}
