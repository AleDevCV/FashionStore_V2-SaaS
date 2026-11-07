# CU06 - Administrar catálogo de prendas

Esta versión utiliza los iconos de actor, interfaz, control y entidad, con mensajes de comunicación numerados individualmente. No utiliza etiquetas de métodos HTTP ni agrupa crear, editar y consultar en una sola comunicación.

## Archivos

- `CU06_Robustez_Numerada.drawio`: archivo editable con cuatro páginas: general, categorías, temporadas/colecciones y prendas/variantes.
- `JScript_Generar_Robustez_CU06.js`: script autocontenido para Enterprise Architect, con las mismas cuatro vistas y la misma numeración.
- `CU06_Robustez_Numerada_*.svg` y `.png`: exportaciones de cada vista. Los PNG conservan el tamaño completo y metadatos de 300 ppp.
- `MENSAJES_CU06.csv`: número, acción, origen, destino, mensaje y referencias al código.
- `CU06_Robustez_Numerada_Modelo.json`: modelo común, geometría y fuentes verificables.
- `CU06_Robustez_Numerada_Validacion.json` y `VALIDACION_JSCRIPT.json`: resultados de validación.

## Lectura del diagrama

Los números 1 a 173 son únicos y consecutivos en la vista general. Identifican el recorrido de 15 acciones. Las vistas por bloque conservan los mismos números; por eso una vista parcial puede tener saltos cuando omite mensajes de otro bloque.

Cada renglón representa un mensaje independiente. La flecha pequeña indica su dirección. Las invocaciones aparecen sobre el enlace y los retornos debajo. Los mensajes verdes son respuestas; los negros corresponden a consulta o interacción del actor, los azules a solicitudes de modificación y los rojos a escrituras de datos. La bitácora y otras escrituras sin un valor recuperado no reciben retornos artificiales.

Una operación comienza con la acción del actor, continúa en la interfaz y el control, consulta o modifica las entidades y vuelve a la interfaz cuando corresponde. Los escenarios de creación, modificación y baja son alternativas de uso; no se afirma que un usuario siempre los ejecute todos seguidos.

## Correspondencia con la implementación

El actor del recorrido principal es el Administrador de empresa, que puede ejecutar las operaciones actuales de catálogo. La ficha documental también incluye al responsable de inventario, pero el acceso web de escritura de prendas todavía está restringido al Administrador. El encargado de sucursal puede acceder al módulo de temporadas; no se incorpora un permiso de edición de prendas inexistente.

El control `Backend : Gestión del catálogo` agrupa responsabilidades de los routers y servicios de categorías, temporadas y prendas. Es un control de análisis, no una clase Python inventada ni un modelo ORM. Todos los métodos técnicos referenciados se comprobaron contra las definiciones reales del código mediante su estructura sintáctica.

Los mensajes de respuesta, por ejemplo «categoría creada», expresan datos devueltos. Los mensajes de presentación describen la interacción de la pantalla; no se presentan como funciones nuevas del proyecto.

Temporadas y colecciones comparten la tabla `temporada`. Material, medidas, precios, umbral mayorista y ofertas pertenecen a `prenda`. No se inventan entidades para esos atributos.

Se representa la creación inicial de variantes, su inventario y los movimientos de entrada. El movimiento actualiza el stock mediante el trigger existente; no se dibuja una comunicación directa de entidad a entidad. La edición de una prenda conserva sus variantes.

Se modela la persistencia de una URL de imagen ya obtenida. La subida opcional al proveedor de almacenamiento queda fuera de este recorrido de persistencia. Tampoco se añade edición posterior de variantes ni asignación de temporada desde el formulario web actual. No fue necesario incorporar operaciones futuras para representar estos recorridos.

La numeración indica un orden de lectura coherente. Angular puede descargar los catálogos auxiliares de forma concurrente. Las recargas posteriores reutilizan las consultas representadas, sin repetir cada callback de la pantalla.

## Abrir en draw.io

Abre el archivo `.drawio` y utiliza las pestañas inferiores para cambiar de vista. Para el documento, utiliza la vista del bloque correspondiente o exporta una selección del diagrama. La vista general conserva todo el contenido y requiere ampliación para leer los mensajes.

## Ejecutar en Enterprise Architect

1. Abre el proyecto de Enterprise Architect y selecciona un paquete de destino en el navegador del modelo.
2. Abre la ventana de scripting, crea un script de tipo **JScript** y pega el contenido completo de `JScript_Generar_Robustez_CU06.js`.
3. Ejecuta el script. Se creará un paquete nuevo `CU06 - Robustez numerada - <fecha interna>` con cuatro subpaquetes y diagramas de comunicación.
4. Utiliza la ventana **Script** para revisar el resultado. La vista general se abre al finalizar. En las propiedades del diagrama, activa **Show Collaboration Numbers** si tu configuración personal oculta la numeración.

El script no reemplaza diagramas existentes. Cada ejecución crea otro paquete. Crea primero las asociaciones y después los mensajes nativos `Collaboration`, siguiendo el convenio del JScript de VecinoMarket que se proporcionó como referencia. La vinculación de mensajes al enlace usa el mismo convenio interno de repositorio del ejemplo; las actualizaciones se limitan a los conectores nuevos del script.

La documentación de Sparx describe los [mensajes sobre asociaciones de comunicación](https://www.sparxsystems.com/enterprise_architect_user_guide/17.1/modeling_languages/message-communication.html), los atributos públicos del [conector](https://www.sparxsystems.com/enterprise_architect_user_guide/17.1/add-ins___scripting/connector2_2.html) y su [representación en el diagrama](https://www.sparxsystems.com/enterprise_architect_user_guide/17.1/add-ins___scripting/diagramlinks.html). Los campos internos PDATA utilizados por el ejemplo no constituyen una API pública documentada y pueden variar entre versiones de EA.

## Validación realizada

- Numeración completa y sin duplicados en la vista general; igualdad de mensajes y direcciones entre los dos formatos.
- Ausencia de comunicación directa entre entidades; cada entidad tiene un solo control interlocutor.
- Actores conectados únicamente a interfaces; ausencia de métodos HTTP en las etiquetas.
- XML `.drawio` válido contra el esquema oficial, identificadores y referencias íntegros.
- Métodos existentes comprobados por archivo y línea; hashes de las fuentes conservados.
- Exportaciones revisadas visualmente y filas de mensajes sin solapamientos.
- JScript ejecutado completo contra un sustituto local de la interfaz de EA: cuatro diagramas y 346 mensajes incluyendo las repeticiones de las vistas parciales.

No se ejecutó el script dentro de una sesión real de Enterprise Architect. La comprobación simulada valida la lógica de generación y las direcciones; no certifica el renderizado nativo ni la compatibilidad de campos internos con una versión concreta de EA.

La versión anterior permanece en la carpeta superior. No se modificó el documento Word, el código funcional ni la configuración de despliegue. No se ejecutaron comandos Git.
