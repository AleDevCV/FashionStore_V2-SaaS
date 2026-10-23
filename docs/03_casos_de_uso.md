# Especificaciones de casos de uso

Autor: Equipo FashionStore. Fecha de especificación: 22 de octubre de 2026.

Las fichas expresan comportamiento requerido. El estado de implementación y de prueba se registra en la matriz, sin inferirlo del prototipo P1.

## CU-01 Iniciar y cerrar sesión

**Actor:** Todos los usuarios. **Plataforma:** Web y Flutter. **Antecedente P1:** 01.

**Objetivo:** Sesión vinculada a una empresa y datos locales separados.

**Precondiciones:** empresa identificada y activa; permisos vigentes para operaciones privadas; referencias pertenecientes a la misma empresa. Para registro offline, snapshot y sesión previamente habilitados.

**Disparador:** el actor solicita iniciar y cerrar sesión.

**Datos:** empresa, correo, contraseña.

**Flujo principal**

1. Seleccionar empresa.
2. Enviar credenciales.
3. Validar cuenta activa y empresa.
4. Emitir sesión con permisos y sucursales.
5. Cerrar sesión por acción del usuario.

**Flujos alternativos**

- Credenciales incorrectas: respuesta uniforme sin revelar existencia.
- Empresa inactiva: impedir acceso.
- Sin red: solo sesión offline previamente habilitada.

**Postcondición:** Sesión vinculada a una empresa y datos locales separados.

**Aceptación:** ejecutar el flujo con datos de la empresa A, comprobar el resultado y repetir una petición con referencias de B para verificar la restricción cuando corresponda. Ejecutar cada alternativa y conservar el resultado real; no basta una captura de la pantalla inicial.

**Prototipo:** `prototipos/CU-01.svg`. **Diagrama:** `diagramas/casos_uso/CU-01.puml`.

## CU-02 Recuperar contraseña

**Actor:** Usuario registrado. **Plataforma:** Web y Flutter. **Antecedente P1:** 04.

**Objetivo:** Acceso recuperable sin revelar información de cuentas.

**Precondiciones:** empresa identificada y activa; permisos vigentes para operaciones privadas; referencias pertenecientes a la misma empresa. Para registro offline, snapshot y sesión previamente habilitados.

**Disparador:** el actor solicita recuperar contraseña.

**Datos:** empresa, correo, token, contraseña nueva.

**Flujo principal**

1. Solicitar recuperación.
2. Emitir respuesta uniforme.
3. Entregar enlace temporal por correo.
4. Validar token de un solo uso.
5. Actualizar hash e invalidar token.

**Flujos alternativos**

- Token vencido o reutilizado: rechazar.
- Cuenta inexistente: misma respuesta.
- Sin red: solicitar conexión.

**Postcondición:** Acceso recuperable sin revelar información de cuentas.

**Aceptación:** ejecutar el flujo con datos de la empresa A, comprobar el resultado y repetir una petición con referencias de B para verificar la restricción cuando corresponda. Ejecutar cada alternativa y conservar el resultado real; no basta una captura de la pantalla inicial.

**Prototipo:** `prototipos/CU-02.svg`. **Diagrama:** `diagramas/casos_uso/CU-02.puml`.

## CU-03 Administrar empresas

**Actor:** Superadministrador. **Plataforma:** Web. **Antecedente P1:** nuevo.

**Objetivo:** Empresa y administrador creados atómicamente.

**Precondiciones:** empresa identificada y activa; permisos vigentes para operaciones privadas; referencias pertenecientes a la misma empresa. Para registro offline, snapshot y sesión previamente habilitados.

**Disparador:** el actor solicita administrar empresas.

**Datos:** nombre, identificador público, administrador.

**Flujo principal**

1. Validar identidad de plataforma.
2. Registrar empresa.
3. Crear administrador inicial.
4. Asignar plan inicial.
5. Consultar o modificar estado.

**Flujos alternativos**

- Identificador repetido: rechazar.
- Usuario de empresa: acceso denegado.
- Error de alta: revertir toda la operación.

**Postcondición:** Empresa y administrador creados atómicamente.

**Aceptación:** ejecutar el flujo con datos de la empresa A, comprobar el resultado y repetir una petición con referencias de B para verificar la restricción cuando corresponda. Ejecutar cada alternativa y conservar el resultado real; no basta una captura de la pantalla inicial.

**Prototipo:** `prototipos/CU-03.svg`. **Diagrama:** `diagramas/casos_uso/CU-03.puml`.

## CU-04 Configurar planes

**Actor:** Superadministrador. **Plataforma:** Web. **Antecedente P1:** nuevo.

**Objetivo:** Límites centralizados y configurables.

**Precondiciones:** empresa identificada y activa; permisos vigentes para operaciones privadas; referencias pertenecientes a la misma empresa. Para registro offline, snapshot y sesión previamente habilitados.

**Disparador:** el actor solicita configurar planes.

**Datos:** nombre, máximo sucursales, reportes IA.

**Flujo principal**

1. Consultar planes.
2. Editar límites y capacidades.
3. Validar valores positivos.
4. Guardar configuración.
5. Registrar auditoría.

**Flujos alternativos**

- Límite inválido: rechazar.
- Empresa intenta editar: denegar.
- Reducción incompatible: informar empresas afectadas.

**Postcondición:** Límites centralizados y configurables.

**Aceptación:** ejecutar el flujo con datos de la empresa A, comprobar el resultado y repetir una petición con referencias de B para verificar la restricción cuando corresponda. Ejecutar cada alternativa y conservar el resultado real; no basta una captura de la pantalla inicial.

**Prototipo:** `prototipos/CU-04.svg`. **Diagrama:** `diagramas/casos_uso/CU-04.puml`.

## CU-05 Gestionar suscripciones

**Actor:** Superadministrador y administrador de empresa. **Plataforma:** Web. **Antecedente P1:** nuevo.

**Objetivo:** Vigencia y capacidades aplicadas en backend.

**Precondiciones:** empresa identificada y activa; permisos vigentes para operaciones privadas; referencias pertenecientes a la misma empresa. Para registro offline, snapshot y sesión previamente habilitados.

**Disparador:** el actor solicita gestionar suscripciones.

**Datos:** empresa, plan, inicio, vencimiento.

**Flujo principal**

1. Consultar suscripción.
2. Asignar o renovar administrativamente.
3. Validar fechas.
4. Comprobar cupo al cambiar plan.
5. Actualizar capacidades efectivas.

**Flujos alternativos**

- Vencida: permitir historial y renovación.
- Downgrade con exceso: rechazar.
- Empresa ajena: denegar.

**Postcondición:** Vigencia y capacidades aplicadas en backend.

**Aceptación:** ejecutar el flujo con datos de la empresa A, comprobar el resultado y repetir una petición con referencias de B para verificar la restricción cuando corresponda. Ejecutar cada alternativa y conservar el resultado real; no basta una captura de la pantalla inicial.

**Prototipo:** `prototipos/CU-05.svg`. **Diagrama:** `diagramas/casos_uso/CU-05.puml`.

## CU-06 Gestionar roles y permisos

**Actor:** Administrador de empresa. **Plataforma:** Web. **Antecedente P1:** 03.

**Objetivo:** Roles propios sin escalamiento a plataforma.

**Precondiciones:** empresa identificada y activa; permisos vigentes para operaciones privadas; referencias pertenecientes a la misma empresa. Para registro offline, snapshot y sesión previamente habilitados.

**Disparador:** el actor solicita gestionar roles y permisos.

**Datos:** rol, descripción, permisos.

**Flujo principal**

1. Consultar roles propios.
2. Crear o editar rol.
3. Seleccionar permisos permitidos.
4. Guardar matriz.
5. Verificar acceso con usuario afectado.

**Flujos alternativos**

- Permiso de plataforma: rechazar.
- Rol ajeno: no encontrado.
- Sin permiso de administrar: denegar.

**Postcondición:** Roles propios sin escalamiento a plataforma.

**Aceptación:** ejecutar el flujo con datos de la empresa A, comprobar el resultado y repetir una petición con referencias de B para verificar la restricción cuando corresponda. Ejecutar cada alternativa y conservar el resultado real; no basta una captura de la pantalla inicial.

**Prototipo:** `prototipos/CU-06.svg`. **Diagrama:** `diagramas/casos_uso/CU-06.puml`.

## CU-07 Administrar usuarios

**Actor:** Administrador de empresa. **Plataforma:** Web. **Antecedente P1:** 02.

**Objetivo:** Personal y autorizaciones actualizados.

**Precondiciones:** empresa identificada y activa; permisos vigentes para operaciones privadas; referencias pertenecientes a la misma empresa. Para registro offline, snapshot y sesión previamente habilitados.

**Disparador:** el actor solicita administrar usuarios.

**Datos:** nombre, correo, rol, sucursales, estado.

**Flujo principal**

1. Consultar personal.
2. Registrar usuario.
3. Asignar rol propio.
4. Asignar sucursales propias.
5. Activar o suspender cuenta.

**Flujos alternativos**

- Correo repetido en empresa: rechazar.
- Rol o sucursal ajena: rechazar.
- Cuenta revocada: impedir futuras operaciones.

**Postcondición:** Personal y autorizaciones actualizados.

**Aceptación:** ejecutar el flujo con datos de la empresa A, comprobar el resultado y repetir una petición con referencias de B para verificar la restricción cuando corresponda. Ejecutar cada alternativa y conservar el resultado real; no basta una captura de la pantalla inicial.

**Prototipo:** `prototipos/CU-07.svg`. **Diagrama:** `diagramas/casos_uso/CU-07.puml`.

## CU-08 Gestionar ciudades y sucursales

**Actor:** Administrador de empresa. **Plataforma:** Web. **Antecedente P1:** 06.

**Objetivo:** Sucursal propia dentro del límite contratado.

**Precondiciones:** empresa identificada y activa; permisos vigentes para operaciones privadas; referencias pertenecientes a la misma empresa. Para registro offline, snapshot y sesión previamente habilitados.

**Disparador:** el actor solicita gestionar ciudades y sucursales.

**Datos:** nombre, dirección, ciudad, encargado, estado.

**Flujo principal**

1. Consultar sucursales.
2. Preparar alta o reactivación.
3. Bloquear empresa para comprobar cupo.
4. Guardar sucursal y encargado.
5. Actualizar listado.

**Flujos alternativos**

- Cupo agotado: rechazar.
- Encargado ajeno: rechazar.
- Altas concurrentes: no exceder límite.

**Postcondición:** Sucursal propia dentro del límite contratado.

**Aceptación:** ejecutar el flujo con datos de la empresa A, comprobar el resultado y repetir una petición con referencias de B para verificar la restricción cuando corresponda. Ejecutar cada alternativa y conservar el resultado real; no basta una captura de la pantalla inicial.

**Prototipo:** `prototipos/CU-08.svg`. **Diagrama:** `diagramas/casos_uso/CU-08.puml`.

## CU-09 Gestionar clientes

**Actor:** Administrador y cajero. **Plataforma:** Web. **Antecedente P1:** 05.

**Objetivo:** Fichas comerciales aisladas.

**Precondiciones:** empresa identificada y activa; permisos vigentes para operaciones privadas; referencias pertenecientes a la misma empresa. Para registro offline, snapshot y sesión previamente habilitados.

**Disparador:** el actor solicita gestionar clientes.

**Datos:** identificación, nombre, contacto.

**Flujo principal**

1. Buscar ficha propia.
2. Validar identificación.
3. Crear o actualizar contacto.
4. Comprobar permisos.
5. Auditar modificación.

**Flujos alternativos**

- Identificación duplicada en empresa: rechazar.
- Cliente de otra empresa: no encontrado.
- Cliente autenticado: limitar a su ficha.

**Postcondición:** Fichas comerciales aisladas.

**Aceptación:** ejecutar el flujo con datos de la empresa A, comprobar el resultado y repetir una petición con referencias de B para verificar la restricción cuando corresponda. Ejecutar cada alternativa y conservar el resultado real; no basta una captura de la pantalla inicial.

**Prototipo:** `prototipos/CU-09.svg`. **Diagrama:** `diagramas/casos_uso/CU-09.puml`.

## CU-10 Gestionar categorías

**Actor:** Administrador de empresa. **Plataforma:** Web. **Antecedente P1:** 07.

**Objetivo:** Categorías propias utilizables por catálogo.

**Precondiciones:** empresa identificada y activa; permisos vigentes para operaciones privadas; referencias pertenecientes a la misma empresa. Para registro offline, snapshot y sesión previamente habilitados.

**Disparador:** el actor solicita gestionar categorías.

**Datos:** nombre, descripción, categoría padre.

**Flujo principal**

1. Consultar categorías.
2. Crear o editar.
3. Validar padre propio.
4. Comprobar ausencia de ciclos.
5. Guardar estado.

**Flujos alternativos**

- Padre ajeno o ciclo: rechazar.
- Sin permiso: denegar.
- Categoría usada: mantener integridad.

**Postcondición:** Categorías propias utilizables por catálogo.

**Aceptación:** ejecutar el flujo con datos de la empresa A, comprobar el resultado y repetir una petición con referencias de B para verificar la restricción cuando corresponda. Ejecutar cada alternativa y conservar el resultado real; no basta una captura de la pantalla inicial.

**Prototipo:** `prototipos/CU-10.svg`. **Diagrama:** `diagramas/casos_uso/CU-10.puml`.

## CU-11 Gestionar temporadas y colecciones

**Actor:** Administrador de empresa. **Plataforma:** Web. **Antecedente P1:** 09.

**Objetivo:** Períodos comerciales definidos.

**Precondiciones:** empresa identificada y activa; permisos vigentes para operaciones privadas; referencias pertenecientes a la misma empresa. Para registro offline, snapshot y sesión previamente habilitados.

**Disparador:** el actor solicita gestionar temporadas y colecciones.

**Datos:** nombre, descripción, inicio, fin.

**Flujo principal**

1. Consultar temporadas.
2. Crear o editar período.
3. Validar orden de fechas.
4. Relacionar prendas propias.
5. Guardar configuración.

**Flujos alternativos**

- Fin anterior a inicio: rechazar.
- Temporada ajena: no encontrado.
- Sin permiso: denegar.

**Postcondición:** Períodos comerciales definidos.

**Aceptación:** ejecutar el flujo con datos de la empresa A, comprobar el resultado y repetir una petición con referencias de B para verificar la restricción cuando corresponda. Ejecutar cada alternativa y conservar el resultado real; no basta una captura de la pantalla inicial.

**Prototipo:** `prototipos/CU-11.svg`. **Diagrama:** `diagramas/casos_uso/CU-11.puml`.

## CU-12 Gestionar prendas y variantes

**Actor:** Administrador y responsable de inventario. **Plataforma:** Web. **Antecedente P1:** 08.

**Objetivo:** Catálogo consistente con variantes y precio calculable.

**Precondiciones:** empresa identificada y activa; permisos vigentes para operaciones privadas; referencias pertenecientes a la misma empresa. Para registro offline, snapshot y sesión previamente habilitados.

**Disparador:** el actor solicita gestionar prendas y variantes.

**Datos:** SKU, categoría, temporada, material, medidas, tallas, colores, precios.

**Flujo principal**

1. Crear ficha de prenda.
2. Definir variantes y combinaciones de colores.
3. Asignar precios minoristas y mayoristas.
4. Configurar oferta vigente.
5. Publicar ficha.

**Flujos alternativos**

- SKU repetido en empresa: rechazar.
- Precio negativo o referencia ajena: rechazar.
- Descuento vencido: no aplicar.

**Postcondición:** Catálogo consistente con variantes y precio calculable.

**Aceptación:** ejecutar el flujo con datos de la empresa A, comprobar el resultado y repetir una petición con referencias de B para verificar la restricción cuando corresponda. Ejecutar cada alternativa y conservar el resultado real; no basta una captura de la pantalla inicial.

**Prototipo:** `prototipos/CU-12.svg`. **Diagrama:** `diagramas/casos_uso/CU-12.puml`.

## CU-13 Gestionar proveedores

**Actor:** Responsable de inventario. **Plataforma:** Web y Flutter. **Antecedente P1:** 12.

**Objetivo:** Proveedores disponibles para compras propias.

**Precondiciones:** empresa identificada y activa; permisos vigentes para operaciones privadas; referencias pertenecientes a la misma empresa. Para registro offline, snapshot y sesión previamente habilitados.

**Disparador:** el actor solicita gestionar proveedores.

**Datos:** NIT, razón social, contacto.

**Flujo principal**

1. Buscar proveedor.
2. Registrar o editar ficha.
3. Validar identificación propia.
4. Guardar contacto.
5. Auditar cambio.

**Flujos alternativos**

- NIT repetido en empresa: rechazar.
- Sin rol autorizado: denegar.
- Proveedor ajeno: no encontrado.

**Postcondición:** Proveedores disponibles para compras propias.

**Aceptación:** ejecutar el flujo con datos de la empresa A, comprobar el resultado y repetir una petición con referencias de B para verificar la restricción cuando corresponda. Ejecutar cada alternativa y conservar el resultado real; no basta una captura de la pantalla inicial.

**Prototipo:** `prototipos/CU-13.svg`. **Diagrama:** `diagramas/casos_uso/CU-13.puml`.

## CU-14 Registrar compras y recepciones

**Actor:** Responsable de inventario. **Plataforma:** Web y Flutter. **Antecedente P1:** 13.

**Objetivo:** Compra y existencia física consistentes.

**Precondiciones:** empresa identificada y activa; permisos vigentes para operaciones privadas; referencias pertenecientes a la misma empresa. Para registro offline, snapshot y sesión previamente habilitados.

**Disparador:** el actor solicita registrar compras y recepciones.

**Datos:** proveedor, sucursal, variantes, cantidades, costos.

**Flujo principal**

1. Seleccionar proveedor y destino.
2. Registrar detalles.
3. Validar cantidades y costos.
4. Confirmar recepción.
5. Crear entradas de inventario y auditoría en una transacción.

**Flujos alternativos**

- Referencia ajena: rechazar.
- Fallo de detalle: revertir recepción.
- Reenvío confirmado: no duplicar recepción.

**Postcondición:** Compra y existencia física consistentes.

**Aceptación:** ejecutar el flujo con datos de la empresa A, comprobar el resultado y repetir una petición con referencias de B para verificar la restricción cuando corresponda. Ejecutar cada alternativa y conservar el resultado real; no basta una captura de la pantalla inicial.

**Prototipo:** `prototipos/CU-14.svg`. **Diagrama:** `diagramas/casos_uso/CU-14.puml`.

## CU-15 Consultar inventario

**Actor:** Encargado y responsable de inventario. **Plataforma:** Web y Flutter. **Antecedente P1:** 10.

**Objetivo:** Existencias interpretables sin prometer actualización offline.

**Precondiciones:** empresa identificada y activa; permisos vigentes para operaciones privadas; referencias pertenecientes a la misma empresa. Para registro offline, snapshot y sesión previamente habilitados.

**Disparador:** el actor solicita consultar inventario.

**Datos:** sucursal, producto, variante.

**Flujo principal**

1. Seleccionar sucursal autorizada.
2. Consultar existencia física.
3. Calcular retenciones vigentes.
4. Mostrar disponible.
5. Indicar actualización de datos.

**Flujos alternativos**

- Sucursal no autorizada: denegar.
- Sin datos: mostrar vacío.
- Sin red: mostrar copia conocida y fecha.

**Postcondición:** Existencias interpretables sin prometer actualización offline.

**Aceptación:** ejecutar el flujo con datos de la empresa A, comprobar el resultado y repetir una petición con referencias de B para verificar la restricción cuando corresponda. Ejecutar cada alternativa y conservar el resultado real; no basta una captura de la pantalla inicial.

**Prototipo:** `prototipos/CU-15.svg`. **Diagrama:** `diagramas/casos_uso/CU-15.puml`.

## CU-16 Registrar movimientos de inventario

**Actor:** Responsable de inventario. **Plataforma:** Web y Flutter. **Antecedente P1:** 11.

**Objetivo:** Movimiento y saldo físico concordantes.

**Precondiciones:** empresa identificada y activa; permisos vigentes para operaciones privadas; referencias pertenecientes a la misma empresa. Para registro offline, snapshot y sesión previamente habilitados.

**Disparador:** el actor solicita registrar movimientos de inventario.

**Datos:** origen, destino, variante, cantidad, motivo.

**Flujo principal**

1. Seleccionar operación.
2. Validar sucursales y variante.
3. Bloquear existencia afectada.
4. Registrar movimiento único.
5. Confirmar transacción.

**Flujos alternativos**

- Cantidad no positiva: rechazar.
- Stock insuficiente: revertir.
- Fallo en transferencia: revertir ambos lados.

**Postcondición:** Movimiento y saldo físico concordantes.

**Aceptación:** ejecutar el flujo con datos de la empresa A, comprobar el resultado y repetir una petición con referencias de B para verificar la restricción cuando corresponda. Ejecutar cada alternativa y conservar el resultado real; no basta una captura de la pantalla inicial.

**Prototipo:** `prototipos/CU-16.svg`. **Diagrama:** `diagramas/casos_uso/CU-16.puml`.

## CU-17 Consultar catálogo

**Actor:** Cliente y visitante. **Plataforma:** Web y Flutter. **Antecedente P1:** 14.

**Objetivo:** Catálogo público limitado a una empresa.

**Precondiciones:** empresa identificada y activa; permisos vigentes para operaciones privadas; referencias pertenecientes a la misma empresa. Para registro offline, snapshot y sesión previamente habilitados.

**Disparador:** el actor solicita consultar catálogo.

**Datos:** empresa pública, categoría, talla, colores, temporada.

**Flujo principal**

1. Resolver empresa pública.
2. Consultar prendas activas.
3. Aplicar filtros.
4. Mostrar variantes y precio aplicable.
5. Consultar disponibilidad.

**Flujos alternativos**

- Empresa inexistente: no encontrado.
- Sin coincidencias: resultado vacío.
- Sin red: usar catálogo descargado.

**Postcondición:** Catálogo público limitado a una empresa.

**Aceptación:** ejecutar el flujo con datos de la empresa A, comprobar el resultado y repetir una petición con referencias de B para verificar la restricción cuando corresponda. Ejecutar cada alternativa y conservar el resultado real; no basta una captura de la pantalla inicial.

**Prototipo:** `prototipos/CU-17.svg`. **Diagrama:** `diagramas/casos_uso/CU-17.puml`.

## CU-18 Gestionar carrito y checkout

**Actor:** Cliente. **Plataforma:** Web y Flutter. **Antecedente P1:** 15.

**Objetivo:** Pedido coherente pendiente de confirmación de pago.

**Precondiciones:** empresa identificada y activa; permisos vigentes para operaciones privadas; referencias pertenecientes a la misma empresa. Para registro offline, snapshot y sesión previamente habilitados.

**Disparador:** el actor solicita gestionar carrito y checkout.

**Datos:** variantes, cantidades, sucursal, entrega.

**Flujo principal**

1. Agregar variantes.
2. Modificar cantidades.
3. Recalcular precios en servidor.
4. Seleccionar entrega.
5. Iniciar checkout sin consolidar venta.

**Flujos alternativos**

- Stock cambiado: informar.
- Precio alterado: recalcular y confirmar.
- Pago pendiente: no confirmar venta.

**Postcondición:** Pedido coherente pendiente de confirmación de pago.

**Aceptación:** ejecutar el flujo con datos de la empresa A, comprobar el resultado y repetir una petición con referencias de B para verificar la restricción cuando corresponda. Ejecutar cada alternativa y conservar el resultado real; no basta una captura de la pantalla inicial.

**Prototipo:** `prototipos/CU-18.svg`. **Diagrama:** `diagramas/casos_uso/CU-18.puml`.

## CU-19 Registrar reservas online

**Actor:** Cliente y personal autorizado. **Plataforma:** Web y Flutter. **Antecedente P1:** 16.

**Objetivo:** Reserva central aceptada con vencimiento explícito.

**Precondiciones:** empresa identificada y activa; permisos vigentes para operaciones privadas; referencias pertenecientes a la misma empresa. Para registro offline, snapshot y sesión previamente habilitados.

**Disparador:** el actor solicita registrar reservas online.

**Datos:** cliente, sucursal, variantes, cantidades.

**Flujo principal**

1. Seleccionar prendas.
2. Validar cliente y sucursal.
3. Bloquear existencias.
4. Crear reserva con retención de 24 horas.
5. Mostrar comprobante de reserva.

**Flujos alternativos**

- Disponible insuficiente: rechazar.
- Referencia ajena: rechazar.
- Reserva vencida: liberar retención.

**Postcondición:** Reserva central aceptada con vencimiento explícito.

**Aceptación:** ejecutar el flujo con datos de la empresa A, comprobar el resultado y repetir una petición con referencias de B para verificar la restricción cuando corresponda. Ejecutar cada alternativa y conservar el resultado real; no basta una captura de la pantalla inicial.

**Prototipo:** `prototipos/CU-19.svg`. **Diagrama:** `diagramas/casos_uso/CU-19.puml`.

## CU-20 Preparar entregar o cancelar reservas

**Actor:** Encargado. **Plataforma:** Web y Flutter. **Antecedente P1:** 17.

**Objetivo:** Estados comerciales separados y trazables.

**Precondiciones:** empresa identificada y activa; permisos vigentes para operaciones privadas; referencias pertenecientes a la misma empresa. Para registro offline, snapshot y sesión previamente habilitados.

**Disparador:** el actor solicita preparar entregar o cancelar reservas.

**Datos:** reserva, acción, observación.

**Flujo principal**

1. Consultar reserva propia.
2. Validar transición.
3. Preparar prendas.
4. Confirmar pago cuando corresponda.
5. Entregar o cancelar liberando retención.

**Flujos alternativos**

- Preparar no cobra: mantener pendiente de pago.
- Ya atendida: no duplicar venta.
- Vencida: cancelar y liberar.

**Postcondición:** Estados comerciales separados y trazables.

**Aceptación:** ejecutar el flujo con datos de la empresa A, comprobar el resultado y repetir una petición con referencias de B para verificar la restricción cuando corresponda. Ejecutar cada alternativa y conservar el resultado real; no basta una captura de la pantalla inicial.

**Prototipo:** `prototipos/CU-20.svg`. **Diagrama:** `diagramas/casos_uso/CU-20.puml`.

## CU-21 Registrar venta presencial

**Actor:** Cajero. **Plataforma:** Web y Flutter. **Antecedente P1:** 19.

**Objetivo:** Una venta de contado con un descuento de inventario.

**Precondiciones:** empresa identificada y activa; permisos vigentes para operaciones privadas; referencias pertenecientes a la misma empresa. Para registro offline, snapshot y sesión previamente habilitados.

**Disparador:** el actor solicita registrar venta presencial.

**Datos:** sucursal, cliente opcional, variantes, efectivo.

**Flujo principal**

1. Seleccionar sucursal autorizada.
2. Agregar productos.
3. Calcular precios.
4. Registrar efectivo.
5. Confirmar venta y movimientos atómicamente.

**Flujos alternativos**

- Stock insuficiente: rechazar.
- Precio manipulado: rechazar.
- Fallo intermedio: revertir toda la venta.

**Postcondición:** Una venta de contado con un descuento de inventario.

**Aceptación:** ejecutar el flujo con datos de la empresa A, comprobar el resultado y repetir una petición con referencias de B para verificar la restricción cuando corresponda. Ejecutar cada alternativa y conservar el resultado real; no basta una captura de la pantalla inicial.

**Prototipo:** `prototipos/CU-21.svg`. **Diagrama:** `diagramas/casos_uso/CU-21.puml`.

## CU-22 Procesar pagos electrónicos

**Actor:** Cliente y pasarela. **Plataforma:** Web y Flutter. **Antecedente P1:** 20.

**Objetivo:** Pago comprobado sin doble confirmación.

**Precondiciones:** empresa identificada y activa; permisos vigentes para operaciones privadas; referencias pertenecientes a la misma empresa. Para registro offline, snapshot y sesión previamente habilitados.

**Disparador:** el actor solicita procesar pagos electrónicos.

**Datos:** pedido, monto calculado, evento firmado.

**Flujo principal**

1. Crear sesión sandbox.
2. Redirigir a pasarela.
3. Recibir evento firmado.
4. Verificar importe y pedido.
5. Confirmar una sola vez.

**Flujos alternativos**

- Firma inválida: rechazar.
- Rechazo o expiración: conservar estado fallido.
- Evento repetido: misma confirmación.

**Postcondición:** Pago comprobado sin doble confirmación.

**Aceptación:** ejecutar el flujo con datos de la empresa A, comprobar el resultado y repetir una petición con referencias de B para verificar la restricción cuando corresponda. Ejecutar cada alternativa y conservar el resultado real; no basta una captura de la pantalla inicial.

**Prototipo:** `prototipos/CU-22.svg`. **Diagrama:** `diagramas/casos_uso/CU-22.puml`.

## CU-23 Emitir y consultar comprobantes

**Actor:** Cliente y cajero. **Plataforma:** Web y Flutter. **Antecedente P1:** 21.

**Objetivo:** Documento coherente y protegido.

**Precondiciones:** empresa identificada y activa; permisos vigentes para operaciones privadas; referencias pertenecientes a la misma empresa. Para registro offline, snapshot y sesión previamente habilitados.

**Disparador:** el actor solicita emitir y consultar comprobantes.

**Datos:** venta, identificación fiscal.

**Flujo principal**

1. Seleccionar venta confirmada.
2. Validar propiedad y empresa.
3. Generar documento.
4. Guardar referencia protegida.
5. Descargar con autorización.

**Flujos alternativos**

- Venta ajena: no encontrado.
- Pago no confirmado: impedir comprobante definitivo.
- Ruta privada directa: denegar.

**Postcondición:** Documento coherente y protegido.

**Aceptación:** ejecutar el flujo con datos de la empresa A, comprobar el resultado y repetir una petición con referencias de B para verificar la restricción cuando corresponda. Ejecutar cada alternativa y conservar el resultado real; no basta una captura de la pantalla inicial.

**Prototipo:** `prototipos/CU-23.svg`. **Diagrama:** `diagramas/casos_uso/CU-23.puml`.

## CU-24 Solicitar y consultar cambios

**Actor:** Cliente. **Plataforma:** Web y Flutter. **Antecedente P1:** nuevo.

**Objetivo:** Solicitud trazable sin modificar stock antes de recepción.

**Precondiciones:** empresa identificada y activa; permisos vigentes para operaciones privadas; referencias pertenecientes a la misma empresa. Para registro offline, snapshot y sesión previamente habilitados.

**Disparador:** el actor solicita solicitar y consultar cambios.

**Datos:** venta, variante, unidades, motivo.

**Flujo principal**

1. Consultar compra propia.
2. Comprobar siete días y unidades.
3. Registrar solicitud.
4. Mostrar condiciones.
5. Consultar avance y notificaciones.

**Flujos alternativos**

- Fuera de plazo: rechazar.
- Unidad cambiada: rechazar.
- Prenda no elegible: informar.

**Postcondición:** Solicitud trazable sin modificar stock antes de recepción.

**Aceptación:** ejecutar el flujo con datos de la empresa A, comprobar el resultado y repetir una petición con referencias de B para verificar la restricción cuando corresponda. Ejecutar cada alternativa y conservar el resultado real; no basta una captura de la pantalla inicial.

**Prototipo:** `prototipos/CU-24.svg`. **Diagrama:** `diagramas/casos_uso/CU-24.puml`.

## CU-25 Atender cambios y reembolsos

**Actor:** Encargado y cajero. **Plataforma:** Web. **Antecedente P1:** nuevo.

**Objetivo:** Recepción y entrega separadas con crédito y pagos trazables.

**Precondiciones:** empresa identificada y activa; permisos vigentes para operaciones privadas; referencias pertenecientes a la misma empresa. Para registro offline, snapshot y sesión previamente habilitados.

**Disparador:** el actor solicita atender cambios y reembolsos.

**Datos:** solicitud, recepción, reemplazo, diferencia.

**Flujo principal**

1. Inspeccionar prenda.
2. Registrar recepción aceptada y entrada.
3. Seleccionar reemplazo.
4. Cobrar o devolver diferencia y notificar.
5. Entregar cuando corresponda y registrar salida.

**Flujos alternativos**

- Sin reemplazo: esperar o reembolsar.
- Sobreprecio rechazado: cancelar reemplazo.
- Notificación fallida: conservar bandeja.

**Postcondición:** Recepción y entrega separadas con crédito y pagos trazables.

**Aceptación:** ejecutar el flujo con datos de la empresa A, comprobar el resultado y repetir una petición con referencias de B para verificar la restricción cuando corresponda. Ejecutar cada alternativa y conservar el resultado real; no basta una captura de la pantalla inicial.

**Prototipo:** `prototipos/CU-25.svg`. **Diagrama:** `diagramas/casos_uso/CU-25.puml`.

## CU-26 Utilizar vestidor existente

**Actor:** Cliente. **Plataforma:** Web y Flutter. **Antecedente P1:** 18.

**Objetivo:** Capacidad previa conservada y tecnología descrita fielmente.

**Precondiciones:** empresa identificada y activa; permisos vigentes para operaciones privadas; referencias pertenecientes a la misma empresa. Para registro offline, snapshot y sesión previamente habilitados.

**Disparador:** el actor solicita utilizar vestidor existente.

**Datos:** prenda, imagen o cámara autorizada.

**Flujo principal**

1. Seleccionar prenda propia del catálogo.
2. Solicitar permiso de cámara.
3. Abrir integración existente.
4. Procesar visualización.
5. Cerrar y liberar cámara.

**Flujos alternativos**

- Permiso rechazado: informar.
- Proveedor caído: error controlado.
- Sin red: función no disponible.

**Postcondición:** Capacidad previa conservada y tecnología descrita fielmente.

**Aceptación:** ejecutar el flujo con datos de la empresa A, comprobar el resultado y repetir una petición con referencias de B para verificar la restricción cuando corresponda. Ejecutar cada alternativa y conservar el resultado real; no basta una captura de la pantalla inicial.

**Prototipo:** `prototipos/CU-26.svg`. **Diagrama:** `diagramas/casos_uso/CU-26.puml`.

## CU-27 Consultar recomendaciones

**Actor:** Cliente. **Plataforma:** Web y Flutter. **Antecedente P1:** 22.

**Objetivo:** Recomendaciones limitadas a datos autorizados.

**Precondiciones:** empresa identificada y activa; permisos vigentes para operaciones privadas; referencias pertenecientes a la misma empresa. Para registro offline, snapshot y sesión previamente habilitados.

**Disparador:** el actor solicita consultar recomendaciones.

**Datos:** preferencias, talla, catálogo propio.

**Flujo principal**

1. Recibir preferencias.
2. Consultar catálogo autorizado.
3. Solicitar recomendación.
4. Validar productos y disponibilidad.
5. Presentar resultados.

**Flujos alternativos**

- Proveedor caído: informar o respaldo declarado.
- Producto inexistente: excluir.
- Tenant ajeno: impedir consulta.

**Postcondición:** Recomendaciones limitadas a datos autorizados.

**Aceptación:** ejecutar el flujo con datos de la empresa A, comprobar el resultado y repetir una petición con referencias de B para verificar la restricción cuando corresponda. Ejecutar cada alternativa y conservar el resultado real; no basta una captura de la pantalla inicial.

**Prototipo:** `prototipos/CU-27.svg`. **Diagrama:** `diagramas/casos_uso/CU-27.puml`.

## CU-28 Preparar y consultar catálogo offline

**Actor:** Personal y cliente. **Plataforma:** Web y Flutter. **Antecedente P1:** nuevo.

**Objetivo:** PWA y SQLite consultables después de reiniciar.

**Precondiciones:** empresa identificada y activa; permisos vigentes para operaciones privadas; referencias pertenecientes a la misma empresa. Para registro offline, snapshot y sesión previamente habilitados.

**Disparador:** el actor solicita preparar y consultar catálogo offline.

**Datos:** sucursal, productos, última actualización.

**Flujo principal**

1. Autenticar con red.
2. Descargar catálogo acotado.
3. Guardar snapshot completo.
4. Consultar sin conexión.
5. Mostrar antigüedad de información.

**Flujos alternativos**

- Descarga interrumpida: conservar snapshot previo.
- Sin espacio: informar sin borrar pendientes.
- Cuenta distinta: no mostrar datos anteriores.

**Postcondición:** PWA y SQLite consultables después de reiniciar.

**Aceptación:** ejecutar el flujo con datos de la empresa A, comprobar el resultado y repetir una petición con referencias de B para verificar la restricción cuando corresponda. Ejecutar cada alternativa y conservar el resultado real; no basta una captura de la pantalla inicial.

**Prototipo:** `prototipos/CU-28.svg`. **Diagrama:** `diagramas/casos_uso/CU-28.puml`.

## CU-29 Registrar reserva offline

**Actor:** Cliente y personal autorizado. **Plataforma:** Web y Flutter. **Antecedente P1:** nuevo.

**Objetivo:** Reserva local durable sin promesa de confirmación central.

**Precondiciones:** empresa identificada y activa; permisos vigentes para operaciones privadas; referencias pertenecientes a la misma empresa. Para registro offline, snapshot y sesión previamente habilitados.

**Disparador:** el actor solicita registrar reserva offline.

**Datos:** UUID, cliente conocido, sucursal, detalles.

**Flujo principal**

1. Validar sesión offline.
2. Seleccionar variantes locales.
3. Crear UUID único.
4. Guardar cabecera detalles y pendiente en una transacción.
5. Mostrar reserva provisional.

**Flujos alternativos**

- Sesión offline vencida: bloquear registro.
- Fallo local: revertir.
- Sin stock local conocido: advertir o impedir cantidad inválida.

**Postcondición:** Reserva local durable sin promesa de confirmación central.

**Aceptación:** ejecutar el flujo con datos de la empresa A, comprobar el resultado y repetir una petición con referencias de B para verificar la restricción cuando corresponda. Ejecutar cada alternativa y conservar el resultado real; no basta una captura de la pantalla inicial.

**Prototipo:** `prototipos/CU-29.svg`. **Diagrama:** `diagramas/casos_uso/CU-29.puml`.

## CU-30 Registrar venta de contado offline

**Actor:** Cajero. **Plataforma:** Web y Flutter. **Antecedente P1:** nuevo.

**Objetivo:** Venta provisional recuperable tras cierre.

**Precondiciones:** empresa identificada y activa; permisos vigentes para operaciones privadas; referencias pertenecientes a la misma empresa. Para registro offline, snapshot y sesión previamente habilitados.

**Disparador:** el actor solicita registrar venta de contado offline.

**Datos:** UUID, responsable, sucursal, detalles, efectivo.

**Flujo principal**

1. Validar permiso offline.
2. Preparar venta con precios conocidos.
3. Registrar efectivo recibido.
4. Guardar venta detalles y outbox.
5. Emitir constancia provisional.

**Flujos alternativos**

- Sin permiso: impedir venta.
- Fallo local: no declarar registro exitoso.
- Conflicto posterior: conservar efectivo y exigir resolución.

**Postcondición:** Venta provisional recuperable tras cierre.

**Aceptación:** ejecutar el flujo con datos de la empresa A, comprobar el resultado y repetir una petición con referencias de B para verificar la restricción cuando corresponda. Ejecutar cada alternativa y conservar el resultado real; no basta una captura de la pantalla inicial.

**Prototipo:** `prototipos/CU-30.svg`. **Diagrama:** `diagramas/casos_uso/CU-30.puml`.

## CU-31 Consultar operaciones locales

**Actor:** Autor y encargado autorizado. **Plataforma:** Web y Flutter. **Antecedente P1:** nuevo.

**Objetivo:** Usuario conoce el estado real de cada operación.

**Precondiciones:** empresa identificada y activa; permisos vigentes para operaciones privadas; referencias pertenecientes a la misma empresa. Para registro offline, snapshot y sesión previamente habilitados.

**Disparador:** el actor solicita consultar operaciones locales.

**Datos:** estado, tipo, UUID.

**Flujo principal**

1. Abrir almacenamiento de sesión.
2. Listar operaciones.
3. Consultar detalles.
4. Mostrar último intento y resultado.
5. Mantener confirmaciones y pendientes.

**Flujos alternativos**

- Otra cuenta: ocultar datos.
- Almacenamiento inaccesible: informar.
- Enviando tras reinicio: recuperar a pendiente.

**Postcondición:** Usuario conoce el estado real de cada operación.

**Aceptación:** ejecutar el flujo con datos de la empresa A, comprobar el resultado y repetir una petición con referencias de B para verificar la restricción cuando corresponda. Ejecutar cada alternativa y conservar el resultado real; no basta una captura de la pantalla inicial.

**Prototipo:** `prototipos/CU-31.svg`. **Diagrama:** `diagramas/casos_uso/CU-31.puml`.

## CU-32 Sincronizar operaciones

**Actor:** Cliente y personal autorizado. **Plataforma:** Web y Flutter. **Antecedente P1:** nuevo.

**Objetivo:** Resultado durable por operación y ausencia de duplicados.

**Precondiciones:** empresa identificada y activa; permisos vigentes para operaciones privadas; referencias pertenecientes a la misma empresa. Para registro offline, snapshot y sesión previamente habilitados.

**Disparador:** el actor solicita sincronizar operaciones.

**Datos:** lote, UUID, versión, identidad, payload.

**Flujo principal**

1. Detectar conectividad o solicitud manual.
2. Enviar lote sin cambiar UUID.
3. Validar contexto y negocio por operación.
4. Confirmar transacción idempotente.
5. Guardar resultado local.

**Flujos alternativos**

- Timeout después del commit: consultar y reenviar.
- UUID con contenido diferente: rechazar.
- 401: esperar reautenticación sin pérdida.

**Postcondición:** Resultado durable por operación y ausencia de duplicados.

**Aceptación:** ejecutar el flujo con datos de la empresa A, comprobar el resultado y repetir una petición con referencias de B para verificar la restricción cuando corresponda. Ejecutar cada alternativa y conservar el resultado real; no basta una captura de la pantalla inicial.

**Prototipo:** `prototipos/CU-32.svg`. **Diagrama:** `diagramas/casos_uso/CU-32.puml`.

## CU-33 Resolver conflictos

**Actor:** Encargado y autor autorizado. **Plataforma:** Web y Flutter. **Antecedente P1:** nuevo.

**Objetivo:** Conflicto resuelto sin sobrescribir original.

**Precondiciones:** empresa identificada y activa; permisos vigentes para operaciones privadas; referencias pertenecientes a la misma empresa. Para registro offline, snapshot y sesión previamente habilitados.

**Disparador:** el actor solicita resolver conflictos.

**Datos:** operación original, motivo, resolución.

**Flujo principal**

1. Consultar conflicto.
2. Revisar stock precio y efectivo.
3. Elegir corrección o compensación.
4. Crear revisión con nuevo UUID.
5. Conservar vínculo y auditoría.

**Flujos alternativos**

- Sin permiso o empresa ajena: denegar.
- Precio no aceptado: compensar y cancelar.
- Conflicto concurrente: repetir evaluación.

**Postcondición:** Conflicto resuelto sin sobrescribir original.

**Aceptación:** ejecutar el flujo con datos de la empresa A, comprobar el resultado y repetir una petición con referencias de B para verificar la restricción cuando corresponda. Ejecutar cada alternativa y conservar el resultado real; no basta una captura de la pantalla inicial.

**Prototipo:** `prototipos/CU-33.svg`. **Diagrama:** `diagramas/casos_uso/CU-33.puml`.

## CU-34 Consultar reportes convencionales

**Actor:** Administrador y encargado. **Plataforma:** Web. **Antecedente P1:** 23.

**Objetivo:** Datos actuales autorizados disponibles en ambos planes.

**Precondiciones:** empresa identificada y activa; permisos vigentes para operaciones privadas; referencias pertenecientes a la misma empresa. Para registro offline, snapshot y sesión previamente habilitados.

**Disparador:** el actor solicita consultar reportes convencionales.

**Datos:** tipo, fechas, sucursales, categorías, productos.

**Flujo principal**

1. Seleccionar reporte.
2. Validar filtros.
3. Ejecutar consulta parametrizada propia.
4. Mostrar tabla o gráfico.
5. Exportar mismos resultados.

**Flujos alternativos**

- Filtro ajeno: rechazar.
- Sin datos: mostrar vacío.
- Consulta excesiva: limitar alcance.

**Postcondición:** Datos actuales autorizados disponibles en ambos planes.

**Aceptación:** ejecutar el flujo con datos de la empresa A, comprobar el resultado y repetir una petición con referencias de B para verificar la restricción cuando corresponda. Ejecutar cada alternativa y conservar el resultado real; no basta una captura de la pantalla inicial.

**Prototipo:** `prototipos/CU-34.svg`. **Diagrama:** `diagramas/casos_uso/CU-34.puml`.

## CU-35 Solicitar reportes generativos

**Actor:** Usuario autorizado Profesional. **Plataforma:** Web y Flutter. **Antecedente P1:** 23.

**Objetivo:** Reporte dinámico sobre datos reales sin SQL libre.

**Precondiciones:** empresa identificada y activa; permisos vigentes para operaciones privadas; referencias pertenecientes a la misma empresa. Para registro offline, snapshot y sesión previamente habilitados.

**Disparador:** el actor solicita solicitar reportes generativos.

**Datos:** texto o transcripción, filtros, formato.

**Flujo principal**

1. Recibir texto o voz editable.
2. Interpretar intención estructurada.
3. Validar plan permisos y filtros.
4. Ejecutar consulta permitida.
5. Presentar y exportar resultado.

**Flujos alternativos**

- Ambigüedad: pedir precisión.
- Proveedor caído: informar y ofrecer convencional.
- SQL o tenant arbitrario: rechazar.

**Postcondición:** Reporte dinámico sobre datos reales sin SQL libre.

**Aceptación:** ejecutar el flujo con datos de la empresa A, comprobar el resultado y repetir una petición con referencias de B para verificar la restricción cuando corresponda. Ejecutar cada alternativa y conservar el resultado real; no basta una captura de la pantalla inicial.

**Prototipo:** `prototipos/CU-35.svg`. **Diagrama:** `diagramas/casos_uso/CU-35.puml`.

## CU-36 Preparar datos y entrenar modelos

**Actor:** Responsable técnico y administrador. **Plataforma:** Herramienta técnica y Web. **Antecedente P1:** nuevo.

**Objetivo:** Modelos evaluados y procedencia identificable.

**Precondiciones:** empresa identificada y activa; permisos vigentes para operaciones privadas; referencias pertenecientes a la misma empresa. Para registro offline, snapshot y sesión previamente habilitados.

**Disparador:** el actor solicita preparar datos y entrenar modelos.

**Datos:** semilla, dataset, variables, particiones, versión.

**Flujo principal**

1. Generar datos sintéticos reproducibles.
2. Preparar variables sin fuga.
3. Entrenar demanda y segmentación.
4. Evaluar contra referencia y registrar métricas.
5. Versionar artefactos.

**Flujos alternativos**

- Datos insuficientes: impedir entrenamiento.
- Modelo ausente: informar.
- Métrica desfavorable: conservar evidencia sin inventar precisión.

**Postcondición:** Modelos evaluados y procedencia identificable.

**Aceptación:** ejecutar el flujo con datos de la empresa A, comprobar el resultado y repetir una petición con referencias de B para verificar la restricción cuando corresponda. Ejecutar cada alternativa y conservar el resultado real; no basta una captura de la pantalla inicial.

**Prototipo:** `prototipos/CU-36.svg`. **Diagrama:** `diagramas/casos_uso/CU-36.puml`.

## CU-37 Consultar dashboard y analítica

**Actor:** Administrador y encargado. **Plataforma:** Web. **Antecedente P1:** 24.

**Objetivo:** Resultados comerciales y predictivos interpretables.

**Precondiciones:** empresa identificada y activa; permisos vigentes para operaciones privadas; referencias pertenecientes a la misma empresa. Para registro offline, snapshot y sesión previamente habilitados.

**Disparador:** el actor solicita consultar dashboard y analítica.

**Datos:** período, sucursal, versión modelo.

**Flujo principal**

1. Consultar KPI propios.
2. Preparar variables autorizadas.
3. Ejecutar inferencia acotada.
4. Mostrar predicción segmentos y métricas.
5. Explicar limitaciones.

**Flujos alternativos**

- Sin historial: informar.
- Modelo ausente: mantener KPI y avisar.
- Tenant ajeno: denegar.

**Postcondición:** Resultados comerciales y predictivos interpretables.

**Aceptación:** ejecutar el flujo con datos de la empresa A, comprobar el resultado y repetir una petición con referencias de B para verificar la restricción cuando corresponda. Ejecutar cada alternativa y conservar el resultado real; no basta una captura de la pantalla inicial.

**Prototipo:** `prototipos/CU-37.svg`. **Diagrama:** `diagramas/casos_uso/CU-37.puml`.

## CU-38 Consultar auditoría

**Actor:** Administrador autorizado. **Plataforma:** Web. **Antecedente P1:** 25.

**Objetivo:** Historial de acciones y fallos accesible solo a responsables.

**Precondiciones:** empresa identificada y activa; permisos vigentes para operaciones privadas; referencias pertenecientes a la misma empresa. Para registro offline, snapshot y sesión previamente habilitados.

**Disparador:** el actor solicita consultar auditoría.

**Datos:** acción, fecha, usuario, UUID.

**Flujo principal**

1. Autenticar permiso de auditoría.
2. Aplicar filtros propios.
3. Consultar eventos paginados.
4. Relacionar operación y resultado.
5. Presentar diagnóstico sin secretos.

**Flujos alternativos**

- Sin permiso: denegar.
- Empresa ajena: no encontrado.
- Filtros extensos: paginar y limitar.

**Postcondición:** Historial de acciones y fallos accesible solo a responsables.

**Aceptación:** ejecutar el flujo con datos de la empresa A, comprobar el resultado y repetir una petición con referencias de B para verificar la restricción cuando corresponda. Ejecutar cada alternativa y conservar el resultado real; no basta una captura de la pantalla inicial.

**Prototipo:** `prototipos/CU-38.svg`. **Diagrama:** `diagramas/casos_uso/CU-38.puml`.
