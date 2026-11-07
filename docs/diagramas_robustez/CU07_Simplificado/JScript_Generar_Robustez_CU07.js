/* FashionStore CU07. Ejecutar como JScript dentro de Enterprise Architect.
 * Genera un paquete nuevo con las vistas del modelo sin modificar diagramas existentes.
 * Las llamadas nativas y sus referencias proceden del modelo compartido con draw.io.
 * El enlace Association se crea antes de sus mensajes Collaboration, como en el
 * JScript de referencia. PDATA4 conserva el número explícito y SeqNo su orden.
 * Los campos internos de EA se escriben solo para conectores recién creados.
 */

var CU07_MODEL = {
  "nodes": {
    "actor": {
      "kind": "actor",
      "name": "Administrador de empresa"
    },
    "b_pre": {
      "kind": "boundary",
      "name": "Frontend : Proveedores y compras"
    },
    "control": {
      "kind": "control",
      "name": "Backend : Gestión de abastecimiento",
      "note": "Control de análisis que agrupa los módulos indicados en las referencias del caso de uso."
    },
    "proveedor": {
      "kind": "entity",
      "name": "Proveedor",
      "table": "proveedor"
    },
    "compra": {
      "kind": "entity",
      "name": "Compra",
      "table": "compra"
    },
    "detalle": {
      "kind": "entity",
      "name": "Detalle de compra",
      "table": "detalle_compra"
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
      "a": "actor",
      "b": "b_pre",
      "text": "Consultar proveedores",
      "kind": "ui",
      "color": "#28343E",
      "source": null,
      "symbol": null
    },
    {
      "n": 2,
      "action": 1,
      "a": "b_pre",
      "b": "control",
      "text": "listar_proveedores(búsqueda)",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/routers/proveedores.py",
      "symbol": "listar_proveedores",
      "line": 39
    },
    {
      "n": 3,
      "action": 1,
      "a": "control",
      "b": "proveedor",
      "text": "listar_proveedores(búsqueda)",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/services/proveedor_service.py",
      "symbol": "listar_proveedores",
      "line": 25
    },
    {
      "n": 4,
      "action": 1,
      "a": "proveedor",
      "b": "control",
      "text": "proveedores",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 5,
      "action": 1,
      "a": "control",
      "b": "b_pre",
      "text": "proveedores",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 6,
      "action": 1,
      "a": "b_pre",
      "b": "actor",
      "text": "Mostrar proveedores",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 7,
      "action": 2,
      "a": "actor",
      "b": "b_pre",
      "text": "Registrar proveedor",
      "kind": "ui",
      "color": "#28343E",
      "source": null,
      "symbol": null
    },
    {
      "n": 8,
      "action": 2,
      "a": "b_pre",
      "b": "control",
      "text": "crear_proveedor(datos)",
      "kind": "invoke",
      "color": "#215D9C",
      "source": "Parcial2_backend/app/routers/proveedores.py",
      "symbol": "crear_proveedor",
      "line": 94
    },
    {
      "n": 9,
      "action": 2,
      "a": "control",
      "b": "proveedor",
      "text": "crear_proveedor(datos)",
      "kind": "write",
      "color": "#AC3636",
      "source": "Parcial2_backend/app/services/proveedor_service.py",
      "symbol": "crear_proveedor",
      "line": 109
    },
    {
      "n": 10,
      "action": 2,
      "a": "proveedor",
      "b": "control",
      "text": "proveedor creado",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 11,
      "action": 2,
      "a": "control",
      "b": "bitacora",
      "text": "registrar_bitacora(proveedor, alta)",
      "kind": "write",
      "color": "#AC3636",
      "source": "Parcial2_backend/app/services/bitacora_service.py",
      "symbol": "registrar_bitacora",
      "line": 65
    },
    {
      "n": 12,
      "action": 2,
      "a": "control",
      "b": "b_pre",
      "text": "proveedor registrado",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 13,
      "action": 3,
      "a": "actor",
      "b": "b_pre",
      "text": "Editar proveedor",
      "kind": "ui",
      "color": "#28343E",
      "source": null,
      "symbol": null
    },
    {
      "n": 14,
      "action": 3,
      "a": "b_pre",
      "b": "control",
      "text": "actualizar_proveedor(id, cambios)",
      "kind": "invoke",
      "color": "#215D9C",
      "source": "Parcial2_backend/app/routers/proveedores.py",
      "symbol": "actualizar_proveedor",
      "line": 119
    },
    {
      "n": 15,
      "action": 3,
      "a": "control",
      "b": "proveedor",
      "text": "actualizar_proveedor(id, cambios)",
      "kind": "write",
      "color": "#AC3636",
      "source": "Parcial2_backend/app/services/proveedor_service.py",
      "symbol": "actualizar_proveedor",
      "line": 174
    },
    {
      "n": 16,
      "action": 3,
      "a": "control",
      "b": "bitacora",
      "text": "registrar_bitacora(proveedor, modificación)",
      "kind": "write",
      "color": "#AC3636",
      "source": "Parcial2_backend/app/services/bitacora_service.py",
      "symbol": "registrar_bitacora",
      "line": 65
    },
    {
      "n": 17,
      "action": 3,
      "a": "control",
      "b": "b_pre",
      "text": "proveedor actualizado",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 18,
      "action": 4,
      "a": "actor",
      "b": "b_pre",
      "text": "Confirmar compra y recepción",
      "kind": "ui",
      "color": "#28343E",
      "source": null,
      "symbol": null
    },
    {
      "n": 19,
      "action": 4,
      "a": "b_pre",
      "b": "control",
      "text": "registrar_compra(datos e ítems)",
      "kind": "invoke",
      "color": "#215D9C",
      "source": "Parcial2_backend/app/routers/compras.py",
      "symbol": "registrar_compra",
      "line": 39
    },
    {
      "n": 20,
      "action": 4,
      "a": "control",
      "b": "compra",
      "text": "registrar_compra(datos)",
      "kind": "write",
      "color": "#AC3636",
      "source": "Parcial2_backend/app/services/compra_service.py",
      "symbol": "registrar_compra",
      "line": 30
    },
    {
      "n": 21,
      "action": 4,
      "a": "compra",
      "b": "control",
      "text": "id_compra",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 22,
      "action": 4,
      "a": "control",
      "b": "detalle",
      "text": "Guardar detalle [por ítem]",
      "kind": "write",
      "color": "#AC3636",
      "source": "Parcial2_backend/app/services/compra_service.py",
      "symbol": "registrar_compra",
      "line": 30
    },
    {
      "n": 23,
      "action": 4,
      "a": "control",
      "b": "movimiento",
      "text": "Registrar Entrada [por ítem recibido]",
      "kind": "write",
      "color": "#AC3636",
      "source": "Parcial2_backend/app/services/compra_service.py",
      "symbol": "registrar_compra",
      "line": 30
    },
    {
      "n": 24,
      "action": 4,
      "a": "control",
      "b": "bitacora",
      "text": "registrar_bitacora(compra, recepción)",
      "kind": "write",
      "color": "#AC3636",
      "source": "Parcial2_backend/app/services/bitacora_service.py",
      "symbol": "registrar_bitacora",
      "line": 65
    },
    {
      "n": 25,
      "action": 4,
      "a": "control",
      "b": "b_pre",
      "text": "compra y recepción confirmadas",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 26,
      "action": 4,
      "a": "b_pre",
      "b": "actor",
      "text": "Mostrar recepción registrada",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 27,
      "action": 5,
      "a": "actor",
      "b": "b_pre",
      "text": "Consultar compra y detalles",
      "kind": "ui",
      "color": "#28343E",
      "source": null,
      "symbol": null
    },
    {
      "n": 28,
      "action": 5,
      "a": "b_pre",
      "b": "control",
      "text": "obtener_compra(id_compra)",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/routers/compras.py",
      "symbol": "obtener_compra",
      "line": 94
    },
    {
      "n": 29,
      "action": 5,
      "a": "control",
      "b": "compra",
      "text": "obtener_compra_por_id(id_compra)",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/services/compra_service.py",
      "symbol": "obtener_compra_por_id",
      "line": 250
    },
    {
      "n": 30,
      "action": 5,
      "a": "compra",
      "b": "control",
      "text": "compra con sus detalles",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 31,
      "action": 5,
      "a": "control",
      "b": "b_pre",
      "text": "detalle de compra",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 32,
      "action": 5,
      "a": "b_pre",
      "b": "actor",
      "text": "Mostrar compra recibida",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    }
  ],
  "views": [
    {
      "name": "CU07 - Robustez simplificada",
      "title": "CU07 - Gestionar proveedores, compras y recepciones - Diagrama de robustez",
      "width": 4600,
      "height": 2258,
      "nodes": {
        "actor": {
          "x": 180,
          "y": 1129
        },
        "b_pre": {
          "x": 1100,
          "y": 1129
        },
        "control": {
          "x": 2400,
          "y": 1129
        },
        "proveedor": {
          "x": 4300,
          "y": 377
        },
        "compra": {
          "x": 4300,
          "y": 793
        },
        "detalle": {
          "x": 4300,
          "y": 1165
        },
        "movimiento": {
          "x": 4300,
          "y": 1520
        },
        "bitacora": {
          "x": 4300,
          "y": 1963
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
              215,
              1129
            ],
            [
              1035,
              1129
            ]
          ],
          "rows": [
            {
              "n": 1,
              "x": 650,
              "y": 893,
              "width": 600,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 7,
              "x": 650,
              "y": 937,
              "width": 600,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 13,
              "x": 650,
              "y": 981,
              "width": 600,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 18,
              "x": 650,
              "y": 1025,
              "width": 600,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 27,
              "x": 650,
              "y": 1069,
              "width": 600,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 6,
              "x": 650,
              "y": 1189,
              "width": 600,
              "height": 44,
              "forward": false,
              "rightward": false
            },
            {
              "n": 26,
              "x": 650,
              "y": 1233,
              "width": 600,
              "height": 44,
              "forward": false,
              "rightward": false
            },
            {
              "n": 32,
              "x": 650,
              "y": 1277,
              "width": 600,
              "height": 44,
              "forward": false,
              "rightward": false
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
              1165,
              1129
            ],
            [
              2335,
              1129
            ]
          ],
          "rows": [
            {
              "n": 2,
              "x": 1650,
              "y": 893,
              "width": 550,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 8,
              "x": 1650,
              "y": 937,
              "width": 550,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 14,
              "x": 1650,
              "y": 981,
              "width": 550,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 19,
              "x": 1650,
              "y": 1025,
              "width": 550,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 28,
              "x": 1650,
              "y": 1069,
              "width": 550,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 5,
              "x": 1650,
              "y": 1189,
              "width": 550,
              "height": 44,
              "forward": false,
              "rightward": false
            },
            {
              "n": 12,
              "x": 1650,
              "y": 1233,
              "width": 550,
              "height": 44,
              "forward": false,
              "rightward": false
            },
            {
              "n": 17,
              "x": 1650,
              "y": 1277,
              "width": 550,
              "height": 44,
              "forward": false,
              "rightward": false
            },
            {
              "n": 25,
              "x": 1650,
              "y": 1321,
              "width": 550,
              "height": 44,
              "forward": false,
              "rightward": false
            },
            {
              "n": 31,
              "x": 1650,
              "y": 1365,
              "width": 550,
              "height": 44,
              "forward": false,
              "rightward": false
            }
          ]
        },
        {
          "pair": [
            "control",
            "proveedor"
          ],
          "points": [
            [
              2465,
              1129
            ],
            [
              2720,
              377
            ],
            [
              4235,
              377
            ]
          ],
          "rows": [
            {
              "n": 3,
              "x": 3300,
              "y": 229,
              "width": 1050,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 9,
              "x": 3300,
              "y": 273,
              "width": 1050,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 15,
              "x": 3300,
              "y": 317,
              "width": 1050,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 4,
              "x": 3300,
              "y": 437,
              "width": 1050,
              "height": 44,
              "forward": false,
              "rightward": false
            },
            {
              "n": 10,
              "x": 3300,
              "y": 481,
              "width": 1050,
              "height": 44,
              "forward": false,
              "rightward": false
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
              2465,
              1129
            ],
            [
              2720,
              1963
            ],
            [
              4235,
              1963
            ]
          ],
          "rows": [
            {
              "n": 11,
              "x": 3300,
              "y": 1815,
              "width": 1050,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 16,
              "x": 3300,
              "y": 1859,
              "width": 1050,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 24,
              "x": 3300,
              "y": 1903,
              "width": 1050,
              "height": 44,
              "forward": true,
              "rightward": true
            }
          ]
        },
        {
          "pair": [
            "control",
            "compra"
          ],
          "points": [
            [
              2465,
              1129
            ],
            [
              2720,
              793
            ],
            [
              4235,
              793
            ]
          ],
          "rows": [
            {
              "n": 20,
              "x": 3300,
              "y": 689,
              "width": 1050,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 29,
              "x": 3300,
              "y": 733,
              "width": 1050,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 21,
              "x": 3300,
              "y": 853,
              "width": 1050,
              "height": 44,
              "forward": false,
              "rightward": false
            },
            {
              "n": 30,
              "x": 3300,
              "y": 897,
              "width": 1050,
              "height": 44,
              "forward": false,
              "rightward": false
            }
          ]
        },
        {
          "pair": [
            "control",
            "detalle"
          ],
          "points": [
            [
              2465,
              1129
            ],
            [
              2720,
              1165
            ],
            [
              4235,
              1165
            ]
          ],
          "rows": [
            {
              "n": 22,
              "x": 3300,
              "y": 1105,
              "width": 1050,
              "height": 44,
              "forward": true,
              "rightward": true
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
              2465,
              1129
            ],
            [
              2720,
              1520
            ],
            [
              4235,
              1520
            ]
          ],
          "rows": [
            {
              "n": 23,
              "x": 3300,
              "y": 1460,
              "width": 1050,
              "height": 44,
              "forward": true,
              "rightward": true
            }
          ]
        }
      ]
    }
  ]
};
var CU07_SCALE = 0.6;

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
    var definition = CU07_MODEL.nodes[key];
    var element = pkg.Elements.AddNew(definition.name, definition.kind == "actor" ? "Actor" : "Object");
    if (definition.kind != "actor") { element.Stereotype = definition.kind; }
    element.Notes = "FashionStore CU07. Identificador lógico: " + key + ".";
    if (definition.table) { element.Notes += " Tabla real: " + definition.table + "."; }
    if (definition.source) { element.Notes += " Fuente: " + definition.source + "."; }
    if (definition.kind == "control") {
        element.Notes += " " + (definition.note || "Control de análisis que agrupa responsabilidades reales del código; no presupone una clase concreta.");
    }
    checkedUpdate(element, "Crear elemento " + key);
    return element;
}

function place(diagram, element, point, kind) {
    var radiusX = kind == "actor" ? 35 : 65;
    var radiusY = 65;
    var left = Math.round((point.x - radiusX) * CU07_SCALE);
    var right = Math.round((point.x + radiusX) * CU07_SCALE);
    var top = -Math.round((point.y - radiusY) * CU07_SCALE);
    var bottom = -Math.round((point.y + radiusY) * CU07_SCALE);
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
    connector.Notes = "CU07 mensaje " + message.n + ". Origen: " + message.a + ". Destino: " + message.b + ".";
    if (message.source) {
        connector.Notes += " Fuente: " + message.source + ":" + message.line + ", " + message.symbol + ".";
    }
    checkedUpdate(connector, "Crear mensaje " + message.n);

    var p1 = positions[pair[0]];
    var p2 = positions[pair[1]];
    var offsetX = Math.round((row.x - (p1.x + p2.x) / 2) * CU07_SCALE);
    var offsetY = -Math.round((row.y - (p1.y + p2.y) / 2) * CU07_SCALE);
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
            place(diagram, elements[key], view.nodes[key], CU07_MODEL.nodes[key].kind);
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
    var root = selected.Packages.AddNew("CU07 - Robustez numerada - " + stamp, "");
    checkedUpdate(root, "Crear paquete principal");
    var byNumber = {};
    for (var i = 0; i < CU07_MODEL.messages.length; i++) {
        byNumber[CU07_MODEL.messages[i].n] = CU07_MODEL.messages[i];
    }
    var firstDiagram = 0;
    for (var vi = 0; vi < CU07_MODEL.views.length; vi++) {
        var generated = generateView(root, CU07_MODEL.views[vi], byNumber);
        if (!firstDiagram) { firstDiagram = generated; }
    }
    root.Packages.Refresh();
    selected.Packages.Refresh();
    Repository.RefreshModelView(selected.PackageID);
    Repository.OpenDiagram(firstDiagram);
    Repository.WriteOutput("Script", "CU07 finalizado: " + CU07_MODEL.messages.length + " mensajes en " + CU07_MODEL.views.length + " vista(s).", 0);
}

main();
