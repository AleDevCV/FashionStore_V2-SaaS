# CAPÍTULO V: PRUEBAS Y RESULTADOS — A4 implementado y validado

Verificado: 2026-11-07T17:18:27.540316+00:00. Proyecto local `C:\Examen si2 FASHIONSTORE`. **A4 corregido en código y verificado en entorno aislado. Distribución y aceptación en dispositivo: pendientes.** Se conserva el informe de diagnóstico anterior, incluido su fallo de aceptación. Este archivo nuevo no sobrescribe el capítulo ni documentación de otros integrantes.

## 5.2. Pruebas funcionales

Se comprobó la recuperación de ventas y reservas SQLite cuando la aplicación utiliza los dos hostnames aprobados del mismo despliegue: `https://fashionstore-v2.aledevcv.me` y `https://fashionstore.aledevcv.me`. Ambos resuelven ahora a una identidad de almacenamiento estable, `fashionstore-main`, manteniendo empresa y usuario en el nombre y metadatos de la base. La URL de las solicitudes HTTP sigue siendo la configurada.

Las fuentes antiguas se abren exclusivamente en solo lectura. Se validan identidad, estructura, versión 1, integridad, FK y vínculos; se importa de forma aditiva en una transacción a una base canónica nueva. No se borran ni renombran archivos anteriores ni se sobrescriben sus registros. Las cabeceras, detalles, UUID, device_id históricos, empresa, autor, sucursal, fechas, efectivo, estados, resultados y enlaces a revisiones se conservan.

La aceptación sobre copias de los archivos que reprodujeron el defecto recuperó **cinco operaciones y cinco detalles**: cuatro de la base anterior y una del hostname actual. Se compararon los `wire` completos y los bytes de ambos originales. Las cinco operaciones reaparecen desde cualquiera de los dos alias; antes faltaban los cuatro UUID antiguos.

Se verificaron reapertura, reintentos de recuperación, aperturas concurrentes, empresa/usuario distintos, rechazo de envelope/snapshot ajenos y mantenimiento de separación de hosts locales/desconocidos. Un UUID idéntico no duplica registros. Contenido, detalle o estado divergente entre fuentes nuevas detiene y revierte la recuperación. Una fuente ya importada y sin cambios no degrada resultados actualizados después por el servidor.

La recuperación conserva historial y reintentos, pero marca el catálogo para renovación. No permite crear nuevas ventas/reservas hasta descargar un catálogo de la cuenta correcta. No suma stock procedente de cachés diferentes ni modifica los permisos offline de operaciones anteriores.

## 5.3. Pruebas de integración

| Componentes | Evidencia comprobada |
|---|---|
| Configuración → LocalDatabase | Identidad compartida únicamente por los dos alias; los demás orígenes conservan nombre anterior y separación |
| SQLite v1 → recuperación → SQLite canónica | Transacción aditiva, FK, UUID, detalle e historial conservados; rollback ante SQL, corrupción, versión desconocida y límite real de páginas SQLite |
| Perfil de sesión → OfflineController → recuperación | El controlador espera a la recuperación antes de programar envío; una recuperación fallida no abre cola ni transmite |
| Cola recuperada → ApiClient → FastAPI → PostgreSQL efímero | Dos pruebas de HTTP real con token/permiso válidos exclusivos del entorno de prueba |
| Respuesta central → applyResults → reapertura SQLite | CONFIRMADA se conserva al reabrir aunque la fuente antigua mantenga PENDIENTE |
| Recuperación → descarga de catálogo | Captura deshabilitada hasta renovación; historial y reintentos siguen disponibles |

Se inició un proyecto separado `fashionstore_a4_test`, PostgreSQL 16 tmpfs sin volúmenes persistentes y una copia exacta de la imagen API A3 activa, publicada solo en `127.0.0.1:18084`. No se reconstruyó la API ni se usaron credenciales de demostración/producción. Los tokens de prueba no se incluyen en estos entregables.

La prueba principal creó una venta y una reserva SQLite con permiso real del servidor efímero, las recuperó y envió. Se simuló una respuesta perdida sin aplicarla localmente, se reenviaron los mismos UUID desde OfflineController y se repitió el lote una tercera vez. La verificación SQL directa confirmó **1 venta, 1 reserva, 2 operacion_sync, 1 movimiento, stock físico 4 y retención 1**, partiendo de stock 5. La segunda empresa tuvo cero ventas/reservas/sync. No hubo duplicaciones ni alteración del envelope, UUID o detalles.

SQLite fue real mediante `sqflite_common_ffi`; Secure Storage y el canal de conectividad del dispositivo se simularon. El tráfico HTTP, las autorizaciones del servidor y PostgreSQL de prueba fueron reales. El primer intento de integración encontró la interceptación HTTP predeterminada de Flutter Test, que devolvía 400 sin tráfico; se habilitó HTTP real solo en la prueba de loopback. La ejecución final aprobó. No se atribuye ese fallo de preparación a la aplicación.

## 5.4. Corrección de errores

**Problema:** la aplicación abría una SQLite distinta al cambiar hostname. **Causa:** el nombre contenía Base64 de `apiBaseUrl`; SessionVault solo copiaba referencias de sesión, no las bases. La regresión existente de hostname validaba las claves seguras, sin comprobar la cola SQLite.

**Solución aprobada:** identidad estable para el par de alias; nueva base canónica por despliegue/empresa/usuario; importación validada en solo lectura de originales; inserción aditiva transaccional; marcadores de fuente en `meta`; rechazo explícito de divergencias; catálogo renovable antes de nuevas capturas. Se conservan SQLite y el esquema versión 1; no hay nuevas dependencias, ORM ni cambios en PostgreSQL o en contratos HTTP.

Se modificaron o añadieron exactamente estos **9 archivos de código/pruebas**:

- `Parcial2_mobile/lib/core/config.dart` — modified
- `Parcial2_mobile/lib/features/offline/local_database.dart` — modified
- `Parcial2_mobile/lib/features/offline/offline_controller.dart` — modified
- `Parcial2_mobile/lib/features/offline/database_recovery.dart` — added
- `Parcial2_mobile/test/database_recovery_test.dart` — added
- `Parcial2_mobile/test/offline_recovery_controller_test.dart` — added
- `Parcial2_mobile/test/fixtures/offline_v1.dart` — added
- `Parcial2_mobile/integration/offline_recovery_http_test.dart` — added
- `Parcial2_mobile/integration/offline_legacy_acceptance_test.dart` — added

`session_vault.dart` y autenticación permanecen intactos. Los tres archivos existentes modificados son config, LocalDatabase y OfflineController; los otros seis son el módulo de recuperación y pruebas/fixtures. Se conservaron copias previas y un diff exclusivo A4. El controlador admite dependencias opcionales para verificar el flujo con SQLite temporal y API efímera; el uso normal mantiene sus valores anteriores.

Los nombres de bases previas no cambian. Solo la nueva base canónica recibe datos recuperados y metadatos propios; los UUID/device_id de los envelopes anteriores no se regeneran. Las marcas impiden que una reapertura sobre fuentes estáticas reemplace un resultado central nuevo por el estado antiguo. Cualquier divergencia nueva requiere revisión en vez de selección silenciosa.

La documentación de requisitos/trazabilidad vincula esta corrección con **RF-16/CU16** (persistencia y recuperación), **RF-17/CU17** (sincronización), **RN-16**, **RN-18** y **RN-19**. Se mantiene como pendiente la aceptación en dispositivo; no se marca la entrega móvil como desplegada.

## 5.5. Resultados de las pruebas

| Conjunto final | Aprobadas | Fallidas | Omitidas |
|---|---:|---:|---:|
| Regresión Flutter existente: autenticación, SQLite y cinco contratos A3 | 16 | 0 | 0 |
| Pruebas nuevas de recuperación SQLite | 30 | 0 | 0 |
| Pruebas nuevas del controlador | 2 | 0 | 0 |
| Integración Flutter–FastAPI–PostgreSQL efímero por HTTP real | 2 | 0 | 0 |
| Aceptación posterior con copias de ambas bases del diagnóstico | 1 | 0 | 0 |
| **Total final** | **51** | **0** | **0** |

La suite estándar suma 48; las tres integraciones/aceptación que requieren sus fixtures externas se ejecutaron explícitamente. El análisis estático de módulos offline afectados, pruebas e integraciones terminó con **No issues found**. Las repeticiones durante desarrollo no se suman para inflar el total.

Antes de corregir se habían ejecutado 28 pruebas: 27 aprobadas y 1 aceptación fallida. Se mantienen sus evidencias separadas en el informe de diagnóstico. Tras la corrección, la aceptación con los mismos datos de laboratorio recuperó las cinco operaciones sin alterar originales. Los fallos de preparación del harness y observaciones de estilo se corrigieron antes de cerrar la validación; no se presentan como fallos finales ni se oculta el defecto inicial.

**Pendiente: 1 caso manual**, actualización/reinicio real en dispositivo con datos anteriores y verificación de almacenamiento seguro/SQLite nativos. No equivale a un test omitido por Flutter. No se intentó compilar ni reparar el APK; su problema preexistente sigue separado.

Integridad: los 9 archivos aplicados coinciden por hash con la copia probada; los otros **75 archivos originales de móvil** y los manifiestos/lockfile permanecen intactos. Los **9 módulos críticos backend C1/A1/A2/A3** conservan sus hashes. Los cuatro contenedores de demostración conservan ID, imagen y arranque. Las huellas de sus **46 tablas y 489 filas** coinciden con el cierre A3; el registro 018 sigue presente y no se modificaron datos comerciales, volúmenes o servicios persistentes.

No se reejecutó la regresión completa del backend para este cambio exclusivamente móvil. Se verificaron sus fuentes e imágenes, las pruebas Flutter heredadas y el flujo afectado real contra la misma imagen en un entorno efímero. No se avanzó con A5/A6 ni se modificó producción, secretos o migraciones históricas.

Evidencia: [resumen y hashes](A4_implementacion_evidencias/resumen.json), [JUnit final](A4_implementacion_evidencias/pruebas-finales.xml), [análisis estático](A4_implementacion_evidencias/analyze.log), [conteos PostgreSQL efímero](A4_implementacion_evidencias/runtime-business-final.json), [integridad final](A4_implementacion_evidencias/final-integrity.json). Logs y resultados de cada ejecución están en la misma carpeta. El diagnóstico previo se conserva en `Capitulo_V_5_2_a_5_6_A4_diagnostico_y_propuesta.md`.

## 5.6. Casos de prueba

Los siguientes **35 casos A4 automatizados** aprobaron; los 16 heredados se detallan por nombre en `final-summary.json`. Evidencias de la última columna en `A4_implementacion_evidencias/`.

| ID | Escenario | Entrada | Resultado esperado | Resultado obtenido | Estado | Evidencia |
|---|---|---|---|---|---|---|
| CP-A4-001 | A4: solo los dos alias aprobados comparten identidad; otros orígenes quedan separados | Dos HTTPS aprobados y cuatro orígenes diferentes | Compartir identidad exclusivamente entre los dos alias | Solo el par aprobado comparte identidad | APROBADO | `final.jsonl` |
| CP-A4-002 | A4: base canónica nueva se comparte en ambas direcciones entre alias | Mismo perfil; abrir alias anterior, actual y anterior | Mismo archivo y UUID en ambas direcciones | Contenido conservado en las tres aperturas | APROBADO | `final.jsonl` |
| CP-A4-003 | A4: recupera v1, mantiene sucursales UUID device y detalles; fuente idéntica | Cuatro operaciones v1 de dos sucursales | Copiar cabeceras/detalles/UUID/device sin tocar fuente | 4 operaciones y 4 detalles; bytes originales iguales | APROBADO | `final.jsonl` |
| CP-A4-004 | A4: une cuatro UUID antiguos y uno nuevo sin sumar stocks | Base anterior con 4 UUID y actual con 1 distinto | Conservar los cinco; no sumar stock | 5 operaciones/5 detalles; stock de referencia 10 | APROBADO | `final.jsonl` |
| CP-A4-005 | A4: solo el archivo del hostname actual también se recupera | Dos operaciones solo en el hostname actual | Recuperarlas también al abrir el alias anterior | Dos wire idénticos recuperados | APROBADO | `final.jsonl` |
| CP-A4-006 | A4: UUID idénticos en las dos fuentes no duplican cabecera ni detalles | Dos bases copias con dos UUID idénticos | Una cabecera y detalle por UUID | 2 operaciones y 2 detalles | APROBADO | `final.jsonl` |
| CP-A4-007 | A4 controlador: recuperación fallida no abre cola ni programa envíos | Opener lanza error; cliente HTTP registra llamadas | No habilitar cola ni enviar | local nulo y 0 solicitudes | APROBADO | `final.jsonl` |
| CP-A4-008 | A4: UUID con envelope divergente revierte toda la importación | Mismo UUID, efectivo del envelope modificado | Rechazar y revertir toda la recuperación | Error explícito; destino sin operaciones ni marcador | APROBADO | `final.jsonl` |
| CP-A4-009 | A4: UUID con detail divergente revierte toda la importación | Mismo UUID, cantidad de detalle diferente | Rechazar sin escoger un contenido | Rollback completo del destino | APROBADO | `final.jsonl` |
| CP-A4-010 | A4 controlador: refresh conserva historial y desactiva captura hasta renovar catálogo | Una operación recuperada y catálogo con permiso vigente | Mostrar historial; bloquear captura hasta renovar | Historial 1; validLease false, después true | APROBADO | `final.jsonl` |
| CP-A4-011 | A4: UUID con state divergente revierte toda la importación | Mismo UUID, PENDIENTE frente a CONFIRMADA | Detener sin escoger estado | Rollback completo del destino | APROBADO | `final.jsonl` |
| CP-A4-012 | A4: rechaza envelope con tenant_id ajeno sin exponer operaciones | Envelope con tenant_id=999 | No importar ni exponer otra empresa | StateError y recuperación detenida | APROBADO | `final.jsonl` |
| CP-A4-013 | A4: rechaza envelope con author_id ajeno sin exponer operaciones | Envelope con author_id=999 | No importar otro autor | StateError y recuperación detenida | APROBADO | `final.jsonl` |
| CP-A4-014 | A4: rechaza envelope con branch_id ajeno sin exponer operaciones | Envelope con branch_id=999 distinto de cabecera | Rechazar identidad/referencias incompatibles | StateError y recuperación detenida | APROBADO | `final.jsonl` |
| CP-A4-015 | A4: snapshot de otra cuenta se rechaza aunque el envelope sea propio | Snapshot de usuario 12 en archivo 7:11 | Bloquear datos de perfil distinto | Recuperación rechazada | APROBADO | `final.jsonl` |
| CP-A4-016 | A4: no recupera bases de otra empresa ni de otro usuario | Abrir perfiles 8:11 y 7:12 con datos previos de 7:11 | No abrir/exponer la cola ajena | Ambos historiales y snapshots vacíos | APROBADO | `final.jsonl` |
| CP-A4-017 | A4: namespace inválido no abre base | Namespace ../7:11 | Rechazar antes de crear archivos | StateError; directorio sin archivos | APROBADO | `final.jsonl` |
| CP-A4-018 | A4: host local mantiene su archivo existente sin importar cola HTTPS | Colas separadas localhost y HTTPS | Conservar archivo local y no importar HTTPS | Solo los dos UUID locales; sin flag de recuperación | APROBADO | `final.jsonl` |
| CP-A4-019 | A4: no migra mientras la fuente tenga un bloqueo vigente | sync_lock futuro; luego se simula vencimiento | Detener mientras esté activo; importar al vencer | Primero error; después 2 operaciones | APROBADO | `final.jsonl` |
| CP-A4-020 | A4: ENVIANDO se recupera después de expirar lock sin alterar wire ni intentos | Dos ENVIANDO, attempts=3 y sin lock vigente | PENDIENTE en destino sin cambiar fuente/wire | Intentos 3; fuente sigue ENVIANDO; UUID iguales | APROBADO | `final.jsonl` |
| CP-A4-021 | A4: reabrir no duplica ni degrada CONFIRMADA a PENDIENTE antigua | Resultado canónico confirmado y fuentes PENDIENTE sin cambios | Conservar resultado tras tres reaperturas | Filas y wire iguales; no degradación de estado | APROBADO | `final.jsonl` |
| CP-A4-022 | A4: cambio tardío de estado en fuente importada no reemplaza resultado canónico | Fuente ya importada cambia su estado a RECHAZADA | Bloquear la nueva divergencia | Error; no sustituye resultado canónico | APROBADO | `final.jsonl` |
| CP-A4-023 | A4: referencias y enlace de revisión se conservan | Operación original en conflicto y revisión enlazada | Conservar original, resolved, detalle y vínculo | 3 cabeceras y sus detalles iguales; FK válidas | APROBADO | `final.jsonl` |
| CP-A4-024 | A4: exige catálogo fresco para capturas y mantiene wire de pendientes | Captura antes de renovar; snapshot ajeno; renovación propia | Bloquear primeras dos acciones y permitir captura con catálogo nuevo | Flag conserva hasta descarga válida; luego 3 operaciones | APROBADO | `final.jsonl` |
| CP-A4-025 | A4: error SQL real revierte fuentes completas y conserva base canónica previa | Trigger de fallo durante segundo origen; destino previo con una operación | Rollback de ambas fuentes y marcadores; reintento posterior único | Destino previo idéntico; después 4 operaciones | APROBADO | `final.jsonl` |
| CP-A4-026 | A4: fuente corrupta provoca rollback de la otra fuente válida | Un origen válido y otro archivo no SQLite | Revertir también el primer origen | Destino sin operaciones | APROBADO | `final.jsonl` |
| CP-A4-027 | A4: FK huérfana en fuente se conserva y bloquea recuperación | Detalle sin cabecera en origen | Rechazar sin eliminar ni reparar silenciosamente | Recuperación detenida | APROBADO | `final.jsonl` |
| CP-A4-028 | A4: identidad canónica ajena se rechaza | Meta de destino con namespace distinto | Bloquear acceso al archivo incompatible | Recuperación detenida | APROBADO | `final.jsonl` |
| CP-A4-029 | A4: variante con producto incompatible entre fuentes revierte importación | Mismo ID de variante, producto diferente en la otra fuente | Rechazar referencias incompatibles | Rollback completo | APROBADO | `final.jsonl` |
| CP-A4-030 | A4: versión de fuente desconocida no se migra silenciosamente | PRAGMA user_version=2 en fuente v1 | No migrar una versión desconocida | Error explícito; archivo conservado | APROBADO | `final.jsonl` |
| CP-A4-031 | A4: falta real de páginas SQLite revierte importación y conserva fuentes | max_page_count limitado y producto de 500000 caracteres | Fallar y revertir sin cambiar destino ni fuente | Snapshots destino y bytes fuente idénticos | APROBADO | `final.jsonl` |
| CP-A4-032 | A4: aperturas concurrentes de ambos alias importan cada UUID una sola vez | Abrir ambos alias simultáneamente sobre el mismo destino | Serializar importación y no duplicar UUID | Ambas aperturas muestran 2 operaciones/2 detalles | APROBADO | `final.jsonl` |
| CP-A4-033 | A4 HTTP: recupera SQLite real, reenvía respuesta perdida y conserva UUID sin duplicar | SQLite v1 con venta/reserva; respuesta perdida y tres envíos reales | Una venta y una reserva centrales, mismos UUID | 2 sync; 1 venta; 1 reserva; 1 movimiento; stock 4; retención 1 | APROBADO | `runtime.jsonl` |
| CP-A4-034 | A4 HTTP: sesión de la segunda empresa abre otra base sin historial ajeno | Sesión real de prueba de la segunda empresa | No exponer la SQLite de la primera empresa | Historial vacío; snapshot nulo; sin escrituras comerciales ajenas | APROBADO | `runtime.jsonl` |
| CP-A4-035 | A4 aceptación posterior: recupera los cinco UUID de los archivos del diagnóstico sin alterar originales | Copias de ambos archivos del diagnóstico, con 4+1 UUID | Recuperar cinco y abrir desde ambos alias | 5 wire y 5 detalles; archivos originales idénticos | APROBADO | `acceptance.jsonl` |

| ID pendiente | Escenario | Entrada | Resultado esperado | Resultado obtenido | Estado | Evidencia |
|---|---|---|---|---|---|---|
| CP-A4-P01 | Actualización y reinicio reales de aplicación | Dispositivo de pruebas con SQLite de versión anterior | Recuperación, sesión y reintentos íntegros con plugins nativos | No ejecutado | PENDIENTE | No existe; requiere distribución del cliente |

Los escenarios A4-13 a A4-21 diseñados en el diagnóstico quedan cubiertos por los casos automatizados anteriores. A4-22 corresponde a CP-A4-P01 y permanece pendiente. La aceptación fallida previa A4-11 se contrasta con CP-A4-035.

### Activación y riesgos pendientes

La corrección está aplicada al código local, **no a un APK/dispositivo instalado**. Para activarla en un teléfono se deberá distribuir el cliente actualizado y verificar con una copia controlada de sus datos. No requiere reconstruir Docker, cambiar PostgreSQL ni ejecutar scripts de migración sobre la demostración. La recuperación ocurre al abrir la función offline desde el cliente actualizado, para el perfil activo.

Una fuente con colisiones, corrupción, identidad incompatible o bloqueo activo queda conservada y requiere revisión; no se fuerza su importación. Los orígenes no incluidos expresamente continúan aislados. Conservar originales aumenta temporalmente el uso de disco; la falta de espacio fue ensayada y produce rollback. No reinstalar eliminando datos ni bajar a una versión antigua durante la aceptación: un cliente anterior no conoce la nueva base canónica. La aceptación nativa y la distribución quedan pendientes; el fallo APK se tratará como tarea independiente.

Se detiene el trabajo de A4 después de esta implementación/verificación. No se continúa con A5 ni A6.


## Compilación APK posterior — 2026-11-07

Se resolvió por separado el bloqueo de APK: propiedad de compatibilidad AGP para WebView 1.1.3 y pin dirigido de permission_handler 12.0.3 / Android 13.0.1. Se generaron/verificaron dos APK debug (habitual y local), con análisis completo sin incidencias y 48 pruebas Flutter estándar aprobadas. Los nueve archivos de A4 conservan sus hashes. Las 51 pruebas de la fase A4 siguen como evidencia histórica; en esta fase se repitieron 48, sin Docker/PostgreSQL.

No había Android conectado: instalación, cámara/WebView y aceptación nativa de A4 permanecen pendientes. La corrección del build no marca CP-A4-P01 como aprobado. [Informe APK y lista manual](CAPITULO_V_COMPILACION_APK_ANDROID.md).
