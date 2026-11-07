# Diagramas de secuencia CU01–CU05

Los cinco archivos .drawio son editables, tienen una sola vista por caso de uso y representan el código actual contrastado con consultas MCP de Graphify. Los SVG y PNG son exportaciones de consulta.

| Archivo | Caso de uso |
|---|---|
| CU01_Diagrama_Secuencia.drawio | Gestionar acceso y cuenta |
| CU02_Diagrama_Secuencia.drawio | Administrar empresas, planes y suscripciones |
| CU03_Diagrama_Secuencia.drawio | Administrar personal, roles y permisos |
| CU04_Diagrama_Secuencia.drawio | Gestionar ciudades y sucursales |
| CU05_Diagrama_Secuencia.drawio | Gestionar fichas de clientes |

Se utilizan actores, interfaces, módulos de control, entidades persistentes, llamadas, retornos, ejecuciones y fragmentos UML alt, opt y loop. Las tablas y funciones SQL representan la persistencia implementada con psycopg2; no se inventan clases ORM.

Las agrupaciones de módulos en una línea de vida representan el componente que atiende una responsabilidad. Los mensajes identifican funciones reales o describen la operación SQL realizada. Se omiten utilidades de presentación y estructuras internas del framework que no cambian el resultado.

La autenticación, el contexto empresarial y los permisos son precondiciones de las operaciones privadas. Los diagramas administrativos muestran los flujos de sus actores autorizados; la validación transversal de credenciales se concentra en CU01. Las restricciones RLS y de integridad siguen aplicándose en cada transacción.

## Correspondencia con la implementación actual

- CU01 distingue registro global, autenticación, recuperación, selección de tienda y cierre de sesión. La selección puede crear perfil y ficha comercial mediante identity_customer_profile(). La llamada resume los efectos de esa función SQL. La entrega de correo depende de SMTP.
- CU02 diferencia edición de plan y cambio de suscripción. El recuento de sucursales se representa en edit_subscription(), donde existe en el código; no se atribuye a edit_plan(). La suscripción utiliza ON CONFLICT(tenant_id), conforme al esquema actual.
- CU03 muestra alta, modificación y baja lógica de usuarios, creación de roles, sustitución de permisos y asignación de sucursales. No se dibujan edición o eliminación de roles sin endpoint.
- CU04 representa consultas, alta de ciudades, alta/edición de sucursales y cambio de estado. El cupo se valida en check_branch_limit() y el bloqueo de empresa serializa altas/reactivaciones concurrentes. No se inventan eliminación de sucursales ni edición/baja de ciudades.
- CU05 diferencia fichas empresariales e identidad global. La autogestión no cambia el correo de acceso global. El historial entre tiendas corresponde a las ventas consultadas por identity.purchases(), conservando el contexto de cada empresa.

TRAZABILIDAD_Y_VALIDACION.json identifica archivos fuente y hashes. CU##_Trazas.json relaciona mensajes con símbolos y líneas encontrados. VALIDACION_FORMATO.json registra la validación XML, referencias, numeración y ajuste de texto. El código funcional y el documento Word no se modifican ni se despliegan en esta tarea.

Generadores: scripts/build_sequences_cu01_cu05.py y scripts/sequence_diagrams.py.
