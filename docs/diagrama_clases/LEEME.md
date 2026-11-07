# 3.4. Diagrama de clases UML

## Archivos principales

- FashionStore_Clases_General.drawio: vista técnica general, editable.
- FashionStore_Clases_Por_Partes.drawio: la misma vista repartida en páginas consecutivas.
- FashionStore_Clases_General.svg: vista general vectorial.
- laminas/Lamina_001.png, Lamina_002.png, etc.: imágenes listas para el documento, con ancho uniforme y resolución de 300 DPI.
- laminas/Lamina_001.drawio, etc.: cada lámina también está disponible de manera independiente y editable.
- VISTA_ACOPLADA.html: las piezas colocadas una debajo de otra, sin espacios, para comprobar la continuidad.

La cantidad de láminas, sus dimensiones y su orden se registran en MANIFIESTO_LAMINAS.json. Se ofrece la cobertura exhaustiva del código propio de la aplicación, por lo que la cantidad de piezas es considerable.

## Insertar en Word

1. Insertar los PNG en su orden numérico.
2. Dar a todas las imágenes exactamente el mismo ancho, por ejemplo 17 cm.
3. Conservar la relación de aspecto y no recortar ni agregar márgenes a una pieza aislada.
4. Usar imágenes en línea con el texto. Si se desea una composición continua, establecer en cero el espacio anterior y posterior de los párrafos que contienen las imágenes.
5. Mantener las leyendas de figuras fuera de las imágenes.

Los cortes conservan las coordenadas de las conexiones y no atraviesan los caracteres. Una clase extensa puede continuar en la siguiente lámina: su caja y sus líneas se acoplan al reunir ambas piezas. No se repiten encabezados ni se agregan separadores a los cortes, porque eso alteraría el ensamblaje.

## Alcance técnico

El modelo contiene las clases, interfaces, tipos y enumeraciones declarados en el código propio del backend, Angular y Flutter. Los archivos Python con funciones se representan mediante el estereotipo UML «module», con operaciones estáticas; no se transforman en clases ficticias de negocio. También se representa el módulo local de entrenamiento ML.

Se incluyen atributos y operaciones declarados, con su visibilidad y tipos cuando existen. Las operaciones estáticas se subrayan. La herencia y realización internas tienen sus conectores; los tipos base externos al proyecto se identifican en el encabezado del clasificador. No se duplican miembros heredados ni se incorpora el código de las dependencias. Los detalles de funciones anónimas, funciones locales, pruebas, código generado e infraestructura del sistema operativo quedan fuera del modelo de clases de la aplicación.

Las firmas provienen de AST de Python, del compilador TypeScript y del analizador oficial de Dart. Las relaciones se contrastan con Graphify y referencias a tipos/importaciones. Los contratos HTTP se enlazan cuando la ruta del cliente coincide con un endpoint implementado. Los tipos estructurales extensos inferidos por TypeScript pueden mostrarse como object; su información completa se conserva en modelo_clases.json.

Las tablas SQL corresponden a los modelos de persistencia y al modelo de dominio. Este diagrama conserva los clasificadores reales de software y no inventa entidades ORM.

## Trazabilidad y validación

- modelo_clases.json: elementos, miembros, relaciones, evidencias y hashes de fuentes.
- INVENTARIO_CLASES_Y_METODOS.csv: clasificadores y cantidades de miembros.
- INVENTARIO_OPERACIONES.csv: firmas y ubicaciones de todas las operaciones representadas.
- INVENTARIO_ATRIBUTOS.csv: atributos y sus ubicaciones.
- VALIDACION.json: comprobaciones de fuentes, XML, cobertura, ajuste del texto y reconstrucción de las láminas.

El documento Word y el código funcional no se modifican. No se ejecutan comandos Git ni se realiza un despliegue.
