# CAPÍTULO I ASPECTOS GENERALES

## 1.1 Introducción

FashionStore es una plataforma de comercio electrónico orientada a empresas que comercializan prendas de vestir. El prototipo del primer parcial integra gestión de productos y variantes, compras, inventarios, reservas, ventas, pagos y servicios de inteligencia artificial mediante aplicaciones web y móvil. Esta base permite abordar una evolución funcional sin reemplazar las herramientas ni reconstruir los procesos comerciales que ya forman parte de la solución.

La nueva etapa introduce un modelo de software como servicio. Diferentes empresas contratan la plataforma y administran sus propios usuarios, sucursales, clientes y operaciones. Esta coexistencia exige que la identidad de la empresa acompañe las consultas, escrituras, documentos y reportes. Una sucursal representa una unidad operativa de una empresa; no constituye una empresa independiente.

La continuidad comercial también depende de las condiciones de conectividad. Cuando una sucursal pierde acceso al servidor, el personal necesita consultar los datos descargados y registrar reservas y ventas de contado. Estas operaciones se guardan localmente, conservan su identificación después de un reinicio y se someten a validación central cuando regresa la conexión. La aceptación local no equivale a una venta central confirmada, porque las existencias, los precios y los permisos pueden haber cambiado.

El proyecto amplía los reportes mediante solicitudes en lenguaje natural y análisis de los datos de cada empresa. El modelo generativo interpreta la intención; el backend controla las consultas y las autorizaciones. A su vez, el módulo de Machine Learning prepara datos sintéticos, entrena modelos supervisados y no supervisados, evalúa sus resultados y presenta predicciones y patrones en un dashboard. Los reportes comerciales consultan datos operativos reales de la base; la procedencia sintética del entrenamiento se identifica expresamente.

El desarrollo se organiza mediante casos de uso y trazabilidad ICONIX entre requisitos, reglas, implementación y pruebas. La documentación integra los procesos heredados necesarios y las capacidades añadidas, y sus modelos finales se contrastan con la versión de software entregada. El resultado esperado es una plataforma demostrable, con aplicaciones web y móvil, aislamiento entre empresas, recuperación ante fallos y una instalación independiente en el servidor destinado al segundo parcial.

## 1.2 Planteamiento del problema

La solución anterior está orientada a una sola cadena de tiendas. Su reutilización por organizaciones independientes requiere impedir que una cuenta consulte o modifique información ajena, diferenciar los límites del servicio contratado y controlar la pertenencia de cada operación. Ocultar opciones de interfaz es insuficiente: las restricciones deben verificarse en el backend y en las relaciones de datos.

La dependencia permanente de Internet interrumpe el registro de ventas y reservas. Una solución local sin reconciliación puede duplicar ventas, perder efectivo registrado o descontar existencias dos veces. Se requiere persistencia durable, identificación estable de operaciones y un protocolo que reconozca confirmaciones, rechazos y conflictos.

Los reportes estáticos tampoco cubren todas las combinaciones de períodos, sucursales y productos solicitadas por una empresa. Integrar IA sin controles expondría información o permitiría consultas arbitrarias. Es necesario interpretar las solicitudes dentro de un conjunto de operaciones permitidas, verificar los datos obtenidos y distinguir resultados comerciales de predicciones.

## 1.3 Objetivos del proyecto

### 1.3.1 Objetivo general

Adaptar FashionStore para que empresas de prendas de vestir administren operaciones independientes mediante suscripciones, mantengan reservas y ventas de contado durante interrupciones de Internet y consulten información comercial y analítica confiable desde aplicaciones web y móvil.

### 1.3.2 Objetivos específicos

1. Identificar los requisitos y reglas del segundo parcial y relacionarlos con casos de uso, componentes y pruebas.
2. Incorporar empresas, pertenencia de usuarios, límites de planes y vigencia de suscripciones.
3. Proteger los datos y documentos comerciales con autorización por empresa, rol, sucursal y propietario.
4. Proporcionar consulta de catálogo y registro durable de reservas y ventas offline en PWA y Flutter.
5. Confirmar operaciones mediante un protocolo idempotente con resultados persistentes y resolución explícita de conflictos.
6. Integrar cambios de prendas con recepción, reposición, diferencias de precio, notificaciones y entrega.
7. Ampliar reportes de datos reales mediante lenguaje natural, filtros variables, gráficos y exportaciones.
8. Entrenar y evaluar modelos supervisados y no supervisados e integrar sus resultados al dashboard.
9. Verificar reglas críticas y regresiones en un ambiente exclusivo de pruebas.
10. Documentar la solución implementada y disponer de un despliegue reproducible y recuperable.

## 1.4 Justificación

La evolución permite reutilizar la inversión del prototipo y ofrecer una operación independiente a varias empresas. La persistencia local reduce interrupciones comerciales, mientras la confirmación central preserva la consistencia. La administración de planes establece límites observables y verificables. Los reportes y modelos analíticos aportan información para decisiones comerciales, con resultados interpretables y restricciones de acceso explícitas.

En el ámbito académico, el proyecto integra modelado, implementación y pruebas sobre procesos con errores de red, concurrencia y reglas comerciales. La trazabilidad facilita demostrar qué requisito satisface cada componente y evita atribuir al sistema capacidades que no han sido verificadas.

## 1.5 Alcance y limitaciones

El alcance comprende 38 casos de uso especificados en el capítulo II. Se conservan las capacidades comerciales y del vestidor previo, y se incorporan multitenencia lógica sobre PostgreSQL compartido, suscripciones administrativas, PWA con IndexedDB, Flutter con SQLite, sincronización, cambios de prendas, reportes y analítica.

Las ventas offline son de contado. Los pagos electrónicos, el primer inicio de sesión, el alta de cuentas y la IA requieren conexión. El stock local representa la última información descargada; una operación local puede terminar en conflicto. No se promete inventario global actualizado durante una desconexión. El cobro SaaS recurrente, la sustitución del vestidor y las aplicaciones iOS quedan fuera del alcance inicial.

El servidor propio tiene recursos limitados; los modelos se entrenan localmente y producción ejecuta inferencia acotada. La ejecución de producción es nativa: PostgreSQL 17 existente, entorno virtual de Python 3.13, systemd y Nginx; Docker se utiliza solamente en el equipo local. El despliegue público requiere configuración de dominio y HTTPS. Los servicios externos requieren sus credenciales de prueba, configuradas fuera del repositorio.

## 1.6 Metodología de desarrollo ICONIX

Los casos de uso constituyen la unidad de especificación, implementación y aceptación. Se identifican actores, precondiciones, flujos, alternativas, reglas y postcondiciones; cada caso se relaciona con interfaces y pruebas. La matriz de trazabilidad conserva la relación con los requisitos del examen y el antecedente del primer parcial.

Por decisión del equipo, los diagramas técnicos finales se elaboran después de estabilizar el código, usando Graphify y comprobación directa de métodos. Este orden difiere de la indicación docente de elaborar modelos antes de implementar y debe revisarse al valorar el cumplimiento metodológico. Los diagramas de requisitos y prototipos se preparan con la especificación; las versiones finales no se declaran completas antes de su revisión.
