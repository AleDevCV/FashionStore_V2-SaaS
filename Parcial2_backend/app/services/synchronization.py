"""Una transacción por operación; UUID, respuesta y movimientos son atómicos."""
import hashlib,json,os
from datetime import datetime,timedelta,timezone
from decimal import Decimal
from fastapi import HTTPException
from jose import jwt,JWTError
from psycopg2.extras import RealDictCursor,Json
from pydantic import ValidationError
from app.database import get_connection
from app.tenant import require_context
from app.permissions import allowed
from app.services.commerce import authorized_branch,reserve,money

def process_raw(raw,supervision_reason=''):
    from app.schemas.offline import Operation
    from uuid import UUID
    try:op=Operation.model_validate(raw)
    except ValidationError:
        try:oid=str(UUID(str(raw.get('operation_id'))))
        except (ValueError,TypeError):return {'operation_id':raw.get('operation_id'),'state':'RECHAZADA','reason':'Identificador UUID o estructura de operación inválidos.'}
        ctx=require_context();digest=hashlib.sha256(('invalid:'+json.dumps(raw,sort_keys=True,separators=(',',':'),ensure_ascii=False)).encode()).hexdigest()
        with get_connection() as conn,conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,0))',(f'{ctx.tenant_id}:{oid}',))
            cur.execute('SELECT author_id,payload_hash,result FROM operacion_sync WHERE operation_id=%s',(oid,));existing=cur.fetchone()
            if existing:
                if existing['author_id']!=ctx.user_id and not allowed(cur,'conflictos.resolver'):raise HTTPException(404,'Operación no encontrada.')
                if existing['payload_hash']==digest:return existing['result']
                return {'operation_id':oid,'state':'RECHAZADA','reason':'UUID reutilizado con contenido diferente. Consulte el resultado original.'}
            result={'operation_id':oid,'state':'RECHAZADA','reason':'Contrato inválido: revise versión, fecha con zona horaria, importes y detalles.'}
            try:device=str(UUID(str(raw.get('device_id'))))
            except (ValueError,TypeError):device='00000000-0000-0000-0000-000000000000'
            cur.execute('INSERT INTO operacion_sync(operation_id,author_id,branch_id,device_id,kind,payload_hash,envelope,state,result) VALUES(%s,%s,NULL,%s,%s,%s,%s,%s,%s)',(oid,ctx.user_id,device,'reserva' if raw.get('kind')=='reserva' else 'venta',digest,Json(raw),'RECHAZADA',Json(result)))
            cur.execute("INSERT INTO bitacora(id_usuario,accion,tabla_afectada,detalle) VALUES(%s,'SYNC_RECHAZADA','operacion_sync',%s)",(ctx.user_id,oid))
            return result
    return process(op,supervision_reason)

def subscription(cur):
    cur.execute('SELECT s.vencimiento,now() BETWEEN s.inicio AND s.vencimiento AS vigente FROM suscripcion s')
    row=cur.fetchone()
    if not row or not row['vigente']:raise HTTPException(409,'Suscripción no vigente; conserve la operación y gestione renovación.')
    return row

def issue_lease(cur,branch):
    ctx=require_context();sub=subscription(cur);now=datetime.now(timezone.utc)
    payload={'token_use':'offline','tenant_id':ctx.tenant_id,'author_id':ctx.user_id,'branches':[branch],
     'can_sell':allowed(cur,'pos.vender') and allowed(cur,'offline.operar'),'iat':int(now.timestamp()),
     'exp':int(min(now+timedelta(hours=24),sub['vencimiento']).timestamp())}
    token=jwt.encode(payload,os.environ['SECRET_KEY'],algorithm=os.getenv('JWT_ALGORITHM','HS256'))
    return token,payload

def verify_lease(op):
    try:
        claims=jwt.decode(op.lease,os.environ['SECRET_KEY'],algorithms=[os.getenv('JWT_ALGORITHM','HS256')],options={'verify_exp':False})
        if claims.get('token_use')!='offline' or claims['tenant_id']!=op.tenant_id or claims['author_id']!=op.author_id or op.branch_id not in claims['branches']:raise ValueError('identity')
        stamp=op.occurred_at.timestamp()
        if stamp<claims['iat']-300 or stamp>claims['exp'] or stamp>datetime.now(timezone.utc).timestamp()+300:raise ValueError('time')
        return claims
    except (JWTError,ValueError,KeyError,TypeError):raise HTTPException(422,'Permiso offline inválido o registro fuera de su vigencia.')

def process(op,supervision_reason=''):
    ctx=require_context();envelope=op.model_dump(mode='json');oid=str(op.operation_id)
    digest=hashlib.sha256(json.dumps(envelope,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
    with get_connection() as conn,conn.cursor(cursor_factory=RealDictCursor) as cur:
        # El bloqueo dura hasta commit/rollback; también serializa UUID aún no insertados.
        cur.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,0))',(f'{ctx.tenant_id}:{oid}',))
        cur.execute('SELECT * FROM operacion_sync WHERE operation_id=%s',(oid,));existing=cur.fetchone()
        if existing:
            if existing['author_id']!=ctx.user_id and not allowed(cur,'conflictos.resolver'):raise HTTPException(404,'Operación no encontrada.')
            if existing['payload_hash']!=digest:return {'operation_id':oid,'state':'RECHAZADA','reason':'UUID reutilizado con contenido diferente. Consulte el resultado original.'}
            return existing['result']
        author=ctx.user_id;branch=None;revision=False
        cur.execute('SAVEPOINT operation_business')
        try:
            if ctx.platform or ctx.tenant_id!=op.tenant_id:raise HTTPException(422,'La operación no pertenece a la empresa autenticada.')
            lease=verify_lease(op)
            if op.author_id!=ctx.user_id:
                if not allowed(cur,'conflictos.resolver') or len(supervision_reason.strip())<6:raise HTTPException(422,'La recuperación de otra cuenta requiere supervisión explícita.')
                cur.execute('SELECT id_usuario FROM usuario WHERE id_usuario=%s',(op.author_id,))
                if not cur.fetchone():raise HTTPException(422,'El autor original no pertenece a la empresa.')
            author=op.author_id
            authorized_branch(cur,op.branch_id,allow_customer=op.kind=='reserva');branch=op.branch_id
            subscription(cur)
            if op.original_operation:
                cur.execute('SELECT * FROM operacion_sync WHERE operation_id=%s FOR UPDATE',(str(op.original_operation),));original=cur.fetchone()
                if not original or original['state']=='CONFIRMADA' or original['resolved_at'] is not None:raise HTTPException(409,'La operación original no admite una nueva revisión.')
                if original['author_id']!=ctx.user_id and not allowed(cur,'conflictos.resolver'):raise HTTPException(403,'No puede revisar una operación ajena.')
                if original['kind']!=op.kind or original['branch_id']!=op.branch_id:raise HTTPException(409,'La revisión debe conservar el tipo y la sucursal originales.')
                if op.kind=='venta' and Decimal(original['envelope']['cash_received'])!=op.cash_received:raise HTTPException(409,'Conserve el efectivo realmente recibido; registre por separado su compensación.')
                revision=True
            lines=[x.model_dump() for x in op.items]
            if op.kind=='venta':
                if not lease.get('can_sell') or not allowed(cur,'pos.vender') or not allowed(cur,'offline.operar'):raise HTTPException(403,'Los permisos actuales no permiten confirmar esta venta offline.')
                if op.cash_received is None:raise HTTPException(422,'Debe conservar el efectivo realmente recibido.')
                from app.schemas.pos import POSVentaCrear
                from app.services.pos_service import procesar_venta_pos
                try:data=POSVentaCrear(id_sucursal=op.branch_id,id_cliente=op.customer_id,items=lines,metodo_pago='Efectivo',monto_recibido=op.cash_received)
                except ValidationError:raise HTTPException(422,'El efectivo no cubre el total o los detalles de la venta son inválidos.')
                value=procesar_venta_pos(cur,data,author,'offline')
                result={'operation_id':oid,'state':'CONFIRMADA','server_id':value['id_venta'],'kind':'venta','total':str(value['total']),'vuelto':str(money(op.cash_received)-money(value['total'])),'receipt_url':value.get('url_pdf')}
            else:
                if ctx.role!='Cliente' and not allowed(cur,'offline.operar'):raise HTTPException(403,'No tiene permiso para reservar offline.')
                if op.customer_id is None:raise HTTPException(422,'Seleccione un cliente previamente descargado.')
                rid=reserve(cur,op.customer_id,op.branch_id,lines,author)
                result={'operation_id':oid,'state':'CONFIRMADA','server_id':rid,'kind':'reserva'}
            cur.execute('RELEASE SAVEPOINT operation_business')
        except HTTPException as exc:
            cur.execute('ROLLBACK TO SAVEPOINT operation_business')
            cur.execute('RELEASE SAVEPOINT operation_business')
            # Referencias rechazadas no se incorporan como relaciones válidas.
            cur.execute('SELECT id_sucursal FROM sucursal WHERE id_sucursal=%s',(op.branch_id,));branch=op.branch_id if cur.fetchone() else None
            cur.execute('SELECT id_usuario FROM usuario WHERE id_usuario=%s',(author,));author=author if cur.fetchone() else ctx.user_id
            state='EN_CONFLICTO' if exc.status_code in {403,409} and branch is not None else 'RECHAZADA'
            result={'operation_id':oid,'state':state,'reason':str(exc.detail)}
        cur.execute('''INSERT INTO operacion_sync(operation_id,author_id,branch_id,device_id,kind,payload_hash,envelope,state,result,original_operation)
        VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',(oid,author,branch,str(op.device_id),op.kind,digest,Json(envelope),result['state'],Json(result),str(op.original_operation) if revision else None))
        if revision:
            cur.execute("UPDATE operacion_sync SET resolved_at=now(),resolved_by=%s,resolution='Revisada mediante nueva operación' WHERE operation_id=%s",(ctx.user_id,str(op.original_operation)))
        cur.execute("INSERT INTO bitacora(id_usuario,accion,tabla_afectada,detalle) VALUES(%s,'SYNC','operacion_sync',%s)",(ctx.user_id,json.dumps({'uuid':oid,'estado':result['state'],'supervision':bool(supervision_reason),'motivo_supervision':supervision_reason if op.author_id!=ctx.user_id else ''},ensure_ascii=False)))
        return result
