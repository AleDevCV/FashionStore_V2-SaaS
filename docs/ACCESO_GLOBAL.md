# Acceso global por correo — 25 de octubre de 2026

Implementación solicitada para CU-01 y comportamiento relacionado de CU-02, administración de usuarios, clientes y navegación comercial. Las ampliaciones de VecinoMarket quedan fuera de este cambio.

## Comportamiento

- Angular y Flutter solicitan correo y contraseña. El formulario no pide empresa.
- Los correos son únicos globalmente, normalizados sin distinguir mayúsculas. El nombre o prefijo del correo no otorga permisos.
- El servidor determina el tipo de cuenta. Plataforma administra SaaS; el administrador y sus empleados permanecen vinculados a su empresa y sucursales autorizadas.
- El cliente inicia una sesión global y elige tienda después de autenticarse. Una elección válida produce un nuevo token firmado con el contexto comercial de esa tienda. No se utiliza un encabezado modificable para cambiar el tenant de una sesión.
- El cliente puede consultar su historial propio entre tiendas. Los administradores empresariales siguen limitados a sus datos comerciales y no pueden cambiar la contraseña global del cliente ni promoverlo a personal.
- Registro, recuperación y revocación utilizan la identidad global. Un cambio de contraseña revoca las sesiones de todas las tiendas. Suspender el perfil comercial en una tienda no bloquea al cliente en las demás.
- Se conservan los IDs anteriores, la separación de carritos y las colas IndexedDB/SQLite. La migración invalida sesiones previas; se requiere volver a entrar para sincronizar pendientes conservados.

## Cuentas preparadas

| Tipo | Correo | Ámbito |
|---|---|---|
| Superadministrador | admin@fashionstore.com | Plataforma SaaS |
| Administrador | atelierandino@fashionstore.com | Atelier Andino |
| Administrador | casatextil@fashionstore.com | Casa Textil |
| Cajero | cajero-atelierandino-01@fashionstore.com | Atelier Andino |
| Encargado | encargado-atelierandino-01@fashionstore.com | Atelier Andino |
| Cajero | cajero-casatextil-01@fashionstore.com | Casa Textil |
| Encargado | encargado-casatextil-01@fashionstore.com | Casa Textil |
| Clientes | cliente1@fashionstore.com, cliente2@fashionstore.com, cliente3@fashionstore.com | Todas las tiendas, solo datos propios |

Las claves autorizadas se encuentran en `infra/secrets/native/acceso-demo.txt`, excluido por `.gitignore`. PostgreSQL conserva hashes. Estos identificadores no crean buzones; la entrega de recuperación requiere un correo real y SMTP configurado.

## Datos y migración

`017_global_identity.sql` incorpora `cuenta_global`, recuperación y auditoría de identidad, enlazando `usuario.account_id` sin sustituir claves comerciales. Las colisiones heredadas se conservan como cuentas diferentes mediante renombrado explícito. Solo los perfiles conocidos Cliente Demo de demo-a/demo-b se vinculan a cliente1 mediante la semilla de demostración autorizada.

La API usa un rol PostgreSQL sin propiedad, membresías privilegiadas ni BYPASSRLS. El directorio de identidad tiene RLS sin políticas de lectura directa. Las funciones necesarias tienen `SECURITY DEFINER`, ruta de búsqueda fija, ejecución pública revocada y permisos concedidos por firma individual al rol de aplicación. El contexto se fija localmente en cada transacción.

El ensayo nativo restauró un respaldo real de P2 en `fashionstore_p2_restore_20261025051554`. Conservó 480 ventas, Bs 187.320 acumulados, ocho productos, 480 unidades, IDs de clientes y usuarios anteriores. El ensayo añadió las cuentas nuevas y ejecutó las comprobaciones HTTP con el rol limitado. No reemplazó la base productiva.

## Verificación

| Comprobación | Resultado | Evidencia |
|---|---|---|
| Regresión backend PostgreSQL 17 | 96 aprobadas | evidencias/backend-tests-global-identity.xml |
| Infraestructura y migración con propietario limitado | 11 aprobadas | evidencias/global-identity-final-tests.xml, que incluye además 11 pruebas de identidad |
| Angular: acceso, rutas por rol, recuperación y carritos separados | 30 aprobadas | evidencias/global-identity-summary.json; ejecutar `npm run test:auth` |
| Flutter: autenticación y persistencia SQLite | 11 aprobadas | evidencias/global-identity-summary.json |
| Flutter analyze | Sin problemas | evidencias/global-identity-summary.json |
| Angular producción y APK release | Compilaciones correctas | Hash y tamaño APK en evidencias/global-identity-summary.json |
| HTTP local y servidor | Diez cuentas, permisos, cambio de tienda, catálogos, exportaciones, ML y 30 lecturas con concurrencia 3 | evidencias/global-login-local-http.json y global-identity-production-http.json |
| Migración nativa sobre copia | Datos e IDs conservados | evidencias/global-identity-native-migration.json y global-identity-native-rehearsal.json |

Las pruebas incluyen correo único, encabezado de empresa falsificado, permisos reales, cierre y recuperación global, bloqueo local de cliente, imposibilidad de promoción por un administrador empresarial e historial propio entre dos tiendas después de registrar ventas reales en la base efímera.

La suite Angular general tiene pruebas heredadas del vestidor que no compilan contra su implementación actual. La suite específica de autenticación usa `tsconfig.auth.spec.json`; no elimina ni silencia esas pruebas pendientes. Quedan la aceptación en Android físico y la entrega real de recuperación mediante SMTP productivo. Estas verificaciones no cierran los 38 CU ni constituyen carga sostenida.

## Producción

Versión activa: `20261025T051010Z-f476f223`. URL: https://fashionstore.aledevcv.me. Despliegue nativo por SSH: Python 3.13, PostgreSQL 17, systemd y Nginx en `127.0.0.1:2468`; Docker permanece solo en el ambiente local.

Respaldo anterior a la migración: `20261025T051752100650Z`. Se conservaron la versión previa y una copia privada de la configuración. No se modificaron los servicios de VecinoMarket ni el túnel global existente. Después de activar se comprobaron API, túnel, Nginx, Cloudflared y VecinoMarket activos; API y túnel P2 con cero reinicios. API aproximadamente 191 MiB y túnel 23 MiB durante la comprobación breve.

No ejecutar de nuevo `seed_login_accounts.py` en cada despliegue: es una operación explícita que restablece las claves demo y revoca sesiones. Las siguientes versiones requieren migración normal y respaldo; solo volver a sembrar si se desea renovar las cuentas de presentación.

No se ejecutaron comandos Git. La publicación en GitHub queda manual, independiente del despliegue SSH.
