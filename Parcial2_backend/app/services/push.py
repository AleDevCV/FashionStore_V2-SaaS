"""Outbox persistente. Un push nunca sustituye a la notificación consultable."""
import asyncio,hashlib,logging,os
from pathlib import Path
from datetime import timedelta
from functools import lru_cache
from psycopg2.extras import RealDictCursor
from app.database import get_connection
from app.tenant import TenantContext,context
log=logging.getLogger('fashionstore.push')

def configured():return bool(os.getenv('FIREBASE_CREDENTIALS_FILE')) and Path(os.environ['FIREBASE_CREDENTIALS_FILE']).is_file()

@lru_cache(maxsize=1)
def client():
    import firebase_admin
    from firebase_admin import credentials
    try:return firebase_admin.get_app('fashionstore-p2')
    except ValueError:return firebase_admin.initialize_app(credentials.Certificate(os.environ['FIREBASE_CREDENTIALS_FILE']),{'httpTimeout':10},name='fashionstore-p2')

def send(message,tokens,notification_id):
    from firebase_admin import messaging
    # El aviso de pantalla bloqueada no contiene importes, correo ni información de compra.
    value=messaging.MulticastMessage(notification=messaging.Notification(title=message,body='Tiene novedades en una solicitud. Abra FashionStore para consultar el detalle y cualquier diferencia pendiente.'),data={'notification_id':str(notification_id),'screen':'cambios'},tokens=tokens)
    return messaging.send_each_for_multicast(value,app=client()).responses

def tenant_batch(tenant_id):
    marker=context.set(TenantContext(tenant_id,role='Servicio push'))
    try:
        with get_connection() as conn,conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT pg_try_advisory_xact_lock(%s)",(82000000+tenant_id,))
            if not cur.fetchone()['pg_try_advisory_xact_lock']:return
            cur.execute("SELECT * FROM notificacion WHERE NOT push_enviado AND created_at>now()-interval '7 days' ORDER BY id_notificacion LIMIT 5 FOR UPDATE SKIP LOCKED");notifications=cur.fetchall()
            for note in notifications:
                cur.execute('SELECT d.token FROM dispositivo_push d JOIN usuario u USING(tenant_id,id_usuario) JOIN cliente c ON c.tenant_id=u.tenant_id AND lower(c.correo)=lower(u.correo) WHERE c.id_cliente=%s AND u.estado=\'Activo\' ORDER BY d.created_at DESC LIMIT 20',(note['id_cliente'],));tokens=[r['token'] for r in cur.fetchall()]
                pending=[]
                for token in tokens:
                    digest=hashlib.sha256(token.encode()).hexdigest()
                    cur.execute('INSERT INTO push_entrega(id_notificacion,token_hash) VALUES(%s,%s) ON CONFLICT DO NOTHING',(note['id_notificacion'],digest))
                    cur.execute('SELECT enviado,intentos,proximo_intento<=now() AS listo FROM push_entrega WHERE id_notificacion=%s AND token_hash=%s',(note['id_notificacion'],digest));delivery=cur.fetchone()
                    if not delivery['enviado'] and delivery['listo']:pending.append((token,digest,delivery['intentos']))
                if not pending:continue
                try:responses=send(note['titulo'],[r[0] for r in pending],note['id_notificacion'])
                except Exception as exc:
                    log.warning('Envío push pendiente: %s',type(exc).__name__)
                    for token,digest,attempts in pending:cur.execute("UPDATE push_entrega SET intentos=intentos+1,proximo_intento=now()+%s,ultimo_estado='proveedor_no_disponible' WHERE id_notificacion=%s AND token_hash=%s",(timedelta(seconds=min(3600,30*2**min(attempts,7))),note['id_notificacion'],digest))
                    continue
                for (token,digest,attempts),response in zip(pending,responses):
                    state='enviado' if response.success else type(response.exception).__name__
                    cur.execute('UPDATE push_entrega SET enviado=%s,intentos=intentos+1,proximo_intento=now()+%s,ultimo_estado=%s WHERE id_notificacion=%s AND token_hash=%s',(response.success,timedelta(seconds=min(3600,30*2**min(attempts,7))),state,note['id_notificacion'],digest))
                    if state=='UnregisteredError':cur.execute('DELETE FROM dispositivo_push WHERE token=%s',(token,))
                cur.execute('UPDATE notificacion SET intentos=intentos+1,push_enviado=NOT EXISTS(SELECT 1 FROM push_entrega WHERE id_notificacion=%s AND NOT enviado) WHERE id_notificacion=%s',(note['id_notificacion'],note['id_notificacion']))
    finally:context.reset(marker)

def dispatch():
    if not configured():return
    with get_connection() as conn,conn.cursor() as cur:
        cur.execute('SELECT id_empresa FROM empresa WHERE activa AND NOT plataforma ORDER BY id_empresa LIMIT 100');tenants=[r[0] for r in cur.fetchall()]
    for tenant_id in tenants:tenant_batch(tenant_id)

async def loop(stop):
    while not stop.is_set():
        try:await asyncio.to_thread(dispatch)
        except Exception as exc:log.warning('Cola push pendiente: %s',type(exc).__name__)
        try:await asyncio.wait_for(stop.wait(),timeout=30)
        except asyncio.TimeoutError:pass
