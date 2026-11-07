/* FashionStore CU13. Ejecutar como JScript dentro de Enterprise Architect.
 * Genera un paquete nuevo con las vistas del modelo sin modificar diagramas existentes.
 * Las llamadas nativas y sus referencias proceden del modelo compartido con draw.io.
 * El enlace Association se crea antes de sus mensajes Collaboration, como en el
 * JScript de referencia. PDATA4 conserva el número explícito y SeqNo su orden.
 * Los campos internos de EA se escriben solo para conectores recién creados.
 */

var CU13_MODEL = {
  "nodes": {
    "actor": {
      "kind": "actor",
      "name": "Cajero / Personal autorizado"
    },
    "b_pre": {
      "kind": "boundary",
      "name": "Frontend : Terminal de venta POS"
    },
    "control": {
      "kind": "control",
      "name": "Backend : Venta presencial",
      "note": "Control de análisis que agrupa los módulos indicados en las referencias del caso de uso."
    },
    "inventario": {
      "kind": "entity",
      "name": "Inventario",
      "table": "inventario"
    },
    "venta": {
      "kind": "entity",
      "name": "Venta",
      "table": "venta"
    },
    "detalle": {
      "kind": "entity",
      "name": "Detalle de venta",
      "table": "detalle_venta"
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
      "text": "Buscar productos para el ticket",
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
      "text": "listar_productos_pos_endpoint(sucursal, búsqueda)",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/routers/pos.py",
      "symbol": "listar_productos_pos_endpoint",
      "line": 39
    },
    {
      "n": 3,
      "action": 1,
      "a": "control",
      "b": "inventario",
      "text": "listar_productos_pos(sucursal, búsqueda)",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/services/pos_service.py",
      "symbol": "listar_productos_pos",
      "line": 26
    },
    {
      "n": 4,
      "action": 1,
      "a": "inventario",
      "b": "control",
      "text": "productos y stock",
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
      "text": "productos disponibles",
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
      "text": "Mostrar productos",
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
      "text": "Confirmar venta y efectivo recibido",
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
      "text": "procesar_venta_pos_endpoint(ticket y cobro)",
      "kind": "invoke",
      "color": "#215D9C",
      "source": "Parcial2_backend/app/routers/pos.py",
      "symbol": "procesar_venta_pos_endpoint",
      "line": 83
    },
    {
      "n": 9,
      "action": 2,
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
      "n": 10,
      "action": 2,
      "a": "inventario",
      "b": "control",
      "text": "stock y precios verificados",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 11,
      "action": 2,
      "a": "control",
      "b": "venta",
      "text": "procesar_venta_pos(datos)",
      "kind": "write",
      "color": "#AC3636",
      "source": "Parcial2_backend/app/services/pos_service.py",
      "symbol": "procesar_venta_pos",
      "line": 188
    },
    {
      "n": 12,
      "action": 2,
      "a": "venta",
      "b": "control",
      "text": "id_venta",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 13,
      "action": 2,
      "a": "control",
      "b": "detalle",
      "text": "Guardar detalle [por ítem]",
      "kind": "write",
      "color": "#AC3636",
      "source": "Parcial2_backend/app/services/pos_service.py",
      "symbol": "procesar_venta_pos",
      "line": 188
    },
    {
      "n": 14,
      "action": 2,
      "a": "control",
      "b": "movimiento",
      "text": "Registrar Salida [por ítem]",
      "kind": "write",
      "color": "#AC3636",
      "source": "Parcial2_backend/app/services/pos_service.py",
      "symbol": "procesar_venta_pos",
      "line": 188
    },
    {
      "n": 15,
      "action": 2,
      "a": "control",
      "b": "bitacora",
      "text": "registrar_bitacora(venta POS)",
      "kind": "write",
      "color": "#AC3636",
      "source": "Parcial2_backend/app/services/bitacora_service.py",
      "symbol": "registrar_bitacora",
      "line": 65
    },
    {
      "n": 16,
      "action": 2,
      "a": "control",
      "b": "b_pre",
      "text": "venta, total y vuelto",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 17,
      "action": 2,
      "a": "b_pre",
      "b": "actor",
      "text": "Mostrar venta y opción de comprobante",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 18,
      "action": 3,
      "a": "actor",
      "b": "b_pre",
      "text": "Consultar venta registrada",
      "kind": "ui",
      "color": "#28343E",
      "source": null,
      "symbol": null
    },
    {
      "n": 19,
      "action": 3,
      "a": "b_pre",
      "b": "control",
      "text": "obtener_venta(id_venta)",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/routers/ventas.py",
      "symbol": "obtener_venta",
      "line": 170
    },
    {
      "n": 20,
      "action": 3,
      "a": "control",
      "b": "venta",
      "text": "obtener_venta_por_id(id_venta)",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/services/venta_service.py",
      "symbol": "obtener_venta_por_id",
      "line": 145
    },
    {
      "n": 21,
      "action": 3,
      "a": "venta",
      "b": "control",
      "text": "venta con detalles",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 22,
      "action": 3,
      "a": "control",
      "b": "b_pre",
      "text": "venta registrada",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    }
  ],
  "views": [
    {
      "name": "CU13 - Robustez simplificada",
      "title": "CU13 - Registrar venta presencial - Diagrama de robustez",
      "width": 4600,
      "height": 2197,
      "nodes": {
        "actor": {
          "x": 180,
          "y": 1098.5
        },
        "b_pre": {
          "x": 1100,
          "y": 1098.5
        },
        "control": {
          "x": 2400,
          "y": 1098.5
        },
        "inventario": {
          "x": 4300,
          "y": 333
        },
        "venta": {
          "x": 4300,
          "y": 749
        },
        "detalle": {
          "x": 4300,
          "y": 1121
        },
        "movimiento": {
          "x": 4300,
          "y": 1476
        },
        "bitacora": {
          "x": 4300,
          "y": 1831
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
              1098.5
            ],
            [
              1035,
              1098.5
            ]
          ],
          "rows": [
            {
              "n": 1,
              "x": 650,
              "y": 950.5,
              "width": 600,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 7,
              "x": 650,
              "y": 994.5,
              "width": 600,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 18,
              "x": 650,
              "y": 1038.5,
              "width": 600,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 6,
              "x": 650,
              "y": 1158.5,
              "width": 600,
              "height": 44,
              "forward": false,
              "rightward": false
            },
            {
              "n": 17,
              "x": 650,
              "y": 1202.5,
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
              1098.5
            ],
            [
              2335,
              1098.5
            ]
          ],
          "rows": [
            {
              "n": 2,
              "x": 1650,
              "y": 902.5,
              "width": 550,
              "height": 76,
              "forward": true,
              "rightward": true
            },
            {
              "n": 8,
              "x": 1650,
              "y": 978.5,
              "width": 550,
              "height": 76,
              "forward": true,
              "rightward": true
            },
            {
              "n": 19,
              "x": 1650,
              "y": 1038.5,
              "width": 550,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 5,
              "x": 1650,
              "y": 1158.5,
              "width": 550,
              "height": 44,
              "forward": false,
              "rightward": false
            },
            {
              "n": 16,
              "x": 1650,
              "y": 1202.5,
              "width": 550,
              "height": 44,
              "forward": false,
              "rightward": false
            },
            {
              "n": 22,
              "x": 1650,
              "y": 1246.5,
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
              1098.5
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
              "n": 9,
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
              "n": 10,
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
            "venta"
          ],
          "points": [
            [
              2465,
              1098.5
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
              "n": 11,
              "x": 3300,
              "y": 645,
              "width": 1050,
              "height": 44,
              "forward": true,
              "rightward": true
            },
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
              "n": 12,
              "x": 3300,
              "y": 809,
              "width": 1050,
              "height": 44,
              "forward": false,
              "rightward": false
            },
            {
              "n": 21,
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
            "control",
            "detalle"
          ],
          "points": [
            [
              2465,
              1098.5
            ],
            [
              2720,
              1121
            ],
            [
              4235,
              1121
            ]
          ],
          "rows": [
            {
              "n": 13,
              "x": 3300,
              "y": 1061,
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
              1098.5
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
              "n": 14,
              "x": 3300,
              "y": 1416,
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
              1098.5
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
              "n": 15,
              "x": 3300,
              "y": 1771,
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
var CU13_SCALE = 0.6;

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
    var definition = CU13_MODEL.nodes[key];
    var element = pkg.Elements.AddNew(definition.name, definition.kind == "actor" ? "Actor" : "Object");
    if (definition.kind != "actor") { element.Stereotype = definition.kind; }
    element.Notes = "FashionStore CU13. Identificador lógico: " + key + ".";
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
    var left = Math.round((point.x - radiusX) * CU13_SCALE);
    var right = Math.round((point.x + radiusX) * CU13_SCALE);
    var top = -Math.round((point.y - radiusY) * CU13_SCALE);
    var bottom = -Math.round((point.y + radiusY) * CU13_SCALE);
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
    connector.Notes = "CU13 mensaje " + message.n + ". Origen: " + message.a + ". Destino: " + message.b + ".";
    if (message.source) {
        connector.Notes += " Fuente: " + message.source + ":" + message.line + ", " + message.symbol + ".";
    }
    checkedUpdate(connector, "Crear mensaje " + message.n);

    var p1 = positions[pair[0]];
    var p2 = positions[pair[1]];
    var offsetX = Math.round((row.x - (p1.x + p2.x) / 2) * CU13_SCALE);
    var offsetY = -Math.round((row.y - (p1.y + p2.y) / 2) * CU13_SCALE);
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
            place(diagram, elements[key], view.nodes[key], CU13_MODEL.nodes[key].kind);
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
    var root = selected.Packages.AddNew("CU13 - Robustez numerada - " + stamp, "");
    checkedUpdate(root, "Crear paquete principal");
    var byNumber = {};
    for (var i = 0; i < CU13_MODEL.messages.length; i++) {
        byNumber[CU13_MODEL.messages[i].n] = CU13_MODEL.messages[i];
    }
    var firstDiagram = 0;
    for (var vi = 0; vi < CU13_MODEL.views.length; vi++) {
        var generated = generateView(root, CU13_MODEL.views[vi], byNumber);
        if (!firstDiagram) { firstDiagram = generated; }
    }
    root.Packages.Refresh();
    selected.Packages.Refresh();
    Repository.RefreshModelView(selected.PackageID);
    Repository.OpenDiagram(firstDiagram);
    Repository.WriteOutput("Script", "CU13 finalizado: " + CU13_MODEL.messages.length + " mensajes en " + CU13_MODEL.views.length + " vista(s).", 0);
}

main();
