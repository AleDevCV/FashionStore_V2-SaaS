# CU06 - Robustez simplificada

Versión de una sola página: **1 actor, 1 interfaz, 1 control, 5 entidades y 37 mensajes numerados**, organizados en seis acciones principales.

Entidades conservadas: Categoría, Temporada/Colección, Prenda, Variante de prenda y Bitácora. Las once entidades de la versión anterior reflejaban mayor detalle técnico; no es necesario mostrar todas las tablas para explicar el recorrido principal de este caso de uso.

La interfaz agrupa las pantallas actuales de administración del catálogo. El control agrupa las responsabilidades existentes de los routers y servicios de categorías, temporadas y prendas. Son abstracciones de análisis, no una pantalla nueva ni una clase Python añadida.

Se representan consultar el catálogo, registrar categoría, registrar temporada/colección, registrar prenda y variantes, actualizar datos/precios/ofertas e inhabilitar una prenda. Las validaciones, consultas auxiliares y alternativas se omiten del dibujo para conservar su brevedad. Talla y colores son datos de la variante en esta vista; imágenes y efectos internos sobre existencias permanecen dentro del servicio. El código conserva todos esos comportamientos.

Cada entidad se comunica únicamente con el control. La bitácora recibe mensajes independientes por cada modificación representada. No se añaden respuestas artificiales a las escrituras que no devuelven datos, ni se utilizan etiquetas HTTP.

## Archivos

- `CU06_Robustez_Simplificada.drawio`: una página editable.
- `CU06_Robustez_Simplificada_General.png`: imagen para Word.
- `CU06_Robustez_Simplificada_General.svg`: imagen vectorial.
- `JScript_Generar_Robustez_CU06.js`: versión para Enterprise Architect con los mismos 37 mensajes.
- `MENSAJES_CU06.csv`: numeración, origen, destino y referencias al código.
- Los archivos `*_Modelo.json`, `*_Validacion.json` y `VALIDACION_JSCRIPT.json` conservan la trazabilidad y los resultados de comprobación.

## Enterprise Architect

Selecciona el paquete de destino, crea un script de tipo JScript en la ventana de scripting, pega el contenido completo del archivo y ejecútalo. Se crea un paquete nuevo con un único diagrama de comunicación; no se reemplazan diagramas anteriores.

La sintaxis y la generación completa se comprobaron mediante una simulación de la interfaz de EA, incluyendo números, sentidos de las flechas y texto. No se ejecutó en una sesión real de Enterprise Architect; la visualización nativa permanece por comprobar. Se conserva el mecanismo de asociaciones y mensajes del JScript de referencia.

La versión extensa sigue disponible en `../CU06_Numerado`. No se modificó el documento Word ni el código funcional, y no se ejecutaron comandos Git.
