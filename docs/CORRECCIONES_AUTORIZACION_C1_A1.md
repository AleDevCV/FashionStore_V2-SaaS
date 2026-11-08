# Corrección incremental de autorización — C1 y A1

## Alcance y resultado

Corrección local sobre el commit base `d98884c6f882b86d217d91025b974c987e62f4aa`.
La reproducción y la verificación se realizaron con TestClient, servicios reales y
PostgreSQL 17 en `fashionstore_p2_test`, base efímera de `compose.test.yaml`.
No se modificaron producción, secretos, datos del ambiente local funcional ni colas offline.

La política de C1 reutiliza los roles `Administrador` y `Encargado de Sucursal`
que `Parcial2_frontend-web/src/app/app.routes.ts` ya aplica a los cuatro módulos.
Se aplica exclusivamente a las escrituras: los catálogos GET existentes se conservan,
incluido el listado de temporadas utilizado por el monitoreo de inventario.
El actor documental Responsable de inventario no se convirtió en un rol nuevo.
Una futura ampliación de roles o de permisos granulares necesita una decisión explícita.

## Operaciones e implementación

| Hallazgo | Router y manejadores afectados | Guarda reutilizada |
|---|---|---|
| C1 | proveedores: crear_proveedor, actualizar_proveedor, eliminar_proveedor | requiere_rol: Administrador / Encargado de Sucursal |
| C1 | temporadas: crear_temporada, actualizar_temporada, eliminar_temporada | requiere_rol: Administrador / Encargado de Sucursal |
| C1 | compras: registrar_compra | requiere_rol: Administrador / Encargado de Sucursal |
| C1 | movimientos: registrar_movimiento y sus cuatro rutas equivalentes | requiere_rol: Administrador / Encargado de Sucursal |
| A1 | pos: procesar_venta_pos_endpoint y sus dos rutas equivalentes | requiere_permiso: pos.vender |

Archivos de aplicación: `Parcial2_backend/app/routers/proveedores.py`,
`temporadas.py`, `compras.py`, `movimientos.py` y `pos.py`.
Se conservan funciones, métodos HTTP, rutas, DTO, cuerpos de servicios, tablas,
transacciones, RLS y controles de sucursal. No hay migración nueva.
Las solicitudes válidas pero no autorizadas reciben 403; los anónimos reciben 401
cuando la petición identifica una tienda válida.
La revocación de `pos.vender` se consulta en servidor y se prueba con una sesión existente.
La comprobación de sucursal sigue siendo obligatoria aunque el cajero tenga permiso.

## Pruebas y evidencia

Archivo nuevo: `Parcial2_backend/tests/test_authorization_c1_a1.py`.
No sustituye guardas por mocks: utiliza identidades cliente reales, roles existentes,
tablas de permisos, servicios SQL y políticas del esquema de pruebas.

| Ejecución | Resultado |
|---|---|
| Routers originales: 40 pruebas negativas | 38 fallaron porque la escritura se permitió; 2 ya rechazaban al cliente en POS |
| Distribución de las 38 escrituras indebidas | 36 de C1 y 2 de A1; respuestas 201/200 |
| Corrección: matriz específica | 131 aprobadas, cero fallos o errores |
| Regresión backend desde base limpia | 227 aprobadas: 131 nuevas y 96 existentes; cero fallos o errores |
| Comparación OpenAPI original/corregido | Idénticos: 118 rutas y 126 esquemas |

La matriz cubre clientes, anónimos, empleados sin autorización, administradores,
encargados, cajeros con permiso, revocación, sucursales y referencias de otra empresa.
Comprueba que las denegaciones no cambian las filas comerciales ni el inventario,
y que una operación autorizada no modifica datos de la otra empresa.
Se prueban alias de rutas y entradas/salidas; no se redefine el comportamiento de Traspaso.

Evidencias:

- `evidencias/autorizacion-c1-a1-antes.xml`
- `evidencias/autorizacion-c1-a1-especificas.xml`
- `evidencias/autorizacion-c1-a1-regresion.xml`
- `evidencias/autorizacion-c1-a1-resumen.json`

La primera regresión sobre la base acumulada tuvo 226 aprobadas y un fallo de historial.
Había 1.024 empresas de prueba y la consulta de historial limita su recorrido a 500.
El fallo se reprodujo con los routers originales. Se reinicializó únicamente la base
efímera y se repitió toda la suite desde cero, obteniendo las 227 aprobadas indicadas.
No se alteró el historial para hacer pasar la prueba. Para repetir la suite se debe
preparar desde cero la base temporal con el procedimiento existente.
Persisten dos advertencias de deprecación de las bibliotecas de pruebas.

## Trazabilidad

| CU histórico del plan de 38 | CU consolidado | Verificación de esta iteración |
|---|---|---|
| CU-11 | CU-06 | Autorización de escritura de temporadas |
| CU-13 | CU-07 | Autorización de escritura de proveedores |
| CU-14 | CU-07 | Autorización del registro de compras |
| CU-16 | CU-10 | Autorización del registro de movimientos |
| CU-21 | CU-13 | Permiso de venta POS |

Esta evidencia acredita autorización de esas operaciones, no aceptación completa de los CU.
Los diagramas previos se conservan. El cambio añade la evaluación de las guardas
existentes antes de los manejadores, sin añadir clases, entidades o servicios.
Las huellas y líneas anteriores de los routers identifican su versión previa;
el resumen de esta iteración registra las huellas anteriores y posteriores.

## Límites y activación pendiente

- Las lecturas mantienen su política anterior; no se amplió esta tarea a su rediseño.
- No se modificaron los demás hallazgos de la auditoría.
- No se ejecutaron builds Angular/Flutter: sus fuentes no cambiaron.
- La API local que ya estaba iniciada conserva su imagen anterior. El código corregido
  se verificó en el ejecutor aislado, pero no se reconstruyó ni reinició el despliegue local.
- No se publicó ni desplegó producción y no se ejecutó git push.
