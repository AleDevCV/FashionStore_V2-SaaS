# CAPÍTULO II. ANÁLISIS DE REQUISITOS

Versión documental con 20 casos de uso principales. Las 38 capacidades del inventario anterior se conservan mediante la tabla de equivalencias. Este capítulo describe requisitos; la consolidación no certifica implementación ni pruebas nuevas.

## 2.1. Descripción del sistema propuesto

FashionStore se propone como una plataforma de comercio electrónico web y móvil para empresas que comercializan prendas de vestir. Su organización como servicio SaaS permite ofrecer una base tecnológica compartida, conservando espacios de operación separados para cada negocio. Una empresa administra sus sucursales, empleados, catálogo, proveedores, inventarios y transacciones de acuerdo con el plan contratado.

El servicio distingue la administración de plataforma de la administración empresarial. El superadministrador gestiona empresas, planes y contratos; los administradores empresariales y su personal actúan dentro de su organización y de las sucursales autorizadas. El acceso se realiza mediante correo y contraseña. Los clientes disponen de una cuenta común para distintas tiendas, pero cada compra, reserva y solicitud mantiene su pertenencia comercial y sus restricciones de acceso.

La operación combina consultas y registros centrales con almacenamiento local. La aplicación Angular incorpora capacidades PWA e IndexedDB, mientras Flutter utiliza SQLite. Cuando no existe conexión, los usuarios autorizados consultan la información descargada y registran reservas o ventas de contado según su rol. Estos registros se conservan como operaciones provisionales, con identificación y estado, hasta que el servidor pueda validarlos. La sincronización comunica confirmaciones, rechazos y conflictos sin eliminar registros por el solo intento de envío.

La plataforma mantiene los procesos del comercio de prendas, desde su clasificación y abastecimiento hasta las reservas, el checkout, la caja presencial y los cambios. Conserva el vestidor existente y las recomendaciones, e incorpora reportes por lenguaje natural y analítica basada en modelos supervisados y no supervisados. Los reportes consultan datos comerciales autorizados; los conjuntos sintéticos utilizados para entrenamiento se identifican por separado.

La solución se integra mediante una API REST con FastAPI y PostgreSQL central. Su validación considera al menos dos empresas independientes, las aplicaciones web y móvil, la persistencia local, la consistencia del inventario y la trazabilidad entre requisitos, casos de uso y evidencias.

## 2.2. Identificación de actores

Un actor representa un papel externo que interactúa con FashionStore; no equivale necesariamente a una persona o a una tabla. Una persona puede desempeñar varios papeles si sus permisos lo permiten. Las asociaciones indican participación, sin otorgar por sí solas todos los permisos del caso.

| Actor | Participación y límite |
|---|---|
| Usuario de la plataforma | Actor general de quienes disponen de cuenta. Acceso y recuperación; no otorga permisos comerciales por sí mismo. |
| Personal de empresa | Actor general del personal empresarial. Sus especializaciones conservan permisos y sucursales asignados. |
| Superadministrador SaaS | Administra empresas, planes y contratos, y consulta auditoría de plataforma. No se le concede acceso indiscriminado a datos comerciales. |
| Administrador de empresa | Configura personal, catálogo y operación de su empresa. Consulta su contrato; no edita planes globales. |
| Encargado de sucursal | Atiende operaciones, reservas, cambios y conflictos dentro de las sucursales y permisos asignados. |
| Vendedor o cajero | Registra ventas, atiende clientes y utiliza operaciones offline y sincronización autorizadas. |
| Responsable de inventario y compras | Gestiona catálogo autorizado, proveedores, recepciones y movimientos de existencias. |
| Cliente | Cuenta única entre tiendas; compra, reserva y consulta solo sus datos y solicitudes en el contexto correspondiente. |
| Visitante | Consulta tiendas y catálogo público. Requiere cuenta para efectuar operaciones privadas. |
| Responsable técnico de analítica | Prepara datasets, entrena, evalúa y versiona modelos en herramientas técnicas. No es un permiso automático del administrador empresarial. |
| Pasarela de pagos | Procesa pagos y reembolsos de prueba e informa resultados verificables; no es un usuario humano del sistema. |
| Servicio de IA | Interpreta solicitudes y apoya recomendaciones mediante contratos controlados; no recibe acceso irrestricto a PostgreSQL. |
| Servicios de correo y push | Transportan recuperación y avisos; la aplicación conserva sus notificaciones e historial propios. |

Usuario de la plataforma y Personal de empresa son actores generales. Superadministrador, Cliente y Personal especializan al primero; Administrador, Encargado, Cajero y Responsable de inventario especializan a Personal. La herencia de participación no elimina las restricciones de rol, propiedad o sucursal. El backend, la base de datos y el almacenamiento local son componentes internos, no actores externos.

## 2.3. Requisitos funcionales y no funcionales

### 2.3.1. Requisitos funcionales

Los requisitos se expresan como capacidades observables. Su agrupación en 20 casos principales organiza la documentación; cada grupo conserva sus subflujos y criterios de aceptación.

| ID | Requisito funcional | Caso principal |
|---|---|---|
| RF-01 | El sistema deberá registrar clientes globales, iniciar y cerrar sesión, recuperar contraseña y elegir tienda después del acceso del cliente. El personal mantiene su empresa asignada. | CU-01 |
| RF-02 | El sistema deberá aprovisionar empresas y su administrador, configurar planes y administrar vigencias, renovaciones y cambios. El administrador empresarial consulta únicamente su contrato. | CU-02 |
| RF-03 | El sistema deberá mantener empleados, roles, permisos y asignaciones de sucursal de la empresa. Impedir privilegios de plataforma y cambios en la identidad global de clientes. | CU-03 |
| RF-04 | El sistema deberá mantener ciudades y sucursales, su estado y responsables, respetando el cupo de sucursales activas de la suscripción. | CU-04 |
| RF-05 | El sistema deberá crear y mantener fichas comerciales por empresa. El cliente consulta su propia información e historial entre tiendas; la tienda accede solo al perfil y operaciones de su ámbito. | CU-05 |
| RF-06 | El sistema deberá mantener categorías, temporadas, colecciones, prendas, tallas, combinaciones de colores, material, medidas, precios y ofertas. | CU-06 |
| RF-07 | El sistema deberá administrar proveedores y compras; confirmar recepciones físicas con sus detalles y entradas de inventario. Mantener separados los subflujos de proveedor, pedido y recepción. | CU-07 |
| RF-08 | El sistema deberá obtener existencias físicas, unidades retenidas y disponibilidad por sucursal y variante. El mismo comportamiento de consulta se reutiliza al confirmar una venta. | CU-08 |
| RF-09 | El sistema deberá consultar catálogo y filtros, variantes y disponibilidad; utilizar opcionalmente el vestidor existente y las recomendaciones sobre prendas de la tienda elegida. | CU-09 |
| RF-10 | El sistema deberá registrar entradas, salidas, ajustes y transferencias autorizadas. Reutilizar el registro de salida en ventas confirmadas sin descontar stock por un segundo mecanismo. | CU-10 |
| RF-11 | El sistema deberá administrar carrito y checkout hasta la confirmación de una compra pagada. La pasarela informa el resultado firmado; un pedido o pago pendiente no confirma una venta. | CU-11 |
| RF-12 | El sistema deberá registrar y consultar reservas centrales, preparar prendas, cancelar, vencer y entregar según sus transiciones. El cliente opera solo sobre sus reservas. | CU-12 |
| RF-13 | El sistema deberá consolidar una venta presencial autorizada con importes calculados por el servidor, efectivo y vuelto, registro comercial, salida única de stock y auditoría. | CU-13 |
| RF-14 | El sistema deberá emitir o recuperar la representación del comprobante de una venta confirmada, consultarla y descargarla con autorización. La consulta/descarga es opcional respecto al cierre de compra. | CU-14 |
| RF-15 | El sistema deberá solicitar, consultar y atender cambios: elegibilidad, recepción física, reemplazo, diferencias de precio, devolución de importes, notificaciones y entrega. | CU-15 |
| RF-16 | El sistema deberá ofrecer una PWA instalable en navegadores compatibles y almacenamiento persistente en web y móvil para descargar catálogo, consultar datos conocidos, registrar reservas o ventas de contado según rol y recuperar los pendientes después de reiniciar. | CU-16 |
| RF-17 | El sistema deberá enviar pendientes manual o automáticamente, recuperar resultados y tratar conflictos. El autor consulta sus operaciones; una resolución comercial requiere el permiso correspondiente. | CU-17 |
| RF-18 | El sistema deberá consultar reportes convencionales o solicitarlos por texto/voz mediante IA, con filtros variables y datos reales autorizados; representar y exportar resultados a PDF/XLSX. | CU-18 |
| RF-19 | El sistema deberá permitir preparar datos sintéticos y variables, entrenar y evaluar modelos supervisados y no supervisados, versionar los artefactos y consultar indicadores, predicciones y segmentos del tenant autorizado, diferenciando los subflujos técnico y empresarial. | CU-19 |
| RF-20 | El sistema deberá consultar eventos autorizados de acceso y operaciones, pagos, cambios y sincronización. La plataforma consulta su ámbito técnico y SaaS sin acceso comercial irrestricto a empresas. | CU-20 |

### 2.3.2. Requisitos no funcionales

| ID | Criterio de calidad | Comprobación requerida |
|---|---|---|
| RNF-01 | Seguridad de acceso | Comprobar identidad, permisos y propiedad en cada operación privada; rechazar sesiones revocadas. |
| RNF-02 | Separación empresarial | Impedir lecturas y escrituras entre empresas incluso al alterar manualmente identificadores o parámetros. |
| RNF-03 | Persistencia local | Recuperar reservas, ventas y pendientes después de un cierre y reinicio normal de navegador o aplicación. |
| RNF-04 | Consistencia transaccional | Confirmar juntos cabecera, detalles y movimientos; un fallo intermedio debe revertir el conjunto. |
| RNF-05 | Reenvío seguro | Procesar repetidamente un UUID confirmado sin crear ventas, pagos o movimientos adicionales. |
| RNF-06 | Recuperación de comunicación | Conservar datos y permitir reintentar después de timeout, desconexión o respuesta perdida. |
| RNF-07 | Mantenibilidad | Separar presentación, negocio, persistencia y sincronización, con componentes y contratos identificables. |
| RNF-08 | Compatibilidad | Verificar instalación PWA en navegador compatible y persistencia Flutter en Android; no prometer soporte universal de APIs offline. |
| RNF-09 | Uso de recursos | Paginar consultas, limitar lotes y medir latencia, errores y memoria bajo condiciones de prueba documentadas. |
| RNF-10 | Observabilidad | Registrar UUID, responsable, estado, intentos y motivo de conflicto, sin almacenar secretos en evidencias o logs. |
| RNF-11 | Verificación de calidad | Disponer de pruebas reproducibles de aislamiento, inventario, sincronización, planes y reglas comerciales críticas. |
| RNF-12 | Correspondencia documental | Relacionar requisitos, CU, componentes, pruebas y diagramas con una versión identificada de la solución. |

## 2.4. Reglas de negocio

Se diferencian las condiciones del examen de las políticas adoptadas por el equipo. Los plazos de cambios, retenciones, vigencia offline y reembolsos son decisiones documentadas del proyecto, no plazos atribuidos a la guía ni a una normativa legal.

| ID | Regla | Origen | CU nuevos |
|---|---|---|---|
| RN-01 | La empresa es la unidad de aislamiento; sus sucursales son unidades operativas del mismo tenant. | Examen | 02, 04 |
| RN-02 | El contexto empresarial de operaciones privadas se obtiene de la sesión validada; no del prefijo del correo ni de un ID confiado al cliente. | Examen + diseño | 01 y transversal |
| RN-03 | Un correo identifica una cuenta global. El personal conserva su empresa; el cliente elige tienda después de entrar y solo accede a datos propios. | Decisión del proyecto | 01, 03, 05, 09 |
| RN-04 | El administrador empresarial no modifica planes globales ni la contraseña global del cliente, ni obtiene permisos de plataforma. | Diseño de autorización | 02, 03, 05 |
| RN-05 | El plan Básico admite inicialmente dos sucursales activas y Profesional diez; los límites son configurables y se validan también al reactivar y ante concurrencia. | Examen + diseño | 02, 04 |
| RN-06 | Los reportes convencionales están en ambos planes; los generativos requieren Profesional y autorización del usuario. | Examen | 02, 18 |
| RN-07 | Una suscripción vencida conserva historial y pendientes; bloquea nuevas operaciones comerciales y permite consultar su estado y gestionar renovación. | Política del proyecto | 02, 16, 17 |
| RN-08 | El cambio a un plan menor se rechaza mientras existan más sucursales activas que las permitidas por el destino. | Política del proyecto | 02, 04 |
| RN-09 | Los importes se recalculan en el servidor. Se aplica el menor precio válido entre minorista, mayorista y oferta, sin acumular descuentos; el umbral mayorista inicial es seis unidades de la misma prenda y es configurable. | Política del proyecto | 06, 11, 12, 13 |
| RN-10 | La disponibilidad central se calcula restando retenciones vigentes a las existencias físicas; no se confirma una salida que produzca stock negativo. | Examen + diseño | 08, 10, 11, 12, 13, 17 |
| RN-11 | La reserva central aceptada retiene disponibilidad por 24 horas; al cancelar o vencer se libera. La reserva offline es provisional. | Política del proyecto | 12, 16, 17 |
| RN-12 | Preparar una reserva, añadir al carrito o mantener un pago pendiente no constituye una venta confirmada ni acredita un cobro. | Regla comercial del proyecto | 11, 12, 13 |
| RN-13 | Solo se confirma un pago electrónico por resultado verificable del proveedor y por el importe autorizado; los reenvíos no duplican su efecto. | Examen + diseño | 11, 15 |
| RN-14 | Cada entrada o salida de stock se aplica una sola vez mediante el mecanismo de movimientos del sistema. | Examen + diseño | 07, 10, 11, 13, 15, 17 |
| RN-15 | El comprobante corresponde a una venta confirmada y a su empresa; la consulta o descarga exige autorización y no crea otro documento comercial. | Diseño del proyecto | 14 |
| RN-16 | El modo offline exige autenticación previa y datos descargados. La autorización local tendrá vigencia máxima de 24 horas, limitada por la suscripción conocida. | Examen + política del proyecto | 16 |
| RN-17 | Las ventas offline son de contado; recibir efectivo localmente no garantiza aceptación central. Ante rechazo se requiere resolución o compensación documentada. | Examen + diseño | 16, 17 |
| RN-18 | Una operación conserva UUID, autor, empresa, sucursal y contenido entre intentos. El mismo UUID con otro contenido se rechaza. | Examen + diseño | 16, 17 |
| RN-19 | Un envío o cierre de sesión no elimina pendientes. Un lote informa un resultado por operación y conserva los demás registros aunque uno falle. | Examen + diseño | 01, 16, 17 |
| RN-20 | Stock insuficiente, cambio de precio o variante inactiva generan un resultado explícito de conflicto; no se acepta parcialmente una venta. La revocación de permisos impide confirmar. | Política del proyecto | 17 |
| RN-21 | Corregir un conflicto crea una operación nueva enlazada a la original, sin ocultar el historial ni reemplazar silenciosamente el efectivo registrado. | Diseño del proyecto | 17 |
| RN-22 | El cambio de prenda se solicita hasta siete días calendario desde la entrega, con compra comprobable, prenda elegible sin uso y una única sustitución por unidad. | Política del proyecto; el examen exige definir un plazo | 15 |
| RN-23 | La recepción de la prenda y la entrega del reemplazo son eventos separados. El crédito usa el importe efectivamente pagado; las diferencias se cobran o devuelven íntegramente. | Política del proyecto | 15 |
| RN-24 | Sin reemplazo disponible se conserva la solicitud y se permite cancelar con devolución del crédito. El reembolso sigue el medio original y un objetivo administrativo de cinco días hábiles. | Política del proyecto | 15 |
| RN-25 | Los reportes comerciales consultan datos reales del tenant autorizado. La IA interpreta parámetros; el backend valida y ejecuta operaciones permitidas, sin SQL libre del modelo. | Examen + diseño | 18 |
| RN-26 | Texto y voz deben permitir solicitudes variables; se demostrarán al menos cuatro tipos de reportes. PDF y XLSX deben corresponder a los resultados autorizados mostrados. | Examen | 18 |
| RN-27 | La analítica incluye aprendizaje supervisado y no supervisado, preparación de variables, evaluación e integración. Los datos sintéticos se identifican; una predicción no se presenta como una venta real. | Examen + diseño | 19 |
| RN-28 | Consultar el dashboard usa artefactos ya evaluados; el entrenamiento es un subflujo técnico separado y se ejecuta fuera del servidor de producción. | Decisión técnica del proyecto | 19 |

## 2.5. Diagrama UML de casos de uso

### 2.5.1. Modelos de casos de uso

El modelo general representa 20 casos principales y los actores que participan en sus objetivos. Para facilitar lectura y exposición se incluyen cinco vistas complementarias por área dentro del mismo archivo draw.io. Las vistas reutilizan los mismos identificadores; no introducen casos nuevos.

El límite del sistema contiene los casos de uso y mantiene los actores fuera. Las elipses representan objetivos funcionales y las líneas continuas, participación. La generalización de actores utiliza una línea continua con triángulo hueco dirigido al actor general.

**Relación «include».** Una flecha discontinua parte del caso base hacia el comportamiento que necesita ejecutar. En el flujo exitoso de compra o venta, la consulta de disponibilidad y el registro de salidas son comportamientos reutilizados. Las validaciones y los movimientos se ejecutan dentro de la transacción comercial correspondiente; el diagrama no propone dos descuentos de inventario.

**Relación «extend».** La flecha discontinua parte de la extensión hacia el caso base. En este modelo, CU-14 representa obtener la representación del comprobante a solicitud del usuario después de confirmar una compra o venta. La venta puede cerrar y conservar su registro comercial aunque el usuario no descargue el documento; la representación puede generarse o recuperarse después.

| Relación | Origen → destino | Justificación o condición |
|---|---|---|
| «include» | CU-11 → CU-08 | Consulta obligatoria de existencias para validar la compra central. |
| «include» | CU-11 → CU-10 | Salida obligatoria al confirmar una compra pagada; el checkout abandonado o pendiente no alcanza este punto. |
| «include» | CU-13 → CU-08 | Consulta obligatoria de existencias antes de confirmar una venta presencial. |
| «include» | CU-13 → CU-10 | Una venta presencial confirmada registra su salida en la misma transacción. |
| «extend» | CU-14 → CU-11 | Punto: compra confirmada. Condición: el usuario solicita visualizar o descargar su comprobante. |
| «extend» | CU-14 → CU-13 | Punto: venta registrada. Condición: el usuario solicita visualizar o descargar su comprobante. |

La autenticación se establece como precondición de las operaciones privadas; no se dibuja un «include» hacia iniciar sesión desde cada caso. Tampoco se usa «include» para expresar orden temporal: registrar sin conexión no ejecuta necesariamente la sincronización en ese momento. La resolución de conflictos es un subflujo condicionado de CU-17, y entrenar modelos es un subflujo técnico de CU-19 que no se ejecuta al consultar el dashboard.

### Catálogo consolidado y equivalencia con los 38 CU

| CU nuevo | Nombre | CU anteriores absorbidos |
|---|---|---|
| CU-01 | Gestionar acceso y cuenta | CU-01, CU-02 |
| CU-02 | Administrar empresas, planes y suscripciones | CU-03, CU-04, CU-05 |
| CU-03 | Administrar personal, roles y permisos | CU-06, CU-07 |
| CU-04 | Gestionar ciudades y sucursales | CU-08 |
| CU-05 | Gestionar fichas de clientes | CU-09 |
| CU-06 | Administrar catálogo de prendas | CU-10, CU-11, CU-12 |
| CU-07 | Gestionar proveedores, compras y recepciones | CU-13, CU-14 |
| CU-08 | Consultar inventario y disponibilidad | CU-15 |
| CU-09 | Explorar catálogo y asistencia de compra | CU-17, CU-26, CU-27 |
| CU-10 | Registrar movimientos de inventario | CU-16 |
| CU-11 | Realizar compra y pago en línea | CU-18, CU-22 |
| CU-12 | Gestionar reservas de prendas | CU-19, CU-20 |
| CU-13 | Registrar venta presencial | CU-21 |
| CU-14 | Obtener comprobantes de compra | CU-23 |
| CU-15 | Gestionar cambios y reembolsos | CU-24, CU-25 |
| CU-16 | Registrar y consultar operaciones offline | CU-28, CU-29, CU-30, CU-31 |
| CU-17 | Sincronizar operaciones y resolver conflictos | CU-32, CU-33 |
| CU-18 | Obtener reportes comerciales | CU-34, CU-35 |
| CU-19 | Preparar y consultar analítica inteligente | CU-36, CU-37 |
| CU-20 | Consultar auditoría y trazabilidad | CU-38 |

### Criterio de consolidación

Los casos principales agrupan objetivos de una misma área y mantienen subflujos separados. Por ejemplo, CU-02 conserva aprovisionamiento empresarial, configuración de planes y gestión de contratos; CU-16 conserva preparación de datos, reserva local, venta local y consulta de pendientes. CU-19 diferencia entrenamiento técnico y consulta empresarial. No se ejecutan todos estos subflujos cada vez que un actor participa.

La nueva numeración es documental. La equivalencia distingue los 38 CU del plan P2 anterior y los antecedentes del primer parcial. Los comentarios heredados del código pueden utilizar la numeración del P1, que no debe confundirse con la del plan de 38 CU. No se cambian IDs comerciales, rutas ni métodos por esta consolidación. Antes del cierre documental deberán utilizarse los nuevos IDs de forma coherente en fichas, diagramas y matriz, manteniendo ambos vínculos históricos.

La reducción no garantiza por sí sola una disminución proporcional del trabajo: cada regla, alternativa y prueba debe seguir documentada. La guía no establece un total de 38 CU; esta cantidad provenía del desglose inicial del equipo.

## Archivos de apoyo

- `FashionStore_Casos_de_Uso_20.drawio`: modelo editable de seis páginas.
- `CU_20_catalogo.json`: definición estructurada de los 20 casos y sus flujos.
- `equivalencias_38_a_20.csv`: cobertura completa de los 38 identificadores históricos.
- `FICHAS_RESUMIDAS_20_CU.md`: objetivo, actores, cobertura y flujo principal de cada caso.
- Carpeta `vistas/`: SVG y PNG de cada vista.

## Referencias del modelo

- Examen Parcial-2 (IMPORTANTE) - Sistemas 2 - S2-2026.pdf, páginas 2–10.
- Plan del proyecto: inventario histórico de 38 CU.
- Decisiones del equipo: cuenta global de cliente, políticas comerciales y despliegue nativo.
- OMG UML 2.5.1: https://www.omg.org/spec/UML/2.5.1
- Formato draw.io: https://www.drawio.com/docs/reference/diagram-generation/
