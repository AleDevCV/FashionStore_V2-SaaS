# CU08 - Consultar inventario y disponibilidad

Vista simplificada de una página con 18 mensajes numerados. La cantidad de interfaces, controles y entidades responde al flujo de este CU. Las tablas auxiliares y validaciones quedan resumidas dentro del control.

- El monitoreo consulta inventario físico; consultar_disponibilidad utiliza la vista inventario_catalogo. No se atribuye a obtener_monitoreo_inventario una resta de reservas que no realiza.
- La vista de disponibilidad integra las retenciones. Sus tablas auxiliares se omiten del dibujo. No se modifica stock ni se inventan eventos de bitácora para consultas.

El archivo .drawio es editable; el PNG sirve para Word y el SVG conserva calidad vectorial. El JScript crea un paquete nuevo en Enterprise Architect al ejecutarlo con un paquete seleccionado. Su sintaxis y generación se validan en simulación, no en una sesión real de EA.

Los archivos Modelo.json y MENSAJES.csv conservan las referencias de los métodos al código. Los controles y las interfaces agrupadas son abstracciones de análisis, no clases ni pantallas nuevas. No se modificó el código funcional ni el documento Word.
