/* FashionStore CU11. Ejecutar como JScript dentro de Enterprise Architect.
 * Genera un paquete nuevo con las vistas del modelo sin modificar diagramas existentes.
 * Las llamadas nativas y sus referencias proceden del modelo compartido con draw.io.
 * El enlace Association se crea antes de sus mensajes Collaboration, como en el
 * JScript de referencia. PDATA4 conserva el número explícito y SeqNo su orden.
 * Los campos internos de EA se escriben solo para conectores recién creados.
 */

var CU11_MODEL = {
  "nodes": {
    "actor": {
      "kind": "actor",
      "name": "Cliente"
    },
    "b_pre": {
      "kind": "boundary",
      "name": "Frontend : Carrito y checkout"
    },
    "control": {
      "kind": "control",
      "name": "Backend : Compra y pago",
      "note": "Control de análisis que agrupa los módulos indicados en las referencias del caso de uso."
    },
    "reserva": {
      "kind": "entity",
      "name": "Reserva",
      "table": "reserva"
    },
    "pago": {
      "kind": "entity",
      "name": "Pago",
      "table": "pago_transaccion"
    },
    "venta": {
      "kind": "entity",
      "name": "Venta",
      "table": "venta"
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
    },
    "b_stripe": {
      "kind": "boundary",
      "name": "Pasarela : Stripe"
    }
  },
  "messages": [
    {
      "n": 1,
      "action": 1,
      "a": "actor",
      "b": "b_pre",
      "text": "Preparar compra y confirmar resumen",
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
      "text": "crear_reserva(carrito, sucursal)",
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
      "b": "reserva",
      "text": "reserve(cliente, sucursal, ítems)",
      "kind": "write",
      "color": "#AC3636",
      "source": "Parcial2_backend/app/services/commerce.py",
      "symbol": "reserve",
      "line": 49
    },
    {
      "n": 4,
      "action": 1,
      "a": "reserva",
      "b": "control",
      "text": "reserva y total autorizado",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 5,
      "action": 1,
      "a": "control",
      "b": "bitacora",
      "text": "Auditar reserva de checkout",
      "kind": "write",
      "color": "#AC3636",
      "source": "Parcial2_backend/app/services/commerce.py",
      "symbol": "reserve",
      "line": 49
    },
    {
      "n": 6,
      "action": 1,
      "a": "control",
      "b": "b_pre",
      "text": "reserva pendiente de pago",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 7,
      "action": 1,
      "a": "b_pre",
      "b": "actor",
      "text": "Mostrar total y medios de pago",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 8,
      "action": 2,
      "a": "actor",
      "b": "b_pre",
      "text": "Iniciar pago de prueba",
      "kind": "ui",
      "color": "#28343E",
      "source": null,
      "symbol": null
    },
    {
      "n": 9,
      "action": 2,
      "a": "b_pre",
      "b": "control",
      "text": "crear_sesion_stripe(id_reserva)",
      "kind": "invoke",
      "color": "#215D9C",
      "source": "Parcial2_backend/app/routers/pagos.py",
      "symbol": "crear_sesion_stripe",
      "line": 43
    },
    {
      "n": 10,
      "action": 2,
      "a": "control",
      "b": "b_stripe",
      "text": "Crear sesión de pago Stripe",
      "kind": "invoke",
      "color": "#215D9C",
      "source": "Parcial2_backend/app/services/payments.py",
      "symbol": "checkout",
      "line": 25
    },
    {
      "n": 11,
      "action": 2,
      "a": "b_stripe",
      "b": "control",
      "text": "sesión y URL de pago",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 12,
      "action": 2,
      "a": "control",
      "b": "pago",
      "text": "Guardar intento Pendiente",
      "kind": "write",
      "color": "#AC3636",
      "source": "Parcial2_backend/app/services/payments.py",
      "symbol": "checkout",
      "line": 25
    },
    {
      "n": 13,
      "action": 2,
      "a": "control",
      "b": "b_pre",
      "text": "URL de pago",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 14,
      "action": 2,
      "a": "b_pre",
      "b": "actor",
      "text": "Abrir portal Stripe",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 15,
      "action": 3,
      "a": "actor",
      "b": "b_stripe",
      "text": "Completar pago de prueba",
      "kind": "ui",
      "color": "#28343E",
      "source": null,
      "symbol": null
    },
    {
      "n": 16,
      "action": 3,
      "a": "b_stripe",
      "b": "control",
      "text": "stripe_webhook(evento, firma)",
      "kind": "invoke",
      "color": "#215D9C",
      "source": "Parcial2_backend/app/routers/pagos.py",
      "symbol": "stripe_webhook",
      "line": 64
    },
    {
      "n": 17,
      "action": 3,
      "a": "control",
      "b": "reserva",
      "text": "Validar reserva e importe del evento",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/services/payments.py",
      "symbol": "webhook",
      "line": 65
    },
    {
      "n": 18,
      "action": 3,
      "a": "reserva",
      "b": "control",
      "text": "reserva e importe esperado",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 19,
      "action": 3,
      "a": "control",
      "b": "venta",
      "text": "confirm_reservation(pago verificado)",
      "kind": "write",
      "color": "#AC3636",
      "source": "Parcial2_backend/app/services/commerce.py",
      "symbol": "confirm_reservation",
      "line": 77
    },
    {
      "n": 20,
      "action": 3,
      "a": "venta",
      "b": "control",
      "text": "id_venta",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 21,
      "action": 3,
      "a": "control",
      "b": "movimiento",
      "text": "Registrar Salida [por detalle]",
      "kind": "write",
      "color": "#AC3636",
      "source": "Parcial2_backend/app/services/commerce.py",
      "symbol": "confirm_reservation",
      "line": 77
    },
    {
      "n": 22,
      "action": 3,
      "a": "control",
      "b": "pago",
      "text": "Aprobar pago y enlazar venta",
      "kind": "write",
      "color": "#AC3636",
      "source": "Parcial2_backend/app/services/payments.py",
      "symbol": "webhook",
      "line": 65
    },
    {
      "n": 23,
      "action": 3,
      "a": "control",
      "b": "b_stripe",
      "text": "evento procesado de forma idempotente",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 24,
      "action": 4,
      "a": "actor",
      "b": "b_pre",
      "text": "Consultar resultado del pago",
      "kind": "ui",
      "color": "#28343E",
      "source": null,
      "symbol": null
    },
    {
      "n": 25,
      "action": 4,
      "a": "b_pre",
      "b": "control",
      "text": "payment_status(id_reserva)",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/routers/order_lifecycle.py",
      "symbol": "payment_status",
      "line": 9
    },
    {
      "n": 26,
      "action": 4,
      "a": "control",
      "b": "venta",
      "text": "obtener_venta_por_id(id_venta [si pagada])",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/services/venta_service.py",
      "symbol": "obtener_venta_por_id",
      "line": 145
    },
    {
      "n": 27,
      "action": 4,
      "a": "venta",
      "b": "control",
      "text": "venta confirmada",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 28,
      "action": 4,
      "a": "control",
      "b": "b_pre",
      "text": "estado pagado y venta",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 29,
      "action": 4,
      "a": "b_pre",
      "b": "actor",
      "text": "Mostrar compra confirmada",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    }
  ],
  "views": [
    {
      "name": "CU11 - Robustez simplificada",
      "title": "CU11 - Realizar compra y pago en línea - Diagrama de robustez",
      "width": 4600,
      "height": 2913,
      "nodes": {
        "actor": {
          "x": 180,
          "y": 1306.5
        },
        "b_pre": {
          "x": 1100,
          "y": 1306.5
        },
        "control": {
          "x": 2400,
          "y": 1306.5
        },
        "reserva": {
          "x": 4300,
          "y": 333
        },
        "pago": {
          "x": 4300,
          "y": 749
        },
        "venta": {
          "x": 4300,
          "y": 1104
        },
        "movimiento": {
          "x": 4300,
          "y": 1476
        },
        "bitacora": {
          "x": 4300,
          "y": 1831
        },
        "b_stripe": {
          "x": 4300,
          "y": 2230
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
              1306.5
            ],
            [
              1035,
              1306.5
            ]
          ],
          "rows": [
            {
              "n": 1,
              "x": 650,
              "y": 1158.5,
              "width": 600,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 8,
              "x": 650,
              "y": 1202.5,
              "width": 600,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 24,
              "x": 650,
              "y": 1246.5,
              "width": 600,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 7,
              "x": 650,
              "y": 1366.5,
              "width": 600,
              "height": 44,
              "forward": false,
              "rightward": false
            },
            {
              "n": 14,
              "x": 650,
              "y": 1410.5,
              "width": 600,
              "height": 44,
              "forward": false,
              "rightward": false
            },
            {
              "n": 29,
              "x": 650,
              "y": 1454.5,
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
              1306.5
            ],
            [
              2335,
              1306.5
            ]
          ],
          "rows": [
            {
              "n": 2,
              "x": 1650,
              "y": 1158.5,
              "width": 550,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 9,
              "x": 1650,
              "y": 1202.5,
              "width": 550,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 25,
              "x": 1650,
              "y": 1246.5,
              "width": 550,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 6,
              "x": 1650,
              "y": 1366.5,
              "width": 550,
              "height": 44,
              "forward": false,
              "rightward": false
            },
            {
              "n": 13,
              "x": 1650,
              "y": 1410.5,
              "width": 550,
              "height": 44,
              "forward": false,
              "rightward": false
            },
            {
              "n": 28,
              "x": 1650,
              "y": 1454.5,
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
            "reserva"
          ],
          "points": [
            [
              2465,
              1306.5
            ],
            [
              2720,
              333
            ],
            [
              4235,
              333
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
              "n": 17,
              "x": 3300,
              "y": 273,
              "width": 1050,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 4,
              "x": 3300,
              "y": 393,
              "width": 1050,
              "height": 44,
              "forward": false,
              "rightward": false
            },
            {
              "n": 18,
              "x": 3300,
              "y": 437,
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
              1306.5
            ],
            [
              2720,
              1831
            ],
            [
              4235,
              1831
            ]
          ],
          "rows": [
            {
              "n": 5,
              "x": 3300,
              "y": 1771,
              "width": 1050,
              "height": 44,
              "forward": true,
              "rightward": true
            }
          ]
        },
        {
          "pair": [
            "b_stripe",
            "control"
          ],
          "points": [
            [
              4235,
              2230
            ],
            [
              2720,
              2230
            ],
            [
              2465,
              1306.5
            ]
          ],
          "rows": [
            {
              "n": 11,
              "x": 3300,
              "y": 2126,
              "width": 1050,
              "height": 44,
              "forward": true,
              "rightward": false
            },
            {
              "n": 16,
              "x": 3300,
              "y": 2170,
              "width": 1050,
              "height": 44,
              "forward": true,
              "rightward": false
            },
            {
              "n": 10,
              "x": 3300,
              "y": 2290,
              "width": 1050,
              "height": 44,
              "forward": false,
              "rightward": true
            },
            {
              "n": 23,
              "x": 3300,
              "y": 2334,
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
            "pago"
          ],
          "points": [
            [
              2465,
              1306.5
            ],
            [
              2720,
              749
            ],
            [
              4235,
              749
            ]
          ],
          "rows": [
            {
              "n": 12,
              "x": 3300,
              "y": 645,
              "width": 1050,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 22,
              "x": 3300,
              "y": 689,
              "width": 1050,
              "height": 44,
              "forward": true,
              "rightward": true
            }
          ]
        },
        {
          "pair": [
            "actor",
            "b_stripe"
          ],
          "points": [
            [
              215,
              1306.5
            ],
            [
              340,
              2763
            ],
            [
              4300,
              2763
            ],
            [
              4300,
              2295
            ]
          ],
          "rows": [
            {
              "n": 15,
              "x": 1500,
              "y": 2703,
              "width": 800,
              "height": 44,
              "forward": true,
              "rightward": true
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
              1306.5
            ],
            [
              2720,
              1104
            ],
            [
              4235,
              1104
            ]
          ],
          "rows": [
            {
              "n": 19,
              "x": 3300,
              "y": 1000,
              "width": 1050,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 26,
              "x": 3300,
              "y": 1044,
              "width": 1050,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 20,
              "x": 3300,
              "y": 1164,
              "width": 1050,
              "height": 44,
              "forward": false,
              "rightward": false
            },
            {
              "n": 27,
              "x": 3300,
              "y": 1208,
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
            "movimiento"
          ],
          "points": [
            [
              2465,
              1306.5
            ],
            [
              2720,
              1476
            ],
            [
              4235,
              1476
            ]
          ],
          "rows": [
            {
              "n": 21,
              "x": 3300,
              "y": 1416,
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
var CU11_SCALE = 0.6;

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
    var definition = CU11_MODEL.nodes[key];
    var element = pkg.Elements.AddNew(definition.name, definition.kind == "actor" ? "Actor" : "Object");
    if (definition.kind != "actor") { element.Stereotype = definition.kind; }
    element.Notes = "FashionStore CU11. Identificador lógico: " + key + ".";
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
    var left = Math.round((point.x - radiusX) * CU11_SCALE);
    var right = Math.round((point.x + radiusX) * CU11_SCALE);
    var top = -Math.round((point.y - radiusY) * CU11_SCALE);
    var bottom = -Math.round((point.y + radiusY) * CU11_SCALE);
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
    connector.Notes = "CU11 mensaje " + message.n + ". Origen: " + message.a + ". Destino: " + message.b + ".";
    if (message.source) {
        connector.Notes += " Fuente: " + message.source + ":" + message.line + ", " + message.symbol + ".";
    }
    checkedUpdate(connector, "Crear mensaje " + message.n);

    var p1 = positions[pair[0]];
    var p2 = positions[pair[1]];
    var offsetX = Math.round((row.x - (p1.x + p2.x) / 2) * CU11_SCALE);
    var offsetY = -Math.round((row.y - (p1.y + p2.y) / 2) * CU11_SCALE);
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
            place(diagram, elements[key], view.nodes[key], CU11_MODEL.nodes[key].kind);
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
    var root = selected.Packages.AddNew("CU11 - Robustez numerada - " + stamp, "");
    checkedUpdate(root, "Crear paquete principal");
    var byNumber = {};
    for (var i = 0; i < CU11_MODEL.messages.length; i++) {
        byNumber[CU11_MODEL.messages[i].n] = CU11_MODEL.messages[i];
    }
    var firstDiagram = 0;
    for (var vi = 0; vi < CU11_MODEL.views.length; vi++) {
        var generated = generateView(root, CU11_MODEL.views[vi], byNumber);
        if (!firstDiagram) { firstDiagram = generated; }
    }
    root.Packages.Refresh();
    selected.Packages.Refresh();
    Repository.RefreshModelView(selected.PackageID);
    Repository.OpenDiagram(firstDiagram);
    Repository.WriteOutput("Script", "CU11 finalizado: " + CU11_MODEL.messages.length + " mensajes en " + CU11_MODEL.views.length + " vista(s).", 0);
}

main();
