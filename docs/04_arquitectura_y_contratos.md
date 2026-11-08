# Arquitectura y contratos de evolución

## Organización

FastAPI mantiene routers, esquemas y servicios SQL. El contexto de empresa se resuelve por petición y se aplica con set_config local en cada transacción del pool. RLS aplica al rol de ejecución no propietario. El propietario se utiliza exclusivamente para migraciones y semillas controladas.

Angular conserva componentes standalone y administración SaaS. Angular y Flutter autentican únicamente por correo y contraseña. El personal recibe un token vinculado a su empresa; el cliente recibe una sesión global y selecciona tienda después del acceso mediante un nuevo token firmado. El identificador público se usa para navegar catálogos, sin conceder permisos. Los datos de una sucursal siempre pertenecen a una empresa. Detalles y evidencias en `ACCESO_GLOBAL.md`.

## Ejecución local y producción nativa

Docker Compose ejecuta únicamente el ambiente local y la base efímera de pruebas. En el servidor Debian 13 se aprovecha PostgreSQL 17 instalado, con base y roles exclusivos de P2. Cada versión usa un entorno virtual de Python 3.13; systemd supervisa un solo proceso Uvicorn en 127.0.0.1:8002 y Nginx sirve Angular compilado y el proxy en 127.0.0.1:2468. El túnel independiente FashionStore_Parcial2 se ejecuta con el servicio fashionstore-p2-tunnel. La ruta HTTPS se administra en Cloudflare y se verifica por separado, preservando VecinoMarket.

Los comprobantes e imágenes quedan en `shared/files`, fuera del código y del directorio web. Los secretos de API y del propietario se separan en archivos privados; el proceso de aplicación recibe solamente las credenciales limitadas. No hay compilación Angular ni entrenamiento ML en el servidor. El manual vigente es `docs/DESPLIEGUE_NATIVO.md`.

## Entidades de plataforma

- Empresa: identificador interno, slug público, nombre, estado y condición de plataforma.
- Plan: nombre, máximo de sucursales activas y acceso a reportes generativos.
- Suscripción: empresa, plan, inicio y vencimiento con zona horaria.
- Cuenta global: correo único, identidad, hash y versión de sesión. El cliente opera en varias tiendas con la misma cuenta.
- Usuario y rol: perfil operativo perteneciente a una empresa, vinculado a la cuenta global y con sus IDs comerciales conservados.
- Usuario sucursal: relación explícita que restringe operaciones y supervisión de sincronización por sucursal.

## Contratos iniciales implementados

| Método y ruta | Autorización | Resultado |
|---|---|---|
| POST /api/login/ | Correo y contraseña | JWT global del cliente o vinculado a la empresa del personal |
| GET /api/tiendas | Público | Tiendas comerciales activas |
| POST /api/auth/seleccionar-tienda | Cliente global vigente | Nuevo token firmado para operar en la tienda elegida |
| GET /api/cuenta/compras | Cliente global vigente | Historial propio entre tiendas |
| POST /api/logout | Sesión vigente | Revoca sesiones del usuario conservando datos locales |
| GET /api/contexto | Sesión vigente | Empresa, usuario, suscripción y sucursales |
| GET o POST /api/empresas | Administrador de plataforma | Consulta o aprovisionamiento atómico |
| PATCH /api/empresas/{id}?activa= | Administrador de plataforma | Estado de empresa |
| GET /api/planes | Sesión vigente | Características configuradas |
| PATCH /api/planes/{id} | Administrador de plataforma | Límites y acceso IA |
| GET /api/suscripciones/{tenant} | Administrador de plataforma o de esa empresa | Suscripción autorizada |
| PUT /api/suscripciones/{tenant} | Administrador de plataforma | Renovación o cambio validado |

## Contratos pendientes

Los contratos backend de sincronización de la tabla siguiente están implementados y verificados para A2. Los demás contratos de cambios, reportes ampliados y analítica se consultan en sus fichas y evidencias; esta revisión no certifica esos módulos. Los diagramas técnicos finales se elaborarán después de estabilizar los componentes correspondientes.

## Fechas y cantidades

El backend utiliza UTC en los contratos de vigencia. La interfaz presenta fechas locales. Los importes comerciales se representan con Decimal y columnas NUMERIC; los UUID offline se generan una sola vez por operación. Los límites y las políticas no se toman de datos enviados por el cliente sin validación.

## Contratos de sincronización verificados para A2

| Método y ruta real | Autorización adicional al aislamiento de empresa |
|---|---|
| GET /api/offline/catalogo | Descarga con sucursal autorizada; resultados conocidos solo del autor. Sin cambios en A2. |
| GET /api/conflictos | `conflictos.resolver`; autor, sucursal asignada o Administrador. Filtro SQL anterior a LIMIT 100. |
| GET /api/sincronizacion/operaciones/{operation_id} | Autor; o supervisor con permiso y sucursal asignada; o Administrador de esa empresa. |
| POST /api/sincronizacion/lote | Recuperar un UUID existente aplica el mismo control; una revisión comprueba acceso al original antes de mostrar su estado. Las nuevas operaciones conservan sus validaciones comerciales. |
| POST /api/conflictos/{operation_id}/compensar | Permiso, acceso al registro y sucursal activa autorizada si existe; control previo a estado e importes. |

Las rutas se declaran en `app/routers/offline.py`, incluido con prefijo `/api` en `app/main.py`. No se cambiaron firmas, DTO ni OpenAPI (118 rutas, 126 esquemas). Política aprobada para ausencia de sucursal e inactividad: [CORRECCION_AUTORIZACION_A2.md](CORRECCION_AUTORIZACION_A2.md). El control común es una función de módulo de `synchronization.py`, no una clase UML ni un nuevo servicio desplegable.

## Contrato A3 — preparado y verificado, sin activación persistente

Se conservan POST `/api/movimientos-inventario[/]` y `/api/inventario/movimientos[/]`. Para Entrada/Salida el payload y la respuesta de movimiento se mantienen. Para Traspaso, `id_sucursal` es origen y se requieren además `id_sucursal_destino` y `operation_id` UUID. Un Traspaso incompleto se rechaza con 422, sin registro ni stock ficticio.

La respuesta `TraspasoRespuesta` contiene la operación lógica y `movimiento_salida` / `movimiento_entrada`, cada uno un `MovimientoRespuesta` real con su tipo físico y stock al confirmar. El resultado se conserva en JSONB para reintentos idénticos. El historial mantiene las patas Salida/Entrada y añade metadatos `MovimientoVinculadoRespuesta` solo si el vínculo es visible en ambas sucursales; el filtro Traspaso incluye estas patas y conserva los eventos históricos.

GET stock admite `disponible=true` para restar retenciones vigentes; por defecto sigue devolviendo stock físico con el mismo esquema. OpenAPI: 118 rutas antes/después, 126 → 128 esquemas; solo cambian los contratos de movimientos/stock y `MovimientoCrear`, con dos respuestas nuevas. Las demás rutas/esquemas permanecen iguales.

La dependencia de escritura usa `get_db(scope='function')`: confirma antes de emitir HTTP 201. `usuario_movimiento` reutiliza `get_current_user` y la fábrica de roles C1 con el mismo cursor, sin duplicar slots del pool. No se cambia `database.py`, el trigger de stock ni las reglas offline. Requiere 018 antes de ejecutar esta versión contra una base. [Detalle](CORRECCION_AUTORIZACION_A3.md).
