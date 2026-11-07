# Diagramas de secuencia - CU07 a CU14 y CU16

Cada archivo corresponde al respectivo modelo de robustez simplificado, conservando exactamente sus actores, interfaces, controles y entidades. Los mensajes originales mantienen su referencia en el archivo de trazabilidad y se renumeran al incorporar alternativas.

| Caso de uso | Mensajes | Editable | Para Word |
|---|---:|---|---|
| CU07 - Gestionar proveedores, compras y recepciones | 37 | [CU07 .drawio](CU07/CU07_Diagrama_Secuencia.drawio) | [PNG](CU07/CU07_Diagrama_Secuencia.png) |
| CU08 - Consultar inventario y disponibilidad | 21 | [CU08 .drawio](CU08/CU08_Diagrama_Secuencia.drawio) | [PNG](CU08/CU08_Diagrama_Secuencia.png) |
| CU09 - Explorar catálogo y asistencia de compra | 38 | [CU09 .drawio](CU09/CU09_Diagrama_Secuencia.drawio) | [PNG](CU09/CU09_Diagrama_Secuencia.png) |
| CU10 - Registrar movimientos de inventario | 21 | [CU10 .drawio](CU10/CU10_Diagrama_Secuencia.drawio) | [PNG](CU10/CU10_Diagrama_Secuencia.png) |
| CU11 - Realizar compra y pago en línea | 34 | [CU11 .drawio](CU11/CU11_Diagrama_Secuencia.drawio) | [PNG](CU11/CU11_Diagrama_Secuencia.png) |
| CU12 - Gestionar reservas de prendas | 36 | [CU12 .drawio](CU12/CU12_Diagrama_Secuencia.drawio) | [PNG](CU12/CU12_Diagrama_Secuencia.png) |
| CU13 - Registrar venta presencial | 25 | [CU13 .drawio](CU13/CU13_Diagrama_Secuencia.drawio) | [PNG](CU13/CU13_Diagrama_Secuencia.png) |
| CU14 - Obtener comprobantes de compra | 26 | [CU14 .drawio](CU14/CU14_Diagrama_Secuencia.drawio) | [PNG](CU14/CU14_Diagrama_Secuencia.png) |
| CU16 - Registrar y consultar operaciones offline | 39 | [CU16 .drawio](CU16/CU16_Diagrama_Secuencia.drawio) | [PNG](CU16/CU16_Diagrama_Secuencia.png) |

[Abrir los nueve diagramas en un solo archivo](CU07_CU14_CU16_Diagramas_Secuencia.drawio).

Los alt y opt comienzan en la interfaz principal y los loop en el control correspondiente. Todos terminan en su último participante afectado, con margen de 30 px. Las líneas de vida se han ordenado para que cada loop abarque únicamente sus participantes. Un rectángulo continuo de UML puede atravesar otras líneas intermedias sin que reciban mensajes ni participen en ese operando.

Cada CU incluye PNG de alta resolución a 300 ppp, SVG, archivo editable, trazabilidad y validación. Los escenarios se presentan por acción y no constituyen una cadena obligatoria de operaciones. Las consultas sin repetición no reciben loop; los subflujos sin condición opcional no reciben opt.

La revisión incluye formato XML, correspondencia de todos los participantes y mensajes principales, límites de los fragmentos y revisión visual. No se modificó el Word, los diagramas previos ni el código funcional. No se ejecutaron comandos Git.
