# Evaluación de ampliaciones y acceso global

Fecha: 24 de octubre de 2026, Bolivia. Estado: análisis y decisiones de diseño; no acredita implementación ni despliegue de estas ampliaciones.

## Alcance de la revisión

Se revisó el texto aportado por el usuario y se consultó el MCP Graphify del proyecto `C:/SINSTEMA INFORMACION 2/VecinoMarket`. Se excluye íntegramente live commerce. Se mantienen FastAPI, Angular, Flutter, PostgreSQL y los requisitos del examen P2; las ideas del proyecto Django/React se adaptan a esos componentes.

El grafo contiene 3037 nodos y 8407 relaciones, con 59 % extraídas y 41 % inferidas. Se utilizó para localizar fuentes y después se verificaron directamente los símbolos relevantes. La presencia de un módulo en el grafo o en el código no demuestra su funcionamiento en producción.

## Evaluación de las 25 familias restantes

| N.º del texto | Familia | Decisión propuesta para FashionStore |
|---|---|---|
| 1 | Administración y contratación SaaS | Conveniente: solicitud de empresa, plan, revisión y motivo de rechazo. Extender CU-03/05; definir si cada alta requiere aprobación o si existe alta directa. |
| 2 | Perfil y personalización de tienda | Alta utilidad: logo, descripción, contacto, color y URL pública. La marca no cambia reglas comerciales ni permisos. |
| 3 | Autenticación y cuentas | Prioridad inmediata de diseño: acceso por correo y contraseña, identidad global de clientes y recuperación de contraseña coherente. Google y renovación de sesiones son ampliaciones separadas. |
| 4 | Empleados, roles y permisos | Completar el núcleo actual. Mantener rol, permisos efectivos y sucursales por empresa; los permisos individuales necesitan precedencia explícita frente al rol. |
| 5 | Planes y suscripciones | Reforzar CU-04/05 conservando Básico 2 y Profesional 10 sucursales, offline en ambos y reportes generativos exclusivos de Profesional. |
| 6 | Catálogo e imágenes | Reforzar el catálogo de prendas existente; conservar variantes, tallas, colores, temporadas y múltiples imágenes. No sustituirlo por producto genérico. |
| 7 | Clasificación por imagen | Opcional posterior. CLIP debe comparar categorías de ropa; sus afinidades relativas no son probabilidades de acierto. Requiere proveedor y evaluación propios. |
| 8 | Inventario y alertas | Reforzar CU-15/16. Existencias mínimas por variante y sucursal, alertas persistentes y un único mecanismo de movimientos. |
| 9 | Carrito | Reforzar CU-18; un carrito por empresa, variantes explícitas y el mismo cálculo de precios que POS y sincronización. |
| 10 | Pedidos digitales | Integrar con reservas, ventas, pagos y entrega existentes. Evitar una segunda venta o un descuento duplicado de stock. |
| 11 | Pagos | Completar Stripe sandbox y su webhook propio. PayPal y referencias de tarjetas guardadas son opcionales. No almacenar números de tarjeta ni CVV. |
| 12 | Entregas y direcciones | Conveniente después del núcleo: retiro en sucursal y direcciones privadas. En una compra con varias tiendas, separar pedidos, disponibilidades y entregas por empresa. |
| 13 | Promociones | Útil, ampliando la regla existente: vigencia y menor precio válido sin acumulaciones. Debe funcionar igual en web, móvil, POS y reconciliación offline. |
| 15 | Chat cliente-tienda | Ampliación útil para tallas, reservas y cambios. Participantes y adjuntos autorizados por empresa; comenzar con texto y bandeja antes de añadir adjuntos. |
| 16 | FAQ y chatbot | Ampliación de bajo consumo si usa reglas y datos permitidos. No sustituye a Gemini ni a los reportes generativos del examen. |
| 17 | Recomendaciones | Enriquecer CU-27 con popularidad y compras verificadas. No trasladar consultas de datos comerciales de otras tiendas al administrador de una empresa. Filtrar variantes disponibles. |
| 18 | Valoraciones | Útil después del flujo de entrega: compra comprobable y entregada, relación con tienda/prenda y moderación trazable. |
| 19 | Dashboards y reportes | Reforzar CU-34/37 sin reemplazar las consultas y modelos actuales. Panel SaaS con métricas de plataforma y alcance definido; no acceso comercial indiscriminado. |
| 20 | Reportes por texto/voz | Reforzar CU-35. Conservar interpretación generativa estructurada, consultas permitidas, límites, tenant y al menos cuatro tipos demostrados. |
| 21 | Facturación SaaS y comisiones | Posponer. Agrega reglas financieras de cobro, ajustes y conciliación que no son obligatorias para el examen. No equivale a facturación fiscal certificada. |
| 22 | Referidos | Posponer hasta cerrar el producto obligatorio. Beneficios explícitos sin modificar indebidamente las capacidades mínimas de los planes. |
| 23 | Notificaciones y correos | Prioridad de integración: bandeja durable, eventos de negocio, SMTP y FCM cuando exista proyecto Firebase. Alertas en pantalla no demuestran push con la aplicación cerrada. |
| 24 | Geolocalización | Opcional. Empezar con coordenadas y enlaces a mapas; PostGIS y búsqueda por cercanía solo si se justifican consultas geográficas y recursos. |
| 25 | Auditoría | Consolidar CU-38 y la instrumentación transversal; identidad global, empresa, sucursal, UUID, actor y resultado, sin contraseñas ni tokens. |
| 26 | Respaldo y recuperación | Conservar pg_dump, archivos privados, hashes y restauración a copia ya probados. Adaptar la experiencia administrativa; el JSON de Django no restaura FashionStore. |

## Hallazgos comprobados en VecinoMarket

- `Backend/apps/usuarios/models.py:26`: correo único global; tipos de cuenta SUPERADMIN, ADMIN, EMPRESA, EMPLEADO y COMPRADOR. `get_empresa()` diferencia personal de empresa y compradores globales.
- `Backend/apps/usuarios/serializers.py:22`: `LoginSerializer` incorpora rol y empresa al token a partir de la cuenta autenticada.
- `Backend/apps/usuarios/views.py:108`: login con auditoría; la gestión de empleados aparece en las vistas de empresa y de administración. La posibilidad existente en VecinoMarket no significa que ya esté disponible en FashionStore.
- `Backend/apps/usuarios/views.py:170`: parte del alta de empresas utiliza aprobación automática para prueba. No asumir que todas las solicitudes siguen revisión manual.
- `Backend/apps/catalogo/ia.py:1`: CLIP mediante Replicate y descripciones candidatas. Las puntuaciones son afinidades relativas; requiere adaptar las categorías a prendas.
- `Backend/apps/comunicacion/views.py:376`: chatbot basado en FAQ, palabras clave y respuestas construidas desde datos de empresa; no es un LLM generativo.
- `Backend/apps/reportes/migrations/0004_recomendaciones_funciones_y_triggers.py:1`: recomendaciones colaborativas y respaldo por popularidad calculados en SQL. No sustituyen los modelos supervisado/no supervisado del examen.
- `Backend/apps/reportes/serializers.py:6`: valoraciones relacionadas con pedidos y compradores; la comprobación de elegibilidad se realiza también en sus vistas.
- `Backend/apps/core/backup.py:52`: respaldo JSON mediante dumpdata de Django. Se puede adaptar la interfaz e historial, conservando los mecanismos PostgreSQL nativos de FashionStore.

## Decisiones expresas del usuario sobre el acceso

1. Un único formulario de correo y contraseña; sin campo Empresa.
2. El backend obtiene el tipo de cuenta, la empresa, el rol operativo y los permisos a partir de los datos almacenados, nunca del prefijo del correo.
3. Los clientes tienen una cuenta única para comprar en todas las tiendas.
4. El usuario solicita las contraseñas de demostración indicadas también para la aplicación pública. Sus valores deben configurarse de forma privada; la base conserva hashes. No se sustituyen por ellas contraseñas de PostgreSQL, JWT, SSH ni claves externas.

Ejemplos de identificación previstos:

| Tipo | Correo de ejemplo | Alcance |
|---|---|---|
| Superadministrador | admin@fashionstore.com | Administración de plataforma SaaS |
| Administrador de Atelier Andino | atelierandino@fashionstore.com | Su empresa y sucursales |
| Cajero de Atelier Andino | cajero-atelierandino-01@fashionstore.com | Permisos y sucursales asignados |
| Encargado de Casa Textil | encargado-casatextil-01@fashionstore.com | Permisos y sucursales asignados |
| Cliente global | cliente1@fashionstore.com | Sus compras y solicitudes en las tiendas donde opere |

El sufijo numérico permite varias personas con el mismo cargo. Los correos se normalizan y deben ser únicos globalmente. El formato de correo es una convención visual; no concede permisos. Generar un identificador con dominio fashionstore.com no crea un buzón: se necesita un correo real/verificado separado para recuperación y avisos cuando esos identificadores no tengan casilla propia.

## Diseño del cambio de identidad

Separar identidad global de pertenencia a una empresa:

- Cuenta global: identificador estable, correo normalizado único, hash, estado y versión de sesión.
- Personal de plataforma: capacidad explícita de administrar el SaaS.
- Personal de empresa: relación con empresa, rol, permisos y sucursales autorizadas.
- Cliente global: identidad común para la persona; perfiles y operaciones comerciales separados por empresa.
- Ventas, reservas, pagos, inventario, cambios, reportes y auditoría comercial conservan su tenant_id.

Una relación entre la cuenta global y los usuarios/perfiles actuales de cada empresa permite conservar los IDs comerciales y las operaciones existentes. No se debe resolver un correo duplicado tomando arbitrariamente la primera coincidencia ni intentando contraseñas contra todas las empresas.

Al entrar, el servidor autentica la cuenta global. Para personal de empresa fija su ámbito empresarial. Para clientes, la tienda se obtiene de la navegación al catálogo, producto o carrito; seleccionar una tienda no concede facultades administrativas. No vuelve el selector Empresa al formulario de login.

La cuenta global del cliente puede mostrarle su propio historial entre tiendas. Un administrador empresarial sigue limitado a las operaciones y al perfil comercial del cliente dentro de su empresa. Una tienda no debe poder modificar la contraseña global ni acceder al historial ajeno del comprador.

## Migración y comprobaciones necesarias

1. Respaldar y ensayar sobre copia. Inventariar colisiones actuales: admin@example.com y cliente@example.com se repiten entre demo-a y demo-b.
2. Crear la identidad global y sus relaciones; no quitar RLS ni dar BYPASSRLS a la aplicación para localizar un correo.
3. Renombrar las cuentas de demostración del personal con correos únicos. Vincular perfiles de clientes comunes solo mediante una decisión explícita de migración; no fusionar personas reales por coincidencia de correo.
4. Mantener claves primarias y referencias de compras, reservas, pagos, cambios y auditoría.
5. Adaptar login, registro, recuperación, cierre/revocación de sesiones y cambios de contraseña al ámbito global correcto.
6. Adaptar Angular y Flutter, redirección por tipo de cuenta y contexto de tienda del cliente. Permisos verificados por backend en cada operación.
7. Conservar cachés y pendientes offline por empresa y usuario operativo. No borrar colas al actualizar la autenticación ni mezclar carritos de distintas tiendas.
8. Probar correo único, mayúsculas/minúsculas, empresa suspendida, cuenta bloqueada, revocación, cambio de tienda del cliente y rechazo de acceso entre empresas.
9. Verificar reservas, ventas, pagos, cambios y sincronización bajo la nueva identidad; los resultados anteriores no acreditan esta modificación.
10. Preparar nuevas cuentas privadas de demostración y actualizar manuales, fichas y evidencias antes de desplegar una versión validada.

## Orden recomendado

Primero: acceso y clientes globales, con regresión de aislamiento y offline. Después: cerrar los CU obligatorios y completar roles, permisos y notificaciones. A continuación: identidad comercial de tiendas, contratación, FAQ/chat y reputación. Clasificación adicional, Google, nuevos medios de pago, comisiones, referidos y geolocalización avanzada quedan como ampliaciones posteriores.

Mantener los identificadores de los 38 CU existentes. Si se aprueban módulos nuevos, añadir CU posteriores y su trazabilidad; no renumerar los ya documentados para absorber funcionalidades nuevas sin registrar el cambio de alcance.
