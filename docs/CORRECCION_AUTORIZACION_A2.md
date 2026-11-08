# Corrección A2 — acceso a sincronización por sucursal

## 1. Causa raíz y alcance

`GET /api/conflictos` verificaba `conflictos.resolver` pero listaba todos los conflictos/rechazos visibles de la empresa. `GET /api/sincronizacion/operaciones/{operation_id}` y los reintentos válidos/malformados de `POST /api/sincronizacion/lote` aceptaban autor o permiso sin comprobar asignación de sucursal. Las referencias `original_operation` podían revelar estado antes de validar el acceso. Compensar sí llamaba a `authorized_branch`, pero después de evaluar estado/efectivo, y omitía la sucursal si era NULL.

La migración 009 aísla empresas y restringe Cliente a sus operaciones. La 014 limita sucursales en tablas comerciales, pero no incluye `operacion_sync`. El rol no propietario mantuvo el aislamiento entre empresas durante las pruebas; A2 era una omisión de autorización de sucursal en aplicación, no una prueba de ruptura de RLS entre empresas.

Los prefijos reales son los anteriores: el router se incluye en `app/main.py` con `/api`. También se revisó `GET /api/offline/catalogo`: ya valida sucursal y filtra `operation_ids` por autor; permanece intacto.

## 2. Evidencia antes de corregir

La matriz definitiva de 27 pruebas contra las copias originales produjo **19 fallidas y 8 correctas**, sin errores de ejecución. Los fallos son casos de prueba, no 19 vulnerabilidades independientes: incluyen HTTP 200 indebidos en consulta por UUID, recuperación por lote y compensación de rechazo ajeno sin sucursal, así como revelación de estado/importe, omisión de revocación de asignación y listado sin filtro. Las sucursales no autorizadas podían ocupar los 100 resultados y ocultar los autorizados.

Las operaciones históricas se prepararon como fixtures explícitas en una base efímera, con dos empresas, dos sucursales de la primera, un encargado asignado a una y otro a ambas, Administrador, Cajero sin permiso de resolución y Cliente. Se probaron resultados propios/ajenos, confirmados/rechazados/en conflicto, incluidos rechazos NULL. La revisión legítima y el envío posterior de un pendiente ejecutan servicios comerciales reales, además de la regresión heredada.

## 3. Política aplicada y aprobada

La consulta y el reintento del autor se conservan dentro de su empresa, aun si perdió permiso de resolución o asignación. Para supervisar operaciones ajenas se requieren `conflictos.resolver` y asignación vigente en `usuario_sucursal`; el Administrador comercial accede a su empresa. El listado exige ese permiso y filtra por autor, sucursales asignadas o Administrador antes de LIMIT 100. Una sucursal inactiva conserva el acceso de consulta del autor y de los supervisores asignados. Compensar exige el permiso y, si existe sucursal, `authorized_branch` con sucursal activa, incluso para el autor. Sin sucursal válida, solo el autor o el Administrador de esa empresa acceden; listar o compensar sigue exigiendo el permiso. No se infiere autorización del `branch_id` contenido en el envelope. Los UUID inaccesibles y desconocidos reciben 404 sin revelar estado ni efectivo.

| Actor, empresa y sucursal | Consulta/reintento | Listado | Compensación |
|---|---|---|---|
| Autor dentro de su empresa | Sí, incluso con sucursal no asignada/inactiva o NULL | Solo con permiso | Con permiso y sucursal activa autorizada si existe |
| Encargado con `conflictos.resolver`, sucursal ajena asignada | Sí, también historial inactivo | Sí | Solo si activa |
| Encargado con permiso, sucursal no asignada y autor ajeno | 404 | Excluido | 404 antes de revelar estado/importe |
| Encargado con permiso, rechazo NULL ajeno | 404 | Excluido | 404 |
| Administrador comercial de esa empresa | Sí, incluido NULL | Sí | Permitido conforme a estado/efectivo; exige sucursal activa si existe |
| Cajero/Cliente sin permiso, autor ajeno | 404 | 403 | 403 |
| Otra empresa | Sin datos ajenos por RLS/contexto | Sin filas de la otra empresa | 404 para UUID ajeno |

Para rechazo NULL propio, el autor sin permiso solo consulta/reintenta; con permiso también lista/compensa. No se crea un rol ni permiso nuevo. Una revisión inaccesible recibe resultado durable RECHAZADA con motivo genérico, sin alterar el original; una revisión legítima conserva el vínculo y el historial. En lotes con UUID existentes inaccesibles se conserva el comportamiento de error HTTP 404 ya utilizado para accesos indebidos: no se elimina el pendiente.

## 4. Implementación mínima

- `app/services/synchronization.py`: función de módulo `require_operation_access`, reutilizando contexto, permiso y `usuario_sucursal`; aplicada antes de devolver respuestas idempotentes o inspeccionar un original.
- `app/routers/offline.py`: control común en GET por UUID y compensación; filtro SQL de conflictos antes de LIMIT 100; `authorized_branch` se ejecuta antes de estado/importes para compensar.
- `tests/test_authorization_a2.py`: 27 pruebas de acceso, permisos, asignación/revocación, UUID manipulados, NULL, inactividad, revisión, compensación, historial e invariancia comercial.

No se modificaron `permissions.py`, `tenant.py`, `commerce.py`, tablas, migraciones, DTO, rutas, firmas existentes, algoritmo de hash, UUID, estados, locks, lease, transacción por operación, snapshot ni lógica de venta offline. La compensación sigue siendo documental y exige restituir el efectivo completo; una reserva exige cero.

## 5. Resultados reales

| Ejecución | Resultado |
|---|---|
| Mismos 27 casos, módulos originales montados en lectura | 19 fallidas, 8 correctas |
| 27 casos, corrección actual | **27 aprobadas** |
| Regresión completa, base efímera limpia | **254 aprobadas**, 0 fallidas/errores/omitidas |
| Comparación OpenAPI original/corregido/regresión | **Idéntico: 118 rutas, 126 esquemas** |

Las 254 incluyen las 227 existentes: C1/A1, sincronización e inventario, concurrencia e idempotencia, además de las 27 nuevas. Hubo dos avisos de deprecación de librerías. Los incidentes de preparación/codificación, descubrimiento de fixtures y montaje de scripts del ejecutor se registran en el resumen; no se presentan como pruebas aprobadas. La regresión final partió de una nueva base sin fixtures previas. Las bases efímeras anteriores se archivaron, sin DROP ni borrado de evidencia.

Se verificó que las denegaciones no modifican `operacion_sync`, inventario, ventas, detalles, reservas, movimientos y retenciones. La compensación conserva filas e información original; la revisión legítima crea otro UUID enlazado. El pendiente no enviado se conserva en el escenario de prueba y después se confirma una sola vez. **Esto no certifica reinicio/recuperación real en IndexedDB o SQLite**: no se modificaron esos componentes ni se ejecutó aceptación en dispositivo.

## 6. ICONIX, requisitos y diagramas

Se actualizaron requisitos/reglas en el inventario histórico y modelo consolidado, las fichas CU16/CU17, contratos y trazabilidad. CU16 consolida históricos CU28–CU31; CU17 consolida CU32–CU33. Se actualizaron las filas históricas 31–33 sin atribuir a A2 una aceptación completa de web/móvil ni confundir el CU16 histórico de inventario con el CU16 consolidado offline.

La robustez y secuencia existentes de CU16 excluyen expresamente sincronización y representan persistencia local y descarga. Se revisaron sus JSON, README y referencias al código: snapshot permanece intacto, por lo que no se retocaron participantes, draw.io, PNG, SVG ni validaciones previas. Ambos README registran la revisión. No se encontró una robustez/secuencia detallada de CU17; su elaboración queda pendiente. No se inventaron diagramas, clases UML, tablas ni interfaces. El nuevo control es una función Python de módulo.

## 7. Estado local, riesgos y límites

Los cuatro contenedores persistentes conservan ID, imagen y hora de arranque: saludables, sin reinicios ni reconstrucción. C1/A1 y módulos compartidos permanecen intactos. **A2 está corregido y verificado en el código local, pero no activado en la imagen de la API persistente**. No se intervino producción ni se ejecutó git push.

RLS debe seguir ejecutándose con rol de aplicación no propietario. Se conserva el límite actual de 100 conflictos/rechazos autorizados y su tratamiento de resueltos; no se cambió paginación ni ciclo comercial. No se ejecutaron builds Angular/Flutter, pruebas físicas de dispositivo, EA ni integraciones productivas. El contenedor PostgreSQL efímero de A2 se mantiene disponible para inspección; no se borraron los datos de pruebas. A3, A4 y A5 quedan fuera del trabajo realizado.

## 8. Evidencia

- `docs/evidencias/autorizacion-a2-antes.xml`
- `docs/evidencias/autorizacion-a2-especificas.xml`
- `docs/evidencias/autorizacion-a2-regresion.xml`
- `docs/evidencias/autorizacion-a2-resumen.json`
- `Parcial2_backend/tests/test_authorization_a2.py`

Los XML entregables no contienen tokens; UUID y datos sintéticos identifican únicamente las fixtures efímeras. El archivo de cambios A2 separa esta intervención de las modificaciones C1/A1 preexistentes. La tarea se detiene en A2.
