# CU14 - Obtener comprobantes de compra

Vista simplificada de una página con 23 mensajes numerados. La cantidad de interfaces, controles y entidades responde al flujo de este CU. Las tablas auxiliares y validaciones quedan resumidas dentro del control.

- Consultar o descargar no crea otro comprobante ni cambia la venta. Generar es una acción condicional separada; el servicio rechaza duplicados.
- Se incluye Archivo PDF como entidad persistente de archivos, no como una tabla. Los permisos y propiedad se validan mediante el contexto y RLS.
- Si falta el archivo, descargar_pdf_autorizado informa error. No se dibuja una regeneración automática que no existe. El envío de correo es un subflujo opcional omitido.

El archivo .drawio es editable; el PNG sirve para Word y el SVG conserva calidad vectorial. El JScript crea un paquete nuevo en Enterprise Architect al ejecutarlo con un paquete seleccionado. Su sintaxis y generación se validan en simulación, no en una sesión real de EA.

Los archivos Modelo.json y MENSAJES.csv conservan las referencias de los métodos al código. Los controles y las interfaces agrupadas son abstracciones de análisis, no clases ni pantallas nuevas. No se modificó el código funcional ni el documento Word.
