"""Source-faithful UML classifiers, a continuous master and vertically tiled pages."""
from __future__ import annotations
import ast
import csv
import hashlib
import html
import json
import math
import re
import xml.etree.ElementTree as ET
from collections import Counter,defaultdict
from pathlib import Path
from PIL import ImageFont

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'docs/diagrama_clases'
TMP=ROOT/'tmp/class-model'
FONT=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',20)
FONT_BOLD=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',20)
W=1200
BW=470
UNIT=27
COLORS={'Python':'#E8F2EB','TypeScript':'#E8EFF8','Dart':'#F1EAF7','External':'#F2F3F4'}
GROUPS=[
 ('Acceso e identidad',['auth','login','registro','password','identity','session','tenant']),
 ('Empresas, planes y suscripciones',['saas','company','plan','subscription','empresa']),
 ('Personal, roles y permisos',['usuario','rol','permiso','administracion']),
 ('Ciudades y sucursales',['geografia','ciudad','sucursal']),
 ('Fichas de clientes',['cliente']),
 ('Catálogo de prendas',['catalog','prenda','variante','categoria','temporada','coleccion','talla','color']),
 ('Abastecimiento y proveedores',['compra','proveedor']),
 ('Inventario y movimientos',['inventario','movimiento']),
 ('Comercio, reservas y pagos',['venta','reserva','carrito','checkout','pos','pago','payment','comprobante','commerce','order']),
 ('Cambios y notificaciones',['cambio','exchange','push','notifica']),
 ('Vestidor y recomendaciones',['tryon','try_on','vestidor','recomend','ia_','asistente','decart']),
 ('Operación offline y sincronización',['offline','synchron','conflicto','local_database']),
 ('Reportes y aprendizaje automático',['report','analytic','analitic','dashboard','ml/','ml_']),
 ('Auditoría',['bitacora','auditor']),
 ('Infraestructura y aplicación',['database','main.','api_client','widgets','theme','app.','config','safe_images','local_images','image_storage','permissions','interceptor','guard']),
]


def compact(value):
    return re.sub(r'\s+',' ',value or '').strip()


def type_display(value):
    value=compact(value)
    # Structural compiler inference is preserved in JSON; UML uses its category.
    if len(value)>150 and '{' in value:
        start=value.find('{');end=value.rfind('}')
        if end>start:value=value[:start]+'object'+value[end+1:]
    return value


def wrap(value,width=BW-24,font=FONT):
    lines=[]
    for paragraph in str(value).split('\n'):
        remaining=paragraph.strip()
        while remaining and font.getlength(remaining)>width:
            end=1
            while end<len(remaining) and font.getlength(remaining[:end+1])<=width:end+=1
            choices=[remaining.rfind(c,0,end) for c in (' ',',','|','_','/','>')]
            best=max(choices)
            cut=best+1 if best>=end*.45 else end
            lines.append(remaining[:cut].rstrip());remaining=remaining[cut:].lstrip()
        lines.append(remaining)
    return lines


def area(n):
    source=n['source'].lower()
    name=n['name'].lower()
    if n['language']=='Dart' and 'features/ar/' in source:return 10
    if any(t in source for t in ('offline','synchron','local_database')):return 11
    if any(t in source for t in ('report','analytic','analitic','dashboard','/ml/','ml_features')):return 12
    if any(t in source for t in ('tryon','/ia.','/ia_','/ar/','recomend','asistente','probador')):return 10
    if any(t in source for t in ('catalogo.model','venta.model','catalogo_models','venta_models')):
        for i,(label,words) in enumerate(GROUPS):
            if any(t in name for t in words):return i
    for i,(label,words) in enumerate(GROUPS):
        if any(t in source for t in words):return i
    return 14


def read_model():
    datasets=[json.loads((TMP/(name+'.json')).read_text(encoding='utf-8')) for name in ('python','typescript','dart')]
    nodes=[n for d in datasets for n in d['nodes']]
    index={n['id']:n for n in nodes}
    byfile=defaultdict(list)
    for n in nodes:byfile[n['source']].append(n)
    relations={}
    evidence=[]
    def edge(s,t,kind='dependency',label='',many='',file='',line=0):
        if s==t or s not in index or t not in index:return
        key=(s,t,kind)
        if key not in relations:relations[key]={'source':s,'target':t,'kind':kind,'labels':set(),'multiplicity':many,'evidence':[]}
        if label:relations[key]['labels'].add(label)
        if many:relations[key]['multiplicity']=many
        if file:relations[key]['evidence'].append({'file':file,'line':line})
    def resolve(n,name):
        name=re.sub(r'<.*','',name).strip().rstrip('?')
        if n['source']+'::'+name in index:return n['source']+'::'+name
        for imp in n.get('imports',[]):
            targetfile=None;targetname=name
            if n['language']=='Python':
                mapping=imp.get('names',{})
                if name not in mapping:continue
                raw=mapping[name];module=imp['path']
                targetfile='Parcial2_backend/'+module.replace('.','/')+'.py'
                targetname=raw
                candidate='Parcial2_backend/'+(module+'.'+raw).replace('.','/')+'.py'
                if candidate in byfile:targetfile=candidate;targetname='$module'
            else:
                raw=imp.get('path') or ''
                if not raw.startswith('.'):continue
                targetfile=(Path(n['source']).parent/raw).as_posix()
                targetfile=Path(__import__('os').path.normpath(targetfile)).as_posix()
                if n['language']=='TypeScript':
                    if name not in imp.get('names',[]):continue
                    targetfile += '.ts'
                targetname=name
            if targetfile:
                key=targetfile+'::'+targetname
                if key in index:return key
                modules=[x for x in byfile.get(targetfile,[]) if x['kind']=='module']
                if modules:return modules[0]['id']
        return None
    for n in nodes:
        n['area']=area(n)
        for base in n.get('bases',[]):
            target=resolve(n,base['name'])
            base['resolved_target']=target
            if target:edge(n['id'],target,'realization' if base['kind'] in ('implements','mixin') else 'generalization',file=n['source'],line=n['line'])
        for attr in n['attributes']:
            typ=attr.get('type','')
            for token in set(re.findall(r'\b[A-Za-z_]\w*\b',typ)):
                target=resolve(n,token)
                if target:edge(n['id'],target,'association',attr['name'],'0..*' if re.search(r'\b(list|List|Array|Set|Table|Map)\b|\[\]',typ) else '0..1' if ('None' in typ or '?' in typ or attr.get('optional')) else '1',n['source'],attr['line'])
        for m in n['methods']:
            signature=m.get('return','')+' '+m.get('raw_params','')+' '.join(p.get('type','') for p in m.get('params',[]))
            for token in set(re.findall(r'\b[A-Za-z_]\w*\b',signature)):
                target=resolve(n,token)
                if target:edge(n['id'],target,file=n['source'],line=m['line'])
        for typ in n.get('type_refs',[]):
            for token in set(re.findall(r'\b[A-Za-z_]\w*\b',typ)):
                target=resolve(n,token)
                if target:edge(n['id'],target,file=n['source'],line=n['line'])
    for d in datasets:
        for ref in d.get('refs',[]):
            if ref['target'] in index:edge(ref['source'],ref['target'],file=ref.get('file',''),line=ref.get('line',0))
    graph=json.loads((ROOT/'graphify-out/graph.json').read_text(encoding='utf-8'))
    owners={}
    for g in graph['nodes']:
        source=(g.get('source_file') or '').replace('\\','/')
        if source not in byfile:continue
        match=re.match(r'L(\d+)',g.get('source_location') or '')
        line=int(match[1]) if match else 0
        candidates=[n for n in byfile[source] if n['line']<=line<=n['end']]
        if not candidates and len(byfile[source])==1:candidates=byfile[source]
        if candidates:owners[g['id']]=min(candidates,key=lambda n:n['end']-n['line'])['id']
    for e in graph['links']:
        if e.get('confidence')!='EXTRACTED':continue
        s=owners.get(e['source']);t=owners.get(e['target'])
        if s and t and e.get('relation') in ('calls','imports_from','references','uses','imports'):
            edge(s,t,file=e.get('source_file',''),line=int(re.sub(r'\D','',e.get('source_location','') or '0') or '0'))
    # Resolve direct Python aliases and annotated references that a graph may miss.
    for source,classes in byfile.items():
        if not source.endswith('.py'):continue
        tree=ast.parse((ROOT/source).read_text(encoding='utf-8-sig'))
        for token in ast.walk(tree):
            if not isinstance(token,ast.Name):continue
            candidates=[n for n in classes if n['line']<=token.lineno<=n['end']]
            if not candidates:continue
            owner=min(candidates,key=lambda n:n['end']-n['line'])
            target=resolve(owner,token.id)
            if target:edge(owner['id'],target,file=source,line=token.lineno)
    # HTTP contracts connect the web/mobile classifiers to implemented API modules.
    endpoints=defaultdict(set)
    def normal_uri(uri):
        uri=uri.split('?')[0].rstrip('/')
        uri=re.sub(r'\$\{[^}]*\}|\$[A-Za-z_]\w*','{p}',uri)
        return re.sub(r'\{[^}]*\}','{p}',uri)
    for source,classes in byfile.items():
        if '/routers/' not in source or not source.endswith('.py'):continue
        module=next((n for n in classes if n['kind']=='module'),None)
        if module is None:continue
        tree=ast.parse((ROOT/source).read_text(encoding='utf-8-sig'));prefix=''
        for item in tree.body:
            if isinstance(item,ast.Assign) and isinstance(item.value,ast.Call):
                for kw in item.value.keywords:
                    if kw.arg=='prefix' and isinstance(kw.value,ast.Constant):prefix=kw.value.value
        for fn in tree.body:
            if not isinstance(fn,(ast.FunctionDef,ast.AsyncFunctionDef)):continue
            for dec in fn.decorator_list:
                if isinstance(dec,ast.Call) and isinstance(dec.func,ast.Attribute) and dec.func.attr in ('get','post','put','delete','patch') and dec.args and isinstance(dec.args[0],ast.Constant):
                    uri=normal_uri('/api'+prefix+dec.args[0].value)
                    endpoints[uri].add(module['id'])
    for n in nodes:
        if n['language']=='Python' or n['kind']=='module':continue
        text='\n'.join((ROOT/n['source']).read_text(encoding='utf-8-sig').splitlines()[n['line']-1:n['end']])
        pattern=r'/api/[A-Za-z0-9_/'+chr(36)+r'{}.\-\[\]?=&:]*'
        for hit in re.finditer(pattern,text):
            uri=normal_uri(hit.group())
            if len(uri)<6:continue
            for target in endpoints.get(uri,[]):
                edge(n['id'],target,label='HTTP '+uri,file=n['source'],line=n['line']+text[:hit.start()].count('\n'))
    pairs=defaultdict(set)
    for s,t,k in relations:pairs[(s,t)].add(k)
    for key in list(relations):
        if key[2]=='dependency' and pairs[key[:2]]-{'dependency'}:del relations[key]
    for i,r in enumerate(relations.values(),1):
        r['id']=f'R{i:04}';r['labels']=sorted(r['labels'])
        unique={(v['file'],v['line']) for v in r['evidence']}
        r['evidence']=[{'file':p,'line':line} for p,line in sorted(unique)]
    files=sorted(set(f for d in datasets for f in d['files']))
    return nodes,list(relations.values()),files


def namespace(n):
    path=n['source']
    for prefix,alias in [('Parcial2_backend/app/','API.'),('Parcial2_backend/','Backend.'),('Parcial2_frontend-web/src/app/','Web.'),('Parcial2_mobile/lib/','Móvil.')]:
        if path.startswith(prefix):return alias+path[len(prefix):].rsplit('/',1)[0].replace('/','.')
    return path


def member_rows(n):
    attrs=[];methods=[]
    if n.get('value_type'):attrs.append(('= '+type_display(n['value_type']),False))
    for a in n['attributes']:
        text=('' if n['kind']=='enum' else a.get('visibility','+')+' ')+a['name']+('?' if a.get('optional') else '')
        if a.get('type'):text+=': '+type_display(a['type'])
        attrs.append((text,a.get('static',False)))
    for m in n['methods']:
        if 'raw_params' in m:
            params=m['raw_params']
        else:
            params='('+', '.join(p['name']+('?' if p.get('optional') else '')+(': '+type_display(p['type']) if p.get('type') else '') for p in m.get('params',[]))+')'
        text=m.get('visibility','+')+' '+m['name']+params
        if m.get('return'):text+=': '+type_display(m['return'])
        if m.get('kind') in ('getter','setter'):text+=' {get}' if m['kind']=='getter' else ' {set}'
        methods.append((text,m.get('static',False)))
    return attrs,methods


class Canvas:
    def __init__(self):self.primitives=[];self.text_zones=[]
    def rect(self,x,y,w,h,fill='white',stroke='#5E6F7D',width=1.1,uid=''):
        self.primitives.append({'type':'rect','x':x,'y':y,'w':w,'h':h,'fill':fill,'stroke':stroke,'strokeWidth':width,'classifier':uid})
    def path(self,points,kind='line',rid='',source='',target='',uid=''):
        self.primitives.append({'type':'path','points':points,'kind':kind,'relation':rid,'source':source,'target':target,'classifier':uid})
    def text(self,x,y,w,lines,size=20,bold=False,center=False,underline=False,uid='',source='',line=0):
        for i,text in enumerate(lines):
            yy=y+i*UNIT
            self.text_zones.append((yy+2,yy+25))
        self.primitives.append({'type':'text','x':x,'y':y,'w':w,'h':len(lines)*UNIT,'lines':lines,'size':size,'bold':bold,'center':center,'underline':underline,'classifier':uid,'file':source,'line':line})


def layout(nodes,edges):
    canvas=Canvas();locations={};cursor=108
    canvas.text(20,14,W-40,['Diagrama de clases UML — FashionStore'],24,True)
    # Exactly two columns keep every plate at a readable, fixed document width.
    for group,(label,_) in enumerate(GROUPS):
        members=[n for n in nodes if n['area']==group]
        if not members:continue
        canvas.rect(80,cursor,W-160,54,fill='#E9EDF1')
        canvas.text(92,cursor+12,W-184,[label],22,True)
        cursor+=81
        members.sort(key=lambda n:({'Python':0,'TypeScript':1,'Dart':2}[n['language']],n['source'],n['line']))
        for at in range(0,len(members),2):
            row=members[at:at+2];heights=[]
            for col,n in enumerate(row):
                attrs,methods=member_rows(n)
                attrlines=[(wrap(text),static) for text,static in attrs]
                methodlines=[(wrap(text),static) for text,static in methods]
                bases=[b['name'] for b in n.get('bases',[]) if not b.get('resolved_target')]
                header=['«'+{'class':'class','module':'module','interface':'interface','enum':'enumeration','type':'dataType'}[n['kind']]+'» '+n['name'],namespace(n)]
                if bases:header.append('extends / implements: '+', '.join(bases))
                headerlines=[line for text in header for line in wrap(text,font=FONT_BOLD)]
                hh=UNIT*(len(headerlines)+1)
                ah=UNIT*(sum(len(a[0]) for a in attrlines)+1)
                mh=UNIT*(sum(len(a[0]) for a in methodlines)+1)
                height=hh+ah+mh;heights.append(height)
                locations[n['id']]={'x':100+550*col,'y':cursor,'w':BW,'h':height,'header':hh,'col':col,'node':n,
                                    'headerlines':headerlines,'attrlines':attrlines,'methodlines':methodlines}
            cursor+=max(heights)+54
        cursor+=54
    height=cursor+27
    # Relationships are routed in gutters; class fills keep them out of text.
    for i,e in enumerate(edges):
        a,b=locations[e['source']],locations[e['target']]
        ay=a['y']+min(a['header']-10,25+(i%5)*7)
        by=b['y']+min(b['header']-10,25+(i%5)*7)
        if a['col']==b['col']:
            side=0 if a['col']==0 else 1
            ax=a['x']+(a['w'] if side else 0);bx=b['x']+(b['w'] if side else 0)
            rail=20+(i%45)*1.4 if side==0 else W-20-(i%45)*1.4
        else:
            ax=a['x']+(a['w'] if a['col']==0 else 0)
            bx=b['x']+(b['w'] if b['col']==0 else 0)
            rail=586+(i%28)*1.7
        canvas.path([(ax,ay),(rail,ay),(rail,by),(bx,by)],e['kind'],e['id'],e['source'],e['target'])
    # Classifiers are UML boxes with separate attributes and operation compartments.
    for n in nodes:
        p=locations[n['id']];x,y=p['x'],p['y']
        canvas.rect(x,y,BW,p['h'],fill='#FFFFFF',uid=n['id'])
        canvas.rect(x,y,BW,p['header'],fill=COLORS[n['language']],uid=n['id'])
        canvas.text(x+12,y+10,BW-24,p['headerlines'],20,True,True,uid=n['id'],source=n['source'],line=n['line'])
        ay=y+p['header']+13
        for lines,static in p['attrlines']:
            canvas.text(x+12,ay,BW-24,lines,20,underline=static,uid=n['id'],source=n['source']);ay+=len(lines)*UNIT
        sep=y+p['header']+UNIT*(sum(len(a[0]) for a in p['attrlines'])+1)
        canvas.path([(x,sep),(x+BW,sep)],uid=n['id'])
        my=sep+13
        for lines,static in p['methodlines']:
            canvas.text(x+12,my,BW-24,lines,20,underline=static,uid=n['id'],source=n['source']);my+=len(lines)*UNIT
    return canvas,locations,int(height)


def split_positions(canvas,height):
    zones=list(canvas.text_zones)
    if not zones:
        zones=[(p['y']+i*UNIT+2,p['y']+i*UNIT+25)
               for p in canvas.primitives if p['type']=='text'
               for i in range(len(p['lines']))]
    # Keep full border strokes and arrowheads on one side of a seam.
    for p in canvas.primitives:
        if p['type']=='rect':
            zones.extend([(p['y']-2,p['y']+2),(p['y']+p['h']-2,p['y']+p['h']+2)])
        if p['type']=='path':
            if p['kind'] not in ('line','border'):
                end=p['points'][-1][1];zones.append((end-14,end+14))
            for a,b in zip(p['points'],p['points'][1:]):
                if a[1]==b[1]:zones.append((a[1]-2,a[1]+2))
    cuts=[0]
    while height-cuts[-1]>1550:
        target=cuts[-1]+1500
        chosen=None
        for delta in range(0,350):
            for candidate in (target-delta,target+delta):
                if candidate<=cuts[-1]+1000:continue
                if not any(a-1<candidate<b+1 for a,b in zones):
                    chosen=candidate;break
            if chosen is not None:break
        if chosen is None:raise RuntimeError('No safe text boundary for a plate.')
        cuts.append(chosen)
    cuts.append(height)
    return cuts


def clip_polyline(points,y0,y1):
    pieces=[];current=[]
    for a,b in zip(points,points[1:]):
        dy=b[1]-a[1]
        if dy==0:
            if not y0<=a[1]<=y1:
                if current:pieces.append(current);current=[]
                continue
            start,end=a,b
        else:
            t0=max(0,min((y0-a[1])/dy,(y1-a[1])/dy))
            t1=min(1,max((y0-a[1])/dy,(y1-a[1])/dy))
            if t0>t1:
                if current:pieces.append(current);current=[]
                continue
            start=(a[0]+(b[0]-a[0])*t0,a[1]+dy*t0);end=(a[0]+(b[0]-a[0])*t1,a[1]+dy*t1)
        if current and (abs(current[-1][0]-start[0])>.01 or abs(current[-1][1]-start[1])>.01):pieces.append(current);current=[]
        if not current:current=[start]
        current.append(end)
    if current:pieces.append(current)
    return pieces


def page_contents(canvas,y0,y1):
    result=[]
    for p in canvas.primitives:
        if p['type']=='rect':
            top=max(y0,p['y']);bottom=min(y1,p['y']+p['h'])
            if bottom<=top:continue
            q=dict(p,y=top-y0,h=bottom-top,stroke='none');result.append(q)
            if p['stroke']!='none':
                # Clip real borders; a page boundary must not add a separator.
                points=[(p['x'],p['y']),(p['x']+p['w'],p['y']),(p['x']+p['w'],p['y']+p['h']),(p['x'],p['y']+p['h']),(p['x'],p['y'])]
                for piece in clip_polyline(points,y0,y1):result.append({'type':'path','points':[(x,y-y0) for x,y in piece],'kind':'border','relation':'','source':'','target':'','classifier':p.get('classifier','')})
        elif p['type']=='text':
            for i,line in enumerate(p['lines']):
                yy=p['y']+i*UNIT
                if yy+2>=y0 and yy+25<=y1:result.append(dict(p,y=yy-y0,h=UNIT,lines=[line]))
                elif yy+25>y0 and yy+2<y1:raise AssertionError('A glyph would be cut.')
        else:
            for piece in clip_polyline(p['points'],y0,y1):
                end_actual=abs(piece[-1][0]-p['points'][-1][0])<.01 and abs(piece[-1][1]-p['points'][-1][1])<.01
                start_actual=abs(piece[0][0]-p['points'][0][0])<.01 and abs(piece[0][1]-p['points'][0][1])<.01
                result.append(dict(p,points=[(x,y-y0) for x,y in piece],arrow=end_actual,start_actual=start_actual))
    return result


def svg(primitives,height):
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{height}" viewBox="0 0 {W} {height}"><rect width="100%" height="100%" fill="white"/>',
    '<defs><marker id="dependency" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto"><path d="M0,0 L9,5 L0,10" fill="none" stroke="#81919E"/></marker><marker id="generalization" markerWidth="14" markerHeight="14" refX="12" refY="7" orient="auto"><path d="M0,0 L12,7 L0,14 Z" fill="white" stroke="#3C627D"/></marker></defs>']
    for p in primitives:
        if p['type']=='rect':
            parts.append(f'<rect x="{p["x"]}" y="{p["y"]}" width="{p["w"]}" height="{p["h"]}" fill="{p["fill"]}" stroke="{p["stroke"]}"/>')
        elif p['type']=='text':
            x=p['x']+p['w']/2 if p['center'] else p['x']
            for i,line in enumerate(p['lines']):
                parts.append(f'<text x="{x}" y="{p["y"]+i*UNIT+21}" font-family="Arial" font-size="{p["size"]}" text-anchor="{"middle" if p["center"] else "start"}" font-weight="{700 if p["bold"] else 400}" text-decoration="{"underline" if p["underline"] else "none"}" fill="#1F303E">{html.escape(line)}</text>')
        else:
            kind=p['kind'];coords=' '.join(f'{x:.2f},{y:.2f}' for x,y in p['points'])
            color='#5E6F7D' if kind=='border' else '#3C627D' if kind in ('generalization','realization') else '#81919E'
            dash=' stroke-dasharray="7 5"' if kind in ('dependency','realization') else ''
            arrow=f' marker-end="url(#{ "generalization" if kind in ("generalization","realization") else "dependency"})"' if p.get('arrow',True) and kind not in ('line','border') else ''
            parts.append(f'<polyline points="{coords}" fill="none" stroke="{color}" stroke-width="{1.25 if kind in ("border","generalization") else .8}"{dash}{arrow}/>')
    parts.append('</svg>');return ''.join(parts)


def serialize_metadata(root):
    for cell in list(root):
        tip=cell.attrib.pop('tooltip',None)
        if not tip:continue
        if not cell.get('edge') and not cell.get('style','').startswith('group;'):
            continue
        position=list(root).index(cell)
        wrapper=ET.Element('object',id=cell.attrib.pop('id'),label=cell.attrib.pop('value',''),tooltip=tip)
        root.remove(cell);wrapper.append(cell);root.insert(position,wrapper)


def drawio_page(parent,primitives,height,name,pid):
    diagram=ET.SubElement(parent,'diagram',id=pid,name=name)
    model=ET.SubElement(diagram,'mxGraphModel',dx=str(W),dy=str(height),grid='1',gridSize='10',guides='1',tooltips='1',connect='1',arrows='1',fold='1',page='1',pageScale='1',pageWidth=str(W),pageHeight=str(height),math='0',shadow='0')
    root=ET.SubElement(model,'root');ET.SubElement(root,'mxCell',id='0');ET.SubElement(root,'mxCell',id='1',parent='0')
    bounds={}
    for p in primitives:
        cid=p.get('classifier')
        if cid and p['type']=='rect':
            b=bounds.setdefault(cid,{'x':p['x'],'y':p['y'],'right':p['x']+p['w'],'bottom':p['y']+p['h']})
            b['y']=min(b['y'],p['y']);b['bottom']=max(b['bottom'],p['y']+p['h'])
    groups={}
    for cid,b in bounds.items():
        gid=pid+'_class_'+hashlib.sha256(cid.encode()).hexdigest()[:16]
        group=ET.SubElement(root,'mxCell',id=gid,value='',tooltip=cid,style='group;connectable=1;',vertex='1',connectable='1',parent='1')
        ET.SubElement(group,'mxGeometry',x=str(b['x']),y=str(b['y']),width=str(b['right']-b['x']),height=str(b['bottom']-b['y']),**{'as':'geometry'})
        groups[cid]=gid
    for i,p in enumerate(primitives,1):
        uid=pid+'_'+str(i)
        cid=p.get('classifier');container=groups.get(cid,'1')
        ox=bounds[cid]['x'] if cid in bounds else 0
        oy=bounds[cid]['y'] if cid in bounds else 0
        if p['type']=='rect':
            style=f'rect;rounded=0;fillColor={p["fill"]};strokeColor={p["stroke"]};'
            cell=ET.SubElement(root,'mxCell',id=uid,value='',style=style,vertex='1',parent=container)
            ET.SubElement(cell,'mxGeometry',x=str(p['x']-ox),y=str(p['y']-oy),width=str(p['w']),height=str(p['h']),**{'as':'geometry'})
        elif p['type']=='text':
            style=f'text;html=0;whiteSpace=wrap;align={"center" if p["center"] else "left"};verticalAlign=top;spacing=0;fontFamily=Arial;fontSize={p["size"]};fontStyle={(1 if p["bold"] else 0)+(4 if p["underline"] else 0)};fillColor=none;strokeColor=none;fontColor=#1F303E;'
            cell=ET.SubElement(root,'mxCell',id=uid,value='\n'.join(p['lines']),style=style,vertex='1',parent=container)
            if p.get('classifier'):cell.set('tooltip',p['classifier'])
            ET.SubElement(cell,'mxGeometry',x=str(p['x']-ox),y=str(p['y']-oy),width=str(p['w']),height=str(p['h']),**{'as':'geometry'})
        else:
            kind=p['kind'];arrow='block' if kind in ('generalization','realization') else 'open'
            if kind in ('line','border') or not p.get('arrow',True):arrow='none'
            color='#5E6F7D' if kind=='border' else '#3C627D' if kind in ('generalization','realization') else '#81919E'
            style=f'edgeStyle=none;rounded=0;html=0;strokeColor={color};strokeWidth={1.25 if kind in ("border","generalization") else .8};endArrow={arrow};endFill=0;dashed={1 if kind in ("dependency","realization") else 0};'
            for role,actual,point,token in [('source',p.get('start_actual',True),p['points'][0],'exit'),('target',p.get('arrow',True),p['points'][-1],'entry')]:
                endpoint=p.get(role)
                if actual and endpoint in groups:
                    b=bounds[endpoint]
                    rx=(point[0]-b['x'])/(b['right']-b['x'])
                    ry=(point[1]-b['y'])/(b['bottom']-b['y'])
                    style+=f'{token}X={rx};{token}Y={ry};{token}Perimeter=0;'
            cell=ET.SubElement(root,'mxCell',id=uid,value='',style=style,edge='1',parent=container)
            for role,actual in [('source',p.get('start_actual',True)),('target',p.get('arrow',True))]:
                if actual and p.get(role) in groups:cell.set(role,groups[p[role]])
            if p.get('relation'):cell.set('tooltip',p['relation']+': '+p['source']+' → '+p['target'])
            geo=ET.SubElement(cell,'mxGeometry',relative='1',**{'as':'geometry'})
            points=[(x-ox,y-oy) for x,y in p['points']];ET.SubElement(geo,'mxPoint',x=str(points[0][0]),y=str(points[0][1]),**{'as':'sourcePoint'});ET.SubElement(geo,'mxPoint',x=str(points[-1][0]),y=str(points[-1][1]),**{'as':'targetPoint'})
            if len(points)>2:
                arr=ET.SubElement(geo,'Array',**{'as':'points'})
                for x,y in points[1:-1]:ET.SubElement(arr,'mxPoint',x=str(x),y=str(y))
    # Place the classifier groups above routed relationships, as in the SVG.
    cells=list(root)
    groupids=set(groups.values())
    base=[c for c in cells if c.get('id') in ('0','1')]
    globalcells=[c for c in cells if c.get('parent')=='1' and c.get('id') not in groupids]
    ordered=base+globalcells
    for gid in groups.values():
        ordered.extend(c for c in cells if c.get('id')==gid)
        ordered.extend(c for c in cells if c.get('parent')==gid)
    assert len(ordered)==len(cells)
    root[:]=ordered
    serialize_metadata(root)
    return diagram


def main():
    OUT.mkdir(parents=True,exist_ok=True);parts=OUT/'laminas';parts.mkdir(exist_ok=True)
    nodes,edges,files=read_model()
    model={'classifiers':nodes,'relationships':edges,'files_sha256':{f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files}}
    (OUT/'modelo_clases.json').write_text(json.dumps(model,ensure_ascii=False,indent=2),encoding='utf-8')
    canvas,locations,height=layout(nodes,edges);cuts=split_positions(canvas,height)
    master=ET.Element('mxfile',host='app.diagrams.net',type='device',version='26.0.0')
    all_items=page_contents(canvas,0,height)
    drawio_page(master,all_items,height,'General','general')
    ET.ElementTree(master).write(OUT/'FashionStore_Clases_General.drawio',encoding='utf-8',xml_declaration=True)
    (OUT/'FashionStore_Clases_General.svg').write_text(svg(all_items,height),encoding='utf-8')
    tiled=ET.Element('mxfile',host='app.diagrams.net',type='device',version='26.0.0');manifest=[]
    for i,(y0,y1) in enumerate(zip(cuts,cuts[1:]),1):
        content=page_contents(canvas,y0,y1);stem=f'Lamina_{i:03}'
        label=f'{i:03} de {len(cuts)-1:03}'
        drawio_page(tiled,content,y1-y0,label,'parte'+str(i))
        single=ET.Element('mxfile',host='app.diagrams.net',type='device',version='26.0.0')
        drawio_page(single,content,y1-y0,label,'parte'+str(i))
        ET.ElementTree(single).write(parts/(stem+'.drawio'),encoding='utf-8',xml_declaration=True)
        (parts/(stem+'.svg')).write_text(svg(content,y1-y0),encoding='utf-8')
        manifest.append({'numero':i,'archivo':stem,'y_inicio':y0,'y_fin':y1,'ancho':W,'alto':y1-y0})
    ET.ElementTree(tiled).write(OUT/'FashionStore_Clases_Por_Partes.drawio',encoding='utf-8',xml_declaration=True)
    with (OUT/'INVENTARIO_CLASES_Y_METODOS.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.writer(f);writer.writerow(['clasificador','lenguaje','tipo','archivo','linea','atributos','operaciones'])
        for n in nodes:writer.writerow([n['name'],n['language'],n['kind'],n['source'],n['line'],len(n['attributes']),len(n['methods'])])
    for key,filename in [('methods','INVENTARIO_OPERACIONES.csv'),('attributes','INVENTARIO_ATRIBUTOS.csv')]:
        with (OUT/filename).open('w',encoding='utf-8-sig',newline='') as f:
            writer=csv.writer(f);writer.writerow(['clasificador','miembro','archivo','linea','visibilidad','estatico','tipo_retorno','parametros'])
            for n in nodes:
                for m in n[key]:
                    writer.writerow([n['id'],m['name'],n['source'],m.get('line',n['line']),m.get('visibility','+'),m.get('static',False),m.get('return',m.get('type','')),m.get('raw_params',json.dumps(m.get('params',[]),ensure_ascii=False))])
    summary={'clasificadores':len(nodes),'por_lenguaje':dict(Counter(n['language'] for n in nodes)),
             'por_tipo':dict(Counter(n['kind'] for n in nodes)),'atributos':sum(len(n['attributes']) for n in nodes),
             'operaciones':sum(len(n['methods']) for n in nodes),'relaciones':len(edges),
             'ancho':W,'alto':height,'laminas':manifest}
    (OUT/'MANIFIESTO_LAMINAS.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    (TMP/'primitives.json').write_text(json.dumps(canvas.primitives,ensure_ascii=False),encoding='utf-8')
    print(json.dumps({k:v for k,v in summary.items() if k!='laminas'},ensure_ascii=False))
    print('Láminas:',len(manifest))


if __name__=='__main__':main()
