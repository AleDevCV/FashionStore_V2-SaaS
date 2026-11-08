from pathlib import Path
from uuid import uuid4
import json,httpx
from conftest import owner_connection

def data():return json.loads(Path('/private/runtime-fixture.json').read_text())
def api(foreign=False):
 f=data();return httpx.Client(base_url='http://fashionstore-a5-runtime:8000',headers=f['other_company']['header'] if foreign else f['header'],timeout=30)
def test_snapshot_accepts_50_and_rejects_51_without_contract_change():
 f=data();branch=f['before'][0]['branch']['id_sucursal']
 with api() as client:
  for length,status in [(50,200),(51,422)]:
   params=[('branch_id',branch)]+[('operation_ids',op['operation_id']) for op in f['operations'][:length]]
   assert client.get('/api/offline/catalogo',params=params).status_code==status
def test_all_127_results_remain_definitive_and_equal():
 f=data()
 with api() as client:
  for result in f['results']:
   response=client.get('/api/sincronizacion/operaciones/'+result['operation_id']);assert response.status_code==200;assert response.json()==result
def test_replay_preserves_original_and_changed_payload_is_rejected():
 f=data()
 with api() as client:
  for offset in range(0,127,20):
   response=client.post('/api/sincronizacion/lote',json={'operations':f['operations'][offset:offset+20]});assert response.status_code==200;assert response.json()['results']==f['results'][offset:offset+20]
  changed={**f['operations'][-1],'device_id':str(uuid4())}
  assert client.post('/api/sincronizacion/lote',json={'operations':[changed]}).json()['results'][0]['state']=='RECHAZADA'
def test_cross_tenant_result_is_invisible():
 f=data()
 with api(True) as client:
  assert client.get('/api/sincronizacion/operaciones/'+f['operations'][-1]['operation_id']).status_code==404
def test_unknown_uuid_does_not_fabricate_confirmation():
 f=data()
 with api() as client:
  response=client.get('/api/offline/catalogo',params={'branch_id':f['before'][0]['branch']['id_sucursal'],'operation_ids':str(uuid4())});assert response.status_code==200;assert response.json()['operation_results']==[]
def test_inventory_business_counts_and_histories_unchanged_after_clients():
 f=data();tenant=f['operations'][0]['tenant_id']
 with owner_connection() as conn,conn.cursor() as cur:
  cur.execute('SELECT count(*) AS n FROM operacion_sync WHERE tenant_id=%s',(tenant,));assert cur.fetchone()['n']==127
  cur.execute('SELECT count(*) AS n FROM venta WHERE tenant_id=%s',(tenant,));assert cur.fetchone()['n']==77
  cur.execute('SELECT count(*) AS n FROM movimiento_inventario WHERE tenant_id=%s',(tenant,));assert cur.fetchone()['n']==77
  cur.execute('SELECT id_sucursal,stock FROM inventario WHERE tenant_id=%s ORDER BY id_sucursal',(tenant,));assert [r['stock'] for r in cur.fetchall()]==[925,998]
