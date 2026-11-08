from pathlib import Path
from datetime import datetime,timezone,timedelta
from uuid import uuid4
import json,httpx
from conftest import owner_connection

def test_prepare_a5_runtime(companies,headers):
 c=companies[0]
 with owner_connection() as conn,conn.cursor() as cur:
  cur.execute("SELECT set_config('app.tenant_id',%s,true)",(str(c['tenant']),))
  cur.execute('UPDATE inventario SET stock=1000 WHERE tenant_id=%s AND id_sucursal=%s',(c['tenant'],c['branch']))
  cur.execute('SELECT id_ciudad FROM sucursal WHERE id_sucursal=%s',(c['branch'],));city=cur.fetchone()['id_ciudad']
  cur.execute("INSERT INTO sucursal(nombre,direccion,id_ciudad) VALUES('A5 Segunda','Laboratorio efímero',%s) RETURNING id_sucursal",(city,));other=cur.fetchone()['id_sucursal']
  cur.execute('INSERT INTO inventario(id_sucursal,id_variante_prenda,stock) VALUES(%s,%s,1000)',(other,c['variant']))
 seed=str(uuid4());device=str(uuid4());now=datetime.now(timezone.utc)
 with httpx.Client(base_url='http://fashionstore-a5-runtime:8000',headers=headers[0],timeout=30) as api:
  snapshots=[api.get('/api/offline/catalogo',params={'branch_id':branch}).json() for branch in [c['branch'],other]]
  operations=[];results=[]
  for i in range(1,128):
   snap=snapshots[0 if i<=125 else 1]
   op={'operation_id':seed[:24]+f'{i:012x}','version':1,'tenant_id':c['tenant'],'author_id':c['user'],'branch_id':snap['branch']['id_sucursal'],'device_id':device,'kind':'venta','occurred_at':(now+timedelta(days=2) if i<=25 else now-timedelta(seconds=i)).isoformat(),'lease':snap['lease'],'customer_id':None,'cash_received':'50.00','original_operation':None,'items':[{'id_variante_prenda':c['variant'],'cantidad':1,'precio_unitario':'49.00' if 26<=i<=50 else '50.00'}]}
   operations.append(op)
  for offset in range(0,len(operations),20):
   response=api.post('/api/sincronizacion/lote',json={'operations':operations[offset:offset+20]});assert response.status_code==200
   results.extend(response.json()['results'])
  assert [r['state'] for r in results[:25]]==['RECHAZADA']*25
  assert [r['state'] for r in results[25:50]]==['EN_CONFLICTO']*25
  assert [r['state'] for r in results[50:]]==['CONFIRMADA']*77
  current=[api.get('/api/offline/catalogo',params={'branch_id':branch}).json() for branch in [c['branch'],other]]
  assert current[0]['products'][0]['stock']==925 and current[1]['products'][0]['stock']==998
  for offset in range(0,len(operations),20):
   response=api.post('/api/sincronizacion/lote',json={'operations':operations[offset:offset+20]});assert response.status_code==200
   assert response.json()['results']==results[offset:offset+20]
  changed={**operations[-1],'device_id':str(uuid4())}
  assert api.post('/api/sincronizacion/lote',json={'operations':[changed]}).json()['results'][0]['state']=='RECHAZADA'
  foreign=httpx.get('http://fashionstore-a5-runtime:8000/api/sincronizacion/operaciones/'+operations[-1]['operation_id'],headers=headers[1]);assert foreign.status_code==404
 fixture={'namespace':f"{c['tenant']}:{c['user']}",'header':headers[0],'before':snapshots,'after':current,'operations':operations,'results':results,'other_company':{'namespace':f"{companies[1]['tenant']}:{companies[1]['user']}",'header':headers[1]},'expected':{'first_branch_available':900,'first_branch_stock':925,'second_branch_stock':998,'sales':77,'operations':127}}
 Path('/private/runtime-fixture.json').write_text(json.dumps(fixture),encoding='utf-8')
 Path('/results/runtime-prepared.json').write_text(json.dumps({'tmpfs':True,'operations':127,'first_branch':125,'other_branch':2,'confirmed':77,'rejected':25,'conflicts':25,'replay_unchanged':True,'divergent_UUID_rejected':True,'other_company_UUID_denied':True,'stock':[925,998],'credentials_published':False}),encoding='utf-8')
