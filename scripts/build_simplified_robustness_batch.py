"""Nine compact BCE communication diagrams, matching the accepted CU06 style."""
from __future__ import annotations
import ast
from collections import defaultdict
import csv
import hashlib
import json
from pathlib import Path
import re
from lxml import etree
import build_numbered_robustness_cu06 as draw

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/diagramas_robustez'
B='Parcial2_backend/app/'
F='Parcial2_frontend-web/src/app/'
D='Parcial2_mobile/lib/'
BIT=B+'services/bitacora_service.py'
CASES=[]


class Case:
    def __init__(self,number,name,actor,ui,control,sources):
        self.id=f'CU{number:02}'
        self.name=name
        self.sources=sources
        self.notes=[]
        self.messages=[]
        self.actions=[]
        self.nodes={}
        self.node('actor','actor',actor)
        self.node('b_pre','boundary','Frontend : '+ui)
        self.node('control','control',control,note='Control de análisis que agrupa los módulos indicados en las referencias del caso de uso.')
        CASES.append(self)
    def node(self,key,kind,name,table=None,**extra):
        self.nodes[key]=dict(kind=kind,name=name,**extra)
        if table:self.nodes[key]['table']=table
    def entity(self,key,name,table=None):self.node(key,'entity',name,table or key)
    def action(self,name,actor='actor',ui='b_pre'):
        self.actions.append(dict(id=len(self.actions)+1,name=name,first=len(self.messages)+1,actor=actor,ui=ui))
        self.msg(actor,ui,name,'ui')
    def begin(self,name,fn,args,source,kind='invoke',actor='actor',ctrl='control'):
        self.action(name,actor)
        self.msg('b_pre',ctrl,fn+'('+args+')',kind,source,fn)
    def msg(self,a,b,text,kind='read',source=None,symbol=None):
        assert a in self.nodes and b in self.nodes
        self.messages.append(dict(n=len(self.messages)+1,action=self.actions[-1]['id'],a=a,b=b,text=text,kind=kind,color=draw.COLORS[kind],source=source,symbol=symbol))
    def read(self,entity,fn,args,result,source,ctrl='control'):
        self.msg(ctrl,entity,fn+'('+args+')','read',source,fn)
        self.msg(entity,ctrl,result,'reply')
    def write(self,entity,text,source,symbol,ctrl='control'):
        self.msg(ctrl,entity,text,'write',source,symbol)
    def audit(self,label,source=BIT,symbol='registrar_bitacora'):
        self.write('bitacora',label,source,symbol)
    def end(self,result,show=None,ctrl='control'):
        self.msg(ctrl,'b_pre',result,'reply')
        if show:self.msg('b_pre',self.actions[-1]['actor'],show,'reply')
        self.actions[-1]['last']=len(self.messages)


# CU07: purchasing and reception are a single actual transaction, not invented stages.
c=Case(7,'Gestionar proveedores, compras y recepciones','Administrador de empresa','Proveedores y compras','Backend : Gestión de abastecimiento',
 [F+'features/proveedores/proveedores.ts',F+'features/compras/compras.ts',D+'features/compras/compras_screen.dart'])
for k,n,t in [('proveedor','Proveedor','proveedor'),('compra','Compra','compra'),('detalle','Detalle de compra','detalle_compra'),('movimiento','Movimiento de inventario','movimiento_inventario'),('bitacora','Bitácora','bitacora')]:c.entity(k,n,t)
PR,PS=B+'routers/proveedores.py',B+'services/proveedor_service.py'
CR,CS=B+'routers/compras.py',B+'services/compra_service.py'
c.begin('Consultar proveedores','listar_proveedores','búsqueda',PR,'read')
c.read('proveedor','listar_proveedores','búsqueda','proveedores',PS);c.end('proveedores','Mostrar proveedores')
c.begin('Registrar proveedor','crear_proveedor','datos',PR)
c.write('proveedor','crear_proveedor(datos)',PS,'crear_proveedor');c.msg('proveedor','control','proveedor creado','reply')
c.audit('registrar_bitacora(proveedor, alta)');c.end('proveedor registrado')
c.begin('Editar proveedor','actualizar_proveedor','id, cambios',PR)
c.write('proveedor','actualizar_proveedor(id, cambios)',PS,'actualizar_proveedor');c.audit('registrar_bitacora(proveedor, modificación)');c.end('proveedor actualizado')
c.begin('Confirmar compra y recepción','registrar_compra','datos e ítems',CR)
c.write('compra','registrar_compra(datos)',CS,'registrar_compra');c.msg('compra','control','id_compra','reply')
c.write('detalle','Guardar detalle [por ítem]',CS,'registrar_compra')
c.write('movimiento','Registrar Entrada [por ítem recibido]',CS,'registrar_compra');c.audit('registrar_bitacora(compra, recepción)')
c.end('compra y recepción confirmadas','Mostrar recepción registrada')
c.begin('Consultar compra y detalles','obtener_compra','id_compra',CR,'read')
c.read('compra','obtener_compra_por_id','id_compra','compra con sus detalles',CS);c.end('detalle de compra','Mostrar compra recibida')
c.notes=['La recepción ocurre al registrar_compra; no existe una segunda API de recepción independiente. Los movimientos actualizan el inventario mediante el trigger existente.',
 'No se inventa una entidad Recepción ni se duplica el descuento/entrada de stock. La consulta móvil se conserva; el registro se representa en la interfaz administrativa.']

# CU08: read-only inventory and availability, including the existing stock view.
c=Case(8,'Consultar inventario y disponibilidad','Personal autorizado','Inventario y disponibilidad','Backend : Consulta de inventario',
 [F+'features/inventario-monitoreo/inventario-monitoreo.ts',F+'features/catalogo/prenda-detalle/prenda-detalle.ts',D+'features/inventario_monitoreo/estado_inventario_screen.dart'])
c.entity('sucursal','Sucursal');c.entity('inventario','Inventario y disponibilidad','inventario / inventario_catalogo')
c.begin('Seleccionar sucursal autorizada','listar_sucursales','filtros',B+'routers/geografia.py','read')
c.read('sucursal','listar_sucursales','filtros','sucursales autorizadas',B+'services/geografia_service.py');c.end('sucursales','Mostrar sucursales')
c.begin('Consultar existencias físicas','obtener_monitoreo_inventario','sucursal, filtros',B+'routers/inventario.py','read')
c.read('inventario','obtener_monitoreo_inventario','filtros','stock físico por variante',B+'services/inventario_service.py');c.end('existencias','Mostrar existencias')
c.begin('Consultar disponibilidad de variante','consultar_disponibilidad','id_variante',B+'routers/catalogo.py','read')
c.read('inventario','consultar_disponibilidad','id_variante','disponible por sucursal',B+'services/catalogo_service.py');c.end('disponibilidad','Mostrar disponibilidad conocida')
c.notes=['El monitoreo consulta inventario físico; consultar_disponibilidad utiliza la vista inventario_catalogo. No se atribuye a obtener_monitoreo_inventario una resta de reservas que no realiza.',
 'La vista de disponibilidad integra las retenciones. Sus tablas auxiliares se omiten del dibujo. No se modifica stock ni se inventan eventos de bitácora para consultas.']

# CU09: optional external AI is an integration boundary, not a database entity.
c=Case(9,'Explorar catálogo y asistencia de compra','Visitante / Cliente','Catálogo y asistencia','Backend : Catálogo y asistencia',
 [F+'features/catalogo/catalogo.ts',F+'features/catalogo/probador-ia/probador-ia.ts',D+'features/catalogo/catalogo_screen.dart'])
c.entity('prenda','Prenda');c.entity('inventario','Disponibilidad','inventario_catalogo');c.entity('bitacora','Bitácora')
c.node('b_ia','boundary','Integración : Servicios de IA')
R,S=B+'routers/catalogo.py',B+'services/catalogo_service.py'
c.begin('Buscar prendas y aplicar filtros','consultar_catalogo','filtros',R,'read')
c.read('prenda','consultar_catalogo','filtros','prendas publicadas',S);c.end('catálogo filtrado','Mostrar catálogo')
c.begin('Consultar ficha y variantes','obtener_ficha','id_prenda',R,'read')
c.read('prenda','obtener_ficha_publica','id_prenda','ficha con variantes y precios',S);c.end('ficha de prenda','Mostrar ficha')
c.begin('Consultar disponibilidad','consultar_disponibilidad','id_variante',R,'read')
c.read('inventario','consultar_disponibilidad','id_variante','sucursales con disponible',S);c.end('disponibilidad')
c.begin('Solicitar recomendaciones [cliente]','recomendar_outfit','preferencias',B+'routers/ia.py')
c.read('prenda','_obtener_catalogo_activo_con_stock','','catálogo autorizado',B+'services/ia_service.py')
c.msg('control','b_ia','Generar recomendaciones [si proveedor disponible]','invoke',B+'services/ia_service.py','recomendar_outfit')
c.msg('b_ia','control','sugerencias para validar / fallo de proveedor','reply')
c.audit('registrar_bitacora(recomendación IA)');c.end('recomendaciones validadas o alternativa local','Mostrar recomendaciones')
c.begin('Abrir vestidor [opcional]','obtener_realtime_token','',B+'routers/ia.py')
c.audit('registrar_bitacora(inicio de vestidor)')
c.msg('control','b_ia','create_realtime_token()','invoke',B+'services/tryon_service.py','create_realtime_token')
c.msg('b_ia','control','token efímero y configuración','reply');c.end('acceso al vestidor','Abrir cámara y vestidor')
c.notes=['La tienda ya fue elegida; su selección pertenece al acceso y contexto comercial. Las variantes se incluyen en la ficha para no repetir entidades auxiliares.',
 'Las recomendaciones requieren cliente autenticado y disponen de fallback local. La solicitud al proveedor es condicional. Se representa el acceso al vestidor Decart existente mediante token, sin inventar una implementación nueva.',
 'La integración IA es una interfaz externa. La cámara, permisos y procesamiento audiovisual permanecen dentro del subflujo opcional de la interfaz.']

# CU10: the trigger updates stock; no entity-to-entity calls are drawn.
c=Case(10,'Registrar movimientos de inventario','Personal autorizado','Movimientos de inventario','Backend : Gestión de movimientos',
 [F+'features/inventario-movimientos/movimientos.ts',D+'features/movimientos/movimientos_screen.dart'])
c.entity('inventario','Inventario');c.entity('movimiento','Movimiento de inventario','movimiento_inventario');c.entity('bitacora','Bitácora')
R,S=B+'routers/movimientos.py',B+'services/movimiento_service.py'
c.begin('Consultar stock de la variante','consultar_stock','sucursal, variante',R,'read')
c.read('inventario','obtener_stock_actual','sucursal, variante','stock físico',S);c.end('stock actual','Mostrar stock')
c.begin('Registrar movimiento y motivo','registrar_movimiento','datos',R)
c.write('movimiento','registrar_movimiento(datos)',S,'registrar_movimiento');c.msg('movimiento','control','movimiento y stock resultante','reply')
c.audit('registrar_bitacora(movimiento)');c.end('movimiento confirmado','Mostrar movimiento registrado')
c.begin('Consultar historial de movimientos','listar_movimientos','filtros',R,'read')
c.read('movimiento','listar_movimientos','filtros','movimientos autorizados',S);c.end('historial','Mostrar historial')
c.notes=['Las sucursales y variantes se validan dentro del control, sin desplegar todos los catálogos auxiliares. El stock se actualiza por trigger al insertar el movimiento.',
 'El esquema actual recibe una sucursal y no una sucursal de destino: no se inventa un traslado completo de dos sucursales ni una API de idempotencia inexistente para este endpoint.']

# CU11: the Stripe callback confirms payment; browser return alone never does.
c=Case(11,'Realizar compra y pago en línea','Cliente','Carrito y checkout','Backend : Compra y pago',
 [F+'features/checkout/checkout.ts',F+'features/pago/pago-exitoso/pago-exitoso.ts',D+'features/checkout/checkout_screen.dart'])
for k,n,t in [('reserva','Reserva','reserva'),('pago','Pago','pago_transaccion'),('venta','Venta','venta'),('movimiento','Movimiento de inventario','movimiento_inventario'),('bitacora','Bitácora','bitacora')]:c.entity(k,n,t)
c.node('b_stripe','boundary','Pasarela : Stripe')
VR,VS=B+'routers/ventas.py',B+'services/venta_service.py'
COM,PAY=B+'services/commerce.py',B+'services/payments.py'
c.begin('Preparar compra y confirmar resumen','crear_reserva','carrito, sucursal',VR)
c.write('reserva','reserve(cliente, sucursal, ítems)',COM,'reserve');c.msg('reserva','control','reserva y total autorizado','reply')
c.audit('Auditar reserva de checkout',COM,'reserve');c.end('reserva pendiente de pago','Mostrar total y medios de pago')
c.begin('Iniciar pago de prueba','crear_sesion_stripe','id_reserva',B+'routers/pagos.py')
c.msg('control','b_stripe','Crear sesión de pago Stripe','invoke',PAY,'checkout');c.msg('b_stripe','control','sesión y URL de pago','reply')
c.write('pago','Guardar intento Pendiente',PAY,'checkout');c.end('URL de pago','Abrir portal Stripe')
c.action('Completar pago de prueba',ui='b_stripe')
c.msg('b_stripe','control','stripe_webhook(evento, firma)','invoke',B+'routers/pagos.py','stripe_webhook')
c.msg('control','reserva','Validar reserva e importe del evento','read',PAY,'webhook');c.msg('reserva','control','reserva e importe esperado','reply')
c.write('venta','confirm_reservation(pago verificado)',COM,'confirm_reservation');c.msg('venta','control','id_venta','reply')
c.write('movimiento','Registrar Salida [por detalle]',COM,'confirm_reservation')
c.write('pago','Aprobar pago y enlazar venta',PAY,'webhook')
c.msg('control','b_stripe','evento procesado de forma idempotente','reply');c.actions[-1]['last']=len(c.messages)
c.begin('Consultar resultado del pago','payment_status','id_reserva',B+'routers/order_lifecycle.py','read')
c.read('venta','obtener_venta_por_id','id_venta [si pagada]','venta confirmada',VS);c.end('estado pagado y venta','Mostrar compra confirmada')
c.notes=['Se resume la modalidad Stripe de prueba. Firma, tenant, importe, moneda y duplicados se validan dentro del control; la redirección del navegador no confirma la venta.',
 'Los detalles y retenciones permanecen dentro de reserve y confirm_reservation. El descuento ocurre únicamente mediante movimientos. La creación de reserva sí inserta bitácora; no se inventan auditorías adicionales en el webhook actual.',
 'La consulta final representa el caso exitoso; el endpoint devuelve estado pendiente si aún no existe venta. El comprobante se detalla en CU14.']

# CU12: customer and staff have distinct actions, and delivery requires an existing sale.
c=Case(12,'Gestionar reservas de prendas','Cliente','Reservas y atención','Backend : Gestión de reservas',
 [F+'features/reservas-atencion/reservas-atencion.ts',F+'features/checkout/checkout.ts',D+'features/reservas/ticket_reserva_screen.dart'])
c.node('staff','actor','Personal autorizado')
for k,n,t in [('inventario','Inventario','inventario'),('reserva','Reserva','reserva'),('retencion','Retención','retencion'),('venta','Venta pagada','venta'),('bitacora','Bitácora','bitacora')]:c.entity(k,n,t)
c.begin('Registrar reserva de prendas','crear_reserva','cliente, sucursal, ítems',VR)
c.read('inventario','quote','ítems, sucursal','disponibilidad y precios válidos',COM)
c.write('reserva','reserve(cliente, sucursal, ítems)',COM,'reserve');c.msg('reserva','control','id_reserva','reply')
c.write('retencion','Retener unidades durante 24 horas',COM,'reserve');c.audit('Auditar reserva',COM,'reserve');c.end('reserva pendiente','Mostrar reserva')
c.begin('Consultar reserva propia','obtener_reserva','id_reserva',VR,'read')
c.read('reserva','obtener_reserva_por_id','id_reserva','reserva y detalles',VS);c.end('reserva','Mostrar seguimiento')
c.begin('Preparar prendas','actualizar_estado_reserva_endpoint',"id, 'Preparado'",VR,actor='staff')
c.write('reserva',"transition_reservation(id, 'Preparado')",COM,'transition_reservation');c.end('reserva preparada')
c.begin('Entregar reserva ya pagada','deliver','id_venta',B+'routers/order_lifecycle.py',actor='staff')
c.write('venta','Registrar entrega [venta pagada existente]',B+'routers/order_lifecycle.py','deliver')
c.write('reserva',"Marcar reserva 'Atendido'",B+'routers/order_lifecycle.py','deliver');c.end('entrega confirmada','Mostrar entrega registrada')
c.begin('Cancelar reserva sin pago','cancel','id_reserva',B+'routers/order_lifecycle.py')
c.write('retencion','Liberar retenciones',B+'routers/order_lifecycle.py','cancel')
c.write('reserva',"Marcar reserva 'Cancelado'",B+'routers/order_lifecycle.py','cancel');c.end('reserva cancelada')
c.notes=['Crear reserva retiene disponibilidad; preparar no crea una venta. El cobro pertenece a CU11 o CU13. deliver exige una venta existente y registra la entrega física por separado.',
 'La caducidad de disponibilidad se deriva de la vigencia de retencion; no se inventa una tarea programada que actualice estados. Los detalles se incluyen en Reserva como agregado.',
 'El código audita la creación; no se añaden escrituras de bitácora a preparar, cancelar o entregar si esas rutas no las realizan actualmente.']

# CU13: the receipt is optional within POS; its full persistence is covered by CU14.
c=Case(13,'Registrar venta presencial','Cajero / Personal autorizado','Terminal de venta POS','Backend : Venta presencial',
 [F+'features/pos/pos.ts'])
for k,n,t in [('inventario','Inventario','inventario'),('venta','Venta','venta'),('detalle','Detalle de venta','detalle_venta'),('movimiento','Movimiento de inventario','movimiento_inventario'),('bitacora','Bitácora','bitacora')]:c.entity(k,n,t)
PR,PS=B+'routers/pos.py',B+'services/pos_service.py'
c.begin('Buscar productos para el ticket','listar_productos_pos_endpoint','sucursal, búsqueda',PR,'read')
c.read('inventario','listar_productos_pos','sucursal, búsqueda','productos y stock',PS);c.end('productos disponibles','Mostrar productos')
c.begin('Confirmar venta y efectivo recibido','procesar_venta_pos_endpoint','ticket y cobro',PR)
c.read('inventario','quote','ítems, sucursal','stock y precios verificados',COM)
c.write('venta','procesar_venta_pos(datos)',PS,'procesar_venta_pos');c.msg('venta','control','id_venta','reply')
c.write('detalle','Guardar detalle [por ítem]',PS,'procesar_venta_pos')
c.write('movimiento','Registrar Salida [por ítem]',PS,'procesar_venta_pos');c.audit('registrar_bitacora(venta POS)')
c.end('venta, total y vuelto','Mostrar venta y opción de comprobante')
c.begin('Consultar venta registrada','obtener_venta','id_venta',VR,'read')
c.read('venta','obtener_venta_por_id','id_venta','venta con detalles',VS);c.end('venta registrada')
c.notes=['Sucursal, cliente mostrador y autorización se validan dentro del control. El código actual no ofrece una entidad de caja/apertura/cierre; no se inventa ese módulo.',
 'La confirmación de efectivo y la comprobación de precios preceden a la escritura. El trigger aplica el stock por movimiento. El comprobante se intenta en un savepoint opcional: un fallo no revierte la venta; su detalle corresponde a CU14.',
 'No se atribuye a este endpoint una clave UUID o reintento idempotente que no implementa explícitamente.']

# CU14: three independent user actions; generating a duplicate is not a read.
c=Case(14,'Obtener comprobantes de compra','Cliente / Personal autorizado','Comprobantes de compra','Backend : Gestión de comprobantes',
 [F+'core/services/comprobante.service.ts',D+'services/venta_service.dart'])
for k,n,t in [('venta','Venta y detalles','venta / detalle_venta'),('comprobante','Comprobante','comprobante'),('pdf','Archivo PDF','filesystem por tenant'),('bitacora','Bitácora','bitacora')]:c.entity(k,n,t)
c.nodes['pdf']['prefix']='Persistencia :'
RR,RS=B+'routers/comprobantes.py',B+'services/comprobante_service.py'
c.begin('Consultar comprobante de una venta','comprobante_por_venta','id_venta',RR,'read')
c.read('comprobante','obtener_comprobante_por_venta','id_venta','comprobante existente',RS);c.end('datos del comprobante','Mostrar comprobante')
c.begin('Generar comprobante [si no existe]','generar_comprobante','venta y datos',RR)
c.read('venta','generar_comprobante','id_venta','venta autorizada y detalles',RS)
c.write('pdf','Construir y guardar PDF',RS,'generar_comprobante')
c.write('comprobante','Registrar comprobante único y URL',RS,'generar_comprobante');c.msg('comprobante','control','comprobante registrado','reply')
c.audit('registrar_bitacora(comprobante)');c.end('comprobante generado')
c.begin('Descargar PDF autorizado','descargar_pdf_autorizado','número',RR,'read')
c.read('comprobante','descargar_pdf_autorizado','número','comprobante autorizado',RR)
c.msg('control','pdf','Leer PDF del tenant','read',RR,'descargar_pdf_autorizado');c.msg('pdf','control','archivo PDF','reply')
c.end('descarga PDF','Abrir o guardar comprobante')
c.notes=['Consultar o descargar no crea otro comprobante ni cambia la venta. Generar es una acción condicional separada; el servicio rechaza duplicados.',
 'Se incluye Archivo PDF como entidad persistente de archivos, no como una tabla. Los permisos y propiedad se validan mediante el contexto y RLS.',
 'Si falta el archivo, descargar_pdf_autorizado informa error. No se dibuja una regeneración automática que no existe. El envío de correo es un subflujo opcional omitido.']

# CU16: local persistence is explicit and no request to the backend occurs offline.
c=Case(16,'Registrar y consultar operaciones offline','Usuario autorizado','Operación offline web / móvil','Dispositivo : Gestión offline',
 [F+'features/offline/offline.ts',F+'core/services/offline.service.ts',D+'features/offline/offline_controller.dart',D+'features/offline/local_database.dart'])
c.nodes['control']['note']='Servicio local OfflineService en Angular y OfflineController/LocalDatabase en Flutter. No necesita servidor para registrar pendientes.'
c.node('backend','control','Backend : Catálogo offline',note='Router offline.snapshot: se utiliza solo al descargar con conexión.')
c.entity('central','Catálogo autorizado','agregado PostgreSQL')
c.entity('snapshot','Catálogo local y permiso','IndexedDB / SQLite')
c.entity('operacion','Operación local','operations / operation')
c.entity('detalle','Detalle de operación','details / detail')
TS,LD=F+'core/services/offline.service.ts',D+'features/offline/local_database.dart'
c.begin('Preparar dispositivo con conexión','download','sucursal',TS)
c.msg('control','backend','snapshot(sucursal)','invoke',B+'routers/offline.py','snapshot')
c.read('central','snapshot','sucursal','catálogo y autorización',B+'routers/offline.py',ctrl='backend')
c.msg('backend','control','snapshot autorizado','reply')
c.write('snapshot','saveSnapshot(datos)',LD,'saveSnapshot');c.end('catálogo guardado','Dispositivo preparado')
c.begin('Consultar catálogo sin conexión','refresh','',TS,'read')
c.read('snapshot','catalog','sucursal','catálogo y disponible local',LD);c.end('catálogo local','Mostrar copia descargada')
for kind,label in [('reserva','Registrar reserva offline'),('venta','Registrar venta de contado offline')]:
    c.begin(label,'capture',kind+', ítems',TS)
    c.write('operacion','Guardar UUID y estado PENDIENTE',LD,'capture')
    c.write('detalle','Guardar detalles [misma transacción]',LD,'capture')
    c.end(kind+' provisional','Mostrar operación pendiente')
c.begin('Reabrir y consultar pendientes','open','',TS,'read')
c.read('operacion','operations','','pendientes y estados guardados',LD)
c.read('detalle','details','UUID','detalles guardados',TS)
c.end('operaciones recuperadas','Mostrar operaciones tras reinicio')
c.notes=['El backend solo interviene en la descarga inicial con conexión. Consultar y registrar usan IndexedDB o SQLite. No se dibuja sincronización: corresponde a CU17.',
 'Catálogo local y permiso agrupa snapshot, productos, variantes y disponibilidad conocida. Operación y detalles se conservan separados y se guardan en la misma transacción.',
 'No existe una bitácora local separada: la operación conserva UUID, autor, fecha, estado e intentos. La auditoría central de sincronización se escribe posteriormente en CU17; no se inventa acceso a PostgreSQL durante una venta sin red.',
 'Las ventas requieren rol autorizado, efectivo suficiente y permiso offline vigente. Las reservas requieren cliente descargado. Son operaciones provisionales, no ventas confirmadas por el servidor.']


def symbol_line(file,symbol):
    source=(ROOT/file).read_text(encoding='utf-8-sig')
    if file.endswith('.py'):
        tree=ast.parse(source)
        matches=[n.lineno for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==symbol]
    else:
        pattern=re.compile(r'^\s*(?:[\w<>?,]+\s+)*'+re.escape(symbol)+r'\s*\(',re.M)
        matches=[source.count('\n',0,m.start())+1 for m in pattern.finditer(source)]
    assert matches,(file,symbol)
    return matches[0]


def layout(case):
    draw.NODES=case.nodes
    draw.ORDER={k:i for i,k in enumerate(case.nodes)}
    grouped=defaultdict(list)
    for message in case.messages:grouped[draw.pair_key(message)].append(message)
    right=[k for k,n in case.nodes.items() if (n['kind']=='entity' or (n['kind']=='boundary' and k!='b_pre'))]
    if case.id=='CU16':right=['snapshot','operacion','detalle']
    sizes={}
    for key in right:
        pair=next((p for p in grouped if key in p and 'control' in p),None)
        sizes[key]=draw.group_geometry(pair,grouped[pair],1050) if pair else dict(upper=44,lower=44,height=328)
    total=sum(max(355,g['height']) for g in sizes.values())
    height=max(2100,total+300)
    if case.id=='CU16':height=2400
    positions={'actor':dict(x=180,y=height/2),'b_pre':dict(x=1100,y=height/2),'control':dict(x=2400,y=height/2)}
    cursor=160
    for key in right:
        g=sizes[key];slot=max(355,g['height'])
        positions[key]=dict(x=4300,y=cursor+g['upper']+85)
        cursor+=slot
    if 'staff' in case.nodes:positions['staff']=dict(x=180,y=height-350)
    if case.id=='CU16':
        positions['backend']=dict(x=3300,y=290)
        positions['central']=dict(x=4300,y=290)
        positions['snapshot']=dict(x=4300,y=800)
        positions['operacion']=dict(x=4300,y=1370)
        positions['detalle']=dict(x=4300,y=1940)
    if case.id=='CU11':height+=300
    view=dict(name=case.id+' - Robustez simplificada',title=case.id+' - '+case.name+' - Diagrama de robustez',width=4600,height=int(height),nodes=positions,groups=[])
    for pair,messages in grouped.items():
        a,b=positions[pair[0]],positions[pair[1]]
        kinds=[case.nodes[k]['kind'] for k in pair]
        if pair==('actor','b_pre'):
            width,cx,y=600,650,positions['b_pre']['y'];points=[(a['x']+35,a['y']),(b['x']-65,b['y'])]
        elif pair==('staff','b_pre'):
            width,cx,y=600,650,a['y']-60;points=[(a['x']+35,a['y']),(340,y),(b['x']-65,b['y'])]
        elif pair==('b_pre','control'):
            width,cx,y=550,1650,a['y'];points=[(a['x']+65,a['y']),(b['x']-65,b['y'])]
        elif pair==('actor','b_stripe'):
            width,cx,y=800,1500,height-150;points=[(a['x']+35,a['y']),(340,y),(b['x'],y),(b['x'],b['y']+65)]
        elif pair==('control','backend'):
            width,cx,y=500,2800,290;points=[(a['x']+65,a['y']),(2700,y),(b['x']-65,b['y'])]
        elif pair==('backend','central'):
            width,cx,y=550,3800,290;points=[(a['x']+65,a['y']),(b['x']-65,b['y'])]
        else:
            width,cx=1050,3300
            other=pair[1] if pair[0]=='control' else pair[0]
            y=positions[other]['y']
            ctl=positions['control'];end=positions[other]
            points=[(ctl['x']+65,ctl['y']),(2720,y),(end['x']-65,end['y'])]
            if pair[0]!='control':points.reverse()
        g=draw.group_geometry(pair,messages,width)
        rows=[]
        yy=y-38-g['upper']
        for forward,items in [(True,g['calls']),(False,g['returns'])]:
            if not forward:yy=y+38
            for m in items:
                h=draw.message_height(m,width)
                rightward=positions[m['b']]['x']>positions[m['a']]['x']
                rows.append(dict(n=m['n'],x=cx,y=yy+h/2,width=width,height=h,forward=forward,rightward=rightward))
                yy+=h
        view['groups'].append(dict(pair=list(pair),points=points,rows=rows))
    return view


def generate(case):
    folder=OUT/(case.id+'_Simplificado');folder.mkdir(exist_ok=True)
    stem=case.id+'_Robustez_Simplificada'
    owners=defaultdict(set)
    for m in case.messages:
        assert not re.search(r'\b(GET|POST|PUT|PATCH|DELETE|HTTP)\b',m['text'])
        ka,kb=case.nodes[m['a']]['kind'],case.nodes[m['b']]['kind']
        if 'entity' in (ka,kb):
            assert {ka,kb}=={'entity','control'}
            e,ctl=(m['a'],m['b']) if ka=='entity' else (m['b'],m['a'])
            owners[e].add(ctl)
        if 'actor' in (ka,kb):assert {ka,kb}=={'actor','boundary'}
        assert (ka,kb)!=('boundary','boundary')
        if m['source']:m['line']=symbol_line(m['source'],m['symbol'])
    assert all(len(v)==1 for v in owners.values())
    assert set(owners)=={k for k,n in case.nodes.items() if n['kind']=='entity'}
    assert [m['n'] for m in case.messages]==list(range(1,len(case.messages)+1))
    for source in case.sources:assert (ROOT/source).is_file(),source
    view=layout(case)
    draw.NODES,draw.M,draw.A,draw.VIEWS=case.nodes,case.messages,case.actions,[view]
    native=draw.drawio()
    doc=etree.fromstring(native)
    etree.XMLSchema(etree.parse(str(ROOT/'tmp/drawio-validation/mxfile.xsd'))).assertValid(doc)
    ids=[c.get('id') for c in doc.iter('mxCell')]
    assert len(ids)==len(set(ids))
    for group in view['groups']:
        rows=sorted(group['rows'],key=lambda r:r['y'])
        assert all(a['y']+a['height']/2<=b['y']-b['height']/2 for a,b in zip(rows,rows[1:]))
        for row in rows:
            assert row['y']-row['height']/2>115,(case.id,row)
            assert row['y']+row['height']/2<view['height']-20,(case.id,row)
    files=set(case.sources)|{m['source'] for m in case.messages if m['source']}
    model=dict(case=case.id,title=case.id+' - '+case.name,nodes=case.nodes,messages=case.messages,actions=case.actions,views=[view],exports=['General'],notes=case.notes,
               sources=[dict(file=f,sha256=hashlib.sha256((ROOT/f).read_bytes()).hexdigest()) for f in sorted(files)])
    (folder/(stem+'.drawio')).write_bytes(native)
    (folder/(stem+'_General.svg')).write_text(draw.svg(view,0),encoding='utf-8')
    (folder/(stem+'_Modelo.json')).write_text(json.dumps(model,ensure_ascii=False,indent=2),encoding='utf-8')
    with (folder/('MENSAJES_'+case.id+'.csv')).open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.writer(f);writer.writerow(['numero','origen','destino','mensaje','archivo','linea'])
        for m in case.messages:writer.writerow([m['n'],m['a'],m['b'],m['text'],m['source'],m.get('line','')])
    report=dict(caso=case.id,mensajes=len(case.messages),acciones=len(case.actions),entidades=len(owners),interfaces=sum(n['kind']=='boundary' for n in case.nodes.values()),controles=sum(n['kind']=='control' for n in case.nodes.values()),paginas=1,xsd_valido=True,numeracion_consecutiva=True,entidades_solo_con_un_control=True,actores_solo_con_interfaces=True,sin_interfaces_interconectadas=True,sin_etiquetas_HTTP=True,simbolos_en_fuentes_comprobados=True,filas_sin_solapamiento=True)
    (folder/(stem+'_Validacion.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    notes='\n'.join('- '+n for n in case.notes)
    (folder/'LEEME.md').write_text('# '+model['title']+'\n\nVista simplificada de una página con '+str(len(case.messages))+' mensajes numerados. La cantidad de interfaces, controles y entidades responde al flujo de este CU. Las tablas auxiliares y validaciones quedan resumidas dentro del control.\n\n'+notes+'\n\nEl archivo .drawio es editable; el PNG sirve para Word y el SVG conserva calidad vectorial. El JScript crea un paquete nuevo en Enterprise Architect al ejecutarlo con un paquete seleccionado. Su sintaxis y generación se validan en simulación, no en una sesión real de EA.\n\nLos archivos Modelo.json y MENSAJES.csv conservan las referencias de los métodos al código. Los controles y las interfaces agrupadas son abstracciones de análisis, no clases ni pantallas nuevas. No se modificó el código funcional ni el documento Word.\n',encoding='utf-8')
    return dict(**report,folder=folder.relative_to(ROOT).as_posix(),stem=stem)


if __name__=='__main__':
    results=[]
    for case in CASES:
        result=generate(case);results.append(result);print(case.id+': '+str(result['mensajes'])+' mensajes, '+str(result['entidades'])+' entidades, validación aprobada')
    (OUT/'MANIFIESTO_CU07_CU16_SIMPLIFICADOS.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
