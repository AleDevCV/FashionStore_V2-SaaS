# CU10 - Registrar movimientos de inventario - Secuencia

Archivo editable .drawio, SVG vectorial y PNG para Word. Se conservan exactamente los participantes del modelo de robustez simplificado y se cubren sus 19 mensajes principales.

Los alt y opt comienzan en Interfaz. Los loop comienzan en Control y cubren únicamente las líneas afectadas, reordenadas cuando hace falta para situarlas juntas. El borde derecho de cada recuadro corresponde a su último participante involucrado. Un rectángulo continuo puede atravesar líneas de vida intermedias sin enviarles mensajes.

La numeración se asigna de nuevo al incluir alternativas; el archivo de trazabilidad conserva la correspondencia con robustez. No se añaden participantes para validaciones o almacenamiento auxiliares. Cada acción se presenta como escenario independiente.

- Las sucursales y variantes se validan dentro del control, sin desplegar todos los catálogos auxiliares. El stock se actualiza por trigger al insertar el movimiento.
- El esquema actual recibe una sucursal y no una sucursal de destino: no se inventa un traslado completo de dos sucursales ni una API de idempotencia inexistente para este endpoint.

No se modificó el programa, el Word ni los diagramas anteriores.
