"""Identidad global y perfiles empresariales; toda operación comercial mantiene RLS."""
from contextlib import contextmanager
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from psycopg2 import errors
from psycopg2.extras import RealDictCursor, Json
from app.database import get_connection
from app.tenant import context, TenantContext


@contextmanager
def cursor():
    with get_connection() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        yield cur


def lookup(email=None, account_id=None):
    with cursor() as cur:
        cur.execute('SELECT identity_lookup(%s,%s) AS data', (email, account_id))
        return cur.fetchone()['data']


def validate_claims(claims):
    account = lookup(account_id=claims.get('account_id'))
    if not account or account['estado'] != 'Activo' or account['token_version'] != claims.get('account_version'):
        raise HTTPException(401, 'Sesión inválida o revocada.')
    if account['tipo'] != 'CLIENTE' and (not account.get('empresa_activa') or account.get('local_estado')!='Activo' or account.get('tenant_id') != claims.get('tenant_id') or account.get('id_usuario') != claims.get('id_usuario')):
        raise HTTPException(401, 'Empresa o sesión no disponible.')
    return account


def token(account, profile=None):
    from app.services.auth_service import crear_token_acceso
    customer = account['tipo'] == 'CLIENTE'
    profile = profile or account
    tenant_id = (profile.get('tenant_id') or 0) if not customer or profile is not account else 0
    user_id = profile.get('id_usuario') if tenant_id else account['id']
    role = 'Cliente' if customer else account.get('rol')
    marker = context.set(TenantContext(tenant_id, user_id=user_id, role=role or '', email=account['correo'], account_id=account['id']))
    try:
        return crear_token_acceso({'account_id': account['id'], 'account_version': account['token_version'],
            'id_usuario': user_id, 'sub': str(account['id']), 'correo': account['correo'],
            'nombre': (account['nombre'] + ' ' + account['apellido']).strip(), 'rol': role,
            'tipo_cuenta': account['tipo'], 'empresa_slug': profile.get('slug') if tenant_id else None,
            'token_version': profile.get('local_version', 0) if tenant_id else 0})
    finally:
        context.reset(marker)


def index_user(cur, user_id):
    try:
        cur.execute('SELECT identity_index_user(%s)', (user_id,))
    except errors.UniqueViolation:
        raise HTTPException(409, 'El correo ya pertenece a una cuenta de FashionStore.')
    except errors.InsufficientPrivilege:
        raise HTTPException(403, 'La cuenta global del cliente solo puede administrarla su titular.')


def select_store(account, slug):
    if account['tipo'] != 'CLIENTE':
        raise HTTPException(403, 'El personal permanece en su empresa asignada.')
    marker = context.set(TenantContext(0, account_id=account['id']))
    try:
        with cursor() as cur:
            cur.execute('SELECT id_empresa,slug FROM empresa WHERE slug=%s AND activa AND NOT plataforma', (slug,))
            company = cur.fetchone()
            if not company:
                raise HTTPException(404, 'Tienda no disponible.')
            cur.execute('SELECT identity_customer_profile(%s,%s) AS id_usuario', (account['id'], company['id_empresa']))
            uid = cur.fetchone()['id_usuario']
            cur.execute("SELECT set_config('app.tenant_id',%s,true)", (str(company['id_empresa']),))
            cur.execute('SELECT token_version FROM usuario WHERE id_usuario=%s', (uid,))
            version = cur.fetchone()['token_version']
            return token(account, {'tenant_id': company['id_empresa'], 'id_usuario': uid, 'slug': slug, 'local_version': version})
    except errors.InsufficientPrivilege:
        raise HTTPException(403, 'Cuenta o tienda no disponible para esta operación.')
    finally:
        context.reset(marker)


def unbound_context(account):
    return {'empresa': None, 'usuario': {'id_usuario': account['id'], 'account_id': account['id'],
            'correo': account['correo'], 'nombre': account['nombre'], 'apellido': account['apellido'],
            'rol': 'Cliente', 'tipo_cuenta': 'CLIENTE'}, 'sucursales': [], 'suscripcion': None,
            'offline_hasta': None, 'seleccionar_tienda': True}


def purchases(account):
    if account['tipo'] != 'CLIENTE':
        raise HTTPException(403, 'Esta vista corresponde al comprador.')
    # Cada lectura comercial se realiza con tenant, usuario y correo del titular.
    with cursor() as cur:
        cur.execute('SELECT id_empresa,slug,nombre FROM empresa WHERE NOT plataforma ORDER BY id_empresa LIMIT 500')
        companies = cur.fetchall()
    output = []
    for company in companies:
        marker = context.set(TenantContext(company['id_empresa'], role='Cliente', email=account['correo'], account_id=account['id']))
        try:
            with cursor() as cur:
                cur.execute("SELECT id_usuario FROM usuario WHERE account_id=%s AND estado='Activo'", (account['id'],))
                user = cur.fetchone()
                if not user:
                    continue
                cur.execute('''SELECT v.id_venta,v.fecha_venta,v.total,v.fecha_entrega FROM venta v
                    JOIN cliente c USING(id_cliente) WHERE lower(c.correo)=lower(%s) ORDER BY v.fecha_venta DESC LIMIT 100''', (account['correo'],))
                for row in cur.fetchall():
                    output.append({**dict(row), 'empresa': company['slug'], 'tienda': company['nombre']})
        finally:
            context.reset(marker)
    return output
