# CU12 - Gestionar reservas de prendas

Vista simplificada de una página con 31 mensajes numerados. La cantidad de interfaces, controles y entidades responde al flujo de este CU. Las tablas auxiliares y validaciones quedan resumidas dentro del control.

- Crear reserva retiene disponibilidad; preparar no crea una venta. El cobro pertenece a CU11 o CU13. deliver exige una venta existente y registra la entrega física por separado.
- La caducidad de disponibilidad se deriva de la vigencia de retencion; no se inventa una tarea programada que actualice estados. Los detalles se incluyen en Reserva como agregado.
- El código audita la creación; no se añaden escrituras de bitácora a preparar, cancelar o entregar si esas rutas no las realizan actualmente.

El archivo .drawio es editable; el PNG sirve para Word y el SVG conserva calidad vectorial. El JScript crea un paquete nuevo en Enterprise Architect al ejecutarlo con un paquete seleccionado. Su sintaxis y generación se validan en simulación, no en una sesión real de EA.

Los archivos Modelo.json y MENSAJES.csv conservan las referencias de los métodos al código. Los controles y las interfaces agrupadas son abstracciones de análisis, no clases ni pantallas nuevas. No se modificó el código funcional ni el documento Word.
