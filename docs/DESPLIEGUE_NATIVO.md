# Producción nativa en el servidor doméstico

Decisión vigente desde el 23 de octubre de 2026: **no instalar ni ejecutar Docker en el servidor**. Docker se conserva en Windows para desarrollo y pruebas. Este documento sustituye el despliegue con contenedores del plan inicial.

## Entorno comprobado y estado

Servidor Debian 13, dos CPU, 1934 MiB RAM, Python 3.13.5 y PostgreSQL 17.11. PostgreSQL, Nginx, Cloudflared, Tailscale y VecinoMarket ya están activos. No se instala otra instancia de PostgreSQL, no se detienen los servicios ajenos y no se cambian sus puertos ni la configuración global de memoria. Docker no estaba instalado; la sesión anterior que esperaba sudo fue cerrada y el instalador anterior quedó desactivado.

El procesador comprobado es un Pentium Dual-Core T4500 sin SSE4.2. Las ruedas recientes de NumPy provocaron SIGILL; se fija NumPy 2.3.5 y se regeneran los modelos localmente con esa misma versión. No actualizar NumPy a 2.4 o superior con ruedas estándar en este equipo. La carga de artefactos exige coincidencia de NumPy, scikit-learn y joblib con el entrenamiento, además del hash. Referencia: [línea base de CPU de NumPy](https://numpy.org/doc/2.4/reference/simd/build-options.html).

La versión `20261023T135345Z-91cdb032` está activa de forma nativa en `http://127.0.0.1:2468`. El túnel independiente P2 está conectado con cuatro conexiones y arranque automático. El usuario asignará la ruta pública en Cloudflare; al momento de la comprobación el dominio previsto todavía no resolvía y no se declara accesibilidad HTTPS. Stripe del nuevo dominio, SMTP y Firebase requieren su configuración específica.

Verificación registrada en `docs/evidencias/native-deployment-validation.json`: 85 pruebas de backend aprobadas sobre PostgreSQL 17 y 11 pruebas de infraestructura aprobadas. Estas últimas incluyen migración y restauración con dos empresas, ocho productos y 480 unidades de inventario, conservando FORCE RLS y los roles limitados. Las plantillas se validaron con Nginx y systemd del servidor sin iniciar P2; para comprobar directivas systemd se sustituyó únicamente el ejecutable todavía inexistente por `/usr/bin/true` en una copia temporal.

La base y los roles propios ya están aprovisionados en el servidor, con las 16 migraciones aplicadas y dependencias verificadas en un entorno virtual Python 3.13. Se comprobaron imports, RLS sin contexto, carga de artefactos, predicción de demanda, segmentación y conversión de imagen con la cuenta Linux limitada. El proceso de comprobación completa alcanzó 264612 KiB de RSS máximo (258,4 MiB). Es una comprobación privada; no mide concurrencia HTTP, carga sostenida ni disponibilidad pública. La aplicación P2 ya está activa. La prueba HTTP posterior verificó dos empresas, catálogos aislados, reportes PDF/XLSX, inferencia de cuatro productos y segmentación de doce clientes. Treinta consultas con tres hilos finalizaron sin errores: mediana 0,194 s y máximo 0,282 s. La primera consulta del dashboard demoró 3,509 s. Después de las pruebas, la API registró 202162176 bytes de memoria y el túnel 25837568 bytes, ambos con cero reinicios. Son pruebas breves, no carga sostenida. Evidencia: `docs/evidencias/native-http-validation.json`.

## Componentes y límites iniciales

| Componente | Configuración nativa |
|---|---|
| Base central | `fashionstore_p2` dentro de PostgreSQL 17 existente |
| Propietario de migraciones | `fashionstore_p2_owner`, sin superusuario ni creación de roles/bases |
| Rol API | `fashionstore_p2_app`, no propietario, sin BYPASSRLS ni membresías |
| Proceso API | Usuario Linux `fashionstore-p2`, entorno virtual por versión, systemd `fashionstore-p2-api` |
| Uvicorn | Un proceso en `127.0.0.1:8002`, máximo tres conexiones PostgreSQL |
| Espera de conexión | Hasta cinco segundos por cupo; timeout devuelve 503 con Retry-After, sin abrir conexiones adicionales |
| Presupuesto API | MemoryHigh 384 MiB, MemoryMax 512 MiB, CPUQuota 75%, un hilo numérico |
| Web | Angular compilado localmente, servido por el Nginx existente en `127.0.0.1:2468` |
| HTTPS | Túnel independiente `FashionStore_Parcial2`, servicio `fashionstore-p2-tunnel`, destino HTTP `127.0.0.1:2468` |
| ML | Entrenamiento local; artefactos con versión, hash y carga diferida en producción |

Estos límites afectan solo a P2 y son una hipótesis inicial. Medir memoria al arrancar, consultar reportes, cargar los modelos y procesar imágenes. Si el proceso llega al límite, revisar la carga antes de aumentarlo; no atribuir el problema automáticamente al servidor. No ejecutar entrenamientos, Angular, emuladores ni builds Docker allí.

Se prueba compatibilidad SQL con PostgreSQL 17 en una base efímera local. El ambiente local habitual puede seguir en PostgreSQL 16. El runtime nativo también debe pasar importación y carga de artefactos en Python 3.13; una prueba en Python 3.12 no acredita esa comprobación.

## Estructura del servidor

```text
/home/alecv/Parcial2_FashionStore/
  incoming/                   # paquetes transferidos por SSH
  releases/VERSION/           # fuentes, web compilada, modelos y .venv propio
  current -> releases/VERSION
  previous-release            # destino anterior; no es un respaldo de base
  shared/
    api.env                   # root:fashionstore-p2 0640; solo credenciales limitadas
    admin.env                 # root:root 0600; propietario y semillas
    provision.json            # root:root 0600; alta inicial de base y roles
    cloudflared-p2.token       # root:root 0600; token exclusivo del túnel P2
    firebase.json             # opcional, root:fashionstore-p2 0640
    files/comprobantes/        # privados, descarga por backend con autorización
    files/catalog-images/     # fotografías de prendas, entrega mediante ruta de catálogo
  backups/                    # root:root 0700, datos comerciales sensibles
```

Nginx apunta únicamente a `current/web`; ningún archivo de configuración, comprobante o fuente backend se agrega a esa raíz. No se transfieren `.env`, dependencias Windows, entornos virtuales, repositorios internos, datos del P1 ni documentos de clientes con los paquetes de código.

## Preparación local

1. Completar las pruebas del CU y las reglas afectadas. Construir Angular con `npm ci` y `npm run build` en `Parcial2_frontend-web`. Conservar los resultados de pruebas, incluida la compatibilidad PostgreSQL 17.
2. Con un intérprete Python que tenga `python-dotenv`, ejecutar desde la raíz `python scripts/generate_native_config.py`. Genera `infra/secrets/native` ignorado por Git. Crea contraseñas de base y clave JWT nuevas; solo reutiliza Gemini y Stripe **TEST** autorizados. No copiar el secreto del webhook P1: la URL nueva requiere su propio secreto. No imprimir estos archivos en terminales compartidas.
3. Ejecutar `python scripts/package_native.py`. Produce `tmp/native-releases/VERSION.tar.gz` y su archivo `.sha256`. Rechaza Angular compilado antes de los últimos cambios de fuentes. El paquete contiene exclusivamente fuentes permitidas, SQL versionado, artefactos ML y web compilada; excluye documentos e imágenes de usuarios.
4. Transferir por `scp` a `alecv@192.168.1.100` o `alecv@alecv`, según la red. Crear `incoming`, `releases` y `shared` bajo el directorio P2, con `umask 077` durante la transferencia de secretos. Copiar `api.env`, `admin.env` y `provision.json` directamente a `shared`, sin pasarlos por GitHub. Transferir los scripts `infra/native` para la preparación inicial.

Las versiones siguen `YYYYMMDDTHHMMSSZ-hash8`. Sustituir `VERSION` en los comandos siguientes por el nombre real del paquete; no escribir literalmente el marcador.

## Preparación inicial del host

Ejecutar por SSH `sudo bash ~/Parcial2_FashionStore/infra/native/prepare-host.sh`. La contraseña de sudo se introduce en su solicitud interactiva; no se almacena en scripts, argumentos, archivos de configuración ni historial.

El script comprueba Debian 13 y los comandos nativos ya instalados, crea la cuenta de servicio y los directorios privados, y aprovisiona únicamente la base y los roles de P2. Si falta `python3-venv` u otra dependencia, se detiene indicando cuál falta. Las bibliotecas nativas requeridas por OpenCV son `libgl1`, `libglib2.0-0t64` y `libxcb1` en Debian 13. No instala Docker, no ejecuta `ALTER SYSTEM`, no cambia `pg_hba.conf`, no reinicia PostgreSQL y no activa el sitio P2.

Los roles nuevos no tienen privilegios para alterar otros ámbitos. Si ya existen con privilegios elevados, membresías o bases ajenas, el script se detiene. No rota contraseñas de roles preexistentes. Se requiere que `fashionstore-p2` y `www-data` puedan atravesar `/home/alecv`; si no es así, se detiene para resolver una ACL específica, sin abrir automáticamente el directorio personal.

El directorio personal de este servidor tiene modo 700. Tras crear la cuenta P2, ejecutar una sola vez `sudo bash ~/Parcial2_FashionStore/infra/native/grant-traversal.sh` y repetir `prepare-host.sh`. El ajuste agrega únicamente permiso de paso ACL a `fashionstore-p2` y `www-data`, sin permiso de listado ni acceso recursivo a archivos personales. Si falta la herramienta, instala solamente el paquete nativo `acl`.

## Preparar y activar una versión

En `incoming`, verificar `sha256sum -c VERSION.tar.gz.sha256`. Crear `releases/VERSION`, extraer allí el paquete con `tar --no-same-owner -xzf incoming/VERSION.tar.gz -C releases/VERSION`, y no mezclar dos versiones en el mismo directorio.

Como `alecv`, ejecutar `bash releases/VERSION/infra/native/stage-release.sh VERSION`. Verifica los hashes internos, crea `.venv`, instala únicamente ruedas binarias compatibles con Python 3.13 usando las versiones comprobadas de `requirements-linux-py313.lock`, ejecuta `pip check` y conserva las versiones efectivas de dependencias. No reutiliza el entorno virtual de otra aplicación. Si falta una rueda, falla; no inicia compilaciones pesadas de NumPy/OpenCV en el servidor. Si se cambian requisitos de aplicación, revisar y volver a comprobar ese archivo de restricciones.

Después ejecutar `sudo bash releases/VERSION/infra/native/activate-release.sh VERSION`. La activación:

1. Verifica la versión y detiene exclusivamente P2, si estaba activo.
2. Respalda la base y los archivos de P2 con la API detenida para mantenerlos consistentes.
3. Aplica migraciones con el propietario; el rol de aplicación ya fue creado por el administrador PostgreSQL.
4. Comprueba imports, artefactos ML y denegación RLS sin contexto con las credenciales limitadas.
5. Cambia `current`, instala la unidad propia y arranca la API. Comprueba `/health`.
6. Valida el sitio Nginx por separado, lo agrega sin reemplazar VecinoMarket, ejecuta `nginx -t` y recarga Nginx. Comprueba `127.0.0.1:2468/health`.

Un bloqueo de archivo impide dos activaciones simultáneas. Si falla después de cambiar el sitio Nginx, se recupera exclusivamente la configuración P2 anterior; nunca se reemplazan archivos de VecinoMarket.

La comprobación HTTP tras recargar Nginx reintenta conexiones rechazadas durante un máximo de veinte segundos, porque la recarga termina antes de que los nuevos workers abran el listener. Un fallo definitivo conserva el comportamiento de recuperación. El pool de PostgreSQL admite espera acotada para los solapamientos entre peticiones y la liberación de sus dependencias; mantiene tres conexiones máximas.

Las semillas nuevas de demostración son una acción separada y explícita, ejecutada con el Python de la versión y `env_run.py shared/admin.env`. No se ejecutan automáticamente en cada actualización ni se importa la base P1 sobre producción. `scripts/migrate.py` conserva sus comprobaciones de checksum y acepta `APP_DB_USER` para distinguir el rol nativo del rol usado localmente.

## HTTPS, integraciones y aceptación

El usuario creó el túnel remoto `FashionStore_Parcial2` y autorizó su token el 23 de octubre. Su conector se instala con `sudo bash releases/VERSION/infra/native/install-tunnel.sh RUTA_TOKEN_PRIVADO`. Se reutiliza el ejecutable `cloudflared` 2026.10.0 ya instalado; no hace falta cambiar repositorios APT ni reinstalarlo. **No ejecutar `cloudflared service install TOKEN`**, porque el servicio global pertenece a VecinoMarket.

La unidad propia `fashionstore-p2-tunnel` usa `DynamicUser` y `LoadCredential`: el token se conserva en `shared/cloudflared-p2.token` con permisos root 0600 y no aparece en argumentos, variables del proceso ni archivos versionados. La unidad limita memoria a 192 MiB y CPU al 25%; las métricas y `/ready` escuchan únicamente en `127.0.0.1:20245`. El instalador verifica el identificador del túnel antes de activar exclusivamente este servicio.

En Cloudflare, agregar al túnel P2 la ruta pública `fashionstore-v2.aledevcv.me`, tipo **HTTP**, URL **`127.0.0.1:2468`**. El conector corre en el mismo servidor Debian `192.168.1.100`, por lo que se usa su loopback. No necesita abrir puertos en el router ni usar HTTPS entre el conector y Nginx. No exponer PostgreSQL ni la API 8002. El estado conectado del túnel acredita el conector; la accesibilidad HTTPS requiere además esta ruta, DNS y la comprobación externa.

Consulta sin secretos: `systemctl is-active fashionstore-p2-tunnel` y `curl --fail http://127.0.0.1:20245/ready`. Para reiniciar exclusivamente P2: `sudo systemctl restart fashionstore-p2-tunnel`. El servicio global `cloudflared` permanece intacto. La copia temporal del token en `incoming` se elimina después de instalarla; la copia privada local está ignorada por Git.

Configurar el webhook Stripe TEST sobre la nueva URL y guardar su secreto propio en `shared/api.env`. Configurar SMTP para recuperación real de contraseña; Mailpit es solo local. Firebase sigue el procedimiento específico de `docs/FIREBASE.md`. Una bandeja interna operativa no demuestra recepción de push real.

Comprobar desde otra red HTTPS, PWA instalable, inicio por empresa, permisos, aislamiento, pagos sandbox, comprobantes y acceso móvil. Ejecutar los escenarios offline, reintentos y conflictos del plan. Registrar también el estado de VecinoMarket y consumo con `systemctl show fashionstore-p2-api -p MemoryCurrent -p MemoryPeak -p CPUUsageNSec`, `systemctl status fashionstore-p2-api` y `free -m`. No publicar el contenido de los archivos privados en las evidencias.

## Respaldo y recuperación

La activación genera un dump PostgreSQL en formato custom y un archivo de `shared/files`, ambos privados. El dump contiene datos comerciales sensibles y hashes de usuarios; no se agrega a Git. Conservar fuera del servidor una copia protegida de los respaldos y de la configuración privada por separado.

El respaldo se ejecuta como root y usa `runuser -u postgres` por el socket local, exclusivamente para `fashionstore_p2`. Esto permite copiar también tablas con FORCE RLS sin desactivar políticas ni conceder BYPASSRLS al propietario o a la API. El manifiesto guarda hashes SHA-256 del dump y del archivo de documentos; el ensayo de restauración los verifica antes de crear una copia.

Para un respaldo manual, detener solo `fashionstore-p2-api`, ejecutar como root el Python de `current/.venv` con `current/infra/native/env_run.py shared/admin.env` y el programa `current/infra/native/backup.py`, y volver a iniciar P2 después de verificar el resultado. No detener PostgreSQL ni otras aplicaciones.

Ensayar `sudo bash current/infra/native/restore-copy.sh RUTA_RESPALDO fashionstore_p2_restore_YYYYMMDDHHMMSS`. Solo crea una base con ese prefijo; falla si ya existe. Usa `pg_restore --exit-on-error --single-transaction`, comprueba cantidades y verifica el archivo comprimido de documentos. No ejecuta DROP, no reemplaza la base productiva ni modifica sus archivos. Comparar además importes, relaciones, inventario y documentos de la copia contra el manifiesto del respaldo antes de declarar recuperabilidad completa.

Revertir `current` solo revierte código. Si la activación falló antes de migrar, el script intenta reiniciar la versión anterior que estaba activa. Si las migraciones ya finalizaron, conserva el respaldo y deja P2 detenido ante un fallo: comprobar compatibilidad del código anterior o ensayar recuperación antes de iniciarlo. La restauración destructiva sobre producción requiere un procedimiento concreto adicional; no se realiza automáticamente.

## Referencias técnicas

- [systemd: entorno y permisos del proceso](https://www.freedesktop.org/software/systemd/man/latest/systemd.exec.html).
- [systemd: límites de recursos por servicio](https://www.freedesktop.org/software/systemd/man/latest/systemd.resource-control.html).
- [Nginx: proxy HTTP](https://nginx.org/en/docs/http/ngx_http_proxy_module.html).
- [PostgreSQL 17: pg_dump](https://www.postgresql.org/docs/17/app-pgdump.html) y [pg_restore](https://www.postgresql.org/docs/17/app-pgrestore.html).

Ensayo de recuperación nativo del 23 de octubre: el respaldo `20261023T135809111057Z` se restauró en la base nueva `fashionstore_p2_restore_20261023140000`, conservando 16 migraciones, 480 ventas, ocho productos demo, 480 unidades y FORCE RLS. La base productiva y sus archivos no se reemplazaron.
