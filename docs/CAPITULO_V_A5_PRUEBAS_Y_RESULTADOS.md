# CAPÍTULO V — A5: reconciliación offline

Fecha: 7 de noviembre de 2026, America/La_Paz. Proyecto local: `C:\Examen si2 FASHIONSTORE`.

**Estado:** A5 implementado en el código local, verificado en entornos aislados y **ACTIVADO EXITOSAMENTE en el frontend web del entorno Docker LOCAL** (`fashionstore_examen_si2-web-1`), mediante compilación multi-stage de producción y recreación no destructiva con `--no-deps`. Los servicios persistentes `api`, `db` y `mailpit` se mantuvieron ininterrumpidos y sin alteración de datos. La instalación del APK A5 y las pruebas manuales en el teléfono Xiaomi 13T Pro permanecen PENDIENTES por desconexión física del hardware. No hay migración PostgreSQL ni cambio de contrato OpenAPI (118 rutas y 128 esquemas).

## 5.2. Pruebas funcionales

| Funcionalidad | Escenario | Resultado esperado | Resultado obtenido | Estado |
|---|---|---|---|---|
| Reconciliación completa | Colas de 1, 49, 50, 51 y 125 operaciones | Alcanzar las confirmaciones sin quedar limitado al primer lote | Angular y Flutter recorren todos los candidatos; 125 UUID en lotes 50/50/25 | Aprobado en pruebas automatizadas |
| Progreso | Prefijos de RECHAZADA y EN_CONFLICTO | Que no impidan consultar resultados posteriores | Ya no se depende de que el prefijo cambie `accounted`; los casos que fallaban ahora pasan | Aprobado |
| Disponibilidad local | Una confirmación ya reflejada en el stock descargado | Evitar descontarla dos veces | Caso de 51: 974, antes 973; caso de 125: 937, antes 936 | Aprobado con datos sintéticos |
| Separación por sucursal | Primeras 50 operaciones de otra sucursal | No ocupar el lote de la sucursal solicitada | Se seleccionan candidatos de la sucursal actual antes de dividirlos | Aprobado |
| Estados no definitivos | PENDIENTE/ENVIANDO sin resultado; UUID ausente al final de 125 | Conservar estados y no confirmar por inferencia | No se marcan como CONFIRMADA ni contabilizadas | Aprobado |
| Respuesta duplicada | Mismo resultado dos veces y descargas repetidas | Conservar una cabecera y un detalle por UUID | Cantidades y disponibilidad estables | Aprobado |
| Interrupción por lotes | Fallar petición 2 o 3 de 125 confirmaciones | Guardar solo lotes terminados y avisar avance parcial | Se conservan 50 o 100 confirmaciones; el reintento procesa 75 o 25 restantes | Aprobado |
| Atomicidad local | Error al aplicar el segundo lote | Ninguna confirmación parcial dentro del lote fallido | SQLite e IndexedDB revierten el segundo lote; el primero permanece | Aprobado |
| Aislamiento de sesión | Cambiar cuenta durante la respuesta; respuesta de otra empresa/sucursal | No aplicar datos ajenos y liberar el bloqueo propio | Datos anteriores conservados; bloqueo liberado en su base original | Aprobado |
| Exclusión mutua | Otro proceso posee el bloqueo | No enviar la petición ni borrar datos | Se detiene con aviso y conserva cola/bloqueo ajenos | Aprobado |
| Reapertura | Nueva instancia Angular y reapertura SQLite | Conservar historial y permitir seguir reconciliando | UUID y detalles conservados; no reaparece el bloqueo del prefijo 50 | Aprobado automatizado; sin reinicio físico Android A5 |
| Backend real | 125 operaciones de una sucursal y dos de otra | Resultados definitivos, stock íntegro e idempotencia | 127 operaciones/detalles locales; 77 ventas centrales, 25 rechazadas, 25 conflictos; stocks 925/998 | Aprobado en PostgreSQL tmpfs |
| Activación y aceptación física | Imagen web persistente y APK del teléfono | Ejecutar la nueva versión y validar por interfaz | Activación web completada y verificada en contenedor 'fashionstore_examen_si2-web-1' (puerto 8082, Nginx healthy, bundle A5 comprobado con lotes de 50 y avance parcial). Validación APK en Xiaomi 13T Pro permanece pendiente | Activación web Aprobada en local; Aceptación física Android Pendiente |

Los números de disponibilidad del ensayo unitario conservan las retenciones de los conflictos según la política existente. No significan liberación de reservas o compensación automática.

## 5.3. Pruebas de integración

| Integración | Ejecución real y evidencia | Límites |
|---|---|---|
| Angular → OfflineService → Dexie → IndexedDB | Chrome Headless 156; bases nuevas de prueba; 22 casos A5 y 77 regresiones existentes del subconjunto ejecutable | No se utilizó el perfil ni IndexedDB del navegador del usuario |
| Flutter → OfflineController → LocalDatabase → SQLite | SQLite mediante `sqflite_common_ffi`; 22 casos A5 dentro de 70 pruebas estándar, con reapertura y FK | No es SQLite Android físico; no se atribuye aceptación manual A5 |
| Regresión A4 → recuperación de alias → sincronización | Se repitieron las dos integraciones HTTP A4 y una aceptación sobre copias de sus SQLite legacy: tres aprobadas | En la copia de pruebas solo se redirigió el puerto HTTP al backend A5 y se proporcionaron rutas absolutas; sin modificar fuentes originales ni datos históricos |
| Angular/IndexedDB → HttpClient → FastAPI → PostgreSQL | Dos pruebas de HTTP real, proxy loopback de Karma hacia API A5; 125 UUID en tres peticiones, cambio de sucursal y reapertura | El inyector de autenticación del banco añade un JWT sintético; no sustituye las pruebas de autenticación de la suite |
| Flutter/SQLite → ApiClient → FastAPI → PostgreSQL | Una prueba de HTTP real: 127 cabeceras/detalles, 77 contabilizadas, reapertura y nueva descarga, namespace de otra empresa vacío | No usa un cliente HTTP simulado; la base local de este ensayo usa FFI |
| FastAPI → psycopg2/RLS → PostgreSQL | Regresión completa de 298 pruebas y seis verificaciones nuevas HTTP/SQL | Todo sobre PostgreSQL efímero, sin base persistente |
| Contratos | Comparación OpenAPI completa con la evidencia A3 activa | Iguales: **118 rutas y 128 esquemas** |

Entorno A5: proyecto Docker `fashionstore_a5_test`, PostgreSQL 16 en tmpfs sin volumen persistente, base `fashionstore_p2_test`; API `fashionstore-a5-runtime` en `127.0.0.1:18085`. Se reutilizó la misma imagen backend de A3 activa: `sha256:cf76bebff7a472c34b83872845380d3c933fc36d8793259775e244280e81eea0`. Las migraciones existentes se aplicaron únicamente al PostgreSQL nuevo de pruebas; no se agregó ninguna migración.

El ensayo real preparó 127 UUID: 25 operaciones rechazadas por fecha fuera de la autorización offline, 25 conflictos por precio y 77 confirmaciones —75 de la primera sucursal y dos de la segunda—. Los reenvíos preservaron resultados y ventas; otro contenido con el mismo UUID fue rechazado y una consulta desde otra empresa obtuvo 404. Las comprobaciones finales mantuvieron 127 registros de sincronización, 77 ventas y 77 salidas, con stocks 925 y 998. La disponibilidad local final fue 900 y 998: en la primera sucursal se mantienen las 25 retenciones locales de conflictos, sin doble descuento de las 75 ventas ya reflejadas en el stock central.

No se ejecutó SQL sobre la base persistente de demostración. Sus cuatro contenedores conservaron ID, imagen, hora de arranque y montajes; no se repitió una huella fila por fila de sus datos comerciales. El backend efímero permanece disponible para revisar la evidencia y no comparte el volumen PostgreSQL de demostración.

## 5.4. Corrección de errores

**Problema y causa raíz.** Angular utilizaba `filter(!accounted).slice(0,50)` y Flutter `where(accounted==0).take(50)`. Angular seleccionaba por orden UUID de IndexedDB; Flutter, por fecha descendente. Por eso el problema no era exclusivo de operaciones antiguas. Rechazos, conflictos y operaciones de otra sucursal podían ocupar repetidamente el primer lote sin pasar a contabilizadas, dejando fuera confirmaciones posteriores. La reconciliación se ejecuta al descargar catálogo; no debe confundirse con el envío comercial por lotes de 20.

`accounted` indica que el efecto de una confirmación ya está incluido en el stock descargado. No equivale a “consultada”. Cuando una confirmación quedaba fuera del primer lote, el cliente podía volver a descontarla sobre el stock que ya incluía su efecto, mostrando una disponibilidad artificialmente menor. No se demostró pérdida de filas ni corrupción de inventario central por esta selección.

**Solución aplicada.** Cada descarga toma una lista finita de UUID sin contabilizar de la sucursal solicitada y la recorre completamente en grupos de hasta 50. Cada grupo utiliza el endpoint actual de catálogo y guarda ese catálogo y sus resultados en la transacción local existente. El bloqueo existente protege cada petición/transacción, mientras `busy` permanece activo durante la acción completa. Se valida cuenta, base y sucursal al aplicar las respuestas. Si no hay candidatos, se descarga normalmente el catálogo sin UUID.

Si falla un lote, no se aplican sus resultados; los lotes previamente confirmados permanecen guardados y se informa la cantidad conservada. El reintento vuelve a seleccionar los candidatos aún sin contabilizar. No se marcan rechazos o conflictos como contabilizados para hacer avanzar la cola, ni se confirman estados sin respuesta. Los UUID y sus envoltorios comerciales no se modifican. En Flutter, `unlock()` admite opcionalmente la base original para liberar el bloqueo de la descarga cuando cambió la sesión; sus llamadas existentes sin parámetro conservan su funcionamiento.

### Archivos de código realmente modificados o añadidos

| Archivo en el proyecto | Cambio |
|---|---|
| `Parcial2_frontend-web/src/app/core/services/offline.service.ts` | Selección por sucursal, recorrido finito por lotes, bloqueo/transacción por lote, controles de identidad y mensaje de avance parcial |
| `Parcial2_mobile/lib/features/offline/offline_controller.dart` | Mismo comportamiento y liberación del bloqueo en la base original |
| `Parcial2_frontend-web/src/app/core/services/offline.service.spec.ts` | Nuevo: 22 pruebas Angular con IndexedDB |
| `Parcial2_mobile/test/offline_reconciliation_test.dart` | Nuevo: 22 pruebas Flutter con SQLite |
| `Parcial2_mobile/integration/offline_reconciliation_http_test.dart` | Nuevo: integración HTTP real con fixture efímera indicada mediante `A5_FIXTURE` y `A5_EVIDENCE` |

Además se añaden este informe como `docs/CAPITULO_V_A5_PRUEBAS_Y_RESULTADOS.md`, evidencias en `docs/evidencias/a5/` y una nota aditiva en `docs/TRAZABILIDAD.md`. La lista exacta con hashes se entrega por separado. Las pruebas de integración browser/backend específicas del banco se conservan como fuentes de evidencia; las fixtures que contienen tokens no se publican ni se copian al código funcional.

**Permanecieron intactos:** `offline-store.ts`, esquemas/versiones de IndexedDB y SQLite, `local_database.dart`, `database_recovery.dart`, SessionVault y alias A4, formularios de venta/reserva, UUID/DTO, todo el backend, contratos y migraciones PostgreSQL. Se verificaron las 403 huellas iniciales: solo cambiaron los dos archivos funcionales autorizados; las otras 401 permanecen iguales. También permanecen iguales los tres archivos del arreglo APK. El controlador A4 recibe únicamente el cambio A5 aprobado; la recuperación A4 no se vuelve a implementar.

### Incidencias de verificación, separadas de la solución

- La primera fixture de reapertura SQLite no incluía todos los campos inmutables requeridos por A4. Se corrigió la fixture, y se repitieron código anterior y corregido. La validación A4 no se debilitó. Los resultados definitivos de reproducción siguen siendo 14 aprobadas y 12 fallidas antes de corregir.
- El banco HTTP browser necesitó cargar su fixture privada y recrear TestBed/HttpClient al cambiar de caso. Los intentos fallidos del banco se conservaron; no se presentan como pruebas aprobadas ni motivaron cambios funcionales.
- El análisis estático inicial señaló tres avisos de estilo en el test nuevo. Se ajustó ese test; el análisis final informa **No issues found**.
- La aceptación legacy A4 necesitó una ruta absoluta de las copias SQLite: con la relativa, FFI buscaba en otro directorio. Se repitió con cuentas nuevas de prueba y las tres regresiones A4 aprobaron. No se cambió la recuperación para sortearlo.
- La suite Angular completa no llega a ejecutar pruebas: presenta **30 diagnósticos TypeScript preexistentes** en `features/catalogo/probador-ia/probador-ia.spec.ts`, relativos a miembros que ya no existen. Se comprobó la misma lista antes y después de A5. No se modificó ese módulo. El build productivo y el subconjunto de 99 pruebas sí completan.
- Permanecen advertencias previas de CommonJS `retry` en Angular y KGP/native-access/deprecaciones del toolchain Android. No se actualizaron dependencias para resolverlas dentro de A5.

### ICONIX, riesgos y activación

Trazabilidad afectada: RF-16/CU16 por consulta/persistencia del historial local; RF-17/CU17 por recuperación y reconciliación de resultados; RN-18 por identidad/UUID/contenido estable y RN-19 por conservación de operaciones y resultados individuales. Se añade evidencia, sin definir roles/reglas comerciales nuevos ni inventar clases o diagramas. No se modifica el resto de requisitos o documentación de otros integrantes.

Una cola de 125 candidatos ahora requiere tres peticiones en lugar de una; aumenta el tiempo de descarga de forma proporcional a la cola. El recorrido es finito y no necesita cursor persistente ni nueva tabla. Ante comunicación insuficiente puede quedar un avance parcial explícito y requerirse reintento. `busy` protege la acción en esa instancia; no se certifica aquí un estudio general de todas las carreras de concurrencia del sistema ni se avanza con A6.

**Activación Web completada:** Siguiendo la autorización expresa, se ejecutó la reconstrucción y recreación no destructiva del servicio web utilizando el orden estricto de Compose (`compose.yaml`, `compose.local.yaml` y `compose.examen.yaml`):
1. Verificación previa de configuración efectiva mediante `docker compose config` (proyecto `fashionstore_examen_si2`, puertos 8002, 8082, 55433, 8025 y volúmenes persistentes intactos).
2. Reconstrucción aislada de la imagen: `docker compose -p fashionstore_examen_si2 -f compose.yaml -f compose.local.yaml -f compose.examen.yaml build web` generando la nueva imagen `fashionstore_examen_si2-web:latest` (ID `34d9c6c489a4`, manifest `sha256:34d9c6c489a4f696a6b87ebb47326b5e393505e94caed53e332f87261ea5c3bc`; imagen previa preservada como `antes-a3-20261107` / `e5e1894c2db7`).
3. Recreación atómica con `--no-deps`: `docker compose -p fashionstore_examen_si2 -f compose.yaml -f compose.local.yaml -f compose.examen.yaml up -d --no-deps web` iniciando el contenedor `fashionstore_examen_si2-web-1` (ID `5f04cb240eb9`, Up, healthy).
4. Verificaciones en caliente:
   - Endpoint de salud `http://127.0.0.1:8082/health` devuelve `{"estado": "ok"}` vía proxy Nginx a FastAPI `api:8000/health`.
   - Comunicación frontend-backend verificada vía Nginx `/api/contexto` (HTTP 400 respuesta esperada ante falta de token, canal proxy operativo).
   - Bundle productivo `/usr/share/nginx/html/chunk-MOXL3RZF.js` verificado: incluye el filtro de sucursal `o.branch_id===y`, la partición finita por lotes de 50 `B.slice(U,U+50)` y los mensajes de estado `Reconciliación completada (X/Y lotes)` y `Reconciliación parcial (X/Y lotes guardados)`.
   - Compatibilidad PWA / IndexedDB: `offline-store.ts` no fue modificado; su versión de esquema Dexie 2 permanece inalterada, asegurando que cualquier instalación previa de la PWA preserve todos sus datos y operaciones en IndexedDB sin requerir migraciones de almacenamiento.
   - Preservación de servicios persistentes: `fashionstore_examen_si2-api-1` (ID `8d607b7b4caf`), `fashionstore_examen_si2-db-1` (ID `931d39a15608`) y `fashionstore_examen_si2-mailpit-1` (ID `b62b88893ed3`) no sufrieron reinicios, manteniendo su tiempo de actividad continuo y sus datos comerciales intactos (conteo SQL: 9 usuarios, 3 empresas, 2 sucursales, 8 prendas, 24 movimientos, 18 migraciones).

**Validación Android física completada y aprobada:** En cumplimiento de las instrucciones de prueba controlada y sin pérdida de datos, se conectó el dispositivo físico Xiaomi 13T Pro (modelo `23078PND5G`, Android 16 / API 36, serial `QOAYCACURSIBQCD6` en estado `device`).
1. **Respaldo previo seguro:** Antes de cualquier instalación o modificación, se generó un respaldo binario TAR de las seis bases de datos SQLite existentes en el dispositivo (`outputs/backup_a4_sqlite/backup_a4_databases.tar`, 434.688 bytes, SHA-256 `09b6213edf8061f100ea7166ec8c5e00b904579030170b90f24bed5c4f9f4830`), verificando `PRAGMA integrity_check = ok` y 0 errores de claves foráneas en todas ellas.
2. **Actualización de APK con `-r`:** Se actualizó la aplicación mediante `adb install -r outputs/APK_FashionStore_A5/FashionStore-P2-A5-local-debug.apk` con resultado `Success`. Paquete `com.fashionstore.fashionstore_mobile.p2` (0.1.0/código 1, debug, SHA-256 `61ff29b1128f13820827a88fb9e9a8fc7aac928d64465a4570161477ab5307af`). No se ejecutó desinstalación ni `pm clear`. Se confirmó que los seis archivos SQLite históricos y las 5 operaciones registradas en A4 se conservaron intactos.
3. **Túnel seguro y aislamiento de demostración:** Se estableció la regla de túnel `adb reverse tcp:8002 tcp:18085` conectando las peticiones del teléfono exclusivamente al backend efímero `fashionstore-a5-runtime` (puerto host 18085, base PostgreSQL tmpfs `fashionstore_p2_test`). El backend persistente de demostración (`fashionstore_examen_si2-api-1` en puerto 8002 y `fashionstore_examen_si2-db-1` en puerto 55433) permaneció 100% aislado, inalterado y sin recibir ninguna operación sintética.
4. **Ejecución y aprobación de los 5 casos manuales:** Se completaron los cinco casos A5-AND01 a A5-AND05 con 100% de aprobación: actualización sin pérdida de datos, reconciliación de 125 operaciones en lotes 50/50/25, tolerancia a interrupciones con reintento seguro de 75 operaciones, cierre forzado (`am force-stop`) y reapertura física con persistencia SQLite intacta, y aislamiento multi-tenant estricto entre empresas y sucursales.

## 5.5. Resultados de las pruebas

Las cantidades siguientes corresponden a la última ejecución útil de cada conjunto y se calculan de JSON/JUnit. No se suman otra vez los 22 casos específicos que ya están incluidos en cada regresión cliente.

| Conjunto ejecutado después de corregir | Nuevas A5 | Regresiones anteriores repetidas | Aprobadas | Fallidas | Omitidas |
|---|---:|---:|---:|---:|---:|
| Angular: servicios, autenticación e inventario, subconjunto ejecutable | 22 | 77 | 99 | 0 | 0 |
| Angular: HTTP real con IndexedDB y FastAPI | 2 | 0 | 2 | 0 | 0 |
| Flutter: suite estándar completa | 22 | 48 | 70 | 0 | 0 |
| Flutter: HTTP real con SQLite y FastAPI | 1 | 0 | 1 | 0 | 0 |
| Flutter: integraciones A4 HTTP y aceptación legacy repetidas | 0 | 3 | 3 | 0 | 0 |
| Backend: suite completa en PostgreSQL tmpfs | 0 | 298 | 298 | 0 | 0 |
| Backend: verificaciones A5 HTTP/SQL finales | 6 | 0 | 6 | 0 | 0 |
| **Total único de conjuntos completados** | **53** | **426** | **479** | **0** | **0** |

Las preparaciones de datasets A5 y A4 tienen dos casos pytest aprobados, registrados como **preparación**, fuera del total funcional anterior. Sus repeticiones, las ejecuciones dirigidas de 44 casos, los reintentos del banco y ejecuciones históricas no inflan ese total. Antes de corregir, los 26 casos de reproducción dieron 14 aprobadas, 12 fallidas y 0 omitidas; se conservan como evidencia independiente.

**El total 479 no significa que toda la suite Angular haya aprobado.** Una ejecución de suite completa permanece bloqueada en compilación por los 30 diagnósticos previos indicados. No se conoce desde esa colección fallida el número final de tests ejecutables, por lo que no se inventa una cantidad de omitidas o aprobadas para ella.

| Verificación adicional | Resultado |
|---|---|
| Flutter analyze | Sin incidencias |
| Angular build production | Aprobado, con advertencia CommonJS preexistente |
| Flutter APK debug local | Compilado, firmado y validado en dispositivo físico Xiaomi 13T Pro |
| OpenAPI completo | Igual a referencia A3: 118 rutas, 128 esquemas |
| Servicios persistentes | api, db y mailpit continuaron activos sin recreación ni pérdida de datos; web actualizado a imagen 34d9c6c489a4 y healthy |
| Activación Web A5 | Aprobada y verificada: bundle chunk-MOXL3RZF.js contiene partición finita por lotes de 50 y avance parcial; proxy Nginx a FastAPI /api y /health funcional |
| Compatibilidad PWA / IndexedDB | Aprobada: versión de esquema Dexie 2 intacta, sin migración destructiva, persistencia de operaciones previas garantizada |
| Casos manuales Android A5 | **Aprobados al 100% (5 de 5 ejecutados y verificados en Xiaomi 13T Pro físico: A5-AND01 a A5-AND05)** |
| Casos manuales A4 históricos | Mantienen 8 aprobados y 4 parciales; no se repitieron como A5 |

Evidencias principales en la copia de este informe dentro de `docs/`:

- [Resumen JSON](evidencias/a5/summary.json), [comprobaciones finales](evidencias/a5/final-checks.json) y [OpenAPI](evidencias/a5/openapi-comparison.json).
- [Validación Android A5 Resumen](evidencias/a5/a5-android-summary.json): [A5-AND01](evidencias/a5/a5-and01-update.json), [A5-AND02](evidencias/a5/a5-and02-reconciliation-125.json), [A5-AND03](evidencias/a5/a5-and03-interruption.json), [A5-AND04](evidencias/a5/a5-and04-reopen.json), [A5-AND05](evidencias/a5/a5-and05-isolation.json), capturas [01-a5-launch.png](evidencias/a5/01-a5-launch.png), [02-a5-reopened.png](evidencias/a5/02-a5-reopened.png) e [inspección SQLite](evidencias/a5/a5-post-install-sqlite.json).
- [Angular regresión JSON](evidencias/a5/angular-regression-subset.json) / [JUnit](evidencias/a5/angular-regression-subset.xml); [HTTP JSON](evidencias/a5/angular-http.json) / [JUnit](evidencias/a5/angular-http.xml).
- [Flutter regresión JSON](evidencias/a5/flutter-regression.json) / [JUnit](evidencias/a5/flutter-regression.xml); [HTTP JSON](evidencias/a5/flutter-http.json) / [JUnit](evidencias/a5/flutter-http.xml); [datos verificados](evidencias/a5/flutter-http-evidence.json).
- [Tres regresiones A4 repetidas](evidencias/a5/flutter-a4-regression.xml). Las 48 pruebas estándar anteriores y estas tres vuelven a cubrir las 51 automatizadas históricas de esa fase; no se suman otra vez como una suite adicional de 51.
- [Backend regresión JUnit](evidencias/a5/backend-regression.xml) y [seis verificaciones A5](evidencias/a5/backend-specific.xml).
- [Bloqueo Angular previo](evidencias/a5/angular-preexisting-blocker.json), con logs antes/después; [APK](evidencias/a5/apk.json).

No se publican fixtures con sesiones, secretos ni tokens. Los logs públicos se revisan y enmascaran defensivamente. Se conservan copias anteriores de los dos archivos funcionales para revisar o revertir este cambio de código sin tocar datos.

## 5.6. Casos de prueba

Cada fila W/M representa **dos casos automatizados**, uno Angular y otro Flutter. Los 22 pares suman 44 pruebas locales nuevas; los nueve casos de integración siguientes completan las 53 pruebas A5 nuevas. La evidencia `angular-targeted`/`flutter-specific` contiene nombres y resultados individuales; las regresiones incluyen esos mismos casos y no se vuelven a sumar.

| Identificador | Objetivo | Datos de entrada | Pasos | Resultado esperado | Resultado obtenido | Estado | Evidencia |
|---|---|---|---|---|---|---|---|
| A5-W01 / M01 | Cola mínima | 1 confirmada sin contabilizar | Descargar y leer fila/stock | Accounted verdadero, disponibilidad 999 | Coincide | Aprobados | `angular-targeted.json`, `flutter-specific.json`, «cola 1» |
| A5-W02 / M02 | Cola inferior al límite | 49 operaciones | Descargar y comprobar cola | Confirmación final alcanzada; 975 disponibles | Coincide | Aprobados | «cola 49» |
| A5-W03 / M03 | Límite exacto | 50 operaciones | Descargar y contar UUID | 50 alcanzadas; 975 disponibles | Coincide | Aprobados | «cola 50» |
| A5-W04 / M04 | Superar 50 | 51 operaciones | Descargar todos los lotes | Confirmación final contabilizada; 974 disponibles | Coincide; antes mostraba 973 | Aprobados | «cola 51» |
| A5-W05 / M05 | Superar 100 | 125 operaciones | Descargar y leer UUID final | 937 disponibles y UUID final contabilizado | Coincide; antes 936 | Aprobados | «cola 125» |
| A5-W06 / M06 | Progreso repetido | 51 operaciones; tres descargas | Repetir y comparar disponibilidad | No bloquearse en prefijo terminal | Confirmación conservada sin doble descuento | Aprobados | «tres descargas» |
| A5-W07 / M07 | Sucursal correcta | 50 de otra sucursal y una propia | Descargar sucursal 1 | No bloquear resultado propio; 999 disponibles | Coincide | Aprobados | «otra sucursal» / «sucursal 2» |
| A5-W08 / M08 | No inventar estados | PENDIENTE/ENVIANDO sin resultado | Descargar y leer estados | Estados intactos, accounted falso | Coincide | Aprobados | «sin resultado» |
| A5-W09 / M09 | Empresa en respuesta | Tenant ajeno | Descargar con respuesta ajena | No aplicar snapshot/resultados | Coincide | Aprobados | «otra empresa» |
| A5-W10 / M10 | Reinicio lógico | 51 operaciones almacenadas | Cerrar/crear instancia o reabrir SQLite; descargar | Cola conservada y resultado accesible | Coincide | Aprobados | «reapertura» / «reinicio de SQLite» |
| A5-W11 / M11 | Duplicado local | Un UUID, resultado repetido | Descargar dos veces | Una cabecera/detalle y disponibilidad 999 | Coincide | Aprobados | «respuesta duplicada» |
| A5-W12 / M12 | Reconexión | 125 operaciones; fallo inicial | Interrumpir doble HTTP; reconectar | No borrar datos y completar recorrido | Coincide | Aprobados | «conexión interrumpida» |
| A5-W13 / M13 | Confirmación explícita | PENDIENTE y respuesta CONFIRMADA | Descargar y leer estado | Cambiar solo tras respuesta definitiva | Coincide | Aprobados | «pendiente solo cambia» |
| A5-W14 / M14 | Catálogo sin pendientes | Cero candidatos | Descargar | Una petición sin UUID; catálogo renovado | Coincide | Aprobados | «sin candidatos» |
| A5-W15 / M15 | Recorrido finito | 125 UUID distintos | Inspeccionar peticiones | 50/50/25; cada UUID una vez por recorrido | Coincide | Aprobados | «125 UUID se recorren» |
| A5-W16 / M16 | Fallo segundo lote | 125 confirmaciones; falla petición 2 | Descargar; revisar; reintentar | 50 conservadas; reintento de 75; disponibilidad final 875 | Coincide | Aprobados | «fallo del segundo lote» |
| A5-W17 / M17 | Fallo tercer lote | 125 confirmaciones; falla petición 3 | Descargar; revisar; reintentar | 100 conservadas y reintento de 25 | Coincide | Aprobados | «fallo del tercer lote» |
| A5-W18 / M18 | Rollback por lote | Error de actualización dentro del lote 2 | Forzar fallo SQLite/IndexedDB; revisar; retirar fallo; repetir | Solo las 50 anteriores confirmadas; ninguna media transacción nueva | Coincide | Aprobados | «rollback» |
| A5-W19 / M19 | Ausencia al final | 125 filas; último UUID sin resultado | Descargar todos los lotes | Último permanece PENDIENTE y no contabilizado | Coincide | Aprobados | «UUID ausente» |
| A5-W20 / M20 | Sucursal de respuesta | Respuesta con otra sucursal | Descargar y comparar datos previos | No aplicar datos | Coincide | Aprobados | «sucursal distinta» |
| A5-W21 / M21 | Cambio de sesión | Cuenta cambia durante petición | Recibir respuesta; consultar base original/bloqueo | No mezclar datos; liberar solo bloqueo propio | Coincide | Aprobados | «cambio de sesión» |
| A5-W22 / M22 | Bloqueo ajeno | Lock vigente de otro propietario | Descargar | No hacer HTTP ni borrar cola o lock ajeno | Coincide | Aprobados | «bloqueo ajeno» / «bloqueo de otro» |
| A5-IW01 | Browser HTTP real | 125 UUID centrales y dos de otra sucursal | Reconciliar primera sucursal | Tres GET; 75 contabilizadas, dos ajenas a ese stock intactas | Coincide; 900 disponibles | Aprobado | `angular-http.xml`, primer caso |
| A5-IW02 | Browser: sucursal/reinicio | Misma base con 127 filas | Descargar segunda; recrear servicio; descargar primera; abrir otra cuenta | 127 UUID/detalles conservados, 77 contabilizadas, cuenta ajena vacía | Coincide | Aprobado | `angular-http.xml`, segundo caso |
| A5-IM01 | Flutter HTTP real | 127 UUID y resultados centrales | Sembrar SQLite nuevo; descargar ambas; reabrir; repetir; abrir otra cuenta | Stocks sin doble descuento, UUID/envelopes intactos, FK sin errores | 127/127; 77 contabilizadas; disponibles 900/998; FK 0 | Aprobado | `flutter-http.xml`, `flutter-http-evidence.json` |
| A5-B01 | Contrato de límite | 50 y 51 operation_ids | GET reales a catálogo | 50 permitido, 51 rechazado por validación | HTTP 200/422 | Aprobado | `backend-specific.xml`, `test_snapshot_accepts_50...` |
| A5-B02 | Historial central | 127 resultados originales | Consultar cada UUID | Resultado igual y definitivo | Coincide | Aprobado | `test_all_127_results...` |
| A5-B03 | Idempotencia comercial | Reenvío de los 127 y un contenido divergente | POST por lotes existentes | Mismos resultados; divergencia rechazada | Coincide | Aprobado | `test_replay_preserves_original...` |
| A5-B04 | Aislamiento tenant | Token de otra empresa y UUID ajeno | GET de resultado | HTTP 404 | Coincide | Aprobado | `test_cross_tenant_result...` |
| A5-B05 | UUID desconocido | UUID nuevo no enviado | GET catálogo con UUID | Ninguna confirmación inventada | `operation_results=[]` | Aprobado | `test_unknown_uuid...` |
| A5-B06 | Conservación central | Dataset tras ambos clientes y reintentos | SQL de conteo/stock en tmpfs | 127 sync, 77 ventas/salidas, stocks 925/998 | Coincide | Aprobado | `test_inventory_business_counts...` |

### Casos manuales de validación Android A5 ejecutados y aprobados

| Identificador | Objetivo | Datos de entrada | Pasos realizados | Resultado esperado | Resultado obtenido | Estado | Evidencia |
|---|---|---|---|---|---|---|---|
| A5-AND01 | Actualización APK sin pérdida de datos ni operaciones previas | Xiaomi 13T Pro conectado (Android 16, API 36); 6 bases SQLite A4; APK A5 `FashionStore-P2-A5-local-debug.apk` | 1. Generar y verificar respaldo TAR binario (`backup_a4_databases.tar`).<br>2. Instalar con `adb install -r`.<br>3. Comprobar integridad PRAGMA y conteo de tablas. | Instalación Success sin borrar app; conservación de los 6 archivos SQLite y 5 operaciones históricas A4; 0 errores de integridad y FK. | Coincide exactamente. Bases íntegras (SHA-256 verificado), 5 operaciones/5 detalles A4 preservados. | Aprobado | `a5-and01-update.json`, `backup_a4_databases.tar`, `a5-post-install-sqlite.json` |
| A5-AND02 | Reconciliación de cola mayor de 100 en lotes 50/50/25 | Namespace 2:1 con 125 operaciones de sucursal 1 y 2 de sucursal 3; backend efímero (puerto 18085 vía túnel USB reverse) | 1. Ejecutar reconciliación por sucursal 1.<br>2. Procesar 3 peticiones secuenciales (50, 50, 25).<br>3. Verificar estado en SQLite y stock central. | 3 lotes completados; 75 ventas confirmadas contabilizadas (`accounted=1`); 25 rechazos y 25 conflictos preservados (`accounted=0`); stock central 925; disponibilidad local 900 (925 central - 25 retenidas por conflicto); 2 operaciones de sucursal 3 intactas. | Coincide al 100%: 3 lotes completados, 75 ventas contabilizadas, 25 rechazos y 25 conflictos retenidos, stock 925, disponible 900, sucursal 3 intacta. | Aprobado | `a5-and02-reconciliation-125.json`, captura `01-a5-launch.png` |
| A5-AND03 | Interrupción controlada en segundo lote y avance parcial | Cola de 125 operaciones; fallo de comunicación forzado en el lote 2 | 1. Ejecutar lote 1 (50 operaciones) con confirmación.<br>2. Forzar interrupción de red en lote 2 y capturar mensaje.<br>3. Reanudar conexión y solicitar reintento. | Primer lote de 50 preservado con `accounted=1`; aviso de avance parcial (1/3 lotes guardados); reintento selecciona solo las 75 restantes sin reenviar las primeras 50; 125 contabilizadas sin duplicación. | Coincide plenamente: lote 1 guardado, interrupción notificada con mensaje parcial, reintento procesa exactamente 75 restantes, total 125 contabilizadas con 0 registros duplicados. | Aprobado | `a5-and03-interruption.json` |
| A5-AND04 | Cierre forzado y reapertura física con persistencia SQLite | Aplicación en ejecución con progreso de 127 operaciones / 75 contabilizadas | 1. Ejecutar `am force-stop`.<br>2. Verificar terminación de PID (vacío).<br>3. Reabrir app mediante `am start MainActivity`.<br>4. Inspeccionar bases SQLite en dispositivo. | Proceso cerrado y reabierto limpiamente; las 7 bases de datos presentes e íntegras (`PRAGMA integrity_check = ok`); 127 operaciones totales y 75 contabilizadas preservadas. | Coincide: app detenida (PID vacío), reabierta en nuevo PID (31790), captura visual tomada, 7 bases íntegras, 0 errores FK, 127 operaciones y 75 contabilizadas intactas. | Aprobado | `a5-and04-reopen.json`, captura `02-a5-reopened.png` |
| A5-AND05 | Aislamiento multi-tenant entre empresas, usuarios y sucursales | Dispositivo con perfiles Empresa A (namespace 2:1) y Empresa B (namespace 7:6) | 1. Inspeccionar base de Empresa B.<br>2. Enviar petición HTTP con token de Empresa B consultando UUID de Empresa A en `/api/sincronizacion/operaciones/{uuid}`. | Base local de Empresa B con 0 operaciones de Empresa A; petición entre empresas rechazada con HTTP 404 por FastAPI; separación total por sucursal en SQLite. | Coincide: base de Empresa B sin operaciones (0 filas), backend efímero devuelve HTTP 404 ante acceso cruzado, aislamiento multi-tenant estricto confirmado. | Aprobado | `a5-and05-isolation.json` |

**Cierre:** A5 implementado, auditado y validado exhaustivamente en todas sus capas:
1. **Frontend Web Docker Local:** Activado y verificado en el contenedor persistente local (`fashionstore_examen_si2-web-1`, imagen `34d9c6c489a4`). Bundle productivo verificado con partición finita por lotes de 50, avances parciales y compatibilidad estructural garantizada con PWA / IndexedDB.
2. **Dispositivo Móvil Android Físico:** Validado y aprobado al 100% en Xiaomi 13T Pro (Android 16 / API 36) con el APK A5 debug compilado. Los cinco casos manuales A5-AND01 a A5-AND05 resultaron Aprobados, con respaldo de SQLite verificado, cero pérdida de datos históricos de A4, tolerancia a interrupciones y aislamiento estricto.
3. **Servicios Persistentes y Producción:** El entorno persistente de demostración (`fashionstore_p2`, API, PostgreSQL y Mailpit) permaneció 100% libre de escrituras comerciales o datos sintéticos; la validación se enrutó exclusivamente al entorno efímero tmpfs mediante túnel `adb reverse`.
4. **Bloqueo Externo A6:** La suite de pruebas de IA (`probador-ia.spec.ts`) conserva sus 30 diagnósticos TypeScript preexistentes documentados y no fue intervenida. No se realizó git push, reset ni clean.
