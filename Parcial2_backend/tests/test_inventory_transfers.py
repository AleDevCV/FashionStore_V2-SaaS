"""A3: transfers with real PostgreSQL, tenant/branch authorization and transactions."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
from uuid import uuid4

import psycopg2
from psycopg2.extras import RealDictCursor
import pytest

from conftest import owner_connection
from test_authorization_c1_a1 import staff
from test_commerce import pos_body, reserve_body


class World(dict):
    def __repr__(self):return '<isolated transfer fixtures; sessions omitted>'


@pytest.fixture
def world(companies, headers):
    c, other = companies
    with owner_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT set_config('app.tenant_id',%s,true)",(str(c['tenant']),))
        cur.execute('SELECT id_ciudad FROM sucursal WHERE tenant_id=%s AND id_sucursal=%s',(c['tenant'],c['branch']))
        city=cur.fetchone()['id_ciudad']
        cur.execute("INSERT INTO sucursal(nombre,direccion,id_ciudad) VALUES('Destino','Prueba A3',%s) RETURNING id_sucursal",(city,))
        dest=cur.fetchone()['id_sucursal']
        cur.execute('INSERT INTO inventario(id_sucursal,id_variante_prenda,stock) VALUES(%s,%s,2)',(dest,c['variant']))
    return World(c=c,other=other,dest=dest,h=headers[0],other_h=headers[1])


def body(w, **changes):
    return {'id_sucursal':w['c']['branch'],'id_sucursal_destino':w['dest'],
            'id_variante_prenda':w['c']['variant'],'tipo':'Traspaso','cantidad':2,
            'motivo':'Traspaso de prueba','operation_id':str(uuid4()),**changes}


def balances(w):
    with owner_connection() as conn,conn.cursor() as cur:
        cur.execute('SELECT id_sucursal,stock FROM inventario WHERE tenant_id=%s AND id_variante_prenda=%s ORDER BY id_sucursal', (w['c']['tenant'],w['c']['variant']))
        return {row['id_sucursal']:row['stock'] for row in cur.fetchall()}


def counts(w):
    with owner_connection() as conn,conn.cursor() as cur:
        result=[]
        for table in ['movimiento_inventario','traspaso_inventario']:
            cur.execute(f'SELECT count(*) AS n FROM {table} WHERE tenant_id=%s',(w['c']['tenant'],))
            result.append(cur.fetchone()['n'])
        return tuple(result)


def snapshot(w):
    output={}
    with owner_connection() as conn,conn.cursor() as cur:
        for table in ['inventario','movimiento_inventario','traspaso_inventario','bitacora','venta','detalle_venta','reserva','detalle_reserva','retencion','operacion_sync']:
            cur.execute(f'SELECT row_to_json(t) AS row FROM {table} t WHERE tenant_id=ANY(%s)',([w['c']['tenant'],w['other']['tenant']],))
            output[table]=sorted(json.dumps(r['row'],sort_keys=True) for r in cur.fetchall())
    return output


def send(client,w,payload=None,path='/api/movimientos-inventario'):
    return client.post(path,headers=w['h'],json=payload or body(w))


@pytest.mark.parametrize('path',['/api/movimientos-inventario','/api/movimientos-inventario/',
                               '/api/inventario/movimientos','/api/inventario/movimientos/'])
def test_transfer_moves_both_legs_in_all_aliases(client,world,path):
    w=world;r=send(client,w,path=path)
    assert r.status_code==201,r.text
    result=r.json()
    assert result['tipo']=='Traspaso'
    assert result['movimiento_salida']['tipo']=='Salida' and result['movimiento_entrada']['tipo']=='Entrada'
    assert result['movimiento_salida']['id_movimiento']!=result['movimiento_entrada']['id_movimiento']
    assert balances(w)=={w['c']['branch']:3,w['dest']:4} and counts(w)==(2,1)
    assert sum(balances(w).values())==7


@pytest.mark.parametrize('bad',[
    {'id_sucursal_destino':None},{'operation_id':None},{'operation_id':'invalid'},
    {'cantidad':0},{'cantidad':-1},{'cantidad':1.5},{'cantidad':True},{'cantidad':2147483648},
    {'motivo':'   '},
])
def test_invalid_contract_never_writes(client,world,bad):
    before=snapshot(world)
    assert send(client,world,body(world,**bad)).status_code==422
    assert snapshot(world)==before


def test_same_branch_and_old_incomplete_contract_are_rejected(client,world):
    before=snapshot(world)
    assert send(client,world,body(world,id_sucursal_destino=world['c']['branch'])).status_code==422
    old=body(world);old.pop('id_sucursal_destino');old.pop('operation_id')
    assert send(client,world,old).status_code==422
    assert snapshot(world)==before


@pytest.mark.parametrize('field',['id_sucursal','id_sucursal_destino','id_variante_prenda'])
def test_cross_company_references_rejected(client,world,field):
    before=snapshot(world)
    foreign=world['other']['variant' if field=='id_variante_prenda' else 'branch']
    assert send(client,world,body(world,**{field:foreign})).status_code==404
    assert snapshot(world)==before


def test_destination_unknown_and_inactive_never_debit(client,world):
    before=snapshot(world)
    assert send(client,world,body(world,id_sucursal_destino=2147483647)).status_code==404
    with owner_connection() as conn,conn.cursor() as cur:
        cur.execute('UPDATE sucursal SET activa=false WHERE tenant_id=%s AND id_sucursal=%s',(world['c']['tenant'],world['dest']))
    # Audit of branch deactivation is fixture setup, not part of transfer.
    after_setup=snapshot(world)
    assert send(client,world).status_code==404
    assert snapshot(world)==after_setup and counts(world)==(0,0)
    assert balances(world)=={world['c']['branch']:5,world['dest']:2}


@pytest.mark.parametrize('role',['Cajero (POS)','Cliente'])
def test_existing_role_gate_blocks_transfer(client,world,role):
    staff(world['c'],role,assigned=False)
    before=snapshot(world)
    assert send(client,world).status_code==403
    assert snapshot(world)==before


def test_manager_needs_both_assignments_and_current_permission_on_retry(client,world):
    w=world;staff(w['c'],'Encargado de Sucursal')
    request=body(w);before=snapshot(w)
    assert send(client,w,request).status_code==403 and snapshot(w)==before
    with owner_connection() as conn,conn.cursor() as cur:
        cur.execute('INSERT INTO usuario_sucursal(tenant_id,id_usuario,id_sucursal) VALUES(%s,%s,%s)',(w['c']['tenant'],w['c']['user'],w['dest']))
    result=send(client,w,request);assert result.status_code==201,result.text
    with owner_connection() as conn,conn.cursor() as cur:
        cur.execute('DELETE FROM usuario_sucursal WHERE tenant_id=%s AND id_usuario=%s AND id_sucursal=%s',(w['c']['tenant'],w['c']['user'],w['dest']))
    before=snapshot(w)
    assert send(client,w,request).status_code==403 and snapshot(w)==before
    history=client.get('/api/movimientos-inventario',headers=w['h']).json()
    assert len(history)==1 and history[0]['tipo']=='Salida'
    assert 'operation_id' not in history[0]


def test_retry_returns_frozen_result_and_changed_payload_is_rejected(client,world):
    w=world;request=body(w);first=send(client,w,request)
    assert first.status_code==201
    # An unrelated entry changes current stock, not the original transfer receipt.
    extra={k:v for k,v in request.items() if k not in ['operation_id','id_sucursal_destino']}
    extra.update(tipo='Entrada',cantidad=1)
    assert send(client,w,extra).status_code==201
    before=snapshot(w)
    for _ in range(5):assert send(client,w,request).json()==first.json()
    for changes in [{'cantidad':1},{'motivo':'Otro motivo'},{'id_sucursal':w['dest'],'id_sucursal_destino':w['c']['branch']}]:
        assert send(client,w,{**request,**changes}).status_code==409
    assert snapshot(w)==before and counts(w)==(3,1)


def test_header_history_filter_links_real_legs(client,world):
    w=world;result=send(client,w).json()
    r=client.get('/api/movimientos-inventario',headers=w['h'],params={'tipo':'Traspaso'})
    assert r.status_code==200,r.text
    rows=r.json();assert len(rows)==2
    assert {r['tipo'] for r in rows}=={'Salida','Entrada'}
    assert all(r['operation_id']==result['operation_id'] for r in rows)
    for row in rows:
        assert row['id_movimiento_salida']==result['movimiento_salida']['id_movimiento']
        assert row['id_movimiento_entrada']==result['movimiento_entrada']['id_movimiento']


def test_missing_destination_inventory_is_created_by_existing_entry(client,world):
    w=world
    with owner_connection() as conn,conn.cursor() as cur:
        cur.execute('DELETE FROM inventario WHERE tenant_id=%s AND id_sucursal=%s',(w['c']['tenant'],w['dest']))
    assert send(client,w).status_code==201
    assert balances(w)=={w['c']['branch']:3,w['dest']:2}


def test_insufficient_stock_and_holds_reject_without_rows(client,world):
    w=world;before=snapshot(w)
    assert send(client,w,body(w,cantidad=6)).status_code==409 and snapshot(w)==before
    reserve=client.post('/api/ventas/reserva',headers=w['h'],json=reserve_body(w['c'],4))
    assert reserve.status_code==201,reserve.text
    before=snapshot(w)
    assert send(client,w,body(w,cantidad=2)).status_code==409 and snapshot(w)==before
    assert send(client,w,body(w,cantidad=1)).status_code==201


def test_destination_overflow_rejected_without_debit(client,world):
    w=world
    with owner_connection() as conn,conn.cursor() as cur:
        cur.execute('UPDATE inventario SET stock=2147483647 WHERE tenant_id=%s AND id_sucursal=%s',(w['c']['tenant'],w['dest']))
    before=snapshot(w)
    assert send(client,w).status_code==409 and snapshot(w)==before


@pytest.mark.parametrize('point',['credit','after_credit','audit'])
def test_injected_failure_rolls_back_every_business_and_audit_row(client,world,monkeypatch,point):
    from app.services import movimiento_service as svc
    before=snapshot(world)
    with monkeypatch.context() as patch:
        if point=='credit':
            original=svc.registrar_movimiento
            def fail(cursor,datos,id_usuario,ip_address):
                if datos.tipo=='Entrada':raise RuntimeError('A3 rollback probe')
                return original(cursor,datos,id_usuario,ip_address)
            patch.setattr(svc,'registrar_movimiento',fail)
        elif point=='after_credit':
            original=svc.obtener_movimiento_por_id;calls=[]
            def fail(*args):
                calls.append(1)
                if len(calls)==2:raise RuntimeError('A3 rollback probe')
                return original(*args)
            patch.setattr(svc,'obtener_movimiento_por_id',fail)
        else:
            original=svc.registrar_bitacora
            def fail(*args,**kwargs):
                if kwargs.get('tabla_afectada')=='traspaso_inventario':raise RuntimeError('A3 rollback probe')
                return original(*args,**kwargs)
            patch.setattr(svc,'registrar_bitacora',fail)
        with pytest.raises(RuntimeError,match='A3 rollback probe'):send(client,world)
    assert snapshot(world)==before


def test_actual_sql_failure_in_credit_rolls_back_origin(client,world):
    w=world;name='a3_failure_'+str(w['c']['tenant'])
    with owner_connection() as conn,conn.cursor() as cur:
        cur.execute(f"CREATE FUNCTION {name}() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'A3 SQL fault' USING ERRCODE='23514'; END $$")
        cur.execute(f"CREATE TRIGGER {name} BEFORE INSERT ON movimiento_inventario FOR EACH ROW WHEN (NEW.tenant_id={w['c']['tenant']} AND NEW.id_sucursal={w['dest']}) EXECUTE FUNCTION {name}()")
    before=snapshot(w)
    try:
        assert send(client,w).status_code in [400,409]
        assert snapshot(w)==before
    finally:
        with owner_connection() as conn,conn.cursor() as cur:
            cur.execute(f'DROP TRIGGER {name} ON movimiento_inventario')
            cur.execute(f'DROP FUNCTION {name}()')


def test_concurrent_same_uuid_is_one_pair(client,world):
    w=world;request=body(w)
    with ThreadPoolExecutor(max_workers=4) as pool:responses=list(pool.map(lambda _:send(client,w,request),range(4)))
    assert [r.status_code for r in responses]==[201]*4
    assert all(r.json()==responses[0].json() for r in responses)
    assert counts(w)==(2,1) and balances(w)=={w['c']['branch']:3,w['dest']:4}


def test_concurrent_distinct_uuids_cannot_overconsume(client,world):
    w=world
    with ThreadPoolExecutor(max_workers=2) as pool:responses=list(pool.map(lambda _:send(client,w,body(w,cantidad=4)),range(2)))
    assert sorted(r.status_code for r in responses)==[201,409]
    assert counts(w)==(2,1) and balances(w)=={w['c']['branch']:1,w['dest']:6}


def test_opposite_transfers_use_consistent_lock_order(client,world):
    w=world;requests=[body(w,cantidad=1),body(w,cantidad=1,id_sucursal=w['dest'],id_sucursal_destino=w['c']['branch'])]
    with ThreadPoolExecutor(max_workers=2) as pool:responses=list(pool.map(lambda b:send(client,w,b),requests))
    assert [r.status_code for r in responses]==[201,201]
    assert counts(w)==(4,2) and balances(w)=={w['c']['branch']:5,w['dest']:2}


@pytest.mark.parametrize('competitor',['sale','reservation'])
def test_transfer_competes_safely_for_last_unit(client,world,competitor):
    w=world
    with owner_connection() as conn,conn.cursor() as cur:
        cur.execute('UPDATE inventario SET stock=1 WHERE tenant_id=%s AND id_sucursal=%s',(w['c']['tenant'],w['c']['branch']))
    def other():
        return client.post('/api/pos/ventas' if competitor=='sale' else '/api/ventas/reserva',headers=w['h'],
                           json=pos_body(w['c']) if competitor=='sale' else reserve_body(w['c']))
    with ThreadPoolExecutor(max_workers=2) as pool:
        a=pool.submit(send,client,w,body(w,cantidad=1));b=pool.submit(other)
        codes=sorted([a.result().status_code,b.result().status_code])
    assert codes==[201,409]
    assert min(balances(w).values())>=0


def test_transfer_preserves_reserved_units_and_legitimate_reservation_payment(client,world):
    w=world
    r=client.post('/api/ventas/reserva',headers=w['h'],json=reserve_body(w['c'],2));assert r.status_code==201
    assert send(client,w,body(w,cantidad=3)).status_code==201
    sale=pos_body(w['c'],2);sale['id_reserva']=r.json()['id_reserva']
    confirmed=client.post('/api/pos/ventas',headers=w['h'],json=sale)
    assert confirmed.status_code==201,confirmed.text
    assert balances(w)=={w['c']['branch']:0,w['dest']:5}


def test_new_raw_trapaso_and_changes_to_linked_history_are_blocked(client,world):
    w=world;result=send(client,w).json();before=snapshot(w)
    for statement,params in [
        ("INSERT INTO movimiento_inventario(tenant_id,id_sucursal,id_variante_prenda,tipo,cantidad,motivo,id_usuario) VALUES(%s,%s,%s,'Traspaso',1,'Raw probe',%s)",(w['c']['tenant'],w['c']['branch'],w['c']['variant'],w['c']['user'])),
        ('UPDATE movimiento_inventario SET cantidad=1 WHERE id_movimiento=%s',(result['movimiento_salida']['id_movimiento'],)),
        ('DELETE FROM traspaso_inventario WHERE tenant_id=%s',(w['c']['tenant'],)),
    ]:
        with pytest.raises(psycopg2.errors.CheckViolation):
            with owner_connection() as conn,conn.cursor() as cur:cur.execute(statement,params)
    assert snapshot(w)==before


def test_uuid_is_scoped_to_tenant(client,world):
    w=world;request=body(w);first=send(client,w,request);assert first.status_code==201
    other=w['other']
    with owner_connection() as conn,conn.cursor() as cur:
        cur.execute("SELECT set_config('app.tenant_id',%s,true)",(str(other['tenant']),))
        cur.execute('SELECT id_ciudad FROM sucursal WHERE tenant_id=%s AND id_sucursal=%s',(other['tenant'],other['branch']))
        city=cur.fetchone()['id_ciudad']
        cur.execute("INSERT INTO sucursal(nombre,direccion,id_ciudad) VALUES('Destino B','Otro',%s) RETURNING id_sucursal",(city,))
        dest=cur.fetchone()['id_sucursal']
    payload={**request,'id_sucursal':other['branch'],'id_sucursal_destino':dest,'id_variante_prenda':other['variant']}
    response=client.post('/api/movimientos-inventario',headers=w['other_h'],json=payload)
    assert response.status_code==201,response.text
    assert response.json()['movimiento_salida']['id_movimiento']!=first.json()['movimiento_salida']['id_movimiento']


def test_migration_keeps_legacy_transfer_without_replaying_stock():
    name='fashionstore_a3_upgrade_'+uuid4().hex[:10]
    options=dict(host='127.0.0.1',port=55432,user='p2_test_owner',password='p2-test-only-password')
    admin=psycopg2.connect(dbname='postgres',**options);admin.autocommit=True
    try:
        with admin.cursor() as cur:cur.execute('CREATE DATABASE '+name)
    finally:admin.close()
    migrations=Path(__file__).resolve().parents[1]/'database/migrations'
    with psycopg2.connect(dbname=name,cursor_factory=RealDictCursor,**options) as conn,conn.cursor() as cur:
        for path in sorted(migrations.glob('*.sql')):
            if path.name.startswith('018_'):continue
            cur.execute(path.read_text(encoding='utf-8'))
        cur.execute("INSERT INTO empresa(slug,nombre) VALUES('upgrade-a3','Upgrade') RETURNING id_empresa");tid=cur.fetchone()['id_empresa']
        cur.execute("SELECT set_config('app.tenant_id',%s,true)",(str(tid),))
        cur.execute("INSERT INTO suscripcion(tenant_id,id_plan,inicio,vencimiento) VALUES(%s,1,now()-interval '1 day',now()+interval '30 days')",(tid,))
        cur.execute("INSERT INTO ciudad(nombre) VALUES('Prueba') RETURNING id_ciudad");city=cur.fetchone()['id_ciudad']
        cur.execute("INSERT INTO sucursal(nombre,direccion,id_ciudad) VALUES('Origen','Prueba',%s) RETURNING id_sucursal",(city,));branch=cur.fetchone()['id_sucursal']
        cur.execute("INSERT INTO categoria(nombre) VALUES('Prueba') RETURNING id_categoria");cat=cur.fetchone()['id_categoria']
        cur.execute("INSERT INTO prenda(sku,nombre,precio_base,id_categoria) VALUES('LEGACY','Prueba',50,%s) RETURNING id_prenda",(cat,));product=cur.fetchone()['id_prenda']
        cur.execute("INSERT INTO talla(nombre) VALUES('M') RETURNING id_talla");size=cur.fetchone()['id_talla']
        cur.execute("INSERT INTO color(nombre) VALUES('Azul') RETURNING id_color");color=cur.fetchone()['id_color']
        cur.execute("INSERT INTO variante_prenda(id_prenda,id_talla,id_color,sku_variante) VALUES(%s,%s,%s,'LEGACY-V') RETURNING id_variante_prenda",(product,size,color));variant=cur.fetchone()['id_variante_prenda']
        cur.execute('INSERT INTO inventario(id_sucursal,id_variante_prenda,stock) VALUES(%s,%s,5)',(branch,variant))
        cur.execute("INSERT INTO movimiento_inventario(id_sucursal,id_variante_prenda,tipo,cantidad,motivo) VALUES(%s,%s,'Traspaso',2,'Historico sin destino') RETURNING id_movimiento",(branch,variant));mid=cur.fetchone()['id_movimiento']
        cur.execute('SELECT row_to_json(m) AS data FROM movimiento_inventario m WHERE id_movimiento=%s',(mid,));before=cur.fetchone()['data']
        cur.execute((migrations/'018_inventory_transfers.sql').read_text(encoding='utf-8'))
        cur.execute('SELECT row_to_json(m) AS data FROM movimiento_inventario m WHERE id_movimiento=%s',(mid,));assert cur.fetchone()['data']==before
        cur.execute('SELECT stock FROM inventario WHERE id_sucursal=%s',(branch,));assert cur.fetchone()['stock']==5
        cur.execute('SELECT count(*) AS n FROM traspaso_inventario');assert cur.fetchone()['n']==0


def test_available_stock_query_preserves_default_and_subtracts_holds(client,world):
    w=world
    assert client.post('/api/ventas/reserva',headers=w['h'],json=reserve_body(w['c'],4)).status_code==201
    params={'id_sucursal':w['c']['branch'],'id_variante_prenda':w['c']['variant']}
    assert client.get('/api/movimientos-inventario/stock',headers=w['h'],params=params).json()['stock']==5
    assert client.get('/api/movimientos-inventario/stock',headers=w['h'],params={**params,'disponible':'true'}).json()['stock']==1


def test_concurrent_same_uuid_different_payload_has_one_winner(client,world):
    w=world;request=body(w);requests=[request,{**request,'cantidad':3}]
    with ThreadPoolExecutor(max_workers=2) as pool:responses=list(pool.map(lambda b:send(client,w,b),requests))
    assert sorted(r.status_code for r in responses)==[201,409]
    assert counts(w)==(2,1) and sum(balances(w).values())==7


def test_expired_reservation_does_not_block_transfer(client,world):
    w=world
    assert client.post('/api/ventas/reserva',headers=w['h'],json=reserve_body(w['c'],4)).status_code==201
    with owner_connection() as conn,conn.cursor() as cur:
        cur.execute("UPDATE retencion SET vence=now()-interval '1 minute' WHERE tenant_id=%s",(w['c']['tenant'],))
        cur.execute("UPDATE reserva SET fecha_limite=now()-interval '1 minute' WHERE tenant_id=%s",(w['c']['tenant'],))
    assert send(client,w,body(w,cantidad=5)).status_code==201
    assert balances(w)=={w['c']['branch']:0,w['dest']:7}


def test_business_transaction_finalizes_before_http_success(world,monkeypatch):
    from contextlib import contextmanager
    from fastapi.testclient import TestClient
    from app.main import app
    from app import database
    request=body(world);before=snapshot(world);statuses=[]
    original=database.get_connection
    @contextmanager
    def fail_at_transaction_exit():
        with original() as conn:
            yield conn
            with conn.cursor() as cur:
                cur.execute('SELECT 1 FROM traspaso_inventario WHERE operation_id=%s',(request['operation_id'],))
                if cur.fetchone():raise RuntimeError('A3 commit boundary probe')
    async def observed(scope,receive,send_message):
        async def track(message):
            if message['type']=='http.response.start':statuses.append(message['status'])
            await send_message(message)
        await app(scope,receive,track)
    with monkeypatch.context() as patch:
        patch.setattr(database,'get_connection',fail_at_transaction_exit)
        with TestClient(observed) as c:
            with pytest.raises(RuntimeError,match='A3 commit boundary probe'):
                c.post('/api/movimientos-inventario',headers=world['h'],json=request)
    assert 201 not in statuses
    assert snapshot(world)==before


def test_authentication_and_business_share_a_single_pool_slot(client,world,monkeypatch):
    import os
    import threading
    from psycopg2.pool import ThreadedConnectionPool
    from app import database
    small=ThreadedConnectionPool(1,1,host=os.environ['DB_HOST'],port=os.environ['DB_PORT'],
        dbname=os.environ['DB_NAME'],user=os.environ['DB_USER'],password=os.environ['DB_PASSWORD'])
    try:
        with monkeypatch.context() as patch:
            patch.setattr(database,'_connection_pool',small)
            patch.setattr(database,'_pool_slots',threading.BoundedSemaphore(1))
            patch.setattr(database,'DB_POOL_WAIT_SECONDS',0.2)
            response=send(client,world)
            assert response.status_code==201,response.text
    finally:small.closeall()
