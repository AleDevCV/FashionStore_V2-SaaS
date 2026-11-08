# CU16 - Registrar y consultar operaciones offline - Secuencia

Archivo editable .drawio, SVG vectorial y PNG para Word. Se conservan exactamente los participantes del modelo de robustez simplificado y se cubren sus 35 mensajes principales.

Los alt y opt comienzan en Interfaz. Los loop comienzan en Control y cubren únicamente las líneas afectadas, reordenadas cuando hace falta para situarlas juntas. El borde derecho de cada recuadro corresponde a su último participante involucrado. Un rectángulo continuo puede atravesar líneas de vida intermedias sin enviarles mensajes.

La numeración se asigna de nuevo al incluir alternativas; el archivo de trazabilidad conserva la correspondencia con robustez. No se añaden participantes para validaciones o almacenamiento auxiliares. Cada acción se presenta como escenario independiente.

- El backend solo interviene en la descarga inicial con conexión. Consultar y registrar usan IndexedDB o SQLite. No se dibuja sincronización: corresponde a CU17.
- Catálogo local y permiso agrupa snapshot, productos, variantes y disponibilidad conocida. Operación y detalles se conservan separados y se guardan en la misma transacción.
- No existe una bitácora local separada: la operación conserva UUID, autor, fecha, estado e intentos. La auditoría central de sincronización se escribe posteriormente en CU17; no se inventa acceso a PostgreSQL durante una venta sin red.
- Las ventas requieren rol autorizado, efectivo suficiente y permiso offline vigente. Las reservas requieren cliente descargado. Son operaciones provisionales, no ventas confirmadas por el servidor.

No se modificó el programa, el Word ni los diagramas anteriores.

## Revisión de alcance por A2

Se revisaron el modelo de robustez y la secuencia de CU16: representan descarga y persistencia local, y excluyen expresamente la sincronización central de CU17. `snapshot` conserva su validación de sucursal y consulta de resultados propios; A2 no cambia ese flujo ni sus participantes. Por ello no se modifican draw.io, SVG o PNG ni se renueva su validación como si se hubieran generado de nuevo. No se encontró una robustez o secuencia detallada de CU17 en las carpetas revisadas; queda pendiente su elaboración, sin inventar clases ni diagramas. Reglas centrales y evidencia: [A2](../../CORRECCION_AUTORIZACION_A2.md).
