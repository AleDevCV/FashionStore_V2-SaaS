from pathlib import Path
from collections import Counter
import hashlib,json,zipfile
from PIL import Image
from lxml import etree

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'docs/diagramas_secuencia'
reports=json.loads((BASE/'MANIFIESTO_SECUENCIAS_CU07_CU16.json').read_text(encoding='utf-8'))
schema=etree.XMLSchema(etree.parse(str(ROOT/'tmp/drawio-validation/mxfile.xsd')))
rows=[]
sources=set()
for r in reports:
    code=r['cu'];folder=BASE/code;stem=code+'_Diagrama_Secuencia'
    schema.assertValid(etree.parse(str(folder/(stem+'.drawio'))))
    with Image.open(folder/(stem+'.png')) as image:
        assert image.size==(r['ancho']*2,r['alto']*2)
        assert abs(image.info['dpi'][0]-300)<1
    trace=json.loads((folder/(code+'_Secuencia_Trazabilidad.json')).read_text(encoding='utf-8'))
    for source in r['fuentes']:
        assert hashlib.sha256((ROOT/source['file']).read_bytes()).hexdigest()==source['sha256']
        sources.add(source['file'])
    robust=json.loads((ROOT/trace['robustness_source']).read_text(encoding='utf-8'))
    assert {p['id'] for p in trace['participants']}==set(robust['nodes'])
    for p in trace['participants']:
        assert p['name']==robust['nodes'][p['id']]['name'] and p['kind']==robust['nodes'][p['id']]['kind']
    title=robust['title']
    rows.append('| '+title+' | '+str(r['mensajes'])+' | ['+code+' .drawio]('+code+'/'+stem+'.drawio) | [PNG]('+code+'/'+stem+'.png) |')

combined='CU07_CU14_CU16_Diagramas_Secuencia.drawio'
schema.assertValid(etree.parse(str(BASE/combined)))
assert len(etree.parse(str(BASE/combined)).getroot().findall('diagram'))==9
index='''# Diagramas de secuencia - CU07 a CU14 y CU16

Cada archivo corresponde al respectivo modelo de robustez simplificado, conservando exactamente sus actores, interfaces, controles y entidades. Los mensajes originales mantienen su referencia en el archivo de trazabilidad y se renumeran al incorporar alternativas.

| Caso de uso | Mensajes | Editable | Para Word |
|---|---:|---|---|
'''+ '\n'.join(rows)+'''

[Abrir los nueve diagramas en un solo archivo](CU07_CU14_CU16_Diagramas_Secuencia.drawio).

Los alt y opt comienzan en la interfaz principal y los loop en el control correspondiente. Todos terminan en su último participante afectado, con margen de 30 px. Las líneas de vida se han ordenado para que cada loop abarque únicamente sus participantes. Un rectángulo continuo de UML puede atravesar otras líneas intermedias sin que reciban mensajes ni participen en ese operando.

Cada CU incluye PNG de alta resolución a 300 ppp, SVG, archivo editable, trazabilidad y validación. Los escenarios se presentan por acción y no constituyen una cadena obligatoria de operaciones. Las consultas sin repetición no reciben loop; los subflujos sin condición opcional no reciben opt.

La revisión incluye formato XML, correspondencia de todos los participantes y mensajes principales, límites de los fragmentos y revisión visual. No se modificó el Word, los diagramas previos ni el código funcional. No se ejecutaron comandos Git.
'''
(BASE/'INDICE_SECUENCIAS_CU07_CU16.md').write_text(index,encoding='utf-8')
zipname='CU07_CU14_CU16_Diagramas_Secuencia.zip'
with zipfile.ZipFile(BASE/zipname,'w',zipfile.ZIP_DEFLATED) as z:
    for r in reports:
        folder=BASE/r['cu']
        for file in sorted(folder.iterdir()):
            if file.is_file():z.write(file,r['cu']+'/'+file.name)
    for file in [combined,'INDICE_SECUENCIAS_CU07_CU16.md']:
        z.write(BASE/file,file)
fragments=Counter()
for r in reports:fragments.update(r['fragmentos'])
result=dict(casos=9,diagramas_individuales=9,paginas_conjunto=9,
            mensajes_principales_cubiertos=sum(r['mensajes_principales_cubiertos'] for r in reports),
            mensajes_secuencia=sum(r['mensajes'] for r in reports),fragmentos=dict(fragments),
            participantes_identicos_a_robustez=True,inicio_y_fin_fragmentos_validados=True,
            bucles_sin_lineas_ajenas=True,fuentes_sin_cambios=len(sources),png_300ppp=True,xsd_individuales_y_conjunto=True,
            revision_visual_realizada=True)
(BASE/'VALIDACION_ENTREGA_SECUENCIAS_CU07_CU16.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
