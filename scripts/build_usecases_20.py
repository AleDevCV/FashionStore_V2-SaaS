"""Modelo documental de 20 CU. Genera draw.io nativo, SVG y trazabilidad sin tocar código comercial."""
from pathlib import Path
import csv
import json
import math
import textwrap
import xml.etree.ElementTree as ET
from html import escape

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/modelo_20_cu'

# Los IDs anteriores designan el inventario de 38 CU, no los CU del P1.
CASES = [
 (1,'Gestionar acceso y cuenta',[1,2],['usuario'],
  'Registrar clientes globales, iniciar y cerrar sesión, recuperar contraseña y elegir tienda después del acceso del cliente. El personal mantiene su empresa asignada.',
  ['Solicitar acceso o registro con correo y contraseña','Validar identidad y obtener del servidor rol y ámbito','Abrir el espacio de plataforma, empresa o tiendas del cliente','Recuperar acceso mediante enlace de un solo uso cuando se solicite','Cerrar y revocar sesión conservando pendientes locales']),
 (2,'Administrar empresas, planes y suscripciones',[3,4,5],['super','admin'],
  'Aprovisionar empresas y su administrador, configurar planes y administrar vigencias, renovaciones y cambios. El administrador empresarial consulta únicamente su contrato.',
  ['Validar facultades de plataforma o consulta de contrato propio','Registrar empresa y administrador inicial cuando corresponda','Configurar capacidades y límites del plan','Asignar, renovar o cambiar suscripción validando cupos','Consultar el estado efectivo del servicio y auditar cambios']),
 (3,'Administrar personal, roles y permisos',[6,7],['admin'],
  'Mantener empleados, roles, permisos y asignaciones de sucursal de la empresa. Impedir privilegios de plataforma y cambios en la identidad global de clientes.',
  ['Consultar personal y roles de la empresa','Crear o actualizar empleado con correo global único','Asignar rol y sucursales permitidos','Activar, suspender o revocar autorizaciones','Comprobar que los permisos efectivos correspondan a la asignación']),
 (4,'Gestionar ciudades y sucursales',[8],['admin'],
  'Mantener ciudades y sucursales, su estado y responsables, respetando el cupo de sucursales activas de la suscripción.',
  ['Consultar ciudades y sucursales propias','Registrar o modificar dirección y responsables','Validar pertenencia y límite del plan','Guardar alta, actualización o reactivación','Mostrar la estructura operativa actualizada']),
 (5,'Gestionar fichas de clientes',[9],['admin','encargado','cajero','cliente'],
  'Crear y mantener fichas comerciales por empresa. El cliente consulta su propia información e historial entre tiendas; la tienda accede solo al perfil y operaciones de su ámbito.',
  ['Buscar ficha comercial autorizada','Crear o actualizar datos de contacto permitidos','Evitar duplicaciones dentro de la empresa','Consultar las operaciones del cliente según propiedad y rol','Conservar separada la identidad global y el historial comercial de cada tienda']),
 (6,'Administrar catálogo de prendas',[10,11,12],['admin','inventario'],
  'Mantener categorías, temporadas, colecciones, prendas, tallas, combinaciones de colores, material, medidas, precios y ofertas.',
  ['Organizar categorías y temporadas','Registrar o actualizar prenda y sus atributos','Definir variantes y combinaciones de colores','Configurar precios, umbral mayorista y ofertas vigentes','Publicar o desactivar elementos conservando relaciones comerciales']),
 (7,'Gestionar proveedores, compras y recepciones',[13,14],['admin','inventario'],
  'Administrar proveedores y compras; confirmar recepciones físicas con sus detalles y entradas de inventario. Mantener separados los subflujos de proveedor, pedido y recepción.',
  ['Mantener ficha del proveedor propio','Preparar compra con variantes, cantidades y costos','Seleccionar sucursal de recepción autorizada','Confirmar recepción y sus entradas de stock en una transacción','Consultar el documento y sus detalles sin duplicar recepciones']),
 (8,'Consultar inventario y disponibilidad',[15],['personal'],
  'Obtener existencias físicas, unidades retenidas y disponibilidad por sucursal y variante. El mismo comportamiento de consulta se reutiliza al confirmar una venta.',
  ['Determinar empresa, sucursal y variantes autorizadas','Consultar existencias físicas','Obtener retenciones centrales vigentes','Calcular disponibilidad para las variantes solicitadas','Devolver cantidades y fecha de información; si es copia local identificar su antigüedad']),
 (9,'Explorar catálogo y asistencia de compra',[17,26,27],['visitante','cliente','personal','ia'],
  'Consultar catálogo y filtros, variantes y disponibilidad; utilizar opcionalmente el vestidor existente y las recomendaciones sobre prendas de la tienda elegida.',
  ['Elegir tienda pública o usar el contexto empresarial autorizado','Buscar prendas mediante filtros','Consultar variantes y precios aplicables','Solicitar vestidor o recomendaciones si el usuario lo desea','Seleccionar prendas para una compra o reserva independiente']),
 (10,'Registrar movimientos de inventario',[16],['admin','inventario','encargado'],
  'Registrar entradas, salidas, ajustes y transferencias autorizadas. Reutilizar el registro de salida en ventas confirmadas sin descontar stock por un segundo mecanismo.',
  ['Identificar sucursales, variantes y motivo del movimiento','Validar cantidades, pertenencia y autorización','Bloquear o controlar las existencias afectadas','Registrar el movimiento y su efecto único sobre stock','Confirmar trazabilidad; revertir todo ante un fallo']),
 (11,'Realizar compra y pago en línea',[18,22],['cliente','pasarela'],
  'Administrar carrito y checkout hasta la confirmación de una compra pagada. La pasarela informa el resultado firmado; un pedido o pago pendiente no confirma una venta.',
  ['Preparar carrito, sucursal y forma de entrega','Recalcular precios y consultar disponibilidad mediante CU-08','Iniciar pago electrónico y mantener estado pendiente','Validar confirmación firmada, importe e identidad de operación','Confirmar venta y salida de inventario mediante CU-10 una sola vez']),
 (12,'Gestionar reservas de prendas',[19,20],['cliente','encargado','cajero','admin'],
  'Registrar y consultar reservas centrales, preparar prendas, cancelar, vencer y entregar según sus transiciones. El cliente opera solo sobre sus reservas.',
  ['Solicitar reserva con cliente, sucursal y detalles','Comprobar disponibilidad y establecer retención central','Consultar o preparar prendas según permisos','Confirmar pago cuando corresponda antes de entregar','Entregar o cancelar; liberar retenciones al vencer sin crear una venta ficticia']),
 (13,'Registrar venta presencial',[21],['cajero','encargado','admin'],
  'Consolidar una venta presencial autorizada con importes calculados por el servidor, efectivo y vuelto, registro comercial, salida única de stock y auditoría.',
  ['Seleccionar sucursal y productos del ticket','Consultar inventario mediante CU-08 y validar disponibilidad','Calcular precios y registrar efectivo recibido','Confirmar venta y registrar salidas mediante CU-10 en una transacción','Presentar resultado; ofrecer consulta o descarga de comprobante como acción adicional']),
 (14,'Obtener comprobantes de compra',[23],['cliente','cajero','encargado','admin'],
  'Emitir o recuperar la representación del comprobante de una venta confirmada, consultarla y descargarla con autorización. La consulta/descarga es opcional respecto al cierre de compra.',
  ['Solicitar comprobante de una venta confirmada','Verificar empresa, rol y propiedad de la compra','Recuperar documento existente o generar su representación autorizada','Presentar datos de venta y verificación','Descargar PDF sin duplicar el documento comercial']),
 (15,'Gestionar cambios y reembolsos',[24,25],['cliente','encargado','admin','pasarela','notificaciones'],
  'Solicitar, consultar y atender cambios: elegibilidad, recepción física, reemplazo, diferencias de precio, devolución de importes, notificaciones y entrega.',
  ['Registrar solicitud vinculada a unidades de una compra comprobable','Validar plazo, estado y elegibilidad de las prendas','Aceptar recepción física y determinar reposición de stock','Asignar reemplazo y cobrar o devolver diferencias por el medio definido','Notificar resultado y registrar entrega, reembolso o solicitud pendiente']),
 (16,'Registrar y consultar operaciones offline',[28,29,30,31],['cliente','cajero','encargado','admin'],
  'Preparar catálogo persistente, consultar datos descargados, registrar reservas o ventas de contado según rol y revisar operaciones locales tras reiniciar. Las ventas permanecen provisionales.',
  ['Autenticar y preparar datos locales mientras exista conexión','Identificar cuenta, empresa, sucursal y vigencia offline','Consultar catálogo o preparar reserva/venta local según permisos','Guardar UUID, cabecera, detalles y pendiente atómicamente','Consultar operaciones y resultados después de cerrar y volver a abrir']),
 (17,'Sincronizar operaciones y resolver conflictos',[32,33],['cliente','cajero','encargado','admin'],
  'Enviar pendientes manual o automáticamente, recuperar resultados y tratar conflictos. El autor consulta sus operaciones; una resolución comercial requiere el permiso correspondiente.',
  ['Detectar conexión o recibir solicitud manual','Enviar operaciones preservando UUID y contenido','Validar identidad, suscripción y reglas por operación','Guardar confirmación, rechazo o conflicto; conservar pendientes ante error temporal','Resolver conflictos autorizados con nueva operación enlazada o compensación explícita']),
 (18,'Obtener reportes comerciales',[34,35],['admin','encargado','ia'],
  'Consultar reportes convencionales o solicitarlos por texto/voz mediante IA, con filtros variables y datos reales autorizados; representar y exportar resultados a PDF/XLSX.',
  ['Seleccionar reporte convencional o solicitud generativa','Validar permisos y acceso Profesional cuando utilice IA','Interpretar y confirmar filtros o solicitar aclaración','Consultar datos empresariales con operaciones permitidas','Mostrar tabla/gráfico y exportar los mismos resultados autorizados']),
 (19,'Preparar y consultar analítica inteligente',[36,37],['admin','encargado','tecnico'],
  'Agrupar dos subflujos diferenciados: preparación, entrenamiento y evaluación técnica; consulta empresarial de KPI, predicciones y segmentos. Abrir el dashboard no ejecuta entrenamiento.',
  ['Preparar datos sintéticos reproducibles y variables en el subflujo técnico','Entrenar y evaluar modelos supervisados y no supervisados','Versionar artefactos, métricas y procedencia','En el subflujo empresarial obtener datos e inferencias del tenant autorizado','Visualizar indicadores, predicciones y segmentos con sus limitaciones']),
 (20,'Consultar auditoría y trazabilidad',[38],['super','admin','encargado'],
  'Consultar eventos autorizados de acceso y operaciones, pagos, cambios y sincronización. La plataforma consulta su ámbito técnico y SaaS sin acceso comercial irrestricto a empresas.',
  ['Validar permiso y ámbito de auditoría','Aplicar filtros de fecha, usuario, acción o UUID','Consultar eventos paginados','Relacionar acción, operación y resultado','Presentar evidencia sin contraseñas, tokens ni credenciales externas']),
]

ACTORS = {
 'usuario':('Usuario de la plataforma','Actor general de quienes disponen de cuenta. Acceso y recuperación; no otorga permisos comerciales por sí mismo.'),
 'personal':('Personal de empresa','Actor general del personal empresarial. Sus especializaciones conservan permisos y sucursales asignados.'),
 'super':('Superadministrador SaaS','Administra empresas, planes y contratos, y consulta auditoría de plataforma. No se le concede acceso indiscriminado a datos comerciales.'),
 'admin':('Administrador de empresa','Configura personal, catálogo y operación de su empresa. Consulta su contrato; no edita planes globales.'),
 'encargado':('Encargado de sucursal','Atiende operaciones, reservas, cambios y conflictos dentro de las sucursales y permisos asignados.'),
 'cajero':('Vendedor o cajero','Registra ventas, atiende clientes y utiliza operaciones offline y sincronización autorizadas.'),
 'inventario':('Responsable de inventario y compras','Gestiona catálogo autorizado, proveedores, recepciones y movimientos de existencias.'),
 'cliente':('Cliente','Cuenta única entre tiendas; compra, reserva y consulta solo sus datos y solicitudes en el contexto correspondiente.'),
 'visitante':('Visitante','Consulta tiendas y catálogo público. Requiere cuenta para efectuar operaciones privadas.'),
 'tecnico':('Responsable técnico de analítica','Prepara datasets, entrena, evalúa y versiona modelos en herramientas técnicas. No es un permiso automático del administrador empresarial.'),
 'pasarela':('Pasarela de pagos','Procesa pagos y reembolsos de prueba e informa resultados verificables; no es un usuario humano del sistema.'),
 'ia':('Servicio de IA','Interpreta solicitudes y apoya recomendaciones mediante contratos controlados; no recibe acceso irrestricto a PostgreSQL.'),
 'notificaciones':('Servicios de correo y push','Transportan recuperación y avisos; la aplicación conserva sus notificaciones e historial propios.'),
}
GENERALIZATIONS = [('super','usuario'),('personal','usuario'),('cliente','usuario'),('admin','personal'),('encargado','personal'),('cajero','personal'),('inventario','personal')]

RELATIONS = [
 ('include',11,8,'Consulta obligatoria de existencias para validar la compra central.'),
 ('include',11,10,'Salida obligatoria al confirmar una compra pagada; el checkout abandonado o pendiente no alcanza este punto.'),
 ('include',13,8,'Consulta obligatoria de existencias antes de confirmar una venta presencial.'),
 ('include',13,10,'Una venta presencial confirmada registra su salida en la misma transacción.'),
 ('extend',14,11,'Punto: compra confirmada. Condición: el usuario solicita visualizar o descargar su comprobante.'),
 ('extend',14,13,'Punto: venta registrada. Condición: el usuario solicita visualizar o descargar su comprobante.'),
]

RNF = [
 ('Seguridad de acceso','Comprobar identidad, permisos y propiedad en cada operación privada; rechazar sesiones revocadas.'),
 ('Separación empresarial','Impedir lecturas y escrituras entre empresas incluso al alterar manualmente identificadores o parámetros.'),
 ('Persistencia local','Recuperar reservas, ventas y pendientes después de un cierre y reinicio normal de navegador o aplicación.'),
 ('Consistencia transaccional','Confirmar juntos cabecera, detalles y movimientos; un fallo intermedio debe revertir el conjunto.'),
 ('Reenvío seguro','Procesar repetidamente un UUID confirmado sin crear ventas, pagos o movimientos adicionales.'),
 ('Recuperación de comunicación','Conservar datos y permitir reintentar después de timeout, desconexión o respuesta perdida.'),
 ('Mantenibilidad','Separar presentación, negocio, persistencia y sincronización, con componentes y contratos identificables.'),
 ('Compatibilidad','Verificar instalación PWA en navegador compatible y persistencia Flutter en Android; no prometer soporte universal de APIs offline.'),
 ('Uso de recursos','Paginar consultas, limitar lotes y medir latencia, errores y memoria bajo condiciones de prueba documentadas.'),
 ('Observabilidad','Registrar UUID, responsable, estado, intentos y motivo de conflicto, sin almacenar secretos en evidencias o logs.'),
 ('Verificación de calidad','Disponer de pruebas reproducibles de aislamiento, inventario, sincronización, planes y reglas comerciales críticas.'),
 ('Correspondencia documental','Relacionar requisitos, CU, componentes, pruebas y diagramas con una versión identificada de la solución.'),
]

RULES = [
 ('La empresa es la unidad de aislamiento; sus sucursales son unidades operativas del mismo tenant.','Examen','02, 04'),
 ('El contexto empresarial de operaciones privadas se obtiene de la sesión validada; no del prefijo del correo ni de un ID confiado al cliente.','Examen + diseño','01 y transversal'),
 ('Un correo identifica una cuenta global. El personal conserva su empresa; el cliente elige tienda después de entrar y solo accede a datos propios.','Decisión del proyecto','01, 03, 05, 09'),
 ('El administrador empresarial no modifica planes globales ni la contraseña global del cliente, ni obtiene permisos de plataforma.','Diseño de autorización','02, 03, 05'),
 ('El plan Básico admite inicialmente dos sucursales activas y Profesional diez; los límites son configurables y se validan también al reactivar y ante concurrencia.','Examen + diseño','02, 04'),
 ('Los reportes convencionales están en ambos planes; los generativos requieren Profesional y autorización del usuario.','Examen','02, 18'),
 ('Una suscripción vencida conserva historial y pendientes; bloquea nuevas operaciones comerciales y permite consultar su estado y gestionar renovación.','Política del proyecto','02, 16, 17'),
 ('El cambio a un plan menor se rechaza mientras existan más sucursales activas que las permitidas por el destino.','Política del proyecto','02, 04'),
 ('Los importes se recalculan en el servidor. Se aplica el menor precio válido entre minorista, mayorista y oferta, sin acumular descuentos; el umbral mayorista inicial es seis unidades de la misma prenda y es configurable.','Política del proyecto','06, 11, 12, 13'),
 ('La disponibilidad central se calcula restando retenciones vigentes a las existencias físicas; no se confirma una salida que produzca stock negativo.','Examen + diseño','08, 10, 11, 12, 13, 17'),
 ('La reserva central aceptada retiene disponibilidad por 24 horas; al cancelar o vencer se libera. La reserva offline es provisional.','Política del proyecto','12, 16, 17'),
 ('Preparar una reserva, añadir al carrito o mantener un pago pendiente no constituye una venta confirmada ni acredita un cobro.','Regla comercial del proyecto','11, 12, 13'),
 ('Solo se confirma un pago electrónico por resultado verificable del proveedor y por el importe autorizado; los reenvíos no duplican su efecto.','Examen + diseño','11, 15'),
 ('Cada entrada o salida de stock se aplica una sola vez mediante el mecanismo de movimientos del sistema.','Examen + diseño','07, 10, 11, 13, 15, 17'),
 ('El comprobante corresponde a una venta confirmada y a su empresa; la consulta o descarga exige autorización y no crea otro documento comercial.','Diseño del proyecto','14'),
 ('El modo offline exige autenticación previa y datos descargados. La autorización local tendrá vigencia máxima de 24 horas, limitada por la suscripción conocida.','Examen + política del proyecto','16'),
 ('Las ventas offline son de contado; recibir efectivo localmente no garantiza aceptación central. Ante rechazo se requiere resolución o compensación documentada.','Examen + diseño','16, 17'),
 ('Una operación conserva UUID, autor, empresa, sucursal y contenido entre intentos. El mismo UUID con otro contenido se rechaza.','Examen + diseño','16, 17'),
 ('Un envío o cierre de sesión no elimina pendientes. Un lote informa un resultado por operación y conserva los demás registros aunque uno falle.','Examen + diseño','01, 16, 17'),
 ('Stock insuficiente, cambio de precio o variante inactiva generan un resultado explícito de conflicto; no se acepta parcialmente una venta. La revocación de permisos impide confirmar.','Política del proyecto','17'),
 ('Corregir un conflicto crea una operación nueva enlazada a la original, sin ocultar el historial ni reemplazar silenciosamente el efectivo registrado.','Diseño del proyecto','17'),
 ('El cambio de prenda se solicita hasta siete días calendario desde la entrega, con compra comprobable, prenda elegible sin uso y una única sustitución por unidad.','Política del proyecto; el examen exige definir un plazo','15'),
 ('La recepción de la prenda y la entrega del reemplazo son eventos separados. El crédito usa el importe efectivamente pagado; las diferencias se cobran o devuelven íntegramente.','Política del proyecto','15'),
 ('Sin reemplazo disponible se conserva la solicitud y se permite cancelar con devolución del crédito. El reembolso sigue el medio original y un objetivo administrativo de cinco días hábiles.','Política del proyecto','15'),
 ('Los reportes comerciales consultan datos reales del tenant autorizado. La IA interpreta parámetros; el backend valida y ejecuta operaciones permitidas, sin SQL libre del modelo.','Examen + diseño','18'),
 ('Texto y voz deben permitir solicitudes variables; se demostrarán al menos cuatro tipos de reportes. PDF y XLSX deben corresponder a los resultados autorizados mostrados.','Examen','18'),
 ('La analítica incluye aprendizaje supervisado y no supervisado, preparación de variables, evaluación e integración. Los datos sintéticos se identifican; una predicción no se presenta como una venta real.','Examen + diseño','19'),
 ('Consultar el dashboard usa artefactos ya evaluados; el entrenamiento es un subflujo técnico separado y se ejecuta fuera del servidor de producción.','Decisión técnica del proyecto','19'),
]

def case_id(n): return f'CU-{n:02d}'

def data():
    historical=json.loads((ROOT/'docs/casos_de_uso.json').read_text(encoding='utf-8'))
    assert len(historical)==38,'Se necesita el inventario histórico de 38 CU para mantener el vínculo con P1.'
    p1_by_id={c['id']:c['antecedente'] for c in historical}
    return [dict(id=case_id(n),nombre=name,cu_anteriores=[case_id(v) for v in old],
                 cu_p1_antecedentes=sorted({'P1-'+case_id(int(p1_by_id[case_id(v)])) for v in old if p1_by_id[case_id(v)].isdigit()}),actores=actors,
                 alcance=scope,flujo_principal=flow,tipo_modelo='Caso de uso principal con subflujos explícitos',
                 estado_implementacion='No reevaluado por la consolidación documental')
            for n,name,old,actors,scope,flow in CASES]

def write_document(cases):
    p=['# CAPÍTULO II. ANÁLISIS DE REQUISITOS','',
       'Versión documental con 20 casos de uso principales. Las 38 capacidades del inventario anterior se conservan mediante la tabla de equivalencias. Este capítulo describe requisitos; la consolidación no certifica implementación ni pruebas nuevas.','',
       '## 2.1. Descripción del sistema propuesto','',
       'FashionStore se propone como una plataforma de comercio electrónico web y móvil para empresas que comercializan prendas de vestir. Su organización como servicio SaaS permite ofrecer una base tecnológica compartida, conservando espacios de operación separados para cada negocio. Una empresa administra sus sucursales, empleados, catálogo, proveedores, inventarios y transacciones de acuerdo con el plan contratado.','',
       'El servicio distingue la administración de plataforma de la administración empresarial. El superadministrador gestiona empresas, planes y contratos; los administradores empresariales y su personal actúan dentro de su organización y de las sucursales autorizadas. El acceso se realiza mediante correo y contraseña. Los clientes disponen de una cuenta común para distintas tiendas, pero cada compra, reserva y solicitud mantiene su pertenencia comercial y sus restricciones de acceso.','',
       'La operación combina consultas y registros centrales con almacenamiento local. La aplicación Angular incorpora capacidades PWA e IndexedDB, mientras Flutter utiliza SQLite. Cuando no existe conexión, los usuarios autorizados consultan la información descargada y registran reservas o ventas de contado según su rol. Estos registros se conservan como operaciones provisionales, con identificación y estado, hasta que el servidor pueda validarlos. La sincronización comunica confirmaciones, rechazos y conflictos sin eliminar registros por el solo intento de envío.','',
       'La plataforma mantiene los procesos del comercio de prendas, desde su clasificación y abastecimiento hasta las reservas, el checkout, la caja presencial y los cambios. Conserva el vestidor existente y las recomendaciones, e incorpora reportes por lenguaje natural y analítica basada en modelos supervisados y no supervisados. Los reportes consultan datos comerciales autorizados; los conjuntos sintéticos utilizados para entrenamiento se identifican por separado.','',
       'La solución se integra mediante una API REST con FastAPI y PostgreSQL central. Su validación considera al menos dos empresas independientes, las aplicaciones web y móvil, la persistencia local, la consistencia del inventario y la trazabilidad entre requisitos, casos de uso y evidencias.','',
       '## 2.2. Identificación de actores','',
       'Un actor representa un papel externo que interactúa con FashionStore; no equivale necesariamente a una persona o a una tabla. Una persona puede desempeñar varios papeles si sus permisos lo permiten. Las asociaciones indican participación, sin otorgar por sí solas todos los permisos del caso.','',
       '| Actor | Participación y límite |','|---|---|']
    p += [f'| {label} | {desc} |' for key,(label,desc) in ACTORS.items()]
    p += ['','Usuario de la plataforma y Personal de empresa son actores generales. Superadministrador, Cliente y Personal especializan al primero; Administrador, Encargado, Cajero y Responsable de inventario especializan a Personal. La herencia de participación no elimina las restricciones de rol, propiedad o sucursal. El backend, la base de datos y el almacenamiento local son componentes internos, no actores externos.','',
          '## 2.3. Requisitos funcionales y no funcionales','','### 2.3.1. Requisitos funcionales','',
          'Los requisitos se expresan como capacidades observables. Su agrupación en 20 casos principales organiza la documentación; cada grupo conserva sus subflujos y criterios de aceptación.','',
          '| ID | Requisito funcional | Caso principal |','|---|---|---|']
    for i,c in enumerate(cases,1):
        description=c['alcance'][0].lower()+c['alcance'][1:]
        if i==16:description='ofrecer una PWA instalable en navegadores compatibles y almacenamiento persistente en web y móvil para descargar catálogo, consultar datos conocidos, registrar reservas o ventas de contado según rol y recuperar los pendientes después de reiniciar.'
        if i==19:description='permitir preparar datos sintéticos y variables, entrenar y evaluar modelos supervisados y no supervisados, versionar los artefactos y consultar indicadores, predicciones y segmentos del tenant autorizado, diferenciando los subflujos técnico y empresarial.'
        p.append(f"| RF-{i:02d} | El sistema deberá {description} | {c['id']} |")
    p += ['','### 2.3.2. Requisitos no funcionales','','| ID | Criterio de calidad | Comprobación requerida |','|---|---|---|']
    p += [f'| RNF-{i:02d} | {title} | {desc} |' for i,(title,desc) in enumerate(RNF,1)]
    p += ['','## 2.4. Reglas de negocio','',
          'Se diferencian las condiciones del examen de las políticas adoptadas por el equipo. Los plazos de cambios, retenciones, vigencia offline y reembolsos son decisiones documentadas del proyecto, no plazos atribuidos a la guía ni a una normativa legal.','',
          '| ID | Regla | Origen | CU nuevos |','|---|---|---|---|']
    p += [f'| RN-{i:02d} | {rule} | {origin} | {linked} |' for i,(rule,origin,linked) in enumerate(RULES,1)]
    p += ['','## 2.5. Diagrama UML de casos de uso','','### 2.5.1. Modelos de casos de uso','',
          'El modelo general representa 20 casos principales y los actores que participan en sus objetivos. Para facilitar lectura y exposición se incluyen cinco vistas complementarias por área dentro del mismo archivo draw.io. Las vistas reutilizan los mismos identificadores; no introducen casos nuevos.','',
          'El límite del sistema contiene los casos de uso y mantiene los actores fuera. Las elipses representan objetivos funcionales y las líneas continuas, participación. La generalización de actores utiliza una línea continua con triángulo hueco dirigido al actor general.','',
          '**Relación «include».** Una flecha discontinua parte del caso base hacia el comportamiento que necesita ejecutar. En el flujo exitoso de compra o venta, la consulta de disponibilidad y el registro de salidas son comportamientos reutilizados. Las validaciones y los movimientos se ejecutan dentro de la transacción comercial correspondiente; el diagrama no propone dos descuentos de inventario.','',
          '**Relación «extend».** La flecha discontinua parte de la extensión hacia el caso base. En este modelo, CU-14 representa obtener la representación del comprobante a solicitud del usuario después de confirmar una compra o venta. La venta puede cerrar y conservar su registro comercial aunque el usuario no descargue el documento; la representación puede generarse o recuperarse después.','',
          '| Relación | Origen → destino | Justificación o condición |','|---|---|---|']
    p += [f'| «{kind}» | {case_id(source)} → {case_id(target)} | {why} |' for kind,source,target,why in RELATIONS]
    p += ['','La autenticación se establece como precondición de las operaciones privadas; no se dibuja un «include» hacia iniciar sesión desde cada caso. Tampoco se usa «include» para expresar orden temporal: registrar sin conexión no ejecuta necesariamente la sincronización en ese momento. La resolución de conflictos es un subflujo condicionado de CU-17, y entrenar modelos es un subflujo técnico de CU-19 que no se ejecuta al consultar el dashboard.','',
          '### Catálogo consolidado y equivalencia con los 38 CU','',
          '| CU nuevo | Nombre | CU anteriores absorbidos |','|---|---|---|']
    p += [f"| {c['id']} | {c['nombre']} | {', '.join(c['cu_anteriores'])} |" for c in cases]
    p += ['','### Criterio de consolidación','',
          'Los casos principales agrupan objetivos de una misma área y mantienen subflujos separados. Por ejemplo, CU-02 conserva aprovisionamiento empresarial, configuración de planes y gestión de contratos; CU-16 conserva preparación de datos, reserva local, venta local y consulta de pendientes. CU-19 diferencia entrenamiento técnico y consulta empresarial. No se ejecutan todos estos subflujos cada vez que un actor participa.','',
          'La nueva numeración es documental. La equivalencia distingue los 38 CU del plan P2 anterior y los antecedentes del primer parcial. Los comentarios heredados del código pueden utilizar la numeración del P1, que no debe confundirse con la del plan de 38 CU. No se cambian IDs comerciales, rutas ni métodos por esta consolidación. Antes del cierre documental deberán utilizarse los nuevos IDs de forma coherente en fichas, diagramas y matriz, manteniendo ambos vínculos históricos.','',
          'La reducción no garantiza por sí sola una disminución proporcional del trabajo: cada regla, alternativa y prueba debe seguir documentada. La guía no establece un total de 38 CU; esta cantidad provenía del desglose inicial del equipo.','',
          '## Archivos de apoyo','',
          '- `FashionStore_Casos_de_Uso_20.drawio`: modelo editable de seis páginas.','- `CU_20_catalogo.json`: definición estructurada de los 20 casos y sus flujos.','- `equivalencias_38_a_20.csv`: cobertura completa de los 38 identificadores históricos.','- `FICHAS_RESUMIDAS_20_CU.md`: objetivo, actores, cobertura y flujo principal de cada caso.','- Carpeta `vistas/`: SVG y PNG de cada vista.','',
          '## Referencias del modelo','',
          '- Examen Parcial-2 (IMPORTANTE) - Sistemas 2 - S2-2026.pdf, páginas 2–10.','- Plan del proyecto: inventario histórico de 38 CU.','- Decisiones del equipo: cuenta global de cliente, políticas comerciales y despliegue nativo.','- OMG UML 2.5.1: https://www.omg.org/spec/UML/2.5.1','- Formato draw.io: https://www.drawio.com/docs/reference/diagram-generation/','']
    (OUT/'CAPITULO_II_20_CU.md').write_text('\n'.join(p),encoding='utf-8')

def write_catalog(cases):
    (OUT/'CU_20_catalogo.json').write_text(json.dumps({'version':'modelo-20-cu-v1','tipo':'modelo de requisitos; no certifica pruebas nuevas','casos':cases,'relaciones':[dict(tipo=k,origen=case_id(s),destino=case_id(t),condicion=c) for k,s,t,c in RELATIONS]},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (OUT/'equivalencias_38_a_20.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        historical={c['id']:c['antecedente'] for c in json.loads((ROOT/'docs/casos_de_uso.json').read_text(encoding='utf-8'))}
        writer=csv.writer(stream);writer.writerow(['CU_P2_plan_38','Antecedente_P1','CU_P2_modelo_20','Nombre_nuevo'])
        writer.writerows(sorted((old,('P1-'+case_id(int(historical[old]))) if historical[old].isdigit() else 'nuevo en P2',c['id'],c['nombre']) for c in cases for old in c['cu_anteriores']))
    lines=['# Fichas resumidas de los 20 casos principales','','Estas fichas delimitan los grupos y subflujos. Su especificación detallada deberá desarrollar precondiciones, alternativas, postcondiciones y pruebas por subflujo; no equivalen a 20 fichas atómicas ya cerradas.','']
    for c in cases:
        lines += [f"## {c['id']}. {c['nombre']}",'',f"**Cobertura del plan P2 anterior:** {', '.join(c['cu_anteriores'])}.",'',f"**Antecedentes P1:** {', '.join(c['cu_p1_antecedentes']) or 'Nuevos requisitos del P2'}.",'',f"**Actores:** {', '.join(ACTORS[a][0] for a in c['actores'])}.",'',f"**Objetivo y alcance:** {c['alcance']}",'','**Flujo principal / subflujos identificados**','']
        lines += [f'{i}. {step}.' for i,step in enumerate(c['flujo_principal'],1)]
        rel=[f'«{kind}» hacia {case_id(t)}: {why}' for kind,s,t,why in RELATIONS if s==int(c['id'][3:])]
        if rel:lines += ['','**Relaciones salientes:**']+['- '+item for item in rel]
        lines += ['']
    (OUT/'FICHAS_RESUMIDAS_20_CU.md').write_text('\n'.join(lines),encoding='utf-8')

BLUE='#dceafb'; INK='#23374d'; GREEN='#245f9e'; PURPLE='#7240a0'

class View:
    def __init__(self,name,width,height,boundary):
        self.name,self.width,self.height,self.boundary=name,width,height,boundary
        self.nodes={};self.edges=[];self.notes=[]
    def actor(self,key,x,y):self.nodes['a_'+key]=dict(kind='actor',label=ACTORS[key][0],x=x,y=y,w=72,h=96,key=key)
    def uc(self,n,x,y,w=270,h=104):self.nodes['u_'+str(n)]=dict(kind='uc',label=next(c[1] for c in CASES if c[0]==n),x=x,y=y,w=w,h=h,n=n)
    def edge(self,source,target,kind='association',waypoints=None,labelpos=None):
        self.edges.append(dict(source=source,target=target,kind=kind,waypoints=waypoints or [],labelpos=labelpos))
    def connect_actors(self):
        for n,name,old,actors,scope,flow in CASES:
            if 'u_'+str(n) not in self.nodes:continue
            for actor in actors:
                if 'a_'+actor in self.nodes:self.edge('a_'+actor,'u_'+str(n))
        for child,parent in GENERALIZATIONS:
            if 'a_'+child in self.nodes and 'a_'+parent in self.nodes:self.edge('a_'+child,'a_'+parent,'generalization')
    def relations(self):
        for kind,s,t,why in RELATIONS:
            if 'u_'+str(s) in self.nodes and 'u_'+str(t) in self.nodes:self.edge('u_'+str(s),'u_'+str(t),kind)

def views():
    result=[]
    v=View('01 General circular — 20 CU',3200,2200,(510,130,2180,1840))
    # Bloques de objetivos alrededor del contorno, semejante a la referencia visual.
    order=[1,2,3,4,5,6,7,8,10,13,14,11,12,15,16,17,18,19,20,9]
    for i,n in enumerate(order):
        angle=-math.pi/2+2*math.pi*i/20
        v.uc(n,1600+900*math.cos(angle)-125,1060+730*math.sin(angle)-52,250,104)
    for key,y in [('usuario',230),('personal',460),('super',690),('admin',920),('encargado',1150),('cajero',1380),('inventario',1610),('cliente',1840)]:v.actor(key,140,y)
    for key,y in [('visitante',230),('tecnico',600),('pasarela',970),('ia',1340),('notificaciones',1710)]:v.actor(key,2930,y)
    v.connect_actors();v.relations()
    circular_routes={
      (11,8):([(1400,1500),(2000,1400),(2180,1440)],(1720,1410)),
      (11,10):([(1500,1550),(1900,1480),(2100,1500)],(1740,1510)),
      (13,8):([(1930,1430),(2180,1370)],(2080,1360)),
      (13,10):([(1950,1600),(2030,1550)],(1990,1570)),
      (14,11):([(1580,1630),(1450,1610),(1380,1640)],(1440,1580)),
      (14,13):([(1650,1640),(1750,1610),(1820,1640)],(1770,1590)),
    }
    for e in v.edges:
        if e['kind'] in ('include','extend'):
            key=(int(e['source'][2:]),int(e['target'][2:]))
            e['waypoints'],e['labelpos']=circular_routes[key]
    v.notes=[(1235,850,730,265,'Modelo general · 20 objetivos principales\nLas vistas 02–06 amplían su lectura.\n\nLínea continua: participación\nFlecha discontinua azul: «include»\nFlecha discontinua violeta: «extend»\nTriángulo hueco: generalización de actor\n\nLas asociaciones no conceden todos los permisos del grupo.'),
             (540,2000,2100,100,'Los 38 CU anteriores se conservan en la tabla de equivalencias. Los subflujos se detallan en las fichas. Modelo de requisitos: no certifica implementación ni pruebas nuevas.')]
    result.append(v)
    v=View('02 Acceso, SaaS y organización',1900,1300,(540,120,1070,1030))
    for key,x,y in [('usuario',100,150),('super',100,390),('personal',100,660),('cliente',100,950),('admin',1730,650),('notificaciones',1730,950)]:v.actor(key,x,y)
    for n,x,y in [(1,720,180),(2,1140,180),(3,720,490),(4,1140,490),(5,930,820)]:v.uc(n,x,y,310,125)
    v.connect_actors()
    v.notes=[(570,1040,1000,90,'CU-02: la plataforma administra el servicio; la empresa consulta su contrato. CU-01: cuenta global, recuperación y cierre de sesión.')]
    result.append(v)
    v=View('03 Catálogo y abastecimiento',1900,1360,(470,130,1100,1090))
    for key,x,y in [('personal',100,190),('admin',100,470),('inventario',100,790),('visitante',1720,190),('cliente',1720,510),('ia',1720,830)]:v.actor(key,x,y)
    for n,x,y in [(6,620,260),(7,1080,260),(8,620,610),(10,1080,610),(9,850,960)]:v.uc(n,x,y,315,125)
    v.connect_actors()
    v.notes=[(530,1120,1000,90,'CU-09 contiene consulta pública y uso opcional de vestidor/recomendaciones. CU-07 diferencia proveedor, compra y recepción.')]
    result.append(v)
    v=View('04 Ventas, reservas y comprobantes',2350,1700,(480,120,1440,1440))
    for key,x,y in [('cliente',130,260),('admin',130,650),('cajero',130,1060),('encargado',130,1450),('pasarela',2130,500),('notificaciones',2130,1240)]:v.actor(key,x,y)
    for n,x,y in [(8,610,240),(10,1490,240),(11,610,680),(13,1490,680),(14,1050,1110),(12,610,1370),(15,1490,1370)]:v.uc(n,x,y,310,125)
    v.connect_actors();v.relations()
    # Trayectorias internas específicas: los trazos no atraviesan otras elipses.
    for e in v.edges:
        if e['kind']=='include':
            s,t=int(e['source'][2:]),int(e['target'][2:])
            if (s,t)==(11,8):e['waypoints']=[(765,540)]
            if (s,t)==(13,10):e['waypoints']=[(1645,540)]
            if (s,t)==(11,10):e['waypoints']=[(940,535),(1500,470)];e['labelpos']=(1220,505)
            if (s,t)==(13,8):e['waypoints']=[(1460,585),(920,470)];e['labelpos']=(1200,590)
    v.notes=[(550,1590,1750,90,'«include»: disponibilidad y salidas, obligatorias en la confirmación exitosa. «extend»: CU-14 se activa al solicitar el documento tras confirmar una compra o venta. Los movimientos se registran una sola vez.')]
    result.append(v)
    v=View('05 Operación offline y sincronización',1800,1150,(430,120,1070,850))
    for key,x,y in [('cliente',100,200),('cajero',100,510),('encargado',1610,200),('admin',1610,510)]:v.actor(key,x,y)
    v.uc(16,600,260,330,135);v.uc(17,1050,590,330,135);v.connect_actors()
    v.notes=[(510,770,920,150,'CU-16: catálogo, reserva, venta de contado y consulta local según rol.\nCU-17: envío, resultados, reintentos y resolución autorizada de conflictos.\nLa sincronización posterior no es un «include» de cada registro offline.\nEl cliente no registra ventas de caja; su operación offline es la reserva.')]
    result.append(v)
    v=View('06 Reportes, analítica y auditoría',1850,1350,(470,120,1080,1100))
    for key,x,y in [('admin',100,200),('encargado',100,560),('super',100,920),('ia',1660,200),('tecnico',1660,620)]:v.actor(key,x,y)
    v.uc(18,650,270,340,135);v.uc(19,1120,620,340,135);v.uc(20,650,900,340,135);v.connect_actors()
    v.notes=[(520,1070,980,110,'El entrenamiento es un subflujo técnico de CU-19. Consultar el dashboard no lo ejecuta. El superadministrador consulta auditoría de su propio ámbito.')]
    result.append(v)
    return result

def style(node):
    if node['kind']=='actor':return 'shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;html=0;align=center;whiteSpace=wrap;labelWidth=235;fontSize=17;fontColor='+INK+';strokeColor='+INK+';fillColor=#ffffff;'
    return 'ellipse;perimeter=ellipsePerimeter;whiteSpace=wrap;html=0;fontSize=19;fontColor='+INK+';fillColor='+BLUE+';strokeColor=#456787;strokeWidth=1.8;align=center;verticalAlign=middle;'

def write_drawio(all_views):
    mxfile=ET.Element('mxfile',host='app.diagrams.net',agent='FashionStore documental',version='29.0.0')
    for i,v in enumerate(all_views,1):
        diagram=ET.SubElement(mxfile,'diagram',id=f'view-{i}',name=v.name)
        model=ET.SubElement(diagram,'mxGraphModel',dx='0',dy='0',grid='0',gridSize='10',guides='1',tooltips='1',connect='1',arrows='1',fold='1',page='1',pageScale='1',pageWidth=str(v.width),pageHeight=str(v.height),math='0',shadow='0')
        graph=ET.SubElement(model,'root');ET.SubElement(graph,'mxCell',id='0');ET.SubElement(graph,'mxCell',id='1',parent='0')
        def rect(id_,label,x,y,w,h,st):
            cell=ET.SubElement(graph,'mxCell',id=id_,value=label,style=st,vertex='1',parent='1')
            ET.SubElement(cell,'mxGeometry',x=str(x),y=str(y),width=str(w),height=str(h),attrib={'as':'geometry'})
        rect('title',v.name,40,20,v.width-80,70,'text;html=0;whiteSpace=wrap;align=left;fontSize=30;fontStyle=1;fontColor='+INK+';strokeColor=none;fillColor=none;')
        bx,by,bw,bh=v.boundary
        rect('boundary','FashionStore SaaS — límite del sistema',bx,by,bw,bh,'rounded=0;whiteSpace=wrap;html=0;verticalAlign=top;align=left;spacingTop=18;spacingLeft=20;fontSize=22;fontStyle=1;fillColor=#ffffff;strokeColor=#71839a;strokeWidth=2;')
        # Conectores debajo de los nodos para que sus rótulos permanezcan legibles.
        for j,e in enumerate(v.edges,1):
            k=e['kind'];color=GREEN if k=='include' else PURPLE if k=='extend' else '#8291a0'
            st='edgeStyle=none;html=0;rounded=0;strokeWidth='+('2.3' if k in ('include','extend') else '1')+';strokeColor='+color+';fontSize=17;fontColor='+color+';labelBackgroundColor=#ffffff;'
            st+= 'dashed=1;dashPattern=7 5;endArrow=open;endFill=0;' if k in ('include','extend') else 'dashed=0;endArrow=block;endFill=0;' if k=='generalization' else 'dashed=0;endArrow=none;'
            cell=ET.SubElement(graph,'mxCell',id='e'+str(j),value='«'+k+'»' if k in ('include','extend') else '',style=st,edge='1',parent='1',source=e['source'],target=e['target'])
            geo=ET.SubElement(cell,'mxGeometry',relative='1',attrib={'as':'geometry'})
            if e['waypoints']:
                arr=ET.SubElement(geo,'Array',attrib={'as':'points'})
                for x,y in e['waypoints']:ET.SubElement(arr,'mxPoint',x=str(x),y=str(y))
            if e['labelpos']:
                source,target=v.nodes[e['source']],v.nodes[e['target']]
                points=[clipped(source,e['waypoints'][0] if e['waypoints'] else center(target))]+e['waypoints']+[clipped(target,e['waypoints'][-1] if e['waypoints'] else center(source))]
                lengths=[math.dist(a,b) for a,b in zip(points,points[1:])];remaining=sum(lengths)/2
                for a,b,length in zip(points,points[1:],lengths):
                    if remaining<=length:
                        fraction=remaining/length if length else 0
                        midpoint=(a[0]+(b[0]-a[0])*fraction,a[1]+(b[1]-a[1])*fraction);break
                    remaining-=length
                ET.SubElement(geo,'mxPoint',x=str(round(e['labelpos'][0]-midpoint[0],2)),y=str(round(e['labelpos'][1]-midpoint[1],2)),attrib={'as':'offset'})
        for key,node in v.nodes.items():
            label=case_id(node['n'])+'\n'+node['label'] if node['kind']=='uc' else node['label']+(' (general)' if node['key'] in ('usuario','personal') else '')
            rect(key,label,node['x'],node['y'],node['w'],node['h'],style(node))
        for j,(x,y,w,h,label) in enumerate(v.notes,1):
            rect('note'+str(j),label,x,y,w,h,'rounded=1;arcSize=8;whiteSpace=wrap;html=0;align=left;verticalAlign=middle;spacing=18;fontSize=18;fontColor=#425268;fillColor=#f4f7fa;strokeColor=#c4d1de;')
    ET.indent(mxfile,space='  ')
    target=OUT/'FashionStore_Casos_de_Uso_20.drawio'
    ET.ElementTree(mxfile).write(target,encoding='utf-8',xml_declaration=True)
    return target

def wrapped(label,width,font_size):
    lines=[]
    for line in label.split('\n'):
        lines.extend(textwrap.wrap(line,width=max(12,int(width/(font_size*.54)))) or [''])
    return lines

def text_svg(x,y,label,width,font_size=18,anchor='middle',color=INK,bold=False):
    lines=wrapped(label,width,font_size);step=font_size*1.3
    start=y-(len(lines)-1)*step/2
    return '<text font-family="Arial, sans-serif" font-size="'+str(font_size)+'" font-weight="'+('bold' if bold else 'normal')+'" text-anchor="'+anchor+'" fill="'+color+'">'+''.join(f'<tspan x="{x:.1f}" y="{start+i*step:.1f}">{escape(s)}</tspan>' for i,s in enumerate(lines))+'</text>'

def center(n):return n['x']+n['w']/2,n['y']+n['h']/2
def clipped(n,toward):
    cx,cy=center(n);dx,dy=toward[0]-cx,toward[1]-cy
    if n['kind']=='uc':
        den=math.sqrt((dx/(n['w']/2))**2+(dy/(n['h']/2))**2) or 1
        return cx+dx/den,cy+dy/den
    den=max(abs(dx)/(n['w']/2),abs(dy)/(n['h']/2)) or 1
    return cx+dx/den,cy+dy/den

def write_svg(v,i):
    svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{v.width}" height="{v.height}" viewBox="0 0 {v.width} {v.height}">',
         '<defs><marker id="include" markerWidth="12" markerHeight="12" refX="10" refY="6" orient="auto"><path d="M1 1 L10 6 L1 11" fill="none" stroke="'+GREEN+'" stroke-width="1.6"/></marker><marker id="extend" markerWidth="12" markerHeight="12" refX="10" refY="6" orient="auto"><path d="M1 1 L10 6 L1 11" fill="none" stroke="'+PURPLE+'" stroke-width="1.6"/></marker><marker id="generalization" markerWidth="14" markerHeight="14" refX="12" refY="7" orient="auto"><path d="M1 1 L12 7 L1 13 Z" fill="white" stroke="#8291a0" stroke-width="1.4"/></marker></defs>',
         f'<rect width="{v.width}" height="{v.height}" fill="white"/>',text_svg(40,65,v.name,v.width-80,30,'start',bold=True)]
    bx,by,bw,bh=v.boundary
    svg += [f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" fill="#fff" stroke="#71839a" stroke-width="2"/>',text_svg(bx+24,by+40,'FashionStore SaaS — límite del sistema',bw-45,22,'start',bold=True)]
    label_edges=[]
    for e in v.edges:
        s,t=v.nodes[e['source']],v.nodes[e['target']];pts=e['waypoints'];a=clipped(s,pts[0] if pts else center(t));b=clipped(t,pts[-1] if pts else center(s))
        poly=[a]+pts+[b];k=e['kind'];color=GREEN if k=='include' else PURPLE if k=='extend' else '#a0acb8'
        attrs=f'fill="none" stroke="{color}" stroke-width="{2.3 if k in ("include","extend") else 1}"'
        if k!='association':attrs+=f' marker-end="url(#{k})"'
        if k in ('include','extend'):attrs+=' stroke-dasharray="7 5"'
        svg.append('<polyline points="'+' '.join(f'{x:.1f},{y:.1f}' for x,y in poly)+'" '+attrs+'/>')
        if k in ('include','extend'):
            if e['labelpos']:x,y=e['labelpos']
            else:
                mid=len(poly)//2;x,y=(poly[mid-1][0]+poly[mid][0])/2,(poly[mid-1][1]+poly[mid][1])/2
            label_edges += [f'<rect x="{x-65:.1f}" y="{y-14:.1f}" width="130" height="28" rx="4" fill="white"/>',text_svg(x,y+5,'«'+k+'»',160,17,color=color)]
    for key,n in v.nodes.items():
        x,y,w,h=n['x'],n['y'],n['w'],n['h'];cx,cy=center(n)
        if n['kind']=='uc':svg += [f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{w/2}" ry="{h/2}" fill="{BLUE}" stroke="#456787" stroke-width="1.8"/>',text_svg(cx,cy-4,case_id(n['n'])+'\n'+n['label'],w*.86,18,bold=True)]
        else:
            svg += [f'<g fill="none" stroke="{INK}" stroke-width="2.5"><circle cx="{cx:.1f}" cy="{y+15}" r="12"/><path d="M{cx} {y+27} V{y+62} M{cx-27} {y+41} H{cx+27} M{cx} {y+62} L{cx-23} {y+89} M{cx} {y+62} L{cx+23} {y+89}"/></g>',text_svg(cx,y+115,n['label'],235,18)]
    svg+=label_edges
    for x,y,w,h,label in v.notes:
        svg += [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="#f4f7fa" stroke="#c4d1de"/>',text_svg(x+20,y+h/2,label,w-40,18,'start',color='#425268')]
    svg.append('</svg>')
    target=OUT/'vistas'/f'{i:02d}_vista.svg';target.write_text(''.join(svg),encoding='utf-8')

def validate(target,all_views):
    seen=[n for _,_,old,_,_,_ in CASES for n in old]
    assert sorted(seen)==list(range(1,39)) and len(seen)==len(set(seen))
    assert len(CASES)==20 and len(RELATIONS)==6
    doc=ET.parse(target);reports=[]
    for i,page in enumerate(doc.findall('diagram')):
        cells=page.findall('./mxGraphModel/root/mxCell');ids=[c.get('id') for c in cells];assert len(ids)==len(set(ids))
        for c in cells:
            if c.get('edge')=='1':assert c.get('source') in ids and c.get('target') in ids
        uc=[c for c in cells if c.get('id','').startswith('u_')]
        assert len(uc)==len([n for n in all_views[i].nodes.values() if n['kind']=='uc'])
        bx,by,bw,bh=all_views[i].boundary
        for n in all_views[i].nodes.values():
            if n['kind']=='uc':assert bx<n['x'] and by<n['y'] and n['x']+n['w']<bx+bw and n['y']+n['h']<by+bh
            else:assert n['x']+n['w']<bx or n['x']>bx+bw
        reports.append(dict(pagina=page.get('name'),casos=len(uc),actores=sum(n['kind']=='actor' for n in all_views[i].nodes.values()),relaciones=sum(c.get('edge')=='1' for c in cells)))
    assert {c.get('id') for c in doc.findall('./diagram[1]/mxGraphModel/root/mxCell') if c.get('id','').startswith('u_')}=={'u_'+str(i) for i in range(1,21)}
    (OUT/'VALIDACION_MODELO.json').write_text(json.dumps({'xml_parseable':True,'cu_principales':20,'cu_anteriores_cubiertos':38,'cu_anteriores_omitidos':[],'relaciones_include':4,'relaciones_extend':2,'actores_fuera_del_limite':True,'vistas':reports,'nota':'Validación estructural; se complementa con apertura y revisión visual.'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def main():
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'vistas').mkdir(exist_ok=True)
    cases=data();write_catalog(cases);write_document(cases)
    all_views=views();target=write_drawio(all_views)
    for i,v in enumerate(all_views,1):write_svg(v,i)
    validate(target,all_views)
    print('Modelo generado:',target)
    print('20 CU principales; 38 CU anteriores cubiertos; 6 vistas; 4 include y 2 extend.')

if __name__=='__main__':main()
