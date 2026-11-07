"""Shared, source-backed communication/robustness model for draw.io and EA."""
from __future__ import annotations

import ast
from collections import defaultdict
import csv
import hashlib
import html
import json
import math
from pathlib import Path
import re
import xml.etree.ElementTree as ET

from lxml import etree
from PIL import ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/diagramas_robustez/CU06_Numerado'
OUT.mkdir(parents=True, exist_ok=True)
STEM = 'CU06_Robustez_Numerada'
FONT = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 24)
BOLD = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', 25)
COLORS = {'read':'#28343E', 'invoke':'#215D9C', 'write':'#AC3636', 'reply':'#287947', 'ui':'#28343E'}
BASE = 'Parcial2_backend/app/'
CAT_R, CAT_S = BASE+'routers/categorias.py', BASE+'services/categoria_service.py'
TEMP_R, TEMP_S = BASE+'routers/temporadas.py', BASE+'services/temporada_service.py'
PRE_R, PRE_S = BASE+'routers/prendas.py', BASE+'services/prenda_service.py'
BIT_S = BASE+'services/bitacora_service.py'
M: list[dict] = []
A: list[dict] = []

NODES = {
 'actor':dict(kind='actor',name='Administrador de empresa'),
 'b_cat':dict(kind='boundary',name='Frontend : Categorías',source='Parcial2_frontend-web/src/app/features/categorias/categorias.ts'),
 'b_temp':dict(kind='boundary',name='Frontend : Temporadas y colecciones',source='Parcial2_frontend-web/src/app/features/temporadas/temporadas.ts'),
 'b_pre':dict(kind='boundary',name='Frontend : Prendas y variantes',source='Parcial2_frontend-web/src/app/features/prendas/prendas.ts'),
 'control':dict(kind='control',name='Backend : Gestión del catálogo'),
 'categoria':dict(kind='entity',name='Categoría',table='categoria'),
 'temporada':dict(kind='entity',name='Temporada / colección',table='temporada'),
 'prenda':dict(kind='entity',name='Prenda',table='prenda'),
 'variante':dict(kind='entity',name='Variante de prenda',table='variante_prenda'),
 'talla':dict(kind='entity',name='Talla',table='talla'),
 'color':dict(kind='entity',name='Color',table='color'),
 'imagen':dict(kind='entity',name='Imagen de prenda',table='imagen_prenda'),
 'sucursal':dict(kind='entity',name='Sucursal',table='sucursal'),
 'inventario':dict(kind='entity',name='Inventario',table='inventario'),
 'movimiento':dict(kind='entity',name='Movimiento de inventario',table='movimiento_inventario'),
 'bitacora':dict(kind='entity',name='Bitácora',table='bitacora'),
}


def start(name, area, boundary, kind='invoke'):
    action=dict(id=len(A)+1,name=name,area=area,boundary=boundary,first=len(M)+1,kind=kind)
    A.append(action)
    msg('actor',boundary,name,'ui')
    return action


def msg(a,b,text,kind='read',source=None,symbol=None):
    M.append(dict(n=len(M)+1,action=A[-1]['id'],area=A[-1]['area'],a=a,b=b,text=text,
                  kind=kind,color=COLORS[kind],source=source,symbol=symbol))


def invoke(symbol,args,source):
    msg(A[-1]['boundary'],'control',symbol+'('+args+')',A[-1]['kind'],source,symbol)


def read(entity,symbol,args,result,source,guard=''):
    msg('control',entity,symbol+'('+args+')'+(' '+guard if guard else ''),'read',source,symbol)
    msg(entity,'control',result,'reply')


def write(entity,text,source,symbol):
    msg('control',entity,text,'write',source,symbol)


def audit(table,action):
    event={'INSERT':'alta','UPDATE':'modificación','INACTIVAR':'baja lógica','DELETE':'eliminación'}[action]
    write('bitacora','registrar_bitacora('+table+', '+event+')',BIT_S,'registrar_bitacora')


def finish(result,display):
    msg('control',A[-1]['boundary'],result,'reply')
    msg(A[-1]['boundary'],'actor',display,'reply')
    A[-1]['last']=len(M)


start('Consultar categorías','categorias','b_cat','read')
invoke('listar_categorias','estado',CAT_R)
read('categoria','listar_categorias','estado','lista de categorías',CAT_S)
finish('categorías','Mostrar árbol de categorías')

start('Registrar categoría','categorias','b_cat')
invoke('crear_categoria','datos',CAT_R)
read('categoria','existe_nombre','nombre','nombre disponible',CAT_S)
read('categoria','existe_categoria','id_padre','categoría padre válida',CAT_S,'[si se indicó padre]')
write('categoria','crear_categoria(datos)',CAT_S,'crear_categoria')
msg('categoria','control','id_categoria','reply')
audit('categoria','INSERT')
read('categoria','obtener_categoria','id_categoria','categoría creada',CAT_S)
finish('categoría creada','Mostrar categoría registrada')

start('Editar categoría','categorias','b_cat')
invoke('actualizar_categoria','id_categoria, cambios',CAT_R)
read('categoria','obtener_categoria','id_categoria','categoría actual',CAT_S)
read('categoria','existe_nombre','nombre, excluir_id','nombre válido',CAT_S,'[si cambia nombre]')
read('categoria','existe_categoria','id_padre','padre válido',CAT_S,'[si cambia padre]')
write('categoria','actualizar_categoria(id_categoria, cambios)',CAT_S,'actualizar_categoria')
audit('categoria','UPDATE')
read('categoria','obtener_categoria','id_categoria','categoría actualizada',CAT_S)
finish('categoría actualizada','Mostrar cambios guardados')

start('Inhabilitar categoría','categorias','b_cat')
invoke('inhabilitar_categoria','id_categoria',CAT_R)
read('categoria','obtener_categoria','id_categoria','categoría activa',CAT_S)
read('categoria','tiene_subcategorias','id_categoria','sin subcategorías activas',CAT_S)
write('categoria','inhabilitar_categoria(id_categoria)',CAT_S,'inhabilitar_categoria')
audit('categoria','INACTIVAR')
finish('inhabilitación confirmada','Mostrar categoría inactiva')

start('Reactivar categoría','categorias','b_cat')
invoke('actualizar_categoria',"id_categoria, estado='Activo'",CAT_R)
read('categoria','obtener_categoria','id_categoria','categoría actual',CAT_S)
write('categoria',"actualizar_categoria(id_categoria, estado='Activo')",CAT_S,'actualizar_categoria')
audit('categoria','UPDATE')
read('categoria','obtener_categoria','id_categoria','categoría activa',CAT_S)
finish('reactivación confirmada','Mostrar categoría reactivada')

start('Consultar temporadas y colecciones','temporadas','b_temp','read')
invoke('listar_temporadas','búsqueda, estado, vigencia',TEMP_R)
read('temporada','listar_temporadas','filtros','temporadas y vigencias',TEMP_S)
finish('temporadas','Mostrar temporadas y colecciones')

start('Registrar temporada o colección','temporadas','b_temp')
invoke('crear_temporada','datos',TEMP_R)
read('temporada','existe_nombre_temporada','nombre','nombre disponible',TEMP_S)
write('temporada','crear_temporada(datos) [fechas válidas]',TEMP_S,'crear_temporada')
msg('temporada','control','temporada creada','reply')
audit('temporada','INSERT')
finish('temporada creada','Mostrar temporada registrada')

start('Editar temporada o colección','temporadas','b_temp')
invoke('actualizar_temporada','id_temporada, cambios',TEMP_R)
read('temporada','obtener_temporada_por_id','id_temporada','temporada actual',TEMP_S)
read('temporada','existe_nombre_temporada','nombre, excluir_id','nombre disponible',TEMP_S,'[si cambia nombre]')
write('temporada','actualizar_temporada(id_temporada, cambios) [fechas válidas]',TEMP_S,'actualizar_temporada')
audit('temporada','UPDATE')
read('temporada','obtener_temporada_por_id','id_temporada','temporada actualizada',TEMP_S)
finish('temporada actualizada','Mostrar cambios guardados')

start('Eliminar temporada o colección','temporadas','b_temp')
invoke('eliminar_temporada','id_temporada',TEMP_R)
read('temporada','obtener_temporada_por_id','id_temporada','temporada existente',TEMP_S)
write('temporada','eliminar_temporada(id_temporada)',TEMP_S,'eliminar_temporada')
audit('temporada','DELETE')
finish('eliminación confirmada','Mostrar temporada eliminada')

start('Consultar prendas y preparar formulario','prendas','b_pre','read')
invoke('listar_prendas','búsqueda, categoría, género, estado',PRE_R)
read('prenda','listar_prendas','filtros','lista de prendas',PRE_S)
msg('control','b_pre','prendas','reply')
invoke('listar_categorias','estado',CAT_R)
read('categoria','listar_categorias','estado','categorías disponibles',CAT_S)
msg('control','b_pre','categorías','reply')
invoke('listar_tallas','',PRE_R)
read('talla','listar_tallas','','tallas disponibles',PRE_S)
msg('control','b_pre','tallas','reply')
invoke('listar_colores','',PRE_R)
read('color','listar_colores','','colores disponibles',PRE_S)
msg('control','b_pre','colores','reply')
msg('b_pre','actor','Mostrar prendas y opciones del formulario','reply')
A[-1]['last']=len(M)

start('Registrar prenda y variantes','prendas','b_pre')
invoke('crear_prenda','datos, variantes, precios, ofertas',PRE_R)
read('prenda','existe_sku','sku','SKU disponible',PRE_S)
read('categoria','existe_categoria','id_categoria','categoría válida',CAT_S)
write('prenda','crear_prenda(datos maestros y comerciales)',PRE_S,'crear_prenda')
msg('prenda','control','id_prenda','reply')
write('imagen','Guardar imagen principal [si se indicó URL]',PRE_S,'crear_prenda')
read('sucursal','_listar_ids_sucursales','','sucursales activas autorizadas',PRE_S)
write('variante','_crear_variante(talla, color_ids, SKU) [por variante]',PRE_S,'_crear_variante')
msg('variante','control','id_variante','reply')
write('inventario','Inicializar fila con stock=0 [por variante y sucursal]',PRE_S,'_crear_variante')
write('movimiento','Registrar Entrada inicial [stock inicial > 0]',PRE_S,'_crear_variante')
audit('prenda','INSERT')
read('prenda','obtener_prenda','id_prenda','datos maestros creados',PRE_S)
read('variante','listar_variantes','id_prenda','variantes y existencias',PRE_S)
finish('prenda creada con variantes','Mostrar prenda registrada')

start('Editar prenda, precios y ofertas','prendas','b_pre')
invoke('actualizar_prenda','id_prenda, cambios',PRE_R)
read('prenda','obtener_prenda','id_prenda, con_variantes=False','prenda actual',PRE_S)
read('prenda','existe_sku','sku, excluir_id','SKU disponible',PRE_S,'[si cambia SKU]')
read('categoria','existe_categoria','id_categoria','categoría válida',CAT_S,'[si cambia categoría]')
write('prenda','actualizar_prenda(id_prenda, atributos, precios, ofertas)',PRE_S,'actualizar_prenda')
read('imagen','_reemplazar_imagen_principal','id_prenda, url_imagen','referencia actual comprobada',PRE_S,'[si cambia URL]')
write('imagen','Conservar anterior como secundaria y guardar principal [si difiere]',PRE_S,'_reemplazar_imagen_principal')
audit('prenda','UPDATE')
read('prenda','obtener_prenda','id_prenda','prenda actualizada',PRE_S)
read('variante','listar_variantes','id_prenda','variantes conservadas',PRE_S)
finish('prenda actualizada','Mostrar cambios guardados')

start('Inhabilitar prenda','prendas','b_pre')
invoke('inhabilitar_prenda','id_prenda',PRE_R)
read('prenda','obtener_prenda','id_prenda, con_variantes=False','prenda activa',PRE_S)
write('prenda','inhabilitar_prenda(id_prenda)',PRE_S,'inhabilitar_prenda')
audit('prenda','INACTIVAR')
finish('inhabilitación confirmada','Mostrar prenda inactiva')

start('Reactivar prenda','prendas','b_pre')
invoke('actualizar_prenda',"id_prenda, estado='Activo'",PRE_R)
read('prenda','obtener_prenda','id_prenda, con_variantes=False','prenda actual',PRE_S)
write('prenda',"actualizar_prenda(id_prenda, estado='Activo')",PRE_S,'actualizar_prenda')
audit('prenda','UPDATE')
read('prenda','obtener_prenda','id_prenda','prenda activa',PRE_S)
read('variante','listar_variantes','id_prenda','variantes conservadas',PRE_S)
finish('reactivación confirmada','Mostrar prenda reactivada')

start('Intentar registrar un SKU existente','prendas','b_pre')
invoke('crear_prenda','datos con SKU repetido',PRE_R)
read('prenda','existe_sku','sku','SKU ya registrado',PRE_S)
finish('rechazo: SKU duplicado','Mostrar validación sin registrar la prenda')


def wrap(value,width,font=FONT):
    result=[]
    for part in value.split('\n'):
        current=''
        for word in part.split():
            next_text=(current+' '+word).strip()
            if current and font.getlength(next_text)>width:
                result.append(current)
                current=word
            else: current=next_text
        if current: result.append(current)
    return result or ['']


ORDER={k:i for i,k in enumerate(NODES)}
RANK={'actor':0,'boundary':1,'control':2,'entity':3}


def pair_key(m):
    return tuple(sorted([m['a'],m['b']],key=lambda k:(RANK[NODES[k]['kind']],ORDER[k])))


def message_height(m,width):
    return max(44, len(wrap(str(m['n'])+': '+m['text'],width-85))*32+12)


def group_geometry(pair,messages,width):
    calls=[m for m in messages if m['a']==pair[0]]
    returns=[m for m in messages if m['a']!=pair[0]]
    upper=sum(message_height(m,width) for m in calls)
    lower=sum(message_height(m,width) for m in returns)
    return dict(pair=list(pair),calls=calls,returns=returns,width=width,upper=upper,lower=lower,height=upper+lower+240)


def layout(name,messages):
    groups=defaultdict(list)
    for m in messages:groups[pair_key(m)].append(m)
    entities=[k for k in NODES if NODES[k]['kind']=='entity' and ('control',k) in groups]
    boundaries=[k for k in ['b_cat','b_temp','b_pre'] if ('actor',k) in groups]
    geom={p:group_geometry(p,ms,1500 if p[0]=='control' else 1050) for p,ms in groups.items()}
    right_height=sum(geom[('control',e)]['height'] for e in entities)+200
    left_slots={b:max(geom[('actor',b)]['height'],geom[(b,'control')]['height'])+180 for b in boundaries}
    left_height=sum(left_slots.values())+200
    height=max(right_height,left_height,1500)
    positions={'actor':dict(x=180,y=height/2),'control':dict(x=3140,y=height/2)}
    cursor=140+(height-right_height)/2
    for e in entities:
        g=geom[('control',e)]
        line_y=cursor+g['upper']+90
        positions[e]=dict(x=5690,y=line_y)
        g.update(x=4410,y=line_y)
        cursor+=g['height']
    cursor=140+(height-left_height)/2
    for b in boundaries:
        mid=cursor+left_slots[b]/2
        positions[b]=dict(x=1510,y=mid)
        geom[('actor',b)].update(x=820,y=mid)
        geom[(b,'control')].update(x=2320,y=mid)
        cursor+=left_slots[b]
    view=dict(name=name,width=6000,height=int(height+180),nodes=positions,groups=[])
    for p,g in geom.items():
        source,target=positions[p[0]],positions[p[1]]
        y=g['y']
        if p[0]=='actor':points=[(source['x']+40,source['y']),(340,y),(target['x']-65,y)]
        elif p[0]=='control':points=[(source['x']+65,source['y']),(3500,y),(target['x']-65,y)]
        else:points=[(source['x']+65,source['y']),(2890,y),(target['x']-65,target['y'])]
        rows=[]
        yy=y-35-g['upper']
        for m in g['calls']:
            h=message_height(m,g['width'])
            rows.append(dict(n=m['n'],x=g['x'],y=yy+h/2,width=g['width'],height=h,forward=True))
            yy+=h
        yy=y+38
        for m in g['returns']:
            h=message_height(m,g['width'])
            rows.append(dict(n=m['n'],x=g['x'],y=yy+h/2,width=g['width'],height=h,forward=False))
            yy+=h
        view['groups'].append(dict(pair=list(p),points=points,rows=rows))
    return view


VIEWS=[layout('CU06 - General numerado',M)]
for area,name in [('categorias','CU06 - Categorías'),('temporadas','CU06 - Temporadas y colecciones'),('prendas','CU06 - Prendas y variantes')]:
    VIEWS.append(layout(name,[m for m in M if m['area']==area]))


def cell(parent,ident,value='',style='',x=0,y=0,w=0,h=0,**attrs):
    c=ET.SubElement(parent,'mxCell',dict(id=ident,value=value,style=style,vertex='1',parent='1',**attrs))
    ET.SubElement(c,'mxGeometry',dict(x=str(x),y=str(y),width=str(w),height=str(h),**{'as':'geometry'}))
    return c


def native_line(root,ident,points,color='#5A6065',arrow=False,a=None,b=None):
    at=dict(id=ident,edge='1',parent='1',style=f'edgeStyle=none;html=0;rounded=0;strokeColor={color};strokeWidth=1.5;endArrow={"classic" if arrow else "none"};endSize=12;')
    if a:at['source']='node_'+a
    if b:at['target']='node_'+b
    e=ET.SubElement(root,'mxCell',at)
    g=ET.SubElement(e,'mxGeometry',{'relative':'1','as':'geometry'})
    ET.SubElement(g,'mxPoint',{'x':str(points[0][0]),'y':str(points[0][1]),'as':'sourcePoint'})
    ET.SubElement(g,'mxPoint',{'x':str(points[-1][0]),'y':str(points[-1][1]),'as':'targetPoint'})
    if len(points)>2:
        arr=ET.SubElement(g,'Array',{'as':'points'})
        for x,y in points[1:-1]:ET.SubElement(arr,'mxPoint',dict(x=str(x),y=str(y)))


def drawio():
    f=ET.Element('mxfile',dict(host='app.diagrams.net',type='device',version='29.0.0'))
    by_n={m['n']:m for m in M}
    for vi,v in enumerate(VIEWS):
        d=ET.SubElement(f,'diagram',id='cu06-'+str(vi),name=v['name'])
        model=ET.SubElement(d,'mxGraphModel',dict(dx=str(v['width']),dy=str(v['height']),grid='1',gridSize='10',guides='1',tooltips='1',connect='1',arrows='1',fold='1',page='1',pageScale='1',pageWidth=str(v['width']),pageHeight=str(v['height']),math='0',shadow='0'))
        root=ET.SubElement(model,'root')
        ET.SubElement(root,'mxCell',id='0')
        ET.SubElement(root,'mxCell',id='1',parent='0')
        cell(root,'frame',style='fillColor=#FFFFFF;strokeColor=#A0A7AD;pointerEvents=0;',x=20,y=20,w=v['width']-40,h=v['height']-40,connectable='0')
        title=v.get('title','CU06 - Administrar catálogo de prendas - '+('Vista general' if vi==0 else v['name'].split(' - ',1)[1]))
        cell(root,'title',title,'text;html=0;fontFamily=Arial;fontSize=32;fontStyle=1;align=center;strokeColor=none;fillColor=none;',x=40,y=45,w=v['width']-80,h=65,connectable='0')
        for gi,g in enumerate(v['groups']):
            native_line(root,'link_'+str(gi),g['points'],a=g['pair'][0],b=g['pair'][1])
            for row in g['rows']:
                m=by_n[row['n']]
                text=str(m['n'])+': '+m['text']
                lines=wrap(text,row['width']-85)
                tx=row['x']-row['width']/2
                text_width=min(row['width']-85,max(FONT.getlength(s) for s in lines)+12)
                cell(root,'message_'+str(m['n']),'\n'.join(lines),f'text;html=0;fontFamily=Arial;fontSize=24;fontColor={m["color"]};align=left;verticalAlign=middle;whiteSpace=wrap;spacing=3;strokeColor=none;fillColor=#FFFFFF;',x=tx,y=row['y']-row['height']/2,w=text_width,h=row['height'],connectable='0')
                xx=tx+text_width+12
                points=[(xx,row['y']),(xx+46,row['y'])]
                if not row.get('rightward',row['forward']):points.reverse()
                native_line(root,'arrow_'+str(m['n']),points,m['color'],True)
        for key,p in v['nodes'].items():
            node=NODES[key]
            x,y=p['x'],p['y']
            if node['kind']=='actor':
                cell(root,'node_'+key,style='shape=umlActor;fillColor=#FFFFFF;strokeColor=#30383E;strokeWidth=2;',x=x-35,y=y-65,w=70,h=130)
                caption=node['name']
                ly=y+85
                lw=290
            else:
                cell(root,'node_'+key,style='ellipse;fillColor=#E8F3F5;strokeColor=#52636C;strokeWidth=2;',x=x-65,y=y-65,w=130,h=130)
                if node['kind']=='boundary':
                    native_line(root,'bar_'+key,[(x-82,y-65),(x-82,y+65)])
                    native_line(root,'arm_'+key,[(x-82,y),(x-65,y)])
                elif node['kind']=='entity':native_line(root,'base_'+key,[(x-70,y+72),(x+70,y+72)])
                elif node['kind']=='control':native_line(root,'c_arrow_'+key,[(x+28,y-70),(x+5,y-77),(x-22,y-60)],arrow=True)
                prefix=node.get('prefix',{'boundary':'«boundary»','control':'«control»','entity':'Base de datos :'}[node['kind']])
                caption=prefix+'\n'+node['name']
                ly=y+91
                lw=500 if key=='control' else 440
            lines=wrap(caption,lw-12,BOLD)
            cell(root,'caption_'+key,'\n'.join(lines),'text;html=0;fontFamily=Arial;fontSize=25;fontStyle=1;align=center;verticalAlign=top;whiteSpace=wrap;strokeColor=none;fillColor=#FFFFFF;',x=x-lw/2,y=ly,w=lw,h=len(lines)*34+14,connectable='0')
    ET.indent(f,space='  ')
    return ET.tostring(f,encoding='utf-8',xml_declaration=True)


def text_svg(cx,cy,lines,color='#26333B',size=24,anchor='start',bold=False):
    bits=[]
    y0=cy-(len(lines)-1)*16
    for i,line in enumerate(lines):
        bits.append(f'<text x="{cx}" y="{y0+i*32}" dominant-baseline="middle" text-anchor="{anchor}" fill="{color}" font-size="{size}" font-weight="{"bold" if bold else "normal"}">{html.escape(line)}</text>')
    return ''.join(bits)


def svg(v,index):
    by_n={m['n']:m for m in M}
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{v["width"]}" height="{v["height"]}" viewBox="0 0 {v["width"]} {v["height"]}"><defs>']
    for k,color in COLORS.items():parts.append(f'<marker id="a_{k}" markerWidth="12" markerHeight="10" refX="11" refY="5" orient="auto" markerUnits="userSpaceOnUse"><path d="M0,0 L11,5 L0,10 Z" fill="{color}"/></marker>')
    parts.extend(['</defs><g font-family="Arial, sans-serif">',f'<rect width="{v["width"]}" height="{v["height"]}" fill="white"/>',f'<rect x="20" y="20" width="{v["width"]-40}" height="{v["height"]-40}" fill="none" stroke="#A0A7AD"/>'])
    title=v.get('title','CU06 - Administrar catálogo de prendas - '+('Vista general' if index==0 else v['name'].split(' - ',1)[1]))
    parts.append(text_svg(v['width']/2,76,[title],size=32,anchor='middle',bold=True))
    for g in v['groups']:
        points=' '.join(f'{x},{y}' for x,y in g['points'])
        parts.append(f'<polyline points="{points}" fill="none" stroke="#5A6065" stroke-width="1.5"/>')
    for g in v['groups']:
        for row in g['rows']:
            m=by_n[row['n']]
            lines=wrap(str(m['n'])+': '+m['text'],row['width']-85)
            x=row['x']-row['width']/2
            width=min(row['width']-85,max(FONT.getlength(s) for s in lines)+12)
            parts.append(f'<rect x="{x-3}" y="{row["y"]-row["height"]/2}" width="{width+6}" height="{row["height"]}" fill="white"/>')
            parts.append(text_svg(x+3,row['y'],lines,m['color']))
            xx=x+width+12
            start,end=(xx,xx+46) if row.get('rightward',row['forward']) else (xx+46,xx)
            parts.append(f'<path d="M{start},{row["y"]} H{end}" fill="none" stroke="{m["color"]}" stroke-width="2" marker-end="url(#a_{m["kind"]})"/>')
    for key,p in v['nodes'].items():
        node=NODES[key]
        x,y=p['x'],p['y']
        if node['kind']=='actor':
            parts.append(f'<g stroke="#30383E" fill="white" stroke-width="2"><circle cx="{x}" cy="{y-47}" r="18"/><path d="M{x},{y-29} V{y+24} M{x-35},{y-5} H{x+35} M{x},{y+24} L{x-34},{y+65} M{x},{y+24} L{x+34},{y+65}" fill="none"/></g>')
            label=node['name'];ly=y+85;lw=290
        else:
            parts.append(f'<circle cx="{x}" cy="{y}" r="65" fill="#E8F3F5" stroke="#52636C" stroke-width="2"/>')
            if node['kind']=='boundary':parts.append(f'<path d="M{x-82},{y-65} V{y+65} M{x-82},{y} H{x-65}" fill="none" stroke="#5A6065" stroke-width="1.5"/>')
            elif node['kind']=='entity':parts.append(f'<path d="M{x-70},{y+72} H{x+70}" fill="none" stroke="#5A6065" stroke-width="1.5"/>')
            elif node['kind']=='control':parts.append(f'<polyline points="{x+28},{y-70} {x+5},{y-77} {x-22},{y-60}" fill="none" stroke="#5A6065" stroke-width="1.5" marker-end="url(#a_read)"/>')
            prefix=node.get('prefix',{'boundary':'«boundary»','control':'«control»','entity':'Base de datos :'}[node['kind']])
            label=prefix+'\n'+node['name'];ly=y+91;lw=500 if key=='control' else 440
        lines=wrap(label,lw-12,BOLD)
        h=len(lines)*34+14
        parts.append(f'<rect x="{x-lw/2}" y="{ly}" width="{lw}" height="{h}" fill="white"/>')
        parts.append(text_svg(x,ly+h/2,lines,size=25,anchor='middle',bold=True))
    parts.append('</g></svg>')
    return ''.join(parts)


def validate(native):
    assert [m['n'] for m in M]==list(range(1,len(M)+1))
    symbols={}
    owners=defaultdict(set)
    for m in M:
        ak,bk=NODES[m['a']]['kind'],NODES[m['b']]['kind']
        if 'actor' in [ak,bk]:assert set([ak,bk])=={'actor','boundary'}
        if 'entity' in [ak,bk]:
            assert set([ak,bk])=={'entity','control'}
            ent=m['a'] if ak=='entity' else m['b']
            ctrl=m['b'] if ak=='entity' else m['a']
            owners[ent].add(ctrl)
        assert not re.search(r'\b(?:GET|POST|PUT|PATCH|HTTP)\b',m['text'])
        if m['source']:
            if m['source'] not in symbols:
                tree=ast.parse((ROOT/m['source']).read_text(encoding='utf-8-sig'))
                symbols[m['source']]={n.name:n.lineno for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
            assert m['symbol'] in symbols[m['source']],m
            m['line']=symbols[m['source']][m['symbol']]
    assert len(owners)==11 and all(len(v)==1 for v in owners.values())
    schema=etree.XMLSchema(etree.parse(str(ROOT/'tmp/drawio-validation/mxfile.xsd')))
    doc=etree.fromstring(native)
    schema.assertValid(doc)
    for diagram,v in zip(doc.findall('diagram'),VIEWS):
        ids=[c.get('id') for c in diagram.iter('mxCell')]
        assert len(ids)==len(set(ids))
        expected=sorted(row['n'] for g in v['groups'] for row in g['rows'])
        actual=sorted(int(i.removeprefix('message_')) for i in ids if i.startswith('message_'))
        assert actual==expected
        for g in v['groups']:
            rows=g['rows']
            for row in rows:
                assert row['y']-row['height']/2>=115,(v['name'],row)
                assert row['y']+row['height']/2<v['height']-20
                assert row['x']-row['width']/2>20
                assert row['x']+row['width']/2<v['width']-20
            ordered=sorted(rows,key=lambda r:r['y'])
            assert all(a['y']+a['height']/2<=b['y']-b['height']/2+0.01 for a,b in zip(ordered,ordered[1:]))
        for n,p in v['nodes'].items():
            assert p['x']>50 and p['y']>150 and p['y']+220<v['height']
    return dict(mensajes=len(M),acciones=len(A),vistas=len(VIEWS),numeracion_unica_consecutiva=True,
                mensajes_separados=True,sin_etiquetas_HTTP=True,entidades_solo_con_control=True,
                un_control_por_entidad=True,actores_solo_con_interfaces=True,xsd_valido=True,
                funciones_referenciadas_comprobadas_por_AST=True,filas_sin_solapamiento=True,
                operaciones_futuras_inventadas=0,
                dimensiones=[dict(vista=v['name'],ancho=v['width'],alto=v['height']) for v in VIEWS])


if __name__=='__main__':
    native=drawio()
    report=validate(native)
    (OUT/(STEM+'.drawio')).write_bytes(native)
    for i,v in enumerate(VIEWS):
        (OUT/(STEM+('_General' if i==0 else '_'+['','Categorias','Temporadas','Prendas'][i])+'.svg')).write_text(svg(v,i),encoding='utf-8')
    files=sorted({m['source'] for m in M if m['source']}|{n['source'] for n in NODES.values() if 'source' in n})
    model=dict(title='CU06 - Administrar catálogo de prendas',nodes=NODES,messages=M,actions=A,views=VIEWS,
               sources=[dict(file=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest()) for p in files],
               scope=dict(actor='Administrador de empresa',control='Responsabilidad de análisis que agrupa los routers y servicios actuales, no una clase Python inexistente.',
                          replies='Los nombres de datos y mensajes de presentación son interacciones conceptuales, no métodos añadidos al código.',
                          order='Numeración de lectura por escenarios. Las descargas independientes de auxiliares pueden ejecutarse concurrentemente en Angular.',
                          callbacks='La recarga de tablas reutiliza los mensajes de consulta ya representados; no se duplican todos los callbacks.',
                          image='Se representa la persistencia de una URL ya obtenida. La subida opcional a almacenamiento externo se mantiene fuera de este recorrido de persistencia.',
                          future='No se añaden operaciones inexistentes. No se modela edición posterior de variantes ni asignación de temporada desde el formulario actual.',
                          roles='El recorrido principal es del administrador. La ficha incluye un responsable de inventario cuya edición web de prendas no está habilitada actualmente. El encargado de sucursal puede acceder al módulo de temporadas.',
                          trigger='El movimiento inicial actualiza el stock mediante trigger; no existe un mensaje directo entre Movimiento e Inventario en este modelo.',
                          db_results='No se inventan retornos de escritura cuando el servicio no los recupera. Los datos de consultas SQL con joins se adscriben a la entidad principal del resultado.'))
    (OUT/(STEM+'_Modelo.json')).write_text(json.dumps(model,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/(STEM+'_Validacion.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    with (OUT/'MENSAJES_CU06.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.writer(f);writer.writerow(['numero','accion','origen','destino','mensaje','tipo','archivo','linea','funcion'])
        for m in M:writer.writerow([m['n'],m['action'],m['a'],m['b'],m['text'],m['kind'],m['source'],m.get('line',''),m['symbol']])
    print(json.dumps(report,ensure_ascii=False,indent=2))
