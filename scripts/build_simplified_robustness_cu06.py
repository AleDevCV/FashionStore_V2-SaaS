"""Short, single-page CU06: six actions, five essential entities, 37 messages."""
from collections import defaultdict
import ast
import csv
import hashlib
import json
from pathlib import Path
import re

from lxml import etree
import build_numbered_robustness_cu06 as draw

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/diagramas_robustez/CU06_Simplificado'
OUT.mkdir(parents=True,exist_ok=True)
STEM='CU06_Robustez_Simplificada'
draw.M=[]
draw.A=[]
draw.NODES={k:draw.NODES[k].copy() for k in ['actor','b_pre','control','categoria','temporada','prenda','variante','bitacora']}
draw.NODES['b_pre']['name']='Frontend : Administración del catálogo'
draw.NODES['b_pre']['sources']=[
    'Parcial2_frontend-web/src/app/features/categorias/categorias.ts',
    'Parcial2_frontend-web/src/app/features/temporadas/temporadas.ts',
    'Parcial2_frontend-web/src/app/features/prendas/prendas.ts',
]
draw.NODES['b_pre'].pop('source',None)


def begin(name,fn,args,source,kind='invoke'):
    draw.start(name,'catalogo','b_pre',kind)
    draw.invoke(fn,args,source)


def end(result,show=None):
    draw.msg('control','b_pre',result,'reply')
    if show:draw.msg('b_pre','actor',show,'reply')
    draw.A[-1]['last']=len(draw.M)


begin('Consultar catálogo','listar_prendas','filtros',draw.PRE_R,'read')
draw.read('prenda','listar_prendas','filtros','prendas',draw.PRE_S)
end('catálogo','Mostrar catálogo')

begin('Registrar categoría','crear_categoria','datos',draw.CAT_R)
draw.write('categoria','crear_categoria(datos)',draw.CAT_S,'crear_categoria')
draw.msg('categoria','control','id_categoria','reply')
draw.audit('categoria','INSERT')
end('categoría registrada')

begin('Registrar temporada o colección','crear_temporada','datos',draw.TEMP_R)
draw.write('temporada','crear_temporada(datos)',draw.TEMP_S,'crear_temporada')
draw.msg('temporada','control','temporada creada','reply')
draw.audit('temporada','INSERT')
end('temporada registrada')

begin('Registrar prenda y variantes','crear_prenda','datos',draw.PRE_R)
draw.write('prenda','crear_prenda(datos)',draw.PRE_S,'crear_prenda')
draw.msg('prenda','control','id_prenda','reply')
draw.write('variante','_crear_variante(datos) [por variante]',draw.PRE_S,'_crear_variante')
draw.msg('variante','control','variante creada','reply')
draw.audit('prenda','INSERT')
end('prenda con variantes','Mostrar prenda registrada')

begin('Editar datos, precios y ofertas','actualizar_prenda','id, cambios',draw.PRE_R)
draw.write('prenda','actualizar_prenda(id, cambios)',draw.PRE_S,'actualizar_prenda')
draw.audit('prenda','UPDATE')
end('prenda actualizada')

begin('Inhabilitar prenda','inhabilitar_prenda','id',draw.PRE_R)
draw.write('prenda','inhabilitar_prenda(id)',draw.PRE_S,'inhabilitar_prenda')
draw.audit('prenda','INACTIVAR')
end('prenda inactiva')

assert len(draw.M)==37
grouped=defaultdict(list)
for m in draw.M:grouped[draw.pair_key(m)].append(m)
positions={
 'actor':dict(x=180,y=1050),
 'b_pre':dict(x=1100,y=1050),
 'control':dict(x=2400,y=1050),
 'categoria':dict(x=4300,y=260),
 'temporada':dict(x=4300,y=650),
 'prenda':dict(x=4300,y=1050),
 'variante':dict(x=4300,y=1490),
 'bitacora':dict(x=4300,y=2050),
}
view=dict(name='CU06 - Robustez simplificada',title='CU06 - Administrar catálogo de prendas - Diagrama de robustez',width=4600,height=2350,nodes=positions,groups=[])
for pair,messages in grouped.items():
    a,b=positions[pair[0]],positions[pair[1]]
    if pair[0]=='actor':width,cx=600,650
    elif pair[0]=='control':width,cx=1050,3300
    else:width,cx=550,1650
    line_y=b['y'] if pair[0]=='control' else a['y']
    if pair[0]=='actor':points=[(a['x']+35,line_y),(b['x']-65,line_y)]
    elif pair[0]=='control':points=[(a['x']+65,a['y']),(2720,line_y),(b['x']-65,line_y)]
    else:points=[(a['x']+65,line_y),(b['x']-65,line_y)]
    g=draw.group_geometry(pair,messages,width)
    rows=[]
    yy=line_y-38-g['upper']
    for m in g['calls']:
        height=draw.message_height(m,width)
        rows.append(dict(n=m['n'],x=cx,y=yy+height/2,width=width,height=height,forward=True))
        yy+=height
    yy=line_y+38
    for m in g['returns']:
        height=draw.message_height(m,width)
        rows.append(dict(n=m['n'],x=cx,y=yy+height/2,width=width,height=height,forward=False))
        yy+=height
    view['groups'].append(dict(pair=list(pair),points=points,rows=rows))
draw.VIEWS=[view]

# Validate method names against current source without executing application code.
owners=defaultdict(set)
sources={}
for m in draw.M:
    if m['source']:
        if m['source'] not in sources:
            tree=ast.parse((ROOT/m['source']).read_text(encoding='utf-8-sig'))
            sources[m['source']]={n.name:n.lineno for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
        assert m['symbol'] in sources[m['source']]
        m['line']=sources[m['source']][m['symbol']]
    assert not re.search(r'\b(GET|POST|PUT|PATCH|DELETE|HTTP)\b',m['text'])
    ka,kb=draw.NODES[m['a']]['kind'],draw.NODES[m['b']]['kind']
    if 'entity' in (ka,kb):
        assert set((ka,kb))=={'entity','control'}
        e=m['a'] if ka=='entity' else m['b']
        c=m['b'] if ka=='entity' else m['a']
        owners[e].add(c)
    if 'actor' in (ka,kb):assert set((ka,kb))=={'actor','boundary'}
assert len(owners)==5 and all(v=={'control'} for v in owners.values())
native=draw.drawio()
doc=etree.fromstring(native)
etree.XMLSchema(etree.parse(str(ROOT/'tmp/drawio-validation/mxfile.xsd'))).assertValid(doc)
ids=[c.get('id') for c in doc.iter('mxCell')]
assert len(ids)==len(set(ids))
assert sorted(int(i[8:]) for i in ids if i.startswith('message_'))==list(range(1,38))
for g in view['groups']:
    rows=sorted(g['rows'],key=lambda r:r['y'])
    assert all(a['y']+a['height']/2<=b['y']-b['height']/2 for a,b in zip(rows,rows[1:]))
    for row in rows:
        assert row['y']-row['height']/2>115 and row['y']+row['height']/2<view['height']-20

(OUT/(STEM+'.drawio')).write_bytes(native)
(OUT/(STEM+'_General.svg')).write_text(draw.svg(view,0),encoding='utf-8')
all_sources=set(sources)|set(draw.NODES['b_pre']['sources'])
scope={
 'nivel':'Vista resumida de los recorridos principales. No es un inventario de todas las tablas o funciones del CU.',
 'interfaz':'Agrupa las pantallas actuales de categorías, temporadas y prendas; no introduce una pantalla nueva en la aplicación.',
 'control':'Responsabilidad de análisis que agrupa los routers y servicios existentes; no es una clase Python nueva.',
 'conservado':['Categoría','Temporada / colección','Prenda','Variante de prenda','Bitácora'],
 'omitido_del_dibujo':['Talla','Color','Imagen de prenda','Sucursal','Inventario','Movimiento de inventario'],
 'resumen':'Las validaciones, consultas auxiliares, relecturas y efectos internos de stock permanecen dentro de las operaciones del control. No se eliminan ni cambian en el programa.',
 'variantes':'Talla y colores se expresan como datos de las variantes; sus catálogos auxiliares se omiten de esta vista.',
 'respuestas':'Las escrituras sin datos devueltos y la bitácora no reciben retornos ficticios.',
 'alternativas':'La edición y reactivación de categorías/temporadas y otras alternativas siguen implementadas; no se despliegan todos sus mensajes en este resumen.',
 'alcance':'Recorrido principal del administrador; no se añaden permisos nuevos al responsable de inventario.',
}
model=dict(title='CU06 - Administrar catálogo de prendas',nodes=draw.NODES,messages=draw.M,actions=draw.A,views=[view],exports=['General'],scope=scope,
           sources=[dict(file=f,sha256=hashlib.sha256((ROOT/f).read_bytes()).hexdigest()) for f in sorted(all_sources)])
(OUT/(STEM+'_Modelo.json')).write_text(json.dumps(model,ensure_ascii=False,indent=2),encoding='utf-8')
with (OUT/'MENSAJES_CU06.csv').open('w',encoding='utf-8-sig',newline='') as f:
    writer=csv.writer(f);writer.writerow(['numero','origen','destino','mensaje','archivo','linea'])
    for m in draw.M:writer.writerow([m['n'],m['a'],m['b'],m['text'],m['source'],m.get('line','')])
report=dict(actores=1,interfaces=1,controles=1,entidades=5,acciones=6,mensajes=37,paginas=1,
            entidades_sin_comunicacion_directa=True,un_control_por_entidad=True,numeracion_consecutiva=True,
            bitacora_conservada=True,metodos_existentes_comprobados=True,xsd_valido=True,filas_sin_solapamiento=True)
(OUT/(STEM+'_Validacion.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
