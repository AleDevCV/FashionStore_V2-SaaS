# CU16 - Registrar y consultar operaciones offline

Vista simplificada de una página con 35 mensajes numerados. La cantidad de interfaces, controles y entidades responde al flujo de este CU. Las tablas auxiliares y validaciones quedan resumidas dentro del control.

- El backend solo interviene en la descarga inicial con conexión. Consultar y registrar usan IndexedDB o SQLite. No se dibuja sincronización: corresponde a CU17.
- Catálogo local y permiso agrupa snapshot, productos, variantes y disponibilidad conocida. Operación y detalles se conservan separados y se guardan en la misma transacción.
- No existe una bitácora local separada: la operación conserva UUID, autor, fecha, estado e intentos. La auditoría central de sincronización se escribe posteriormente en CU17; no se inventa acceso a PostgreSQL durante una venta sin red.
- Las ventas requieren rol autorizado, efectivo suficiente y permiso offline vigente. Las reservas requieren cliente descargado. Son operaciones provisionales, no ventas confirmadas por el servidor.

El archivo .drawio es editable; el PNG sirve para Word y el SVG conserva calidad vectorial. El JScript crea un paquete nuevo en Enterprise Architect al ejecutarlo con un paquete seleccionado. Su sintaxis y generación se validan en simulación, no en una sesión real de EA.

Los archivos Modelo.json y MENSAJES.csv conservan las referencias de los métodos al código. Los controles y las interfaces agrupadas son abstracciones de análisis, no clases ni pantallas nuevas. No se modificó el código funcional ni el documento Word.
