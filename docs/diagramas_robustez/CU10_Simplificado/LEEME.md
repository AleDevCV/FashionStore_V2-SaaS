# CU10 - Registrar movimientos de inventario

Vista simplificada de una página con 19 mensajes numerados. La cantidad de interfaces, controles y entidades responde al flujo de este CU. Las tablas auxiliares y validaciones quedan resumidas dentro del control.

- Las sucursales y variantes se validan dentro del control, sin desplegar todos los catálogos auxiliares. El stock se actualiza por trigger al insertar el movimiento.
- El esquema actual recibe una sucursal y no una sucursal de destino: no se inventa un traslado completo de dos sucursales ni una API de idempotencia inexistente para este endpoint.

El archivo .drawio es editable; el PNG sirve para Word y el SVG conserva calidad vectorial. El JScript crea un paquete nuevo en Enterprise Architect al ejecutarlo con un paquete seleccionado. Su sintaxis y generación se validan en simulación, no en una sesión real de EA.

Los archivos Modelo.json y MENSAJES.csv conservan las referencias de los métodos al código. Los controles y las interfaces agrupadas son abstracciones de análisis, no clases ni pantallas nuevas. No se modificó el código funcional ni el documento Word.
