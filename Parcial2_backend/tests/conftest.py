"""Pruebas nuevas: credenciales fijas del contenedor efímero, jamás .env P1."""
import os
import sys
from pathlib import Path
import secrets
import pytest
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi.testclient import TestClient

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
os.environ.update(DB_HOST='127.0.0.1',DB_PORT='55432',DB_NAME='fashionstore_p2_test',DB_USER='fashionstore_app',DB_PASSWORD='p2-test-app-only',SECRET_KEY='isolated-test-secret-with-more-than-forty-eight-characters',ALLOWED_ORIGINS='http://testserver')

def owner_connection():
    conn=psycopg2.connect(host='127.0.0.1',port=55432,dbname='fashionstore_p2_test',user='p2_test_owner',password='p2-test-only-password',cursor_factory=RealDictCursor)
    if conn.info.dbname!='fashionstore_p2_test':raise RuntimeError('Se requiere base temporal de pruebas.')
    return conn

@pytest.fixture
def companies():
    from app.services.auth_service import generar_hash_password
    output=[]
    with owner_connection() as conn,conn.cursor() as cur:
        for i in range(2):
            slug='test-'+secrets.token_hex(5)
            cur.execute('INSERT INTO empresa(slug,nombre) VALUES(%s,%s) RETURNING id_empresa',(slug,'Empresa '+str(i)));tid=cur.fetchone()['id_empresa']
            cur.execute("SELECT set_config('app.tenant_id',%s,true)",(str(tid),))
            cur.execute("INSERT INTO rol(nombre) VALUES('Administrador') RETURNING id_rol");rid=cur.fetchone()['id_rol']
            email=slug+'@example.com'
            cur.execute("INSERT INTO usuario(nombre,apellido,correo,password_hash,id_role) VALUES('Prueba','Admin',%s,%s,%s) RETURNING id_usuario",(email,generar_hash_password('test-password-123'),rid));uid=cur.fetchone()['id_usuario']
            cur.execute('SELECT identity_index_user(%s)',(uid,))
            cur.execute("INSERT INTO suscripcion(tenant_id,id_plan,inicio,vencimiento) VALUES(%s,%s,now()-interval '1 day',now()+interval '30 days')",(tid,1 if i==0 else 2))
            cur.execute("INSERT INTO ciudad(nombre) VALUES('Santa Cruz') RETURNING id_ciudad");city=cur.fetchone()['id_ciudad']
            cur.execute("INSERT INTO sucursal(nombre,direccion,id_ciudad) VALUES('Central','Dirección prueba',%s) RETURNING id_sucursal",(city,));branch=cur.fetchone()['id_sucursal']
            cur.execute("INSERT INTO cliente(ci,nombre_completo,correo) VALUES('MOSTRADOR','Cliente Mostrador',%s) RETURNING id_cliente",('cliente@example.com',));customer=cur.fetchone()['id_cliente']
            cur.execute("INSERT INTO categoria(nombre) VALUES('Camisas') RETURNING id_categoria");cat=cur.fetchone()['id_categoria']
            cur.execute("INSERT INTO prenda(sku,nombre,precio_base,id_categoria) VALUES('SKU-COMPARTIDO','Camisa',50,%s) RETURNING id_prenda",(cat,));product=cur.fetchone()['id_prenda']
            cur.execute("INSERT INTO talla(nombre) VALUES('M') RETURNING id_talla");size=cur.fetchone()['id_talla']
            cur.execute("INSERT INTO color(nombre) VALUES('Azul') RETURNING id_color");color=cur.fetchone()['id_color']
            cur.execute("INSERT INTO variante_prenda(id_prenda,id_talla,id_color,sku_variante) VALUES(%s,%s,%s,'SKU-VARIANTE') RETURNING id_variante_prenda",(product,size,color));variant=cur.fetchone()['id_variante_prenda']
            cur.execute("INSERT INTO inventario(id_sucursal,id_variante_prenda,stock) VALUES(%s,%s,5)",(branch,variant))
            output.append(dict(tenant=tid,slug=slug,email=email,user=uid,role=rid,branch=branch,customer=customer,product=product,variant=variant))
    return output

@pytest.fixture
def client():
    from app.main import app
    with TestClient(app) as value:yield value

@pytest.fixture
def headers(companies):
    from app.tenant import context,TenantContext
    from app.services.auth_service import crear_token_acceso
    result=[]
    for c in companies:
        marker=context.set(TenantContext(c['tenant']))
        try:token=crear_token_acceso(dict(id_usuario=c['user'],rol='Administrador',correo=c['email'],nombre='Prueba'))
        finally:context.reset(marker)
        result.append({'Authorization':'Bearer '+token})
    return result
