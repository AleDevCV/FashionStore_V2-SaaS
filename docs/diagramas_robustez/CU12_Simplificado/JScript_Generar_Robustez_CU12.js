/* FashionStore CU12. Ejecutar como JScript dentro de Enterprise Architect.
 * Genera un paquete nuevo con las vistas del modelo sin modificar diagramas existentes.
 * Las llamadas nativas y sus referencias proceden del modelo compartido con draw.io.
 * El enlace Association se crea antes de sus mensajes Collaboration, como en el
 * JScript de referencia. PDATA4 conserva el número explícito y SeqNo su orden.
 * Los campos internos de EA se escriben solo para conectores recién creados.
 */

var CU12_MODEL = {
  "nodes": {
    "actor": {
      "kind": "actor",
      "name": "Cliente"
    },
    "b_pre": {
      "kind": "boundary",
      "name": "Frontend : Reservas y atención"
    },
    "control": {
      "kind": "control",
      "name": "Backend : Gestión de reservas",
      "note": "Control de análisis que agrupa los módulos indicados en las referencias del caso de uso."
    },
    "staff": {
      "kind": "actor",
      "name": "Personal autorizado"
    },
    "inventario": {
      "kind": "entity",
      "name": "Inventario",
      "table": "inventario"
    },
    "reserva": {
      "kind": "entity",
      "name": "Reserva",
      "table": "reserva"
    },
    "retencion": {
      "kind": "entity",
      "name": "Retención",
      "table": "retencion"
    },
    "venta": {
      "kind": "entity",
      "name": "Venta pagada",
      "table": "venta"
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
      "text": "Registrar reserva de prendas",
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
      "text": "crear_reserva(cliente, sucursal, ítems)",
      "kind": "invoke",
      "color": "#215D9C",
      "source": "Parcial2_backend/app/routers/ventas.py",
      "symbol": "crear_reserva",
      "line": 70
    },
    {
      "n": 3,
      "action": 1,
      "a": "control",
      "b": "inventario",
      "text": "quote(ítems, sucursal)",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/services/commerce.py",
      "symbol": "quote",
      "line": 26
    },
    {
      "n": 4,
      "action": 1,
      "a": "inventario",
      "b": "control",
      "text": "disponibilidad y precios válidos",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 5,
      "action": 1,
      "a": "control",
      "b": "reserva",
      "text": "reserve(cliente, sucursal, ítems)",
      "kind": "write",
      "color": "#AC3636",
      "source": "Parcial2_backend/app/services/commerce.py",
      "symbol": "reserve",
      "line": 49
    },
    {
      "n": 6,
      "action": 1,
      "a": "reserva",
      "b": "control",
      "text": "id_reserva",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 7,
      "action": 1,
      "a": "control",
      "b": "retencion",
      "text": "Retener unidades durante 24 horas",
      "kind": "write",
      "color": "#AC3636",
      "source": "Parcial2_backend/app/services/commerce.py",
      "symbol": "reserve",
      "line": 49
    },
    {
      "n": 8,
      "action": 1,
      "a": "control",
      "b": "bitacora",
      "text": "Auditar reserva",
      "kind": "write",
      "color": "#AC3636",
      "source": "Parcial2_backend/app/services/commerce.py",
      "symbol": "reserve",
      "line": 49
    },
    {
      "n": 9,
      "action": 1,
      "a": "control",
      "b": "b_pre",
      "text": "reserva pendiente",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 10,
      "action": 1,
      "a": "b_pre",
      "b": "actor",
      "text": "Mostrar reserva",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 11,
      "action": 2,
      "a": "actor",
      "b": "b_pre",
      "text": "Consultar reserva propia",
      "kind": "ui",
      "color": "#28343E",
      "source": null,
      "symbol": null
    },
    {
      "n": 12,
      "action": 2,
      "a": "b_pre",
      "b": "control",
      "text": "obtener_reserva(id_reserva)",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/routers/ventas.py",
      "symbol": "obtener_reserva",
      "line": 91
    },
    {
      "n": 13,
      "action": 2,
      "a": "control",
      "b": "reserva",
      "text": "obtener_reserva_por_id(id_reserva)",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/services/venta_service.py",
      "symbol": "obtener_reserva_por_id",
      "line": 88
    },
    {
      "n": 14,
      "action": 2,
      "a": "reserva",
      "b": "control",
      "text": "reserva y detalles",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 15,
      "action": 2,
      "a": "control",
      "b": "b_pre",
      "text": "reserva",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 16,
      "action": 2,
      "a": "b_pre",
      "b": "actor",
      "text": "Mostrar seguimiento",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 17,
      "action": 3,
      "a": "staff",
      "b": "b_pre",
      "text": "Preparar prendas",
      "kind": "ui",
      "color": "#28343E",
      "source": null,
      "symbol": null
    },
    {
      "n": 18,
      "action": 3,
      "a": "b_pre",
      "b": "control",
      "text": "actualizar_estado_reserva_endpoint(id, 'Preparado')",
      "kind": "invoke",
      "color": "#215D9C",
      "source": "Parcial2_backend/app/routers/ventas.py",
      "symbol": "actualizar_estado_reserva_endpoint",
      "line": 283
    },
    {
      "n": 19,
      "action": 3,
      "a": "control",
      "b": "reserva",
      "text": "transition_reservation(id, 'Preparado')",
      "kind": "write",
      "color": "#AC3636",
      "source": "Parcial2_backend/app/services/commerce.py",
      "symbol": "transition_reservation",
      "line": 64
    },
    {
      "n": 20,
      "action": 3,
      "a": "control",
      "b": "b_pre",
      "text": "reserva preparada",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 21,
      "action": 4,
      "a": "staff",
      "b": "b_pre",
      "text": "Entregar reserva ya pagada",
      "kind": "ui",
      "color": "#28343E",
      "source": null,
      "symbol": null
    },
    {
      "n": 22,
      "action": 4,
      "a": "b_pre",
      "b": "control",
      "text": "deliver(id_venta)",
      "kind": "invoke",
      "color": "#215D9C",
      "source": "Parcial2_backend/app/routers/order_lifecycle.py",
      "symbol": "deliver",
      "line": 30
    },
    {
      "n": 23,
      "action": 4,
      "a": "control",
      "b": "venta",
      "text": "Registrar entrega [venta pagada existente]",
      "kind": "write",
      "color": "#AC3636",
      "source": "Parcial2_backend/app/routers/order_lifecycle.py",
      "symbol": "deliver",
      "line": 30
    },
    {
      "n": 24,
      "action": 4,
      "a": "control",
      "b": "reserva",
      "text": "Marcar reserva 'Atendido'",
      "kind": "write",
      "color": "#AC3636",
      "source": "Parcial2_backend/app/routers/order_lifecycle.py",
      "symbol": "deliver",
      "line": 30
    },
    {
      "n": 25,
      "action": 4,
      "a": "control",
      "b": "b_pre",
      "text": "entrega confirmada",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 26,
      "action": 4,
      "a": "b_pre",
      "b": "staff",
      "text": "Mostrar entrega registrada",
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
      "text": "Cancelar reserva sin pago",
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
      "text": "cancel(id_reserva)",
      "kind": "invoke",
      "color": "#215D9C",
      "source": "Parcial2_backend/app/routers/order_lifecycle.py",
      "symbol": "cancel",
      "line": 20
    },
    {
      "n": 29,
      "action": 5,
      "a": "control",
      "b": "retencion",
      "text": "Liberar retenciones",
      "kind": "write",
      "color": "#AC3636",
      "source": "Parcial2_backend/app/routers/order_lifecycle.py",
      "symbol": "cancel",
      "line": 20
    },
    {
      "n": 30,
      "action": 5,
      "a": "control",
      "b": "reserva",
      "text": "Marcar reserva 'Cancelado'",
      "kind": "write",
      "color": "#AC3636",
      "source": "Parcial2_backend/app/routers/order_lifecycle.py",
      "symbol": "cancel",
      "line": 20
    },
    {
      "n": 31,
      "action": 5,
      "a": "control",
      "b": "b_pre",
      "text": "reserva cancelada",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    }
  ],
  "views": [
    {
      "name": "CU12 - Robustez simplificada",
      "title": "CU12 - Gestionar reservas de prendas - Diagrama de robustez",
      "width": 4600,
      "height": 2268,
      "nodes": {
        "actor": {
          "x": 180,
          "y": 1134
        },
        "b_pre": {
          "x": 1100,
          "y": 1134
        },
        "control": {
          "x": 2400,
          "y": 1134
        },
        "inventario": {
          "x": 4300,
          "y": 289
        },
        "reserva": {
          "x": 4300,
          "y": 820
        },
        "retencion": {
          "x": 4300,
          "y": 1236
        },
        "venta": {
          "x": 4300,
          "y": 1547
        },
        "bitacora": {
          "x": 4300,
          "y": 1902
        },
        "staff": {
          "x": 180,
          "y": 1918
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
              1134
            ],
            [
              1035,
              1134
            ]
          ],
          "rows": [
            {
              "n": 1,
              "x": 650,
              "y": 986,
              "width": 600,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 11,
              "x": 650,
              "y": 1030,
              "width": 600,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 27,
              "x": 650,
              "y": 1074,
              "width": 600,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 10,
              "x": 650,
              "y": 1194,
              "width": 600,
              "height": 44,
              "forward": false,
              "rightward": false
            },
            {
              "n": 16,
              "x": 650,
              "y": 1238,
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
              1134
            ],
            [
              2335,
              1134
            ]
          ],
          "rows": [
            {
              "n": 2,
              "x": 1650,
              "y": 866,
              "width": 550,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 12,
              "x": 1650,
              "y": 910,
              "width": 550,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 18,
              "x": 1650,
              "y": 970,
              "width": 550,
              "height": 76,
              "forward": true,
              "rightward": true
            },
            {
              "n": 22,
              "x": 1650,
              "y": 1030,
              "width": 550,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 28,
              "x": 1650,
              "y": 1074,
              "width": 550,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 9,
              "x": 1650,
              "y": 1194,
              "width": 550,
              "height": 44,
              "forward": false,
              "rightward": false
            },
            {
              "n": 15,
              "x": 1650,
              "y": 1238,
              "width": 550,
              "height": 44,
              "forward": false,
              "rightward": false
            },
            {
              "n": 20,
              "x": 1650,
              "y": 1282,
              "width": 550,
              "height": 44,
              "forward": false,
              "rightward": false
            },
            {
              "n": 25,
              "x": 1650,
              "y": 1326,
              "width": 550,
              "height": 44,
              "forward": false,
              "rightward": false
            },
            {
              "n": 31,
              "x": 1650,
              "y": 1370,
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
            "inventario"
          ],
          "points": [
            [
              2465,
              1134
            ],
            [
              2720,
              289
            ],
            [
              4235,
              289
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
              "n": 4,
              "x": 3300,
              "y": 349,
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
            "reserva"
          ],
          "points": [
            [
              2465,
              1134
            ],
            [
              2720,
              820
            ],
            [
              4235,
              820
            ]
          ],
          "rows": [
            {
              "n": 5,
              "x": 3300,
              "y": 584,
              "width": 1050,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 13,
              "x": 3300,
              "y": 628,
              "width": 1050,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 19,
              "x": 3300,
              "y": 672,
              "width": 1050,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 24,
              "x": 3300,
              "y": 716,
              "width": 1050,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 30,
              "x": 3300,
              "y": 760,
              "width": 1050,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 6,
              "x": 3300,
              "y": 880,
              "width": 1050,
              "height": 44,
              "forward": false,
              "rightward": false
            },
            {
              "n": 14,
              "x": 3300,
              "y": 924,
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
            "retencion"
          ],
          "points": [
            [
              2465,
              1134
            ],
            [
              2720,
              1236
            ],
            [
              4235,
              1236
            ]
          ],
          "rows": [
            {
              "n": 7,
              "x": 3300,
              "y": 1132,
              "width": 1050,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 29,
              "x": 3300,
              "y": 1176,
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
            "bitacora"
          ],
          "points": [
            [
              2465,
              1134
            ],
            [
              2720,
              1902
            ],
            [
              4235,
              1902
            ]
          ],
          "rows": [
            {
              "n": 8,
              "x": 3300,
              "y": 1842,
              "width": 1050,
              "height": 44,
              "forward": true,
              "rightward": true
            }
          ]
        },
        {
          "pair": [
            "staff",
            "b_pre"
          ],
          "points": [
            [
              215,
              1918
            ],
            [
              340,
              1858
            ],
            [
              1035,
              1134
            ]
          ],
          "rows": [
            {
              "n": 17,
              "x": 650,
              "y": 1754,
              "width": 600,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 21,
              "x": 650,
              "y": 1798,
              "width": 600,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 26,
              "x": 650,
              "y": 1918,
              "width": 600,
              "height": 44,
              "forward": false,
              "rightward": false
            }
          ]
        },
        {
          "pair": [
            "control",
            "venta"
          ],
          "points": [
            [
              2465,
              1134
            ],
            [
              2720,
              1547
            ],
            [
              4235,
              1547
            ]
          ],
          "rows": [
            {
              "n": 23,
              "x": 3300,
              "y": 1487,
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
var CU12_SCALE = 0.6;

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
    var definition = CU12_MODEL.nodes[key];
    var element = pkg.Elements.AddNew(definition.name, definition.kind == "actor" ? "Actor" : "Object");
    if (definition.kind != "actor") { element.Stereotype = definition.kind; }
    element.Notes = "FashionStore CU12. Identificador lógico: " + key + ".";
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
    var left = Math.round((point.x - radiusX) * CU12_SCALE);
    var right = Math.round((point.x + radiusX) * CU12_SCALE);
    var top = -Math.round((point.y - radiusY) * CU12_SCALE);
    var bottom = -Math.round((point.y + radiusY) * CU12_SCALE);
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
    connector.Notes = "CU12 mensaje " + message.n + ". Origen: " + message.a + ". Destino: " + message.b + ".";
    if (message.source) {
        connector.Notes += " Fuente: " + message.source + ":" + message.line + ", " + message.symbol + ".";
    }
    checkedUpdate(connector, "Crear mensaje " + message.n);

    var p1 = positions[pair[0]];
    var p2 = positions[pair[1]];
    var offsetX = Math.round((row.x - (p1.x + p2.x) / 2) * CU12_SCALE);
    var offsetY = -Math.round((row.y - (p1.y + p2.y) / 2) * CU12_SCALE);
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
            place(diagram, elements[key], view.nodes[key], CU12_MODEL.nodes[key].kind);
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
    var root = selected.Packages.AddNew("CU12 - Robustez numerada - " + stamp, "");
    checkedUpdate(root, "Crear paquete principal");
    var byNumber = {};
    for (var i = 0; i < CU12_MODEL.messages.length; i++) {
        byNumber[CU12_MODEL.messages[i].n] = CU12_MODEL.messages[i];
    }
    var firstDiagram = 0;
    for (var vi = 0; vi < CU12_MODEL.views.length; vi++) {
        var generated = generateView(root, CU12_MODEL.views[vi], byNumber);
        if (!firstDiagram) { firstDiagram = generated; }
    }
    root.Packages.Refresh();
    selected.Packages.Refresh();
    Repository.RefreshModelView(selected.PackageID);
    Repository.OpenDiagram(firstDiagram);
    Repository.WriteOutput("Script", "CU12 finalizado: " + CU12_MODEL.messages.length + " mensajes en " + CU12_MODEL.views.length + " vista(s).", 0);
}

main();
