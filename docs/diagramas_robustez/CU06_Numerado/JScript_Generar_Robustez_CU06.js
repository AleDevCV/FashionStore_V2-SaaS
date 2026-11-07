/* FashionStore CU06. Ejecutar como JScript dentro de Enterprise Architect.
 * Genera un paquete nuevo y cuatro diagramas sin modificar diagramas existentes.
 * Las llamadas nativas y sus referencias proceden del modelo compartido con draw.io.
 * El enlace Association se crea antes de sus mensajes Collaboration, como en el
 * JScript de referencia. PDATA4 conserva el número explícito y SeqNo su orden.
 * Los campos internos de EA se escriben solo para conectores recién creados.
 */

var CU06_MODEL = {
  "nodes": {
    "actor": {
      "kind": "actor",
      "name": "Administrador de empresa"
    },
    "b_cat": {
      "kind": "boundary",
      "name": "Frontend : Categorías",
      "source": "Parcial2_frontend-web/src/app/features/categorias/categorias.ts"
    },
    "b_temp": {
      "kind": "boundary",
      "name": "Frontend : Temporadas y colecciones",
      "source": "Parcial2_frontend-web/src/app/features/temporadas/temporadas.ts"
    },
    "b_pre": {
      "kind": "boundary",
      "name": "Frontend : Prendas y variantes",
      "source": "Parcial2_frontend-web/src/app/features/prendas/prendas.ts"
    },
    "control": {
      "kind": "control",
      "name": "Backend : Gestión del catálogo"
    },
    "categoria": {
      "kind": "entity",
      "name": "Categoría",
      "table": "categoria"
    },
    "temporada": {
      "kind": "entity",
      "name": "Temporada / colección",
      "table": "temporada"
    },
    "prenda": {
      "kind": "entity",
      "name": "Prenda",
      "table": "prenda"
    },
    "variante": {
      "kind": "entity",
      "name": "Variante de prenda",
      "table": "variante_prenda"
    },
    "talla": {
      "kind": "entity",
      "name": "Talla",
      "table": "talla"
    },
    "color": {
      "kind": "entity",
      "name": "Color",
      "table": "color"
    },
    "imagen": {
      "kind": "entity",
      "name": "Imagen de prenda",
      "table": "imagen_prenda"
    },
    "sucursal": {
      "kind": "entity",
      "name": "Sucursal",
      "table": "sucursal"
    },
    "inventario": {
      "kind": "entity",
      "name": "Inventario",
      "table": "inventario"
    },
    "movimiento": {
      "kind": "entity",
      "name": "Movimiento de inventario",
      "table": "movimiento_inventario"
    },
    "bitacora": {
      "kind": "entity",
      "name": "Bitácora",
      "table": "bitacora"
    }
  },
  "messages": [
    {
      "n": 1,
      "action": 1,
      "area": "categorias",
      "a": "actor",
      "b": "b_cat",
      "text": "Consultar categorías",
      "kind": "ui",
      "color": "#28343E",
      "source": null,
      "symbol": null
    },
    {
      "n": 2,
      "action": 1,
      "area": "categorias",
      "a": "b_cat",
      "b": "control",
      "text": "listar_categorias(estado)",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/routers/categorias.py",
      "symbol": "listar_categorias",
      "line": 46
    },
    {
      "n": 3,
      "action": 1,
      "area": "categorias",
      "a": "control",
      "b": "categoria",
      "text": "listar_categorias(estado)",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/services/categoria_service.py",
      "symbol": "listar_categorias",
      "line": 30
    },
    {
      "n": 4,
      "action": 1,
      "area": "categorias",
      "a": "categoria",
      "b": "control",
      "text": "lista de categorías",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 5,
      "action": 1,
      "area": "categorias",
      "a": "control",
      "b": "b_cat",
      "text": "categorías",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 6,
      "action": 1,
      "area": "categorias",
      "a": "b_cat",
      "b": "actor",
      "text": "Mostrar árbol de categorías",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 7,
      "action": 2,
      "area": "categorias",
      "a": "actor",
      "b": "b_cat",
      "text": "Registrar categoría",
      "kind": "ui",
      "color": "#28343E",
      "source": null,
      "symbol": null
    },
    {
      "n": 8,
      "action": 2,
      "area": "categorias",
      "a": "b_cat",
      "b": "control",
      "text": "crear_categoria(datos)",
      "kind": "invoke",
      "color": "#215D9C",
      "source": "Parcial2_backend/app/routers/categorias.py",
      "symbol": "crear_categoria",
      "line": 70
    },
    {
      "n": 9,
      "action": 2,
      "area": "categorias",
      "a": "control",
      "b": "categoria",
      "text": "existe_nombre(nombre)",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/services/categoria_service.py",
      "symbol": "existe_nombre",
      "line": 72
    },
    {
      "n": 10,
      "action": 2,
      "area": "categorias",
      "a": "categoria",
      "b": "control",
      "text": "nombre disponible",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 11,
      "action": 2,
      "area": "categorias",
      "a": "control",
      "b": "categoria",
      "text": "existe_categoria(id_padre) [si se indicó padre]",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/services/categoria_service.py",
      "symbol": "existe_categoria",
      "line": 98
    },
    {
      "n": 12,
      "action": 2,
      "area": "categorias",
      "a": "categoria",
      "b": "control",
      "text": "categoría padre válida",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 13,
      "action": 2,
      "area": "categorias",
      "a": "control",
      "b": "categoria",
      "text": "crear_categoria(datos)",
      "kind": "write",
      "color": "#AC3636",
      "source": "Parcial2_backend/app/services/categoria_service.py",
      "symbol": "crear_categoria",
      "line": 114
    },
    {
      "n": 14,
      "action": 2,
      "area": "categorias",
      "a": "categoria",
      "b": "control",
      "text": "id_categoria",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 15,
      "action": 2,
      "area": "categorias",
      "a": "control",
      "b": "bitacora",
      "text": "registrar_bitacora(categoria, alta)",
      "kind": "write",
      "color": "#AC3636",
      "source": "Parcial2_backend/app/services/bitacora_service.py",
      "symbol": "registrar_bitacora",
      "line": 65
    },
    {
      "n": 16,
      "action": 2,
      "area": "categorias",
      "a": "control",
      "b": "categoria",
      "text": "obtener_categoria(id_categoria)",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/services/categoria_service.py",
      "symbol": "obtener_categoria",
      "line": 57
    },
    {
      "n": 17,
      "action": 2,
      "area": "categorias",
      "a": "categoria",
      "b": "control",
      "text": "categoría creada",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 18,
      "action": 2,
      "area": "categorias",
      "a": "control",
      "b": "b_cat",
      "text": "categoría creada",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 19,
      "action": 2,
      "area": "categorias",
      "a": "b_cat",
      "b": "actor",
      "text": "Mostrar categoría registrada",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 20,
      "action": 3,
      "area": "categorias",
      "a": "actor",
      "b": "b_cat",
      "text": "Editar categoría",
      "kind": "ui",
      "color": "#28343E",
      "source": null,
      "symbol": null
    },
    {
      "n": 21,
      "action": 3,
      "area": "categorias",
      "a": "b_cat",
      "b": "control",
      "text": "actualizar_categoria(id_categoria, cambios)",
      "kind": "invoke",
      "color": "#215D9C",
      "source": "Parcial2_backend/app/routers/categorias.py",
      "symbol": "actualizar_categoria",
      "line": 135
    },
    {
      "n": 22,
      "action": 3,
      "area": "categorias",
      "a": "control",
      "b": "categoria",
      "text": "obtener_categoria(id_categoria)",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/services/categoria_service.py",
      "symbol": "obtener_categoria",
      "line": 57
    },
    {
      "n": 23,
      "action": 3,
      "area": "categorias",
      "a": "categoria",
      "b": "control",
      "text": "categoría actual",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 24,
      "action": 3,
      "area": "categorias",
      "a": "control",
      "b": "categoria",
      "text": "existe_nombre(nombre, excluir_id) [si cambia nombre]",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/services/categoria_service.py",
      "symbol": "existe_nombre",
      "line": 72
    },
    {
      "n": 25,
      "action": 3,
      "area": "categorias",
      "a": "categoria",
      "b": "control",
      "text": "nombre válido",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 26,
      "action": 3,
      "area": "categorias",
      "a": "control",
      "b": "categoria",
      "text": "existe_categoria(id_padre) [si cambia padre]",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/services/categoria_service.py",
      "symbol": "existe_categoria",
      "line": 98
    },
    {
      "n": 27,
      "action": 3,
      "area": "categorias",
      "a": "categoria",
      "b": "control",
      "text": "padre válido",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 28,
      "action": 3,
      "area": "categorias",
      "a": "control",
      "b": "categoria",
      "text": "actualizar_categoria(id_categoria, cambios)",
      "kind": "write",
      "color": "#AC3636",
      "source": "Parcial2_backend/app/services/categoria_service.py",
      "symbol": "actualizar_categoria",
      "line": 135
    },
    {
      "n": 29,
      "action": 3,
      "area": "categorias",
      "a": "control",
      "b": "bitacora",
      "text": "registrar_bitacora(categoria, modificación)",
      "kind": "write",
      "color": "#AC3636",
      "source": "Parcial2_backend/app/services/bitacora_service.py",
      "symbol": "registrar_bitacora",
      "line": 65
    },
    {
      "n": 30,
      "action": 3,
      "area": "categorias",
      "a": "control",
      "b": "categoria",
      "text": "obtener_categoria(id_categoria)",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/services/categoria_service.py",
      "symbol": "obtener_categoria",
      "line": 57
    },
    {
      "n": 31,
      "action": 3,
      "area": "categorias",
      "a": "categoria",
      "b": "control",
      "text": "categoría actualizada",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 32,
      "action": 3,
      "area": "categorias",
      "a": "control",
      "b": "b_cat",
      "text": "categoría actualizada",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 33,
      "action": 3,
      "area": "categorias",
      "a": "b_cat",
      "b": "actor",
      "text": "Mostrar cambios guardados",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 34,
      "action": 4,
      "area": "categorias",
      "a": "actor",
      "b": "b_cat",
      "text": "Inhabilitar categoría",
      "kind": "ui",
      "color": "#28343E",
      "source": null,
      "symbol": null
    },
    {
      "n": 35,
      "action": 4,
      "area": "categorias",
      "a": "b_cat",
      "b": "control",
      "text": "inhabilitar_categoria(id_categoria)",
      "kind": "invoke",
      "color": "#215D9C",
      "source": "Parcial2_backend/app/routers/categorias.py",
      "symbol": "inhabilitar_categoria",
      "line": 217
    },
    {
      "n": 36,
      "action": 4,
      "area": "categorias",
      "a": "control",
      "b": "categoria",
      "text": "obtener_categoria(id_categoria)",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/services/categoria_service.py",
      "symbol": "obtener_categoria",
      "line": 57
    },
    {
      "n": 37,
      "action": 4,
      "area": "categorias",
      "a": "categoria",
      "b": "control",
      "text": "categoría activa",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 38,
      "action": 4,
      "area": "categorias",
      "a": "control",
      "b": "categoria",
      "text": "tiene_subcategorias(id_categoria)",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/services/categoria_service.py",
      "symbol": "tiene_subcategorias",
      "line": 176
    },
    {
      "n": 39,
      "action": 4,
      "area": "categorias",
      "a": "categoria",
      "b": "control",
      "text": "sin subcategorías activas",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 40,
      "action": 4,
      "area": "categorias",
      "a": "control",
      "b": "categoria",
      "text": "inhabilitar_categoria(id_categoria)",
      "kind": "write",
      "color": "#AC3636",
      "source": "Parcial2_backend/app/services/categoria_service.py",
      "symbol": "inhabilitar_categoria",
      "line": 156
    },
    {
      "n": 41,
      "action": 4,
      "area": "categorias",
      "a": "control",
      "b": "bitacora",
      "text": "registrar_bitacora(categoria, baja lógica)",
      "kind": "write",
      "color": "#AC3636",
      "source": "Parcial2_backend/app/services/bitacora_service.py",
      "symbol": "registrar_bitacora",
      "line": 65
    },
    {
      "n": 42,
      "action": 4,
      "area": "categorias",
      "a": "control",
      "b": "b_cat",
      "text": "inhabilitación confirmada",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 43,
      "action": 4,
      "area": "categorias",
      "a": "b_cat",
      "b": "actor",
      "text": "Mostrar categoría inactiva",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 44,
      "action": 5,
      "area": "categorias",
      "a": "actor",
      "b": "b_cat",
      "text": "Reactivar categoría",
      "kind": "ui",
      "color": "#28343E",
      "source": null,
      "symbol": null
    },
    {
      "n": 45,
      "action": 5,
      "area": "categorias",
      "a": "b_cat",
      "b": "control",
      "text": "actualizar_categoria(id_categoria, estado='Activo')",
      "kind": "invoke",
      "color": "#215D9C",
      "source": "Parcial2_backend/app/routers/categorias.py",
      "symbol": "actualizar_categoria",
      "line": 135
    },
    {
      "n": 46,
      "action": 5,
      "area": "categorias",
      "a": "control",
      "b": "categoria",
      "text": "obtener_categoria(id_categoria)",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/services/categoria_service.py",
      "symbol": "obtener_categoria",
      "line": 57
    },
    {
      "n": 47,
      "action": 5,
      "area": "categorias",
      "a": "categoria",
      "b": "control",
      "text": "categoría actual",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 48,
      "action": 5,
      "area": "categorias",
      "a": "control",
      "b": "categoria",
      "text": "actualizar_categoria(id_categoria, estado='Activo')",
      "kind": "write",
      "color": "#AC3636",
      "source": "Parcial2_backend/app/services/categoria_service.py",
      "symbol": "actualizar_categoria",
      "line": 135
    },
    {
      "n": 49,
      "action": 5,
      "area": "categorias",
      "a": "control",
      "b": "bitacora",
      "text": "registrar_bitacora(categoria, modificación)",
      "kind": "write",
      "color": "#AC3636",
      "source": "Parcial2_backend/app/services/bitacora_service.py",
      "symbol": "registrar_bitacora",
      "line": 65
    },
    {
      "n": 50,
      "action": 5,
      "area": "categorias",
      "a": "control",
      "b": "categoria",
      "text": "obtener_categoria(id_categoria)",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/services/categoria_service.py",
      "symbol": "obtener_categoria",
      "line": 57
    },
    {
      "n": 51,
      "action": 5,
      "area": "categorias",
      "a": "categoria",
      "b": "control",
      "text": "categoría activa",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 52,
      "action": 5,
      "area": "categorias",
      "a": "control",
      "b": "b_cat",
      "text": "reactivación confirmada",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 53,
      "action": 5,
      "area": "categorias",
      "a": "b_cat",
      "b": "actor",
      "text": "Mostrar categoría reactivada",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 54,
      "action": 6,
      "area": "temporadas",
      "a": "actor",
      "b": "b_temp",
      "text": "Consultar temporadas y colecciones",
      "kind": "ui",
      "color": "#28343E",
      "source": null,
      "symbol": null
    },
    {
      "n": 55,
      "action": 6,
      "area": "temporadas",
      "a": "b_temp",
      "b": "control",
      "text": "listar_temporadas(búsqueda, estado, vigencia)",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/routers/temporadas.py",
      "symbol": "listar_temporadas",
      "line": 39
    },
    {
      "n": 56,
      "action": 6,
      "area": "temporadas",
      "a": "control",
      "b": "temporada",
      "text": "listar_temporadas(filtros)",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/services/temporada_service.py",
      "symbol": "listar_temporadas",
      "line": 46
    },
    {
      "n": 57,
      "action": 6,
      "area": "temporadas",
      "a": "temporada",
      "b": "control",
      "text": "temporadas y vigencias",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 58,
      "action": 6,
      "area": "temporadas",
      "a": "control",
      "b": "b_temp",
      "text": "temporadas",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 59,
      "action": 6,
      "area": "temporadas",
      "a": "b_temp",
      "b": "actor",
      "text": "Mostrar temporadas y colecciones",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 60,
      "action": 7,
      "area": "temporadas",
      "a": "actor",
      "b": "b_temp",
      "text": "Registrar temporada o colección",
      "kind": "ui",
      "color": "#28343E",
      "source": null,
      "symbol": null
    },
    {
      "n": 61,
      "action": 7,
      "area": "temporadas",
      "a": "b_temp",
      "b": "control",
      "text": "crear_temporada(datos)",
      "kind": "invoke",
      "color": "#215D9C",
      "source": "Parcial2_backend/app/routers/temporadas.py",
      "symbol": "crear_temporada",
      "line": 100
    },
    {
      "n": 62,
      "action": 7,
      "area": "temporadas",
      "a": "control",
      "b": "temporada",
      "text": "existe_nombre_temporada(nombre)",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/services/temporada_service.py",
      "symbol": "existe_nombre_temporada",
      "line": 24
    },
    {
      "n": 63,
      "action": 7,
      "area": "temporadas",
      "a": "temporada",
      "b": "control",
      "text": "nombre disponible",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 64,
      "action": 7,
      "area": "temporadas",
      "a": "control",
      "b": "temporada",
      "text": "crear_temporada(datos) [fechas válidas]",
      "kind": "write",
      "color": "#AC3636",
      "source": "Parcial2_backend/app/services/temporada_service.py",
      "symbol": "crear_temporada",
      "line": 131
    },
    {
      "n": 65,
      "action": 7,
      "area": "temporadas",
      "a": "temporada",
      "b": "control",
      "text": "temporada creada",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 66,
      "action": 7,
      "area": "temporadas",
      "a": "control",
      "b": "bitacora",
      "text": "registrar_bitacora(temporada, alta)",
      "kind": "write",
      "color": "#AC3636",
      "source": "Parcial2_backend/app/services/bitacora_service.py",
      "symbol": "registrar_bitacora",
      "line": 65
    },
    {
      "n": 67,
      "action": 7,
      "area": "temporadas",
      "a": "control",
      "b": "b_temp",
      "text": "temporada creada",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 68,
      "action": 7,
      "area": "temporadas",
      "a": "b_temp",
      "b": "actor",
      "text": "Mostrar temporada registrada",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 69,
      "action": 8,
      "area": "temporadas",
      "a": "actor",
      "b": "b_temp",
      "text": "Editar temporada o colección",
      "kind": "ui",
      "color": "#28343E",
      "source": null,
      "symbol": null
    },
    {
      "n": 70,
      "action": 8,
      "area": "temporadas",
      "a": "b_temp",
      "b": "control",
      "text": "actualizar_temporada(id_temporada, cambios)",
      "kind": "invoke",
      "color": "#215D9C",
      "source": "Parcial2_backend/app/routers/temporadas.py",
      "symbol": "actualizar_temporada",
      "line": 122
    },
    {
      "n": 71,
      "action": 8,
      "area": "temporadas",
      "a": "control",
      "b": "temporada",
      "text": "obtener_temporada_por_id(id_temporada)",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/services/temporada_service.py",
      "symbol": "obtener_temporada_por_id",
      "line": 107
    },
    {
      "n": 72,
      "action": 8,
      "area": "temporadas",
      "a": "temporada",
      "b": "control",
      "text": "temporada actual",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 73,
      "action": 8,
      "area": "temporadas",
      "a": "control",
      "b": "temporada",
      "text": "existe_nombre_temporada(nombre, excluir_id) [si cambia nombre]",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/services/temporada_service.py",
      "symbol": "existe_nombre_temporada",
      "line": 24
    },
    {
      "n": 74,
      "action": 8,
      "area": "temporadas",
      "a": "temporada",
      "b": "control",
      "text": "nombre disponible",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 75,
      "action": 8,
      "area": "temporadas",
      "a": "control",
      "b": "temporada",
      "text": "actualizar_temporada(id_temporada, cambios) [fechas válidas]",
      "kind": "write",
      "color": "#AC3636",
      "source": "Parcial2_backend/app/services/temporada_service.py",
      "symbol": "actualizar_temporada",
      "line": 186
    },
    {
      "n": 76,
      "action": 8,
      "area": "temporadas",
      "a": "control",
      "b": "bitacora",
      "text": "registrar_bitacora(temporada, modificación)",
      "kind": "write",
      "color": "#AC3636",
      "source": "Parcial2_backend/app/services/bitacora_service.py",
      "symbol": "registrar_bitacora",
      "line": 65
    },
    {
      "n": 77,
      "action": 8,
      "area": "temporadas",
      "a": "control",
      "b": "temporada",
      "text": "obtener_temporada_por_id(id_temporada)",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/services/temporada_service.py",
      "symbol": "obtener_temporada_por_id",
      "line": 107
    },
    {
      "n": 78,
      "action": 8,
      "area": "temporadas",
      "a": "temporada",
      "b": "control",
      "text": "temporada actualizada",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 79,
      "action": 8,
      "area": "temporadas",
      "a": "control",
      "b": "b_temp",
      "text": "temporada actualizada",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 80,
      "action": 8,
      "area": "temporadas",
      "a": "b_temp",
      "b": "actor",
      "text": "Mostrar cambios guardados",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 81,
      "action": 9,
      "area": "temporadas",
      "a": "actor",
      "b": "b_temp",
      "text": "Eliminar temporada o colección",
      "kind": "ui",
      "color": "#28343E",
      "source": null,
      "symbol": null
    },
    {
      "n": 82,
      "action": 9,
      "area": "temporadas",
      "a": "b_temp",
      "b": "control",
      "text": "eliminar_temporada(id_temporada)",
      "kind": "invoke",
      "color": "#215D9C",
      "source": "Parcial2_backend/app/routers/temporadas.py",
      "symbol": "eliminar_temporada",
      "line": 146
    },
    {
      "n": 83,
      "action": 9,
      "area": "temporadas",
      "a": "control",
      "b": "temporada",
      "text": "obtener_temporada_por_id(id_temporada)",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/services/temporada_service.py",
      "symbol": "obtener_temporada_por_id",
      "line": 107
    },
    {
      "n": 84,
      "action": 9,
      "area": "temporadas",
      "a": "temporada",
      "b": "control",
      "text": "temporada existente",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 85,
      "action": 9,
      "area": "temporadas",
      "a": "control",
      "b": "temporada",
      "text": "eliminar_temporada(id_temporada)",
      "kind": "write",
      "color": "#AC3636",
      "source": "Parcial2_backend/app/services/temporada_service.py",
      "symbol": "eliminar_temporada",
      "line": 254
    },
    {
      "n": 86,
      "action": 9,
      "area": "temporadas",
      "a": "control",
      "b": "bitacora",
      "text": "registrar_bitacora(temporada, eliminación)",
      "kind": "write",
      "color": "#AC3636",
      "source": "Parcial2_backend/app/services/bitacora_service.py",
      "symbol": "registrar_bitacora",
      "line": 65
    },
    {
      "n": 87,
      "action": 9,
      "area": "temporadas",
      "a": "control",
      "b": "b_temp",
      "text": "eliminación confirmada",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 88,
      "action": 9,
      "area": "temporadas",
      "a": "b_temp",
      "b": "actor",
      "text": "Mostrar temporada eliminada",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 89,
      "action": 10,
      "area": "prendas",
      "a": "actor",
      "b": "b_pre",
      "text": "Consultar prendas y preparar formulario",
      "kind": "ui",
      "color": "#28343E",
      "source": null,
      "symbol": null
    },
    {
      "n": 90,
      "action": 10,
      "area": "prendas",
      "a": "b_pre",
      "b": "control",
      "text": "listar_prendas(búsqueda, categoría, género, estado)",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/routers/prendas.py",
      "symbol": "listar_prendas",
      "line": 101
    },
    {
      "n": 91,
      "action": 10,
      "area": "prendas",
      "a": "control",
      "b": "prenda",
      "text": "listar_prendas(filtros)",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/services/prenda_service.py",
      "symbol": "listar_prendas",
      "line": 58
    },
    {
      "n": 92,
      "action": 10,
      "area": "prendas",
      "a": "prenda",
      "b": "control",
      "text": "lista de prendas",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 93,
      "action": 10,
      "area": "prendas",
      "a": "control",
      "b": "b_pre",
      "text": "prendas",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 94,
      "action": 10,
      "area": "prendas",
      "a": "b_pre",
      "b": "control",
      "text": "listar_categorias(estado)",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/routers/categorias.py",
      "symbol": "listar_categorias",
      "line": 46
    },
    {
      "n": 95,
      "action": 10,
      "area": "prendas",
      "a": "control",
      "b": "categoria",
      "text": "listar_categorias(estado)",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/services/categoria_service.py",
      "symbol": "listar_categorias",
      "line": 30
    },
    {
      "n": 96,
      "action": 10,
      "area": "prendas",
      "a": "categoria",
      "b": "control",
      "text": "categorías disponibles",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 97,
      "action": 10,
      "area": "prendas",
      "a": "control",
      "b": "b_pre",
      "text": "categorías",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 98,
      "action": 10,
      "area": "prendas",
      "a": "b_pre",
      "b": "control",
      "text": "listar_tallas()",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/routers/prendas.py",
      "symbol": "listar_tallas",
      "line": 50
    },
    {
      "n": 99,
      "action": 10,
      "area": "prendas",
      "a": "control",
      "b": "talla",
      "text": "listar_tallas()",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/services/prenda_service.py",
      "symbol": "listar_tallas",
      "line": 462
    },
    {
      "n": 100,
      "action": 10,
      "area": "prendas",
      "a": "talla",
      "b": "control",
      "text": "tallas disponibles",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 101,
      "action": 10,
      "area": "prendas",
      "a": "control",
      "b": "b_pre",
      "text": "tallas",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 102,
      "action": 10,
      "area": "prendas",
      "a": "b_pre",
      "b": "control",
      "text": "listar_colores()",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/routers/prendas.py",
      "symbol": "listar_colores",
      "line": 64
    },
    {
      "n": 103,
      "action": 10,
      "area": "prendas",
      "a": "control",
      "b": "color",
      "text": "listar_colores()",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/services/prenda_service.py",
      "symbol": "listar_colores",
      "line": 477
    },
    {
      "n": 104,
      "action": 10,
      "area": "prendas",
      "a": "color",
      "b": "control",
      "text": "colores disponibles",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 105,
      "action": 10,
      "area": "prendas",
      "a": "control",
      "b": "b_pre",
      "text": "colores",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 106,
      "action": 10,
      "area": "prendas",
      "a": "b_pre",
      "b": "actor",
      "text": "Mostrar prendas y opciones del formulario",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 107,
      "action": 11,
      "area": "prendas",
      "a": "actor",
      "b": "b_pre",
      "text": "Registrar prenda y variantes",
      "kind": "ui",
      "color": "#28343E",
      "source": null,
      "symbol": null
    },
    {
      "n": 108,
      "action": 11,
      "area": "prendas",
      "a": "b_pre",
      "b": "control",
      "text": "crear_prenda(datos, variantes, precios, ofertas)",
      "kind": "invoke",
      "color": "#215D9C",
      "source": "Parcial2_backend/app/routers/prendas.py",
      "symbol": "crear_prenda",
      "line": 170
    },
    {
      "n": 109,
      "action": 11,
      "area": "prendas",
      "a": "control",
      "b": "prenda",
      "text": "existe_sku(sku)",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/services/prenda_service.py",
      "symbol": "existe_sku",
      "line": 178
    },
    {
      "n": 110,
      "action": 11,
      "area": "prendas",
      "a": "prenda",
      "b": "control",
      "text": "SKU disponible",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 111,
      "action": 11,
      "area": "prendas",
      "a": "control",
      "b": "categoria",
      "text": "existe_categoria(id_categoria)",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/services/categoria_service.py",
      "symbol": "existe_categoria",
      "line": 98
    },
    {
      "n": 112,
      "action": 11,
      "area": "prendas",
      "a": "categoria",
      "b": "control",
      "text": "categoría válida",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 113,
      "action": 11,
      "area": "prendas",
      "a": "control",
      "b": "prenda",
      "text": "crear_prenda(datos maestros y comerciales)",
      "kind": "write",
      "color": "#AC3636",
      "source": "Parcial2_backend/app/services/prenda_service.py",
      "symbol": "crear_prenda",
      "line": 217
    },
    {
      "n": 114,
      "action": 11,
      "area": "prendas",
      "a": "prenda",
      "b": "control",
      "text": "id_prenda",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 115,
      "action": 11,
      "area": "prendas",
      "a": "control",
      "b": "imagen",
      "text": "Guardar imagen principal [si se indicó URL]",
      "kind": "write",
      "color": "#AC3636",
      "source": "Parcial2_backend/app/services/prenda_service.py",
      "symbol": "crear_prenda",
      "line": 217
    },
    {
      "n": 116,
      "action": 11,
      "area": "prendas",
      "a": "control",
      "b": "sucursal",
      "text": "_listar_ids_sucursales()",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/services/prenda_service.py",
      "symbol": "_listar_ids_sucursales",
      "line": 350
    },
    {
      "n": 117,
      "action": 11,
      "area": "prendas",
      "a": "sucursal",
      "b": "control",
      "text": "sucursales activas autorizadas",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 118,
      "action": 11,
      "area": "prendas",
      "a": "control",
      "b": "variante",
      "text": "_crear_variante(talla, color_ids, SKU) [por variante]",
      "kind": "write",
      "color": "#AC3636",
      "source": "Parcial2_backend/app/services/prenda_service.py",
      "symbol": "_crear_variante",
      "line": 288
    },
    {
      "n": 119,
      "action": 11,
      "area": "prendas",
      "a": "variante",
      "b": "control",
      "text": "id_variante",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 120,
      "action": 11,
      "area": "prendas",
      "a": "control",
      "b": "inventario",
      "text": "Inicializar fila con stock=0 [por variante y sucursal]",
      "kind": "write",
      "color": "#AC3636",
      "source": "Parcial2_backend/app/services/prenda_service.py",
      "symbol": "_crear_variante",
      "line": 288
    },
    {
      "n": 121,
      "action": 11,
      "area": "prendas",
      "a": "control",
      "b": "movimiento",
      "text": "Registrar Entrada inicial [stock inicial > 0]",
      "kind": "write",
      "color": "#AC3636",
      "source": "Parcial2_backend/app/services/prenda_service.py",
      "symbol": "_crear_variante",
      "line": 288
    },
    {
      "n": 122,
      "action": 11,
      "area": "prendas",
      "a": "control",
      "b": "bitacora",
      "text": "registrar_bitacora(prenda, alta)",
      "kind": "write",
      "color": "#AC3636",
      "source": "Parcial2_backend/app/services/bitacora_service.py",
      "symbol": "registrar_bitacora",
      "line": 65
    },
    {
      "n": 123,
      "action": 11,
      "area": "prendas",
      "a": "control",
      "b": "prenda",
      "text": "obtener_prenda(id_prenda)",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/services/prenda_service.py",
      "symbol": "obtener_prenda",
      "line": 114
    },
    {
      "n": 124,
      "action": 11,
      "area": "prendas",
      "a": "prenda",
      "b": "control",
      "text": "datos maestros creados",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 125,
      "action": 11,
      "area": "prendas",
      "a": "control",
      "b": "variante",
      "text": "listar_variantes(id_prenda)",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/services/prenda_service.py",
      "symbol": "listar_variantes",
      "line": 136
    },
    {
      "n": 126,
      "action": 11,
      "area": "prendas",
      "a": "variante",
      "b": "control",
      "text": "variantes y existencias",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 127,
      "action": 11,
      "area": "prendas",
      "a": "control",
      "b": "b_pre",
      "text": "prenda creada con variantes",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 128,
      "action": 11,
      "area": "prendas",
      "a": "b_pre",
      "b": "actor",
      "text": "Mostrar prenda registrada",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 129,
      "action": 12,
      "area": "prendas",
      "a": "actor",
      "b": "b_pre",
      "text": "Editar prenda, precios y ofertas",
      "kind": "ui",
      "color": "#28343E",
      "source": null,
      "symbol": null
    },
    {
      "n": 130,
      "action": 12,
      "area": "prendas",
      "a": "b_pre",
      "b": "control",
      "text": "actualizar_prenda(id_prenda, cambios)",
      "kind": "invoke",
      "color": "#215D9C",
      "source": "Parcial2_backend/app/routers/prendas.py",
      "symbol": "actualizar_prenda",
      "line": 274
    },
    {
      "n": 131,
      "action": 12,
      "area": "prendas",
      "a": "control",
      "b": "prenda",
      "text": "obtener_prenda(id_prenda, con_variantes=False)",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/services/prenda_service.py",
      "symbol": "obtener_prenda",
      "line": 114
    },
    {
      "n": 132,
      "action": 12,
      "area": "prendas",
      "a": "prenda",
      "b": "control",
      "text": "prenda actual",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 133,
      "action": 12,
      "area": "prendas",
      "a": "control",
      "b": "prenda",
      "text": "existe_sku(sku, excluir_id) [si cambia SKU]",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/services/prenda_service.py",
      "symbol": "existe_sku",
      "line": 178
    },
    {
      "n": 134,
      "action": 12,
      "area": "prendas",
      "a": "prenda",
      "b": "control",
      "text": "SKU disponible",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 135,
      "action": 12,
      "area": "prendas",
      "a": "control",
      "b": "categoria",
      "text": "existe_categoria(id_categoria) [si cambia categoría]",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/services/categoria_service.py",
      "symbol": "existe_categoria",
      "line": 98
    },
    {
      "n": 136,
      "action": 12,
      "area": "prendas",
      "a": "categoria",
      "b": "control",
      "text": "categoría válida",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 137,
      "action": 12,
      "area": "prendas",
      "a": "control",
      "b": "prenda",
      "text": "actualizar_prenda(id_prenda, atributos, precios, ofertas)",
      "kind": "write",
      "color": "#AC3636",
      "source": "Parcial2_backend/app/services/prenda_service.py",
      "symbol": "actualizar_prenda",
      "line": 363
    },
    {
      "n": 138,
      "action": 12,
      "area": "prendas",
      "a": "control",
      "b": "imagen",
      "text": "_reemplazar_imagen_principal(id_prenda, url_imagen) [si cambia URL]",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/services/prenda_service.py",
      "symbol": "_reemplazar_imagen_principal",
      "line": 396
    },
    {
      "n": 139,
      "action": 12,
      "area": "prendas",
      "a": "imagen",
      "b": "control",
      "text": "referencia actual comprobada",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 140,
      "action": 12,
      "area": "prendas",
      "a": "control",
      "b": "imagen",
      "text": "Conservar anterior como secundaria y guardar principal [si difiere]",
      "kind": "write",
      "color": "#AC3636",
      "source": "Parcial2_backend/app/services/prenda_service.py",
      "symbol": "_reemplazar_imagen_principal",
      "line": 396
    },
    {
      "n": 141,
      "action": 12,
      "area": "prendas",
      "a": "control",
      "b": "bitacora",
      "text": "registrar_bitacora(prenda, modificación)",
      "kind": "write",
      "color": "#AC3636",
      "source": "Parcial2_backend/app/services/bitacora_service.py",
      "symbol": "registrar_bitacora",
      "line": 65
    },
    {
      "n": 142,
      "action": 12,
      "area": "prendas",
      "a": "control",
      "b": "prenda",
      "text": "obtener_prenda(id_prenda)",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/services/prenda_service.py",
      "symbol": "obtener_prenda",
      "line": 114
    },
    {
      "n": 143,
      "action": 12,
      "area": "prendas",
      "a": "prenda",
      "b": "control",
      "text": "prenda actualizada",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 144,
      "action": 12,
      "area": "prendas",
      "a": "control",
      "b": "variante",
      "text": "listar_variantes(id_prenda)",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/services/prenda_service.py",
      "symbol": "listar_variantes",
      "line": 136
    },
    {
      "n": 145,
      "action": 12,
      "area": "prendas",
      "a": "variante",
      "b": "control",
      "text": "variantes conservadas",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 146,
      "action": 12,
      "area": "prendas",
      "a": "control",
      "b": "b_pre",
      "text": "prenda actualizada",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 147,
      "action": 12,
      "area": "prendas",
      "a": "b_pre",
      "b": "actor",
      "text": "Mostrar cambios guardados",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 148,
      "action": 13,
      "area": "prendas",
      "a": "actor",
      "b": "b_pre",
      "text": "Inhabilitar prenda",
      "kind": "ui",
      "color": "#28343E",
      "source": null,
      "symbol": null
    },
    {
      "n": 149,
      "action": 13,
      "area": "prendas",
      "a": "b_pre",
      "b": "control",
      "text": "inhabilitar_prenda(id_prenda)",
      "kind": "invoke",
      "color": "#215D9C",
      "source": "Parcial2_backend/app/routers/prendas.py",
      "symbol": "inhabilitar_prenda",
      "line": 362
    },
    {
      "n": 150,
      "action": 13,
      "area": "prendas",
      "a": "control",
      "b": "prenda",
      "text": "obtener_prenda(id_prenda, con_variantes=False)",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/services/prenda_service.py",
      "symbol": "obtener_prenda",
      "line": 114
    },
    {
      "n": 151,
      "action": 13,
      "area": "prendas",
      "a": "prenda",
      "b": "control",
      "text": "prenda activa",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 152,
      "action": 13,
      "area": "prendas",
      "a": "control",
      "b": "prenda",
      "text": "inhabilitar_prenda(id_prenda)",
      "kind": "write",
      "color": "#AC3636",
      "source": "Parcial2_backend/app/services/prenda_service.py",
      "symbol": "inhabilitar_prenda",
      "line": 437
    },
    {
      "n": 153,
      "action": 13,
      "area": "prendas",
      "a": "control",
      "b": "bitacora",
      "text": "registrar_bitacora(prenda, baja lógica)",
      "kind": "write",
      "color": "#AC3636",
      "source": "Parcial2_backend/app/services/bitacora_service.py",
      "symbol": "registrar_bitacora",
      "line": 65
    },
    {
      "n": 154,
      "action": 13,
      "area": "prendas",
      "a": "control",
      "b": "b_pre",
      "text": "inhabilitación confirmada",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 155,
      "action": 13,
      "area": "prendas",
      "a": "b_pre",
      "b": "actor",
      "text": "Mostrar prenda inactiva",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 156,
      "action": 14,
      "area": "prendas",
      "a": "actor",
      "b": "b_pre",
      "text": "Reactivar prenda",
      "kind": "ui",
      "color": "#28343E",
      "source": null,
      "symbol": null
    },
    {
      "n": 157,
      "action": 14,
      "area": "prendas",
      "a": "b_pre",
      "b": "control",
      "text": "actualizar_prenda(id_prenda, estado='Activo')",
      "kind": "invoke",
      "color": "#215D9C",
      "source": "Parcial2_backend/app/routers/prendas.py",
      "symbol": "actualizar_prenda",
      "line": 274
    },
    {
      "n": 158,
      "action": 14,
      "area": "prendas",
      "a": "control",
      "b": "prenda",
      "text": "obtener_prenda(id_prenda, con_variantes=False)",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/services/prenda_service.py",
      "symbol": "obtener_prenda",
      "line": 114
    },
    {
      "n": 159,
      "action": 14,
      "area": "prendas",
      "a": "prenda",
      "b": "control",
      "text": "prenda actual",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 160,
      "action": 14,
      "area": "prendas",
      "a": "control",
      "b": "prenda",
      "text": "actualizar_prenda(id_prenda, estado='Activo')",
      "kind": "write",
      "color": "#AC3636",
      "source": "Parcial2_backend/app/services/prenda_service.py",
      "symbol": "actualizar_prenda",
      "line": 363
    },
    {
      "n": 161,
      "action": 14,
      "area": "prendas",
      "a": "control",
      "b": "bitacora",
      "text": "registrar_bitacora(prenda, modificación)",
      "kind": "write",
      "color": "#AC3636",
      "source": "Parcial2_backend/app/services/bitacora_service.py",
      "symbol": "registrar_bitacora",
      "line": 65
    },
    {
      "n": 162,
      "action": 14,
      "area": "prendas",
      "a": "control",
      "b": "prenda",
      "text": "obtener_prenda(id_prenda)",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/services/prenda_service.py",
      "symbol": "obtener_prenda",
      "line": 114
    },
    {
      "n": 163,
      "action": 14,
      "area": "prendas",
      "a": "prenda",
      "b": "control",
      "text": "prenda activa",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 164,
      "action": 14,
      "area": "prendas",
      "a": "control",
      "b": "variante",
      "text": "listar_variantes(id_prenda)",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/services/prenda_service.py",
      "symbol": "listar_variantes",
      "line": 136
    },
    {
      "n": 165,
      "action": 14,
      "area": "prendas",
      "a": "variante",
      "b": "control",
      "text": "variantes conservadas",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 166,
      "action": 14,
      "area": "prendas",
      "a": "control",
      "b": "b_pre",
      "text": "reactivación confirmada",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 167,
      "action": 14,
      "area": "prendas",
      "a": "b_pre",
      "b": "actor",
      "text": "Mostrar prenda reactivada",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 168,
      "action": 15,
      "area": "prendas",
      "a": "actor",
      "b": "b_pre",
      "text": "Intentar registrar un SKU existente",
      "kind": "ui",
      "color": "#28343E",
      "source": null,
      "symbol": null
    },
    {
      "n": 169,
      "action": 15,
      "area": "prendas",
      "a": "b_pre",
      "b": "control",
      "text": "crear_prenda(datos con SKU repetido)",
      "kind": "invoke",
      "color": "#215D9C",
      "source": "Parcial2_backend/app/routers/prendas.py",
      "symbol": "crear_prenda",
      "line": 170
    },
    {
      "n": 170,
      "action": 15,
      "area": "prendas",
      "a": "control",
      "b": "prenda",
      "text": "existe_sku(sku)",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/services/prenda_service.py",
      "symbol": "existe_sku",
      "line": 178
    },
    {
      "n": 171,
      "action": 15,
      "area": "prendas",
      "a": "prenda",
      "b": "control",
      "text": "SKU ya registrado",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 172,
      "action": 15,
      "area": "prendas",
      "a": "control",
      "b": "b_pre",
      "text": "rechazo: SKU duplicado",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 173,
      "action": 15,
      "area": "prendas",
      "a": "b_pre",
      "b": "actor",
      "text": "Mostrar validación sin registrar la prenda",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    }
  ],
  "views": [
    {
      "name": "CU06 - General numerado",
      "width": 6000,
      "height": 7728,
      "nodes": {
        "actor": {
          "x": 180,
          "y": 3774
        },
        "control": {
          "x": 3140,
          "y": 3774
        },
        "categoria": {
          "x": 5690,
          "y": 1066
        },
        "temporada": {
          "x": 5690,
          "y": 2406
        },
        "prenda": {
          "x": 5690,
          "y": 3570
        },
        "variante": {
          "x": 5690,
          "y": 4470
        },
        "talla": {
          "x": 5690,
          "y": 4930
        },
        "color": {
          "x": 5690,
          "y": 5258
        },
        "imagen": {
          "x": 5690,
          "y": 5674
        },
        "sucursal": {
          "x": 5690,
          "y": 6002
        },
        "inventario": {
          "x": 5690,
          "y": 6330
        },
        "movimiento": {
          "x": 5690,
          "y": 6614
        },
        "bitacora": {
          "x": 5690,
          "y": 7338
        },
        "b_cat": {
          "x": 1510,
          "y": 2822
        },
        "b_temp": {
          "x": 1510,
          "y": 3638
        },
        "b_pre": {
          "x": 1510,
          "y": 4630
        }
      },
      "groups": [
        {
          "pair": [
            "actor",
            "b_cat"
          ],
          "points": [
            [
              220,
              3774
            ],
            [
              340,
              2822
            ],
            [
              1445,
              2822
            ]
          ],
          "rows": [
            {
              "n": 1,
              "x": 820,
              "y": 2589,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 7,
              "x": 820,
              "y": 2633,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 20,
              "x": 820,
              "y": 2677,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 34,
              "x": 820,
              "y": 2721,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 44,
              "x": 820,
              "y": 2765,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 6,
              "x": 820,
              "y": 2882,
              "width": 1050,
              "height": 44,
              "forward": false
            },
            {
              "n": 19,
              "x": 820,
              "y": 2926,
              "width": 1050,
              "height": 44,
              "forward": false
            },
            {
              "n": 33,
              "x": 820,
              "y": 2970,
              "width": 1050,
              "height": 44,
              "forward": false
            },
            {
              "n": 43,
              "x": 820,
              "y": 3014,
              "width": 1050,
              "height": 44,
              "forward": false
            },
            {
              "n": 53,
              "x": 820,
              "y": 3058,
              "width": 1050,
              "height": 44,
              "forward": false
            }
          ]
        },
        {
          "pair": [
            "b_cat",
            "control"
          ],
          "points": [
            [
              1575,
              2822
            ],
            [
              2890,
              2822
            ],
            [
              3075,
              3774
            ]
          ],
          "rows": [
            {
              "n": 2,
              "x": 2320,
              "y": 2589,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 8,
              "x": 2320,
              "y": 2633,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 21,
              "x": 2320,
              "y": 2677,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 35,
              "x": 2320,
              "y": 2721,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 45,
              "x": 2320,
              "y": 2765,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 5,
              "x": 2320,
              "y": 2882,
              "width": 1050,
              "height": 44,
              "forward": false
            },
            {
              "n": 18,
              "x": 2320,
              "y": 2926,
              "width": 1050,
              "height": 44,
              "forward": false
            },
            {
              "n": 32,
              "x": 2320,
              "y": 2970,
              "width": 1050,
              "height": 44,
              "forward": false
            },
            {
              "n": 42,
              "x": 2320,
              "y": 3014,
              "width": 1050,
              "height": 44,
              "forward": false
            },
            {
              "n": 52,
              "x": 2320,
              "y": 3058,
              "width": 1050,
              "height": 44,
              "forward": false
            }
          ]
        },
        {
          "pair": [
            "control",
            "categoria"
          ],
          "points": [
            [
              3205,
              3774
            ],
            [
              3500,
              1066
            ],
            [
              5625,
              1066
            ]
          ],
          "rows": [
            {
              "n": 3,
              "x": 4410,
              "y": 217,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 9,
              "x": 4410,
              "y": 261,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 11,
              "x": 4410,
              "y": 305,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 13,
              "x": 4410,
              "y": 349,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 16,
              "x": 4410,
              "y": 393,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 22,
              "x": 4410,
              "y": 437,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 24,
              "x": 4410,
              "y": 481,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 26,
              "x": 4410,
              "y": 525,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 28,
              "x": 4410,
              "y": 569,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 30,
              "x": 4410,
              "y": 613,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 36,
              "x": 4410,
              "y": 657,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 38,
              "x": 4410,
              "y": 701,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 40,
              "x": 4410,
              "y": 745,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 46,
              "x": 4410,
              "y": 789,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 48,
              "x": 4410,
              "y": 833,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 50,
              "x": 4410,
              "y": 877,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 95,
              "x": 4410,
              "y": 921,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 111,
              "x": 4410,
              "y": 965,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 135,
              "x": 4410,
              "y": 1009,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 4,
              "x": 4410,
              "y": 1126,
              "width": 1500,
              "height": 44,
              "forward": false
            },
            {
              "n": 10,
              "x": 4410,
              "y": 1170,
              "width": 1500,
              "height": 44,
              "forward": false
            },
            {
              "n": 12,
              "x": 4410,
              "y": 1214,
              "width": 1500,
              "height": 44,
              "forward": false
            },
            {
              "n": 14,
              "x": 4410,
              "y": 1258,
              "width": 1500,
              "height": 44,
              "forward": false
            },
            {
              "n": 17,
              "x": 4410,
              "y": 1302,
              "width": 1500,
              "height": 44,
              "forward": false
            },
            {
              "n": 23,
              "x": 4410,
              "y": 1346,
              "width": 1500,
              "height": 44,
              "forward": false
            },
            {
              "n": 25,
              "x": 4410,
              "y": 1390,
              "width": 1500,
              "height": 44,
              "forward": false
            },
            {
              "n": 27,
              "x": 4410,
              "y": 1434,
              "width": 1500,
              "height": 44,
              "forward": false
            },
            {
              "n": 31,
              "x": 4410,
              "y": 1478,
              "width": 1500,
              "height": 44,
              "forward": false
            },
            {
              "n": 37,
              "x": 4410,
              "y": 1522,
              "width": 1500,
              "height": 44,
              "forward": false
            },
            {
              "n": 39,
              "x": 4410,
              "y": 1566,
              "width": 1500,
              "height": 44,
              "forward": false
            },
            {
              "n": 47,
              "x": 4410,
              "y": 1610,
              "width": 1500,
              "height": 44,
              "forward": false
            },
            {
              "n": 51,
              "x": 4410,
              "y": 1654,
              "width": 1500,
              "height": 44,
              "forward": false
            },
            {
              "n": 96,
              "x": 4410,
              "y": 1698,
              "width": 1500,
              "height": 44,
              "forward": false
            },
            {
              "n": 112,
              "x": 4410,
              "y": 1742,
              "width": 1500,
              "height": 44,
              "forward": false
            },
            {
              "n": 136,
              "x": 4410,
              "y": 1786,
              "width": 1500,
              "height": 44,
              "forward": false
            }
          ]
        },
        {
          "pair": [
            "control",
            "bitacora"
          ],
          "points": [
            [
              3205,
              3774
            ],
            [
              3500,
              7338
            ],
            [
              5625,
              7338
            ]
          ],
          "rows": [
            {
              "n": 15,
              "x": 4410,
              "y": 6841,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 29,
              "x": 4410,
              "y": 6885,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 41,
              "x": 4410,
              "y": 6929,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 49,
              "x": 4410,
              "y": 6973,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 66,
              "x": 4410,
              "y": 7017,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 76,
              "x": 4410,
              "y": 7061,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 86,
              "x": 4410,
              "y": 7105,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 122,
              "x": 4410,
              "y": 7149,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 141,
              "x": 4410,
              "y": 7193,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 153,
              "x": 4410,
              "y": 7237,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 161,
              "x": 4410,
              "y": 7281,
              "width": 1500,
              "height": 44,
              "forward": true
            }
          ]
        },
        {
          "pair": [
            "actor",
            "b_temp"
          ],
          "points": [
            [
              220,
              3774
            ],
            [
              340,
              3638
            ],
            [
              1445,
              3638
            ]
          ],
          "rows": [
            {
              "n": 54,
              "x": 820,
              "y": 3449,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 60,
              "x": 820,
              "y": 3493,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 69,
              "x": 820,
              "y": 3537,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 81,
              "x": 820,
              "y": 3581,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 59,
              "x": 820,
              "y": 3698,
              "width": 1050,
              "height": 44,
              "forward": false
            },
            {
              "n": 68,
              "x": 820,
              "y": 3742,
              "width": 1050,
              "height": 44,
              "forward": false
            },
            {
              "n": 80,
              "x": 820,
              "y": 3786,
              "width": 1050,
              "height": 44,
              "forward": false
            },
            {
              "n": 88,
              "x": 820,
              "y": 3830,
              "width": 1050,
              "height": 44,
              "forward": false
            }
          ]
        },
        {
          "pair": [
            "b_temp",
            "control"
          ],
          "points": [
            [
              1575,
              3638
            ],
            [
              2890,
              3638
            ],
            [
              3075,
              3774
            ]
          ],
          "rows": [
            {
              "n": 55,
              "x": 2320,
              "y": 3449,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 61,
              "x": 2320,
              "y": 3493,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 70,
              "x": 2320,
              "y": 3537,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 82,
              "x": 2320,
              "y": 3581,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 58,
              "x": 2320,
              "y": 3698,
              "width": 1050,
              "height": 44,
              "forward": false
            },
            {
              "n": 67,
              "x": 2320,
              "y": 3742,
              "width": 1050,
              "height": 44,
              "forward": false
            },
            {
              "n": 79,
              "x": 2320,
              "y": 3786,
              "width": 1050,
              "height": 44,
              "forward": false
            },
            {
              "n": 87,
              "x": 2320,
              "y": 3830,
              "width": 1050,
              "height": 44,
              "forward": false
            }
          ]
        },
        {
          "pair": [
            "control",
            "temporada"
          ],
          "points": [
            [
              3205,
              3774
            ],
            [
              3500,
              2406
            ],
            [
              5625,
              2406
            ]
          ],
          "rows": [
            {
              "n": 56,
              "x": 4410,
              "y": 1997,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 62,
              "x": 4410,
              "y": 2041,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 64,
              "x": 4410,
              "y": 2085,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 71,
              "x": 4410,
              "y": 2129,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 73,
              "x": 4410,
              "y": 2173,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 75,
              "x": 4410,
              "y": 2217,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 77,
              "x": 4410,
              "y": 2261,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 83,
              "x": 4410,
              "y": 2305,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 85,
              "x": 4410,
              "y": 2349,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 57,
              "x": 4410,
              "y": 2466,
              "width": 1500,
              "height": 44,
              "forward": false
            },
            {
              "n": 63,
              "x": 4410,
              "y": 2510,
              "width": 1500,
              "height": 44,
              "forward": false
            },
            {
              "n": 65,
              "x": 4410,
              "y": 2554,
              "width": 1500,
              "height": 44,
              "forward": false
            },
            {
              "n": 72,
              "x": 4410,
              "y": 2598,
              "width": 1500,
              "height": 44,
              "forward": false
            },
            {
              "n": 74,
              "x": 4410,
              "y": 2642,
              "width": 1500,
              "height": 44,
              "forward": false
            },
            {
              "n": 78,
              "x": 4410,
              "y": 2686,
              "width": 1500,
              "height": 44,
              "forward": false
            },
            {
              "n": 84,
              "x": 4410,
              "y": 2730,
              "width": 1500,
              "height": 44,
              "forward": false
            }
          ]
        },
        {
          "pair": [
            "actor",
            "b_pre"
          ],
          "points": [
            [
              220,
              3774
            ],
            [
              340,
              4630
            ],
            [
              1445,
              4630
            ]
          ],
          "rows": [
            {
              "n": 89,
              "x": 820,
              "y": 4353,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 107,
              "x": 820,
              "y": 4397,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 129,
              "x": 820,
              "y": 4441,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 148,
              "x": 820,
              "y": 4485,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 156,
              "x": 820,
              "y": 4529,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 168,
              "x": 820,
              "y": 4573,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 106,
              "x": 820,
              "y": 4690,
              "width": 1050,
              "height": 44,
              "forward": false
            },
            {
              "n": 128,
              "x": 820,
              "y": 4734,
              "width": 1050,
              "height": 44,
              "forward": false
            },
            {
              "n": 147,
              "x": 820,
              "y": 4778,
              "width": 1050,
              "height": 44,
              "forward": false
            },
            {
              "n": 155,
              "x": 820,
              "y": 4822,
              "width": 1050,
              "height": 44,
              "forward": false
            },
            {
              "n": 167,
              "x": 820,
              "y": 4866,
              "width": 1050,
              "height": 44,
              "forward": false
            },
            {
              "n": 173,
              "x": 820,
              "y": 4910,
              "width": 1050,
              "height": 44,
              "forward": false
            }
          ]
        },
        {
          "pair": [
            "b_pre",
            "control"
          ],
          "points": [
            [
              1575,
              4630
            ],
            [
              2890,
              4630
            ],
            [
              3075,
              3774
            ]
          ],
          "rows": [
            {
              "n": 90,
              "x": 2320,
              "y": 4221,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 94,
              "x": 2320,
              "y": 4265,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 98,
              "x": 2320,
              "y": 4309,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 102,
              "x": 2320,
              "y": 4353,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 108,
              "x": 2320,
              "y": 4397,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 130,
              "x": 2320,
              "y": 4441,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 149,
              "x": 2320,
              "y": 4485,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 157,
              "x": 2320,
              "y": 4529,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 169,
              "x": 2320,
              "y": 4573,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 93,
              "x": 2320,
              "y": 4690,
              "width": 1050,
              "height": 44,
              "forward": false
            },
            {
              "n": 97,
              "x": 2320,
              "y": 4734,
              "width": 1050,
              "height": 44,
              "forward": false
            },
            {
              "n": 101,
              "x": 2320,
              "y": 4778,
              "width": 1050,
              "height": 44,
              "forward": false
            },
            {
              "n": 105,
              "x": 2320,
              "y": 4822,
              "width": 1050,
              "height": 44,
              "forward": false
            },
            {
              "n": 127,
              "x": 2320,
              "y": 4866,
              "width": 1050,
              "height": 44,
              "forward": false
            },
            {
              "n": 146,
              "x": 2320,
              "y": 4910,
              "width": 1050,
              "height": 44,
              "forward": false
            },
            {
              "n": 154,
              "x": 2320,
              "y": 4954,
              "width": 1050,
              "height": 44,
              "forward": false
            },
            {
              "n": 166,
              "x": 2320,
              "y": 4998,
              "width": 1050,
              "height": 44,
              "forward": false
            },
            {
              "n": 172,
              "x": 2320,
              "y": 5042,
              "width": 1050,
              "height": 44,
              "forward": false
            }
          ]
        },
        {
          "pair": [
            "control",
            "prenda"
          ],
          "points": [
            [
              3205,
              3774
            ],
            [
              3500,
              3570
            ],
            [
              5625,
              3570
            ]
          ],
          "rows": [
            {
              "n": 91,
              "x": 4410,
              "y": 2941,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 109,
              "x": 4410,
              "y": 2985,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 113,
              "x": 4410,
              "y": 3029,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 123,
              "x": 4410,
              "y": 3073,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 131,
              "x": 4410,
              "y": 3117,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 133,
              "x": 4410,
              "y": 3161,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 137,
              "x": 4410,
              "y": 3205,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 142,
              "x": 4410,
              "y": 3249,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 150,
              "x": 4410,
              "y": 3293,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 152,
              "x": 4410,
              "y": 3337,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 158,
              "x": 4410,
              "y": 3381,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 160,
              "x": 4410,
              "y": 3425,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 162,
              "x": 4410,
              "y": 3469,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 170,
              "x": 4410,
              "y": 3513,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 92,
              "x": 4410,
              "y": 3630,
              "width": 1500,
              "height": 44,
              "forward": false
            },
            {
              "n": 110,
              "x": 4410,
              "y": 3674,
              "width": 1500,
              "height": 44,
              "forward": false
            },
            {
              "n": 114,
              "x": 4410,
              "y": 3718,
              "width": 1500,
              "height": 44,
              "forward": false
            },
            {
              "n": 124,
              "x": 4410,
              "y": 3762,
              "width": 1500,
              "height": 44,
              "forward": false
            },
            {
              "n": 132,
              "x": 4410,
              "y": 3806,
              "width": 1500,
              "height": 44,
              "forward": false
            },
            {
              "n": 134,
              "x": 4410,
              "y": 3850,
              "width": 1500,
              "height": 44,
              "forward": false
            },
            {
              "n": 143,
              "x": 4410,
              "y": 3894,
              "width": 1500,
              "height": 44,
              "forward": false
            },
            {
              "n": 151,
              "x": 4410,
              "y": 3938,
              "width": 1500,
              "height": 44,
              "forward": false
            },
            {
              "n": 159,
              "x": 4410,
              "y": 3982,
              "width": 1500,
              "height": 44,
              "forward": false
            },
            {
              "n": 163,
              "x": 4410,
              "y": 4026,
              "width": 1500,
              "height": 44,
              "forward": false
            },
            {
              "n": 171,
              "x": 4410,
              "y": 4070,
              "width": 1500,
              "height": 44,
              "forward": false
            }
          ]
        },
        {
          "pair": [
            "control",
            "talla"
          ],
          "points": [
            [
              3205,
              3774
            ],
            [
              3500,
              4930
            ],
            [
              5625,
              4930
            ]
          ],
          "rows": [
            {
              "n": 99,
              "x": 4410,
              "y": 4873,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 100,
              "x": 4410,
              "y": 4990,
              "width": 1500,
              "height": 44,
              "forward": false
            }
          ]
        },
        {
          "pair": [
            "control",
            "color"
          ],
          "points": [
            [
              3205,
              3774
            ],
            [
              3500,
              5258
            ],
            [
              5625,
              5258
            ]
          ],
          "rows": [
            {
              "n": 103,
              "x": 4410,
              "y": 5201,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 104,
              "x": 4410,
              "y": 5318,
              "width": 1500,
              "height": 44,
              "forward": false
            }
          ]
        },
        {
          "pair": [
            "control",
            "imagen"
          ],
          "points": [
            [
              3205,
              3774
            ],
            [
              3500,
              5674
            ],
            [
              5625,
              5674
            ]
          ],
          "rows": [
            {
              "n": 115,
              "x": 4410,
              "y": 5529,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 138,
              "x": 4410,
              "y": 5573,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 140,
              "x": 4410,
              "y": 5617,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 139,
              "x": 4410,
              "y": 5734,
              "width": 1500,
              "height": 44,
              "forward": false
            }
          ]
        },
        {
          "pair": [
            "control",
            "sucursal"
          ],
          "points": [
            [
              3205,
              3774
            ],
            [
              3500,
              6002
            ],
            [
              5625,
              6002
            ]
          ],
          "rows": [
            {
              "n": 116,
              "x": 4410,
              "y": 5945,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 117,
              "x": 4410,
              "y": 6062,
              "width": 1500,
              "height": 44,
              "forward": false
            }
          ]
        },
        {
          "pair": [
            "control",
            "variante"
          ],
          "points": [
            [
              3205,
              3774
            ],
            [
              3500,
              4470
            ],
            [
              5625,
              4470
            ]
          ],
          "rows": [
            {
              "n": 118,
              "x": 4410,
              "y": 4281,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 125,
              "x": 4410,
              "y": 4325,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 144,
              "x": 4410,
              "y": 4369,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 164,
              "x": 4410,
              "y": 4413,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 119,
              "x": 4410,
              "y": 4530,
              "width": 1500,
              "height": 44,
              "forward": false
            },
            {
              "n": 126,
              "x": 4410,
              "y": 4574,
              "width": 1500,
              "height": 44,
              "forward": false
            },
            {
              "n": 145,
              "x": 4410,
              "y": 4618,
              "width": 1500,
              "height": 44,
              "forward": false
            },
            {
              "n": 165,
              "x": 4410,
              "y": 4662,
              "width": 1500,
              "height": 44,
              "forward": false
            }
          ]
        },
        {
          "pair": [
            "control",
            "inventario"
          ],
          "points": [
            [
              3205,
              3774
            ],
            [
              3500,
              6330
            ],
            [
              5625,
              6330
            ]
          ],
          "rows": [
            {
              "n": 120,
              "x": 4410,
              "y": 6273,
              "width": 1500,
              "height": 44,
              "forward": true
            }
          ]
        },
        {
          "pair": [
            "control",
            "movimiento"
          ],
          "points": [
            [
              3205,
              3774
            ],
            [
              3500,
              6614
            ],
            [
              5625,
              6614
            ]
          ],
          "rows": [
            {
              "n": 121,
              "x": 4410,
              "y": 6557,
              "width": 1500,
              "height": 44,
              "forward": true
            }
          ]
        }
      ]
    },
    {
      "name": "CU06 - Categorías",
      "width": 6000,
      "height": 2312,
      "nodes": {
        "actor": {
          "x": 180,
          "y": 1066
        },
        "control": {
          "x": 3140,
          "y": 1066
        },
        "categoria": {
          "x": 5690,
          "y": 934
        },
        "bitacora": {
          "x": 5690,
          "y": 1922
        },
        "b_cat": {
          "x": 1510,
          "y": 1106
        }
      },
      "groups": [
        {
          "pair": [
            "actor",
            "b_cat"
          ],
          "points": [
            [
              220,
              1066
            ],
            [
              340,
              1106
            ],
            [
              1445,
              1106
            ]
          ],
          "rows": [
            {
              "n": 1,
              "x": 820,
              "y": 873,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 7,
              "x": 820,
              "y": 917,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 20,
              "x": 820,
              "y": 961,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 34,
              "x": 820,
              "y": 1005,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 44,
              "x": 820,
              "y": 1049,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 6,
              "x": 820,
              "y": 1166,
              "width": 1050,
              "height": 44,
              "forward": false
            },
            {
              "n": 19,
              "x": 820,
              "y": 1210,
              "width": 1050,
              "height": 44,
              "forward": false
            },
            {
              "n": 33,
              "x": 820,
              "y": 1254,
              "width": 1050,
              "height": 44,
              "forward": false
            },
            {
              "n": 43,
              "x": 820,
              "y": 1298,
              "width": 1050,
              "height": 44,
              "forward": false
            },
            {
              "n": 53,
              "x": 820,
              "y": 1342,
              "width": 1050,
              "height": 44,
              "forward": false
            }
          ]
        },
        {
          "pair": [
            "b_cat",
            "control"
          ],
          "points": [
            [
              1575,
              1106
            ],
            [
              2890,
              1106
            ],
            [
              3075,
              1066
            ]
          ],
          "rows": [
            {
              "n": 2,
              "x": 2320,
              "y": 873,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 8,
              "x": 2320,
              "y": 917,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 21,
              "x": 2320,
              "y": 961,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 35,
              "x": 2320,
              "y": 1005,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 45,
              "x": 2320,
              "y": 1049,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 5,
              "x": 2320,
              "y": 1166,
              "width": 1050,
              "height": 44,
              "forward": false
            },
            {
              "n": 18,
              "x": 2320,
              "y": 1210,
              "width": 1050,
              "height": 44,
              "forward": false
            },
            {
              "n": 32,
              "x": 2320,
              "y": 1254,
              "width": 1050,
              "height": 44,
              "forward": false
            },
            {
              "n": 42,
              "x": 2320,
              "y": 1298,
              "width": 1050,
              "height": 44,
              "forward": false
            },
            {
              "n": 52,
              "x": 2320,
              "y": 1342,
              "width": 1050,
              "height": 44,
              "forward": false
            }
          ]
        },
        {
          "pair": [
            "control",
            "categoria"
          ],
          "points": [
            [
              3205,
              1066
            ],
            [
              3500,
              934
            ],
            [
              5625,
              934
            ]
          ],
          "rows": [
            {
              "n": 3,
              "x": 4410,
              "y": 217,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 9,
              "x": 4410,
              "y": 261,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 11,
              "x": 4410,
              "y": 305,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 13,
              "x": 4410,
              "y": 349,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 16,
              "x": 4410,
              "y": 393,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 22,
              "x": 4410,
              "y": 437,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 24,
              "x": 4410,
              "y": 481,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 26,
              "x": 4410,
              "y": 525,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 28,
              "x": 4410,
              "y": 569,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 30,
              "x": 4410,
              "y": 613,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 36,
              "x": 4410,
              "y": 657,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 38,
              "x": 4410,
              "y": 701,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 40,
              "x": 4410,
              "y": 745,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 46,
              "x": 4410,
              "y": 789,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 48,
              "x": 4410,
              "y": 833,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 50,
              "x": 4410,
              "y": 877,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 4,
              "x": 4410,
              "y": 994,
              "width": 1500,
              "height": 44,
              "forward": false
            },
            {
              "n": 10,
              "x": 4410,
              "y": 1038,
              "width": 1500,
              "height": 44,
              "forward": false
            },
            {
              "n": 12,
              "x": 4410,
              "y": 1082,
              "width": 1500,
              "height": 44,
              "forward": false
            },
            {
              "n": 14,
              "x": 4410,
              "y": 1126,
              "width": 1500,
              "height": 44,
              "forward": false
            },
            {
              "n": 17,
              "x": 4410,
              "y": 1170,
              "width": 1500,
              "height": 44,
              "forward": false
            },
            {
              "n": 23,
              "x": 4410,
              "y": 1214,
              "width": 1500,
              "height": 44,
              "forward": false
            },
            {
              "n": 25,
              "x": 4410,
              "y": 1258,
              "width": 1500,
              "height": 44,
              "forward": false
            },
            {
              "n": 27,
              "x": 4410,
              "y": 1302,
              "width": 1500,
              "height": 44,
              "forward": false
            },
            {
              "n": 31,
              "x": 4410,
              "y": 1346,
              "width": 1500,
              "height": 44,
              "forward": false
            },
            {
              "n": 37,
              "x": 4410,
              "y": 1390,
              "width": 1500,
              "height": 44,
              "forward": false
            },
            {
              "n": 39,
              "x": 4410,
              "y": 1434,
              "width": 1500,
              "height": 44,
              "forward": false
            },
            {
              "n": 47,
              "x": 4410,
              "y": 1478,
              "width": 1500,
              "height": 44,
              "forward": false
            },
            {
              "n": 51,
              "x": 4410,
              "y": 1522,
              "width": 1500,
              "height": 44,
              "forward": false
            }
          ]
        },
        {
          "pair": [
            "control",
            "bitacora"
          ],
          "points": [
            [
              3205,
              1066
            ],
            [
              3500,
              1922
            ],
            [
              5625,
              1922
            ]
          ],
          "rows": [
            {
              "n": 15,
              "x": 4410,
              "y": 1733,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 29,
              "x": 4410,
              "y": 1777,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 41,
              "x": 4410,
              "y": 1821,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 49,
              "x": 4410,
              "y": 1865,
              "width": 1500,
              "height": 44,
              "forward": true
            }
          ]
        }
      ]
    },
    {
      "name": "CU06 - Temporadas y colecciones",
      "width": 6000,
      "height": 1696,
      "nodes": {
        "actor": {
          "x": 180,
          "y": 758
        },
        "control": {
          "x": 3140,
          "y": 758
        },
        "temporada": {
          "x": 5690,
          "y": 626
        },
        "bitacora": {
          "x": 5690,
          "y": 1306
        },
        "b_temp": {
          "x": 1510,
          "y": 798
        }
      },
      "groups": [
        {
          "pair": [
            "actor",
            "b_temp"
          ],
          "points": [
            [
              220,
              758
            ],
            [
              340,
              798
            ],
            [
              1445,
              798
            ]
          ],
          "rows": [
            {
              "n": 54,
              "x": 820,
              "y": 609,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 60,
              "x": 820,
              "y": 653,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 69,
              "x": 820,
              "y": 697,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 81,
              "x": 820,
              "y": 741,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 59,
              "x": 820,
              "y": 858,
              "width": 1050,
              "height": 44,
              "forward": false
            },
            {
              "n": 68,
              "x": 820,
              "y": 902,
              "width": 1050,
              "height": 44,
              "forward": false
            },
            {
              "n": 80,
              "x": 820,
              "y": 946,
              "width": 1050,
              "height": 44,
              "forward": false
            },
            {
              "n": 88,
              "x": 820,
              "y": 990,
              "width": 1050,
              "height": 44,
              "forward": false
            }
          ]
        },
        {
          "pair": [
            "b_temp",
            "control"
          ],
          "points": [
            [
              1575,
              798
            ],
            [
              2890,
              798
            ],
            [
              3075,
              758
            ]
          ],
          "rows": [
            {
              "n": 55,
              "x": 2320,
              "y": 609,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 61,
              "x": 2320,
              "y": 653,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 70,
              "x": 2320,
              "y": 697,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 82,
              "x": 2320,
              "y": 741,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 58,
              "x": 2320,
              "y": 858,
              "width": 1050,
              "height": 44,
              "forward": false
            },
            {
              "n": 67,
              "x": 2320,
              "y": 902,
              "width": 1050,
              "height": 44,
              "forward": false
            },
            {
              "n": 79,
              "x": 2320,
              "y": 946,
              "width": 1050,
              "height": 44,
              "forward": false
            },
            {
              "n": 87,
              "x": 2320,
              "y": 990,
              "width": 1050,
              "height": 44,
              "forward": false
            }
          ]
        },
        {
          "pair": [
            "control",
            "temporada"
          ],
          "points": [
            [
              3205,
              758
            ],
            [
              3500,
              626
            ],
            [
              5625,
              626
            ]
          ],
          "rows": [
            {
              "n": 56,
              "x": 4410,
              "y": 217,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 62,
              "x": 4410,
              "y": 261,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 64,
              "x": 4410,
              "y": 305,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 71,
              "x": 4410,
              "y": 349,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 73,
              "x": 4410,
              "y": 393,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 75,
              "x": 4410,
              "y": 437,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 77,
              "x": 4410,
              "y": 481,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 83,
              "x": 4410,
              "y": 525,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 85,
              "x": 4410,
              "y": 569,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 57,
              "x": 4410,
              "y": 686,
              "width": 1500,
              "height": 44,
              "forward": false
            },
            {
              "n": 63,
              "x": 4410,
              "y": 730,
              "width": 1500,
              "height": 44,
              "forward": false
            },
            {
              "n": 65,
              "x": 4410,
              "y": 774,
              "width": 1500,
              "height": 44,
              "forward": false
            },
            {
              "n": 72,
              "x": 4410,
              "y": 818,
              "width": 1500,
              "height": 44,
              "forward": false
            },
            {
              "n": 74,
              "x": 4410,
              "y": 862,
              "width": 1500,
              "height": 44,
              "forward": false
            },
            {
              "n": 78,
              "x": 4410,
              "y": 906,
              "width": 1500,
              "height": 44,
              "forward": false
            },
            {
              "n": 84,
              "x": 4410,
              "y": 950,
              "width": 1500,
              "height": 44,
              "forward": false
            }
          ]
        },
        {
          "pair": [
            "control",
            "bitacora"
          ],
          "points": [
            [
              3205,
              758
            ],
            [
              3500,
              1306
            ],
            [
              5625,
              1306
            ]
          ],
          "rows": [
            {
              "n": 66,
              "x": 4410,
              "y": 1161,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 76,
              "x": 4410,
              "y": 1205,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 86,
              "x": 4410,
              "y": 1249,
              "width": 1500,
              "height": 44,
              "forward": true
            }
          ]
        }
      ]
    },
    {
      "name": "CU06 - Prendas y variantes",
      "width": 6000,
      "height": 5200,
      "nodes": {
        "actor": {
          "x": 180,
          "y": 2510
        },
        "control": {
          "x": 3140,
          "y": 2510
        },
        "categoria": {
          "x": 5690,
          "y": 362
        },
        "prenda": {
          "x": 5690,
          "y": 1350
        },
        "variante": {
          "x": 5690,
          "y": 2250
        },
        "talla": {
          "x": 5690,
          "y": 2710
        },
        "color": {
          "x": 5690,
          "y": 3038
        },
        "imagen": {
          "x": 5690,
          "y": 3454
        },
        "sucursal": {
          "x": 5690,
          "y": 3782
        },
        "inventario": {
          "x": 5690,
          "y": 4110
        },
        "movimiento": {
          "x": 5690,
          "y": 4394
        },
        "bitacora": {
          "x": 5690,
          "y": 4810
        },
        "b_pre": {
          "x": 1510,
          "y": 2550
        }
      },
      "groups": [
        {
          "pair": [
            "actor",
            "b_pre"
          ],
          "points": [
            [
              220,
              2510
            ],
            [
              340,
              2550
            ],
            [
              1445,
              2550
            ]
          ],
          "rows": [
            {
              "n": 89,
              "x": 820,
              "y": 2273,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 107,
              "x": 820,
              "y": 2317,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 129,
              "x": 820,
              "y": 2361,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 148,
              "x": 820,
              "y": 2405,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 156,
              "x": 820,
              "y": 2449,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 168,
              "x": 820,
              "y": 2493,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 106,
              "x": 820,
              "y": 2610,
              "width": 1050,
              "height": 44,
              "forward": false
            },
            {
              "n": 128,
              "x": 820,
              "y": 2654,
              "width": 1050,
              "height": 44,
              "forward": false
            },
            {
              "n": 147,
              "x": 820,
              "y": 2698,
              "width": 1050,
              "height": 44,
              "forward": false
            },
            {
              "n": 155,
              "x": 820,
              "y": 2742,
              "width": 1050,
              "height": 44,
              "forward": false
            },
            {
              "n": 167,
              "x": 820,
              "y": 2786,
              "width": 1050,
              "height": 44,
              "forward": false
            },
            {
              "n": 173,
              "x": 820,
              "y": 2830,
              "width": 1050,
              "height": 44,
              "forward": false
            }
          ]
        },
        {
          "pair": [
            "b_pre",
            "control"
          ],
          "points": [
            [
              1575,
              2550
            ],
            [
              2890,
              2550
            ],
            [
              3075,
              2510
            ]
          ],
          "rows": [
            {
              "n": 90,
              "x": 2320,
              "y": 2141,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 94,
              "x": 2320,
              "y": 2185,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 98,
              "x": 2320,
              "y": 2229,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 102,
              "x": 2320,
              "y": 2273,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 108,
              "x": 2320,
              "y": 2317,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 130,
              "x": 2320,
              "y": 2361,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 149,
              "x": 2320,
              "y": 2405,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 157,
              "x": 2320,
              "y": 2449,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 169,
              "x": 2320,
              "y": 2493,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 93,
              "x": 2320,
              "y": 2610,
              "width": 1050,
              "height": 44,
              "forward": false
            },
            {
              "n": 97,
              "x": 2320,
              "y": 2654,
              "width": 1050,
              "height": 44,
              "forward": false
            },
            {
              "n": 101,
              "x": 2320,
              "y": 2698,
              "width": 1050,
              "height": 44,
              "forward": false
            },
            {
              "n": 105,
              "x": 2320,
              "y": 2742,
              "width": 1050,
              "height": 44,
              "forward": false
            },
            {
              "n": 127,
              "x": 2320,
              "y": 2786,
              "width": 1050,
              "height": 44,
              "forward": false
            },
            {
              "n": 146,
              "x": 2320,
              "y": 2830,
              "width": 1050,
              "height": 44,
              "forward": false
            },
            {
              "n": 154,
              "x": 2320,
              "y": 2874,
              "width": 1050,
              "height": 44,
              "forward": false
            },
            {
              "n": 166,
              "x": 2320,
              "y": 2918,
              "width": 1050,
              "height": 44,
              "forward": false
            },
            {
              "n": 172,
              "x": 2320,
              "y": 2962,
              "width": 1050,
              "height": 44,
              "forward": false
            }
          ]
        },
        {
          "pair": [
            "control",
            "prenda"
          ],
          "points": [
            [
              3205,
              2510
            ],
            [
              3500,
              1350
            ],
            [
              5625,
              1350
            ]
          ],
          "rows": [
            {
              "n": 91,
              "x": 4410,
              "y": 721,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 109,
              "x": 4410,
              "y": 765,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 113,
              "x": 4410,
              "y": 809,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 123,
              "x": 4410,
              "y": 853,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 131,
              "x": 4410,
              "y": 897,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 133,
              "x": 4410,
              "y": 941,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 137,
              "x": 4410,
              "y": 985,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 142,
              "x": 4410,
              "y": 1029,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 150,
              "x": 4410,
              "y": 1073,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 152,
              "x": 4410,
              "y": 1117,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 158,
              "x": 4410,
              "y": 1161,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 160,
              "x": 4410,
              "y": 1205,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 162,
              "x": 4410,
              "y": 1249,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 170,
              "x": 4410,
              "y": 1293,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 92,
              "x": 4410,
              "y": 1410,
              "width": 1500,
              "height": 44,
              "forward": false
            },
            {
              "n": 110,
              "x": 4410,
              "y": 1454,
              "width": 1500,
              "height": 44,
              "forward": false
            },
            {
              "n": 114,
              "x": 4410,
              "y": 1498,
              "width": 1500,
              "height": 44,
              "forward": false
            },
            {
              "n": 124,
              "x": 4410,
              "y": 1542,
              "width": 1500,
              "height": 44,
              "forward": false
            },
            {
              "n": 132,
              "x": 4410,
              "y": 1586,
              "width": 1500,
              "height": 44,
              "forward": false
            },
            {
              "n": 134,
              "x": 4410,
              "y": 1630,
              "width": 1500,
              "height": 44,
              "forward": false
            },
            {
              "n": 143,
              "x": 4410,
              "y": 1674,
              "width": 1500,
              "height": 44,
              "forward": false
            },
            {
              "n": 151,
              "x": 4410,
              "y": 1718,
              "width": 1500,
              "height": 44,
              "forward": false
            },
            {
              "n": 159,
              "x": 4410,
              "y": 1762,
              "width": 1500,
              "height": 44,
              "forward": false
            },
            {
              "n": 163,
              "x": 4410,
              "y": 1806,
              "width": 1500,
              "height": 44,
              "forward": false
            },
            {
              "n": 171,
              "x": 4410,
              "y": 1850,
              "width": 1500,
              "height": 44,
              "forward": false
            }
          ]
        },
        {
          "pair": [
            "control",
            "categoria"
          ],
          "points": [
            [
              3205,
              2510
            ],
            [
              3500,
              362
            ],
            [
              5625,
              362
            ]
          ],
          "rows": [
            {
              "n": 95,
              "x": 4410,
              "y": 217,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 111,
              "x": 4410,
              "y": 261,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 135,
              "x": 4410,
              "y": 305,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 96,
              "x": 4410,
              "y": 422,
              "width": 1500,
              "height": 44,
              "forward": false
            },
            {
              "n": 112,
              "x": 4410,
              "y": 466,
              "width": 1500,
              "height": 44,
              "forward": false
            },
            {
              "n": 136,
              "x": 4410,
              "y": 510,
              "width": 1500,
              "height": 44,
              "forward": false
            }
          ]
        },
        {
          "pair": [
            "control",
            "talla"
          ],
          "points": [
            [
              3205,
              2510
            ],
            [
              3500,
              2710
            ],
            [
              5625,
              2710
            ]
          ],
          "rows": [
            {
              "n": 99,
              "x": 4410,
              "y": 2653,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 100,
              "x": 4410,
              "y": 2770,
              "width": 1500,
              "height": 44,
              "forward": false
            }
          ]
        },
        {
          "pair": [
            "control",
            "color"
          ],
          "points": [
            [
              3205,
              2510
            ],
            [
              3500,
              3038
            ],
            [
              5625,
              3038
            ]
          ],
          "rows": [
            {
              "n": 103,
              "x": 4410,
              "y": 2981,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 104,
              "x": 4410,
              "y": 3098,
              "width": 1500,
              "height": 44,
              "forward": false
            }
          ]
        },
        {
          "pair": [
            "control",
            "imagen"
          ],
          "points": [
            [
              3205,
              2510
            ],
            [
              3500,
              3454
            ],
            [
              5625,
              3454
            ]
          ],
          "rows": [
            {
              "n": 115,
              "x": 4410,
              "y": 3309,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 138,
              "x": 4410,
              "y": 3353,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 140,
              "x": 4410,
              "y": 3397,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 139,
              "x": 4410,
              "y": 3514,
              "width": 1500,
              "height": 44,
              "forward": false
            }
          ]
        },
        {
          "pair": [
            "control",
            "sucursal"
          ],
          "points": [
            [
              3205,
              2510
            ],
            [
              3500,
              3782
            ],
            [
              5625,
              3782
            ]
          ],
          "rows": [
            {
              "n": 116,
              "x": 4410,
              "y": 3725,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 117,
              "x": 4410,
              "y": 3842,
              "width": 1500,
              "height": 44,
              "forward": false
            }
          ]
        },
        {
          "pair": [
            "control",
            "variante"
          ],
          "points": [
            [
              3205,
              2510
            ],
            [
              3500,
              2250
            ],
            [
              5625,
              2250
            ]
          ],
          "rows": [
            {
              "n": 118,
              "x": 4410,
              "y": 2061,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 125,
              "x": 4410,
              "y": 2105,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 144,
              "x": 4410,
              "y": 2149,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 164,
              "x": 4410,
              "y": 2193,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 119,
              "x": 4410,
              "y": 2310,
              "width": 1500,
              "height": 44,
              "forward": false
            },
            {
              "n": 126,
              "x": 4410,
              "y": 2354,
              "width": 1500,
              "height": 44,
              "forward": false
            },
            {
              "n": 145,
              "x": 4410,
              "y": 2398,
              "width": 1500,
              "height": 44,
              "forward": false
            },
            {
              "n": 165,
              "x": 4410,
              "y": 2442,
              "width": 1500,
              "height": 44,
              "forward": false
            }
          ]
        },
        {
          "pair": [
            "control",
            "inventario"
          ],
          "points": [
            [
              3205,
              2510
            ],
            [
              3500,
              4110
            ],
            [
              5625,
              4110
            ]
          ],
          "rows": [
            {
              "n": 120,
              "x": 4410,
              "y": 4053,
              "width": 1500,
              "height": 44,
              "forward": true
            }
          ]
        },
        {
          "pair": [
            "control",
            "movimiento"
          ],
          "points": [
            [
              3205,
              2510
            ],
            [
              3500,
              4394
            ],
            [
              5625,
              4394
            ]
          ],
          "rows": [
            {
              "n": 121,
              "x": 4410,
              "y": 4337,
              "width": 1500,
              "height": 44,
              "forward": true
            }
          ]
        },
        {
          "pair": [
            "control",
            "bitacora"
          ],
          "points": [
            [
              3205,
              2510
            ],
            [
              3500,
              4810
            ],
            [
              5625,
              4810
            ]
          ],
          "rows": [
            {
              "n": 122,
              "x": 4410,
              "y": 4621,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 141,
              "x": 4410,
              "y": 4665,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 153,
              "x": 4410,
              "y": 4709,
              "width": 1500,
              "height": 44,
              "forward": true
            },
            {
              "n": 161,
              "x": 4410,
              "y": 4753,
              "width": 1500,
              "height": 44,
              "forward": true
            }
          ]
        }
      ]
    }
  ]
};
var CU06_SCALE = 0.6;

function eaColor(hex) {
    var red = parseInt(hex.substr(1, 2), 16);
    var green = parseInt(hex.substr(3, 2), 16);
    var blue = parseInt(hex.substr(5, 2), 16);
    return red + green * 256 + blue * 65536;
}

function checkedUpdate(object, context) {
    if (!object.Update()) {
        throw new Error(context + ": " + object.GetLastError());
    }
}

function createElement(pkg, key) {
    var definition = CU06_MODEL.nodes[key];
    var element = pkg.Elements.AddNew(definition.name, definition.kind == "actor" ? "Actor" : "Object");
    if (definition.kind != "actor") { element.Stereotype = definition.kind; }
    element.Notes = "FashionStore CU06. Identificador lógico: " + key + ".";
    if (definition.table) { element.Notes += " Tabla real: " + definition.table + "."; }
    if (definition.source) { element.Notes += " Fuente: " + definition.source + "."; }
    if (key == "control") {
        element.Notes += " Control de análisis que agrupa categorias.py, temporadas.py, prendas.py y sus servicios. No representa una clase Python existente.";
    }
    checkedUpdate(element, "Crear elemento " + key);
    return element;
}

function place(diagram, element, point, kind) {
    var radiusX = kind == "actor" ? 35 : 65;
    var radiusY = 65;
    var left = Math.round((point.x - radiusX) * CU06_SCALE);
    var right = Math.round((point.x + radiusX) * CU06_SCALE);
    var top = -Math.round((point.y - radiusY) * CU06_SCALE);
    var bottom = -Math.round((point.y + radiusY) * CU06_SCALE);
    var item = diagram.DiagramObjects.AddNew("l=" + left + ";r=" + right + ";t=" + top + ";b=" + bottom + ";", "");
    item.ElementID = element.ElementID;
    checkedUpdate(item, "Colocar elemento " + element.Name);
}

function createAssociation(source, target, diagram) {
    var association = source.Connectors.AddNew("", "Association");
    association.SupplierID = target.ElementID;
    association.Direction = "Unspecified";
    checkedUpdate(association, "Crear asociación");
    var link = diagram.DiagramLinks.AddNew("", "");
    link.ConnectorID = association.ConnectorID;
    link.Style = "Mode=1;Color=5592405;LWidth=1;";
    checkedUpdate(link, "Mostrar asociación");
    return association.ConnectorID;
}

function createMessage(elements, diagram, associationID, pair, message, row, positions) {
    var first = elements[pair[0]];
    var second = elements[pair[1]];
    var connector = first.Connectors.AddNew(message.text, "Collaboration");
    connector.SupplierID = second.ElementID;
    connector.DiagramID = diagram.DiagramID;
    connector.Direction = row.forward ? "Source -> Destination" : "Destination -> Source";
    connector.SequenceNo = message.n;
    connector.Notes = "CU06 mensaje " + message.n + ". Origen: " + message.a + ". Destino: " + message.b + ".";
    if (message.source) {
        connector.Notes += " Fuente: " + message.source + ":" + message.line + ", " + message.symbol + ".";
    }
    checkedUpdate(connector, "Crear mensaje " + message.n);

    var p1 = positions[pair[0]];
    var p2 = positions[pair[1]];
    var offsetX = Math.round((row.x - (p1.x + p2.x) / 2) * CU06_SCALE);
    var offsetY = -Math.round((row.y - (p1.y + p2.y) / 2) * CU06_SCALE);
    var geometry = "SX=" + offsetX + ";SY=" + offsetY + ";EX=0;EY=0;";

    // El convenio de asociación de mensajes es el mismo del archivo de referencia.
    // No se interpolan textos de negocio en SQL ni se actualizan objetos ajenos.
    var sql = "UPDATE t_connector SET " +
        "SourceIsAggregate=" + associationID + ", " +
        "SeqNo=" + message.n + ", " +
        "PDATA1='Synchronous', PDATA3='Call', " +
        "PDATA4='" + message.n + "', " +
        "PDATA5='" + geometry + "', " +
        "HeadStyle=1, RouteStyle=3 " +
        "WHERE Connector_ID=" + connector.ConnectorID;
    if (!Repository.Execute(sql)) {
        throw new Error("EA no pudo asociar el mensaje " + message.n + ". Se conserva el paquete parcial para revisión.");
    }

    var link = diagram.DiagramLinks.AddNew("", "");
    link.ConnectorID = connector.ConnectorID;
    link.Geometry = geometry + "EDGE=2;";
    link.Style = "Mode=1;Color=" + eaColor(message.color) + ";LWidth=1;";
    checkedUpdate(link, "Mostrar mensaje " + message.n);
}

function generateView(parent, view, byNumber) {
    var pkg = parent.Packages.AddNew(view.name, "");
    checkedUpdate(pkg, "Crear paquete de vista");
    var diagram = pkg.Diagrams.AddNew(view.name, "Communication");
    if (!diagram.Update()) {
        throw new Error("No se pudo crear un diagrama Communication: " + diagram.GetLastError());
    }
    var elements = {};
    var key;
    for (key in view.nodes) {
        if (view.nodes.hasOwnProperty(key)) {
            elements[key] = createElement(pkg, key);
            place(diagram, elements[key], view.nodes[key], CU06_MODEL.nodes[key].kind);
        }
    }
    var count = 0;
    for (var gi = 0; gi < view.groups.length; gi++) {
        var group = view.groups[gi];
        var associationID = createAssociation(elements[group.pair[0]], elements[group.pair[1]], diagram);
        for (var ri = 0; ri < group.rows.length; ri++) {
            var row = group.rows[ri];
            createMessage(elements, diagram, associationID, group.pair, byNumber[row.n], row, view.nodes);
            count++;
        }
    }
    diagram.DiagramObjects.Refresh();
    diagram.DiagramLinks.Refresh();
    checkedUpdate(diagram, "Guardar diagrama");
    Repository.ReloadDiagram(diagram.DiagramID);
    Repository.WriteOutput("Script", view.name + ": " + count + " mensajes generados.", 0);
    return diagram.DiagramID;
}

function main() {
    Repository.EnsureOutputVisible("Script");
    var selected = Repository.GetTreeSelectedPackage();
    if (selected == null) {
        Session.Prompt("Abre un proyecto y selecciona el paquete de destino en el navegador antes de ejecutar este JScript.", 0);
        return;
    }
    var stamp = new Date().getTime();
    var root = selected.Packages.AddNew("CU06 - Robustez numerada - " + stamp, "");
    checkedUpdate(root, "Crear paquete principal");
    var byNumber = {};
    for (var i = 0; i < CU06_MODEL.messages.length; i++) {
        byNumber[CU06_MODEL.messages[i].n] = CU06_MODEL.messages[i];
    }
    var firstDiagram = 0;
    for (var vi = 0; vi < CU06_MODEL.views.length; vi++) {
        var generated = generateView(root, CU06_MODEL.views[vi], byNumber);
        if (!firstDiagram) { firstDiagram = generated; }
    }
    root.Packages.Refresh();
    selected.Packages.Refresh();
    Repository.RefreshModelView(selected.PackageID);
    Repository.OpenDiagram(firstDiagram);
    Repository.WriteOutput("Script", "CU06 finalizado: " + CU06_MODEL.messages.length + " mensajes, numeración única compartida en cuatro vistas.", 0);
}

main();
