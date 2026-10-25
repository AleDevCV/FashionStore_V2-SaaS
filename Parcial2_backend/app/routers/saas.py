"""CU 01 a 05: contexto y administración de empresas, planes y suscripciones."""
from datetime import datetime, timedelta, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, EmailStr
from app.database import get_db
from app.tenant import require_context
from app.services.auth_service import get_current_user, generar_hash_password

router=APIRouter(tags=['SaaS'])

class CompanyCreate(BaseModel):
    nombre: str=Field(min_length=2,max_length=150)
    slug: str=Field(pattern=r'^[a-z0-9][a-z0-9-]{1,60}$')
    correo_admin: EmailStr
    password_admin: str=Field(min_length=12,max_length=72)
    id_plan: int=Field(gt=0)

class PlanEdit(BaseModel):
    max_sucursales: int=Field(gt=0,le=1000)
    reportes_ia: bool

class SubscriptionEdit(BaseModel):
    id_plan: int=Field(gt=0)
    inicio: datetime
    vencimiento: datetime

def platform_user(user=Depends(get_current_user)):
    tenant=require_context()
    if not tenant.platform or user.get('rol')!='Administrador':
        raise HTTPException(403,'Se requiere administración de plataforma.')
    return user

def initialize_company(cur,tenant_id,email,password,plan_id):
    """Provisiona dentro de la transacción del alta, usando el contexto nuevo."""
    cur.execute("SELECT set_config('app.tenant_id',%s,true)",(str(tenant_id),))
    cur.execute("INSERT INTO suscripcion(tenant_id,id_plan,inicio,vencimiento) VALUES(%s,%s,now(),now()+interval '30 days')",(tenant_id,plan_id))
    roles=['Administrador','Encargado de Sucursal','Cajero (POS)','Cliente']
    role_ids=[]
    for name in roles:
        cur.execute('INSERT INTO rol(nombre,descripcion) VALUES(%s,%s) RETURNING id_rol',(name,'Rol de empresa'));role_ids.append(cur.fetchone()['id_rol'])
    from app.permissions import provision_permissions
    provision_permissions(cur,dict(zip(roles,role_ids)))
    cur.execute("INSERT INTO usuario(nombre,apellido,correo,password_hash,id_role) VALUES('Administrador','Empresa',%s,%s,%s) RETURNING id_usuario",(email,generar_hash_password(password),role_ids[0]))
    admin=cur.fetchone()['id_usuario']
    from app.services.identity import index_user
    index_user(cur, admin)
    cur.execute("INSERT INTO cliente(ci,nombre_completo) VALUES('MOSTRADOR','Cliente Mostrador')")
    return admin

@router.get('/contexto')
def session_context(user=Depends(get_current_user),cur=Depends(get_db)):
    ctx=require_context()
    cur.execute('SELECT id_empresa,slug,nombre,plataforma FROM empresa WHERE id_empresa=%s',(ctx.tenant_id,));company=dict(cur.fetchone())
    cur.execute('SELECT s.*,p.nombre AS plan,p.max_sucursales,p.reportes_ia, now() BETWEEN s.inicio AND s.vencimiento AS vigente FROM suscripcion s JOIN plan p USING(id_plan)');subscription=cur.fetchone()
    if ctx.role in {'Administrador','Cliente'}:cur.execute('SELECT id_sucursal,nombre FROM sucursal WHERE activa ORDER BY nombre')
    else:cur.execute('SELECT s.id_sucursal,s.nombre FROM sucursal s JOIN usuario_sucursal us USING(tenant_id,id_sucursal) WHERE us.id_usuario=%s AND s.activa ORDER BY s.nombre',(ctx.user_id,))
    branches=cur.fetchall()
    return {'empresa':company,'usuario':user,'sucursales':branches,'suscripcion':subscription,'offline_hasta':min(datetime.now(timezone.utc)+timedelta(hours=24),subscription['vencimiento']) if subscription else None}

@router.post('/logout')
def logout(user=Depends(get_current_user),cur=Depends(get_db)):
    ctx=require_context()
    if ctx.account_id:
        cur.execute('SELECT identity_revoke(%s)',(ctx.account_id,))
    cur.execute('UPDATE usuario SET token_version=token_version+1 WHERE id_usuario=%s',(user['id_usuario'],))
    return {'mensaje':'Sesiones revocadas. Las operaciones locales se conservan.'}

@router.get('/empresas')
def companies(_=Depends(platform_user),cur=Depends(get_db)):
    cur.execute('SELECT id_empresa,slug,nombre,activa FROM empresa WHERE NOT plataforma ORDER BY id_empresa')
    return cur.fetchall()

@router.post('/empresas',status_code=201)
def create_company(data:CompanyCreate,_=Depends(platform_user),cur=Depends(get_db)):
    cur.execute('SELECT id_plan FROM plan WHERE id_plan=%s',(data.id_plan,))
    if not cur.fetchone():raise HTTPException(404,'Plan no encontrado.')
    cur.execute('SELECT 1 FROM empresa WHERE slug=%s',(data.slug,))
    if cur.fetchone():raise HTTPException(409,'Identificador de empresa ya utilizado.')
    cur.execute('INSERT INTO empresa(nombre,slug) VALUES(%s,%s) RETURNING id_empresa',(data.nombre,data.slug));tid=cur.fetchone()['id_empresa']
    admin=initialize_company(cur,tid,str(data.correo_admin),data.password_admin,data.id_plan)
    return {'id_empresa':tid,'id_admin':admin,'slug':data.slug}

@router.patch('/empresas/{tenant_id}')
def company_state(tenant_id:int,activa:bool,_=Depends(platform_user),cur=Depends(get_db)):
    cur.execute('UPDATE empresa SET activa=%s WHERE id_empresa=%s AND NOT plataforma RETURNING id_empresa,activa',(activa,tenant_id))
    row=cur.fetchone()
    if not row:raise HTTPException(404,'Empresa no encontrada.')
    return row

@router.get('/planes')
def plans(_=Depends(get_current_user),cur=Depends(get_db)):
    cur.execute('SELECT * FROM plan ORDER BY id_plan');return cur.fetchall()

@router.patch('/planes/{plan_id}')
def edit_plan(plan_id:int,data:PlanEdit,_=Depends(platform_user),cur=Depends(get_db)):
    # SERIALIZABLE por bloqueo del plan y empresas al modificar límites.
    cur.execute('SELECT id_plan FROM plan WHERE id_plan=%s FOR UPDATE',(plan_id,))
    if not cur.fetchone():raise HTTPException(404,'Plan no encontrado.')
    cur.execute('UPDATE plan SET max_sucursales=%s,reportes_ia=%s WHERE id_plan=%s RETURNING *',(data.max_sucursales,data.reportes_ia,plan_id));return cur.fetchone()

@router.get('/suscripciones/{tenant_id}')
def get_subscription(tenant_id:int,user=Depends(get_current_user),cur=Depends(get_db)):
    ctx=require_context()
    if not ctx.platform and (tenant_id!=ctx.tenant_id or ctx.role!='Administrador'):raise HTTPException(403,'Acceso no autorizado.')
    if ctx.platform:
        if ctx.role!='Administrador':raise HTTPException(403,'Acceso no autorizado.')
        cur.execute("SELECT set_config('app.tenant_id',%s,true)",(str(tenant_id),))
    cur.execute('SELECT s.*,p.nombre,p.max_sucursales,p.reportes_ia FROM suscripcion s JOIN plan p USING(id_plan) WHERE s.tenant_id=%s',(tenant_id,));row=cur.fetchone()
    if not row:raise HTTPException(404,'Suscripción no encontrada.')
    return row

@router.put('/suscripciones/{tenant_id}')
def edit_subscription(tenant_id:int,data:SubscriptionEdit,_=Depends(platform_user),cur=Depends(get_db)):
    if data.inicio.tzinfo is None or data.vencimiento.tzinfo is None or data.vencimiento<=data.inicio:
        raise HTTPException(422,'Fechas con zona horaria y vencimiento posterior al inicio requeridos.')
    cur.execute('SELECT id_empresa FROM empresa WHERE id_empresa=%s AND NOT plataforma FOR UPDATE',(tenant_id,))
    if not cur.fetchone():raise HTTPException(404,'Empresa no encontrada.')
    cur.execute('SELECT max_sucursales FROM plan WHERE id_plan=%s FOR SHARE',(data.id_plan,));plan=cur.fetchone()
    if not plan:raise HTTPException(404,'Plan no encontrado.')
    cur.execute("SELECT set_config('app.tenant_id',%s,true)",(str(tenant_id),))
    cur.execute('SELECT count(*) AS n FROM sucursal WHERE activa');n=cur.fetchone()['n']
    if n>plan['max_sucursales']:raise HTTPException(409,'Desactive sucursales antes de reducir el plan.')
    cur.execute('INSERT INTO suscripcion(tenant_id,id_plan,inicio,vencimiento) VALUES(%s,%s,%s,%s) ON CONFLICT(tenant_id) DO UPDATE SET id_plan=excluded.id_plan,inicio=excluded.inicio,vencimiento=excluded.vencimiento RETURNING *',(tenant_id,data.id_plan,data.inicio,data.vencimiento))
    return cur.fetchone()
