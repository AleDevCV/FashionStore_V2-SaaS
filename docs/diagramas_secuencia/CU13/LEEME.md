# CU13 - Registrar venta presencial - Secuencia

Archivo editable .drawio, SVG vectorial y PNG para Word. Se conservan exactamente los participantes del modelo de robustez simplificado y se cubren sus 22 mensajes principales.

Los alt y opt comienzan en Interfaz. Los loop comienzan en Control y cubren únicamente las líneas afectadas, reordenadas cuando hace falta para situarlas juntas. El borde derecho de cada recuadro corresponde a su último participante involucrado. Un rectángulo continuo puede atravesar líneas de vida intermedias sin enviarles mensajes.

La numeración se asigna de nuevo al incluir alternativas; el archivo de trazabilidad conserva la correspondencia con robustez. No se añaden participantes para validaciones o almacenamiento auxiliares. Cada acción se presenta como escenario independiente.

- Sucursal, cliente mostrador y autorización se validan dentro del control. El código actual no ofrece una entidad de caja/apertura/cierre; no se inventa ese módulo.
- La confirmación de efectivo y la comprobación de precios preceden a la escritura. El trigger aplica el stock por movimiento. El comprobante se intenta en un savepoint opcional: un fallo no revierte la venta; su detalle corresponde a CU14.
- No se atribuye a este endpoint una clave UUID o reintento idempotente que no implementa explícitamente.

No se modificó el programa, el Word ni los diagramas anteriores.
