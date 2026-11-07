# CU14 - Obtener comprobantes de compra - Secuencia

Archivo editable .drawio, SVG vectorial y PNG para Word. Se conservan exactamente los participantes del modelo de robustez simplificado y se cubren sus 23 mensajes principales.

Los alt y opt comienzan en Interfaz. Los loop comienzan en Control y cubren únicamente las líneas afectadas, reordenadas cuando hace falta para situarlas juntas. El borde derecho de cada recuadro corresponde a su último participante involucrado. Un rectángulo continuo puede atravesar líneas de vida intermedias sin enviarles mensajes.

La numeración se asigna de nuevo al incluir alternativas; el archivo de trazabilidad conserva la correspondencia con robustez. No se añaden participantes para validaciones o almacenamiento auxiliares. Cada acción se presenta como escenario independiente.

- Consultar o descargar no crea otro comprobante ni cambia la venta. Generar es una acción condicional separada; el servicio rechaza duplicados.
- Se incluye Archivo PDF como entidad persistente de archivos, no como una tabla. Los permisos y propiedad se validan mediante el contexto y RLS.
- Si falta el archivo, descargar_pdf_autorizado informa error. No se dibuja una regeneración automática que no existe. El envío de correo es un subflujo opcional omitido.

No se modificó el programa, el Word ni los diagramas anteriores.
