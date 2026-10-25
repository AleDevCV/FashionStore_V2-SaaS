"""Resuelve la empresa y valida sesiones antes de abrir servicios comerciales."""
import asyncio
import os
from dataclasses import replace
from fastapi.responses import JSONResponse
from app.tenant import TenantContext, context
from app.database import get_connection

def resolve(slug, claims):
    from psycopg2.extras import RealDictCursor
    with get_connection() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        if claims:
            cur.execute('SELECT * FROM empresa WHERE id_empresa=%s AND activa', (claims['tenant_id'],))
        else:
            cur.execute('SELECT * FROM empresa WHERE slug=%s AND activa', (slug,))
        company=cur.fetchone()
    if not company:return None
    tenant=TenantContext(company['id_empresa'],platform=company['plataforma'],slug=company['slug'])
    if claims:
        marker=context.set(tenant)
        try:
            with get_connection() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute('SELECT u.id_usuario,u.account_id,u.correo,u.estado,u.token_version,r.nombre AS rol FROM usuario u JOIN rol r ON r.id_rol=u.id_role WHERE u.id_usuario=%s',(claims['id_usuario'],))
                user=cur.fetchone()
            if not user or user['estado']!='Activo' or user['token_version']!=claims.get('token_version',0):return None
            if claims.get('account_id') and user['account_id']!=claims['account_id']:return None
            tenant=replace(tenant,user_id=user['id_usuario'],role=user['rol'],email=user['correo'],account_id=claims.get('account_id'))
        finally:context.reset(marker)
    return tenant

def subscription_active(tenant):
    marker=context.set(tenant)
    try:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute('SELECT 1 FROM suscripcion WHERE now() BETWEEN inicio AND vencimiento')
            return cur.fetchone() is not None
    finally:context.reset(marker)

async def tenant_middleware(request, call_next):
    from fastapi import HTTPException
    from app.services import identity
    path=request.url.path
    if request.method=='OPTIONS' or request.url.path in {'/health','/docs','/openapi.json','/redoc'}:
        return await call_next(request)
    public_identity={'/api/login','/api/login/','/api/auth/registro','/api/auth/registro/',
        '/api/auth/recuperar-password','/api/auth/recuperar-password/',
        '/api/auth/verificar-token-recuperacion','/api/auth/verificar-token-recuperacion/',
        '/api/auth/restablecer-password','/api/auth/restablecer-password/','/api/tiendas'}
    if path in public_identity:
        return await call_next(request)
    from app.services.auth_service import decodificar_token_acceso
    if request.url.path.endswith('/stripe/webhook'):
        import stripe
        secret=os.getenv('STRIPE_WEBHOOK_SECRET','')
        if not secret:return JSONResponse({'detail':'Webhook no configurado.'},status_code=503)
        try:
            event=stripe.Webhook.construct_event(await request.body(),request.headers.get('stripe-signature',''),secret,tolerance=300)
            tenant_id=int(event['data']['object']['metadata']['tenant_id'])
        except Exception:
            return JSONResponse({'detail':'Firma o contexto de webhook inválido.'},status_code=400)
        def signed_context():
            with get_connection() as conn,conn.cursor() as cur:
                cur.execute('SELECT slug FROM empresa WHERE id_empresa=%s AND activa',(tenant_id,));row=cur.fetchone()
            return resolve(row[0],None) if row else None
        tenant=await asyncio.to_thread(signed_context)
        if not tenant:return JSONResponse({'detail':'Empresa no disponible.'},status_code=404)
        marker=context.set(tenant)
        try:return await call_next(request)
        finally:context.reset(marker)
    authorization=request.headers.get('authorization','')
    claims=None
    if authorization:
        parts=authorization.split(' ',1)
        claims=decodificar_token_acceso(parts[1]) if len(parts)==2 and parts[0].lower()=='bearer' else None
        if not claims or (not claims.get('tenant_id') and not claims.get('account_id')) or not claims.get('id_usuario'):
            return JSONResponse({'detail':'Sesión inválida o expirada.'},status_code=401)
    global_paths={'/api/auth/seleccionar-tienda','/api/cuenta/perfil','/api/cuenta/compras'}
    if claims and claims.get('account_id'):
        try:
            account=await asyncio.to_thread(identity.validate_claims,claims)
        except HTTPException as error:
            return JSONResponse({'detail':error.detail},status_code=error.status_code)
        request.state.identity=account
        if path in global_paths or not claims.get('tenant_id'):
            marker=context.set(TenantContext(0,user_id=account['id'],role='Cliente' if account['tipo']=='CLIENTE' else '',email=account['correo'],account_id=account['id']))
            try:
                if path=='/api/contexto':return JSONResponse(identity.unbound_context(account))
                if path=='/api/logout':
                    def revoke():
                        with identity.cursor() as cur:cur.execute('SELECT identity_revoke(%s)',(account['id'],))
                    await asyncio.to_thread(revoke)
                    return JSONResponse({'mensaje':'Sesión global revocada. Sus pendientes se conservan.'})
                if path not in global_paths:
                    return JSONResponse({'detail':'Elija una tienda desde el catálogo para continuar.'},status_code=409)
                return await call_next(request)
            finally:context.reset(marker)
    elif path in global_paths:
        return JSONResponse({'detail':'Inicie sesión con su cuenta global.'},status_code=401)
    slug=request.headers.get('x-empresa') or request.query_params.get('empresa')
    if request.url.path.startswith('/api/catalogo/imagenes/'):
        parts=request.url.path.split('/')
        if len(parts)==6:slug=parts[4]
    if not claims and not slug:
        return JSONResponse({'detail':'Seleccione una empresa mediante X-Empresa.'},status_code=400)
    from psycopg2 import OperationalError
    from psycopg2.pool import PoolError
    try:tenant=await asyncio.to_thread(resolve,slug,claims)
    except (OperationalError,PoolError):return JSONResponse({'detail':'Servicio de datos temporalmente ocupado. Conserve la operación y reintente.'},status_code=503,headers={'Retry-After':'5'})
    if tenant is None:return JSONResponse({'detail':'Empresa o sesión no disponible.'},status_code=401 if claims else 404)
    path=request.url.path
    public_auth=path.startswith(('/api/login','/api/auth/')) or path=='/api/logout'
    settlement=path=='/api/reportes/convencional' or path.startswith(('/api/notificaciones','/api/dispositivos/push','/api/conflictos/')) or path.endswith(('/reembolsar','/cancelar'))
    if request.method not in {'GET','HEAD','OPTIONS'} and not public_auth and not settlement and not tenant.platform and not path.startswith('/api/sincronizacion'):
        if not await asyncio.to_thread(subscription_active,tenant):
            return JSONResponse({'detail':'Suscripción no vigente. Las operaciones locales se conservan.'},status_code=403)
    marker=context.set(tenant)
    try:
        request.state.tenant=tenant
        return await call_next(request)
    finally:context.reset(marker)
