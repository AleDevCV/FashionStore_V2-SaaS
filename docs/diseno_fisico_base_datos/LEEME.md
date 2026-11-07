# Diseño físico de la base de datos de FashionStore

El archivo `FASHIONSTORE_DISENO_FISICO_COMPLETO.sql` reconstruye la estructura real de PostgreSQL de FashionStore P2, extraída el 1 de noviembre de 2026 desde la base `fashionstore_p2` del servidor. Se ejecuta sobre una **base nueva y vacía**, con un administrador de PostgreSQL. Fue probado con PostgreSQL **17.11**; no se ha validado su ejecución en versiones anteriores.

## Contenido

| Elemento | Cantidad |
|---|---:|
| Tablas | 45 |
| Claves primarias | 45 |
| Claves foráneas | 136 |
| Restricciones totales, incluidas PK y FK | 238 |
| Índices, incluidos los de restricciones | 121 |
| Funciones | 29 |
| Triggers de usuario | 18 |
| Políticas de seguridad por fila | 59 |
| Tablas con RLS habilitada | 41 |
| Vistas | 1 |
| Secuencias | 30 |

Incluye tipos de columnas, valores predeterminados, nulabilidad, relaciones, índices, funciones, triggers, propietarios, permisos y políticas RLS. Conserva la bitácora y las estructuras de identidad global, empresas, suscripciones, comercio, pagos, cambios, sincronización, reportes y notificaciones.

No contiene registros comerciales, usuarios, contraseñas, tokens ni datos de demostración. Los cuerpos de funciones contienen las instrucciones necesarias para su funcionamiento; estas no se ejecutan al crear las funciones.

## Ejecutar en pgAdmin

1. Utilizar PostgreSQL 17 con la extensión `uuid-ossp` disponible. Iniciar sesión con un administrador, por ejemplo `postgres`.
2. Abrir Query Tool sobre la base administrativa `postgres` y ejecutar `00_ROLES_SIN_CREDENCIALES.sql`.
3. Ejecutar `01_CREAR_BASE_VACIA.sql` una sola vez, fuera de una transacción explícita. Crea la base `fashionstore_diseno_fisico`; se puede cambiar ese nombre antes de ejecutarlo.
4. Abrir una nueva conexión de Query Tool sobre la base recién creada.
5. Abrir y ejecutar **todo** `FASHIONSTORE_DISENO_FISICO_COMPLETO.sql`. Incluye `BEGIN` y `COMMIT` para aplicar la estructura como una sola transacción.
6. Actualizar el explorador de objetos de pgAdmin para consultar las tablas, relaciones, índices y demás objetos.

El SQL principal también incluye la creación condicional de los roles, por lo que basta ese archivo si ya se dispone de una base vacía correctamente preparada. Los archivos auxiliares facilitan la preparación completa desde pgAdmin.

## Ejecutar con psql

Desde esta carpeta, usando una cuenta administrativa de PostgreSQL y su autenticación habitual:

```powershell
psql -h localhost -U postgres -d postgres -X -v ON_ERROR_STOP=1 -f "00_ROLES_SIN_CREDENCIALES.sql"
psql -h localhost -U postgres -d postgres -X -v ON_ERROR_STOP=1 -f "01_CREAR_BASE_VACIA.sql"
psql -h localhost -U postgres -d fashionstore_diseno_fisico -X -v ON_ERROR_STOP=1 -f "FASHIONSTORE_DISENO_FISICO_COMPLETO.sql"
```

Las contraseñas no se incluyen en los archivos ni en los comandos. Si los roles `fashionstore_p2_owner` y `fashionstore_p2_app` no existen, se crean sin capacidad de iniciar sesión (`NOLOGIN`). Sus credenciales y autenticación para un despliegue se configuran por separado; los roles existentes no se modifican.

Este archivo sirve para construir y estudiar el diseño físico. No es una migración incremental para la base en uso. Tampoco inicializa cuentas, empresas, planes ni existencias. La tabla `schema_migrations` se crea vacía, como las demás: antes de utilizar esta reconstrucción como base de una aplicación debe prepararse su inicialización y el registro de migraciones correspondiente. No se deben volver a ejecutar indiscriminadamente las migraciones 001–017 sobre ella, puesto que su estructura ya está incorporada.

## Verificación realizada

- Se ejecutó el archivo SQL principal exacto en una base temporal y vacía del servidor.
- Se compararon esquemas, relaciones, columnas, restricciones, índices, funciones, triggers, políticas RLS, vistas, secuencias, enumeraciones y extensiones con el origen.
- Nueve restricciones `CHECK` cambiaron su representación textual al restaurarse: PostgreSQL trasladó una conversión del arreglo a sus elementos. Se verificaron sus definiciones utilizando nuevamente el analizador de PostgreSQL en tablas temporales de la base de prueba. El detalle queda en `CHECKS_REINTERPRETADOS.json`.
- La base de prueba se eliminó al terminar. No se modificaron registros de producción ni se solicitaron reinicios de servicios.
- Las 17 migraciones locales coinciden por SHA-256 con las de la versión desplegada; véase `MIGRACIONES_LOCAL_SERVIDOR.json`.
- API, Nginx, PostgreSQL y túnel de FashionStore continuaron activos. La API local, el proxy, el inicio de sesión, el manifiesto del Service Worker y la disponibilidad del túnel devolvieron HTTP 200.
- También se verificaron por HTTPS público `/health`, `/login` y `/ngsw.json`. Son comprobaciones de disponibilidad; no sustituyen las pruebas funcionales de cada caso de uso.

## Archivos de apoyo

- `VALIDACION_DISENO_FISICO.json`: resultado de restauración, cantidades, SHA-256 y estado de servicios antes y después.
- `INVENTARIO_ORIGEN.json` y `INVENTARIO_RESTAURADO.json`: inventarios estructurales comparados.
- `DIFERENCIAS.json`: diferencias estructurales sin resolver; el resultado validado está vacío.
- `CHECKS_REINTERPRETADOS.json`: equivalencias de restricciones comprobadas por PostgreSQL.
- `DICCIONARIO_COLUMNAS.csv`: columnas de las tablas con tipos, nulabilidad, valores predeterminados e identidad.
- `RESTRICCIONES.csv`: claves y demás restricciones de las tablas.
- `VERIFICACION_HTTPS.json`: disponibilidad pública comprobada desde la laptop de trabajo.

El exportador reproducible se conserva en `infra/native/export_physical_design.py`. La exportación utiliza `pg_dump --schema-only`; referencia: [documentación oficial de PostgreSQL 17](https://www.postgresql.org/docs/17/app-pgdump.html).
