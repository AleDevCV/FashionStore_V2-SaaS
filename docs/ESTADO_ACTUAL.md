# Estado de implementación

Actualización del 23 de octubre de 2026. El proyecto completo sigue en implementación; no se declaran los 38 CU terminados por disponer de pantallas o código.

## Cambio de producción solicitado

Producción queda **nativa, sin Docker**. Docker sigue habilitado únicamente para desarrollo y pruebas locales. Se actualizaron plan, arquitectura, manual y configuración de Firebase; se prepararon empaquetado, configuración privada separada, entorno virtual por versión, systemd, Nginx, migraciones con rol configurable, respaldo y ensayo de restauración a copia.

En el servidor se cerró la sesión anterior de sudo y se desactivó el instalador de Docker. Docker no está instalado. Nginx, PostgreSQL 17, Cloudflared y VecinoMarket continúan activos. Ya se crearon la base, los roles y la cuenta Linux exclusivos de P2, se aplicaron 16 migraciones y se comprobaron dependencias en Python 3.13. Se agregó una ACL de solo paso para P2 y Nginx sobre el directorio personal, que conserva la restricción de listado. **P2 está activo de forma nativa en `127.0.0.1:2468`**. El servicio independiente `fashionstore-p2-tunnel` conecta el túnel `FashionStore_Parcial2` con cuatro conexiones. El usuario asignará el hostname en Cloudflare; HTTPS público sigue sin verificar.

## Evidencia nueva

- Compilación Angular de producción completada, con Service Worker. Una advertencia CommonJS heredada de `retry` no impide compilar.
- 85 pruebas de backend aprobadas sobre PostgreSQL 17 local, incluyendo autorización, aislamiento, reglas comerciales, sincronización, pagos, cambios, reportes, analítica y rechazo de artefactos con versiones incompatibles. Dos advertencias de deprecación de las bibliotecas de pruebas siguen presentes.
- 11 pruebas de infraestructura aprobadas: separación de secretos, configuración literal, integridad y exclusiones del paquete, rechazo de Angular desactualizado, migración y restauración con propietario limitado, dos empresas, ocho productos y 480 unidades.
- Sintaxis Bash/Python, sitio Nginx y directivas systemd comprobadas en Debian del servidor sin activar la aplicación. El ejecutable de Uvicorn se sustituyó por `/usr/bin/true` solo en la copia temporal usada para verificar directivas.
- Candidato nativo empaquetado y verificado: no incluye comprobantes, imágenes de usuarios, archivos privados, dependencias Windows ni entornos virtuales. No se encontraron valores de las credenciales privadas configuradas dentro del paquete.
- Runtime nativo comprobado con la cuenta limitada: imports de la API, RLS, carga de modelos e inferencia supervisada/no supervisada con datos artificiales y OpenCV. Pico RSS del proceso completo: 264612 KiB (258,4 MiB), sin probar carga HTTP.
- El Pentium T4500 no tiene SSE4.2: se fijó NumPy 2.3.5, se regeneraron modelos localmente y se verifican versiones de NumPy, joblib y scikit-learn al cargarlos. Las métricas de evaluación permanecieron iguales. El archivo de restricciones conserva las dependencias Linux comprobadas.
- El respaldo de tablas con FORCE RLS usa el administrador PostgreSQL local únicamente para copiar P2; el rol de aplicación mantiene sus restricciones. Los respaldos incluyen hashes para verificar su integridad.

Los XML y el JSON de `docs/evidencias` conservan los resultados. El JSON identifica el candidato y su hash. Es un candidato técnico, no la versión final de defensa.

## Despliegue comprobado

Versión activa: `20261023T135345Z-91cdb032`. Se corrigieron una comprobación demasiado temprana tras la recarga Nginx y el rechazo inmediato del pool durante el solapamiento de peticiones. El pool conserva tres conexiones y espera hasta cinco segundos por un cupo. La regresión pasó 85 pruebas; las comprobaciones HTTP nativas aprobaron recursos PWA, dos empresas y doce variantes por empresa, aislamiento, denegación de reportes ajenos, PDF/XLSX, cuatro predicciones, doce segmentos y treinta consultas con concurrencia tres. La API y el túnel no registraron reinicios. Los servicios de VecinoMarket siguen activos y Docker permanece ausente del servidor.

El token P2 queda privado dentro del proyecto, con permisos root 0600, leído mediante LoadCredential. No se reemplazó el servicio global cloudflared. El origen del túnel es HTTP `127.0.0.1:2468`; no necesita puertos del router abiertos. Las cuentas de demostración se consultan en el archivo privado local `infra/secrets/native/acceso-demo.txt`, ignorado por Git.

## Pendientes que permanecen

Completar carga sostenida y aceptación integral; cerrar regresiones e interfaces pendientes; asignar y verificar HTTPS público, configurar webhook Stripe propio y SMTP; disponer de un proyecto Firebase para verificar push real. También siguen la verificación Android en dispositivo, los diagramas técnicos finales y el documento Word/PDF completo. La medición privada de 258,4 MiB no sustituye las pruebas de carga de la aplicación.

La migración ensayada del P1 usa su SQL y datos sintéticos comerciales no vacíos en una copia aislada. La base operativa P1 configurada no fue accesible; no se presenta ese ensayo como una restauración de su respaldo real. No se ejecutaron subidas a GitHub.

Ensayo de recuperación nativo del 23 de octubre: el respaldo `20261023T135809111057Z` se restauró en la base nueva `fashionstore_p2_restore_20261023140000`, conservando 16 migraciones, 480 ventas, ocho productos demo, 480 unidades y FORCE RLS. La base productiva y sus archivos no se reemplazaron.

Actualización comunicada por el usuario el 23 de octubre: hostname definitivo `fashionstore.aledevcv.me`, CNAME a `9a7b9898-27eb-4ae0-bda4-7977eb3159c9.cfargotunnel.com`, publicado en el túnel FashionStore_Parcial2. Sustituye al hostname propuesto fashionstore-v2.aledevcv.me. La configuración del hostname es información aportada por el usuario; queda comprobar HTTPS y actualizar las URLs privadas de origen/retorno al dominio definitivo.
