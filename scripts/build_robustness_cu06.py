"""CU06: native, editable ICONIX robustness diagram and local vector preview."""
from __future__ import annotations

import hashlib
import html
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET

from lxml import etree
from PIL import ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/diagramas_robustez'
OUT.mkdir(parents=True, exist_ok=True)
STEM = 'CU06_Diagrama_Robustez'
W, H = 2500, 2440
R = 46
BLACK = '#41474B'
REQUEST = '#9A4545'
READ = '#3D7C50'
REPLY = '#347994'
FONT_PATH = 'C:/Windows/Fonts/arial.ttf'
FONT = ImageFont.truetype(FONT_PATH, 18)

NODES = [
    dict(id='admin', kind='actor', x=135, y=1040, label='Administrador\nde empresa'),
    dict(id='encargado', kind='actor', x=135, y=1620, label='Encargado\nde sucursal'),
    dict(id='ui_categorias', kind='boundary', x=560, y=420, label='Categorías\nCategorias / CategoriaModal'),
    dict(id='ui_temporadas', kind='boundary', x=560, y=1100, label='Temporadas y colecciones\nTemporadas / TemporadaModal'),
    dict(id='ui_prendas', kind='boundary', x=560, y=1740, label='Prendas y variantes\nPrendas / PrendaModal'),
    dict(id='catalogo', kind='control', x=1130, y=1110, label='Gestión de catálogo'),
    dict(id='auditoria', kind='control', x=1130, y=2270, label='Registro de auditoría'),
    dict(id='categoria', kind='entity', x=2230, y=240, label='Categoría', table='categoria'),
    dict(id='temporada', kind='entity', x=2230, y=435, label='Temporada / colección', table='temporada'),
    dict(id='prenda', kind='entity', x=2230, y=630, label='Prenda', table='prenda'),
    dict(id='variante', kind='entity', x=2230, y=825, label='Variante de prenda', table='variante_prenda'),
    dict(id='talla', kind='entity', x=2230, y=1020, label='Talla', table='talla'),
    dict(id='color', kind='entity', x=2230, y=1215, label='Color', table='color'),
    dict(id='imagen', kind='entity', x=2230, y=1410, label='Imagen de prenda', table='imagen_prenda'),
    dict(id='sucursal', kind='entity', x=2230, y=1605, label='Sucursal', table='sucursal'),
    dict(id='inventario', kind='entity', x=2230, y=1800, label='Inventario', table='inventario'),
    dict(id='movimiento', kind='entity', x=2230, y=1995, label='Movimiento de inventario', table='movimiento_inventario'),
    dict(id='bitacora', kind='entity', x=2230, y=2270, label='Bitácora', table='bitacora'),
]
BY_ID = {n['id']: n for n in NODES}
EDGES: list[dict] = []


def anchor(node, toward, delta=0):
    angle = math.atan2(toward['y'] - node['y'], toward['x'] - node['x']) + delta
    if node['kind'] == 'actor':
        return (node['x'] + 26 * math.cos(angle), node['y'] + 26 * math.sin(angle))
    return (node['x'] + R * math.cos(angle), node['y'] + R * math.sin(angle))


def edge(a, b, label, color, *, offset=0, label_x=None, label_y=None, label_width=500, points=None):
    left, right = BY_ID[a], BY_ID[b]
    start = anchor(left, right, offset)
    end = anchor(right, left, -offset)
    if points:
        start, end = points[0], points[-1]
    else:
        points = [start, end]
    if label_x is None:
        label_x = (start[0] + end[0]) / 2
    if label_y is None:
        label_y = (start[1] + end[1]) / 2 - 24
    EDGES.append(dict(id=f'flow_{len(EDGES)+1:02}', a=a, b=b, label=label,
                      color=color, points=points, label_x=label_x, label_y=label_y,
                      label_width=label_width))


edge('admin', 'ui_categorias', 'gestionar categorías', BLACK, label_x=292, label_y=710, label_width=230)
edge('admin', 'ui_temporadas', 'gestionar temporadas\ny colecciones', BLACK, label_x=320, label_y=1002, label_width=270)
edge('admin', 'ui_prendas', 'gestionar prendas\ny variantes', BLACK, label_x=302, label_y=1330, label_width=240)
edge('encargado', 'ui_temporadas', 'gestionar temporadas\ny colecciones', BLACK,
     label_x=300, label_y=1510, label_width=270,
     points=[(160, 1610), (350, 1450), (350, 1260), (527, 1132)])

for ui, request, result, px, py in [
    ('ui_categorias', 'consultar / crear / actualizar\ninhabilitar / reactivar categorías', 'categorías actualizadas / errores', 800, 710),
    ('ui_temporadas', 'consultar / crear / actualizar\neliminar temporadas y colecciones', 'temporadas actualizadas / errores', 815, 1040),
    ('ui_prendas', 'consultar / crear / actualizar prendas\nvariantes, precios, ofertas e imagen\ninhabilitar / reactivar', 'prenda y variantes / errores', 800, 1410),
]:
    edge(ui, 'catalogo', request, REQUEST, offset=-0.22, label_x=px, label_y=py, label_width=420)
    edge('catalogo', ui, result, REPLY, offset=-0.22, label_x=px, label_y=py+94, label_width=430)

DATA = [
    ('categoria', 'consultar / validar / crear\nactualizar / inhabilitar categorías', 'categorías / validación'),
    ('temporada', 'consultar / validar / crear\nactualizar / eliminar temporadas', 'temporadas / vigencias'),
    ('prenda', 'consultar / guardar atributos, precios y ofertas\nactualizar / inhabilitar / reactivar prenda', 'prenda / validación de SKU'),
    ('variante', 'consultar / crear variantes y SKU\ncombinar talla y colores', 'variantes / combinaciones'),
    ('talla', 'listar tallas disponibles', 'tallas'),
    ('color', 'listar colores disponibles', 'colores'),
    ('imagen', 'registrar imagen principal\nreemplazar imagen principal', 'referencia de imagen'),
    ('sucursal', 'consultar sucursales activas autorizadas', 'sucursales'),
    ('inventario', 'inicializar inventario de cada variante\nconsultar existencias', 'inventario / stock conocido'),
    ('movimiento', 'registrar entrada inicial [stock inicial > 0]', 'movimiento registrado'),
]
for i, (entity, request, response) in enumerate(DATA):
    node = BY_ID[entity]
    # The same x coordinate yields a readable vertical label column for the fan.
    label_x = 1680
    fraction = (label_x - BY_ID['catalogo']['x']) / (node['x'] - BY_ID['catalogo']['x'])
    center_y = BY_ID['catalogo']['y'] + fraction * (node['y'] - BY_ID['catalogo']['y'])
    edge('catalogo', entity, request, READ, offset=-0.25, label_x=label_x,
         label_y=center_y-30, label_width=610)
    edge(entity, 'catalogo', response, REPLY, offset=-0.25, label_x=label_x,
         label_y=center_y+28, label_width=480)

edge('catalogo', 'auditoria', 'auditar cambios', BLACK, label_x=900, label_y=2050,
     label_width=200, points=[(1097, 1142), (1000, 1245), (1000, 2165), (1097, 2238)])
edge('auditoria', 'bitacora', 'registrar_bitacora()', READ, offset=-0.3,
     label_x=1680, label_y=2215, label_width=400)
edge('bitacora', 'auditoria', 'evento registrado', REPLY, offset=-0.3,
     label_x=1680, label_y=2315, label_width=400)


def wrapped(value, width, font=FONT):
    result = []
    for line in value.split('\n'):
        words = line.split()
        current = ''
        for word in words:
            proposed = (current+' '+word).strip()
            if current and font.getlength(proposed) > width:
                result.append(current)
                current = word
            else:
                current = proposed
        result.append(current)
    return result


def cell(parent, ident, value='', style='', x=0, y=0, w=0, h=0, **attrs):
    result = ET.SubElement(parent, 'mxCell', dict(id=ident, value=value, style=style,
                                                vertex='1', parent=attrs.pop('parent','1'), **attrs))
    ET.SubElement(result, 'mxGeometry', dict(x=str(x), y=str(y), width=str(w), height=str(h), **{'as':'geometry'}))
    return result


def line_native(parent, ident, points, color=BLACK, arrow=False, source=None, target=None):
    attrs = dict(id=ident, edge='1', parent='1', style=f'edgeStyle=none;rounded=0;html=0;strokeColor={color};strokeWidth=1.5;endArrow={"classic" if arrow else "none"};endFill=1;startArrow=none;')
    if source:
        attrs['source'] = f'symbol_{source}'
    if target:
        attrs['target'] = f'symbol_{target}'
    if source or target:
        for which, key, point in [('exit',source,points[0]), ('entry',target,points[-1])]:
            if key:
                node = BY_ID[key]
                ex, ey = (26,45) if node['kind']=='actor' else (R,R)
                attrs['style'] += f'{which}X={(point[0]-node["x"]+ex)/(2*ex)};{which}Y={(point[1]-node["y"]+ey)/(2*ey)};{which}Perimeter=0;'
    result=ET.SubElement(parent, 'mxCell', attrs)
    geo=ET.SubElement(result, 'mxGeometry', {'relative':'1', 'as':'geometry'})
    ET.SubElement(geo, 'mxPoint', dict(x=str(points[0][0]),y=str(points[0][1]), **{'as':'sourcePoint'}))
    ET.SubElement(geo, 'mxPoint', dict(x=str(points[-1][0]),y=str(points[-1][1]), **{'as':'targetPoint'}))
    if len(points)>2:
        array=ET.SubElement(geo,'Array', {'as':'points'})
        for px,py in points[1:-1]:
            ET.SubElement(array,'mxPoint',dict(x=str(px), y=str(py)))


def build_native():
    file=ET.Element('mxfile', dict(host='app.diagrams.net',version='29.0.0', type='device'))
    diagram=ET.SubElement(file,'diagram',dict(id='cu06-robustez',name='CU06 - Robustez'))
    model=ET.SubElement(diagram,'mxGraphModel',dict(dx=str(W),dy=str(H),grid='1',gridSize='10',guides='1',tooltips='1',connect='1',arrows='1',fold='1',page='1',pageScale='1',pageWidth=str(W),pageHeight=str(H),math='0',shadow='0'))
    root=ET.SubElement(model,'root')
    ET.SubElement(root,'mxCell',dict(id='0'))
    ET.SubElement(root,'mxCell',dict(id='1',parent='0'))
    cell(root,'frame',style='fillColor=#FFFFFF;strokeColor=#747B80;strokeWidth=1;pointerEvents=0;',x=20,y=20,w=W-40,h=H-40,connectable='0')
    cell(root,'title','CU06 - Administrar catálogo de prendas - Diagrama de robustez',
         'text;html=0;align=center;verticalAlign=middle;fontFamily=Arial;fontSize=25;fontStyle=1;strokeColor=none;fillColor=none;',x=40,y=42,w=W-80,h=54,connectable='0')
    for e in EDGES:
        line_native(root,e['id'],e['points'],e['color'],True,e['a'],e['b'])
    for e in EDGES:
        lines=wrapped(e['label'],e['label_width']-16)
        e['label_width']=min(e['label_width'],max(FONT.getlength(s) for s in lines)+22)
        height=24*len(lines)+10
        e['label_lines']=lines
        e['label_box']=[e['label_x']-e['label_width']/2,e['label_y']-height/2,e['label_width'],height]
        cell(root,e['id']+'_label','\n'.join(lines),f'text;html=0;align=center;verticalAlign=middle;whiteSpace=wrap;overflow=hidden;fontFamily=Arial;fontSize=18;fontColor={e["color"]};fillColor=#FFFFFF;strokeColor=none;spacing=4;',
             x=e['label_box'][0],y=e['label_box'][1],w=e['label_width'],h=height,connectable='0')
    for n in NODES:
        x,y=n['x'],n['y']
        if n['kind']=='actor':
            cell(root,f'symbol_{n["id"]}',style=f'shape=umlActor;html=0;fillColor=#FFFFFF;strokeColor={BLACK};strokeWidth=1.6;',x=x-26,y=y-45,w=52,h=90)
            label=n['label']
            ly=y+55
        else:
            cell(root,f'symbol_{n["id"]}',style=f'ellipse;html=0;fillColor=#FFFFFF;strokeColor={BLACK};strokeWidth=1.6;',x=x-R,y=y-R,w=2*R,h=2*R)
            if n['kind']=='boundary':
                line_native(root,f'boundary_bar_{n["id"]}',[(x-R-15,y-R),(x-R-15,y+R)])
                line_native(root,f'boundary_arm_{n["id"]}',[(x-R-15,y),(x-R,y)])
            elif n['kind']=='entity':
                line_native(root,f'entity_base_{n["id"]}',[(x-R-6,y+R+7),(x+R+6,y+R+7)])
            elif n['kind']=='control':
                line_native(root,f'control_arrow_{n["id"]}',[(x+21,y-R-6),(x+3,y-R-10),(x-16,y-R+3)],arrow=True)
            label='«'+n['kind']+'»\n'+n['label']
            ly=y+67
        label_width = 210 if n['kind']=='actor' else 380
        n['label_box']=[x-label_width/2,ly,label_width,24*len(label.splitlines())+10]
        n['display_label']=label
        cell(root,f'label_{n["id"]}',label,f'text;html=0;align=center;verticalAlign=top;whiteSpace=wrap;fontFamily=Arial;fontSize=19;fontColor={BLACK};fillColor=#FFFFFF;strokeColor=none;spacing=2;',x=n['label_box'][0],y=ly,w=label_width,h=n['label_box'][3],connectable='0')
    ET.indent(file,space='  ')
    return ET.tostring(file,encoding='utf-8',xml_declaration=True)


def svg_text(cx,cy,lines,color=BLACK,size=18,bold=False,background=False,width=None):
    height=24*len(lines)+10
    bits=[]
    if background:
        bits.append(f'<rect x="{cx-width/2}" y="{cy-height/2}" width="{width}" height="{height}" fill="white"/>')
    first_y=cy-(len(lines)-1)*12
    for i,line in enumerate(lines):
        bits.append(f'<text x="{cx}" y="{first_y+i*24}" text-anchor="middle" dominant-baseline="middle" fill="{color}" font-size="{size}" font-weight="{"bold" if bold else "normal"}">{html.escape(line)}</text>')
    return ''.join(bits)


def build_svg():
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
           '<defs>']
    for i,color in enumerate([BLACK,REQUEST,READ,REPLY]):
        parts.append(f'<marker id="arrow{i}" markerWidth="9" markerHeight="7" refX="8" refY="3.5" orient="auto" markerUnits="userSpaceOnUse"><path d="M0,0 L8,3.5 L0,7 Z" fill="{color}"/></marker>')
    parts.extend(['</defs>','<g font-family="Arial, sans-serif">',f'<rect width="{W}" height="{H}" fill="white"/>',f'<rect x="20" y="20" width="{W-40}" height="{H-40}" fill="none" stroke="#747B80"/>',svg_text(W/2,69,['CU06 - Administrar catálogo de prendas - Diagrama de robustez'],size=25,bold=True)])
    for e in EDGES:
        points=' '.join(f'{x},{y}' for x,y in e['points'])
        marker=[BLACK,REQUEST,READ,REPLY].index(e['color'])
        parts.append(f'<polyline points="{points}" fill="none" stroke="{e["color"]}" stroke-width="1.5" marker-end="url(#arrow{marker})"/>')
    for e in EDGES:
        parts.append(svg_text(e['label_x'],e['label_y'],e['label_lines'],e['color'],background=True,width=e['label_width']))
    for n in NODES:
        x,y=n['x'],n['y']
        if n['kind']=='actor':
            parts.append(f'<g stroke="{BLACK}" fill="white" stroke-width="1.6"><circle cx="{x}" cy="{y-33}" r="12"/><path d="M{x},{y-21} V{y+15} M{x-26},{y-5} H{x+26} M{x},{y+15} L{x-24},{y+45} M{x},{y+15} L{x+24},{y+45}" fill="none"/></g>')
        else:
            parts.append(f'<circle cx="{x}" cy="{y}" r="{R}" fill="white" stroke="{BLACK}" stroke-width="1.6"/>')
            if n['kind']=='boundary':
                parts.append(f'<path d="M{x-R-15},{y-R} V{y+R} M{x-R-15},{y} H{x-R}" fill="none" stroke="{BLACK}" stroke-width="1.6"/>')
            elif n['kind']=='entity':
                parts.append(f'<path d="M{x-R-6},{y+R+7} H{x+R+6}" fill="none" stroke="{BLACK}" stroke-width="1.6"/>')
            elif n['kind']=='control':
                parts.append(f'<polyline points="{x+21},{y-R-6} {x+3},{y-R-10} {x-16},{y-R+3}" fill="none" stroke="{BLACK}" stroke-width="1.6" marker-end="url(#arrow0)"/>')
        x0,y0,w,h=n['label_box']
        parts.append(svg_text(n['x'],y0+h/2,n['display_label'].splitlines(),size=19,background=True,width=w))
    parts.append('</g></svg>')
    return ''.join(parts)


SOURCES=[
    'Parcial2_backend/app/routers/categorias.py','Parcial2_backend/app/routers/temporadas.py',
    'Parcial2_backend/app/routers/prendas.py','Parcial2_backend/app/services/categoria_service.py',
    'Parcial2_backend/app/services/temporada_service.py','Parcial2_backend/app/services/prenda_service.py',
    'Parcial2_backend/app/services/bitacora_service.py','Parcial2_backend/app/schemas/prenda.py',
    'Parcial2_frontend-web/src/app/app.routes.ts',
    'Parcial2_frontend-web/src/app/features/categorias/categorias.ts',
    'Parcial2_frontend-web/src/app/features/temporadas/temporadas.ts',
    'Parcial2_frontend-web/src/app/features/prendas/prendas.ts',
    'Parcial2_frontend-web/src/app/features/prendas/prenda-modal/prenda-modal.ts',
    'docs/DOCUMENTACION PARCIAL 2/2.6_ESPECIFICACION_CASOS_DE_USO.md',
]


def validate(native):
    schema=etree.XMLSchema(etree.parse(str(ROOT/'tmp/drawio-validation/mxfile.xsd')))
    document=etree.fromstring(native)
    schema.assertValid(document)
    ids=[n.get('id') for n in document.iter('mxCell')]
    assert len(ids)==len(set(ids))
    owners={n['id']:set() for n in NODES if n['kind']=='entity'}
    for e in EDGES:
        a,b=BY_ID[e['a']],BY_ID[e['b']]
        if a['kind']=='entity' or b['kind']=='entity':
            entity,other=(a,b) if a['kind']=='entity' else (b,a)
            assert other['kind']=='control',e
            owners[entity['id']].add(other['id'])
        if a['kind']=='actor' or b['kind']=='actor':
            assert set([a['kind'],b['kind']])=={'actor','boundary'},e
        if a['kind']=='boundary' and b['kind']=='boundary':
            raise AssertionError('Boundary-to-boundary communication')
    assert all(len(v)==1 for v in owners.values())
    for n in NODES:
        x,y,w,h=n['label_box']
        assert x>=20 and y>=20 and x+w<W-20 and y+h<H-20,n
    for e in EDGES:
        x,y,w,h=e['label_box']
        assert x>=20 and y>=20 and x+w<W-20 and y+h<H-20,e
        assert all(FONT.getlength(s)<=w-10 for s in e['label_lines']),e
    return dict(xsd_valido=True,ids_unicos=True,entidades_sin_comunicacion_directa=True,
                cada_entidad_tiene_un_unico_control=True,actores_solo_con_interfaces=True,
                sin_interfaces_interconectadas=True,etiquetas_dentro_del_lienzo=True,
                actores=2,interfaces=3,controles=2,entidades=len(owners),comunicaciones=len(EDGES),
                control_por_entidad={k:next(iter(v)) for k,v in owners.items()})


if __name__=='__main__':
    native=build_native()
    report=validate(native)
    (OUT/(STEM+'.drawio')).write_bytes(native)
    (OUT/(STEM+'.svg')).write_text(build_svg(),encoding='utf-8')
    trace=dict(caso='CU06 - Administrar catálogo de prendas',nodes=NODES,edges=EDGES,
               fuentes=[dict(archivo=s,sha256=hashlib.sha256((ROOT/s).read_bytes()).hexdigest()) for s in SOURCES],
               alcance='Vista de robustez: controles de análisis agrupados por responsabilidad; no son clases ORM ni una secuencia temporal.',
               correspondencia_controles={'catalogo':['routers/categorias.py','routers/temporadas.py','routers/prendas.py','services/categoria_service.py','services/temporada_service.py','services/prenda_service.py'], 'auditoria':['services/bitacora_service.py']},
               diferencias_ficha_codigo=[
                   'La ficha incluye Responsable de inventario y compras; la ruta web /prendas y sus escrituras actuales requieren Administrador. No se concede acceso inexistente en este diagrama.',
                   'La ruta web /temporadas permite Administrador y Encargado de Sucursal; se representa ese actor únicamente en esa interfaz.',
                   'Temporadas y colecciones comparten temporada: no existe una entidad coleccion separada.',
                   'Precios, umbral mayorista y oferta son atributos de prenda, no tablas separadas.',
                   'El modelo de análisis incluye el registro de inventario y movimientos iniciales porque crear_prenda llama _crear_variante; el efecto del trigger no se dibuja como una llamada entidad-entidad.'
               ])
    (OUT/(STEM+'_Trazabilidad.json')).write_text(json.dumps(trace,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/(STEM+'_Validacion.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))
