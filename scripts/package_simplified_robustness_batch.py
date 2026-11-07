"""Collect the nine verified standalone diagrams and their delivery index."""
from pathlib import Path
import hashlib
import json
import xml.etree.ElementTree as ET
import zipfile
from lxml import etree
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'docs/diagramas_robustez'
manifest=json.loads((BASE/'MANIFIESTO_CU07_CU16_SIMPLIFICADOS.json').read_text(encoding='utf-8'))
all_native=ET.Element('mxfile',dict(host='app.diagrams.net',type='device',version='29.0.0'))
rows=[]
sources=set()
for e in manifest:
    folder=ROOT/e['folder'];stem=e['stem'];case=e['caso']
    model=json.loads((folder/(stem+'_Modelo.json')).read_text(encoding='utf-8'))
    for s in model['sources']:
        assert hashlib.sha256((ROOT/s['file']).read_bytes()).hexdigest()==s['sha256'],s['file']
        sources.add(s['file'])
    native=ET.parse(folder/(stem+'.drawio')).getroot()
    assert len(native.findall('diagram'))==1
    diagram=native.find('diagram');diagram.set('id',case+'-simplificado')
    diagram.set('name',model['title'])
    all_native.append(diagram)
    script=json.loads((folder/'VALIDACION_JSCRIPT.json').read_text(encoding='utf-8'))
    assert script['mensajes']==len(model['messages']) and script['textos_numeros_y_sentidos_coinciden']
    with Image.open(folder/(stem+'_General.png')) as image:
        assert image.size==(model['views'][0]['width'],model['views'][0]['height'])
        assert abs(image.info['dpi'][0]-300)<1
    def link(label,file):return '['+label+']('+case+'_Simplificado/'+file+')'
    rows.append('| '+model['title']+' | '+str(e['mensajes'])+' | '+str(e['entidades'])+' | '+link('draw.io',stem+'.drawio')+' | '+link('PNG',stem+'_General.png')+' | '+link('JScript','JScript_Generar_Robustez_'+case+'.js')+' |')

ET.indent(all_native,space='  ')
xml=ET.tostring(all_native,encoding='utf-8',xml_declaration=True)
etree.XMLSchema(etree.parse(str(ROOT/'tmp/drawio-validation/mxfile.xsd'))).assertValid(etree.fromstring(xml))
combined='CU07_CU14_CU16_Robustez_Simplificada.drawio'
(BASE/combined).write_bytes(xml)
index='''# Diagramas de robustez simplificados - CU07 a CU14 y CU16

Cada caso tiene una página propia con mensajes separados y numeración consecutiva, sin etiquetas HTTP ni comunicación entre entidades. Se conserva una única responsabilidad de control por entidad, aunque el CU16 diferencia los controles local y central.

| Caso de uso | Mensajes | Entidades | Editable | Para Word | Enterprise Architect |
|---|---:|---:|---|---|---|
'''+ '\n'.join(rows)+'''

También puedes abrir [todos los diagramas en un archivo con nueve pestañas](CU07_CU14_CU16_Robustez_Simplificada.drawio) o utilizar [el paquete de entrega ZIP](CU07_CU14_CU16_Robustez_Simplificada.zip).

La bitácora se representa cuando el flujo actual escribe sus eventos. CU08 solo consulta información; CU16 registra localmente y su auditoría central corresponde a CU17. No se inventan tablas ni llamadas a un servidor durante la operación sin conexión.

Los controles y las interfaces pueden agrupar pantallas o módulos reales como abstracción de análisis. Los archivos Modelo.json, CSV, Validacion.json y LEEME de cada carpeta explican las fuentes y los detalles omitidos para mantener el diagrama breve.

Los JScript son autocontenidos: selecciona el paquete de destino en Enterprise Architect, crea un script JScript, pega el contenido del caso y ejecútalo. Se crea un paquete nuevo. Se validó su generación completa en simulación; la visualización en una sesión real de EA permanece por comprobar.

No se modificó el CU06 aceptado, el documento Word ni el código funcional del programa. No se ejecutaron comandos Git.
'''
(BASE/'INDICE_SIMPLIFICADOS_CU07_CU16.md').write_text(index,encoding='utf-8')
with zipfile.ZipFile(BASE/'CU07_CU14_CU16_Robustez_Simplificada.zip','w',zipfile.ZIP_DEFLATED) as z:
    for e in manifest:
        folder=ROOT/e['folder']
        for file in sorted(folder.iterdir()):
            if file.is_file():z.write(file,e['caso']+'_Simplificado/'+file.name)
    z.write(BASE/combined,combined)
    z.write(BASE/'INDICE_SIMPLIFICADOS_CU07_CU16.md','INDICE_SIMPLIFICADOS_CU07_CU16.md')
report=dict(casos=9,archivos_drawio_individuales=9,paginas_conjunto=9,jscript_individuales=9,
            png_individuales=9,mensajes=sum(e['mensajes'] for e in manifest),fuentes_sin_cambios=len(sources),
            xsd_individuales_y_conjunto=True,indices_y_direcciones_validados=True,png_con_dimensiones_y_300ppp=True,
            revision_visual_realizada=True,ejecucion_nativa_EA=False)
(BASE/'VALIDACION_ENTREGA_CU07_CU16.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
