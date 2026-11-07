# Diagramas de robustez simplificados - CU07 a CU14 y CU16

Cada caso tiene una página propia con mensajes separados y numeración consecutiva, sin etiquetas HTTP ni comunicación entre entidades. Se conserva una única responsabilidad de control por entidad, aunque el CU16 diferencia los controles local y central.

| Caso de uso | Mensajes | Entidades | Editable | Para Word | Enterprise Architect |
|---|---:|---:|---|---|---|
| CU07 - Gestionar proveedores, compras y recepciones | 32 | 5 | [draw.io](CU07_Simplificado/CU07_Robustez_Simplificada.drawio) | [PNG](CU07_Simplificado/CU07_Robustez_Simplificada_General.png) | [JScript](CU07_Simplificado/JScript_Generar_Robustez_CU07.js) |
| CU08 - Consultar inventario y disponibilidad | 18 | 2 | [draw.io](CU08_Simplificado/CU08_Robustez_Simplificada.drawio) | [PNG](CU08_Simplificado/CU08_Robustez_Simplificada_General.png) | [JScript](CU08_Simplificado/JScript_Generar_Robustez_CU08.js) |
| CU09 - Explorar catálogo y asistencia de compra | 33 | 3 | [draw.io](CU09_Simplificado/CU09_Robustez_Simplificada.drawio) | [PNG](CU09_Simplificado/CU09_Robustez_Simplificada_General.png) | [JScript](CU09_Simplificado/JScript_Generar_Robustez_CU09.js) |
| CU10 - Registrar movimientos de inventario | 19 | 3 | [draw.io](CU10_Simplificado/CU10_Robustez_Simplificada.drawio) | [PNG](CU10_Simplificado/CU10_Robustez_Simplificada_General.png) | [JScript](CU10_Simplificado/JScript_Generar_Robustez_CU10.js) |
| CU11 - Realizar compra y pago en línea | 29 | 5 | [draw.io](CU11_Simplificado/CU11_Robustez_Simplificada.drawio) | [PNG](CU11_Simplificado/CU11_Robustez_Simplificada_General.png) | [JScript](CU11_Simplificado/JScript_Generar_Robustez_CU11.js) |
| CU12 - Gestionar reservas de prendas | 31 | 5 | [draw.io](CU12_Simplificado/CU12_Robustez_Simplificada.drawio) | [PNG](CU12_Simplificado/CU12_Robustez_Simplificada_General.png) | [JScript](CU12_Simplificado/JScript_Generar_Robustez_CU12.js) |
| CU13 - Registrar venta presencial | 22 | 5 | [draw.io](CU13_Simplificado/CU13_Robustez_Simplificada.drawio) | [PNG](CU13_Simplificado/CU13_Robustez_Simplificada_General.png) | [JScript](CU13_Simplificado/JScript_Generar_Robustez_CU13.js) |
| CU14 - Obtener comprobantes de compra | 23 | 4 | [draw.io](CU14_Simplificado/CU14_Robustez_Simplificada.drawio) | [PNG](CU14_Simplificado/CU14_Robustez_Simplificada_General.png) | [JScript](CU14_Simplificado/JScript_Generar_Robustez_CU14.js) |
| CU16 - Registrar y consultar operaciones offline | 35 | 4 | [draw.io](CU16_Simplificado/CU16_Robustez_Simplificada.drawio) | [PNG](CU16_Simplificado/CU16_Robustez_Simplificada_General.png) | [JScript](CU16_Simplificado/JScript_Generar_Robustez_CU16.js) |

También puedes abrir [todos los diagramas en un archivo con nueve pestañas](CU07_CU14_CU16_Robustez_Simplificada.drawio) o utilizar [el paquete de entrega ZIP](CU07_CU14_CU16_Robustez_Simplificada.zip).

La bitácora se representa cuando el flujo actual escribe sus eventos. CU08 solo consulta información; CU16 registra localmente y su auditoría central corresponde a CU17. No se inventan tablas ni llamadas a un servidor durante la operación sin conexión.

Los controles y las interfaces pueden agrupar pantallas o módulos reales como abstracción de análisis. Los archivos Modelo.json, CSV, Validacion.json y LEEME de cada carpeta explican las fuentes y los detalles omitidos para mantener el diagrama breve.

Los JScript son autocontenidos: selecciona el paquete de destino en Enterprise Architect, crea un script JScript, pega el contenido del caso y ejecútalo. Se crea un paquete nuevo. Se validó su generación completa en simulación; la visualización en una sesión real de EA permanece por comprobar.

No se modificó el CU06 aceptado, el documento Word ni el código funcional del programa. No se ejecutaron comandos Git.
