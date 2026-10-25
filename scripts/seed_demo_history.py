"""Historial comercial identificado como demostración. Solo demo-a y demo-b, nunca P1."""
from pathlib import Path
from datetime import date,timedelta,datetime,time
import os,random
from decimal import Decimal
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
ROOT=Path(__file__).resolve().parents[1]

def main():
    load_dotenv(ROOT/'.env');name=os.environ['POSTGRES_DB']
    if name!='fashionstore_p2':raise SystemExit('Este generador solo admite fashionstore_p2 y tenants demo explícitos.')
    rng=random.Random(262026);anchor=date.today()
    with psycopg2.connect(host=os.getenv('MIGRATION_HOST','127.0.0.1'),port=os.getenv('MIGRATION_PORT','55433'),dbname=name,user=os.environ['POSTGRES_USER'],password=os.environ['POSTGRES_PASSWORD'],cursor_factory=RealDictCursor) as conn,conn.cursor() as cur:
        for slug in ('demo-a','demo-b'):
            cur.execute('SELECT id_empresa FROM empresa WHERE slug=%s AND NOT plataforma',(slug,));company=cur.fetchone()
            if not company:continue
            tid=company['id_empresa'];cur.execute("SELECT set_config('app.tenant_id',%s,true)",(str(tid),))
            cur.execute("SELECT count(*) AS n FROM venta WHERE tenant_id=%s AND referencia_demo LIKE 'HIST-V1-%%'",(tid,))
            if cur.fetchone()['n']:print(slug+': historial ya preparado; no se duplica.');continue
            cur.execute('SELECT id_sucursal FROM sucursal WHERE tenant_id=%s ORDER BY id_sucursal LIMIT 1',(tid,));branch=cur.fetchone()['id_sucursal']
            cur.execute("SELECT u.id_usuario FROM usuario u JOIN rol r ON r.id_rol=u.id_role WHERE u.tenant_id=%s AND r.nombre='Administrador' ORDER BY u.id_usuario LIMIT 1",(tid,));admin=cur.fetchone()['id_usuario']
            clients=[]
            for i in range(1,13):
                cur.execute('INSERT INTO cliente(ci,nombre_completo,correo) VALUES(%s,%s,%s) ON CONFLICT(tenant_id,ci) DO UPDATE SET ci=excluded.ci RETURNING id_cliente',(f'HIST-DEMO-{i:02}',f'Cliente sintético {i:02}',f'demo{i:02}@example.com'));clients.append(cur.fetchone()['id_cliente'])
            cur.execute('SELECT DISTINCT ON(p.id_prenda) v.id_variante_prenda,p.precio_base FROM prenda p JOIN variante_prenda v USING(id_prenda) WHERE p.tenant_id=%s AND p.sku LIKE \'DEMO-%%\' ORDER BY p.id_prenda,v.id_variante_prenda',(tid,));variants=cur.fetchall();count=0
            for day in range(60,0,-1):
                stamp=anchor-timedelta(days=day)
                for idx,row in enumerate(variants):
                    qty=1+rng.randrange(3)+(1 if stamp.weekday() in (4,5) else 0);price=Decimal(row['precio_base']);total=qty*price;customer=clients[(day+idx)%len(clients)];variant=row['id_variante_prenda']
                    cur.execute("INSERT INTO movimiento_inventario(id_sucursal,id_variante_prenda,tipo,cantidad,motivo,id_usuario,fecha) VALUES(%s,%s,'Entrada',%s,'Reposición histórica sintética DEMO',%s,%s)",(branch,variant,qty,admin,datetime.combine(stamp,time(9))))
                    cur.execute("INSERT INTO venta(id_cliente,id_sucursal,id_cajero,tipo_venta,metodo_pago,subtotal,total,fecha_venta,fecha_entrega,origen_datos,referencia_demo) VALUES(%s,%s,%s,'Presencial','Efectivo',%s,%s,%s,%s,'demostracion',%s) RETURNING id_venta",(customer,branch,admin,total,total,datetime.combine(stamp,time(12)),datetime.combine(stamp,time(12)),f'HIST-V1-{day}-{idx}'));sale=cur.fetchone()['id_venta']
                    cur.execute('INSERT INTO detalle_venta(id_venta,id_variante_prenda,cantidad,precio_unitario,subtotal) VALUES(%s,%s,%s,%s,%s)',(sale,variant,qty,price,total))
                    cur.execute("INSERT INTO movimiento_inventario(id_sucursal,id_variante_prenda,tipo,cantidad,motivo,id_usuario,fecha) VALUES(%s,%s,'Salida',%s,%s,%s,%s)",(branch,variant,qty,f'Venta histórica sintética {sale}',admin,datetime.combine(stamp,time(12))));count+=1
            print(f'{slug}: {count} ventas marcadas demostracion; entradas y salidas equilibradas. No son el dataset de entrenamiento.')
if __name__=='__main__':main()
