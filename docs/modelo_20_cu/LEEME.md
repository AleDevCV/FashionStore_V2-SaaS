# Modelo de requisitos de FashionStore: 20 casos principales

Archivo editable: **FashionStore_Casos_de_Uso_20.drawio**. Contiene seis páginas: general circular, acceso/SaaS, catálogo/abastecimiento, ventas, offline y reportes/analítica/auditoría.

En draw.io/diagrams.net puede abrirse desde **Archivo → Abrir desde → Dispositivo** y elegir el archivo. También puede abrirse con draw.io Desktop. El archivo no está publicado ni enlazado a una cuenta externa.

**CAPITULO_II_20_CU.md** contiene la redacción completa del capítulo: descripción, actores, requisitos funcionales y no funcionales, reglas con su origen, explicación UML y equivalencias. Se usa numeración 2.1–2.5 por corresponder al capítulo II.

**FICHAS_RESUMIDAS_20_CU.md** y **CU_20_catalogo.json** identifican los subflujos de cada grupo. Son modelos de requisitos; la reducción no declara nuevos resultados de pruebas.

**equivalencias_38_a_20.csv** conserva exactamente los 38 CU del plan inicial e incluye una columna distinta para los antecedentes del P1. Los comentarios del código pueden utilizar IDs del primer parcial; no deben confundirse con la numeración del plan de 38 CU. Cada ID del plan anterior se asigna a un único grupo nuevo; las vistas adicionales reutilizan los mismos 20 IDs.

Las imágenes de **vistas/** se generaron desde el mismo modelo de coordenadas como recursos de documentación. Las SVG son vectoriales y las PNG tienen 2600 píxeles de ancho. Para Word conviene utilizar las vistas de área y reservar la vista general para una hoja horizontal o anexo a mayor tamaño.

## Relaciones UML

- CU-11 y CU-13 incluyen CU-08 y CU-10: consulta de disponibilidad y salida de inventario en la confirmación exitosa. Los movimientos se aplican una única vez dentro de la transacción correspondiente.
- CU-14 extiende CU-11 y CU-13 al solicitar la representación del comprobante después de una compra o venta confirmada. La descarga es opcional; el registro comercial permanece aunque no se descargue.
- No hay flecha include desde cada caso a iniciar sesión: la sesión es una precondición de las operaciones privadas.
- No hay include entre registro offline y sincronización: el envío puede suceder después.
- La resolución de conflictos y el entrenamiento se detallan como subflujos, sin ejecutar resolución cuando no hay conflicto ni entrenamiento al consultar el dashboard.

## Validación

Se verificaron XML, esquema oficial mxfile.xsd, IDs, referencias, conteo de casos, cobertura del inventario anterior, actores fuera del límite y las seis vistas renderizadas. La apertura en el servicio web no se completó: la revisión automática bloqueó la transmisión del documento al servicio externo. Ningún contenido del XML se subió para esa comprobación.

Los archivos históricos de 38 CU y el documento Word abierto se conservaron. La nueva numeración debe adoptarse mediante esta equivalencia al actualizar las fichas, matrices y diagramas del documento; no corresponde renombrar rutas, IDs de base ni funciones existentes.

Para regenerar: ejecutar `python scripts/build_usecases_20.py` y, con `sharp` disponible en Node, `node scripts/render_usecases_20.cjs`.
