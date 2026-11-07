# CU06 - Diagrama de secuencia

Una vista general editable con exactamente los ocho participantes del diagrama de robustez simplificado: Administrador de empresa, Administración del catálogo, Gestión del catálogo, Categoría, Temporada/Colección, Prenda, Variante y Bitácora.

La numeración se asigna de nuevo para incluir las alternativas. Los 37 mensajes principales de robustez conservan su correspondencia en el archivo de trazabilidad. Las seis acciones se presentan como recorridos independientes, no como pasos que todo usuario deba ejecutar obligatoriamente.

Los fragmentos alt y opt comienzan en Interfaz con un margen de 30 px. El loop comienza en Control y abarca únicamente Control y Variante, colocados contiguamente. El límite derecho de cada fragmento corresponde a su último participante afectado. En UML, un rectángulo continuo puede atravesar líneas de vida intermedias por su orden fijo; eso no añade interacciones con esas entidades.

El opt representa la confirmación de la edición; cancelar no invoca el backend. Los alt distinguen consultas vacías y validaciones fallidas de los recorridos aceptados. No se añaden entidades para catálogos auxiliares, imagen o inventario; se conserva el nivel de abstracción de robustez. La aplicación funcional y el Word no se modifican.
