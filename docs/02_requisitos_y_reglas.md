# CAPÍTULO II ANÁLISIS DE REQUISITOS

## 2.1 Descripción del sistema propuesto

FashionStore SaaS presta servicios a empresas independientes. Cada empresa dispone de sucursales, personal, clientes, catálogo e inventario propios. La plataforma controla el plan contratado y autoriza la operación comercial. Angular y Flutter acceden al mismo backend REST; el almacenamiento local permite registrar operaciones provisionales que después se validan contra PostgreSQL.

## 2.2 Identificación de actores

| Actor | Responsabilidad y límite |
|---|---|
| Superadministrador | Empresas, planes y suscripciones; no posee acceso comercial indiscriminado |
| Administrador de empresa | Personal, permisos y configuración dentro de su empresa |
| Encargado | Operación de sucursales autorizadas, reservas, cambios y conflictos |
| Cajero | Venta, cobro y consulta de operaciones autorizadas |
| Responsable de inventario | Proveedores, adquisiciones, recepciones y movimientos |
| Cliente | Catálogo, compras, reservas y seguimiento de sus propios cambios |
| Pasarela | Confirma pagos mediante eventos firmados |
| Servicio IA | Interpreta solicitudes dentro del contrato permitido |
| Servicio push | Transporta avisos; la bandeja central conserva la notificación |

## 2.3 Requisitos funcionales

| ID | Capacidad | CU relacionados |
|---|---|---|
| RF01 | Autenticar por correo global sin campo Empresa, recuperar y revocar acceso; personal vinculado a su empresa y cliente con una cuenta para todas las tiendas | 01, 02 |
| RF02 | Registrar empresas independientes y su administrador | 03 |
| RF03 | Configurar límites de planes y vigencia de suscripciones | 04, 05 |
| RF04 | Administrar roles, permisos, usuarios y sucursales | 06, 07, 08 |
| RF05 | Mantener clientes, categorías, temporadas, prendas y variantes | 09 a 12 |
| RF06 | Registrar proveedores, compras y recepción de existencias | 13, 14 |
| RF07 | Consultar y modificar inventario mediante movimientos trazables | 15, 16 |
| RF08 | Consultar catálogo, precios, ofertas y variantes | 17 |
| RF09 | Gestionar carrito y checkout sin consolidar venta impaga | 18, 22 |
| RF10 | Registrar, preparar, entregar, cancelar y vencer reservas | 19, 20 |
| RF11 | Registrar ventas presenciales de contado | 21 |
| RF12 | Verificar pagos electrónicos y emitir documentos protegidos | 22, 23 |
| RF13 | Solicitar y atender cambios con diferencias y reembolsos | 24, 25 |
| RF14 | Conservar vestidor y recomendaciones existentes | 26, 27 |
| RF15 | Instalar PWA y descargar catálogo autorizado para ambos clientes | 28 |
| RF16 | Registrar reservas y ventas de contado sin red | 29, 30 |
| RF17 | Consultar operaciones pendientes tras cerrar y reabrir | 31 |
| RF18 | Sincronizar con identificación única, reintentos y resultados | 32 |
| RF19 | Detectar y resolver conflictos con historial conservado | 33 |
| RF20 | Consultar reportes convencionales filtrados | 34 |
| RF21 | Generar reportes por texto o voz con datos reales y exportación | 35 |
| RF22 | Preparar datos sintéticos y entrenar modelos supervisados y no supervisados | 36 |
| RF23 | Presentar métricas, predicciones y patrones en dashboard | 37 |
| RF24 | Auditar acceso y operaciones relevantes | 38 y transversal |

## Requisitos no funcionales del examen

| ID | Requisito | Verificación prevista |
|---|---|---|
| RNF01 | Seguridad | Autenticación, permisos y propiedad del recurso |
| RNF02 | Aislamiento | Pruebas negativas empresa A contra B |
| RNF03 | Persistencia offline | Cierre y reinicio sin pérdida |
| RNF04 | Integridad transaccional | Fallo intermedio revierte cabecera, detalles y movimientos |
| RNF05 | Idempotencia | Veinte reenvíos producen una operación |
| RNF06 | Recuperación | Fallos de red conservan pendientes |
| RNF07 | Mantenibilidad | Presentación, negocio, persistencia y sincronización identificables |
| RNF08 | Compatibilidad | PWA en navegador compatible y Flutter en Android físico |
| RNF09 | Rendimiento | Paginación, límites, índices y consulta medida |
| RNF10 | Observabilidad | UUID, intento y motivo de fallo sin secretos |
| RNF11 | Calidad | Pruebas automatizadas de reglas críticas |
| RNF12 | Coherencia documental | Símbolos, diagramas y versión de entrega coinciden |

## 2.4 Reglas de negocio

| ID | Regla |
|---|---|
| RN01 | Tenant significa empresa; una sucursal pertenece a una sola empresa. |
| RN02 | El backend establece el tenant autenticado y valida toda referencia recibida. |
| RN03 | Básico permite dos sucursales activas; Profesional diez; límites editables. |
| RN04 | Los reportes generativos requieren Profesional y permiso explícito. |
| RN05 | No se elimina información al vencer una suscripción o cambiar de plan. |
| RN06 | El downgrade se bloquea mientras exceda sucursales activas permitidas. |
| RN07 | Inventario disponible es existencia física menos retenciones centrales vigentes. |
| RN08 | Una reserva central retiene disponibilidad 24 horas; la local es provisional. |
| RN09 | Cada movimiento modifica stock una sola vez; no se permite stock negativo. |
| RN10 | El backend valida precio y recalcula importes; los descuentos no se acumulan. |
| RN11 | Mayorista aplica desde seis unidades de una prenda, con umbral configurable. |
| RN12 | Un carrito o pago pendiente no equivale a venta confirmada. |
| RN13 | Venta offline únicamente de contado y con sesión previa de hasta 24 horas. |
| RN14 | UUID es estable entre reintentos; contenido distinto con mismo UUID se rechaza. |
| RN15 | Una operación no desaparece al intentar enviarla. |
| RN16 | El lote tiene resultado por operación y transacción independiente por operación. |
| RN17 | Precio cambiado o stock insuficiente producen conflicto completo, sin aceptación parcial. |
| RN18 | Corregir un conflicto conserva el original y crea una operación nueva enlazada. |
| RN19 | Cambio de prenda se solicita hasta siete días calendario después de entrega. |
| RN20 | Solo prendas elegibles sin uso, un cambio por unidad y compra comprobable. |
| RN21 | Recepción de devolución y entrega del reemplazo son eventos separados. |
| RN22 | Crédito corresponde al precio efectivamente pagado; diferencias se cobran o devuelven íntegramente. |
| RN23 | Reembolso por medio original, con objetivo administrativo de cinco días hábiles. |
| RN24 | IA interpreta parámetros; únicamente el backend ejecuta consultas autorizadas. |
| RN25 | Los reportes consultan datos operativos; los datos sintéticos de entrenamiento se identifican. |
| RN26 | Cerrar sesión o cambiar cuenta no mezcla ni elimina silenciosamente pendientes. |

## 2.5 Diagramas UML de casos de uso

Las fuentes editables se encuentran en `diagramas/casos_uso`. Los diagramas técnicos finales se reservan para la etapa posterior al código. Las relaciones include y extend solo se incorporan cuando existe obligatoriedad o extensión condicional real del flujo.

## 2.6 Especificación de casos de uso

El archivo `03_casos_de_uso.md` contiene las 38 fichas. La fuente estructurada `casos_de_uso.json` permite mantener la tabla maestra, las fichas y la matriz sincronizadas. El estado inicial es especificado; implementación, pruebas y evidencia se registran por separado.
