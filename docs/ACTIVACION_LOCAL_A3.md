# Activación local y verificación A3 — FashionStore V2 SaaS

Verificado: 2026-11-07T16:25:33.637868+00:00. **A3 está activado únicamente en Docker Desktop local y verificado.** No se modificó producción ni se avanzó con A4/A5/A6. El APK continúa pendiente; no se cambió Flutter durante esta activación.

## 1. Estado antes y después

Contexto `desktop-linux`, host `docker-desktop`, proyecto `fashionstore_examen_si2`, configuración `compose.yaml` + `compose.local.yaml` + `compose.examen.yaml` en `C:\Examen si2 FASHIONSTORE`. Puertos publicados exclusivamente en 127.0.0.1: API 8002, Angular 8082, PostgreSQL 55433 y Mailpit 8025. No se usó SSH ni se contactó producción.

| Servicio | Antes: contenedor / imagen abreviados | Después: contenedor / imagen abreviados | Estado final |
|---|---|---|---|
| api | 6b78e92af812 / `0c594ae3e8cc` | 8d607b7b4caf / `cf76bebff7a4` | saludable |
| web | 90e60965a082 / `e5e1894c2db7` | f0635973fa32 / `00e5826ce995` | saludable |
| db | 931d39a15608 / `cf78e76683b9` | 931d39a15608 / `cf78e76683b9` | saludable |
| mailpit | b62b88893ed3 / `9b3a463be153` | b62b88893ed3 / `9b3a463be153` | saludable |

API activa: `sha256:cf76bebff7a472c34b83872845380d3c933fc36d8793259775e244280e81eea0`. Web activa: `sha256:00e5826ce995aa25c9cfc6eb7fb1c302cfc7ffe62d52931ea2d10b2235de3c0f`.

Solo `api` y `web` se reconstruyeron y recrearon. PostgreSQL y Mailpit conservan ID, imagen, hora de arranque y montajes; los cuatro servicios están saludables. Los volúmenes `fashionstore_examen_si2_p2_database`, `fashionstore_examen_si2_p2_documents` y `fashionstore_examen_si2_p2_catalog_images` conservan sus montajes. No hubo `down`, limpieza, reinicialización ni eliminación de volúmenes.

## 2. Migración 018

Antes existían 17 versiones registradas y no existía `traspaso_inventario`. Se revisó íntegramente 018, se comprobaron sus dependencias contra el catálogo real y se ensayó sobre una copia restaurada. Se ejecutó **exclusivamente 018** con `scripts/migrate.py` sin modificarlo, en su transacción y bajo su advisory lock. Opciones de conexión: `lock_timeout=5000`, `statement_timeout=60000`, `idle_in_transaction_session_timeout=60000` (milisegundos).

Resultado comprobado contra el catálogo de la copia ensayada: tabla `traspaso_inventario`, 12 columnas, 4 índices nuevos en total, 14 restricciones, 2 funciones, 3 triggers y 2 políticas RLS. La tabla anterior de movimientos conserva columnas y restricciones históricas y recibe el índice de apoyo y la guarda de transferencias. Los índices nuevos están válidos y las restricciones validadas. El rol de aplicación recibe los permisos existentes del runner sin convertirse en propietario.

Checksum de 018: `de2b8c77e8cc05319f35328667e78dc8ac302f0788dff441d04c4492d9c041e3`. Las 17 versiones históricas conservan checksum y registro completo, incluido `applied_at`. No se modificaron SQL históricos, tablas o saldos existentes, ni se reejecutaron traspasos antiguos. La tabla nueva contiene **0 filas**.

## 3. Respaldo y recuperación comprobada

Se realizó `pg_dump -Fc` antes de migrar: **270268 bytes**, SHA-256 `70847143af6ba88c005ff17e6fe34b21196e3c73cab1807e742f40b432bd6b45`. Archivo privado: `C:\Users\Klara\Documents\Codex\2026-11-06\https-github-com-aledevcv-fashionstore-v2\work\activation-a3\private\fashionstore_before_018.dump`. Se restringió su ACL al usuario local; el respaldo no se incluye en entregables públicos porque contiene los datos de la demostración.

El archivo pasó `pg_restore --list` y se restauró con `--exit-on-error --single-transaction --no-owner` en un PostgreSQL 16 de la misma imagen que la demostración, con almacenamiento tmpfs, sin red ni puertos. Coincidieron las 45 tablas, 488 filas, historial y estructura. Nueve CHECK se representan tras restaurar con casts por elemento en vez de cast del array completo; se verificó equivalencia estructural y resultado SQL para 23 muestras por CHECK, incluidos NULL e inválidos. No quedó diferencia inesperada.

Se ensayó un bloqueo exclusivo de movimientos en esa copia: el runner agotó 3 segundos, falló y revirtió **DDL, historial y datos**. Tras liberar el bloqueo, el mismo runner aplicó 018 correctamente. La ejecución local persistente posterior aplicó 018 sin fallos. Procedimiento preparado antes de migrar: `work/activation-a3/RECUPERACION.md`; ante error, detener activación, comprobar rollback y permanecer en imágenes anteriores. Nunca restaurar encima de la base persistente sin un plan y aprobación específicos.

Se conservaron etiquetas `fashionstore_examen_si2-api:antes-a3-20261107` y `fashionstore_examen_si2-web:antes-a3-20261107` y un override `rollback-images.json`. Una reversión de aplicación debe conservar 018 y sus futuros datos; no borrar vínculos ni recalcular saldos automáticamente. El servidor anterior mantiene Entrada/Salida y la guarda nueva rechaza Traspaso bruto.

## 4. Servicios activados

Después de validar 018: `docker compose -p fashionstore_examen_si2 -f compose.yaml -f compose.local.yaml -f compose.examen.yaml build api web`, seguido de `up -d --no-deps --no-build --pull never --wait --wait-timeout 180 api web`. Los logs completos se conservaron. No se reiniciaron db/mailpit ni se modificaron Dockerfiles o configuración de Compose.

## 5. Pruebas reales de esta activación

| Alcance | Resultado |
|---|---:|
| A3 sobre HTTP real y PostgreSQL 16 efímero | 38 aprobadas |
| C1/A1 sobre HTTP real y PostgreSQL 16 efímero | 131 aprobadas |
| A2 sobre HTTP real y PostgreSQL 16 efímero | 27 aprobadas |
| Total HTTP aislado, imágenes exactas de API **y web** activadas | **196 aprobadas, 0 fallos, 0 omitidas** |
| Demostración persistente: lecturas/solicitudes deliberadamente inválidas C1/A1 | 88/88 |
| Demostración persistente: lecturas/UUID inexistente A2 | 15/15 |
| Demostración persistente: consultas A3/historial/stock | 25/25 |
| Salud, docs, página y proxy | 5 respuestas HTTP 200 |
| Chrome headless, perfil nuevo, Angular `/tiendas` | Renderizó datos de ambas empresas recibidos de FastAPI |
| Archivos JavaScript servidos frente a manifiesto PWA | 65 hashes coinciden; contrato A3 presente |

Las 196 pruebas usaron HTTP real a Nginx y Uvicorn; ambas imágenes tienen exactamente los IDs activos, sin montar código fuente sobre ellas. Base `fashionstore_p2_test`, red independiente, tmpfs y sin puertos ni volúmenes persistentes. El cliente de pruebas usó fuentes locales solo para fixtures y generación de tokens de prueba; no se simularon permisos ni el servidor. Se registraron 365 solicitudes con códigos 200/201/400/401/403/404/409/422 según cada escenario.

Se verificó transferencia de cantidad 2: origen **5 → 3**, destino **2 → 4**, suma **7 → 7**, una Salida y una Entrada y un solo vínculo. Se verificaron autorizaciones en ambas sucursales, denegaciones de empresa/rol/asignación, cantidades/destinos inválidos y los cuatro alias. Reintentos idénticos conservaron IDs y respuesta, contenido distinto devolvió 409 y concurrencia no duplicó patas ni permitió sobreconsumo.

Stock insuficiente y retenciones activas devolvieron 409 sin escrituras parciales. Retenciones vencidas no bloquearon stock libre. Un error SQL real provocado exclusivamente en el crédito efímero revirtió débito, crédito, vínculo y auditoría; se verificaron snapshots completos. Se probaron competencia con ventas/reservas, cobro legítimo de reserva y compatibilidad de Entrada/Salida.

Las 298 pruebas backend completas y las 44 específicas (incluida instrumentación de commit/pool y fallos internos que no pueden inyectarse desde un cliente remoto) corresponden a la fase de implementación anterior. **No se presentan como reejecutadas ahora**; la imagen activa coincide por hash con aquellos fuentes. La evidencia nueva de activación son las 196 pruebas HTTP anteriores y las comprobaciones persistentes de solo lectura/errores controlados.

## 6. Integridad y contrato

Se compararon todas las tablas públicas, no solo las comerciales. Antes: **45 tablas y 488 filas**. Después: **46 tablas y 489 filas**; la única fila adicional es el registro de 018 en `schema_migrations`, y la tabla de traspasos nueva está vacía. Las filas de las 44 tablas anteriores ajenas al historial conservan cantidad y huella de contenido; los 17 registros históricos también conservan su huella. Las 26 tablas comerciales y sus 230 filas siguen intactas.

Las secuencias coinciden con la copia restaurada anterior a 018. Los archivos de comprobantes e imágenes mantienen cantidad y SHA-256 agregado. Los montajes y el volumen PostgreSQL son los mismos; no se introdujeron datos ficticios en la demostración.

Se verificaron hashes de los módulos activos A3 y C1/A1/A2. OpenAPI vivo coincide exactamente con el contrato A3 previamente probado: **118 rutas y 128 esquemas**. Se conservan todas las rutas; respecto a la versión anterior cambian únicamente movimientos y stock según la ampliación aprobada.

## 7. Documentación y evidencias

Se añade este registro de activación y una nota de estado en trazabilidad/CU10 y el informe A3, conservando evidencias anteriores. Se adjuntan resumen JSON, JUnit HTTP, logs de ejecución, comprobaciones de respaldo/recuperación, integridad y comparación OpenAPI. No se modifican reglas adicionales ni diagramas que ya describen esta implementación.

## 8. Estado final y pendientes

**A3 activado y verificado en Docker local.** API y Angular operativos; inventario persistente anterior intacto. No se ejecutó ningún traspaso comercial de prueba en la demostración. Las instancias efímeras quedan aisladas, sin puertos publicados, y la copia de recuperación conserva red `none`.

APK Flutter **pendiente** por el fallo preexistente documentado en `flutter_inappwebview_android`/Gradle; no se modificó Flutter, plugins ni toolchain durante esta activación. No se declara aceptación en dispositivo físico ni prueba manual completa del formulario autenticado. Los perfiles PWA existentes pueden requerir su actualización/recarga normal. El UUID del formulario online se conserva durante reintentos del formulario abierto; ante cierre con respuesta incierta se debe revisar el historial.

No hay cambios de producción, secretos, operaciones offline o pendientes, migraciones históricas ni trabajo sobre A4/A5/A6. Se detiene el trabajo al finalizar A3.
