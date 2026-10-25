# Plan maestro del Parcial 2: FashionStore SaaS



## 1. Punto de partida y decisiones confirmadas



El objetivo es **evolucionar FashionStore**, conservando su funcionalidad anterior e incorporando SaaS multitenant, suscripciones, operación offline en Angular y Flutter, sincronización segura, cambios de prendas, reportes generativos y analítica con Machine Learning.



La fuente principal es :codex-file-citation{path="C:Sistemas_Informacion2-Parcial2CONTEXTOExamen Parcial-2 (IMPORTANTE) - Sistemas 2 - S2-2026.pdf" purpose="source"}. El antecedente es :codex-file-citation{path="C:UsersMSI LAPTOPDownloadsExamen1-Ecommerce-Si2-s2-26 (2).pdf" purpose="source"}.



Se revisaron los doce archivos de `CONTEXTO`, contrastando resúmenes con transcripciones y documentos originales. Los audios se analizaron mediante sus transcripciones y una retranscripción complementaria de segmentos omitidos, incluidos los primeros 4:29 del segundo audio. Los fragmentos de reconocimiento dudoso no se convertirán en requisitos.



**Estado comprobado:**



- Las tres carpetas `Parcial2_*` están vacías; la raíz nueva todavía no tiene repositorio Git.

- El código reutilizable está en [el proyecto del primer parcial](<C:/SISTEMAS DE INFORMACION 2>).

- Existen funciones de catálogo, compras, inventario, reservas, POS, pagos, comprobantes, aplicaciones móviles, recomendaciones y reportes generativos. Deben adaptarse y probarse.

- PWA con IndexedDB, SQLite móvil, multitenencia y suscripciones sí requieren desarrollo nuevo.

- El servidor tiene Debian 13, dos CPU y aproximadamente 2 GB de RAM. Tiene servicios de otra aplicación activos y todavía no tiene Docker.

- Ambos accesos SSH indicados funcionan. La carpeta de P2 existe y está vacía.



| Decisión | Criterio adoptado |

|---|---|

| Orden de trabajo | Teoría y especificaciones → código por CU en orden → diagramas técnicos finales. |

| Dedicación | Dos personas, entre cuatro y seis horas diarias por persona. |

| Producción | V2 separada; destino propuesto `fashionstore-v2.aledevcv.me`. |

| Datos | Demostración nueva con dos empresas; migración del P1 probada sobre una copia. |

| Cambios de prendas | Siete días, prenda sin uso, una vez por unidad; cobrar o devolver la diferencia correspondiente. |

| GitHub | Respaldo manual en el repositorio indicado. Prohibidos `git push`, automatizaciones de publicación y escrituras equivalentes mediante API sin nueva instrucción tuya. |



**Diferencia metodológica que queda registrada:** la docente pide modelos anteriores al código y modelos de datos para la primera presentación. Mantendremos tu elección de diagramas técnicos al final, pero no presentaremos esa secuencia como cumplimiento completo de esa indicación. La primera entrega tendrá ese pendiente explícito.



También se documentará el despliegue como **servidor propio accesible públicamente mediante HTTPS**. El acceso SSH por sí solo no cumple la accesibilidad externa de la aplicación; tampoco se afirmará que el servidor doméstico equivale literalmente al requisito de nube.



## 2. Primera etapa: documentación teórica y preparación



### Documento principal



Se seguirá exactamente el índice del examen. El documento será autosuficiente: incluirá los CU heredados necesarios para entender la solución actual y su correspondencia con el P1.



| Parte | Trabajo previo al código | Cierre posterior |

|---|---|---|

| Capítulo I | Introducción de una página, problema, objetivos propios, justificación, alcance, limitaciones y metodología. | Ajustar afirmaciones a lo realmente entregado. |

| Capítulo II | Actores, RF, los doce RNF, reglas de negocio, tabla maestra, diagramas de CU y especificaciones. | Incorporar cambios aprobados durante implementación. |

| Capítulo III | Glosario del dominio, decisiones de datos, contratos y prototipos de interfaz. | Completar modelos y diagramas técnicos mediante verificación del código. |

| Capítulo IV | Estructura prevista de tecnologías, arquitectura y módulos. | Describir implementación, integración y despliegue reales. |

| Capítulo V | Plan de pruebas y criterios de aceptación. | Agregar resultados, evidencias y correcciones. |

| Capítulo VI | Estructura preparada. | Redactar conclusiones y recomendaciones después de verificar resultados. |

| Bibliografía y anexos | Referencias y antecedentes relevantes del P1. | Añadir manuales, evidencias, inventarios y material de defensa. |



Formato de trabajo: fuentes editables versionadas, documento final Word y PDF, estilo APA 7 como criterio del proyecto. El índice no se organizará en “Iteración 1, 2, 3”.



### Actores



Se definirán los siguientes actores con permisos diferenciados:



- Superadministrador de la plataforma.

- Administrador de empresa.

- Encargado de sucursal.

- Vendedor o cajero.

- Responsable de inventario y compras.

- Cliente.

- Servicios externos de pagos, IA y notificaciones, cuando participen en un CU.



El superadministrador gestiona empresas y planes; no obtiene acceso comercial indiscriminado a los datos de cada empresa.



### Especificación obligatoria por CU



Cada ficha contendrá:



- Identificador secuencial desde `CU-01`, nombre, autor y fecha.

- Objetivo, actores, plataforma y relación con el CU anterior.

- Precondiciones, disparador y postcondiciones.

- Flujo principal y alternativos.

- Validaciones y reglas de negocio.

- Comportamiento ante desconexión, cuando corresponda.

- Prototipo y diagrama de CU.

- Criterios de aceptación y pruebas asociadas.



Se preparará una matriz:



**Fuente → requisito → regla → CU → componente/API → prueba → evidencia → diagrama.**



Los estados serán `pendiente`, `especificado`, `implementado`, `probado` y `documentado`. Un CU no se marcará terminado únicamente porque su pantalla exista.



### Preparación del proyecto



En [la carpeta de trabajo](<C:/Sistemas_Informacion2-Parcial2>) se conservarán las tres carpetas elegidas y se añadirán directorios para documentación, infraestructura, pruebas integrales y resultados de ingeniería inversa.



La incorporación del P1 será selectiva:



- Copiar fuentes, recursos necesarios, manifiestos y archivos de dependencias.

- Excluir repositorios `.git` internos, entornos virtuales, dependencias descargadas, compilaciones, cachés y secretos.

- Mantener intacto el proyecto original.

- Crear un único repositorio local para P2.

- Preparar configuración de ejemplo, instrucciones de arranque y variables separadas por ambiente.

- Revisar las pruebas heredadas antes de ejecutarlas: actualmente contienen limpiezas de base de datos que deben quedar limitadas a una base exclusiva de pruebas.



No se añadirá como alcance obligatorio implementar otras pasarelas o rehacer el vestidor: los resúmenes confunden algunas investigaciones del P1 con obligaciones de implementación.



## 3. Diseño técnico y reglas que guiarán la implementación



### 3.1. Arquitectura y servicios



Se conservará el stack existente:



| Componente | Decisión |

|---|---|

| Backend | FastAPI, Pydantic y acceso PostgreSQL existente con `psycopg2`. |

| Web | Angular existente, agregando Service Worker, manifest e IndexedDB mediante Dexie. |

| Móvil | Flutter existente, agregando SQLite mediante `sqflite`. |

| Base central | PostgreSQL 16 compartido con aislamiento por empresa. |

| Reportes | Ampliación del módulo existente; Gemini interpreta solicitudes estructuradas. |

| ML | `scikit-learn`; entrenamiento local y artefactos versionados para inferencia. |

| Pagos | Stripe en modo de prueba, conservando y corrigiendo la integración anterior. |

| Exportación | PDF y XLSX desde resultados autorizados del backend. |

| Notificaciones | Bandeja persistente y push a Android mediante Firebase Cloud Messaging. |

| Ejecución | Docker Compose para backend, PostgreSQL y web; Flutter se ejecuta en dispositivo o emulador. |



Se mantendrá un backend modular. No se añadirá una migración general a ORM, microservicios, Kubernetes ni una cola externa.



El Service Worker cubrirá los recursos de la aplicación; la persistencia comercial y la cola de operaciones tendrán implementación propia. Angular describe su Service Worker como una herramienta de caché básica, por lo que instalarlo no resuelve por sí solo las ventas offline. [Documentación de Angular](https://angular.dev/ecosystem/service-workers).



### 3.2. Multitenencia y seguridad



La unidad de aislamiento será la **empresa**, no la sucursal.



Implementación:



1. Incorporar empresas, planes, suscripciones y pertenencia de usuarios.

2. Clasificar todas las tablas como globales o pertenecientes a un tenant.

3. Agregar `tenant_id` obligatorio a los datos comerciales y sus detalles.

4. Adaptar unicidades, índices y relaciones para que SKU, clientes, proveedores y documentos puedan existir independientemente en distintas empresas.

5. Obtener el tenant desde el contexto autenticado; no confiar en un identificador enviado por la interfaz.

6. Comprobar también rol, sucursal y propiedad del recurso.

7. Proteger archivos y comprobantes mediante descargas autorizadas; eliminar su exposición privada mediante rutas estáticas públicas.

8. Separar el catálogo público de cada empresa mediante su identificador legible en la URL.



Se utilizarán filtros explícitos y Row-Level Security como segunda barrera. El usuario de base de datos de la aplicación no será propietario ni tendrá `BYPASSRLS`; el contexto se fijará con `SET LOCAL` dentro de cada transacción para evitar contaminación entre conexiones reutilizadas. PostgreSQL documenta que propietarios y roles especiales pueden eludir RLS, por lo que esa configuración forma parte de la prueba. [Documentación de PostgreSQL](https://www.postgresql.org/docs/16/ddl-rowsecurity.html).



**Migración:**



- Probar primero sobre una copia del P1.

- Asociar sus datos a una empresa inicial.

- Verificar cantidades, relaciones, importes e inventario antes y después.

- Crear otra empresa con datos independientes.

- Publicar finalmente una base de demostración reproducible, sin datos personales ni credenciales heredadas.



### 3.3. Planes y suscripciones



| Capacidad | Básico | Profesional |

|---|---:|---:|

| Sucursales activas | 2 | 10 |

| Productos, ventas y reservas | Sí | Sí |

| Operación offline | Sí | Sí |

| Reportes convencionales | Sí | Sí |

| Reportes generativos | No | Sí |



Los límites serán configurables en el backend.



Reglas:



- Contratación y renovación administrativas, sin cobro recurrente SaaS.

- Controlar el límite al crear y reactivar sucursales, incluyendo solicitudes concurrentes.

- Impedir un cambio a Básico mientras existan más de dos sucursales activas.

- Una suscripción vencida permite consultar historial y gestionar renovación, pero bloquea nuevas operaciones comerciales.

- Conservar todas las operaciones offline pendientes cuando cambie la suscripción.

- Una operación que ya no pueda aceptarse tendrá un resultado explícito; nunca desaparecerá de la cola.



### 3.4. Inventario, ventas y cambios de prendas



Se conservará un único mecanismo de movimientos de inventario. El P1 ya contiene un trigger de actualización; la sincronización no podrá descontar stock nuevamente por otro camino.



Reglas de comercio:



- Carrito y pedido sin pago no constituyen una venta confirmada.

- Separar reserva preparada, pago confirmado y entrega.

- Una reserva central aceptada retendrá disponibilidad durante 24 horas, con liberación al vencer o cancelar.

- Una reserva offline será provisional hasta su aceptación central.

- Venta offline exclusivamente de contado.

- El backend recalculará importes y validará precios y descuentos.

- Stock insuficiente o precio diferente del conocido generarán conflicto de la operación completa, sin aceptación parcial.

- Una venta con efectivo ya recibido que no pueda confirmarse requerirá resolución y constancia de compensación.



Reglas de catálogo derivadas de las aclaraciones docentes:



- Variantes por talla y combinaciones de colores.

- Descripción de material y medidas.

- Precio minorista y mayorista; umbral inicial de seis unidades de la misma prenda, configurable.

- Ofertas con vigencia y filtros.

- Aplicar el menor precio válido entre minorista, mayorista y oferta, sin acumular descuentos.



**Cambios y devoluciones:**



- Solicitud dentro de siete días calendario desde la entrega.

- Prenda sin uso, elegible y con compra comprobable.

- Un cambio por unidad adquirida.

- Recepción física y entrega del reemplazo como operaciones separadas.

- Reposición de stock solamente después de aceptar la prenda recibida.

- Crédito calculado con el precio efectivamente pagado.

- Reemplazo más caro: cobrar diferencia por pasarela antes de entregar.

- Reemplazo más barato: devolver íntegramente la diferencia.

- Reemplazo no disponible: conservar solicitud pendiente y permitir cancelación con devolución del crédito.

- Reembolso por el medio original; objetivo administrativo máximo de cinco días hábiles, registrado como política del proyecto.

- Atención inicialmente en la sucursal de la compra o entrega original.



La notificación push avisará disponibilidad y diferencia pendiente; también existirá una notificación persistente para no depender de que el dispositivo reciba el push. La integración móvil seguirá el cliente oficial de Firebase. [Documentación de FCM para Flutter](https://firebase.google.com/docs/cloud-messaging/flutter/get-started).



### 3.5. Persistencia offline y sincronización



Web y Flutter compartirán reglas y contrato REST, con almacenamiento diferente.



Se persistirán:



- Catálogo descargado, variantes, precios y existencias conocidas.

- Sucursales autorizadas y clientes mínimos necesarios.

- Cabeceras y detalles de reservas y ventas.

- Operaciones pendientes, intentos y resultados.

- Fecha de última actualización.



No habrá alta de usuarios ni procesamiento electrónico de pagos offline. Las reservas utilizarán clientes previamente disponibles; las ventas podrán utilizar un cliente mostrador propio de la empresa.



La sesión offline requerirá una autenticación previa y tendrá vigencia máxima de 24 horas, limitada además por la suscripción conocida. Los permisos se volverán a validar al sincronizar.



**Contrato mínimo:**



| Interfaz | Responsabilidad |

|---|---|

| `GET /api/contexto` | Usuario, empresa, permisos, sucursales y suscripción. |

| `GET /api/offline/catalogo` | Descargar catálogo autorizado, paginado y versionado. |

| `POST /api/sincronizacion/lote` | Procesar operaciones y devolver un resultado individual por cada una. |

| `GET /api/sincronizacion/operaciones/{uuid}` | Recuperar el resultado cuando se perdió una respuesta. |

| `/api/conflictos` | Consulta y resolución autorizada de conflictos. |

| `/api/empresas`, `/api/planes`, `/api/suscripciones` | Administración SaaS. |

| `/api/reportes`, `/api/analitica`, `/api/cambios` | Capacidades nuevas o ampliadas. |



Se conservará el prefijo `/api` y las rutas existentes compatibles.



Cada operación incluirá UUID estable, versión de contrato, dispositivo, empresa declarada, sucursal, autor, fecha local, detalles y precios conocidos. El servidor comprobará todos los datos de identidad contra la sesión.



Estados locales:



`PENDIENTE → ENVIANDO → CONFIRMADA / RECHAZADA / EN_CONFLICTO`



Reglas esenciales:



- UUID generado una sola vez; no cambiarlo al reintentar.

- Unicidad central por empresa y UUID.

- Mismo UUID y contenido: devolver el resultado anterior.

- Mismo UUID con contenido diferente: rechazar reutilización.

- Venta, detalles, movimiento, auditoría y resultado idempotente se confirman en una sola transacción.

- Timeout o error temporal conserva la operación pendiente.

- Una operación encontrada como `ENVIANDO` después de reiniciar vuelve a ser reintentable.

- Confirmadas conservan recibo e identificador del servidor.

- Corregir un conflicto crea una nueva operación enlazada a la original.

- Una operación inválida no impide procesar las demás del lote.

- Separar almacenamiento por empresa y usuario; cerrar sesión no elimina pendientes silenciosamente.

- Impedir que dos pestañas despachen simultáneamente la misma cola.



Habrá sincronización manual y automática al recuperar conectividad o abrir la aplicación. No dependerá exclusivamente de Background Sync, cuya disponibilidad varía entre navegadores. [Documentación de compatibilidad](https://developer.mozilla.org/en-US/docs/Web/API/Background_Synchronization_API).



### 3.6. Reportes generativos y Machine Learning



Se ampliará el módulo existente mediante este flujo:



**Texto o voz → intención estructurada validada → consulta permitida → datos reales → tabla/gráfico → exportación.**



La IA no ejecutará SQL libre ni recibirá credenciales de PostgreSQL. El backend impondrá tenant, permisos, filtros admitidos, límites y tiempo máximo de consulta.



Se implementarán seis tipos:



1. Ventas por sucursal y período.

2. Productos más vendidos.

3. Evolución de ventas por día, semana o mes.

4. Existencias bajas.

5. Ingresos por categoría.

6. Comparación de sucursales entre períodos.



Habrá solicitudes de aclaración para consultas ambiguas, mensajes para consultas no soportadas y resultados vacíos legítimos. PDF y XLSX utilizarán los mismos resultados autorizados de la pantalla.



La voz tendrá transcripción visible y editable. Reportes e IA requerirán conexión; su indisponibilidad no bloqueará las operaciones comerciales offline.



**ML será un módulo distinto del modelo generativo:**



- Generador reproducible de datos sintéticos con semilla fija.

- Datos separados y identificados como sintéticos.

- Modelo supervisado de demanda por producto y sucursal: `HistGradientBoostingRegressor`.

- División temporal de entrenamiento, validación y prueba; comparación contra una predicción simple basada en demanda reciente.

- Métricas MAE y RMSE.

- Modelo no supervisado: K-Means sobre variables RFM de clientes, con escalado, evaluación e interpretación de grupos.

- Artefactos con versión, variables, métricas y fecha de entrenamiento.

- Dashboard con indicadores comerciales, predicciones, segmentos y limitaciones.



El entrenamiento se ejecutará localmente. Los modelos iniciales se entrenarán únicamente con datos sintéticos; las consultas e inferencias comerciales se limitarán al tenant autorizado.



## 4. Orden completo de casos de uso



La siguiente numeración será la del P2. El vínculo con los CU anteriores quedará en la matriz de trazabilidad.



**W:** Angular web/PWA. **M:** Flutter. Todos los CU tendrán soporte backend cuando corresponda. No se duplicará en móvil toda la administración SaaS, pero se conservarán las capacidades móviles existentes.



| CU | Caso de uso | Plataforma | Resultado exigido para cerrarlo |

|---|---|---|---|

| 01 | Iniciar y cerrar sesión | W/M | Identidad, tenant, rol y sucursales correctos; separación de sesión y datos locales. |

| 02 | Recuperar contraseña | W/M | Recuperación segura y sin confundir cuentas de distintas empresas. |

| 03 | Administrar empresas | W | Alta, estado y administrador inicial; dos empresas independientes. |

| 04 | Configurar planes | W | Capacidades y límites editables y validados. |

| 05 | Gestionar suscripciones | W | Asignación, renovación, vencimiento y cambio de plan. |

| 06 | Gestionar roles y permisos | W | Permisos propios de empresa y separación respecto de la plataforma. |

| 07 | Administrar usuarios | W | Alta y asignación de roles y sucursales; revocación efectiva. |

| 08 | Gestionar ciudades y sucursales | W | Pertenencia a empresa y límites de sucursales activas. |

| 09 | Gestionar clientes | W | Fichas aisladas y control de acceso por propietario cuando corresponda. |

| 10 | Gestionar categorías | W | Catálogo de categorías propio de cada empresa. |

| 11 | Gestionar temporadas y colecciones | W | Vigencias y relaciones consistentes con prendas. |

| 12 | Gestionar prendas y variantes | W | Tallas, multicolores, material, medidas, precios y ofertas. |

| 13 | Gestionar proveedores | W/M | Proveedores independientes y acceso según rol. |

| 14 | Registrar compras y recepciones | W/M | Compra, detalles y entrada de stock consistentes. |

| 15 | Consultar inventario | W/M | Existencia física, reservada y disponible por sucursal. |

| 16 | Registrar movimientos de inventario | W/M | Entradas, salidas y transferencias trazables sin duplicaciones. |

| 17 | Consultar catálogo | W/M | Filtros, variantes, precios aplicables y disponibilidad del tenant. |

| 18 | Gestionar carrito y checkout | W/M | Totales calculados correctamente; sin consolidar venta antes del pago. |

| 19 | Registrar reservas online | W/M | Reserva de cliente, sucursal y variantes con retención controlada. |

| 20 | Preparar, entregar o cancelar reservas | W/M | Transiciones separadas; preparar no genera automáticamente una venta. |

| 21 | Registrar venta presencial | W/M | POS autorizado y confirmación transaccional de contado. |

| 22 | Procesar pagos electrónicos | W/M | Pago sandbox, firma de webhook, rechazo, expiración e idempotencia. |

| 23 | Emitir y consultar comprobantes | W/M | Documentos correctos y descargas autorizadas. |

| 24 | Solicitar y consultar cambios | W/M | Elegibilidad, plazo, motivo, unidades y seguimiento. |

| 25 | Atender cambios y reembolsos | W | Recepción, reemplazo, diferencia, notificación, pago y entrega trazables. |

| 26 | Utilizar el vestidor existente | W/M | Preservar funcionamiento e integración; describir honestamente su tecnología. |

| 27 | Consultar recomendaciones | W/M | Recomendaciones sobre catálogo autorizado y validación de disponibilidad. |

| 28 | Preparar y consultar catálogo offline | W/M | Descarga persistente, PWA instalable, SQLite y aviso de desactualización. |

| 29 | Registrar reserva offline | W/M | Cabecera, detalles y operación pendiente guardados atómicamente. |

| 30 | Registrar venta de contado offline | W/M | Efectivo recibido y venta provisional diferenciados de confirmación central. |

| 31 | Consultar operaciones locales | W/M | Persistencia tras reinicio, estado, detalle y último resultado. |

| 32 | Sincronizar operaciones | W/M | Envío manual/automático, reintentos, resultados e idempotencia. |

| 33 | Resolver conflictos | W/M | Motivo visible y resolución autorizada, sin pérdida de historial. |

| 34 | Consultar reportes convencionales | W | Filtros, datos reales y exportaciones disponibles en ambos planes. |

| 35 | Solicitar reportes generativos | W/M | Texto y voz, seis tipos, filtros variables y restricción a Profesional. |

| 36 | Preparar datos y entrenar modelos | Herramienta técnica + consulta W | Dataset reproducible, modelos, evaluación y artefactos identificables. |

| 37 | Consultar dashboard y analítica | W | KPI existentes, predicciones, segmentos y explicación de resultados. |

| 38 | Consultar auditoría | W | Trazabilidad de acciones, sincronización, pagos y cambios sin exponer secretos. |



La auditoría y las notificaciones necesarias se instrumentarán desde el primer CU que las utilice; CU-38 corresponde al cierre de su consulta y presentación.



**Ciclo de cierre por CU:**



1. Revisar la ficha ya preparada.

2. Implementar o adaptar datos y backend.

3. Implementar las interfaces asignadas.

4. Ejecutar pruebas del CU y de sus reglas afectadas.

5. Capturar evidencia y actualizar trazabilidad.

6. Preparar un resumen de cambios para la subida manual a GitHub.

7. Continuar al siguiente CU después de resolver fallos bloqueantes.



Los diagramas técnicos seguirán pendientes hasta la etapa final elegida.



## 5. Calendario, reparto y entregas



El calendario objetivo suma aproximadamente **206 horas-persona**. Para sostenerlo será necesario trabajar cerca de cinco a seis horas diarias por persona y reutilizar efectivamente el P1.



| Fecha | Trabajo previsto | Evidencia o salida |

|---|---|---|

| 22–24 octubre | Teoría, reglas, tabla de CU, fichas, prototipos y matriz de requisitos. | Capítulos I–II y contratos definidos. |

| 25 octubre | Incorporación del P1, Docker local, base de pruebas y preparación de migración. **Presentación 1.** | Documento inicial, inventario de reutilización y entorno reproducible. Diagramas técnicos declarados pendientes. |

| 26 octubre | CU-01 a CU-05. | Acceso por empresa, empresas, planes y suscripciones. |

| 27 octubre | CU-06 a CU-12. | Usuarios, permisos, sucursales y catálogo administrativo aislados. |

| 28 octubre | CU-13 a CU-18. | Compras, inventario, catálogo y checkout adaptados. |

| 29 octubre | CU-19 a CU-23. | Reservas, POS, pagos y comprobantes consistentes. |

| 30 octubre | CU-24 y CU-25. | Flujo de cambios y reembolsos con notificación. |

| 31 octubre | CU-26 a CU-28. | Vestidor y recomendaciones preservados; catálogo offline web/móvil. |

| 1 noviembre | CU-29 a CU-31. **Presentación 2.** | Reservas y ventas locales que sobreviven al reinicio. Sincronización integral aún pendiente. |

| 2 noviembre | CU-32 y CU-33. | Sincronización, duplicados, concurrencia y conflictos resueltos. |

| 3 noviembre | CU-34 y CU-35. | Reportes convencionales y generativos con exportación. |

| 4 noviembre | CU-36 y CU-37. | Modelos evaluados e integrados al dashboard. |

| 5 noviembre | CU-38 y regresión integral. | Código funcional estabilizado y resultados de pruebas. |

| 6–8 noviembre | Ingeniería inversa, diagramas, capítulos III–VI, despliegue y revisión final. **Presentación 3.** | Entrega integral de software, documentación y evidencias. |

| 9 noviembre | Ensayo, restauración de respaldo y correcciones finales. | Versión congelada para defensa. |

| 10 noviembre, 07:00 | Defensa, hora de Bolivia. | Demostración guiada y trazabilidad disponible. |



No se inventará una hora de cierre para las entregas dominicales: el PDF no la fija.



**Reparto inicial:**



- Tú: backend, PostgreSQL, migraciones, infraestructura e integración.

- Tu compañera: interfaces Angular/Flutter, prototipos y consolidación documental.

- Ambos: reglas, pruebas de aceptación, revisión de evidencias y defensa.



El paralelismo será dentro del CU activo: mientras se implementa su backend pueden prepararse sus interfaces y pruebas. No se abrirán varios CU incompletos para aparentar avance.



Si hay retrasos, se recortarán mejoras visuales, análisis adicionales y automatizaciones accesorias. No se eliminarán aislamiento, persistencia, sincronización, ML ni pruebas obligatorias. La entrega del 25 no debe describirse como ICONIX completo mientras falten los modelos que pidió la docente.



## 6. Diagramas finales, despliegue y aceptación



### Ingeniería inversa con Graphify



Se generará un grafo nuevo del código P2 estabilizado. El grafo anterior servirá únicamente como referencia.



Procedimiento:



1. Fijar la versión local del código utilizada para documentar.

2. Extraer estructura y relaciones de Python, TypeScript, Dart y SQL.

3. Consultar Graphify por cada CU.

4. Verificar las rutas encontradas directamente en el código.

5. Complementar las omisiones con análisis de símbolos y ejecución de pruebas.

6. Construir los diagramas editables en PlantUML.

7. Exportar imágenes legibles para Word/PDF.

8. Comprobar correspondencia bidireccional entre métodos, mensajes y fuentes.



**Diagramas y modelos finales:**



- Casos de uso general e individuales.

- Modelo de dominio.

- Robustez por CU.

- Secuencia por CU y alternativas críticas.

- Clases de diseño organizadas por módulos.

- Datos conceptual, lógico y físico.

- Persistencia IndexedDB y SQLite.

- Componentes y arquitectura.

- Despliegue real.

- Estados de sincronización, reservas y cambios.



Se elaborará además un **inventario de todos los métodos y funciones escritos por el equipo**, excluyendo dependencias y código generado. Incluirá firma, archivo, ubicación, responsabilidad y CU asociado.



No se inventarán clases para representar servicios implementados como funciones. Graphify será una ayuda de extracción y navegación, no una garantía automática de cobertura. Las relaciones inferidas se verificarán antes de incorporarlas.



### Despliegue independiente



Destino: `/home/alecv/Parcial2_FashionStore`.



Diseño:



- Docker Engine y Compose instalados para Debian mediante el repositorio oficial. [Procedimiento oficial](https://docs.docker.com/engine/install/debian/).

- Proyecto Compose propio: `fashionstore_p2`.

- PostgreSQL, red y volúmenes independientes.

- Backend con un proceso inicialmente.

- Web publicada únicamente en `127.0.0.1:8082`.

- Acceso público HTTPS del subdominio propuesto mediante el servicio de túnel existente.

- Base de datos sin puerto público.

- Imágenes construidas localmente y transferidas por SSH para reducir carga en el servidor.

- Entrenamiento ML fuera del servidor; carga diferida de modelos para inferencia.

- Límites de memoria y prueba de consumo real antes de aceptar el despliegue.



Se preservarán los servicios y rutas de la otra aplicación existente.



**Publicación de cada versión validada:**



1. Ejecutar pruebas locales y generar artefactos identificados.

2. Transferir por SSH a una carpeta de versión.

3. Respaldar la base y recursos persistentes de P2.

4. Ejecutar migraciones.

5. Levantar servicios y comprobar salud.

6. Probar acceso público, móvil y flujos críticos.

7. Activar la versión.

8. Conservar la anterior para reversión.



La reversión de código y la recuperación de base se documentarán por separado; cambiar la imagen no deshace automáticamente una migración.



GitHub no será un requisito para desplegar. La transferencia al servidor seguirá siendo independiente de las subidas manuales al [repositorio de respaldo](https://github.com/AleDevCV/FashionStore_V2-SaaS).



### Pruebas obligatorias



| Área | Escenarios de aceptación |

|---|---|

| Migración | Copia del P1 preserva relaciones, importes y stock; datos de A y B independientes. |

| Aislamiento | A no puede listar, leer, modificar, borrar ni exportar datos de B, incluso cambiando IDs manualmente. |

| Propiedad y roles | Un cliente no puede ver compras ajenas ni confirmar pagos; permisos también aplicados en móvil. |

| RLS y conexiones | Alternar peticiones A/B en conexiones reutilizadas sin contaminación; falta de contexto deniega acceso. |

| Planes | Rechazar tercera sucursal Básico y undécima Profesional; probar reactivaciones y altas simultáneas. |

| Suscripciones | Vencimiento, renovación y downgrade; no perder pendientes offline. |

| Offline web | Instalar PWA, desconectar, registrar operaciones, cerrar navegador y recuperar datos al abrir. |

| Offline móvil | Mismo recorrido en Android físico, verificando persistencia SQLite. |

| Idempotencia | Reenviar veinte veces una operación y obtener una sola venta y un solo movimiento. |

| Respuesta perdida | Confirmar en servidor, perder respuesta y reintentar recuperando el mismo resultado. |

| Concurrencia | Dos dispositivos venden la última unidad; nunca quedan dos ventas confirmadas sobre ese stock. |

| Atomicidad | Fallo intermedio no deja cabeceras, detalles o movimientos incompletos. |

| Conflictos | Precio cambiado, stock agotado, variante inactiva y permisos revocados; originales conservados. |

| Pagos | Webhook válido, firma inválida, duplicado, rechazo y expiración; sin doble descuento de stock. |

| Cambios | Dentro/fuera de plazo, unidad ya cambiada, diferencias positivas/negativas y reemplazo pendiente. |

| IA | Al menos cuatro tipos demostrados con filtros cambiantes, datos actuales y consultas entre varias tablas. |

| Seguridad de IA | Peticiones sobre otra empresa, instrucciones maliciosas, ambigüedad y caída del proveedor. |

| ML | Datos reproducibles, separación de evaluación, métricas, comparación de referencia e inferencia integrada. |

| Regresión | Acceso, catálogo, compras, inventario, reservas, POS, checkout y vestidor siguen funcionando. |

| Producción | HTTPS desde otra red, instalación PWA, APK, respaldos, restauración y consumo de memoria. |



Las pruebas automatizadas se concentrarán en reglas críticas, integración PostgreSQL, sincronización y autorización. Se utilizarán pytest, pruebas Angular, pruebas Flutter y recorridos integrales web; las comprobaciones offline incluirán cierres y reinicios reales.



### Paquete final y defensa



La entrega contendrá:



- Documento Word y PDF completos.

- Código de backend, Angular y Flutter.

- Configuración Docker e instrucciones reproducibles.

- Migraciones y datos de demostración.

- APK identificada con la versión entregada.

- Diagramas editables y exportados.

- Inventario de métodos y matriz de trazabilidad.

- Evidencias y resultados de pruebas.

- Informe de datasets, entrenamiento y evaluación ML.

- Manual de usuario, despliegue, respaldo y recuperación.



La demostración seguirá este recorrido: dos empresas aisladas → restricciones de plan → reserva y venta offline en web y móvil → reinicio → sincronización repetida sin duplicados → conflicto de última unidad → cambio de prenda → reportes dinámicos → dashboard ML → localización de métodos de un diagrama en el código.



**Criterio final de terminación:** requisitos cubiertos por evidencia, flujos críticos funcionando localmente y en producción, diagramas correspondientes a la versión entregada y documentación que distingue claramente lo implementado de sus limitaciones.



