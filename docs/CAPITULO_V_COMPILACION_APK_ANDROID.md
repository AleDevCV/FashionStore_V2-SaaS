# CAPÍTULO V — Corrección de compilación APK Android y preparación de A4

Fecha: 2026-11-07T16:28:00.221422-04:00 (America/La_Paz). **Compilación APK corregida y verificada; aceptación en Android real pendiente.** No se modificaron Docker, PostgreSQL o producción. No se avanzó con A5/A6 ni se instaló la app en ningún dispositivo.

## 5.2. Pruebas funcionales

Se generaron dos APK debug universales de FashionStore P2. Se verificaron firma APK v2, integridad ZIP, identificador, versión, SDK y arquitecturas. No se declara ejecución funcional en Android: `adb devices -l` no mostró dispositivos conectados.

| Artefacto | Backend compilado | Uso previsto |
|---|---|---|
| `FashionStore-P2-A4-local-debug.apk` | `http://127.0.0.1:8002` | Pruebas controladas mediante adb reverse a un backend efímero identificado |
| `FashionStore-P2-A4-normal-debug.apk` | `https://fashionstore.aledevcv.me` | Configuración habitual; recuperación legacy únicamente offline durante esta validación, sin pruebas comerciales sobre producción |

Ambos: `com.fashionstore.fashionstore_mobile.p2`, versión `0.1.0`/código `1`, mínimo Android API 24, target/compile SDK 36; ABIs `armeabi-v7a`, `arm64-v8a`, `x86_64`. Conservan el mismo certificado de depuración. Instalar una variante reemplaza a la otra bajo el mismo paquete, conservando datos cuando la firma/versionado sean compatibles.

## 5.3. Pruebas de integración

Se verificó la integración de Flutter 3.47.2/Dart 3.13.2, Gradle 9.3.1, AGP 9.1.0, Kotlin 2.4.0, Java 25.0.2 y Android SDK 36 con las dependencias nativas. El plugin WebView original 1.1.3 se conservó y compiló; no se editó su caché global. El permiso de cámara conserva la API `Permission.camera.request()` usada por la aplicación.

Las 48 pruebas Flutter actuales aprobaron con la resolución nueva, incluidas recuperación SQLite, fuentes en solo lectura, UUID, rollback, concurrencia, separación de cuentas y contratos A3. No se repitieron las tres pruebas A4 que requieren fixtures externas/HTTP: las 51 anteriores pertenecen a la fase A4 y sus evidencias siguen intactas. No se hicieron llamadas a Docker o PostgreSQL en esta tarea.

Se conservan advertencias de KGP en `firebase_core`, APIs Java antiguas y acceso nativo de Java. No bloquearon los APK. La documentación Flutter describe el soporte de compatibilidad KGP/DSL; no se realizó una migración general del toolchain. [Guía oficial Flutter](https://docs.flutter.dev/release/breaking-changes/migrate-to-built-in-kotlin/for-app-developers).

## 5.4. Corrección de errores

### Causa 1 — plugin WebView y AGP

El fallo original se reprodujo con el código A4 actual, igual que en los logs anteriores a A3: `flutter_inappwebview_android-1.1.3/android/build.gradle`, línea 44, llama a `getDefaultProguardFile('proguard-android.txt')`. AGP 9 cambió la aceptación de ese archivo heredado. [Notas oficiales Android](https://developer.android.com/build/releases/agp-9-0-0-release-notes).

Corrección mínima: añadir `android.r8.proguardAndroidTxt.disallowed=false` a `android/gradle.properties`, conservando las reglas anteriores del plugin. Esta compatibilidad permitió superar su evaluación. No se cambió código del plugin ni versiones de Flutter/Gradle/AGP, y no se deshabilitó R8 globalmente. Es una medida temporal: debe revisarse al actualizar el plugin o AGP; la configuración debug queda validada y no se certifica una compilación release/R8 optimizada.

### Causa 2 — permiso Android y SDK

Al superar el primer bloqueo apareció otro requisito preexistente: `permission_handler 13.0.2` fija `permission_handler_android ^14.1.0`, que solicita `android-37`. Gradle instaló la plataforma disponible `android-37.0`, pero no pudo resolver el hash solicitado. El mantenedor registra este mismo problema; elevar únicamente compileSdk no lo soluciona. [Incidencia del mantenedor](https://github.com/Baseflow/flutter-permission-handler/issues/1556).

Se fijó solo `permission_handler: 12.0.3`, compatible con SDK 35 o superior y la API utilizada. Resolvió la implementación Android 13.0.1. Se conservaron compileSdk/targetSdk 36 y minSdk 24. La resolución cambió **exactamente dos paquetes**; todos los demás bloques del lockfile permanecen iguales. [Versión/documentación del mantenedor](https://pub.dev/packages/permission_handler/versions/12.0.3).

Impacto: se debe comprobar la concesión/denegación del permiso de cámara en los Android de destino, especialmente permisos de un solo uso. No se cambiaron permisos declarados en AndroidManifest, funcionalidades offline, SQLite, sincronización, autenticación, URLs por defecto, identificador o versión de la app.

### Archivos realmente modificados

1. `Parcial2_mobile/android/gradle.properties`: propiedad de compatibilidad y comentario.
2. `Parcial2_mobile/pubspec.yaml`: pin dirigido de permission_handler.
3. `Parcial2_mobile/pubspec.lock`: solo los dos paquetes indicados.

Los **81 archivos restantes** y los nueve fuentes/pruebas A4 conservan sus hashes. Se guardaron copias previas y un diff exclusivo. No se actualizaron dependencias indiscriminadamente. En el entorno de herramientas, Gradle descargó SDK 37.0 durante el diagnóstico y CMake 3.22.1 para dependencias nativas ya existentes; no se borraron instalaciones ni se aceptaron licencias mediante automatización.

## 5.5. Resultados y evidencias

| Verificación de esta tarea | Resultado |
|---|---|
| Reproducción original sin corrección | Falló en ProGuard de WebView; evidencia conservada |
| Propiedad AGP sin pin de permisos | Superó WebView; falló al resolver android-37; evidencia conservada |
| APK debug con corrección completa | **Aprobado**, Flutter/Gradle exit code 0 |
| APK debug dirigido a entorno local | **Aprobado**, Flutter/Gradle exit code 0 |
| Flutter analyze completo | **No issues found** |
| Flutter test, suite completa estándar | **48 aprobadas; 0 fallidas; 0 omitidas** |
| Firma, ZIP y metadatos de ambos APK | **Aprobados** |
| Instalación/lanzamiento en Android y lista manual | **Pendientes: 12 casos; 0 ejecutados** |

Son cuatro intentos de compilación: dos fallos de diagnóstico resueltos y dos variantes finales exitosas. No se ocultan los fallos iniciales ni se suman builds/verificaciones a las 48 pruebas para inflar el total. Un fallo de codificación de consola al imprimir el símbolo de éxito ocurrió después del primer build aprobado; el log de Flutter y su código 0 se conservaron y el APK fue verificado de forma independiente.

**APK local:** `C:\Users\Klara\Documents\Codex\2026-11-06\https-github-com-aledevcv-fashionstore-v2\outputs\APK_FashionStore_A4\FashionStore-P2-A4-local-debug.apk` — 197649091 bytes, SHA-256 `721eb810e8742a842c0af9882d253b53a3a7707960c970eba8901b947b0a9326`.

**APK habitual:** `C:\Users\Klara\Documents\Codex\2026-11-06\https-github-com-aledevcv-fashionstore-v2\outputs\APK_FashionStore_A4\FashionStore-P2-A4-normal-debug.apk` — 171734751 bytes, SHA-256 `dd4cc8cc26f8ef32a95bcf1fe8b6287d1e70cf26d9a9d9c3b6111c1ecf6e1ff9`.

Certificado público de firma SHA-256 común: `35930069a1ca21a3b4643f3d5f44d221a48ddb3e4f20bd0d6ab12b2de561e1ea`. Los APK son de depuración; no constituyen despliegue de producción ni firma de publicación.

Evidencia: [resumen](APK_compilacion_evidencias/resumen.json), [JUnit Flutter](APK_compilacion_evidencias/pruebas-flutter.xml), [análisis](APK_compilacion_evidencias/analysis.log), [fallo original](APK_compilacion_evidencias/before.log), [build final](APK_compilacion_evidencias/pinned-build.log), [build local](APK_compilacion_evidencias/local-build.log). Firmas, metadata y resolución exacta de dependencias están en la misma carpeta.

## 5.6. Instalación y casos manuales pendientes

### Instalar conservando datos

Conectar un Android de pruebas, habilitar depuración USB y autorizar el equipo. Confirmar previamente que el paquete instalado tiene el mismo applicationId, una versión compatible y el mismo certificado. Conservar una copia consistente de los datos SQLite del dispositivo y anotar UUID/estados antes de la actualización. El paquete fue compilado con firma debug; si el instalado usa otra firma, **no desinstalar ni borrar datos para sortear el error**. Se requiere una compilación firmada con la clave autorizada correspondiente.

```powershell
$adbPath = 'C:\Users\Klara\AppData\Local\Android\sdk\platform-tools\adb.exe'
& $adbPath devices -l
& $adbPath install -r 'C:\Users\Klara\Documents\Codex\2026-11-06\https-github-com-aledevcv-fashionstore-v2\outputs\APK_FashionStore_A4\FashionStore-P2-A4-local-debug.apk'
```

`install -r` solicita actualización conservando datos. No ejecutar `uninstall`, `pm clear` ni borrar datos de la app. No se ejecutó ninguno de estos comandos de instalación durante esta tarea.

El APK local utiliza el puerto 8002 del teléfono. Para tráfico de prueba, redirigirlo únicamente al puerto de un **backend efímero ya identificado**, por ejemplo 18084 si sigue disponible el entorno aislado de A4:

```powershell
# Solo cuando 18084 esté confirmado como backend efímero de pruebas.
& $adbPath reverse tcp:8002 tcp:18084
```

Esto configura el enlace USB, no Docker. No redirigir las pruebas comerciales al PostgreSQL persistente de demostración ni a producción. Si no hay backend efímero disponible, dejar sincronización pendiente; no se crea ni modifica uno en esta tarea. El puerto web 8082 solo se habilitará cuando exista un frontend de prueba identificado y sea necesario.

La política A4 separa orígenes locales de los dos alias HTTPS: el APK local no debe mostrar colas de producción por coincidencia de IDs. Para verificar exclusivamente la recuperación de archivos HTTPS anteriores, usar el APK habitual en un dispositivo de prueba preparado, **completamente sin red durante todo el ensayo**. Cerrar forzadamente esa app antes de restablecer conectividad. La prueba completa de migración de alias más sincronización exige un banco Android y backend equivalente aislados; permanece M12 pendiente. No se deben trasladar envelopes de producción a otro despliegue, cambiarles UUID/empresa ni rehacer sus permisos.

| ID | Escenario | Entrada/precondición | Resultado esperado | Resultado obtenido | Estado |
|---|---|---|---|---|---|
| M01 | Instalación en sitio | Mismo applicationId y certificado que la versión instalada | adb install -r conserva datos; app abre | No hay dispositivo conectado | PENDIENTE |
| M02 | Conexión al backend efímero | APK local; USB reverse a un backend de prueba identificado; cuenta autorizada | Login/contexto/catálogo de su empresa y sucursal | No ejecutado | PENDIENTE |
| M03 | Venta y reserva offline | Catálogo de prueba descargado; modo avión; cantidades/efectivo válidos | UUID únicos y PENDIENTE; detalles y sucursal correctos | No ejecutado | PENDIENTE |
| M04 | Cierre forzado y reapertura | Pendientes anotados antes; am force-stop y reabrir | Mismos UUID, detalles, cantidades e importes | No ejecutado | PENDIENTE |
| M05 | Reinicio de Android | Datos de prueba persistidos; reiniciar teléfono | Perfil/SQLite íntegros; cola recuperable | No ejecutado | PENDIENTE |
| M06 | Recuperación nativa entre alias | Dispositivo de prueba con archivos v1 de ambos alias y perfil correcto; APK habitual totalmente sin red | Se recuperan todos los UUID y se conservan fuentes; catálogo requiere renovación | No ejecutado | PENDIENTE |
| M07 | Separación entre cuentas | Cambiar empresa/usuario con datos de prueba | No mostrar catálogo ni operaciones ajenas | No ejecutado | PENDIENTE |
| M08 | Dos sucursales y retenciones locales | Pendientes de dos sucursales autorizadas | Sucursal original y detalles conservados; disponibilidad no sumada entre cachés | No ejecutado | PENDIENTE |
| M09 | Sincronización controlada | Solo APK local y backend efímero correspondiente; restablecer conexión | Un resultado por UUID, estados persistidos; sin escritura en demostración/producción | No ejecutado | PENDIENTE |
| M10 | Respuesta perdida y reintento | Reenviar mismos UUID y contenido en el backend efímero | Una venta/reserva central; UUID con otro contenido rechazado | No ejecutado | PENDIENTE |
| M11 | Cámara y WebView | Aceptar/denegar permiso, abrir y cerrar vestidor/checkout sin pagos | Diálogo y WebView operativos; denegación manejada sin cierre inesperado | No ejecutado | PENDIENTE |
| M12 | Actualización completa A4 | Banco Android autorizado con datos legacy y backend aislado equivalente | Recuperación + renovación + sincronización en una misma instalación sin pérdida ni duplicación | No ejecutado | PENDIENTE |

Para cada caso registrar fecha, Android/modelo, APK y SHA, perfil/empresa/sucursal de prueba, UUID y estado antes/después, capturas y logcat depurado sin tokens. En los casos centrales guardar conteos de venta/reserva/operacion_sync del backend efímero y demostrar que repetir un UUID no crea otro documento. Todos los resultados anteriores siguen **pendientes**, no aprobados por la sola compilación.

### Reproducción del build

```powershell
Set-Location 'C:\Examen si2 FASHIONSTORE\Parcial2_mobile'
C:\flutter\bin\flutter.bat pub get --enforce-lockfile
C:\flutter\bin\flutter.bat analyze --no-pub
C:\flutter\bin\flutter.bat test --no-pub
C:\flutter\bin\flutter.bat build apk --debug --no-pub --dart-define=API_BASE_URL=http://127.0.0.1:8002 --dart-define=WEB_BASE_URL=http://127.0.0.1:8082
```

El resultado estándar será `build/app/outputs/flutter-apk/app-debug.apk`. Los APK entregados se generaron en la copia aislada y se copiaron a `outputs/APK_FashionStore_A4/`, no se ejecutaron sobre el proyecto de demostración.

**Cierre:** el bloqueo de compilación está resuelto. A4 conserva sus fuentes y pruebas; su aceptación nativa continúa pendiente. No se modificaron Docker, PostgreSQL, producción, secretos ni A5/A6.
