# CU11 - Realizar compra y pago en línea - Secuencia

Archivo editable .drawio, SVG vectorial y PNG para Word. Se conservan exactamente los participantes del modelo de robustez simplificado y se cubren sus 29 mensajes principales.

Los alt y opt comienzan en Interfaz. Los loop comienzan en Control y cubren únicamente las líneas afectadas, reordenadas cuando hace falta para situarlas juntas. El borde derecho de cada recuadro corresponde a su último participante involucrado. Un rectángulo continuo puede atravesar líneas de vida intermedias sin enviarles mensajes.

La numeración se asigna de nuevo al incluir alternativas; el archivo de trazabilidad conserva la correspondencia con robustez. No se añaden participantes para validaciones o almacenamiento auxiliares. Cada acción se presenta como escenario independiente.

- Se resume la modalidad Stripe de prueba. Firma, tenant, importe, moneda y duplicados se validan dentro del control; la redirección del navegador no confirma la venta.
- Los detalles y retenciones permanecen dentro de reserve y confirm_reservation. El descuento ocurre únicamente mediante movimientos. La creación de reserva sí inserta bitácora; no se inventan auditorías adicionales en el webhook actual.
- La consulta final representa el caso exitoso; el endpoint devuelve estado pendiente si aún no existe venta. El comprobante se detalla en CU14.

No se modificó el programa, el Word ni los diagramas anteriores.
