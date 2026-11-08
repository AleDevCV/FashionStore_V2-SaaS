# Fichas resumidas de los 20 casos principales

Estas fichas delimitan los grupos y subflujos. Su especificación detallada deberá desarrollar precondiciones, alternativas, postcondiciones y pruebas por subflujo; no equivalen a 20 fichas atómicas ya cerradas.

## CU-01. Gestionar acceso y cuenta

**Cobertura del plan P2 anterior:** CU-01, CU-02.

**Antecedentes P1:** P1-CU-01, P1-CU-04.

**Actores:** Usuario de la plataforma.

**Objetivo y alcance:** Registrar clientes globales, iniciar y cerrar sesión, recuperar contraseña y elegir tienda después del acceso del cliente. El personal mantiene su empresa asignada.

**Flujo principal / subflujos identificados**

1. Solicitar acceso o registro con correo y contraseña.
2. Validar identidad y obtener del servidor rol y ámbito.
3. Abrir el espacio de plataforma, empresa o tiendas del cliente.
4. Recuperar acceso mediante enlace de un solo uso cuando se solicite.
5. Cerrar y revocar sesión conservando pendientes locales.

## CU-02. Administrar empresas, planes y suscripciones

**Cobertura del plan P2 anterior:** CU-03, CU-04, CU-05.

**Antecedentes P1:** Nuevos requisitos del P2.

**Actores:** Superadministrador SaaS, Administrador de empresa.

**Objetivo y alcance:** Aprovisionar empresas y su administrador, configurar planes y administrar vigencias, renovaciones y cambios. El administrador empresarial consulta únicamente su contrato.

**Flujo principal / subflujos identificados**

1. Validar facultades de plataforma o consulta de contrato propio.
2. Registrar empresa y administrador inicial cuando corresponda.
3. Configurar capacidades y límites del plan.
4. Asignar, renovar o cambiar suscripción validando cupos.
5. Consultar el estado efectivo del servicio y auditar cambios.

## CU-03. Administrar personal, roles y permisos

**Cobertura del plan P2 anterior:** CU-06, CU-07.

**Antecedentes P1:** P1-CU-02, P1-CU-03.

**Actores:** Administrador de empresa.

**Objetivo y alcance:** Mantener empleados, roles, permisos y asignaciones de sucursal de la empresa. Impedir privilegios de plataforma y cambios en la identidad global de clientes.

**Flujo principal / subflujos identificados**

1. Consultar personal y roles de la empresa.
2. Crear o actualizar empleado con correo global único.
3. Asignar rol y sucursales permitidos.
4. Activar, suspender o revocar autorizaciones.
5. Comprobar que los permisos efectivos correspondan a la asignación.

## CU-04. Gestionar ciudades y sucursales

**Cobertura del plan P2 anterior:** CU-08.

**Antecedentes P1:** P1-CU-06.

**Actores:** Administrador de empresa.

**Objetivo y alcance:** Mantener ciudades y sucursales, su estado y responsables, respetando el cupo de sucursales activas de la suscripción.

**Flujo principal / subflujos identificados**

1. Consultar ciudades y sucursales propias.
2. Registrar o modificar dirección y responsables.
3. Validar pertenencia y límite del plan.
4. Guardar alta, actualización o reactivación.
5. Mostrar la estructura operativa actualizada.

## CU-05. Gestionar fichas de clientes

**Cobertura del plan P2 anterior:** CU-09.

**Antecedentes P1:** P1-CU-05.

**Actores:** Administrador de empresa, Encargado de sucursal, Vendedor o cajero, Cliente.

**Objetivo y alcance:** Crear y mantener fichas comerciales por empresa. El cliente consulta su propia información e historial entre tiendas; la tienda accede solo al perfil y operaciones de su ámbito.

**Flujo principal / subflujos identificados**

1. Buscar ficha comercial autorizada.
2. Crear o actualizar datos de contacto permitidos.
3. Evitar duplicaciones dentro de la empresa.
4. Consultar las operaciones del cliente según propiedad y rol.
5. Conservar separada la identidad global y el historial comercial de cada tienda.

## CU-06. Administrar catálogo de prendas

**Cobertura del plan P2 anterior:** CU-10, CU-11, CU-12.

**Antecedentes P1:** P1-CU-07, P1-CU-08, P1-CU-09.

**Actores:** Administrador de empresa, Responsable de inventario y compras.

**Objetivo y alcance:** Mantener categorías, temporadas, colecciones, prendas, tallas, combinaciones de colores, material, medidas, precios y ofertas.

**Flujo principal / subflujos identificados**

1. Organizar categorías y temporadas.
2. Registrar o actualizar prenda y sus atributos.
3. Definir variantes y combinaciones de colores.
4. Configurar precios, umbral mayorista y ofertas vigentes.
5. Publicar o desactivar elementos conservando relaciones comerciales.

## CU-07. Gestionar proveedores, compras y recepciones

**Cobertura del plan P2 anterior:** CU-13, CU-14.

**Antecedentes P1:** P1-CU-12, P1-CU-13.

**Actores:** Administrador de empresa, Responsable de inventario y compras.

**Objetivo y alcance:** Administrar proveedores y compras; confirmar recepciones físicas con sus detalles y entradas de inventario. Mantener separados los subflujos de proveedor, pedido y recepción.

**Flujo principal / subflujos identificados**

1. Mantener ficha del proveedor propio.
2. Preparar compra con variantes, cantidades y costos.
3. Seleccionar sucursal de recepción autorizada.
4. Confirmar recepción y sus entradas de stock en una transacción.
5. Consultar el documento y sus detalles sin duplicar recepciones.

## CU-08. Consultar inventario y disponibilidad

**Cobertura del plan P2 anterior:** CU-15.

**Antecedentes P1:** P1-CU-10.

**Actores:** Personal de empresa.

**Objetivo y alcance:** Obtener existencias físicas, unidades retenidas y disponibilidad por sucursal y variante. El mismo comportamiento de consulta se reutiliza al confirmar una venta.

**Flujo principal / subflujos identificados**

1. Determinar empresa, sucursal y variantes autorizadas.
2. Consultar existencias físicas.
3. Obtener retenciones centrales vigentes.
4. Calcular disponibilidad para las variantes solicitadas.
5. Devolver cantidades y fecha de información; si es copia local identificar su antigüedad.

## CU-09. Explorar catálogo y asistencia de compra

**Cobertura del plan P2 anterior:** CU-17, CU-26, CU-27.

**Antecedentes P1:** P1-CU-14, P1-CU-18, P1-CU-22.

**Actores:** Visitante, Cliente, Personal de empresa, Servicio de IA.

**Objetivo y alcance:** Consultar catálogo y filtros, variantes y disponibilidad; utilizar opcionalmente el vestidor existente y las recomendaciones sobre prendas de la tienda elegida.

**Flujo principal / subflujos identificados**

1. Elegir tienda pública o usar el contexto empresarial autorizado.
2. Buscar prendas mediante filtros.
3. Consultar variantes y precios aplicables.
4. Solicitar vestidor o recomendaciones si el usuario lo desea.
5. Seleccionar prendas para una compra o reserva independiente.

## CU-10. Registrar movimientos de inventario

**Cobertura del plan P2 anterior:** CU-16.

**Antecedentes P1:** P1-CU-11.

**Actores:** Administrador de empresa, Responsable de inventario y compras, Encargado de sucursal.

**Objetivo y alcance:** Registrar entradas, salidas, ajustes y transferencias autorizadas. Reutilizar el registro de salida en ventas confirmadas sin descontar stock por un segundo mecanismo.

**Flujo principal / subflujos identificados**

1. Identificar sucursales, variantes y motivo del movimiento.
2. Validar cantidades, pertenencia y autorización.
3. Bloquear o controlar las existencias afectadas.
4. Registrar el movimiento y su efecto único sobre stock.
5. Confirmar trazabilidad; revertir todo ante un fallo.

**Implementación A3, validada en entorno aislado:** origen/destino y UUID obligatorios para Traspaso; ambas sucursales activas y autorizadas. Salida + Entrada vinculadas, sin doble mecanismo de descuento; disponibilidad resta retenciones. Reintento idéntico no vuelve a mutar; UUID con otro contenido se rechaza; cualquier fallo revierte el conjunto y no emite 201. Exclusivamente online; Entrada/Salida mantienen contrato. A3 no está activado en la demostración persistente. [Evidencias y límites](../CORRECCION_AUTORIZACION_A3.md).

## CU-11. Realizar compra y pago en línea

**Cobertura del plan P2 anterior:** CU-18, CU-22.

**Antecedentes P1:** P1-CU-15, P1-CU-20.

**Actores:** Cliente, Pasarela de pagos.

**Objetivo y alcance:** Administrar carrito y checkout hasta la confirmación de una compra pagada. La pasarela informa el resultado firmado; un pedido o pago pendiente no confirma una venta.

**Flujo principal / subflujos identificados**

1. Preparar carrito, sucursal y forma de entrega.
2. Recalcular precios y consultar disponibilidad mediante CU-08.
3. Iniciar pago electrónico y mantener estado pendiente.
4. Validar confirmación firmada, importe e identidad de operación.
5. Confirmar venta y salida de inventario mediante CU-10 una sola vez.

**Relaciones salientes:**
- «include» hacia CU-08: Consulta obligatoria de existencias para validar la compra central.
- «include» hacia CU-10: Salida obligatoria al confirmar una compra pagada; el checkout abandonado o pendiente no alcanza este punto.

## CU-12. Gestionar reservas de prendas

**Cobertura del plan P2 anterior:** CU-19, CU-20.

**Antecedentes P1:** P1-CU-16, P1-CU-17.

**Actores:** Cliente, Encargado de sucursal, Vendedor o cajero, Administrador de empresa.

**Objetivo y alcance:** Registrar y consultar reservas centrales, preparar prendas, cancelar, vencer y entregar según sus transiciones. El cliente opera solo sobre sus reservas.

**Flujo principal / subflujos identificados**

1. Solicitar reserva con cliente, sucursal y detalles.
2. Comprobar disponibilidad y establecer retención central.
3. Consultar o preparar prendas según permisos.
4. Confirmar pago cuando corresponda antes de entregar.
5. Entregar o cancelar; liberar retenciones al vencer sin crear una venta ficticia.

## CU-13. Registrar venta presencial

**Cobertura del plan P2 anterior:** CU-21.

**Antecedentes P1:** P1-CU-19.

**Actores:** Vendedor o cajero, Encargado de sucursal, Administrador de empresa.

**Objetivo y alcance:** Consolidar una venta presencial autorizada con importes calculados por el servidor, efectivo y vuelto, registro comercial, salida única de stock y auditoría.

**Flujo principal / subflujos identificados**

1. Seleccionar sucursal y productos del ticket.
2. Consultar inventario mediante CU-08 y validar disponibilidad.
3. Calcular precios y registrar efectivo recibido.
4. Confirmar venta y registrar salidas mediante CU-10 en una transacción.
5. Presentar resultado; ofrecer consulta o descarga de comprobante como acción adicional.

**Relaciones salientes:**
- «include» hacia CU-08: Consulta obligatoria de existencias antes de confirmar una venta presencial.
- «include» hacia CU-10: Una venta presencial confirmada registra su salida en la misma transacción.

## CU-14. Obtener comprobantes de compra

**Cobertura del plan P2 anterior:** CU-23.

**Antecedentes P1:** P1-CU-21.

**Actores:** Cliente, Vendedor o cajero, Encargado de sucursal, Administrador de empresa.

**Objetivo y alcance:** Emitir o recuperar la representación del comprobante de una venta confirmada, consultarla y descargarla con autorización. La consulta/descarga es opcional respecto al cierre de compra.

**Flujo principal / subflujos identificados**

1. Solicitar comprobante de una venta confirmada.
2. Verificar empresa, rol y propiedad de la compra.
3. Recuperar documento existente o generar su representación autorizada.
4. Presentar datos de venta y verificación.
5. Descargar PDF sin duplicar el documento comercial.

**Relaciones salientes:**
- «extend» hacia CU-11: Punto: compra confirmada. Condición: el usuario solicita visualizar o descargar su comprobante.
- «extend» hacia CU-13: Punto: venta registrada. Condición: el usuario solicita visualizar o descargar su comprobante.

## CU-15. Gestionar cambios y reembolsos

**Cobertura del plan P2 anterior:** CU-24, CU-25.

**Antecedentes P1:** Nuevos requisitos del P2.

**Actores:** Cliente, Encargado de sucursal, Administrador de empresa, Pasarela de pagos, Servicios de correo y push.

**Objetivo y alcance:** Solicitar, consultar y atender cambios: elegibilidad, recepción física, reemplazo, diferencias de precio, devolución de importes, notificaciones y entrega.

**Flujo principal / subflujos identificados**

1. Registrar solicitud vinculada a unidades de una compra comprobable.
2. Validar plazo, estado y elegibilidad de las prendas.
3. Aceptar recepción física y determinar reposición de stock.
4. Asignar reemplazo y cobrar o devolver diferencias por el medio definido.
5. Notificar resultado y registrar entrega, reembolso o solicitud pendiente.

## CU-16. Registrar y consultar operaciones offline

**Cobertura del plan P2 anterior:** CU-28, CU-29, CU-30, CU-31.

**Antecedentes P1:** Nuevos requisitos del P2.

**Actores:** Cliente, Vendedor o cajero, Encargado de sucursal, Administrador de empresa.

**Objetivo y alcance:** Preparar catálogo persistente, consultar datos descargados, registrar reservas o ventas de contado según rol y revisar operaciones locales tras reiniciar. Las ventas permanecen provisionales.

**Flujo principal / subflujos identificados**

1. Autenticar y preparar datos locales mientras exista conexión.
2. Identificar cuenta, empresa, sucursal y vigencia offline.
3. Consultar catálogo o preparar reserva/venta local según permisos.
4. Guardar UUID, cabecera, detalles y pendiente atómicamente.
5. Consultar operaciones y resultados después de cerrar y volver a abrir. La recuperación central conserva el acceso del autor dentro de su empresa; las consultas no eliminan pendientes.

## CU-17. Sincronizar operaciones y resolver conflictos

**Cobertura del plan P2 anterior:** CU-32, CU-33.

**Antecedentes P1:** Nuevos requisitos del P2.

**Actores:** Cliente, Vendedor o cajero, Encargado de sucursal, Administrador de empresa.

**Objetivo y alcance:** Enviar pendientes manual o automáticamente, recuperar resultados y tratar conflictos. El autor consulta sus operaciones; una resolución comercial requiere el permiso correspondiente.

**Flujo principal / subflujos identificados**

1. Detectar conexión o recibir solicitud manual.
2. Enviar operaciones preservando UUID y contenido.
3. Validar identidad, empresa, autor, permisos y sucursal antes de revelar resultados ajenos; aplicar suscripción y reglas por operación.
4. Guardar confirmación, rechazo o conflicto; conservar pendientes ante error temporal.
5. Resolver conflictos autorizados con nueva operación enlazada o compensación explícita. El permiso no concede acceso a sucursales ajenas; los rechazos sin sucursal siguen la política A2 aprobada.

**Alternativas de autorización A2:** el autor conserva consulta/reintentos; un supervisor sin asignación no obtiene datos por UUID ni por lote. Sin permiso no lista ni compensa. La consulta histórica admite sucursales inactivas autorizadas; compensar exige sucursal activa cuando existe. No se descartan registros. [Política, evidencias y límites](../CORRECCION_AUTORIZACION_A2.md).

## CU-18. Obtener reportes comerciales

**Cobertura del plan P2 anterior:** CU-34, CU-35.

**Antecedentes P1:** P1-CU-23.

**Actores:** Administrador de empresa, Encargado de sucursal, Servicio de IA.

**Objetivo y alcance:** Consultar reportes convencionales o solicitarlos por texto/voz mediante IA, con filtros variables y datos reales autorizados; representar y exportar resultados a PDF/XLSX.

**Flujo principal / subflujos identificados**

1. Seleccionar reporte convencional o solicitud generativa.
2. Validar permisos y acceso Profesional cuando utilice IA.
3. Interpretar y confirmar filtros o solicitar aclaración.
4. Consultar datos empresariales con operaciones permitidas.
5. Mostrar tabla/gráfico y exportar los mismos resultados autorizados.

## CU-19. Preparar y consultar analítica inteligente

**Cobertura del plan P2 anterior:** CU-36, CU-37.

**Antecedentes P1:** P1-CU-24.

**Actores:** Administrador de empresa, Encargado de sucursal, Responsable técnico de analítica.

**Objetivo y alcance:** Agrupar dos subflujos diferenciados: preparación, entrenamiento y evaluación técnica; consulta empresarial de KPI, predicciones y segmentos. Abrir el dashboard no ejecuta entrenamiento.

**Flujo principal / subflujos identificados**

1. Preparar datos sintéticos reproducibles y variables en el subflujo técnico.
2. Entrenar y evaluar modelos supervisados y no supervisados.
3. Versionar artefactos, métricas y procedencia.
4. En el subflujo empresarial obtener datos e inferencias del tenant autorizado.
5. Visualizar indicadores, predicciones y segmentos con sus limitaciones.

## CU-20. Consultar auditoría y trazabilidad

**Cobertura del plan P2 anterior:** CU-38.

**Antecedentes P1:** P1-CU-25.

**Actores:** Superadministrador SaaS, Administrador de empresa, Encargado de sucursal.

**Objetivo y alcance:** Consultar eventos autorizados de acceso y operaciones, pagos, cambios y sincronización. La plataforma consulta su ámbito técnico y SaaS sin acceso comercial irrestricto a empresas.

**Flujo principal / subflujos identificados**

1. Validar permiso y ámbito de auditoría.
2. Aplicar filtros de fecha, usuario, acción o UUID.
3. Consultar eventos paginados.
4. Relacionar acción, operación y resultado.
5. Presentar evidencia sin contraseñas, tokens ni credenciales externas.
