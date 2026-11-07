/* FashionStore CU09. Ejecutar como JScript dentro de Enterprise Architect.
 * Genera un paquete nuevo con las vistas del modelo sin modificar diagramas existentes.
 * Las llamadas nativas y sus referencias proceden del modelo compartido con draw.io.
 * El enlace Association se crea antes de sus mensajes Collaboration, como en el
 * JScript de referencia. PDATA4 conserva el número explícito y SeqNo su orden.
 * Los campos internos de EA se escriben solo para conectores recién creados.
 */

var CU09_MODEL = {
  "nodes": {
    "actor": {
      "kind": "actor",
      "name": "Visitante / Cliente"
    },
    "b_pre": {
      "kind": "boundary",
      "name": "Frontend : Catálogo y asistencia"
    },
    "control": {
      "kind": "control",
      "name": "Backend : Catálogo y asistencia",
      "note": "Control de análisis que agrupa los módulos indicados en las referencias del caso de uso."
    },
    "prenda": {
      "kind": "entity",
      "name": "Prenda",
      "table": "prenda"
    },
    "inventario": {
      "kind": "entity",
      "name": "Disponibilidad",
      "table": "inventario_catalogo"
    },
    "bitacora": {
      "kind": "entity",
      "name": "Bitácora",
      "table": "bitacora"
    },
    "b_ia": {
      "kind": "boundary",
      "name": "Integración : Servicios de IA"
    }
  },
  "messages": [
    {
      "n": 1,
      "action": 1,
      "a": "actor",
      "b": "b_pre",
      "text": "Buscar prendas y aplicar filtros",
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
      "text": "consultar_catalogo(filtros)",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/routers/catalogo.py",
      "symbol": "consultar_catalogo",
      "line": 69
    },
    {
      "n": 3,
      "action": 1,
      "a": "control",
      "b": "prenda",
      "text": "consultar_catalogo(filtros)",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/services/catalogo_service.py",
      "symbol": "consultar_catalogo",
      "line": 95
    },
    {
      "n": 4,
      "action": 1,
      "a": "prenda",
      "b": "control",
      "text": "prendas publicadas",
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
      "text": "catálogo filtrado",
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
      "text": "Mostrar catálogo",
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
      "text": "Consultar ficha y variantes",
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
      "text": "obtener_ficha(id_prenda)",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/routers/catalogo.py",
      "symbol": "obtener_ficha",
      "line": 135
    },
    {
      "n": 9,
      "action": 2,
      "a": "control",
      "b": "prenda",
      "text": "obtener_ficha_publica(id_prenda)",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/services/catalogo_service.py",
      "symbol": "obtener_ficha_publica",
      "line": 300
    },
    {
      "n": 10,
      "action": 2,
      "a": "prenda",
      "b": "control",
      "text": "ficha con variantes y precios",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 11,
      "action": 2,
      "a": "control",
      "b": "b_pre",
      "text": "ficha de prenda",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 12,
      "action": 2,
      "a": "b_pre",
      "b": "actor",
      "text": "Mostrar ficha",
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
      "text": "Consultar disponibilidad",
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
      "text": "consultar_disponibilidad(id_variante)",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/routers/catalogo.py",
      "symbol": "consultar_disponibilidad",
      "line": 169
    },
    {
      "n": 15,
      "action": 3,
      "a": "control",
      "b": "inventario",
      "text": "consultar_disponibilidad(id_variante)",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/services/catalogo_service.py",
      "symbol": "consultar_disponibilidad",
      "line": 266
    },
    {
      "n": 16,
      "action": 3,
      "a": "inventario",
      "b": "control",
      "text": "sucursales con disponible",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 17,
      "action": 3,
      "a": "control",
      "b": "b_pre",
      "text": "disponibilidad",
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
      "text": "Solicitar recomendaciones [cliente]",
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
      "text": "recomendar_outfit(preferencias)",
      "kind": "invoke",
      "color": "#215D9C",
      "source": "Parcial2_backend/app/routers/ia.py",
      "symbol": "recomendar_outfit",
      "line": 75
    },
    {
      "n": 20,
      "action": 4,
      "a": "control",
      "b": "prenda",
      "text": "_obtener_catalogo_activo_con_stock()",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/services/ia_service.py",
      "symbol": "_obtener_catalogo_activo_con_stock",
      "line": 98
    },
    {
      "n": 21,
      "action": 4,
      "a": "prenda",
      "b": "control",
      "text": "catálogo autorizado",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 22,
      "action": 4,
      "a": "control",
      "b": "b_ia",
      "text": "Generar recomendaciones [si proveedor disponible]",
      "kind": "invoke",
      "color": "#215D9C",
      "source": "Parcial2_backend/app/services/ia_service.py",
      "symbol": "recomendar_outfit",
      "line": 165
    },
    {
      "n": 23,
      "action": 4,
      "a": "b_ia",
      "b": "control",
      "text": "sugerencias para validar / fallo de proveedor",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 24,
      "action": 4,
      "a": "control",
      "b": "bitacora",
      "text": "registrar_bitacora(recomendación IA)",
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
      "text": "recomendaciones validadas o alternativa local",
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
      "text": "Mostrar recomendaciones",
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
      "text": "Abrir vestidor [opcional]",
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
      "text": "obtener_realtime_token()",
      "kind": "invoke",
      "color": "#215D9C",
      "source": "Parcial2_backend/app/routers/ia.py",
      "symbol": "obtener_realtime_token",
      "line": 181
    },
    {
      "n": 29,
      "action": 5,
      "a": "control",
      "b": "bitacora",
      "text": "registrar_bitacora(inicio de vestidor)",
      "kind": "write",
      "color": "#AC3636",
      "source": "Parcial2_backend/app/services/bitacora_service.py",
      "symbol": "registrar_bitacora",
      "line": 65
    },
    {
      "n": 30,
      "action": 5,
      "a": "control",
      "b": "b_ia",
      "text": "create_realtime_token()",
      "kind": "invoke",
      "color": "#215D9C",
      "source": "Parcial2_backend/app/services/tryon_service.py",
      "symbol": "create_realtime_token",
      "line": 789
    },
    {
      "n": 31,
      "action": 5,
      "a": "b_ia",
      "b": "control",
      "text": "token efímero y configuración",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 32,
      "action": 5,
      "a": "control",
      "b": "b_pre",
      "text": "acceso al vestidor",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 33,
      "action": 5,
      "a": "b_pre",
      "b": "actor",
      "text": "Abrir cámara y vestidor",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    }
  ],
  "views": [
    {
      "name": "CU09 - Robustez simplificada",
      "title": "CU09 - Explorar catálogo y asistencia de compra - Diagrama de robustez",
      "width": 4600,
      "height": 2100,
      "nodes": {
        "actor": {
          "x": 180,
          "y": 1050
        },
        "b_pre": {
          "x": 1100,
          "y": 1050
        },
        "control": {
          "x": 2400,
          "y": 1050
        },
        "prenda": {
          "x": 4300,
          "y": 377
        },
        "inventario": {
          "x": 4300,
          "y": 793
        },
        "bitacora": {
          "x": 4300,
          "y": 1192
        },
        "b_ia": {
          "x": 4300,
          "y": 1547
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
              1050
            ],
            [
              1035,
              1050
            ]
          ],
          "rows": [
            {
              "n": 1,
              "x": 650,
              "y": 814,
              "width": 600,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 7,
              "x": 650,
              "y": 858,
              "width": 600,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 13,
              "x": 650,
              "y": 902,
              "width": 600,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 18,
              "x": 650,
              "y": 946,
              "width": 600,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 27,
              "x": 650,
              "y": 990,
              "width": 600,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 6,
              "x": 650,
              "y": 1110,
              "width": 600,
              "height": 44,
              "forward": false,
              "rightward": false
            },
            {
              "n": 12,
              "x": 650,
              "y": 1154,
              "width": 600,
              "height": 44,
              "forward": false,
              "rightward": false
            },
            {
              "n": 26,
              "x": 650,
              "y": 1198,
              "width": 600,
              "height": 44,
              "forward": false,
              "rightward": false
            },
            {
              "n": 33,
              "x": 650,
              "y": 1242,
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
              1050
            ],
            [
              2335,
              1050
            ]
          ],
          "rows": [
            {
              "n": 2,
              "x": 1650,
              "y": 814,
              "width": 550,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 8,
              "x": 1650,
              "y": 858,
              "width": 550,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 14,
              "x": 1650,
              "y": 902,
              "width": 550,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 19,
              "x": 1650,
              "y": 946,
              "width": 550,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 28,
              "x": 1650,
              "y": 990,
              "width": 550,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 5,
              "x": 1650,
              "y": 1110,
              "width": 550,
              "height": 44,
              "forward": false,
              "rightward": false
            },
            {
              "n": 11,
              "x": 1650,
              "y": 1154,
              "width": 550,
              "height": 44,
              "forward": false,
              "rightward": false
            },
            {
              "n": 17,
              "x": 1650,
              "y": 1198,
              "width": 550,
              "height": 44,
              "forward": false,
              "rightward": false
            },
            {
              "n": 25,
              "x": 1650,
              "y": 1258,
              "width": 550,
              "height": 76,
              "forward": false,
              "rightward": false
            },
            {
              "n": 32,
              "x": 1650,
              "y": 1318,
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
            "prenda"
          ],
          "points": [
            [
              2465,
              1050
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
              "n": 20,
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
            },
            {
              "n": 21,
              "x": 3300,
              "y": 525,
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
            "inventario"
          ],
          "points": [
            [
              2465,
              1050
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
              "n": 15,
              "x": 3300,
              "y": 733,
              "width": 1050,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 16,
              "x": 3300,
              "y": 853,
              "width": 1050,
              "height": 44,
              "forward": false,
              "rightward": false
            }
          ]
        },
        {
          "pair": [
            "b_ia",
            "control"
          ],
          "points": [
            [
              4235,
              1547
            ],
            [
              2720,
              1547
            ],
            [
              2465,
              1050
            ]
          ],
          "rows": [
            {
              "n": 23,
              "x": 3300,
              "y": 1443,
              "width": 1050,
              "height": 44,
              "forward": true,
              "rightward": false
            },
            {
              "n": 31,
              "x": 3300,
              "y": 1487,
              "width": 1050,
              "height": 44,
              "forward": true,
              "rightward": false
            },
            {
              "n": 22,
              "x": 3300,
              "y": 1607,
              "width": 1050,
              "height": 44,
              "forward": false,
              "rightward": true
            },
            {
              "n": 30,
              "x": 3300,
              "y": 1651,
              "width": 1050,
              "height": 44,
              "forward": false,
              "rightward": true
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
              1050
            ],
            [
              2720,
              1192
            ],
            [
              4235,
              1192
            ]
          ],
          "rows": [
            {
              "n": 24,
              "x": 3300,
              "y": 1088,
              "width": 1050,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 29,
              "x": 3300,
              "y": 1132,
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
var CU09_SCALE = 0.6;

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
    var definition = CU09_MODEL.nodes[key];
    var element = pkg.Elements.AddNew(definition.name, definition.kind == "actor" ? "Actor" : "Object");
    if (definition.kind != "actor") { element.Stereotype = definition.kind; }
    element.Notes = "FashionStore CU09. Identificador lógico: " + key + ".";
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
    var left = Math.round((point.x - radiusX) * CU09_SCALE);
    var right = Math.round((point.x + radiusX) * CU09_SCALE);
    var top = -Math.round((point.y - radiusY) * CU09_SCALE);
    var bottom = -Math.round((point.y + radiusY) * CU09_SCALE);
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
    connector.Notes = "CU09 mensaje " + message.n + ". Origen: " + message.a + ". Destino: " + message.b + ".";
    if (message.source) {
        connector.Notes += " Fuente: " + message.source + ":" + message.line + ", " + message.symbol + ".";
    }
    checkedUpdate(connector, "Crear mensaje " + message.n);

    var p1 = positions[pair[0]];
    var p2 = positions[pair[1]];
    var offsetX = Math.round((row.x - (p1.x + p2.x) / 2) * CU09_SCALE);
    var offsetY = -Math.round((row.y - (p1.y + p2.y) / 2) * CU09_SCALE);
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
            place(diagram, elements[key], view.nodes[key], CU09_MODEL.nodes[key].kind);
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
    var root = selected.Packages.AddNew("CU09 - Robustez numerada - " + stamp, "");
    checkedUpdate(root, "Crear paquete principal");
    var byNumber = {};
    for (var i = 0; i < CU09_MODEL.messages.length; i++) {
        byNumber[CU09_MODEL.messages[i].n] = CU09_MODEL.messages[i];
    }
    var firstDiagram = 0;
    for (var vi = 0; vi < CU09_MODEL.views.length; vi++) {
        var generated = generateView(root, CU09_MODEL.views[vi], byNumber);
        if (!firstDiagram) { firstDiagram = generated; }
    }
    root.Packages.Refresh();
    selected.Packages.Refresh();
    Repository.RefreshModelView(selected.PackageID);
    Repository.OpenDiagram(firstDiagram);
    Repository.WriteOutput("Script", "CU09 finalizado: " + CU09_MODEL.messages.length + " mensajes en " + CU09_MODEL.views.length + " vista(s).", 0);
}

main();
