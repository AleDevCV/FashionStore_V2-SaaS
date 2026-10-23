"""Ensayo sobre el SQL fuente P1 dentro del PostgreSQL efímero de pruebas.
No conecta a la base original. Elimina solo la copia temporal que acaba de crear.
"""
import argparse,hashlib,json,re,secrets
from pathlib import Path
from datetime import datetime,timezone
import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
from migrate import executable_content
ROOT=Path(__file__).resolve().parents[1]
CONFIG=dict(host='127.0.0.1',port=55432,user='p2_test_owner',password='p2-test-only-password')
TABLES=['rol','rol_permiso','usuario','usuario_token','ciudad','sucursal','cliente','temporada','categoria','talla','color','prenda','variante_prenda','imagen_prenda','proveedor','inventario','movimiento_inventario','compra','detalle_compra','reserva','detalle_reserva','venta','detalle_venta','pago_transaccion','comprobante','bitacora']
def snapshot(cur):
    output={}
    for table in TABLES:
        if table in {'bitacora','rol_permiso'}:continue # Auditoría y asignación de permisos crecen por diseño.
        cur.execute(sql.SQL('SELECT count(*) AS n FROM {}').format(sql.Identifier(table)));output[table]=cur.fetchone()['n']
    for table,column in [('venta','total'),('detalle_venta','subtotal'),('compra','total')]:
        cur.execute(sql.SQL('SELECT COALESCE(sum({}),0) AS n FROM {}').format(sql.Identifier(column),sql.Identifier(table)));output[table+'_importe']=str(cur.fetchone()['n'])
    cur.execute('SELECT id_sucursal,id_variante_prenda,stock FROM inventario ORDER BY id_sucursal,id_variante_prenda');output['stock_sha256']=hashlib.sha256(json.dumps([dict(x) for x in cur.fetchall()],sort_keys=True).encode()).hexdigest()
    return output
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--source-sql',default=r'C:\SISTEMAS DE INFORMACION 2\fashionstore-backend\database\db_scheme.sql');args=parser.parse_args();path=Path(args.source_sql)
    content=path.read_text(encoding='utf-8-sig')
    if re.search(r'(?im)^\s*\\|\b(?:CREATE|DROP)\s+DATABASE\b|\bCOPY\b[^;]*\bPROGRAM\b',content):raise SystemExit('El SQL fuente requiere revisión: contiene operaciones fuera del esquema de la copia.')
    name='fashionstore_p1_copy_'+secrets.token_hex(4)
    admin=psycopg2.connect(dbname='fashionstore_p2_test',**CONFIG);admin.autocommit=True
    with admin.cursor() as cur:cur.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(name)))
    conn=None
    try:
        conn=psycopg2.connect(dbname=name,cursor_factory=RealDictCursor,**CONFIG)
        with conn:
            with conn.cursor() as cur:
                cur.execute(content)
                extra=path.parent/'migration_bloque3.sql'
                if extra.exists():cur.execute(extra.read_text(encoding='utf-8-sig'))
                # Compra, reserva y venta sintéticas hacen el ensayo no trivial.
                cur.execute("INSERT INTO proveedor(nit,razon_social) VALUES('MIG-TEST','Proveedor sintético de ensayo') RETURNING id_proveedor");supplier=cur.fetchone()['id_proveedor']
                cur.execute('SELECT id_sucursal FROM sucursal ORDER BY id_sucursal LIMIT 1');branch=cur.fetchone()['id_sucursal']
                cur.execute('SELECT id_usuario FROM usuario ORDER BY id_usuario LIMIT 1');actor=cur.fetchone()['id_usuario']
                cur.execute('SELECT id_categoria FROM categoria ORDER BY id_categoria LIMIT 1');category=cur.fetchone()['id_categoria']
                cur.execute("INSERT INTO prenda(sku,nombre,precio_base,id_categoria) VALUES('MIG-TEST','Prenda sintética de ensayo',50,%s) RETURNING id_prenda",(category,));product=cur.fetchone()['id_prenda']
                cur.execute('SELECT id_talla FROM talla ORDER BY id_talla LIMIT 1');size=cur.fetchone()['id_talla']
                cur.execute('SELECT id_color FROM color ORDER BY id_color LIMIT 1');color=cur.fetchone()['id_color']
                cur.execute("INSERT INTO variante_prenda(id_prenda,id_talla,id_color,sku_variante) VALUES(%s,%s,%s,'MIG-TEST-SKU') RETURNING id_variante_prenda",(product,size,color));variant=cur.fetchone()['id_variante_prenda']
                cur.execute('INSERT INTO compra(id_proveedor,id_sucursal,id_usuario,total) VALUES(%s,%s,%s,100) RETURNING id_compra',(supplier,branch,actor));purchase=cur.fetchone()['id_compra']
                cur.execute('INSERT INTO detalle_compra(id_compra,id_variante_prenda,cantidad,costo_unitario) VALUES(%s,%s,5,20)',(purchase,variant))
                cur.execute("INSERT INTO movimiento_inventario(id_sucursal,id_variante_prenda,tipo,cantidad,motivo,id_usuario) VALUES(%s,%s,'Entrada',5,'Ensayo sintético de migración',%s)",(branch,variant,actor))
                cur.execute('SELECT id_cliente FROM cliente ORDER BY id_cliente LIMIT 1');customer=cur.fetchone()['id_cliente']
                cur.execute("INSERT INTO reserva(id_cliente,id_sucursal,fecha_limite,estado,total) VALUES(%s,%s,now()+interval '24 hours','Pendiente',50) RETURNING id_reserva",(customer,branch));reservation=cur.fetchone()['id_reserva']
                cur.execute('INSERT INTO detalle_reserva(id_reserva,id_variante_prenda,cantidad,precio_unitario) VALUES(%s,%s,1,50)',(reservation,variant))
                cur.execute("INSERT INTO venta(id_cliente,id_sucursal,id_cajero,tipo_venta,metodo_pago,subtotal,total) VALUES(%s,%s,%s,'Presencial','Efectivo',100,100) RETURNING id_venta",(customer,branch,actor));sale=cur.fetchone()['id_venta']
                cur.execute('INSERT INTO detalle_venta(id_venta,id_variante_prenda,cantidad,precio_unitario,subtotal) VALUES(%s,%s,2,50,100)',(sale,variant))
                cur.execute("INSERT INTO movimiento_inventario(id_sucursal,id_variante_prenda,tipo,cantidad,motivo,id_usuario) VALUES(%s,%s,'Salida',2,'Venta sintética de ensayo',%s)",(branch,variant,actor))
                before=snapshot(cur)
                for p in sorted((ROOT/'Parcial2_backend/database/migrations').glob('*.sql')):
                    if not p.name.startswith('001_'):cur.execute(executable_content(p.read_text(encoding='utf-8'),True))
                after=snapshot(cur)
                if before!=after:raise AssertionError('Cambiaron conteos, importes o stock del legado durante la migración.')
                cur.execute("SELECT id_empresa FROM empresa WHERE slug='fashionstore-legado'");legacy=cur.fetchone()['id_empresa']
                for table in TABLES:
                    cur.execute(sql.SQL('SELECT count(*) AS n FROM {} WHERE tenant_id IS NULL OR tenant_id<>%s').format(sql.Identifier(table)),(legacy,));invalid=cur.fetchone()['n']
                    if table=='bitacora':continue # Eventos de plataforma tienen tenant propio.
                    if invalid:raise AssertionError('Asignación incorrecta en '+table)
                cur.execute("INSERT INTO empresa(slug,nombre) VALUES('segunda-empresa','Empresa de contraste') RETURNING id_empresa");second=cur.fetchone()['id_empresa']
                cur.execute("SELECT set_config('app.tenant_id',%s,true)",(str(second),))
                cur.execute("INSERT INTO categoria(nombre) VALUES('Contraste') RETURNING id_categoria");category=cur.fetchone()['id_categoria']
                cur.execute('SELECT sku FROM prenda WHERE tenant_id=%s ORDER BY id_prenda LIMIT 1',(legacy,));original=cur.fetchone();shared_sku=original['sku'] if original else 'CONTRASTE'
                cur.execute("INSERT INTO prenda(sku,nombre,id_categoria,precio_base) VALUES(%s,'Solo empresa B',%s,50)",(shared_sku,category))
                cur.execute('GRANT USAGE ON SCHEMA public TO fashionstore_app; GRANT SELECT ON ALL TABLES IN SCHEMA public TO fashionstore_app;')
        app=psycopg2.connect(host=CONFIG['host'],port=CONFIG['port'],dbname=name,user='fashionstore_app',password='p2-test-app-only')
        try:
            with app,app.cursor() as cur:
                cur.execute("SELECT set_config('app.tenant_id',%s,true),set_config('app.role','Administrador',true)",(str(legacy),));cur.execute('SELECT count(*) FROM prenda');assert cur.fetchone()[0]==before['prenda']
                cur.execute("SELECT set_config('app.tenant_id',%s,true)",(str(second),));cur.execute('SELECT count(*) FROM prenda');assert cur.fetchone()[0]==1
        finally:app.close()
        result={'fecha':datetime.now(timezone.utc).isoformat(),'origen':'Esquema y semilla SQL P1, Bloque 3 y recorrido sintético de compra, reserva, venta e inventario; no es un respaldo de la base operativa actual.','archivo_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'antes':before,'despues':after,'preservacion':True,'aislamiento_segunda_empresa':True,'base_original_modificada':False}
        out=ROOT/'docs/evidencias/migracion-p1-sql.json';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('Ensayo SQL P1: conteos, importes, inventario y aislamiento verificados en copia temporal.')
    finally:
        if conn:conn.close()
        if not re.fullmatch(r'fashionstore_p1_copy_[a-f0-9]{8}',name):raise RuntimeError('Nombre de copia no permitido.')
        with admin.cursor() as cur:cur.execute(sql.SQL('DROP DATABASE {}').format(sql.Identifier(name)))
        admin.close()
if __name__=='__main__':main()
