"""Build the principal ER model from the verified PostgreSQL catalog inventory."""
from pathlib import Path
import hashlib, json, re

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/diagrama_entidad_relacion'
OUT.mkdir(exist_ok=True)
INV=ROOT/'docs/diseno_fisico_base_datos/INVENTARIO_ORIGEN.json'
inventory=json.loads(INV.read_text(encoding='utf-8-sig'))

GROUPS=[
 ('saas','Administración SaaS','#dce9fa',['empresa','plan','suscripcion']),
 ('acceso','Identidad y autorización','#e8e1f5',['cuenta_global','rol','permiso','usuario','rol_permiso','usuario_sucursal']),
 ('organizacion','Organización y clientes','#dceee9',['ciudad','sucursal','cliente']),
 ('catalogo','Catálogo de prendas','#e4eedb',['categoria','temporada','prenda','imagen_prenda','talla','color','variante_prenda','variante_color']),
 ('inventario','Abastecimiento e inventario','#fff0d2',['proveedor','compra','detalle_compra','inventario','movimiento_inventario']),
 ('comercio','Reservas y ventas','#dcecf5',['reserva','detalle_reserva','retencion','venta','detalle_venta']),
 ('pagos','Pagos y comprobantes','#f8e4d7',['pago_transaccion','comprobante']),
 ('cambios','Cambios y notificaciones','#f4e1e8',['cambio','ajuste_monetario','notificacion']),
 ('servicios','Sincronización, reportes y auditoría','#e8e8e8',['operacion_sync','reporte_resultado','bitacora']),
]
EXTRAS={
 'empresa':['slug','nombre','activa'], 'plan':['nombre','max_sucursales','reportes_ia'],
 'suscripcion':['inicio','vencimiento'], 'cuenta_global':['correo','tipo','estado'],
 'usuario':['correo','estado'], 'rol':['nombre'], 'permiso':['codigo','modulo'],
 'ciudad':['nombre'], 'sucursal':['nombre','activa'], 'cliente':['ci','nombre_completo','correo'],
 'categoria':['nombre','estado'], 'temporada':['nombre','fecha_inicio','fecha_fin'],
 'prenda':['sku','nombre','precio_base','precio_mayorista','precio_oferta','estado'],
 'imagen_prenda':['url_imagen','es_principal'], 'talla':['nombre'], 'color':['nombre','codigo_hex'],
 'variante_prenda':['sku_variante','precio_adicional'], 'proveedor':['nit','razon_social'],
 'compra':['fecha','total'], 'detalle_compra':['cantidad','costo_unitario'], 'inventario':['stock'],
 'movimiento_inventario':['tipo','cantidad','fecha'], 'reserva':['estado','fecha_limite','total'],
 'detalle_reserva':['cantidad','precio_unitario'], 'retencion':['cantidad','vence'],
 'venta':['metodo_pago','total','fecha_venta'], 'detalle_venta':['cantidad','precio_unitario','subtotal'],
 'pago_transaccion':['transaccion_id','monto','estado_pago'],
 'comprobante':['numero_comprobante','fecha_emision'], 'cambio':['estado','cantidad','credito','diferencia'],
 'ajuste_monetario':['tipo','importe','referencia'], 'notificacion':['titulo','leida'],
 'operacion_sync':['kind','state','created_at'], 'reporte_resultado':['filters','result','expires_at'],
 'bitacora':['accion','tabla_afectada','fecha'],
}

def cols(text):return [s.strip().strip('"') for s in text.split(',')]
constraints={t:[] for _,_,_,ts in GROUPS for t in ts}
for item in inventory['constraints']:
 if item['relname'] in constraints:constraints[item['relname']].append(item)
all_columns={t:{c['attname']:c for c in inventory['columns'] if c['relname']==t} for t in constraints}
raw_fks=[]
pk={}
for table,items in constraints.items():
 pk[table]=cols(next(x['definition'] for x in items if x['contype']=='p')[13:-1])
 for item in items:
  if item['contype']!='f':continue
  m=re.match(r'FOREIGN KEY \((.*?)\) REFERENCES (?:(\w+)\.)?(\w+)\((.*?)\)',item['definition'])
  assert m,item
  raw_fks.append(dict(child=table,columns=cols(m[1]),parent=m[3],ref_columns=cols(m[4]),constraint=item['conname'],definition=item['definition']))

# Suppress redundant single-column FK drawings when a tenant-composite FK
# expresses the same business link. Keep every source constraint in provenance.
canonical=[]
for fk in raw_fks:
 duplicate=any(other is not fk and other['child']==fk['child'] and other['parent']==fk['parent'] and
  set(zip(fk['columns'],fk['ref_columns'])) < set(zip(other['columns'],other['ref_columns'])) for other in raw_fks)
 if not duplicate:canonical.append(fk)

company_links={'suscripcion','sucursal','rol','cliente','prenda','proveedor','operacion_sync','bitacora'}
edges=[];omitted=[]
for fk in canonical:
 if fk['parent'] not in constraints:omitted.append(dict(**fk,reason='Tabla técnica fuera de esta vista principal.'));continue
 if fk['parent']=='empresa' and fk['columns']==['tenant_id'] and fk['child'] not in company_links:
  omitted.append(dict(**fk,reason='Pertenencia empresarial indicada por tenant_id FK; enlace repetitivo omitido.'));continue
 optional=any(not all_columns[fk['child']][c]['attnotnull'] for c in fk['columns'])
 unique=[]
 for k in constraints[fk['child']]:
  if k['contype'] in ('p','u'):
   unique.append(cols(re.search(r'\((.*?)\)',k['definition'])[1]))
 # A partial unique index on non-null reservation IDs also enforces one sale
 # at most per reservation. It is recorded explicitly in the verified source.
 unique_indexes=[i for i in inventory['indexes'] if i['table_name']==fk['child'] and i['definition'].startswith('CREATE UNIQUE INDEX ')]
 for index in unique_indexes:
  match=re.search(r'USING btree \(([^()]*)\)(?: WHERE (.*))?$',index['definition'])
  if match and (not match[2] or match[2]=='(id_reserva IS NOT NULL)'):
   unique.append(cols(match[1]))
 one=any(set(u)<=set(fk['columns']) for u in unique)
 edges.append(dict(**fk,id='relation_'+str(len(edges)+1),parent_cardinality='0..1' if optional else '1',child_cardinality='0..1' if one else '0..*',color='#40546b'))

entities=[]
for group,title,color,tables in GROUPS:
 for table in tables:
  fk_fields={c for fk in raw_fks if fk['child']==table for c in fk['columns']}
  selected=set(pk[table])|fk_fields|set(EXTRAS.get(table,[]))
  assert selected<=set(all_columns[table]),(table,selected-set(all_columns[table]))
  fields=[]
  for name,column in all_columns[table].items():
   if name not in selected:continue
   key=('PK' if name in pk[table] else '')+('/FK' if name in pk[table] and name in fk_fields else 'FK' if name in fk_fields else '')
   dtype=column['type'].replace('character varying','varchar').replace('timestamp with time zone','timestamptz').replace('timestamp without time zone','timestamp').replace('integer','int').replace('boolean','bool')
   fields.append(dict(name=name,type=dtype,key=key,nullable=not column['attnotnull']))
  # Key fields first, preserving catalog order within each category.
  fields.sort(key=lambda c:(0 if 'PK' in c['key'] else 1 if 'FK' in c['key'] else 2))
  entities.append(dict(id=table,group=group,color=color,title=table,fields=fields,width=420,height=36+24*len(fields)))

model=dict(title='FashionStore · Diagrama entidad-relación general',entities=entities,edges=edges,
 groups=[dict(id=g,title=t,color=c) for g,t,c,_ in GROUPS],
 source=str(INV.relative_to(ROOT)),source_sha256=hashlib.sha256(INV.read_bytes()).hexdigest(),
 scope='Vista principal de PostgreSQL. Atributos seleccionados; pertenencia empresarial común indicada por tenant_id FK. No representa IndexedDB ni SQLite.',
 omitted_relationships=omitted,source_foreign_keys=raw_fks)
(OUT/'MODELO_ER_VERIFICADO.json').write_text(json.dumps(model,ensure_ascii=False,indent=2),encoding='utf-8')

dot=['digraph FashionStore {',
 'graph [rankdir=LR, splines=ortho, nodesep=0.65, ranksep=1.4, pad=0.5, compound=true, newrank=true, concentrate=false, outputorder=edgesfirst];',
 'node [shape=box, fixedsize=true, label="", margin=0];',
 'edge [arrowhead=none,arrowtail=none];']
for g,title,color,tables in GROUPS:
 dot.append('subgraph cluster_'+g+' { graph [label='+json.dumps(title)+', fontsize=18, margin=28];')
 for entity in entities:
  if entity['group']==g:dot.append(entity['id']+f' [width={entity["width"]/72},height={entity["height"]/72}];')
 dot.append('}')
for edge in edges:
 dot.append(f'{edge["parent"]} -> {edge["child"]} [id="{edge["id"]}", weight='+('0.4' if edge['parent']=='empresa' else '2')+'];')
dot.append('}')
(OUT/'layout.dot').write_text('\n'.join(dot),encoding='utf-8')
print(json.dumps(dict(tables=len(entities),relationships=len(edges),omitted_relationships=len(omitted)),ensure_ascii=False))
