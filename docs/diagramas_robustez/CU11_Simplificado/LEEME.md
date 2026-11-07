# CU11 - Realizar compra y pago en línea

Vista simplificada de una página con 29 mensajes numerados. La cantidad de interfaces, controles y entidades responde al flujo de este CU. Las tablas auxiliares y validaciones quedan resumidas dentro del control.

- Se resume la modalidad Stripe de prueba. Firma, tenant, importe, moneda y duplicados se validan dentro del control; la redirección del navegador no confirma la venta.
- Los detalles y retenciones permanecen dentro de reserve y confirm_reservation. El descuento ocurre únicamente mediante movimientos. La creación de reserva sí inserta bitácora; no se inventan auditorías adicionales en el webhook actual.
- La consulta final representa el caso exitoso; el endpoint devuelve estado pendiente si aún no existe venta. El comprobante se detalla en CU14.

El archivo .drawio es editable; el PNG sirve para Word y el SVG conserva calidad vectorial. El JScript crea un paquete nuevo en Enterprise Architect al ejecutarlo con un paquete seleccionado. Su sintaxis y generación se validan en simulación, no en una sesión real de EA.

Los archivos Modelo.json y MENSAJES.csv conservan las referencias de los métodos al código. Los controles y las interfaces agrupadas son abstracciones de análisis, no clases ni pantallas nuevas. No se modificó el código funcional ni el documento Word.
