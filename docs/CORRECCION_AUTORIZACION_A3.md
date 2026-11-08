# A3 — Implementación y validación aislada de traspasos

## Resultado y estado de activación

**A3 está implementado y validado en el código local y en bases efímeras. NO está migrado ni activado en Docker persistente.** La API de demostración conserva su imagen anterior con C1/A1/A2. No se modificaron producción, secretos, dependencias del proyecto ni migraciones históricas; no hubo push ni despliegue. La fase se detiene antes de aplicar 018 o activar A3.

## Corrección funcional

El traspaso es inmediato y exclusivamente online, con origen/destino distintos, activos y de la misma empresa. Mantiene roles Administrador/Encargado y comprueba autorización actual sobre ambas sucursales, también al reintentar. Cantidad positiva entera; disponible del origen = físico menos retenciones vigentes. Una Salida y una Entrada se confirman con el vínculo y la auditoría en una única transacción. UUID por empresa: mismo contenido recupera el resultado estable; contenido distinto se rechaza. No agrega traspasos al protocolo offline ni recalcula movimientos históricos.

El servicio reutiliza los movimientos actuales: Salida en origen y Entrada en destino, sin UPDATE paralelo de stock ni doble descuento. Bloquea sucursales activas, UUID, variante y existencias en orden estable; consulta retenciones bajo esos bloqueos. Se comprueban destino faltante/igual/ajeno/inactivo, variante, cantidad entera, insuficiencia y desbordamiento. Se conserva la regla previa de variante existente, sin inventar un veto por prenda inactiva.

`traspaso_inventario` vincula las patas y conserva hash/resultado. FK, unicidad, RLS y validación de patas refuerzan la integridad. La migración bloquea nuevos movimientos brutos Traspaso sin efectos, pero conserva históricos. No los transforma ni ajusta saldos retrospectivamente. La auditoría participa en la misma transacción.

`get_db(scope='function')` finaliza el cursor de negocio antes del HTTP 201; un fallo al finalizar no debe presentarse como éxito. `usuario_movimiento` reutiliza autenticación y rol C1 con ese mismo cursor. Se probó incluso con un pool de un slot para evitar retener una conexión de autenticación mientras se espera otra para negocio.

## Contrato conservado y ampliación aprobada

No se añadieron/eliminaron rutas. Se mantienen los cuatro alias POST y GET de movimientos. Entrada/Salida conservan payload y respuesta; Traspaso exige `id_sucursal_destino` y `operation_id` y devuelve una operación lógica con `movimiento_salida` y `movimiento_entrada` reales. El contrato incompleto anterior devuelve 422. El historial conserva tipos físicos y añade el vínculo visible solo con acceso a ambas sucursales. El filtro Traspaso incluye las patas vinculadas y los registros históricos.

GET stock conserva por defecto stock físico y el mismo esquema; el parámetro opcional `disponible=true` descuenta retenciones para el formulario. OpenAPI conserva **118 rutas**, cambia **126 → 128 esquemas** por `MovimientoVinculadoRespuesta` y `TraspasoRespuesta`, y modifica `MovimientoCrear`. Solo cambian los contratos de `/api/movimientos-inventario/` y `/api/movimientos-inventario/stock`; las demás rutas/esquemas son iguales.

Ejemplo de petición nueva:

```json
{"id_sucursal":1,"id_sucursal_destino":2,"id_variante_prenda":7,"tipo":"Traspaso","cantidad":2,"motivo":"Reponer sucursal","operation_id":"00000000-0000-4000-8000-000000000003"}
```

Los formularios Angular/Flutter piden destino explícito, mantienen el UUID durante reintentos y muestran confirmación de ambas patas. Un supuesto éxito del servidor antiguo sin ambas patas se rechaza en los clientes. No se crea cola offline ni se modifican SQLite/IndexedDB o pendientes de venta/reserva. Si se cierra/reinicia un formulario tras una respuesta incierta, se debe revisar historial antes de iniciar otra operación: no se implementó recuperación durable de formularios online.

## Pruebas ejecutadas y evidencia

| Verificación final | Resultado |
|---|---|
| A3, PostgreSQL 17 efímero | **44 aprobadas** |
| Backend completo, nueva base PostgreSQL 17 limpia | **298 aprobadas** (254 existentes + 44 A3) |
| A3 + migración, PostgreSQL 16 efímero como la demostración | **44 aprobadas** |
| Angular build de producción en copia aislada | **Aprobado** |
| Angular formulario/contrato, Chrome headless | **9 aprobadas** |
| Flutter análisis de módulos afectados | **Sin incidencias** |
| Flutter suite existente + A3, copia aislada | **16 aprobadas** (5 nuevas de contrato) |
| APK Android debug, con A3 | **Falló** en plugin preexistente |
| APK Android debug, copia anterior a A3 | **Mismo fallo confirmado** |

Las pruebas backend usan FastAPI TestClient, servicios SQL reales, RLS y rol no propietario, sin simular autorizaciones. Cubren los cuatro alias, permisos/ambas asignaciones, aislamiento por empresa, destino/cantidad inválidos, saldos, retenciones, reintentos exactos y con contenido diferente, UUID por tenant, destino sin inventario, desbordamiento, historial, guardas SQL y conservación de legacy.

Se ejecutaron concurrencia de UUID idéntico/distinto, solicitudes sobre el último saldo y traspasos opuestos; competencia con POS/reservas y cobro legítimo de la propia reserva. Se inyectaron fallos antes/durante/después de Entrada, en auditoría y al finalizar transacción, y un fallo SQL real: no quedaron medias patas ni auditoría/vínculo parcial. No hubo stock negativo. La prueba de upgrade crea una base pre-018, conserva un Traspaso histórico y stock 5, aplica 018 y verifica que no hay recalculado ni vínculo inventado.

Los avisos backend son deprecaciones de librerías. Angular conserva un aviso CommonJS preexistente. Android falla antes de compilar Dart porque `flutter_inappwebview_android` 1.1.3 usa `getDefaultProguardFile('proguard-android.txt')`, no soportado por el toolchain instalado. Se reprodujo con los fuentes previos y el mismo lockfile; no se modificaron plugin, Gradle ni versiones para ocultarlo. **No se declara APK compilado ni aceptación móvil física.**

## Archivos y organización

Backend: `app/schemas/movimiento.py`, `app/routers/movimientos.py`, `app/services/movimiento_service.py`, nueva `database/migrations/018_inventory_transfers.sql` y `tests/test_inventory_transfers.py`.

Angular: modelos/servicio y sus pruebas, modal TS/HTML y pruebas del modal; indicación del vínculo en el historial existente. Flutter: modelos/servicio, formulario, indicación del vínculo en historial y nuevas pruebas de contrato. No se reorganizaron carpetas, incorporaron ORM/Repository ni cambiaron gestores de estado. `permissions.py`, `tenant.py`, `database.py`, sincronización y el trigger histórico de stock permanecen intactos.

La lista exacta y un diff de esta intervención, separados de los cambios C1/A1/A2 anteriores, acompañan el informe. Hay copias previas en el espacio de trabajo. Las dependencias se restauraron solo en copias de compilación usando los lockfiles existentes; no se actualizaron los manifiestos del proyecto.

## ICONIX, reglas y UML

Se actualizaron RF-10/CU10 consolidado ↔ CU16 histórico, RN-10/RN-14/RNF-04, contratos y trazabilidad. La matriz mantiene verificación parcial de aceptación completa porque APK/dispositivo/activación aún están pendientes; no confunde CU16 histórico con el offline consolidado.

Se añadieron suplementos CU10/A3 de robustez y secuencia en draw.io/SVG y fuente PlantUML para alternativas; se conservaron los gráficos anteriores como evidencia de su alcance previo. Los SVG se renderizaron y revisaron visualmente, los XML se analizaron. Los controles son abstracciones de módulos/funciones implementados; `traspaso_inventario` es una entidad SQL, no una clase ORM. No se afirma ejecución en EA ni render con PlantUML.

Un apéndice físico describe PK/FK, RLS, resultado estable y las guardas nuevas. El dump/ER anterior no se presenta como regenerado a partir de una demostración donde 018 todavía no existe. El esquema 018 está ensayado solamente en bases efímeras.

## Impacto antes de migrar o activar la demostración — aprobación pendiente

1. **Base persistente:** 018 creará una tabla de vínculo, índice único de apoyo y funciones/triggers/políticas. No sustituye PK, no elimina columnas/filas, no modifica las 17 migraciones anteriores ni recalcula inventario. Puede bloquear brevemente escrituras al crear índice/triggers; debe planificarse la aplicación con respaldo y revisión.
2. **Compatibilidad:** Entrada/Salida siguen funcionando. Tras 018, un servidor antiguo que intente insertar tipo Traspaso bruto será rechazado; no habrá nuevo falso éxito. Las llamadas antiguas de Traspaso sin destino/UUID se rechazarán por la API nueva. Se deben coordinar API y clientes.
3. **Orden imprescindible:** aplicar 018 con el runner existente aprobado, luego activar la nueva API; el GET de historial del código nuevo consulta la tabla de vínculo. No arrancar esa versión contra la base persistente sin 018. Después actualizar Angular y, cuando se resuelva su compilación, Flutter.
4. **Servicios:** la activación local futura requeriría reconstruir/recrear `api` y reconstruir/activar `web` por sus cambios; no requiere reiniciar PostgreSQL ni Mailpit. No se ejecutó ninguna de estas acciones.
5. **Reversión:** conservar imagen anterior y respaldos. Si se revierte la app, mantener los objetos/datos aditivos; no borrar la cabecera ni deshacer saldos automáticamente. El código antiguo verá las patas físicas; los movimientos brutos Traspaso seguirán bloqueados por la guarda.
6. **Verificación posterior:** hashes de código activo, OpenAPI, salud/proxy, pruebas de la misma imagen con DB aislada y comparación de datos/volúmenes. Evitar traspasos comerciales reales como prueba sobre la demostración.

No se avanzó con A4, A5 o A6. Se solicita una aprobación separada antes de ejecutar el plan de migración/activación persistente. La limitación Android queda registrada y requiere una decisión técnica independiente para cambiar el plugin/toolchain; no se solucionó ampliando el alcance de A3.

## Integridad comprobada antes de solicitar activación

Los cuatro contenedores persistentes conservan ID, imagen, hora de arranque, montajes y salud. La imagen API sigue siendo `0c594ae3e8ccdf5f796a94b8c609d19a209803b72fe2e2f5bab8fdc9722b1db5` (C1/A1/A2). **No existe `traspaso_inventario` en la base persistente** y 018 no está registrado. Las 17 migraciones existentes coinciden con sus checksums según el cálculo del runner y sus archivos no cambiaron.

Las 26 tablas comerciales y 230 filas mantienen sus huellas antes/después. Las fuentes ajenas a A3, incluidas sincronización, offline local y los otros routers C1/A1/A2, permanecen sin cambios. Se mantuvieron los volúmenes persistentes. No se ejecutó push, reconstrucción ni recreación persistente.

Entregables de revisión: `Archivos_modificados_A3.txt`, `Cambios_A3.diff`, `Verificacion_implementacion_A3.json`, XML backend/específicos/PostgreSQL16 y logs de Angular/Flutter/APK. Los suplementos UML están en `docs/diagramas_*` y en la copia `A3_UML` de los entregables.


## Activación local posterior — 2026-11-07

La fase aislada documentada arriba fue seguida de la activación local aprobada. 018 quedó aplicada mediante el runner existente después de verificar respaldo/restauración y rollback; únicamente API/web fueron recreados. Las 196 pruebas HTTP de las imágenes exactas activadas aprobaron; datos comerciales y volúmenes permanecen intactos. OpenAPI: 118 rutas/128 esquemas. APK pendiente y Flutter sin cambios en activación. [Informe y evidencia de activación local](ACTIVACION_LOCAL_A3.md).
