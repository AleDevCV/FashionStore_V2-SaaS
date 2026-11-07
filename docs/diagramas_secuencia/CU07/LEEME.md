# CU07 - Gestionar proveedores, compras y recepciones - Secuencia

Archivo editable .drawio, SVG vectorial y PNG para Word. Se conservan exactamente los participantes del modelo de robustez simplificado y se cubren sus 32 mensajes principales.

Los alt y opt comienzan en Interfaz. Los loop comienzan en Control y cubren únicamente las líneas afectadas, reordenadas cuando hace falta para situarlas juntas. El borde derecho de cada recuadro corresponde a su último participante involucrado. Un rectángulo continuo puede atravesar líneas de vida intermedias sin enviarles mensajes.

La numeración se asigna de nuevo al incluir alternativas; el archivo de trazabilidad conserva la correspondencia con robustez. No se añaden participantes para validaciones o almacenamiento auxiliares. Cada acción se presenta como escenario independiente.

- La recepción ocurre al registrar_compra; no existe una segunda API de recepción independiente. Los movimientos actualizan el inventario mediante el trigger existente.
- No se inventa una entidad Recepción ni se duplica el descuento/entrada de stock. La consulta móvil se conserva; el registro se representa en la interfaz administrativa.

No se modificó el programa, el Word ni los diagramas anteriores.
