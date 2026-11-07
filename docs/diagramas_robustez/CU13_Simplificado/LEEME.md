# CU13 - Registrar venta presencial

Vista simplificada de una página con 22 mensajes numerados. La cantidad de interfaces, controles y entidades responde al flujo de este CU. Las tablas auxiliares y validaciones quedan resumidas dentro del control.

- Sucursal, cliente mostrador y autorización se validan dentro del control. El código actual no ofrece una entidad de caja/apertura/cierre; no se inventa ese módulo.
- La confirmación de efectivo y la comprobación de precios preceden a la escritura. El trigger aplica el stock por movimiento. El comprobante se intenta en un savepoint opcional: un fallo no revierte la venta; su detalle corresponde a CU14.
- No se atribuye a este endpoint una clave UUID o reintento idempotente que no implementa explícitamente.

El archivo .drawio es editable; el PNG sirve para Word y el SVG conserva calidad vectorial. El JScript crea un paquete nuevo en Enterprise Architect al ejecutarlo con un paquete seleccionado. Su sintaxis y generación se validan en simulación, no en una sesión real de EA.

Los archivos Modelo.json y MENSAJES.csv conservan las referencias de los métodos al código. Los controles y las interfaces agrupadas son abstracciones de análisis, no clases ni pantallas nuevas. No se modificó el código funcional ni el documento Word.
