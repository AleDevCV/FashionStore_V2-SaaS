# CU12 - Gestionar reservas de prendas - Secuencia

Archivo editable .drawio, SVG vectorial y PNG para Word. Se conservan exactamente los participantes del modelo de robustez simplificado y se cubren sus 31 mensajes principales.

Los alt y opt comienzan en Interfaz. Los loop comienzan en Control y cubren únicamente las líneas afectadas, reordenadas cuando hace falta para situarlas juntas. El borde derecho de cada recuadro corresponde a su último participante involucrado. Un rectángulo continuo puede atravesar líneas de vida intermedias sin enviarles mensajes.

La numeración se asigna de nuevo al incluir alternativas; el archivo de trazabilidad conserva la correspondencia con robustez. No se añaden participantes para validaciones o almacenamiento auxiliares. Cada acción se presenta como escenario independiente.

- Crear reserva retiene disponibilidad; preparar no crea una venta. El cobro pertenece a CU11 o CU13. deliver exige una venta existente y registra la entrega física por separado.
- La caducidad de disponibilidad se deriva de la vigencia de retencion; no se inventa una tarea programada que actualice estados. Los detalles se incluyen en Reserva como agregado.
- El código audita la creación; no se añaden escrituras de bitácora a preparar, cancelar o entregar si esas rutas no las realizan actualmente.

No se modificó el programa, el Word ni los diagramas anteriores.
