"""Editable draw.io ER model and matching vector preview from one layout."""
from pathlib import Path
import html,json,math,hashlib
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'docs/diagrama_entidad_relacion'
model=json.loads((BASE/'MODELO_ER_VERIFICADO.json').read_text(encoding='utf-8'))
layout=json.loads((BASE/'layout.json').read_text(encoding='utf-8'))
_,_,gw,gh=map(float,layout['bb'].split(','))
MX,MY=48,115
W,H=int(gw+MX*2),int(gh+MY+60)
entities={e['id']:e for e in model['entities']}
groups={g['id']:g for g in model['groups']}
objects={o['_gvid']:o for o in layout['objects']}

def transform(p):return [round(p[0]+MX,2),round(gh-p[1]+MY,2)]
def box(bb):
 x1,y1,x2,y2=map(float,bb.split(','));return x1+MX,gh-y2+MY,x2-x1,y2-y1
def esc(v):return html.escape(str(v),quote=True)
def geom(cell,x,y,w,h):return ET.SubElement(cell,'mxGeometry',{'x':str(x),'y':str(y),'width':str(w),'height':str(h),'as':'geometry'})

mf=ET.Element('mxfile',{'host':'app.diagrams.net','type':'device','version':'24.7.17','compressed':'false'})
dg=ET.SubElement(mf,'diagram',{'id':'fashionstore-er-general','name':'ER general principal'})
gm=ET.SubElement(dg,'mxGraphModel',{'dx':'1800','dy':'1000','grid':'1','gridSize':'10','guides':'1','tooltips':'1','connect':'1','arrows':'1','fold':'1','page':'1','pageScale':'1','pageWidth':str(W),'pageHeight':str(H),'math':'0','shadow':'0','background':'#ffffff'})
root=ET.SubElement(gm,'root');ET.SubElement(root,'mxCell',{'id':'0'});ET.SubElement(root,'mxCell',{'id':'1','parent':'0'})
svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
 '<rect width="100%" height="100%" fill="white"/>',
 '<g font-family="Arial, Helvetica, sans-serif">']

def text(x,y,value,size=13,weight='normal',fill='#1e293b',anchor='start'):
 svg.append(f'<text x="{x:.2f}" y="{y:.2f}" font-size="{size}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">{esc(value)}</text>')
def native_text(id_,value,x,y,w,h,size,bold=False):
 c=ET.SubElement(root,'mxCell',{'id':id_,'value':value,'vertex':'1','parent':'1','style':f'text;html=0;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;whiteSpace=wrap;rounded=0;fontFamily=Arial;fontSize={size};fontStyle={1 if bold else 0};fontColor=#1e293b;spacingLeft=0;'});geom(c,x,y,w,h)

title='FashionStore — Diagrama entidad-relación general'
legend='PK: clave primaria     FK: clave foránea     ?: admite NULL     Pata de cuervo: 0..*'
scope='tenant_id FK → empresa · Los enlaces empresariales repetitivos se resumen en ese atributo.'
text(MX,40,title,28,'bold');native_text('title',title,MX,12,W-2*MX,40,28,True)
text(MX,69,legend,14);native_text('legend',legend,MX,50,W-2*MX,24,14)
text(MX,91,scope,13,fill='#475569');native_text('scope',scope,MX,74,W-2*MX,22,13)

cluster_boxes=[]
for obj in layout['objects']:
 if not obj['name'].startswith('cluster_'):continue
 group=groups[obj['name'][8:]]
 x,y,w,h=box(obj['bb']);cluster_boxes.append((x,y,w,h))
 svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{group["color"]}" fill-opacity="0.17" stroke="{group["color"]}" stroke-width="2"/>')
 text(x+16,y+24,group['title'],18,'bold')
 c=ET.SubElement(root,'mxCell',{'id':obj['name'],'value':group['title'],'vertex':'1','parent':'1','style':f'rounded=1;arcSize=3;whiteSpace=wrap;html=0;fillColor={group["color"]};fillOpacity=17;strokeColor={group["color"]};strokeWidth=2;fontFamily=Arial;fontSize=18;fontStyle=1;align=left;verticalAlign=top;spacingTop=8;spacingLeft=16;connectable=0;'});geom(c,x,y,w,h)

for obj in layout['objects']:
 if obj['name'] not in entities:continue
 e=entities[obj['name']];cx,cy=map(float,obj['pos'].split(','));e.update(x=cx-e['width']/2+MX,y=gh-cy-e['height']/2+MY)

def polyline_points(points):
 result=[]
 for p in map(transform,points):
  if not result or abs(result[-1][0]-p[0])+abs(result[-1][1]-p[1])>0.01:result.append(p)
 changed=True
 while changed:
  changed=False
  for i in range(1,len(result)-1):
   a,b,c=result[i-1:i+2]
   if (abs(a[0]-b[0])<.05 and abs(b[0]-c[0])<.05) or (abs(a[1]-b[1])<.05 and abs(b[1]-c[1])<.05):
    result.pop(i);changed=True;break
 return result

def snap(p,e):
 x,y=e['x'],e['y'];w,h=e['width'],e['height']
 options=[([x,p[1]],abs(x-p[0])),([x+w,p[1]],abs(x+w-p[0])),([p[0],y],abs(y-p[1])),([p[0],y+h],abs(y+h-p[1]))]
 q,dist=min(options,key=lambda v:v[1]);assert dist<2,(e['id'],p,dist)
 return [round(q[0],2),round(q[1],2)]

def cardinality(endpoint,nextpoint,kind,color):
 dx,dy=nextpoint[0]-endpoint[0],nextpoint[1]-endpoint[1]
 mag=math.hypot(dx,dy);assert mag>0
 ux,uy=dx/mag,dy/mag;px,py=-uy,ux
 def at(t,s=0):return endpoint[0]+ux*t+px*s,endpoint[1]+uy*t+py*s
 def line(a,b):svg.append(f'<path d="M {a[0]:.2f},{a[1]:.2f} L {b[0]:.2f},{b[1]:.2f}" fill="none" stroke="{color}" stroke-width="1.7"/>')
 if kind=='1':
  for t in (5,10):line(at(t,-5),at(t,5))
 else:
  c=at(18);svg.append(f'<circle cx="{c[0]:.2f}" cy="{c[1]:.2f}" r="4" fill="white" stroke="{color}" stroke-width="1.6"/>')
  if kind=='0..1':line(at(7,-5),at(7,5))
  else:
   for s in (-6,0,6):line(at(1,s),at(11))

edge_report=[]
for route in layout['edges']:
 edge=next(e for e in model['edges'] if e['id']==route['id'])
 drawing=next(d for d in route['_draw_'] if d['op']=='b')
 ps=polyline_points(drawing['points']);assert len(ps)>=2
 parent,child=entities[edge['parent']],entities[edge['child']]
 assert objects[route['tail']]['name']==parent['id'] and objects[route['head']]['name']==child['id']
 ps[0]=snap(ps[0],parent);ps[-1]=snap(ps[-1],child)
 color=edge['color']
 d='M '+' L '.join(f'{p[0]:.2f},{p[1]:.2f}' for p in ps)
 svg.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="1.45" stroke-linejoin="round"/>')
 cardinality(ps[0],ps[1],edge['parent_cardinality'],color)
 cardinality(ps[-1],ps[-2],edge['child_cardinality'],color)
 marker={'1':'ERmandOne','0..1':'ERzeroToOne','0..*':'ERzeroToMany'}
 ex=(ps[0][0]-parent['x'])/parent['width'];ey=(ps[0][1]-parent['y'])/parent['height']
 ix=(ps[-1][0]-child['x'])/child['width'];iy=(ps[-1][1]-child['y'])/child['height']
 cell=ET.SubElement(root,'mxCell',{'id':edge['id'],'value':'','edge':'1','parent':'1','source':parent['id'],'target':child['id'],
  'style':f'edgeStyle=none;rounded=0;html=0;strokeColor={color};strokeWidth=1.45;startArrow={marker[edge["parent_cardinality"]]};startFill=0;startSize=12;endArrow={marker[edge["child_cardinality"]]};endFill=0;endSize=12;exitX={ex:.8f};exitY={ey:.8f};exitDx=0;exitDy=0;exitPerimeter=0;entryX={ix:.8f};entryY={iy:.8f};entryDx=0;entryDy=0;entryPerimeter=0;jumpStyle=arc;jumpSize=6;'})
 geometry=ET.SubElement(cell,'mxGeometry',{'relative':'1','as':'geometry'})
 if len(ps)>2:
  arr=ET.SubElement(geometry,'Array',{'as':'points'})
  for x,y in ps[1:-1]:ET.SubElement(arr,'mxPoint',{'x':str(x),'y':str(y)})
 edge_report.append(dict(id=edge['id'],parent=parent['id'],child=child['id'],parent_cardinality=edge['parent_cardinality'],child_cardinality=edge['child_cardinality'],constraint=edge['constraint'],points=ps))

for entity in model['entities']:
 x,y,w,h=entity['x'],entity['y'],entity['width'],entity['height'];color=entity['color']
 svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="white" stroke="#53677c" stroke-width="1.5"/>')
 svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="36" fill="{color}" stroke="#53677c" stroke-width="1.2"/>')
 text(x+12,y+24,entity['title'],16,'bold')
 cell=ET.SubElement(root,'mxCell',{'id':entity['id'],'value':entity['title'],'vertex':'1','parent':'1','style':f'swimlane;horizontal=1;startSize=36;rounded=0;html=0;whiteSpace=wrap;fillColor={color};swimlaneFillColor=#ffffff;strokeColor=#53677c;strokeWidth=1.5;fontFamily=Arial;fontSize=16;fontStyle=1;align=left;spacingLeft=12;collapsible=0;'});geom(cell,x,y,w,h)
 for i,field in enumerate(entity['fields']):
  row_y=36+i*24
  if i%2:svg.append(f'<rect x="{x+1}" y="{y+row_y}" width="{w-2}" height="24" fill="#f8fafc"/>')
  svg.append(f'<path d="M {x},{y+row_y+24} H {x+w}" stroke="#e2e8f0" stroke-width="0.6"/>')
  values=[(0,44,field['key'],10,'bold','#52677d'),(44,226,field['name'],13,'bold' if 'PK' in field['key'] else 'normal','#1e293b'),(270,150,field['type']+(' ?' if field['nullable'] else ''),12,'normal','#52677d')]
  for j,(offset,width,value,size,weight,fill) in enumerate(values):
   text(x+offset+7,y+row_y+16,value,size,weight,fill)
   fc=ET.SubElement(root,'mxCell',{'id':f'{entity["id"]}_{i}_{j}','value':value,'vertex':'1','parent':entity['id'],
    'style':f'text;html=0;strokeColor=none;fillColor={"#f8fafc" if i%2 else "#ffffff"};align=left;verticalAlign=middle;whiteSpace=nowrap;overflow=hidden;fontFamily=Arial;fontSize={size};fontColor={fill};fontStyle={1 if weight=="bold" else 0};spacingLeft=7;connectable=0;'});geom(fc,offset,row_y,width,24)

svg.extend(['</g>','</svg>'])
stem=BASE/'FashionStore_Diagrama_Entidad_Relacion_General'
ET.indent(mf,space='  ');ET.ElementTree(mf).write(stem.with_suffix('.drawio'),encoding='utf-8',xml_declaration=True)
stem.with_suffix('.svg').write_text('\n'.join(svg),encoding='utf-8')

# Validate references, editable cells, coordinates, entity non-overlap and routes.
cells=list(root);ids=[c.get('id') for c in cells];assert len(ids)==len(set(ids))
for a in model['entities']:
 for b in model['entities']:
  if a['id']>=b['id']:continue
  assert a['x']+a['width']<=b['x'] or b['x']+b['width']<=a['x'] or a['y']+a['height']<=b['y'] or b['y']+b['height']<=a['y'],(a['id'],b['id'])
crossed=[]
for edge in edge_report:
 for a,b in zip(edge['points'],edge['points'][1:]):
  assert abs(a[0]-b[0])<.1 or abs(a[1]-b[1])<.1,(edge['id'],a,b)
  for e in model['entities']:
   if e['id'] in (edge['parent'],edge['child']):continue
   xmin,xmax=sorted((a[0],b[0]));ymin,ymax=sorted((a[1],b[1]))
   if abs(a[1]-b[1])<.1:
    hit=e['y']+1<a[1]<e['y']+e['height']-1 and xmax>e['x']+1 and xmin<e['x']+e['width']-1
   else:hit=e['x']+1<a[0]<e['x']+e['width']-1 and ymax>e['y']+1 and ymin<e['y']+e['height']-1
   if hit:crossed.append((edge['id'],e['id']))
assert not crossed,crossed
from lxml import etree
schema=etree.XMLSchema(etree.parse(str(ROOT/'tmp/drawio-validation/mxfile.xsd')))
schema.assertValid(etree.parse(str(stem.with_suffix('.drawio'))))
report=dict(tables=len(entities),relationships=len(edge_report),domains=len(groups),width=W,height=H,
 drawio_xsd_valid=True,entities_do_not_overlap=True,routes_do_not_cross_unrelated_tables=True,
 only_verified_foreign_keys=True,cardinality_from_nullability_and_unique_keys=True,
 source=model['source'],source_sha256=model['source_sha256'],
 drawio_sha256=hashlib.sha256(stem.with_suffix('.drawio').read_bytes()).hexdigest(),relationships_detail=edge_report,
 omitted_relationships=model['omitted_relationships'])
(BASE/'VALIDACION_ER.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k not in ('relationships_detail','omitted_relationships')},ensure_ascii=False))
