"""Modelo conceptual general basado en las veinte fichas actuales; no modifica fuentes ni Word."""
from pathlib import Path
import hashlib
import json

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/modelo_dominio'

NODES=[]
EDGES=[]

def c(key,name,group,*attributes):
    NODES.append(dict(id=key,nombre=name,grupo=group,atributos=list(attributes)))

def r(a,b,ma,mb,label,composition=False,primary=True):
    EDGES.append(dict(id=f'r{len(EDGES)+1:03d}',origen=a,destino=b,multiplicidad_origen=ma,
                      multiplicidad_destino=mb,nombre=label,composicion=composition,ordenar=primary))

# Nombres y atributos del negocio, sin tipos SQL, identificadores de tablas ni operaciones de software.
c('empresa','Empresa','organizacion','nombre','identificador público','estado')
c('plan','Plan','organizacion','nombre','límite de sucursales','reportes generativos habilitados')
c('suscripcion','Suscripción','organizacion','fecha de inicio','fecha de vencimiento','estado')
c('ciudad','Ciudad','organizacion','nombre')
c('sucursal','Sucursal','organizacion','nombre','dirección','estado')
c('caja','Caja','organizacion','denominación','estado')
c('cuenta','Cuenta global','identidad','correo','nombre','tipo de cuenta','estado')
c('perfil','Perfil empresarial','identidad','fecha de vinculación','estado')
c('rol','Rol','identidad','nombre','descripción')
c('permiso','Permiso','identidad','recurso','acción autorizada')
c('sesion','Sesión','identidad','inicio','vencimiento','estado')
c('recuperacion','Solicitud de recuperación','identidad','fecha de solicitud','vencimiento','utilizada')
c('cliente','Ficha de cliente','identidad','identificación','nombre completo','teléfono','dirección de entrega')

c('categoria','Categoría','catalogo','nombre','descripción')
c('temporada','Temporada','catalogo','nombre','inicio','fin')
c('coleccion','Colección','catalogo','nombre','descripción')
c('prenda','Prenda','catalogo','SKU','nombre','material y medidas','precio minorista','precio mayorista','umbral mayorista','estado')
c('variante','Variante de prenda','catalogo','SKU de variante','estado')
c('talla','Talla','catalogo','denominación')
c('color','Color','catalogo','nombre','código de color')
c('oferta','Oferta','catalogo','precio promocional','inicio','fin')
c('recomendacion','Recomendación de prenda','asistencia','fecha','criterio','puntuación')
c('prueba','Prueba virtual','asistencia','fecha','modalidad','estado')

c('inventario','Inventario','inventario','existencia física','/cantidad retenida','/cantidad disponible','fecha de actualización')
c('movimiento','Movimiento de inventario','inventario','tipo','cantidad','fecha','motivo')
c('transferencia','Transferencia de inventario','inventario','fecha','motivo','estado')
c('retencion','Retención de inventario','inventario','cantidad','vencimiento','estado')

c('proveedor','Proveedor','abastecimiento','NIT','razón social','contacto','estado')
c('compra','Compra de abastecimiento','abastecimiento','fecha','estado','importe total')
c('detalle_compra','Detalle de compra','abastecimiento','cantidad','costo unitario','subtotal')
c('recepcion_compra','Recepción de compra','abastecimiento','fecha de recepción','estado')

c('carrito','Carrito','compra_digital','fecha de creación','estado')
c('item_carrito','Ítem de carrito','compra_digital','cantidad','precio conocido')
c('pedido','Pedido de compra','compra_digital','fecha','estado','modalidad de entrega','importe calculado')
c('detalle_pedido','Detalle de pedido','compra_digital','cantidad','precio acordado','subtotal')
c('pago','Pago','pagos','fecha','medio','importe','estado','referencia del proveedor')
c('venta','Venta','ventas','fecha','canal','importe total','efectivo recibido','vuelto')
c('detalle_venta','Detalle de venta','ventas','cantidad','precio efectivamente pagado','subtotal')
c('comprobante','Comprobante','ventas','número','fecha de emisión','importe')
c('entrega','Entrega de compra','ventas','fecha','modalidad','estado')
c('reserva','Reserva','reservas','fecha','vencimiento','estado','importe conocido')
c('detalle_reserva','Detalle de reserva','reservas','cantidad','precio conocido')

c('solicitud_cambio','Solicitud de cambio','cambios','fecha','motivo','estado')
c('detalle_cambio','Detalle de cambio','cambios','cantidad solicitada','crédito reconocido','diferencia de precio','estado')
c('recepcion_prenda','Recepción de prenda','cambios','fecha','condición observada','aceptada')
c('entrega_reemplazo','Entrega de reemplazo','cambios','fecha','estado')
c('reembolso','Reembolso','pagos','fecha','importe','motivo','estado')

c('dispositivo','Dispositivo','offline','denominación','tipo de aplicación')
c('contexto_offline','Habilitación offline','offline','inicio','vencimiento','estado')
c('catalogo_local','Catálogo descargado','offline','versión','fecha de descarga')
c('item_local','Dato de variante descargada','offline','precio conocido','existencia conocida','fecha de actualización')
c('operacion_local','Operación local','sincronizacion','UUID','tipo','fecha','estado','total provisional','efectivo recibido')
c('detalle_local','Detalle de operación local','sincronizacion','cantidad','precio conocido','subtotal')
c('lote','Lote de sincronización','sincronizacion','fecha de envío','estado')
c('intento','Intento de sincronización','sincronizacion','fecha','número de intento','resultado de comunicación')
c('resultado','Resultado de sincronización','sincronizacion','fecha','estado','motivo')
c('conflicto','Conflicto','sincronizacion','tipo','motivo','estado')
c('resolucion','Resolución de conflicto','sincronizacion','fecha','decisión','compensación registrada')

c('solicitud_reporte','Solicitud de reporte','reportes','fecha','modalidad','solicitud del usuario','tipo de reporte')
c('filtro','Filtro de reporte','reportes','criterio','valor solicitado')
c('reporte','Reporte comercial','reportes','tipo','fecha de generación','fecha de corte','representación')
c('exportacion','Exportación de reporte','reportes','formato','fecha','estado')
c('datos','Conjunto de datos','analitica','procedencia','fecha de preparación','semilla de generación','variables utilizadas')
c('entrenamiento','Entrenamiento','analitica','fecha','configuración','estado')
c('modelo','Modelo analítico','analitica','nombre','tipo de aprendizaje','versión','estado')
c('evaluacion','Evaluación de modelo','analitica','métrica','valor','partición evaluada','fecha')
c('prediccion','Predicción de demanda','analitica','período','horizonte','valor estimado','fecha de cálculo')
c('segmento','Segmento de clientes','analitica','nombre','características','fecha de cálculo')
c('indicador','Indicador comercial','analitica','nombre','período','valor','fecha de cálculo')
c('notificacion','Notificación','trazabilidad','fecha','asunto','canal','estado de lectura')
c('evento','Evento de auditoría','trazabilidad','fecha','acción','resultado','referencia de operación')

r('empresa','suscripcion','1','0..*','contrata')
r('plan','suscripcion','1','0..*','establece condiciones')
r('empresa','sucursal','1','0..*','dispone de')
r('ciudad','sucursal','1','0..*','ubica')
r('sucursal','caja','1','0..*','habilita')
r('cuenta','perfil','1','0..*','mantiene')
r('empresa','perfil','1','0..*','vincula personal y clientes',primary=False)
r('empresa','rol','1','0..*','define roles',primary=False)
r('rol','perfil','1','0..*','determina facultades')
r('rol','permiso','0..*','0..*','autoriza')
r('perfil','sucursal','0..*','0..*','tiene acceso asignado',primary=False)
r('cuenta','sesion','1','0..*','inicia')
r('perfil','sesion','0..1','0..*','delimita contexto',primary=False)
r('cuenta','recuperacion','1','0..*','solicita')
r('empresa','cliente','1','0..*','mantiene ficha comercial',primary=False)
r('cuenta','cliente','0..1','0..*','identifica al titular')

r('empresa','categoria','1','0..*','organiza categorías',primary=False)
r('empresa','temporada','1','0..*','define temporadas',primary=False)
r('empresa','coleccion','1','0..*','organiza colecciones',primary=False)
r('empresa','prenda','1','0..*','comercializa',primary=False)
r('categoria','prenda','1','0..*','clasifica')
r('categoria','categoria','0..1','0..*','agrupa subcategorías',primary=False)
r('temporada','coleccion','0..1','0..*','enmarca')
r('temporada','prenda','0..1','0..*','sitúa comercialmente',primary=False)
r('coleccion','prenda','0..1','0..*','agrupa')
r('prenda','variante','1','0..*','se ofrece como')
r('talla','variante','1','0..*','define talla')
r('color','variante','1..*','0..*','integra colores')
r('prenda','oferta','1','0..1','tiene oferta configurada')
r('prenda','recomendacion','1','0..*','es sugerida mediante',primary=False)
r('cliente','recomendacion','0..1','0..*','personaliza',primary=False)
r('prenda','prueba','1','0..*','se visualiza en',primary=False)
r('cuenta','prueba','0..1','0..*','realiza',primary=False)

r('sucursal','inventario','1','0..*','mantiene existencias',primary=False)
r('variante','inventario','1','0..*','tiene existencias')
r('inventario','movimiento','1','0..*','registra variaciones')
r('perfil','movimiento','0..1','0..*','responsabiliza',primary=False)
r('sucursal','transferencia','1','0..*','es origen de',primary=False)
r('sucursal','transferencia','1','0..*','es destino de',primary=False)
r('transferencia','movimiento','0..1','2..*','se concreta mediante')
r('inventario','retencion','1','0..*','reserva disponibilidad')

r('empresa','proveedor','1','0..*','registra proveedores',primary=False)
r('proveedor','compra','1','0..*','abastece')
r('sucursal','compra','1','0..*','recibe abastecimiento',primary=False)
r('compra','detalle_compra','1','1..*','contiene',composition=True)
r('variante','detalle_compra','1','0..*','se adquiere en',primary=False)
r('compra','recepcion_compra','1','0..1','se recibe mediante')
r('recepcion_compra','movimiento','0..1','1..*','origina entradas',primary=False)

r('empresa','carrito','1','0..*','delimita tienda',primary=False)
r('cuenta','carrito','0..1','0..*','mantiene carrito',primary=False)
r('carrito','item_carrito','1','0..*','contiene',composition=True)
r('variante','item_carrito','1','0..*','se selecciona en',primary=False)
r('carrito','pedido','1','0..*','origina intentos de compra')
r('cliente','pedido','1','0..*','solicita compra',primary=False)
r('sucursal','pedido','1','0..*','atiende pedido',primary=False)
r('pedido','detalle_pedido','1','1..*','contiene',composition=True)
r('variante','detalle_pedido','1','0..*','se solicita en',primary=False)
r('pedido','pago','0..1','0..*','origina pagos')
r('pedido','venta','0..1','0..1','se confirma como',primary=False)
r('sucursal','venta','1','0..*','registra venta',primary=False)
r('caja','venta','0..1','0..*','procesa venta presencial',primary=False)
r('cliente','venta','0..1','0..*','realiza compra',primary=False)
r('perfil','venta','0..1','0..*','atiende venta',primary=False)
r('venta','detalle_venta','1','1..*','contiene',composition=True)
r('variante','detalle_venta','1','0..*','se vende en',primary=False)
r('venta','pago','0..1','1..*','recibe cobros')
r('venta','comprobante','1','0..1','documenta')
r('venta','entrega','1','0..1','se entrega mediante')
r('detalle_venta','movimiento','0..1','1..*','origina salidas',primary=False)

r('cliente','reserva','1','0..*','solicita reserva',primary=False)
r('sucursal','reserva','1','0..*','atiende reserva',primary=False)
r('reserva','detalle_reserva','1','1..*','contiene',composition=True)
r('variante','detalle_reserva','1','0..*','se aparta en',primary=False)
r('detalle_reserva','retencion','1','0..1','genera retención')
r('reserva','venta','0..1','0..1','se convierte en',primary=False)

r('venta','solicitud_cambio','1','0..*','da origen a')
r('cliente','solicitud_cambio','1','0..*','solicita cambio',primary=False)
r('solicitud_cambio','detalle_cambio','1','1..*','contiene',composition=True)
r('detalle_venta','detalle_cambio','1','0..*','acredita unidad adquirida',primary=False)
r('variante','detalle_cambio','0..1','0..*','es reemplazo seleccionado',primary=False)
r('detalle_cambio','recepcion_prenda','1','0..1','se inspecciona mediante')
r('recepcion_prenda','movimiento','0..1','0..1','puede reponer existencias',primary=False)
r('solicitud_cambio','entrega_reemplazo','1','0..1','finaliza mediante')
r('entrega_reemplazo','movimiento','0..1','1..*','origina salida de reemplazos',primary=False)
r('solicitud_cambio','pago','0..1','0..*','cobra diferencias',primary=False)
r('solicitud_cambio','reembolso','0..1','0..*','devuelve crédito',primary=False)
r('pago','reembolso','1','0..*','es medio original de')

r('perfil','contexto_offline','1','0..*','habilita operación local',primary=False)
r('dispositivo','contexto_offline','1','0..*','conserva contexto')
r('contexto_offline','catalogo_local','1','0..*','dispone de copias')
r('sucursal','catalogo_local','1','0..*','sitúa disponibilidad conocida',primary=False)
r('catalogo_local','item_local','1','0..*','contiene',composition=True)
r('variante','item_local','1','0..*','es conocida mediante',primary=False)
r('contexto_offline','operacion_local','1','0..*','registra pendientes')
r('sucursal','operacion_local','1','0..*','recibe operación provisional',primary=False)
r('cliente','operacion_local','0..1','0..*','figura en operación',primary=False)
r('operacion_local','detalle_local','1','1..*','contiene',composition=True)
r('variante','detalle_local','1','0..*','se registra localmente en',primary=False)
r('operacion_local','intento','1','0..*','se envía mediante')
r('lote','intento','1','1..*','agrupa envíos')
r('operacion_local','resultado','1','0..1','obtiene resultado central')
r('intento','resultado','0..*','0..1','recupera resultado',primary=False)
r('resultado','venta','0..1','0..1','confirma venta',primary=False)
r('resultado','reserva','0..1','0..1','confirma reserva',primary=False)
r('resultado','conflicto','1','0..1','puede identificar')
r('conflicto','resolucion','1','0..1','se resuelve mediante')
r('perfil','resolucion','1','0..*','decide con autorización',primary=False)
r('operacion_local','operacion_local','0..1','0..*','es revisada por',primary=False)
r('resolucion','operacion_local','0..1','0..1','puede originar corrección',primary=False)

r('empresa','solicitud_reporte','1','0..*','delimita información',primary=False)
r('perfil','solicitud_reporte','1','0..*','solicita reporte',primary=False)
r('solicitud_reporte','filtro','1','0..*','establece filtros',composition=True)
r('solicitud_reporte','reporte','1','0..1','produce')
r('reporte','exportacion','1','0..*','se exporta mediante')
r('datos','entrenamiento','1','0..*','alimenta')
r('entrenamiento','modelo','1','0..1','produce versión')
r('entrenamiento','evaluacion','1','0..*','se valida mediante')
r('modelo','prediccion','1','0..*','estima demanda')
r('modelo','segmento','1','0..*','identifica segmentos')
r('prenda','prediccion','1','0..*','es objetivo de estimación',primary=False)
r('sucursal','prediccion','1','0..*','sitúa demanda',primary=False)
r('empresa','segmento','1','0..*','delimita segmentación',primary=False)
r('segmento','cliente','0..1','0..*','clasifica clientes',primary=False)
r('empresa','indicador','1','0..*','resume actividad',primary=False)
r('sucursal','indicador','0..1','0..*','delimita indicador',primary=False)

r('cuenta','notificacion','1','0..*','recibe avisos',primary=False)
r('empresa','notificacion','1','0..*','emite aviso comercial',primary=False)
r('solicitud_cambio','notificacion','0..1','0..*','origina aviso',primary=False)
r('cuenta','evento','0..1','0..*','actúa en',primary=False)
r('empresa','evento','0..1','0..*','delimita ámbito de auditoría',primary=False)
r('operacion_local','evento','0..1','0..*','correlaciona trazabilidad',primary=False)

COVERAGE={
 'CU01':['cuenta','perfil','sesion','recuperacion'],
 'CU02':['empresa','plan','suscripcion'],
 'CU03':['cuenta','perfil','rol','permiso'],
 'CU04':['ciudad','sucursal','caja'],
 'CU05':['cuenta','cliente'],
 'CU06':['categoria','temporada','coleccion','prenda','variante','talla','color','oferta'],
 'CU07':['proveedor','compra','detalle_compra','recepcion_compra'],
 'CU08':['inventario','retencion','variante'],
 'CU09':['prenda','variante','recomendacion','prueba'],
 'CU10':['inventario','movimiento','transferencia'],
 'CU11':['carrito','item_carrito','pedido','detalle_pedido','pago','venta'],
 'CU12':['reserva','detalle_reserva','retencion','venta'],
 'CU13':['caja','venta','detalle_venta','pago','movimiento'],
 'CU14':['venta','comprobante'],
 'CU15':['solicitud_cambio','detalle_cambio','recepcion_prenda','entrega_reemplazo','reembolso','notificacion'],
 'CU16':['dispositivo','contexto_offline','catalogo_local','item_local','operacion_local','detalle_local'],
 'CU17':['lote','intento','resultado','conflicto','resolucion','operacion_local'],
 'CU18':['solicitud_reporte','filtro','reporte','exportacion'],
 'CU19':['datos','entrenamiento','modelo','evaluacion','prediccion','segmento','indicador'],
 'CU20':['evento','cuenta','empresa'],
}

DESCRIPTION='''## 3.1. Modelo de dominio

El modelo de dominio de FashionStore representa los conceptos necesarios para comprender la operación de la plataforma y las relaciones que existen entre ellos. Su alcance integra la prestación del servicio SaaS, la identidad de los usuarios, la organización de las empresas, el catálogo, el abastecimiento, los inventarios y las operaciones comerciales, junto con el funcionamiento offline, la sincronización, los reportes y la analítica inteligente.

Se presenta una vista general compartida por los veinte casos de uso. Los conceptos conservan un significado común aunque intervengan en diferentes procesos; por ejemplo, una venta puede originarse en la caja o en una compra digital y posteriormente relacionarse con pagos, comprobantes, entregas y solicitudes de cambio.

La representación utiliza clases conceptuales con atributos relevantes, asociaciones y multiplicidades. Las relaciones de composición identifican detalles que pertenecen a un único documento o registro principal. Los conceptos no equivalen necesariamente a tablas de PostgreSQL: algunos representan información temporal, copias locales o resultados analíticos. No se incluyen métodos, controladores, endpoints ni claves foráneas, ya que corresponden a los modelos técnicos posteriores.
'''

RELATION_TEXT='''### Relaciones y restricciones principales

**Organización del servicio.** Una empresa puede disponer de varias sucursales y de un historial de suscripciones. Cada suscripción corresponde a una empresa y a un plan; sus fechas determinan su vigencia. Como política operativa, debe existir como máximo una suscripción efectiva para un mismo instante. El límite de sucursales activas se comprueba al dar de alta, reactivar o cambiar de plan. Una caja pertenece a una sucursal.

**Identidad y pertenencia empresarial.** La cuenta global identifica a la persona mediante un correo único y puede mantener perfiles en distintos contextos empresariales. Cada perfil pertenece a una sola empresa, tiene un rol y accede únicamente a las sucursales asignadas. Los roles reúnen permisos. El personal permanece en su empresa asignada; los clientes pueden utilizar su cuenta en diferentes tiendas. El superadministrador actúa mediante su condición de plataforma y no necesita una vinculación comercial con cada empresa.

**Ficha comercial del cliente.** Cada ficha pertenece a una empresa y puede vincularse a una cuenta global. La vinculación es opcional para permitir clientes registrados por el personal o ventas de mostrador. Una cuenta puede tener fichas en varias empresas; no se duplicará su ficha para la misma empresa. El historial propio entre tiendas se obtiene relacionando sus fichas, sin dar a una tienda acceso a operaciones de las demás.

**Organización del catálogo.** Las categorías clasifican prendas y pueden organizar subcategorías sin ciclos. Temporadas y colecciones expresan agrupaciones comerciales; su participación es opcional cuando la prenda todavía no pertenece a una de ellas. Una prenda puede disponer de variantes, cada una con una talla y uno o varios colores. Para publicar una prenda comercializable debe existir al menos una variante activa. Los SKU se interpretan dentro de la empresa. La oferta configurada y los precios minorista y mayorista se evalúan según sus condiciones de vigencia y cantidad.

**Existencias y movimientos.** Cada registro de inventario corresponde a una combinación única de sucursal y variante. La disponibilidad es un valor derivado de la existencia física y las retenciones vigentes. Los movimientos registran cambios de existencias y pueden estar relacionados con abastecimiento, ventas, transferencias o cambios de prendas. Una transferencia vincula una sucursal de origen y otra de destino de la misma empresa, y se concreta mediante movimientos correlacionados de salida y entrada. No se descuenta stock por un mecanismo adicional al registro de movimientos.

**Abastecimiento.** La compra relaciona un proveedor, una sucursal y uno o varios detalles de variantes adquiridas. La recepción identifica la confirmación física de esa compra y origina los movimientos de entrada. La recepción y sus efectos deben confirmarse conjuntamente; repetir la confirmación o consultar el documento no genera nuevas entradas. El modelo contempla una recepción por compra, conforme al flujo actual, sin introducir entregas parciales adicionales.

**Carrito, pedido y venta.** El carrito reúne ítems seleccionados y puede originar intentos de pedido. El pedido conserva la solicitud de compra y los intentos de pago antes de que exista una venta confirmada. Un pedido puede finalizar sin venta si el pago falla, expira o es abandonado. La venta confirmada contiene uno o varios detalles, se atiende en una sucursal y registra sus cobros y movimientos. La caja interviene en la venta presencial; su asociación es opcional en el modelo general porque una compra digital no utiliza necesariamente una caja física.

**Reservas y retenciones.** La reserva identifica cliente, sucursal y prendas solicitadas. Sus detalles pueden originar retenciones de inventario cuando la reserva central es aceptada. La retención reduce disponibilidad, sin representar una salida física. La preparación, el pago, la entrega y la cancelación son condiciones diferenciadas del proceso. Una reserva puede dar origen a una venta, mientras su cancelación o vencimiento libera la retención sin crear una venta ficticia.

**Pagos, comprobantes y entregas.** Un pago puede existir antes de vincularse con una venta confirmada. Puede corresponder al pedido o al cobro de una diferencia de cambio; un pago de caja no requiere un pedido digital. La venta conserva los cobros que la acreditan. Un comprobante pertenece a una sola venta y se genera sin duplicar su registro comercial. Su participación es opcional mientras se prepara o recupera la representación del documento. La entrega identifica el cumplimiento físico de una compra y proporciona la fecha para evaluar el plazo de cambios.

**Cambios y reembolsos.** La solicitud de cambio se vincula con una venta y contiene detalles que identifican las unidades adquiridas afectadas. Cada detalle puede incorporar un reemplazo cuando esté disponible. La recepción de la prenda y la entrega del reemplazo son conceptos separados: recibir una devolución no implica que el reemplazo ya fue entregado. La reposición de stock requiere una recepción aceptada. El crédito se calcula con el precio efectivamente pagado; las diferencias se cobran o se devuelven mediante pagos y reembolsos identificables. Una solicitud puede quedar pendiente o cancelarse. Cada reembolso referencia el pago original.

**Operación offline.** La habilitación offline vincula un perfil empresarial y un dispositivo, y determina el período en el que se permite operar localmente. El catálogo descargado conserva información conocida de una sucursal y sus variantes; sus existencias no representan una consulta central actualizada. La operación local identifica su contexto, sucursal, UUID, detalles y, cuando corresponda, cliente. El registro es provisional y no equivale todavía a una venta o reserva central. Las colas se conservan separadas por cuenta, empresa y dispositivo.

**Sincronización y conflictos.** Cada operación puede participar en varios intentos agrupados en lotes, manteniendo UUID y contenido. Su resultado central se conserva y puede recuperarse en reintentos. Un resultado aceptado se vincula con una venta o una reserva, según el tipo de operación; no con ambas. Un resultado rechazado o en conflicto no crea esos documentos como si estuvieran confirmados. Un conflicto puede tener una resolución autorizada, con compensación o una nueva operación de corrección enlazada a la original. La operación original y sus detalles no se sobrescriben silenciosamente.

**Reportes y analítica.** Una solicitud de reporte se formula en el contexto de una empresa y puede contener filtros. Su resultado puede representarse y exportarse en diferentes formatos conservando los datos autorizados. La preparación y el entrenamiento de modelos se relacionan con conjuntos de datos y evaluaciones; el modelo resultante se identifica por su versión y tipo de aprendizaje. Sus predicciones se refieren a prendas y sucursales, mientras la segmentación relaciona fichas de clientes de una misma empresa. Un cliente puede permanecer sin clasificar; el segmento mostrado corresponde a su clasificación actual. El entrenamiento no se ejecuta al abrir el dashboard y los datos sintéticos no sustituyen los datos reales de los reportes comerciales.

**Notificaciones y auditoría.** Las notificaciones comerciales identifican empresa y destinatario, conservando su estado de lectura aunque falle el transporte del aviso. Los eventos de auditoría relacionan acción, resultado y referencia de operación. La cuenta o empresa pueden estar ausentes en un evento global, automático o de intento de acceso desconocido. Esta opcionalidad no autoriza consultar información empresarial ajena.

**Restricciones transversales.** Las asociaciones entre perfiles, roles, sucursales, prendas, fichas y documentos deben conservar coherencia empresarial. Las multiplicidades describen cantidades de relaciones; no sustituyen la validación de permisos, los estados ni las reglas temporales. Se mantienen las políticas del proyecto: reserva central por 24 horas; habilitación offline de hasta 24 horas, limitada por la suscripción; cambios hasta siete días calendario desde la entrega, con prenda elegible sin uso y un cambio por unidad; reembolsos por el medio original, con objetivo administrativo de cinco días hábiles. El pago y los movimientos deben ser idempotentes, y no se confirma una salida que produzca stock negativo.
'''

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    keys=[x['id'] for x in NODES];assert len(keys)==len(set(keys))
    assert set(COVERAGE)=={f'CU{i:02d}' for i in range(1,21)}
    assert all(e['origen'] in keys and e['destino'] in keys for e in EDGES)
    assert all(v in keys for values in COVERAGE.values() for v in values)
    document=ROOT/'docs/DOCUMENTACION PARCIAL 2/SEGUNDO_EXAMEN_PARCIAL-FASHIONSTORE.docx'
    specification=ROOT/'docs/DOCUMENTACION PARCIAL 2/2.6_ESPECIFICACION_CASOS_DE_USO.md'
    model={'tipo':'modelo conceptual de dominio','vista':'general única','clases':NODES,'relaciones':EDGES,
           'cobertura_casos':COVERAGE,'fuentes':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (document,specification)}}
    (OUT/'modelo_dominio.json').write_text(json.dumps(model,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (OUT/'3.1_MODELO_DE_DOMINIO_TEXTO.md').write_text(DESCRIPTION+'\n'+RELATION_TEXT,encoding='utf-8')
    print(f'Modelo conceptual preparado: {len(NODES)} clases, {len(EDGES)} relaciones y cobertura de 20 CU.')

if __name__=='__main__':main()
