# CU10 - Registrar movimientos de inventario

Vista simplificada de una página con 19 mensajes numerados. La cantidad de interfaces, controles y entidades responde al flujo de este CU. Las tablas auxiliares y validaciones quedan resumidas dentro del control.

- Las sucursales y variantes se validan dentro del control, sin desplegar todos los catálogos auxiliares. El stock se actualiza por trigger al insertar el movimiento.
- El archivo original representa el esquema anterior a A3, de una sucursal y sin idempotencia; se conserva como evidencia de esa versión. El suplemento A3 documenta el contrato y la implementación nuevos.

El archivo .drawio es editable; el PNG sirve para Word y el SVG conserva calidad vectorial. El JScript crea un paquete nuevo en Enterprise Architect al ejecutarlo con un paquete seleccionado. Su sintaxis y generación se validan en simulación, no en una sesión real de EA.

Los archivos Modelo.json y MENSAJES.csv conservan las referencias de los métodos al código. Los controles y las interfaces agrupadas son abstracciones de análisis, no clases ni pantallas nuevas. No se modificó el código funcional ni el documento Word.

## Suplemento A3 vigente en el código local

`CU10_A3_Traspaso.drawio` y `.svg` añaden la vista de traspaso; se conserva el gráfico anterior sin fingir que sus mensajes históricos ya cubrían dos sucursales. El modelo de robustez identifica módulos/funciones reales y entidades SQL, no clases Python ficticias. La secuencia SVG muestra el escenario válido de UUID nuevo; el `.puml` de la carpeta de secuencia incluye alternativas de caché, contenido distinto y rollback.

Los SVG se renderizaron localmente y se revisaron visualmente; los XML draw.io se analizaron y sus referencias se comprobaron. El PlantUML es fuente revisada, no se afirma ejecución con PlantUML ni Enterprise Architect. Migración 018 aplicada solo en DBs efímeras; representación de diseño físico no implica que exista ya en la demostración persistente. [Reglas, pruebas y límites](../../CORRECCION_AUTORIZACION_A3.md).
