"""CU06 sequence with exactly the accepted simplified robustness participants."""
from pathlib import Path
import hashlib
import json
from collections import Counter
from lxml import etree
from sequence_diagrams import Diagram,M,R,A,O,L

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/diagramas_secuencia/CU06'
source=ROOT/'docs/diagramas_robustez/CU06_Simplificado/CU06_Robustez_Simplificada_Modelo.json'
robust=json.loads(source.read_text(encoding='utf-8'))
original={m['n']:m for m in robust['messages']}
refs=[]

def msg(n,text=None):
    m=original[n]
    result=M(m['a'],m['b'],text or m['text'],m['kind']=='reply')
    result['robustness_number']=n
    refs.append(dict(robustness=n,source=m['source'],symbol=m['symbol'],line=m.get('line'),sequence_text=result['text']))
    return result

def error(text):return R('control','b_pre',text)

body=[
 msg(1),msg(2),msg(3),msg(4),
 A(('hay coincidencias',[msg(5)]),('sin coincidencias',[error('Catálogo vacío')])),msg(6),
 msg(7),msg(8),
 A(('datos y nombre válidos',[msg(9),msg(10),msg(11),msg(12)]),
   ('datos o nombre inválidos',[error('Informar validación de categoría')])),
 msg(13),msg(14),
 A(('nombre y fechas válidos',[msg(15),msg(16),msg(17),msg(18)]),
   ('nombre o fechas inválidos',[error('Informar validación de temporada')])),
 msg(19),msg(20),
 A(('datos válidos y SKU único',[
    msg(21),msg(22),
    L('por cada variante',msg(23,'_crear_variante(datos)'),msg(24)),
    msg(25),msg(26)]),
   ('datos inválidos o SKU repetido',[error('Informar validación de prenda')])),
 msg(27,'Mostrar resultado del registro'),
 msg(28),
 O('se confirman los cambios',msg(29),
   A(('cambios válidos',[msg(30),msg(31),msg(32)]),
     ('cambios inválidos',[error('Informar validación de cambios')]))),
 msg(33),msg(34),
 A(('prenda activa y autorizada',[msg(35),msg(36),msg(37)]),
   ('prenda ausente o ya inactiva',[error('Informar rechazo de inhabilitación')]))
]

# Variant is adjacent to Control, so the repetition frame contains only those two.
order=['actor','b_pre','control','variante','prenda','categoria','temporada','bitacora']
participants=[(k,robust['nodes'][k]['name'],robust['nodes'][k]['kind']) for k in order]
diagram=Diagram('CU06','Administrar catálogo de prendas',participants,body,robust['sources'])
diagram.width+=30
for frame in diagram.frames:
    first='control' if frame['kind']=='loop' else 'b_pre'
    frame['left']=diagram.x[first]-30
    frame['right']=max(diagram.x[p] for p in frame['participants'])+30
    frame['width']=frame['right']-frame['left']
    frame['starts_at']=first
    assert all(diagram.x[p]>=diagram.x[first] for p in frame['participants'])
    assert len(frame['participants'])>=2

report=diagram.render(OUT)
native=OUT/'CU06_Diagrama_Secuencia.drawio'
doc=etree.parse(str(native))
etree.XMLSchema(etree.parse(str(ROOT/'tmp/drawio-validation/mxfile.xsd'))).assertValid(doc)
ids=[c.get('id') for c in doc.iter('mxCell')]
assert len(ids)==len(set(ids))
assert Counter(k for _,_,k in participants)==Counter(n['kind'] for n in robust['nodes'].values())
assert set(order)==set(robust['nodes'])
covered=[e['robustness_number'] for e in diagram.events if 'robustness_number' in e]
assert sorted(covered)==list(range(1,38))
assert all(not (robust['nodes'][e['a']]['kind']=='entity' and robust['nodes'][e['b']]['kind']=='entity') for e in diagram.events)
for f in diagram.frames:
    assert f['left']==diagram.x['control' if f['kind']=='loop' else 'b_pre']-30
    assert f['right']==max(diagram.x[p] for p in f['participants'])+30
    if f['kind']=='loop':assert set(f['participants'])=={'control','variante'}
for s in robust['sources']:
    assert hashlib.sha256((ROOT/s['file']).read_bytes()).hexdigest()==s['sha256'],s['file']
trace=dict(participants=[dict(id=k,name=n,kind=t) for k,n,t in participants],
           robustness_source=str(source.relative_to(ROOT)),
           events=diagram.events,frames=diagram.frames,correspondence=refs,
           scope='Mismas seis acciones principales de la robustez; validaciones y alternativas resumidas sin añadir entidades. Los controles son responsabilidades de análisis, no clases Python inventadas.',
           geometry='alt y opt inician en la línea de vida de Interfaz (margen de 30 px); loop inicia en Control. El extremo derecho se limita al último participante afectado. Las líneas intermedias del orden fijo no implican interacción si no reciben mensajes.',
           changes='Se conserva cada uno de los 37 mensajes principales. El retorno 27 se generaliza a resultado para cubrir éxito y rechazo. Los números de secuencia se asignan de nuevo al añadir alternativas.')
(OUT/'CU06_Secuencia_Trazabilidad.json').write_text(json.dumps(trace,ensure_ascii=False,indent=2),encoding='utf-8')
report.update(actores=1,interfaces=1,controles=1,entidades=5,xsd_valido=True,participantes_identicos_a_robustez=True,
              mensajes_principales_cubiertos=37,fragmentos_con_inicio_y_fin_validado=True,
              loop_solo_control_y_variante=True,sin_comunicacion_entre_entidades=True)
(OUT/'CU06_Secuencia_Validacion.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'LEEME.md').write_text('''# CU06 - Diagrama de secuencia

Una vista general editable con exactamente los ocho participantes del diagrama de robustez simplificado: Administrador de empresa, Administración del catálogo, Gestión del catálogo, Categoría, Temporada/Colección, Prenda, Variante y Bitácora.

La numeración se asigna de nuevo para incluir las alternativas. Los 37 mensajes principales de robustez conservan su correspondencia en el archivo de trazabilidad. Las seis acciones se presentan como recorridos independientes, no como pasos que todo usuario deba ejecutar obligatoriamente.

Los fragmentos alt y opt comienzan en Interfaz con un margen de 30 px. El loop comienza en Control y abarca únicamente Control y Variante, colocados contiguamente. El límite derecho de cada fragmento corresponde a su último participante afectado. En UML, un rectángulo continuo puede atravesar líneas de vida intermedias por su orden fijo; eso no añade interacciones con esas entidades.

El opt representa la confirmación de la edición; cancelar no invoca el backend. Los alt distinguen consultas vacías y validaciones fallidas de los recorridos aceptados. No se añaden entidades para catálogos auxiliares, imagen o inventario; se conserva el nivel de abstracción de robustez. La aplicación funcional y el Word no se modifican.
''',encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
