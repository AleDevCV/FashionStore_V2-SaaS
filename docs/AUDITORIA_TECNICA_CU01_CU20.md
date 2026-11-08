# Auditoría técnica de FashionStore SaaS

Fecha de revisión: 8 de noviembre de 2026. Base Git: `7621aff`, rama `main`. La inspección incluye los cambios locales de recuperación de CU01. La referencia de requisitos son las 20 fichas de la sección «Especificación de casos de uso» del [documento de examen](DOCUMENTACION%20PARCIAL%202/SEGUNDO_EXAMEN_PARCIAL-FASHIONSTORE.docx).

Los 20 casos tienen código ejecutable y alguna interfaz web conectada. La cobertura más sólida está en el aislamiento de datos, las transferencias de inventario y el registro y la reconciliación offline. Las diferencias de mayor impacto están en la repetición de operaciones comerciales, la resolución de revisiones offline fallidas y la visibilidad incompleta de la auditoría. Un submenú habilitado para el superadministrador acredita navegación, mientras que la aceptación de cada caso depende de sus operaciones y reglas.

## Criterio de evaluación

- **Backend %** y **Frontend %** son estimaciones de cobertura funcional por decenas. Para cada capa se asignaron hasta dos puntos a cada uno de cinco aspectos. En backend se evaluaron contrato, flujo normal, autorización y aislamiento, alternativas o consistencia y evidencia de ejecución. En web se evaluaron acceso, interacción principal, conexión con la API, alternativas y evidencia de ejecución. Dos puntos indican cobertura suficiente, uno cobertura parcial y cero ausencia. Los porcentajes web excluyen Flutter, que se evalúa por separado en cada ficha.
- **Completo** exige que los flujos requeridos tengan implementación y evidencia suficiente en las plataformas que especifica la ficha. **En Progreso / Parcial** indica una brecha funcional o de aceptación relevante. **Solo Backend**, **Solo Mock** y **Pendiente / No Encontrado** se reservan para ausencia de las capas o de un flujo efectivo. Ningún CU completo se clasifica como mock por el hecho de contener una integración externa simulada en pruebas.
- Graphify se usó para localizar dependencias. Los contratos, permisos, consultas y estados se contrastaron con las fuentes actuales. La numeración de algunos comentarios heredados corresponde a los CU anteriores. La referencia de numeración es el Word y el menú `use-case-navigation.ts`.
- Las referencias abreviadas **API**, **Web** y **Móvil** corresponden respectivamente a `Parcial2_backend/app`, `Parcial2_frontend-web/src/app` y `Parcial2_mobile/lib`. Las migraciones se encuentran en `Parcial2_backend/database/migrations`. Todas las rutas de negocio aquí citadas tienen prefijo `/api`.

## Resumen por caso de uso

| CU | Nombre | Estado | Backend % | Frontend % | Offline/Sync |
|---|---|---|---:|---:|---|
| CU01 | Gestionar acceso y cuenta | En Progreso / Parcial | 100 % | 100 % | Conserva pendientes al cerrar sesión |
| CU02 | Administrar empresas, planes y suscripciones | En Progreso / Parcial | 90 % | 90 % | Gestión en línea. Vigencia limita las operaciones |
| CU03 | Administrar personal, roles y permisos | En Progreso / Parcial | 90 % | 70 % | Permisos vigentes se revalidan al sincronizar |
| CU04 | Gestionar ciudades y sucursales | En Progreso / Parcial | 90 % | 70 % | Copia operativa parcial en CU16 |
| CU05 | Gestionar fichas de clientes | En Progreso / Parcial | 90 % | 80 % | Fichas mínimas descargadas para operar |
| CU06 | Administrar catálogo de prendas | En Progreso / Parcial | 90 % | 90 % | Lectura desde snapshot. Edición en línea |
| CU07 | Gestionar proveedores, compras y recepciones | En Progreso / Parcial | 90 % | 90 % | Confirmación en línea |
| CU08 | Consultar inventario y disponibilidad | En Progreso / Parcial | 80 % | 70 % | Snapshot de disponibilidad por sucursal |
| CU09 | Explorar catálogo y asistencia de compra | En Progreso / Parcial | 90 % | 90 % | Catálogo local separado. IA en línea |
| CU10 | Registrar movimientos de inventario | En Progreso / Parcial | 90 % | 90 % | Movimientos en línea. Las ventas offline generan salidas al confirmar |
| CU11 | Realizar compra y pago en línea | En Progreso / Parcial | 90 % | 80 % | Checkout y pagos en línea |
| CU12 | Gestionar reservas de prendas | En Progreso / Parcial | 90 % | 90 % | Reserva provisional vía CU16 y CU17 |
| CU13 | Registrar venta presencial | En Progreso / Parcial | 90 % | 90 % | Venta de contado provisional en CU16 |
| CU14 | Obtener comprobantes de compra | En Progreso / Parcial | 90 % | 90 % | PDF central tras confirmar la venta |
| CU15 | Gestionar cambios y reembolsos | En Progreso / Parcial | 90 % | 90 % | Atención y pagos en línea |
| CU16 | Registrar y consultar operaciones offline | En Progreso / Parcial | 100 % | 90 % | IndexedDB y SQLite, autorización por tiempo y sucursal |
| CU17 | Sincronizar operaciones y resolver conflictos | En Progreso / Parcial | 90 % | 90 % | UUID, lotes, reintentos, revisión y compensación |
| CU18 | Obtener reportes comerciales | En Progreso / Parcial | 90 % | 90 % | Consultas y exportaciones en línea |
| CU19 | Preparar y consultar analítica inteligente | En Progreso / Parcial | 90 % | 100 % | Entrenamiento separado. Consulta en línea |
| CU20 | Consultar auditoría y trazabilidad | En Progreso / Parcial | 80 % | 70 % | Eventos de sincronización al procesar en servidor |

## Evaluación detallada

### CU01 · Gestionar acceso y cuenta

- **Estado** — En Progreso / Parcial.
- **Backend** — `routers/auth.py` implementa `POST /api/login`, `/api/auth/registro`, `/api/auth/seleccionar-tienda`, `/api/auth/recuperar-password`, `/api/auth/verificar-token-recuperacion` y `/api/auth/restablecer-password`. `routers/saas.py` aporta `GET /api/contexto` y `POST /api/logout`. `services/identity.py`, `services/auth_service.py` y `tenant_middleware.py` firman y revalidan JWT, estado y versiones de identidad. Migraciones 017 y 019 crean `cuenta_global`, `cuenta_recuperacion`, perfiles y operadores SaaS. El enlace lleva un token almacenado como hash, vence a los 30 minutos y se invalida al usarlo. `services/email_service.py` aplica el alias demo y usa SMTP.
- **Web / PWA** — `features/auth/` contiene login, alta de cliente, solicitud y restablecimiento. `features/tiendas/`, `AuthService`, `authGuard`, `tiendaGuard` y el interceptor enlazan el contexto autenticado. `features/casos-plataforma/` muestra la cuenta global y abre la recuperación sin selector de empresa. Las pruebas previas de este chat registran recepción en Mailpit, apertura con sesión activa y revocación tras restablecer.
- **Móvil Flutter** — `features/login/`, `features/auth/screens/`, `features/tiendas/`, `services/auth_service.dart` y `core/session_vault.dart`. Inicio, registro, recuperación y elección de tienda están presentes.
- **Gaps / deuda** — Flutter anuncia un enlace y un código, mientras el correo contiene un enlace con token. El formulario nativo permite pegar el token y el enlace apunta al navegador. Falta concordar ese recorrido y verificar la recuperación final en Android. La captura de Mailpit para el alias Gmail está verificada. En producción se comprobó la configuración de ese alias y la salud de la API. La entrega al buzón Gmail de destino con el alias actual carece de comprobación directa en esta auditoría.

### CU02 · Administrar empresas, planes y suscripciones

- **Estado** — En Progreso / Parcial.
- **Backend** — `routers/saas.py` expone `GET/POST /api/empresas`, `PATCH /api/empresas/{id}`, `GET/PATCH /api/planes` y `GET/PUT /api/suscripciones/{id}`. Alta de empresa, plan inicial, roles y administrador en la misma transacción. Migración 002 define `empresa`, `plan`, `suscripcion`, límites Básico 2 y Profesional 10, RLS y cupos. `tenant_middleware.py` verifica vigencia antes de mutaciones y conserva vías de consulta y regularización.
- **Web / PWA** — `features/saas/saas.ts` ofrece gobierno SaaS y consulta del contrato por empresa. `rolGuard` y `CasosPlataforma` separan los ámbitos. `test_subscriptions.py` cubre aprovisionamiento, cambio a plan menor y consultas con suscripción vencida.
- **Móvil Flutter** — Selección de tienda y consumo de contexto. La ficha asigna el gobierno a la consola, por lo que no se exige replicar en Flutter la edición de planes.
- **Gaps / deuda** — `edit_subscription` comprueba sucursales activas antes de asignar un plan menor. `edit_plan` modifica directamente el cupo global tras bloquear la fila de plan y carece de comprobación equivalente sobre las empresas suscritas. Tampoco existe un campo de plan inactivo para el alternativo que lo exige. Falta reflejar estos rechazos en la interfaz.

### CU03 · Administrar personal, roles y permisos

- **Estado** — En Progreso / Parcial.
- **Backend** — `routers/usuarios.py`, `roles.py` y `administracion_ext.py` implementan `/api/usuarios/`, `POST /api/roles`, `/api/roles/{id}/permisos` y `PUT /api/usuarios/{id}/sucursales`. `usuario`, `rol`, `permiso`, `rol_permiso` y `usuario_sucursal` vinculan empleados, permisos y sucursales. `identity_index_user` protege el correo global y la identidad del cliente. La revocación se aplica al validar la sesión.
- **Web / PWA** — `features/usuarios/`, `features/admin/roles-permisos/`, `usuario.service.ts` y `permiso.service.ts` cubren usuarios, rol, baja/reactivación y matriz. El guard y varias rutas autorizan mediante listas de roles nominales.
- **Móvil Flutter** — El perfil y la empresa autorizan la navegación. La administración de personal corresponde a la web.
- **Gaps / deuda** — El formulario de usuario no conecta el endpoint de asignación de sucursales. La matriz muestra permisos del rol, pero falta una vista del permiso efectivo por usuario, incluida su sucursal. Los roles personalizados creados por API no consiguen acceso automático a las rutas que exigen nombres fijos, aunque se les asigne el permiso correspondiente. Falta prueba del flujo UI completo alta → sucursal → comprobación → revocación.

### CU04 · Gestionar ciudades y sucursales

- **Estado** — En Progreso / Parcial.
- **Backend** — `routers/geografia.py` expone `GET/POST /api/ciudades`, `GET/POST /api/sucursales`, `PUT /api/sucursales/{id}`. `administracion_ext.py` añade `PATCH /api/sucursales/{id}/estado`. Migración 002 aporta `activa`, RLS, referencias del tenant y el trigger de cupo con bloqueo de empresa. La 014 protege datos operativos por sucursal.
- **Web / PWA** — `features/sucursales/` y `geografia.service.ts` permiten consulta y alta de ciudad, alta y edición de sucursal. El modal conserva `id_encargado` de la fila existente y envía nulo en una nueva.
- **Móvil Flutter** — Inventario, movimientos y offline consumen sucursales autorizadas. La administración del directorio corresponde a la web.
- **Gaps / deuda** — La web no conecta suspensión/reactivación ni ofrece selección de encargado. El esquema de respuesta heredado tampoco expone `activa` para representar el estado. No se acredita un recorrido de consulta local del directorio de ciudades y responsables, más allá de la sucursal del snapshot offline.

### CU05 · Gestionar fichas de clientes

- **Estado** — En Progreso / Parcial.
- **Backend** — `routers/clientes.py` y `services/cliente_service.py` implementan `/api/clientes/`, `/api/clientes/{id}` y `/api/clientes/me`. `routers/auth.py` agrega `/api/cuenta/perfil` y `/api/cuenta/compras`. Migraciones 002, 003 y 017 aíslan la ficha comercial y separan identidad global de compras por tienda.
- **Web / PWA** — `features/clientes/` mantiene la ficha. `features/tiendas/` muestra compras globales y `features/cliente/mis-pedidos/` las consulta por tienda. `ClienteService` y `VentaService` consumen estas rutas.
- **Móvil Flutter** — `features/tiendas/tiendas_screen.dart` muestra historial global. Checkout obtiene la ficha propia para reservar. Offline selecciona fichas mínimas descargadas.
- **Gaps / deuda** — El historial del titular está implementado. Falta enlazar desde una ficha administrativa su historial comercial autorizado, con paginación y filtros según el rol. En móvil no se identificó una pantalla específica de edición de la ficha global.

### CU06 · Administrar catálogo de prendas

- **Estado** — En Progreso / Parcial.
- **Backend** — `routers/categorias.py`, `temporadas.py`, `prendas.py` y `services/prenda_service.py` exponen `/api/categorias/`, `/api/temporadas/`, `/api/prendas/`, tallas, colores e imágenes. `prenda`, `variante_prenda`, `variante_color`, `categoria` y `temporada` cubren catálogo y relaciones. Migraciones 004 y 016 agregan multicolor y fechas de oferta. `services/commerce.py` calcula precio aplicable y umbral de mayoreo.
- **Web / PWA** — `features/prendas/`, `categorias/`, `temporadas/` y sus servicios editan atributos, variantes, tarifas y vigencias. La vitrina consume catálogo publicado.
- **Móvil Flutter** — Vitrina, ficha y variantes en `features/catalogo/` y `features/detalle/`. La edición administrativa corresponde a la web.
- **Gaps / deuda** — `prenda-modal.ts` permite guardar material y medidas vacíos, aunque el alternativo de la ficha exige rechazar omisiones obligatorias. El módulo agrupa temporadas y colecciones bajo `temporada`. Si la ficha requiere colecciones administrables como entidad distinta, falta ese contrato. La prueba de publicación y desactivación con historial debe comprobar los tres módulos, además de sus tests de catálogo y variantes.

### CU07 · Gestionar proveedores, compras y recepciones

- **Estado** — En Progreso / Parcial.
- **Backend** — `routers/proveedores.py` y `compras.py` implementan CRUD de proveedor y `POST/GET /api/compras/`, `GET /api/compras/{id}`. `services/compra_service.py` inserta `compra`, `detalle_compra` y entradas de `movimiento_inventario` con auditoría en la transacción. El trigger incrementa el inventario.
- **Web / PWA** — `features/proveedores/` y `features/compras/` contienen directorio, listado, detalle y formulario `compras/nueva` para proveedor, variantes, cantidades, costos y sucursal.
- **Móvil Flutter** — `proveedores_screen.dart`, `compras_screen.dart`, `compra_detalle_screen.dart` y `compra_service.dart` ofrecen lectura, que es el alcance móvil de la ficha.
- **Gaps / deuda** — La confirmación registra la compra y recepción en una sola llamada. Falta una clave de idempotencia o una transición de compra preparada a recibida que permita reintentar ante respuesta perdida sin duplicar entradas. La transacción protege un intento individual. En la prueba efímera, dos POST iguales devolvieron dos compras y sumaron dos unidades.

### CU08 · Consultar inventario y disponibilidad

- **Estado** — En Progreso / Parcial.
- **Backend** — `routers/inventario.py` ofrece `GET /api/inventario/resumen` y `/monitoreo`. `routers/catalogo.py` ofrece `GET /api/catalogo/variantes/{id}/disponibilidad`. `inventario_catalogo` de la migración 005 descuenta retenciones no vencidas. `commerce.py` y movimientos reutilizan disponibilidad para autorizar operaciones.
- **Web / PWA** — `features/inventario-monitoreo/` y `InventarioMonitoreoService` consultan el stock del monitor. `features/offline/` muestra disponibilidad descargada, fecha y vigencia.
- **Móvil Flutter** — `estado_inventario_screen.dart` y `inventario_monitoreo_service.dart` muestran el monitor. `OfflineScreen` expone catálogo descargado por sucursal.
- **Gaps / deuda** — `inventario_service.py` calcula el monitor con `inventario.stock`. El monitor no separa físico, retenido y disponible, y Flutter rotula el total físico como disponible. Con cinco unidades y una reserva de tres, la prueba devolvió cinco en el monitor y dos en el snapshot. Falta exponer los tres campos en el contrato y en ambos monitores con la fecha de actualización.

### CU09 · Explorar catálogo y asistencia de compra

- **Estado** — En Progreso / Parcial.
- **Backend** — `routers/catalogo.py` y `services/catalogo_service.py` ofrecen `GET /api/catalogo/`, filtros, ficha y disponibilidad. `routers/ia.py` conecta `POST /api/ia/recomendar/`, `/try-on/` y `/realtime-token/`. `ia_service.py` valida recomendaciones contra catálogo con stock y devuelve un fallback identificado. `tryon_service.py` integra proveedores y alternativas de procesamiento.
- **Web / PWA** — `features/tiendas/`, `catalogo/`, `ia/asistente-moda/`, vestidor y carrito utilizan las rutas. El catálogo descargado se consulta desde la pantalla offline.
- **Móvil Flutter** — `catalogo_screen.dart`, `prenda_detalle_screen.dart`, `asistente_moda_screen.dart`, `vestidor_virtual_screen.dart` y `ia_service.dart` cubren búsqueda, ficha, cámara y asistencia.
- **Gaps / deuda** — La API pública y ambas vitrinas filtran categoría, género, talla, color y precio. Falta el filtro de temporada de la ficha. Conviene probar el proveedor real, su fallback y cámara denegada en el cliente y dispositivo de entrega. Los adaptadores reales y el fallback explícito impiden clasificar el CU como mock.

### CU10 · Registrar movimientos de inventario

- **Estado** — En Progreso / Parcial.
- **Backend** — `routers/movimientos.py`, `services/movimiento_service.py` y `schemas/movimiento.py` gestionan `GET/POST /api/movimientos-inventario/` y `GET /stock`. El trigger de `movimiento_inventario` aplica el efecto físico. La migración 018 agrega `traspaso_inventario`, UUID, dos movimientos enlazados y restricciones del tenant. Hay pruebas de concurrencia, rollback y reenvío para transferencias.
- **Web / PWA** — `features/inventario-movimientos/`, el modal y su servicio permiten registrar y consultar movimientos y transferencias.
- **Móvil Flutter** — `movimientos_screen.dart`, `registrar_movimiento_screen.dart` y `movimiento_service.dart` exponen el flujo. `inventory_transfer_test.dart` verifica el contrato de transferencia.
- **Gaps / deuda** — El UUID idempotente se aplica al traspaso. El camino de entrada, salida o ajuste directo inserta el movimiento sin el mismo control de reenvío. Falta llevar la regla del alternativo 5b a esos tipos y probar pérdida de respuesta.

### CU11 · Realizar compra y pago en línea

- **Estado** — En Progreso / Parcial.
- **Backend** — `routers/cotizaciones.py`, `ventas.py`, `pagos.py`, `order_lifecycle.py` y `services/payments.py` cubren `/api/ventas/cotizar`, `/api/ventas/reserva`, `/api/pagos/stripe/crear-sesion`, webhook, QR y estado de pago. Migraciones 004 y 015 impiden duplicar la venta de una reserva y persisten `stripe_event`. Firma, monto, moneda, metadatos y estados se validan. QR es un código propio con conciliación manual.
- **Web / PWA** — Carrito, `features/checkout/`, retorno de pago y `features/pagos-control/` cubren pedido, QR/Stripe, verificación y entrega.
- **Móvil Flutter** — `carrito_screen.dart`, `checkout_screen.dart`, `stripe_webview_screen.dart` y `venta_service.dart` cotizan, seleccionan sucursal, abren pago y esperan confirmación del servidor.
- **Gaps / deuda** — La sucursal se elige, pero falta una modalidad de entrega diferenciada en el contrato y en ambas interfaces. Stripe usa SDK real en modo prueba. Las pruebas del webhook y el ciclo de pagos usan eventos firmados de prueba y sustitutos del SDK, por lo que la aceptación del checkout completo con Stripe Sandbox queda separada. QR manual no acredita confirmación bancaria automática.

### CU12 · Gestionar reservas de prendas

- **Estado** — En Progreso / Parcial.
- **Backend** — `routers/ventas.py`, `order_lifecycle.py`, `services/venta_service.py` y `commerce.py` ofrecen `POST /api/ventas/reserva`, `/api/ventas/mis-reservas/{id}`, rutas de probador, estado de pago, cancelación y entrega. Migración 005 crea `retencion`. La reserva ordinaria retiene 24 horas y el cálculo excluye retenciones vencidas. RLS protege titularidad y sucursal.
- **Web / PWA** — `features/reservas-atencion/` permite atender reservas. Checkout ofrece la variante `?flujo=reserva` con confirmación sin pago y el módulo de entregas separa el cierre físico.
- **Móvil Flutter** — `ticket_reserva_screen.dart`, checkout y offline registran y muestran reservas en sus respectivos recorridos. La atención del personal se concentra en web.
- **Gaps / deuda** — La protección de stock y la unicidad de la venta por reserva están implementadas. Falta una deduplicación específica del alta de reserva ante repetición de la misma solicitud con stock todavía disponible. En móvil, falta comprobar un recorrido equivalente de consulta y seguimiento de reservas ordinarias independientemente del checkout, además del ticket de probador.

### CU13 · Registrar venta presencial

- **Estado** — En Progreso / Parcial.
- **Backend** — `routers/pos.py`, `schemas/pos.py` y `services/pos_service.py` implementan `GET /api/pos/productos`, `GET /api/pos/reserva/{codigo}` y `POST /api/pos/ventas`. Validan sucursal, existencias, precios y efectivo, calculan vuelto y registran venta, salida y auditoría. El PDF se intenta en un savepoint separado.
- **Web / PWA** — `features/pos/pos.ts` y `PosService` muestran la terminal por sucursal, ticket, carga de reserva, pago, vuelto y descarga de comprobante.
- **Móvil Flutter** — La venta de contado provisional está en `OfflineScreen`. No se identificó una terminal POS online separada, que la ficha no establece como entrega móvil explícita.
- **Gaps / deuda** — `POSVentaCrear` carece de una clave idempotente general. En la prueba efímera, dos POST iguales sin reserva crearon dos ventas y descontaron dos unidades. La unicidad ligada a reserva y la del sincronizador cubren otros caminos. La terminal selecciona sucursal y no representa una caja habilitada como entidad independiente.

### CU14 · Obtener comprobantes de compra

- **Estado** — En Progreso / Parcial.
- **Backend** — `routers/comprobantes.py` y `services/comprobante_service.py` exponen `GET /api/comprobantes`, `POST /generar`, búsqueda por venta, verificación y descarga `/{numero}/pdf`. ReportLab produce PDF con QR. La descarga verifica la fila y la ruta dentro del tenant. Las migraciones 003 y 014 restringen titularidad y sucursal.
- **Web / PWA** — `features/comprobantes/`, `features/cliente/mis-pedidos/`, checkout, POS, `ComprobanteService` y `DescargaService` ofrecen consulta y PDF autenticado.
- **Móvil Flutter** — Checkout genera y descarga el comprobante con `ApiClient.download` y `OpenFilex`. El historial global muestra las compras.
- **Gaps / deuda** — Si existe la fila y falta el archivo, la descarga responde 404 mientras la generación responde 409 por duplicado. Falta una regeneración segura de esa representación sin nueva emisión. Flutter necesita recuperación desde el historial al volver a abrir la aplicación, además de la descarga inmediata del checkout.

### CU15 · Gestionar cambios y reembolsos

- **Estado** — En Progreso / Parcial.
- **Backend** — `routers/cambios.py` y `services/exchanges.py` exponen `/api/cambios`, elegibles, recepción, reemplazo, pago, cancelación, reembolso y entrega. Migraciones 006, 012 y 015 sostienen cambio, ajuste monetario y notificaciones. Valida elegibilidad y cantidad, registra recepción física, crédito, diferencia y restitución. Stripe de prueba y compensación manual por medio original son vías distintas.
- **Web / PWA** — `features/cambios/cambios.ts` permite solicitud, recepción, selección de reemplazo, diferencias, reembolso, entrega y bandeja.
- **Móvil Flutter** — `features/cambios/cambios_screen.dart` cubre solicitud, estado, pago/cancelación y bandeja. `core/push_service.dart` y los endpoints de dispositivo preparan FCM.
- **Gaps / deuda** — El límite actual compara 168 horas desde la entrega, mientras «siete días calendario» requiere acordar el corte de fecha local y probar el límite. Se acredita la bandeja y pruebas del despachador. El [estado de Firebase](FIREBASE.md) deja pendiente la entrega push real, y el reembolso con proveedor necesita su evidencia Sandbox independiente.

### CU16 · Registrar y consultar operaciones offline

- **Estado** — En Progreso / Parcial.
- **Backend** — `routers/offline.py` ofrece `GET /api/offline/catalogo` con autorización por sucursal, disponibilidad, clientes y resultados conocidos. `services/synchronization.py` firma una autorización de hasta 24 horas y la acota por suscripción. El snapshot es un subconjunto explícito, con límite por consulta.
- **Web / PWA** — `features/offline/`, `core/services/offline-store.ts` y `offline.service.ts` utilizan Dexie, transacciones IndexedDB y separación por cuenta y empresa. `app.config.ts`, `angular.json` y `ngsw-config.json` registran el Service Worker y la navegación offline. Captura reserva y contado, historial, UUID, disponibilidad local, vigencia y exportación de pendientes.
- **Móvil Flutter** — `local_database.dart`, `offline_controller.dart`, `offline_screen.dart` y `database_recovery.dart` usan SQLite y mantienen las operaciones al reiniciar o cambiar de cuenta. Las evidencias A4/A5 documentan ensayos Android de conservación y reconciliación.
- **Gaps / deuda** — El registro provisional queda en el historial, visible con UUID y estado. La exportación web entrega pendientes en JSON y Flutter permite copiar la operación. Falta presentar una constancia individual pensada para el usuario, con resumen y marca provisional, como pide el paso 7. La aceptación Android histórica corresponde al APK y escenarios de su evidencia, no al binario más reciente de este árbol.

### CU17 · Sincronizar operaciones y resolver conflictos

- **Estado** — En Progreso / Parcial.
- **Backend** — `routers/offline.py` y `services/synchronization.py` implementan `POST /api/sincronizacion/lote`, `GET /api/sincronizacion/operaciones/{uuid}`, `GET /api/conflictos` y compensación. La migración 009 crea `operacion_sync`. UUID por tenant, huella de payload, bloqueo, permisos actuales y transacciones por operación protegen el reenvío. Se validan stock y precios y se devuelve un estado por operación.
- **Web / PWA** — `offline.service.ts` y `Offline` cubren envío manual/automático, reintentos, consulta de cola, conciliación por sucursal y compensación de conflictos locales o centrales.
- **Móvil Flutter** — `offline_controller.dart` y `offline_screen.dart` conservan el UUID, reintentan y permiten revisar y compensar operaciones locales. A5 acredita 125 UUID en bloques de 50 para reconciliación de catálogo. El envío comercial usa un lote distinto.
- **Gaps / deuda** — En `synchronization.py`, una revisión marca `revision=True` antes de ejecutar el negocio. La prueba efímera confirmó que, si la nueva operación también queda en conflicto, la consulta del original devuelve `resolved: true`. IndexedDB también marca el original como resuelto al preparar la nueva operación, antes de la confirmación central. Falta distinguir «en revisión» de «resuelto» y verificar la recuperación de una revisión nuevamente rechazada. Flutter carece de la bandeja de conflictos centrales que ofrece Angular.

### CU18 · Obtener reportes comerciales

- **Estado** — En Progreso / Parcial.
- **Backend** — `routers/reportes.py`, `schemas/reports.py` y `services/reports.py` ofrecen `/api/reportes/tipos`, `/convencional`, `/generativo`, resultados y `/exportar/{format}`. Ejecutan seis consultas parametrizadas, guardan el resultado en `reporte_resultado` y exportan el mismo conjunto a PDF/XLSX. La IA interpreta una intención estructurada y exige plan habilitado y sucursal autorizada.
- **Web / PWA** — `features/reportes/` ofrece filtros, texto, dictado por Web Speech, presentación y exportación. `features/ia/analitica-voz/` ofrece otra interfaz cuyo endpoint delega en el mismo intérprete y aplica los controles de reportes.
- **Móvil Flutter** — `reportes_screen.dart` realiza consultas convencionales y generativas y descarga PDF/XLSX. El campo acepta texto o dictado del teclado del dispositivo.
- **Gaps / deuda** — `ReportFilters` acepta categoría y sucursal, pero carece del filtro de producto requerido por la ficha. Flutter no incorpora control de dictado propio. Las pruebas de contratos, permisos y exportaciones no sustituyen la demostración de Gemini real con una solicitud ambigua, otra denegada y una exportación en el entorno final.

### CU19 · Preparar y consultar analítica inteligente

- **Estado** — En Progreso / Parcial.
- **Backend** — `routers/analitica.py`, `services/analytics.py` y `routers/dashboard.py` implementan `GET /api/analitica/modelos`, `/dashboard` y `/api/kpis`. `Parcial2_backend/ml/train.py` genera datos sintéticos, ajusta `HistGradientBoostingRegressor` y K-Means sobre RFM y versiona artefactos y hashes. Metadatos v1: MAE 2,164 frente a 3,173 de la referencia, RMSE 2,898 frente a 4,100 y silueta 0,262. Son resultados de datos sintéticos.
- **Web / PWA** — `features/dashboard/` y `features/analitica/` muestran KPI, predicciones, segmentos, origen y limitaciones. Consultar el panel carga modelos y realiza inferencia.
- **Móvil Flutter** — No se identificó un dashboard ML independiente. La ficha asigna la consulta empresarial al dashboard y el entrenamiento a una herramienta técnica externa.
- **Gaps / deuda** — `artifact()` calcula el hash con `path.read_bytes()`. Con metadata válida y binario ausente, la prueba reprodujo `FileNotFoundError`. El dashboard atrapa `HTTPException` y deja sin cubrir ese caso, aunque el alternativo exige mantener los KPI y advertir. Falta cubrir la degradación ante artefacto ausente o ilegible. La precisión con datos reales queda fuera de los resultados de entrenamiento sintético.

### CU20 · Consultar auditoría y trazabilidad

- **Estado** — En Progreso / Parcial.
- **Backend** — `routers/bitacora.py` y `services/bitacora_service.py` exponen `GET /api/bitacora` con paginación y filtros de acción, tabla y búsqueda. Migración 007 registra mutaciones comerciales en la misma transacción. La 017 registra accesos, registro, recuperación y cierre en `auditoria_identidad`. Sincronización, pagos y cambios escriben eventos de negocio según sus flujos.
- **Web / PWA** — `features/bitacora/bitacora.ts`, `BitacoraService` y CU20 muestran eventos del ámbito SaaS o de la empresa seleccionada. La pantalla consume `bitacora` con la autorización de su ruta.
- **Móvil Flutter** — No se identificó una vista administrativa de auditoría. El historial offline por UUID es de operaciones propias.
- **Gaps / deuda** — El endpoint consulta `bitacora` y deja fuera `auditoria_identidad`. En la prueba, un inicio de sesión generó una fila `LOGIN_EXITOSO` en identidad y el filtro equivalente del endpoint devolvió cero. Faltan filtros dedicados por fecha, usuario y UUID. La búsqueda textual puede encontrar identificadores en detalles, con una semántica diferente a un filtro explícito. El router restringe la consulta a Administrador aunque la ficha incluye a Encargado de sucursal. Falta habilitar ese rol con alcance efectivo y correlacionar sus eventos autorizados.

## Hallazgos prioritarios y comprobación de cierre

| Prioridad | Hallazgo | Evidencia que permitiría cerrarlo |
|---|---|---|
| Alta | Reenvío de compra o POS sin reserva repitió el efecto comercial. CU07 y CU13 | Simular respuesta perdida, reenviar la misma operación y verificar una sola compra o venta y un solo conjunto de movimientos |
| Alta | Una revisión offline fallida cerró el conflicto original. CU17 | Rechazar una revisión en servidor y verificar que el original sigue pendiente de resolución en PostgreSQL, IndexedDB y SQLite |
| Alta | Un cambio directo de cupo global dejó un plan con límite 1 y dos sucursales activas en una empresa suscrita. CU02 | Intentar reducir el cupo con empresas suscritas por encima del valor y verificar rechazo atómico |
| Media | El monitor mostró cinco unidades físicas frente a dos disponibles tras reservar tres. CU08 | Reservar y cancelar sobre una variante de prueba y verificar físico, retenido y disponible por sucursal en ambos clientes |
| Media | La auditoría web omite eventos de identidad y filtros de la ficha. CU20 | Generar login, recuperación, cambio y sincronización. Verificar filtros, correlación y alcance de Administrador y Encargado |
| Media | La aceptación de proveedores externos depende del entorno final. CU01, CU09, CU11, CU15 y CU18 | Acreditar recepción real de correo, vestidor/asistente, Stripe Sandbox con webhook, push y reporte Gemini con evidencia separada |

## Evidencia de ejecución

| Entorno | Resultado | Alcance |
|---|---|---|
| FastAPI y PostgreSQL 17 efímero | 299 aprobadas y una fallida en la ejecución general de 300 | La prueba de inferencia falló con NumPy 2.5.4 del runtime Windows. El artefacto exige 2.3.5 y el contenedor local usa 2.3.5 |
| Repetición de la suite de analítica | 4 de 4 con NumPy 2.3.5 | La prueba de inferencia que había fallado pasó con la versión fijada. El caso de binario ausente queda como brecha de código independiente |
| Reproducciones dirigidas en PostgreSQL efímero | 7 de 7 reprodujeron el comportamiento observado | Reducción de cupo, doble recepción, doble venta POS, conflicto original cerrado, stock físico distinto de disponibilidad, modelo ausente y evento de identidad omitido. Estos resultados acreditan brechas |
| Angular 20.3, Chrome Headless | 132 de 132 | Suite automatizada de la web, incluidas autenticación, navegación y almacenamiento local. No equivale a 20 recorridos de aceptación en navegador |
| Flutter en la MSI | 70 de 70 | Pruebas de Dart/Flutter, incluidos autenticación, SQLite y recuperación. La evidencia Android A4/A5 del repositorio se considera histórica y acotada a su APK |

Registros de la ejecución local en `tmp/`: `auditoria-backend-tests.log`, `auditoria-ml-repeticion.log`, `auditoria-reproducciones.log`, `auditoria-angular-tests.log` y `auditoria-flutter-tests.log`. Las reproducciones dirigidas están en `tmp/audit_regressions_test.py` y requieren la base efímera de pruebas. Evidencia previa de dispositivos y despliegue en [A4 Android](CAPITULO_V_A4_ANDROID_REAL.md), [A5 reconciliación](CAPITULO_V_A5_PRUEBAS_Y_RESULTADOS.md) y [verificación HTTP nativa](evidencias/native-http-validation.json). En esta auditoría las reproducciones y pruebas de datos se ejecutaron en el entorno de pruebas de la MSI.

## Cinco commits relevantes

Se revisó `git log -n 15 --oneline`. La selección corresponde a los cinco commits más recientes que modifican al menos una de las tres capas de aplicación. El commit documental `d98884c` sirve como referencia del examen y queda fuera de esta selección por el criterio de código.

| Commit | Aporte |
|---|---|
| `7621aff` | Habilita las interfaces de los 20 CU para el superadministrador, introduce ámbitos comerciales y agrega la migración 019 |
| `571176c` | Integra los seis paquetes, la navegación por CU y la documentación asociada |
| `8361310` | Actualiza interfaces y acceso por rol en Angular y pantallas móviles |
| `4d7aeac` | Integra correcciones C1 y A1–A6, con autorización, traspasos, recuperación/reconciliación offline y pruebas |
| `43da34d` | Introduce identidad global, inicio por correo y clientes con selección de tienda |
