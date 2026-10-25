"""Cuentas de presentación autorizadas. Solo plataforma, demo-a y demo-b; claves del entorno privado."""
from pathlib import Path
import os
import re
import sys
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

ROOT=Path(__file__).resolve().parents[1]
load_dotenv(ROOT/'.env')
sys.path.insert(0,str(ROOT/'Parcial2_backend'))
from app.services.auth_service import generar_hash_password


def main():
    if os.environ['POSTGRES_DB']!='fashionstore_p2' and not re.fullmatch(r'fashionstore_p2_restore_[0-9]{14}',os.environ['POSTGRES_DB']):raise SystemExit('Las cuentas demo solo se preparan en P2 o en una copia explícita de restauración P2.')
    password=os.environ['DEMO_PASSWORD'];platform_password=os.environ['DEMO_PLATFORM_PASSWORD']
    accounts=[]
    with psycopg2.connect(host=os.getenv('MIGRATION_HOST','127.0.0.1'),port=os.getenv('MIGRATION_PORT','55433'),dbname=os.environ['POSTGRES_DB'],user=os.environ['POSTGRES_USER'],password=os.environ['POSTGRES_PASSWORD'],cursor_factory=RealDictCursor) as conn,conn.cursor() as cur:
        cur.execute('SELECT pg_advisory_xact_lock(82261025)')

        def update_local(uid,email,secret):
            cur.execute('SELECT account_id FROM usuario WHERE id_usuario=%s',(uid,));aid=cur.fetchone()['account_id']
            hashed=generar_hash_password(secret)
            if aid:
                cur.execute('SELECT id FROM cuenta_global WHERE lower(correo)=lower(%s) AND id<>%s',(email,aid))
                if cur.fetchone():raise RuntimeError('Correo de demostración ocupado por otra identidad; no se sobrescribe.')
                cur.execute("UPDATE cuenta_global SET correo=%s,password_hash=%s,estado='Activo',token_version=token_version+1 WHERE id=%s",(email,hashed,aid))
            cur.execute("UPDATE usuario SET correo=%s,password_hash=%s,estado='Activo',token_version=token_version+1 WHERE id_usuario=%s",(email,hashed,uid))
            if not aid:cur.execute('SELECT identity_index_user(%s)',(uid,))
            accounts.append(email)

        cur.execute("SELECT id_empresa FROM empresa WHERE slug='plataforma' AND plataforma");platform=cur.fetchone()['id_empresa']
        cur.execute("SELECT set_config('app.tenant_id',%s,true)",(str(platform),))
        cur.execute("SELECT u.id_usuario FROM usuario u JOIN rol r ON r.id_rol=u.id_role WHERE u.tenant_id=%s AND r.nombre='Administrador' ORDER BY u.id_usuario LIMIT 1",(platform,));row=cur.fetchone()
        if not row:raise RuntimeError('Falta la cuenta inicial de plataforma; preparar la semilla base primero.')
        update_local(row['id_usuario'],'admin@fashionstore.com',platform_password)

        # Las identidades globales de clientes se crean una vez. Un correo ajeno no se reemplaza.
        customer_ids=[]
        for i in range(1,4):
            email=f'cliente{i}@fashionstore.com'
            cur.execute('SELECT id FROM cuenta_global WHERE correo=%s',(email,));found=cur.fetchone()
            if found:
                cur.execute("SELECT 1 FROM auditoria_identidad WHERE account_id=%s AND accion='SEED_DEMO_V2'",(found['id'],))
                if not cur.fetchone():raise RuntimeError('La cuenta de cliente demo ya pertenece a una identidad no preparada por esta semilla.')
                aid=found['id'];cur.execute("UPDATE cuenta_global SET password_hash=%s,estado='Activo',token_version=token_version+1 WHERE id=%s",(generar_hash_password(password),aid))
            else:
                cur.execute("INSERT INTO cuenta_global(correo,password_hash,nombre,apellido,tipo,ci) VALUES(%s,%s,'Cliente',%s,'CLIENTE',%s) RETURNING id",(email,generar_hash_password(password),f'Demo {i}',f'DEMO-GLOBAL-{i}'));aid=cur.fetchone()['id']
                cur.execute("INSERT INTO auditoria_identidad(account_id,accion) VALUES(%s,'SEED_DEMO_V2')",(aid,))
            customer_ids.append(aid);accounts.append(email)

        for slug,brand in (('demo-a','atelierandino'),('demo-b','casatextil')):
            cur.execute('SELECT id_empresa FROM empresa WHERE slug=%s AND NOT plataforma',(slug,));company=cur.fetchone()
            if not company:raise RuntimeError('Falta empresa demo: '+slug)
            tid=company['id_empresa'];cur.execute("SELECT set_config('app.tenant_id',%s,true)",(str(tid),))
            cur.execute("SELECT u.id_usuario FROM usuario u JOIN rol r ON r.id_rol=u.id_role WHERE u.tenant_id=%s AND r.nombre='Administrador' ORDER BY u.id_usuario LIMIT 1",(tid,));admin=cur.fetchone()['id_usuario']
            update_local(admin,brand+'@fashionstore.com',password)
            for role,prefix in (('Encargado de Sucursal','encargado'),('Cajero (POS)','cajero')):
                email=f'{prefix}-{brand}-01@fashionstore.com'
                cur.execute('SELECT id_rol FROM rol WHERE tenant_id=%s AND nombre=%s',(tid,role));rid=cur.fetchone()['id_rol']
                cur.execute('SELECT id_usuario FROM usuario WHERE tenant_id=%s AND correo=%s',(tid,email));employee=cur.fetchone()
                if employee:uid=employee['id_usuario']
                else:
                    cur.execute('INSERT INTO usuario(tenant_id,nombre,apellido,correo,password_hash,id_role) VALUES(%s,%s,%s,%s,%s,%s) RETURNING id_usuario',(tid,prefix.title(),brand,email,generar_hash_password(password),rid));uid=cur.fetchone()['id_usuario']
                update_local(uid,email,password)
                cur.execute('INSERT INTO usuario_sucursal(tenant_id,id_usuario,id_sucursal) SELECT %s,%s,id_sucursal FROM sucursal WHERE tenant_id=%s AND activa ON CONFLICT DO NOTHING',(tid,uid,tid))

            # Solo el perfil explícito Cliente Demo/DEMO-001 se vincula al comprador global 1.
            cur.execute("SELECT u.id_usuario,u.account_id,u.correo FROM usuario u JOIN rol r ON r.id_rol=u.id_role WHERE u.tenant_id=%s AND r.nombre='Cliente' AND (u.correo='cliente1@fashionstore.com' OR (u.nombre='Cliente' AND u.apellido='Demo')) ORDER BY u.id_usuario LIMIT 1",(tid,));legacy=cur.fetchone()
            if legacy:
                old=legacy['account_id'];email='cliente1@fashionstore.com'
                cur.execute('SELECT password_hash FROM cuenta_global WHERE id=%s',(customer_ids[0],));customer_hash=cur.fetchone()['password_hash']
                cur.execute('UPDATE usuario SET account_id=%s,correo=%s,password_hash=%s,token_version=token_version+1 WHERE id_usuario=%s',(customer_ids[0],email,customer_hash,legacy['id_usuario']))
                cur.execute("UPDATE cliente SET correo=%s WHERE tenant_id=%s AND (ci='DEMO-001' OR correo=%s)",(email,tid,legacy['correo']))
                if old and old!=customer_ids[0]:cur.execute("UPDATE cuenta_global SET estado='Inactivo',token_version=token_version+1 WHERE id=%s AND NOT EXISTS(SELECT 1 FROM usuario WHERE account_id=%s)",(old,old))
            cur.execute("SELECT set_config('app.account_id',%s,true)",(str(customer_ids[0]),))
            cur.execute('SELECT identity_customer_profile(%s,%s)',(customer_ids[0],tid))
        print('Cuentas demo globales preparadas; contraseñas no impresas.')
        for email in accounts:print('  '+email)


if __name__=='__main__':main()
