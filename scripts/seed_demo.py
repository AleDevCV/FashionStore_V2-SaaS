"""Datos nuevos y reproducibles para dos empresas. No importa personas del P1."""
from pathlib import Path
import os,sys
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

ROOT=Path(__file__).resolve().parents[1]
load_dotenv(ROOT/'.env')
sys.path.insert(0,str(ROOT/'Parcial2_backend'))
from app.services.auth_service import generar_hash_password
from app.routers.saas import initialize_company

def main():
    password=os.environ['DEMO_PASSWORD']
    with psycopg2.connect(host=os.getenv('MIGRATION_HOST','127.0.0.1'),port=os.getenv('MIGRATION_PORT','55433'),dbname=os.environ['POSTGRES_DB'],user=os.environ['POSTGRES_USER'],password=os.environ['POSTGRES_PASSWORD'],cursor_factory=RealDictCursor) as conn,conn.cursor() as cur:
        cur.execute('SELECT id_empresa FROM empresa WHERE plataforma');platform=cur.fetchone()['id_empresa']
        cur.execute("SELECT set_config('app.tenant_id',%s,true)",(str(platform),))
        cur.execute("INSERT INTO rol(nombre) VALUES('Administrador') ON CONFLICT(tenant_id,nombre) DO UPDATE SET nombre=excluded.nombre RETURNING id_rol");role=cur.fetchone()['id_rol']
        cur.execute("INSERT INTO usuario(nombre,apellido,correo,password_hash,id_role) VALUES('Administración','Plataforma','plataforma@example.com',%s,%s) ON CONFLICT(tenant_id,correo) DO NOTHING",(generar_hash_password(password),role))
        for slug,name,plan in [('demo-a','Atelier Andino',1),('demo-b','Casa Textil',2)]:
            cur.execute('SELECT id_empresa FROM empresa WHERE slug=%s',(slug,))
            if cur.fetchone():print(slug+': ya existe; no se sobrescribieron datos.');continue
            cur.execute('INSERT INTO empresa(slug,nombre) VALUES(%s,%s) RETURNING id_empresa',(slug,name));tenant=cur.fetchone()['id_empresa']
            admin=initialize_company(cur,tenant,'admin@example.com',password,plan)
            cur.execute("INSERT INTO ciudad(nombre) VALUES('Santa Cruz de la Sierra') RETURNING id_ciudad");city=cur.fetchone()['id_ciudad']
            cur.execute("INSERT INTO sucursal(nombre,direccion,id_ciudad,id_encargado) VALUES('Central','Avenida de demostración 100',%s,%s) RETURNING id_sucursal",(city,admin));branch=cur.fetchone()['id_sucursal']
            cur.execute('INSERT INTO usuario_sucursal(tenant_id,id_usuario,id_sucursal) VALUES(%s,%s,%s)',(tenant,admin,branch))
            cur.execute("SELECT id_rol FROM rol WHERE nombre='Cliente' AND tenant_id=%s",(tenant,));customer_role=cur.fetchone()['id_rol']
            cur.execute("INSERT INTO usuario(nombre,apellido,correo,password_hash,id_role) VALUES('Cliente','Demo','cliente@example.com',%s,%s)",(generar_hash_password(password),customer_role))
            cur.execute("INSERT INTO cliente(ci,nombre_completo,correo,telefono) VALUES('DEMO-001','Cliente Demo','cliente@example.com','70000000')")
            cur.execute("INSERT INTO proveedor(nit,razon_social) VALUES('DEMO-PROV','Proveedor Demostración')")
            cur.execute("INSERT INTO categoria(nombre,descripcion) VALUES('Prendas esenciales','Colección de demostración') RETURNING id_categoria");category=cur.fetchone()['id_categoria']
            cur.execute("INSERT INTO temporada(nombre,fecha_inicio,fecha_fin) VALUES('Colección 2026',CURRENT_DATE-180,CURRENT_DATE+180) RETURNING id_temporada");season=cur.fetchone()['id_temporada']
            sizes=[]
            for size in ['S','M','L']:
                cur.execute('INSERT INTO talla(nombre) VALUES(%s) RETURNING id_talla',(size,));sizes.append(cur.fetchone()['id_talla'])
            cur.execute("INSERT INTO color(nombre,codigo_hex) VALUES('Oliva','#647453') RETURNING id_color");color=cur.fetchone()['id_color']
            for i,(title,price) in enumerate([('Camisa de algodón',120),('Pantalón recto',190),('Chaqueta ligera',250),('Blusa de lino',150)],1):
                cur.execute('INSERT INTO prenda(sku,nombre,precio_base,id_categoria,id_temporada,material,medidas,precio_mayorista) VALUES(%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id_prenda',(f'DEMO-{i:03}',title,price,category,season,'Algodón o lino','Consultar talla de la variante',round(price*.85,2)));product=cur.fetchone()['id_prenda']
                for j,size in enumerate(sizes):
                    cur.execute('INSERT INTO variante_prenda(id_prenda,id_talla,id_color,sku_variante) VALUES(%s,%s,%s,%s) RETURNING id_variante_prenda',(product,size,color,f'DEMO-{i:03}-{j}'));variant=cur.fetchone()['id_variante_prenda']
                    cur.execute("INSERT INTO movimiento_inventario(id_sucursal,id_variante_prenda,tipo,cantidad,motivo,id_usuario) VALUES(%s,%s,'Entrada',20,'Existencia inicial de demostración',%s)",(branch,variant,admin))
            print(slug+': empresa, usuarios, catálogo y existencias creados.')
    print('Clave de acceso demo: consultar DEMO_PASSWORD en .env privado. No se publica en documentación.')
if __name__=='__main__':main()
