# CU10 - Registrar movimientos de inventario - Secuencia

Archivo editable .drawio, SVG vectorial y PNG para Word. Se conservan exactamente los participantes del modelo de robustez simplificado y se cubren sus 19 mensajes principales.

Los alt y opt comienzan en Interfaz. Los loop comienzan en Control y cubren únicamente las líneas afectadas, reordenadas cuando hace falta para situarlas juntas. El borde derecho de cada recuadro corresponde a su último participante involucrado. Un rectángulo continuo puede atravesar líneas de vida intermedias sin enviarles mensajes.

La numeración se asigna de nuevo al incluir alternativas; el archivo de trazabilidad conserva la correspondencia con robustez. No se añaden participantes para validaciones o almacenamiento auxiliares. Cada acción se presenta como escenario independiente.

- Las sucursales y variantes se validan dentro del control, sin desplegar todos los catálogos auxiliares. El stock se actualiza por trigger al insertar el movimiento.
- El archivo original representa el esquema anterior a A3, de una sucursal y sin idempotencia; se conserva como evidencia de esa versión. El suplemento A3 documenta el contrato y la implementación nuevos.

No se modificó el programa, el Word ni los diagramas anteriores.

## Suplemento A3 vigente en el código local

`CU10_A3_Traspaso.drawio` y `.svg` añaden la vista de traspaso; se conserva el gráfico anterior sin fingir que sus mensajes históricos ya cubrían dos sucursales. El modelo de robustez identifica módulos/funciones reales y entidades SQL, no clases Python ficticias. La secuencia SVG muestra el escenario válido de UUID nuevo; el `.puml` de la carpeta de secuencia incluye alternativas de caché, contenido distinto y rollback.

Los SVG se renderizaron localmente y se revisaron visualmente; los XML draw.io se analizaron y sus referencias se comprobaron. El PlantUML es fuente revisada, no se afirma ejecución con PlantUML ni Enterprise Architect. Migración 018 aplicada solo en DBs efímeras; representación de diseño físico no implica que exista ya en la demostración persistente. [Reglas, pruebas y límites](../../CORRECCION_AUTORIZACION_A3.md).
