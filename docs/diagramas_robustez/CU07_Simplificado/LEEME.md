# CU07 - Gestionar proveedores, compras y recepciones

Vista simplificada de una página con 32 mensajes numerados. La cantidad de interfaces, controles y entidades responde al flujo de este CU. Las tablas auxiliares y validaciones quedan resumidas dentro del control.

- La recepción ocurre al registrar_compra; no existe una segunda API de recepción independiente. Los movimientos actualizan el inventario mediante el trigger existente.
- No se inventa una entidad Recepción ni se duplica el descuento/entrada de stock. La consulta móvil se conserva; el registro se representa en la interfaz administrativa.

El archivo .drawio es editable; el PNG sirve para Word y el SVG conserva calidad vectorial. El JScript crea un paquete nuevo en Enterprise Architect al ejecutarlo con un paquete seleccionado. Su sintaxis y generación se validan en simulación, no en una sesión real de EA.

Los archivos Modelo.json y MENSAJES.csv conservan las referencias de los métodos al código. Los controles y las interfaces agrupadas son abstracciones de análisis, no clases ni pantallas nuevas. No se modificó el código funcional ni el documento Word.
