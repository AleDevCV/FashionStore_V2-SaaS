"""CU01/CU02: acceso global por correo, recuperación y elección de tienda del comprador."""
from collections import OrderedDict
import hashlib
import secrets
import threading
import time
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from psycopg2 import errors
from psycopg2.extras import Json
from app.schemas.auth import (SolicitudLogin, RespuestaToken, SolicitudRecuperarPassword,
    SolicitudVerificarToken, SolicitudRestablecerPassword)
from app.schemas.cliente import RegistroClientePeticion
from app.services.auth_service import verificar_password, generar_hash_password
from app.services.email_service import enviar_correo_recuperacion
from app.services import identity

router = APIRouter(tags=['Identidad y acceso global'])
_HASH_SENUELO = '$2b$12$zZo3V7AI.OyS0Nr3B.46Rev0BJawpm/pc9jSjS4u5anr.uEAleZX6'
_failed = OrderedDict()
_attempt_lock = threading.Lock()

def session_account(request):
    account = getattr(request.state, 'identity', None)
    if not account:
        raise HTTPException(401, 'Debe iniciar sesión.')
    return account

@router.post('/login', response_model=RespuestaToken)
@router.post('/login/', response_model=RespuestaToken, include_in_schema=False)
def iniciar_sesion(credenciales: SolicitudLogin, request: Request):
    email = str(credenciales.correo).strip().lower()
    key = (request.client.host if request.client else '', hashlib.sha256(email.encode()).hexdigest())
    now = time.monotonic()
    with _attempt_lock:
        count, start = _failed.get(key, (0, now))
        if now-start > 60:
            count, start = 0, now
        if count >= 8:
            raise HTTPException(429, 'Demasiados intentos. Espere un minuto.', headers={'Retry-After': '60'})
    account = identity.lookup(email=email)
    valid = verificar_password(credenciales.password, account['password_hash'] if account else _HASH_SENUELO)
    if not account or not valid:
        with identity.cursor() as cur:
            cur.execute('SELECT identity_event(%s,%s)', (account['id'] if account else None, 'LOGIN_FALLIDO'))
        with _attempt_lock:
            _failed[key] = (count+1, start)
            _failed.move_to_end(key)
            while len(_failed) > 4096:
                _failed.popitem(last=False)
        raise HTTPException(401, 'Credenciales incorrectas', headers={'WWW-Authenticate': 'Bearer'})
    if account['estado'] != 'Activo' or (account['tipo'] != 'CLIENTE' and (not account.get('empresa_activa') or account.get('local_estado')!='Activo')):
        raise HTTPException(403, 'Cuenta o empresa no disponible.')
    with _attempt_lock:
        _failed.pop(key, None)
    with identity.cursor() as cur:
        cur.execute('SELECT identity_event(%s,%s)', (account['id'], 'LOGIN_EXITOSO'))
    return RespuestaToken(access_token=identity.token(account), token_type='bearer')

@router.get('/tiendas')
def stores():
    with identity.cursor() as cur:
        cur.execute('SELECT id_empresa,slug,nombre FROM empresa WHERE activa AND NOT plataforma ORDER BY nombre LIMIT 500')
        return cur.fetchall()

class StoreChoice(BaseModel):
    empresa: str = Field(pattern=r'^[a-z0-9][a-z0-9-]{1,60}$')

@router.post('/auth/seleccionar-tienda', response_model=RespuestaToken)
def choose_store(data: StoreChoice, request: Request):
    return RespuestaToken(access_token=identity.select_store(session_account(request), data.empresa), token_type='bearer')

@router.get('/cuenta/compras')
def purchases(request: Request):
    return identity.purchases(session_account(request))

@router.get('/cuenta/perfil')
def profile(request: Request):
    account = session_account(request)
    return {key: account.get(key) for key in ('id','correo','nombre','apellido','telefono','correo_recuperacion','tipo')}

@router.post('/auth/registro', status_code=201)
@router.post('/auth/registro/', status_code=201, include_in_schema=False)
def register(data: RegistroClientePeticion):
    values = data.model_dump(mode='json')
    values['password_hash'] = generar_hash_password(values.pop('password'))
    try:
        with identity.cursor() as cur:
            cur.execute('SELECT identity_register(%s) AS id', (Json(values),))
            aid = cur.fetchone()['id']
    except errors.UniqueViolation:
        raise HTTPException(409, 'El correo ya está registrado. Inicie sesión o recupere su contraseña.')
    account = identity.lookup(account_id=aid)
    return {'mensaje': 'Cuenta creada. Puede comprar en todas las tiendas.', 'id_cliente': None,
            'id_usuario': aid, 'nombre_completo': (account['nombre']+' '+account['apellido']).strip(),
            'correo': account['correo'], 'rol': 'Cliente', 'access_token': identity.token(account), 'token_type': 'bearer'}

@router.post('/auth/recuperar-password')
@router.post('/auth/recuperar-password/', include_in_schema=False)
def solicitar_recuperacion_password(data: SolicitudRecuperarPassword):
    account = identity.lookup(email=str(data.correo))
    if account and account['estado'] == 'Activo':
        raw = secrets.token_urlsafe(32)
        with identity.cursor() as cur:
            cur.execute('SELECT identity_reset_issue(%s,%s)', (account['id'], hashlib.sha256(raw.encode()).hexdigest()))
        enviar_correo_recuperacion(account.get('correo_recuperacion') or account['correo'], account['nombre'], raw)
    return {'mensaje': 'Si la cuenta existe, recibirá instrucciones para recuperar su contraseña.'}

@router.post('/auth/verificar-token-recuperacion')
@router.post('/auth/verificar-token-recuperacion/', include_in_schema=False)
def verificar_token_recuperacion(data: SolicitudVerificarToken):
    with identity.cursor() as cur:
        cur.execute('SELECT identity_reset_lookup(%s) AS data', (hashlib.sha256(data.token.strip().encode()).hexdigest(),))
        value = cur.fetchone()['data']
    valid = bool(value and value['valido'])
    email = value['correo'].split('@') if valid else None
    return {'valido': valid, 'correo': email[0][:2]+'***@'+email[1] if email else None,
            'mensaje': 'Token válido.' if valid else 'Token inválido, usado o vencido.'}

@router.post('/auth/restablecer-password')
@router.post('/auth/restablecer-password/', include_in_schema=False)
def restablecer_password(data: SolicitudRestablecerPassword):
    with identity.cursor() as cur:
        cur.execute('SELECT identity_reset_apply(%s,%s) AS done',
                    (hashlib.sha256(data.token.strip().encode()).hexdigest(), generar_hash_password(data.nueva_password)))
        if not cur.fetchone()['done']:
            raise HTTPException(400, 'Token inválido, usado o vencido.')
    return {'mensaje': 'Contraseña restablecida. Inicie sesión de nuevo.'}
