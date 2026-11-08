# Capítulo V — Validación de A4 en Android físico

Fecha: 7 de noviembre de 2026. Proyecto: FashionStore V2 SaaS, segundo examen parcial de Sistemas de Información II.

**Resultado:** se comprobó recuperación, persistencia e idempotencia sobre SQLite nativo en un Xiaomi 13T Pro. De los 12 casos documentados, **8 quedan aprobados en el alcance descrito y 4 parcialmente verificados**. No se declara aprobada la aceptación completa de una actualización histórica entre hostnames. No se encontraron fallos funcionales en las comprobaciones concluyentes; las condiciones pendientes se detallan por caso.

## Entorno y seguridad de la ejecución

| Elemento | Identificación comprobada |
|---|---|
| Dispositivo | Xiaomi 13T Pro, modelo 23078PND5G, Android 16/API 36, arm64-v8a |
| SQLite del teléfono | 3.44.5; esquema de la aplicación versión 1; claves foráneas habilitadas |
| Paquete | `com.fashionstore.fashionstore_mobile.p2`, versión 0.1.0/código 1, debug |
| APK instalado | `FashionStore-P2-A4-local-debug.apk`; SHA-256 `721eb810e8742a842c0af9882d253b53a3a7707960c970eba8901b947b0a9326` |
| Certificado instalado/local | SHA-256 `35930069a1ca21a3b4643f3d5f44d221a48ddb3e4f20bd0d6ab12b2de561e1ea` |
| API del APK | Teléfono `http://127.0.0.1:8002` → USB reverse → PC `http://127.0.0.1:18084` |
| API de prueba | Contenedor `fashionstore-a4-runtime`, imagen `sha256:cf76bebff7a472c34b83872845380d3c933fc36d8793259775e244280e81eea0` |
| Base de prueba | `fashionstore_p2_test`, contenedor `fashionstore_a4_test-db-1`, almacenamiento **tmpfs**, sin volumen persistente |
| Datos sintéticos | Empresa A 6/usuario 5/sucursales 5 y 7; empresa B 7/usuario 6/sucursal 6 |

El puerto 8002 del teléfono se enlazó al **18084** del PC, no al 8002 de la demostración persistente. Los nombres HTTPS aprobados se utilizaron como identificadores de almacenamiento en los ejercicios instrumentados; no se enviaron peticiones a esos servidores. No se realizaron pagos ni llamadas a Decart.

Inicialmente no había un paquete FashionStore instalado. Se realizó instalación inicial y, posteriormente, una reinstalación controlada del mismo APK con `adb install -r`, después de comprobar paquete y certificado y de guardar dos pendientes. No se desinstaló la aplicación, no se ejecutó borrado de datos y no se reemplazaron archivos SQLite existentes. Los archivos de origen del ensayo se crearon nuevos con datos sintéticos.

Las acciones por interfaz se ejecutaron mediante ADB. Las comprobaciones instrumentadas invocaron métodos existentes dentro del **APK local instalado**, mediante su servicio debug; utilizaron SQLite Android y HTTP real contra tmpfs. No se modificó ni recargó el código de la aplicación para estas pruebas. Esto no equivale a haber ejecutado todos los pasos por la interfaz del APK habitual.

## 5.2. Pruebas funcionales

Se verificaron las siguientes funcionalidades:

- Inicio de sesión, contexto de empresa y descarga de catálogo desde el backend efímero.
- Registro por interfaz de una venta y una reserva con el backend inaccesible al retirar su enlace USB. Se conservaron UUID, detalles y estado pendiente. No se activó modo avión ni se alteraron Wi-Fi/datos móviles del usuario.
- Cierre forzado, reapertura y reinicio real de Android. Los dos pendientes mantuvieron sus bytes, UUID, detalles e importes.
- Reinstalación del mismo APK con firma compatible y `-r`, conservando los dos pendientes.
- Recuperación nativa controlada desde dos archivos v1: uno con cuatro operaciones y otro con cinco, con cuatro UUID compartidos. La base canónica terminó con cinco operaciones y cinco detalles, sin duplicar los compartidos.
- Reapertura mediante ambos alias con la misma base canónica. Los originales permanecieron intactos y el catálogo exigió renovación antes de permitir una nueva captura.
- Cambio real a la cuenta B por interfaz: cero operaciones y catálogo offline ajeno no visible. El historial de A permaneció conservado. Una comprobación adicional de un namespace de otro usuario fue solo de almacenamiento, sin autenticar una tercera cuenta.
- Conservación de sucursal y retenciones locales: stock 5 menos 2 pendientes = 3 disponibles en sucursal 5; stock 8 menos 3 pendientes = 5 en sucursal 7. No se sumaron disponibilidades entre sucursales.
- Sincronización de cinco UUID, reintentos tras respuesta no aplicada localmente y rechazo de reutilización del UUID con contenido diferente.
- Permiso de cámara concedido y denegado, apertura/cierre del vestidor y checkout con HTML local. La denegación mostró el mensaje previsto y permitió volver sin caída. No se probó captura de imagen, calidad de AR ni pago real.

## 5.3. Pruebas de integración

| Integración | Evidencia y alcance |
|---|---|
| ADB → Package Manager Android | Paquete/certificado comprobados; instalación inicial y posterior `install -r`; sin desinstalar ni limpiar datos |
| SessionVault/AuthService → perfil local | Cuenta A `6:5`; cambio autenticado a B `7:6`; B no obtuvo el historial de A |
| LocalDatabase → sqflite → SQLite Android | SQLite 3.44.5; seis archivos finales con `integrity_check = ok` y cero errores FK |
| Recuperación → fuentes v1 → base canónica | Cinco UUID únicos, cinco detalles; fuentes leídas sin cambios; apertura por ambos alias al mismo destino |
| OfflineController → LocalDatabase → ApiClient → FastAPI → PostgreSQL tmpfs | Cinco resultados confirmados; dos ventas, tres reservas, dos salidas de inventario y tres retenciones centrales |
| Reintento → idempotencia del backend | Reenvíos conservan cinco registros centrales; contenido diferente devuelve `RECHAZADA`, sin cambiar el resultado original confirmado |
| permission_handler → Android | Estado concedido observado; denegación explícita posterior y aviso visible; permiso final denegado |
| flutter_inappwebview → WebView Android → página local | Renderizado HTTP local, cierre mediante `cerrarProbador` y cierre del checkout; sin Stripe/Decart externos |

Para simular respuesta perdida se enviaron las cinco operaciones y se omitió aplicar su respuesta en SQLite. Después se abrió el controlador offline y se repitió la sincronización con los mismos UUID. Los resultados quedaron guardados en el dispositivo y PostgreSQL conservó solamente dos ventas y tres reservas. No se simuló una interrupción física del cable exactamente durante una respuesta HTTP.

## 5.4. Corrección de errores

El defecto A4 previamente corregido provenía del nombre SQLite derivado de la URL del backend: cambiar de hostname podía abrir otro archivo y dejar los pendientes anteriores fuera de la vista. La solución aprobada reconoce únicamente los dos alias HTTPS establecidos, usa una identidad canónica por despliegue/empresa/usuario y recupera datos de forma aditiva y transaccional, conservando los originales. Los demás orígenes siguen separados.

**En esta validación no se modificó código funcional.** Se verificaron 35 hashes de archivos frente a las evidencias anteriores: nueve archivos A4, tres de compilación APK y archivos de C1/A1/A2/A3 aplicables, respetando que A3 reemplazó posteriormente el router de movimientos de C1. No se repitió aquí la regresión completa backend o Flutter.

Los componentes A4 ejercitados fueron `lib/core/config.dart`, `lib/core/session_vault.dart`, `lib/features/offline/local_database.dart`, `database_recovery.dart`, `offline_controller.dart` y sus servicios de sesión/API existentes. No se introdujeron frameworks ni cambios de esquema PostgreSQL.

Se conservan las incidencias del procedimiento de prueba:

1. Una aserción diagnóstica inicial comparó cadenas JSON y señaló diferencia por el orden de claves del resultado cacheado en PostgreSQL. La comparación posterior normalizó el orden y comprobó igualdad de valores y ausencia de duplicaciones. El archivo inicial con el error se conserva; no fue un cambio de aplicación ni una vulnerabilidad corregida.
2. La primera página de prueba WebView devolvió `ERR_EMPTY_RESPONSE` por el servidor de diagnóstico inaccesible desde ADB. Al ejecutar la página en el loopback accesible del host, la misma pantalla renderizó y cerró correctamente. No se cambió WebView para resolverlo.
3. Los ajustes de conexión del depurador y del serializador de resultados afectaron únicamente al banco de diagnóstico, sin modificar el APK o sus fuentes.

Archivos nuevos de entrega: este informe, su resumen JSON y el directorio de evidencias de Android. En el proyecto se incorpora una copia como `docs/CAPITULO_V_A4_ANDROID_REAL.md`, evidencias en `docs/evidencias/a4-android-real/` y una nota aditiva en `docs/TRAZABILIDAD.md`. Los informes anteriores se conservan como evidencia histórica.

## 5.5. Resultados de las pruebas

| Grupo | Aprobados | Fallidos funcionales | Parciales / pendientes de aceptación completa |
|---|---:|---:|---:|
| Casos documentados M01–M12, esta validación física | **8** | **0** | **4** |
| Nuevas ejecuciones de suite automatizada Flutter en esta validación | 0 | 0 | No se volvió a ejecutar la suite |

Los cuatro casos parciales son M01, M03, M06 y M12: sus comprobaciones ejecutadas fueron satisfactorias, pero no se certifican las precondiciones históricas o variantes exactas pendientes. No hay casos totalmente sin abordar; quedan **cuatro aceptaciones completas pendientes**, no cuatro defectos demostrados. Las incidencias del banco descritas en 5.4 no se cuentan como fallos funcionales de los casos.

La fase anterior de implementación A4 registró 51 pruebas automatizadas aprobadas; la corrección de compilación APK repitió 48. Son evidencias históricas parcialmente superpuestas y no se suman entre sí ni a estos 12 casos manuales.

Resultados cuantitativos comprobados en esta fase:

- Cinco UUID únicos recuperados y cinco detalles; todos conservan sus envoltorios y asociación empresa/usuario/sucursal.
- Cinco resultados `CONFIRMADA` tanto en la base canónica de ensayo como en el namespace loopback usado por la interfaz.
- Dos archivos fuente conservados byte a byte después de recuperación, sincronización y reintentos.
- Seis archivos SQLite finales íntegros; cero errores de claves foráneas.
- Empresa A: dos ventas, tres reservas, cinco registros de sincronización y dos movimientos centrales; empresa B: cero operaciones centrales.
- Una reutilización divergente de UUID rechazada, sin sobrescribir el resultado original.
- Treinta y cinco hashes de archivos coincidentes; cuatro contenedores persistentes de demostración con los mismos identificadores, imágenes, horas de arranque y montajes que al inicio.

No se ejecutaron sentencias SQL sobre la base persistente durante esta tarea. La conservación de sus contenedores y volúmenes está comprobada; no se repitió una huella fila por fila de sus datos comerciales. Las escrituras de negocio se limitaron a las empresas sintéticas de tmpfs.

## 5.6. Casos de prueba

Las evidencias enlazadas están en `evidencias/a4-android-real/` junto a la copia de este informe guardada en `docs/`.

| ID | Escenario y entrada | Resultado esperado | Resultado obtenido | Estado | Evidencia |
|---|---|---|---|---|---|
| M01 | Instalación/actualización conservando datos; mismo paquete y certificado | `install -r` conserva pendientes y app abre | No existía versión histórica. Instalación inicial y reinstalación controlada del mismo APK; dos pendientes/detalles y SHA SQLite iguales | **PARCIAL**: falta actualización desde un APK histórico | `installation.json`, `installation-update.json`, `M01-update-preservation.json` |
| M02 | Login A y catálogo; APK local → API tmpfs | Perfil y catálogo de empresa/sucursal autorizadas | Sesión 6:5, sucursal 5, catálogo y SQLite nativo comprobados | **APROBADO** | `native-sqlite-info.json`, `06-catalog-result.png` |
| M03 | Venta y reserva sin backend; catálogo previo, cantidad 1 | UUID distintos, pendientes y detalles íntegros | Captura por interfaz con enlace USB de API retirado; UUID/stock local conservados. No se activó modo avión | **PARCIAL**: variante modo avión pendiente | `native-two-pending.json`, `two-pending-before-update-sqlite.json`, `09-sale-pending.png`, `12-reservation-pending.png` |
| M04 | Cierre forzado y reapertura con pendientes | Mismos UUID, cantidades, importes y detalles | Reapertura offline y conservación de los registros. La pantalla inicial de login no eliminó el perfil ni la cola | **APROBADO** | `pending-before-reopen-sqlite.json`, `10-reopened-offline.png`, `11-reopened-pending.png` |
| M05 | Reinicio físico de Android y desbloqueo por el usuario | Perfil/SQLite y cola recuperables | Cambió boot_id; arranque completado; dos pendientes, dos detalles y bytes SQLite idénticos | **APROBADO** | `M05-reboot-system.json`, `M05-persistence.json`, `two-pending-after-android-reboot-sqlite.json` |
| M06 | Dos fuentes v1 de los alias conocidos, cuatro y cinco operaciones | Cinco UUID únicos, originales intactos y renovación obligatoria | Métodos A4 del APK local recuperaron cinco; ambos alias abrieron el mismo archivo; nuevas capturas bloqueadas antes de renovar | **PARCIAL**: falta flujo por interfaz del APK habitual/cambio real de hostname | `native-aliases-recovered.json`, `native-recovery-fixtures.json`, `final-checks.json` |
| M07 | Cambiar por interfaz de A a B | No mostrar operaciones/catálogo offline ajenos | B 7:6 mostró cero operaciones y snapshot nulo; cinco de A conservadas. Namespace 6:999 adicional probado solo a nivel almacenamiento | **APROBADO** en cuentas A/B reales del ensayo | `native-account-isolation.json`, `14-company-B-offline-empty.png` |
| M08 | Pendientes en sucursales 5 y 7, misma variante | Detalles/sucursal conservados; retención local por sucursal | Disponibles 3 y 5, respectivamente, sin sumar cachés. Dos capturas por UI y tres mediante métodos nativos | **APROBADO**, instrumentado | `native-branch-availability.json`, `native-recovery-fixtures.json` |
| M09 | Restablecer API y sincronizar cinco UUID | Un resultado por UUID y persistencia local | Cinco confirmadas; dos ventas/tres reservas centrales; historial por interfaz conservado | **APROBADO** | `native-sync-confirmed.json`, `central-after-ui-replay.json`, `22-five-confirmed-history.png`, `23-confirmed-first-branch.png` |
| M10 | Respuesta no aplicada, reenvíos y mismo UUID con otro device_id | Reintento sin duplicación; contenido distinto rechazado | Respuestas equivalentes; cinco registros centrales; divergencia rechazada, originales confirmados intactos | **APROBADO**, instrumentado/HTTP | `native-sync-confirmed.json`, `native-divergent-uuid-rejected.json`, `central-after-ui-replay.json` |
| M11 | Permiso de cámara y vestidor/checkout con HTML local | Concesión/denegación y apertura/cierre sin caída ni pago | Estado concedido y renderizado observados; denegación explícita con aviso; cierre JS y checkout operativo | **APROBADO** como prueba de permisos/WebView | `native-camera-open.json`, `native-camera-reopen.json`, `18-camera-deny-dialog.png`, `19-camera-denied-no-crash.png`, `16-webview-local-rendered.png`, `17-checkout-local-rendered.png`, `webview-local-requests.jsonl` |
| M12 | Recuperación → renovación → sincronización en una instalación | Conservación completa sin duplicados | Cadena comprobada con fuentes sintéticas nativas y backend tmpfs; fuentes intactas y cinco confirmadas | **PARCIAL**: falta aceptación completa por UI sobre actualización histórica | `native-aliases-recovered.json`, `native-sync-confirmed.json`, `final-native-preservation-sqlite.json`, `final-checks.json` |

### Evidencias de conservación

| Fuente SQLite del ensayo | Tamaño | SHA-256 inicial y final, iguales |
|---|---:|---|
| Alias `fashionstore-v2.aledevcv.me`, perfil 6:5 | 69 632 bytes | `0102dafedafaaf60deaf52a52150a9b90e2e9c01ed43dbbd335688cc835520d0` |
| Alias `fashionstore.aledevcv.me`, perfil 6:5 | 69 632 bytes | `9ad5164f1b13663c585a46eadd96b932234a051a3dc9b4660518abdd68eace4b` |

La copia privada final de las bases ocupa 434 688 bytes, SHA-256 `1431efa1a9178aff31043094577ab8ae12413e121e115a838b49b67384229b0d`. Se mantiene fuera del informe público porque los SQLite pueden contener permisos de sesión. Las evidencias públicas contienen hashes, conteos, UUID sintéticos y resultados; no incluyen contraseñas, tokens, URI autenticada del depurador ni el serial USB completo.

Los originales conservan su estado pendiente como fotografías anteriores al ensayo; la base canónica y la base loopback activa tienen cinco confirmadas. No son ventas adicionales: los mismos UUID convergen a cinco registros centrales mediante idempotencia. El origen loopback permanece separado de los alias HTTPS conforme a la política A4.

### Trazabilidad y estado de activación

La evidencia afecta a RF-16/CU16, RF-17/CU17, RN-16, RN-18 y RN-19, según la trazabilidad A4 existente. La persistencia y recuperación de operaciones se relacionan con CU16; los resultados y reintentos idempotentes con CU17. No se agregan actores, clases ficticias, tablas ni diagramas para representar el banco de pruebas.

El APK debug local quedó instalado y abierto con datos sintéticos. El backend efímero y el reverse API se conservan para inspección: teléfono 8002 → PC 18084. Si se desconecta USB o se pierde la base tmpfs, esa conexión de pruebas dejará de estar disponible; los SQLite del teléfono se conservan. No hay activación pendiente en Docker persistente para A4. No se instaló el APK habitual ni se desplegó producción.

Se retiraron el enlace WebView y el forward fijo del depurador creados para este ensayo, y se detuvo el servidor web local de prueba utilizado. El permiso de cámara terminó denegado; no se alteraron las redes del teléfono. No se avanzó con A5 ni A6.

**Aceptación pendiente:** actualización desde una versión histórica compatible, variante modo avión y recuperación completa mediante la interfaz del APK habitual bajo un banco sin acceso a producción. Estas condiciones no deben presentarse como aprobadas a partir de esta ejecución controlada.
