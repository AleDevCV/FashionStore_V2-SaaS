"""Validate source coverage, native UML files and lossless vertical tiling."""
import csv
import hashlib
import json
import math
import sys
from collections import Counter
from pathlib import Path
from lxml import etree

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'scripts'))
from build_class_model import Canvas,page_contents,FONT,FONT_BOLD,W,UNIT
OUT=ROOT/'docs/diagrama_clases'


def length(points):
    return sum(math.hypot(b[0]-a[0],b[1]-a[1]) for a,b in zip(points,points[1:]))


def texts(primitives,offset=0):
    return Counter((p['classifier'],p['x'],p['y']+offset+i*UNIT,line,p['size'],p['bold'],p['underline'])
                   for p in primitives if p['type']=='text'
                   for i,line in enumerate(p['lines']))


def check_native(path,schema,expected_pages):
    doc=etree.parse(str(path),etree.XMLParser(resolve_entities=False,no_network=True))
    schema.assertValid(doc)
    pages=doc.xpath('//diagram');assert len(pages)==expected_pages
    assert not doc.xpath('//comment()')
    for page in pages:
        cells=page.xpath('.//mxCell');identified=page.xpath('.//*[@id]')
        ids={c.get('id') for c in identified}
        assert len(ids)==len(identified)
        for c in cells:
            for role in ('source','target','parent'):
                if c.get(role):assert c.get(role) in ids
    return doc


def main():
    model=json.loads((OUT/'modelo_clases.json').read_text(encoding='utf-8'))
    manifest=json.loads((OUT/'MANIFIESTO_LAMINAS.json').read_text(encoding='utf-8'))
    datasets=[json.loads((ROOT/'tmp/class-model'/(language+'.json')).read_text(encoding='utf-8')) for language in ('python','typescript','dart')]
    original=[n for d in datasets for n in d['nodes']]
    assert {n['id'] for n in original}=={n['id'] for n in model['classifiers']}
    assert len(model['classifiers'])==manifest['clasificadores']==len(original)
    assert sum(len(n['methods']) for n in original)==manifest['operaciones']
    assert sum(len(n['attributes']) for n in original)==manifest['atributos']
    for path,sha in model['files_sha256'].items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==sha
    ids={n['id'] for n in original}
    assert all(e['source'] in ids and e['target'] in ids for e in model['relationships'])
    canvas=Canvas();canvas.primitives=json.loads((ROOT/'tmp/class-model/primitives.json').read_text(encoding='utf-8'))
    full=page_contents(canvas,0,manifest['alto'])
    expected_text=texts(full);actual_text=Counter()
    expected_length=sum(length(p['points']) for p in full if p['type']=='path')
    actual_length=0
    expected_area=sum(p['w']*p['h'] for p in full if p['type']=='rect')
    actual_area=0
    schema=etree.XMLSchema(etree.parse(str(ROOT/'tmp/drawio-validation/mxfile.xsd')))
    general=check_native(OUT/'FashionStore_Clases_General.drawio',schema,1)
    groups=general.xpath('//mxCell[starts-with(@style,"group;")]')
    assert len(groups)==len(original)
    linked=general.xpath('//mxCell[@edge="1"][@source and @target]')
    assert len(linked)==len(model['relationships'])
    check_native(OUT/'FashionStore_Clases_Por_Partes.drawio',schema,len(manifest['laminas']))
    prev=0
    for part in manifest['laminas']:
        assert part['ancho']==W and part['y_inicio']==prev
        assert part['alto']==part['y_fin']-part['y_inicio']
        prev=part['y_fin']
        content=page_contents(canvas,part['y_inicio'],part['y_fin'])
        actual_text+=texts(content,part['y_inicio'])
        actual_length+=sum(length(p['points']) for p in content if p['type']=='path')
        actual_area+=sum(p['w']*p['h'] for p in content if p['type']=='rect')
        check_native(OUT/'laminas'/(part['archivo']+'.drawio'),schema,1)
        svg=etree.parse(str(OUT/'laminas'/(part['archivo']+'.svg')))
        assert float(svg.getroot().get('width'))==W
        assert float(svg.getroot().get('height'))==part['alto']
    assert prev==manifest['alto']
    assert actual_text==expected_text
    assert abs(actual_length-expected_length)<.001
    assert abs(actual_area-expected_area)<.001
    bad=[]
    for p in full:
        if p['type']!='text' or p['size']!=20:continue
        font=FONT_BOLD if p['bold'] else FONT
        for line in p['lines']:
            if font.getlength(line)>p['w']+1:bad.append((p.get('classifier'),line))
    assert not bad,bad[:5]
    for name,total in [('INVENTARIO_OPERACIONES.csv',manifest['operaciones']),('INVENTARIO_ATRIBUTOS.csv',manifest['atributos'])]:
        with (OUT/name).open(encoding='utf-8-sig',newline='') as f:assert len(list(csv.reader(f)))-1==total
    result={'fuentes_sin_modificaciones':True,'todos_los_clasificadores_extraidos_representados':True,
            'clasificadores':len(original),'operaciones':manifest['operaciones'],'atributos':manifest['atributos'],
            'relaciones':len(model['relationships']),'conectores_vinculados_a_clases':len(linked),
            'paginas':len(manifest['laminas']),'ancho_uniforme':W,
            'sin_huecos_ni_solapamientos_entre_laminas':True,
            'textos_reconstruidos_sin_perdidas':True,'longitud_de_conectores_reconstruida':True,
            'fondos_reconstruidos_sin_perdidas':True,'texto_sin_recortes':True,
            'esquema_drawio_valido':True,'sha256_general':hashlib.sha256((OUT/'FashionStore_Clases_General.drawio').read_bytes()).hexdigest()}
    (OUT/'VALIDACION.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':main()
