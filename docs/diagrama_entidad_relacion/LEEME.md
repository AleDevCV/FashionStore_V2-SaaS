# Diagrama entidad-relación general de FashionStore

Archivo editable: `FashionStore_Diagrama_Entidad_Relacion_General.drawio`.

Vista general para el apartado **3.5. Diseño de la base de datos**. Representa 38 tablas principales y 65 relaciones en nueve áreas: administración SaaS; identidad y autorización; organización y clientes; catálogo; abastecimiento e inventario; reservas y ventas; pagos y comprobantes; cambios y notificaciones; sincronización, reportes y auditoría.

## Uso

Abrir el `.drawio` en diagrams.net mediante **Archivo → Abrir desde → Dispositivo**. Las tablas, campos y conectores son editables; el archivo no contiene una imagen incrustada como sustituto del modelo.

Para insertar en Word, utilizar el SVG de igual nombre, que conserva la nitidez al ampliar. También se incluye un PNG de alta resolución. La vista general es grande; para mostrar detalles en varias páginas se pueden exportar selecciones desde draw.io conservando una copia de la vista completa.

## Notación

- `PK`: campo de clave primaria. En tablas asociativas, varios campos forman una misma clave primaria compuesta.
- `FK`: campo que participa en una clave foránea.
- `PK/FK`: campo que cumple ambas funciones.
- `?` junto al tipo: la columna admite `NULL` en el esquema físico.
- Dos barras: exactamente uno; círculo y barra: cero o uno; círculo y pata de cuervo: cero o muchos.

La obligatoriedad del extremo padre se obtiene de la nulabilidad de la clave foránea. La multiplicidad del extremo hijo se obtiene de sus claves e índices únicos. Por ejemplo, una empresa puede tener cero o una suscripción registrada, y una reserva puede estar asociada como máximo con una venta. Las reglas de negocio pueden exigir condiciones adicionales a las expresadas por estas restricciones físicas.

## Alcance y correspondencia con el SQL

La fuente es `docs/diseno_fisico_base_datos/INVENTARIO_ORIGEN.json`, obtenida de la base PostgreSQL real y contrastada mediante restauración del SQL completo. Los campos mostrados son una selección: todas las claves primarias y foráneas de las tablas incluidas, más los atributos principales de negocio.

Para facilitar la lectura se muestra un solo conector cuando existen tanto una FK simple como otra compuesta con `tenant_id` para la misma relación. El campo conserva su nombre real; por ejemplo, `usuario.id_role`.

La pertenencia empresarial se indica mediante `tenant_id FK`. Se dibujan algunos enlaces directos con `empresa` y se omiten los repetitivos restantes, que quedan registrados en el modelo y el informe de validación. Las relaciones compuestas mantienen en la fuente los pares exactos de columnas, aunque el conector visual se establece entre tablas.

Las siete tablas técnicas excluidas de esta vista principal son `auditoria_identidad`, `cuenta_recuperacion`, `dispositivo_push`, `push_entrega`, `schema_migrations`, `stripe_event` y `usuario_token`. Su definición permanece en el SQL completo de 45 tablas. No se agregan relaciones hipotéticas; en particular, no se dibuja una FK directa entre `cuenta_global` y `cliente`, porque el esquema actual no la contiene.

Este es el modelo relacional central de PostgreSQL. IndexedDB y SQLite son almacenes locales complementarios; no se representan como tablas enlazadas mediante claves foráneas a la base central.

## Validación

`VALIDACION_ER.json` registra la correspondencia de cada conector con una restricción real, las cardinalidades, las relaciones resumidas, las huellas de los archivos y las comprobaciones de estructura del `.drawio`. Se verificaron identificadores únicos, ausencia de superposición entre tablas y conectores que no atraviesan tablas ajenas. Las vistas SVG y PNG se revisaron visualmente.

`MODELO_ER_VERIFICADO.json` conserva campos, tipos, claves y restricciones originales. Los archivos `layout.dot` y `layout.json` conservan el trazado reproducible utilizado para generar las vistas.
