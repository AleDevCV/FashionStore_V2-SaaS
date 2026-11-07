"""Sequences corresponding to the nine accepted simplified BCE models."""
from pathlib import Path
from collections import Counter
import hashlib,json
import xml.etree.ElementTree as ET
from lxml import etree
from sequence_diagrams import Diagram,M,R,A,O,L

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'docs/diagramas_secuencia'
REPORTS=[]
SCHEMA=etree.XMLSchema(etree.parse(str(ROOT/'tmp/drawio-validation/mxfile.xsd')))


class Case:
    def __init__(self,num):
        self.code=f'CU{num:02}'
        self.source=ROOT/'docs/diagramas_robustez'/(self.code+'_Simplificado')/(self.code+'_Robustez_Simplificada_Modelo.json')
        self.model=json.loads(self.source.read_text(encoding='utf-8'))
        self.orig={m['n']:m for m in self.model['messages']}
    def m(self,n,text=None):
        m=self.orig[n]
        event=M(m['a'],m['b'],text or m['text'],m['kind']=='reply')
        event['robustness_number']=n
        return event
    def s(self,*numbers):return [self.m(n) for n in numbers]
    def err(self,text):return R('control','b_pre',text)
    def emit(self,body,order):
        nodes=self.model['nodes']
        assert len(order)==len(nodes) and set(order)==set(nodes)
        participants=[(k,nodes[k]['name'],nodes[k]['kind']) for k in order]
        d=Diagram(self.code,self.model['title'].split(' - ',1)[1],participants,body,self.model['sources'])
        d.width+=30
        for f in d.frames:
            if f['kind']=='loop':
                controllers=[p for p in f['participants'] if nodes[p]['kind']=='control']
                assert controllers
                first=min(controllers,key=lambda p:d.x[p])
            else:first='b_pre'
            f['starts_at']=first
            f['left']=d.x[first]-30
            f['right']=max(d.x[p] for p in f['participants'])+30
            f['width']=f['right']-f['left']
            assert all(d.x[p]>=d.x[first] for p in f['participants'])
            assert all(nodes[p]['kind']!='actor' for p in f['participants'])
            if f['kind']=='loop':
                enclosed={p for p in order if d.x[first]<=d.x[p]<=f['right']-30}
                assert enclosed==set(f['participants']),(self.code,'unrelated loop participant',enclosed,f)
        folder=BASE/self.code
        report=d.render(folder)
        native=folder/(self.code+'_Diagrama_Secuencia.drawio')
        doc=etree.parse(str(native));SCHEMA.assertValid(doc)
        ids=[c.get('id') for c in doc.iter('mxCell')]
        assert len(ids)==len(set(ids))
        assert Counter(p[2] for p in participants)==Counter(n['kind'] for n in nodes.values())
        covered=[e['robustness_number'] for e in d.events if 'robustness_number' in e]
        assert sorted(covered)==list(range(1,len(self.orig)+1)),(self.code,covered)
        assert all(not(nodes[e['a']]['kind']=='entity' and nodes[e['b']]['kind']=='entity') for e in d.events)
        for s in self.model['sources']:
            assert hashlib.sha256((ROOT/s['file']).read_bytes()).hexdigest()==s['sha256'],s['file']
        report.update(actores=sum(p[2]=='actor' for p in participants),interfaces=sum(p[2]=='boundary' for p in participants),
                      controles=sum(p[2]=='control' for p in participants),entidades=sum(p[2]=='entity' for p in participants),
                      participantes_identicos_a_robustez=True,mensajes_principales_cubiertos=len(covered),xsd_valido=True,
                      limites_fragmentos_validados=True,bucles_solo_participantes_involucrados=True,
                      sin_actores_dentro_de_fragmentos=True,sin_comunicacion_entre_entidades=True)
        trace=dict(robustness_source=str(self.source.relative_to(ROOT)),participants=[dict(id=p,name=n,kind=k) for p,n,k in participants],
                   events=d.events,frames=d.frames,notes=self.model.get('notes',[]),
                   scope='Mismos recorridos y participantes de robustez; numeración de secuencia nueva al añadir las alternativas.',
                   geometry='alt y opt parten de la interfaz principal; loop parte del control correspondiente. Margen de 30 px. El borde derecho corresponde al último participante afectado. Las líneas intermedias del orden fijo no implican interacciones adicionales.',
                   presentation='Los retornos al actor se generalizan cuando deben mostrar éxito o rechazo. Las acciones son escenarios independientes del CU, no un guion obligatorio.')
        (folder/(self.code+'_Secuencia_Trazabilidad.json')).write_text(json.dumps(trace,ensure_ascii=False,indent=2),encoding='utf-8')
        (folder/(self.code+'_Secuencia_Validacion.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        (folder/'LEEME.md').write_text('# '+self.model['title']+' - Secuencia\n\nArchivo editable .drawio, SVG vectorial y PNG para Word. Se conservan exactamente los participantes del modelo de robustez simplificado y se cubren sus '+str(len(covered))+' mensajes principales.\n\nLos alt y opt comienzan en Interfaz. Los loop comienzan en Control y cubren únicamente las líneas afectadas, reordenadas cuando hace falta para situarlas juntas. El borde derecho de cada recuadro corresponde a su último participante involucrado. Un rectángulo continuo puede atravesar líneas de vida intermedias sin enviarles mensajes.\n\nLa numeración se asigna de nuevo al incluir alternativas; el archivo de trazabilidad conserva la correspondencia con robustez. No se añaden participantes para validaciones o almacenamiento auxiliares. Cada acción se presenta como escenario independiente.\n\n'+ '\n'.join('- '+n for n in self.model.get('notes',[]))+'\n\nNo se modificó el programa, el Word ni los diagramas anteriores.\n',encoding='utf-8')
        REPORTS.append(report)
        print(self.code+': '+str(report['mensajes'])+' mensajes, '+str(len(participants))+' participantes, '+str(report['fragmentos']))


q=Case(7)
q.emit([
 *q.s(1,2,3,4),A(('hay proveedores',q.s(5)),('sin coincidencias',[q.err('Lista vacía')])),q.m(6),
 *q.s(7,8),A(('datos y NIT válidos',q.s(9,10,11,12)),('datos inválidos',[q.err('Informar validación del proveedor')])),
 q.m(13),O('se confirman cambios',q.m(14),A(('cambios válidos',q.s(15,16,17)),('cambios inválidos',[q.err('Informar validación de cambios')]))),
 *q.s(18,19),A(('compra y recepción válidas',[
   *q.s(20,21),L('por cada ítem recibido',q.m(22,'Guardar detalle'),q.m(23,'Registrar Entrada')), *q.s(24,25)]),
   ('datos o existencias inválidos',[q.err('Rechazar compra sin confirmar recepción')])),q.m(26,'Mostrar resultado de recepción'),
 *q.s(27,28),A(('compra autorizada existente',q.s(29,30,31)),('compra no disponible',[q.err('Compra no encontrada')])),q.m(32,'Mostrar detalle o aviso')
],['actor','b_pre','control','detalle','movimiento','compra','proveedor','bitacora'])

q=Case(8)
q.emit([
 *q.s(1,2,3,4),A(('hay sucursales autorizadas',q.s(5)),('sin sucursales',[q.err('Sin sucursales disponibles')])),q.m(6),
 *q.s(7,8,9,10),A(('hay registros',q.s(11)),('sin existencias registradas',[q.err('Resultado vacío')])),q.m(12),
 *q.s(13,14,15,16),A(('hay disponibilidad',q.s(17)),('sin unidades disponibles',[q.err('Sin disponibilidad para la variante')])),q.m(18)
],['actor','b_pre','control','inventario','sucursal'])

q=Case(9)
q.emit([
 *q.s(1,2,3,4),A(('hay prendas',q.s(5)),('sin coincidencias',[q.err('Catálogo vacío')])),q.m(6),
 *q.s(7,8),A(('prenda publicada',q.s(9,10,11)),('prenda no disponible',[q.err('Prenda no encontrada')])),q.m(12,'Mostrar ficha o aviso'),
 *q.s(13,14,15,16,17),
 q.m(18),O('se confirma consulta IA',*q.s(19,20,21),
   A(('proveedor disponible',q.s(22,23)),('usar alternativa local',[M('control','control','_ejecutar_fallback_recomendacion()')])),
   *q.s(24,25)),q.m(26,'Mostrar asistencia si fue solicitada'),
 q.m(27),O('cámara autorizada',*q.s(28,29,30),
   A(('token disponible',q.s(31,32)),('servicio no disponible',[R('b_ia','control','Fallo del proveedor'),q.err('Continuar sin vestidor')]))),
 q.m(33,'Mostrar vestidor o aviso de disponibilidad')
],['actor','b_pre','control','prenda','inventario','bitacora','b_ia'])

q=Case(10)
q.emit([
 *q.s(1,2,3,4,5,6),
 *q.s(7,8),A(('movimiento autorizado',q.s(9,10,11,12)),('datos o stock inválidos',[q.err('Rechazar movimiento sin efecto')])),q.m(13,'Mostrar resultado del movimiento'),
 *q.s(14,15,16,17),A(('hay movimientos',q.s(18)),('sin resultados',[q.err('Historial vacío')])),q.m(19)
],['actor','b_pre','control','inventario','movimiento','bitacora'])

q=Case(11)
q.emit([
 *q.s(1,2),A(('carrito y stock válidos',q.s(3,4,5,6)),('compra no disponible',[q.err('Informar validación de checkout')])),q.m(7,'Mostrar resumen o validación'),
 q.m(8),O('se elige pagar con Stripe',q.m(9),
   A(('Stripe disponible',q.s(10,11,12,13)),('no se puede iniciar pago',[q.err('Conservar reserva y permitir reintento')]))),q.m(14,'Abrir portal si existe sesión'),
 *q.s(15,16),
 A(('evento válido y nuevo',[
   *q.s(17,18,19,20),L('por cada detalle vendido',q.m(21,'Registrar Salida')),*q.s(22,23)]),
   ('evento ya procesado',[R('control','b_stripe','Devolver resultado anterior sin duplicar venta')]),
   ('firma o datos inválidos',[R('control','b_stripe','Rechazar evento sin confirmar venta')])),
 *q.s(24,25),A(('existe venta pagada',q.s(26,27,28)),('pago aún pendiente',[q.err('Mostrar estado pendiente o fallido')])),q.m(29,'Mostrar estado de la compra')
],['actor','b_pre','control','movimiento','reserva','pago','venta','bitacora','b_stripe'])

q=Case(12)
q.emit([
 *q.s(1,2),A(('datos y disponible válidos',[
   *q.s(3,4,5,6),L('por cada detalle reservado',q.m(7,'Retener unidades durante 24 horas')),*q.s(8,9)]),
   ('reserva no disponible',[q.err('Rechazar reserva sin retención')])),q.m(10,'Mostrar resultado de reserva'),
 *q.s(11,12),A(('reserva propia existente',q.s(13,14,15)),('reserva no autorizada',[q.err('Reserva no disponible')])),q.m(16,'Mostrar seguimiento o aviso'),
 *q.s(17,18),A(('transición permitida',q.s(19,20)),('reserva finalizada o cobrada',[q.err('Preparación no permitida')])),
 *q.s(21,22),A(('venta pagada y autorizada',q.s(23,24,25)),('venta no disponible',[q.err('Impedir entrega')])),q.m(26,'Mostrar resultado de entrega'),
 *q.s(27,28),A(('reserva sin venta pagada',q.s(29,30,31)),('reserva ya pagada',[q.err('Gestionar devolución por atención al cliente')]))
],['actor','staff','b_pre','control','retencion','inventario','reserva','venta','bitacora'])

q=Case(13)
q.emit([
 *q.s(1,2,3,4),A(('hay productos',q.s(5)),('sin coincidencias',[q.err('No hay productos disponibles')])),q.m(6),
 *q.s(7,8),A(('ticket, stock y cobro válidos',[
   *q.s(9,10,11,12),L('por cada ítem vendido',q.m(13,'Guardar detalle de venta'),q.m(14,'Registrar Salida')),*q.s(15,16)]),
   ('validación comercial fallida',[q.err('Rechazar venta sin confirmar cobro')])),q.m(17,'Mostrar resultado y opción de comprobante'),
 *q.s(18,19),A(('venta autorizada existente',q.s(20,21,22)),('venta no disponible',[q.err('Venta no encontrada')]))
],['actor','b_pre','control','detalle','movimiento','inventario','venta','bitacora'])

q=Case(14)
q.emit([
 *q.s(1,2),A(('comprobante existente',q.s(3,4,5)),('no existe comprobante',[q.err('Permitir solicitud de generación')])),q.m(6,'Mostrar comprobante o aviso'),
 q.m(7),O('se solicita generar',q.m(8),A(('venta válida sin comprobante',q.s(9,10,11,12,13,14,15)),
   ('venta ajena o comprobante duplicado',[q.err('Rechazar generación sin duplicar documento')]))),
 *q.s(16,17,18,19),A(('archivo autorizado disponible',q.s(20,21,22)),('archivo no disponible',[q.err('Informar archivo ausente o acceso denegado')])),q.m(23,'Mostrar descarga o aviso')
],['actor','b_pre','control','comprobante','venta','pdf','bitacora'])

q=Case(16)
q.emit([
 *q.s(1,2),A(('descarga autorizada con red',q.s(3,4,5,6,7,8)),
   ('fallo de conexión o autorización',[q.err('Conservar copia y pendientes anteriores')])),q.m(9,'Mostrar estado de preparación'),
 *q.s(10,11),A(('existe copia local',q.s(12,13,14)),('sin copia descargada',[q.err('Preparar dispositivo cuando exista red')])),q.m(15,'Mostrar catálogo local o aviso'),
 *q.s(16,17),A(('permiso local y datos válidos',[q.m(18),L('por cada ítem reservado',q.m(19,'Guardar detalle en la misma transacción')),q.m(20)]),
   ('validación o guardado fallidos',[q.err('Revertir guardado sin declarar éxito')])),q.m(21,'Mostrar resultado provisional'),
 *q.s(22,23),A(('permiso, stock y efectivo válidos',[q.m(24),L('por cada ítem vendido',q.m(25,'Guardar detalle en la misma transacción')),q.m(26)]),
   ('validación o guardado fallidos',[q.err('Revertir guardado sin declarar éxito')])),q.m(27,'Mostrar resultado provisional'),
 *q.s(28,29,30,31),L('por cada operación consultada',q.m(32),q.m(33)),*q.s(34,35)
],['actor','b_pre','control','detalle','operacion','snapshot','backend','central'])

(BASE/'MANIFIESTO_SECUENCIAS_CU07_CU16.json').write_text(json.dumps(REPORTS,ensure_ascii=False,indent=2),encoding='utf-8')
combined=ET.Element('mxfile',host='app.diagrams.net',type='device',version='26.0.0')
for r in REPORTS:
    p=ET.parse(BASE/r['cu']/r['archivo']).getroot().find('diagram')
    p.set('name',r['cu']+' - Secuencia');combined.append(p)
data=ET.tostring(combined,encoding='utf-8',xml_declaration=True)
SCHEMA.assertValid(etree.fromstring(data))
(BASE/'CU07_CU14_CU16_Diagramas_Secuencia.drawio').write_bytes(data)
