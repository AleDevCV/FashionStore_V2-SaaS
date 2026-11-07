/* FashionStore CU10. Ejecutar como JScript dentro de Enterprise Architect.
 * Genera un paquete nuevo con las vistas del modelo sin modificar diagramas existentes.
 * Las llamadas nativas y sus referencias proceden del modelo compartido con draw.io.
 * El enlace Association se crea antes de sus mensajes Collaboration, como en el
 * JScript de referencia. PDATA4 conserva el número explícito y SeqNo su orden.
 * Los campos internos de EA se escriben solo para conectores recién creados.
 */

var CU10_MODEL = {
  "nodes": {
    "actor": {
      "kind": "actor",
      "name": "Personal autorizado"
    },
    "b_pre": {
      "kind": "boundary",
      "name": "Frontend : Movimientos de inventario"
    },
    "control": {
      "kind": "control",
      "name": "Backend : Gestión de movimientos",
      "note": "Control de análisis que agrupa los módulos indicados en las referencias del caso de uso."
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
      "a": "actor",
      "b": "b_pre",
      "text": "Consultar stock de la variante",
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
      "text": "consultar_stock(sucursal, variante)",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/routers/movimientos.py",
      "symbol": "consultar_stock",
      "line": 43
    },
    {
      "n": 3,
      "action": 1,
      "a": "control",
      "b": "inventario",
      "text": "obtener_stock_actual(sucursal, variante)",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/services/movimiento_service.py",
      "symbol": "obtener_stock_actual",
      "line": 27
    },
    {
      "n": 4,
      "action": 1,
      "a": "inventario",
      "b": "control",
      "text": "stock físico",
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
      "text": "stock actual",
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
      "text": "Mostrar stock",
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
      "text": "Registrar movimiento y motivo",
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
      "text": "registrar_movimiento(datos)",
      "kind": "invoke",
      "color": "#215D9C",
      "source": "Parcial2_backend/app/routers/movimientos.py",
      "symbol": "registrar_movimiento",
      "line": 85
    },
    {
      "n": 9,
      "action": 2,
      "a": "control",
      "b": "movimiento",
      "text": "registrar_movimiento(datos)",
      "kind": "write",
      "color": "#AC3636",
      "source": "Parcial2_backend/app/services/movimiento_service.py",
      "symbol": "registrar_movimiento",
      "line": 102
    },
    {
      "n": 10,
      "action": 2,
      "a": "movimiento",
      "b": "control",
      "text": "movimiento y stock resultante",
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
      "text": "registrar_bitacora(movimiento)",
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
      "text": "movimiento confirmado",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 13,
      "action": 2,
      "a": "b_pre",
      "b": "actor",
      "text": "Mostrar movimiento registrado",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 14,
      "action": 3,
      "a": "actor",
      "b": "b_pre",
      "text": "Consultar historial de movimientos",
      "kind": "ui",
      "color": "#28343E",
      "source": null,
      "symbol": null
    },
    {
      "n": 15,
      "action": 3,
      "a": "b_pre",
      "b": "control",
      "text": "listar_movimientos(filtros)",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/routers/movimientos.py",
      "symbol": "listar_movimientos",
      "line": 130
    },
    {
      "n": 16,
      "action": 3,
      "a": "control",
      "b": "movimiento",
      "text": "listar_movimientos(filtros)",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/services/movimiento_service.py",
      "symbol": "listar_movimientos",
      "line": 201
    },
    {
      "n": 17,
      "action": 3,
      "a": "movimiento",
      "b": "control",
      "text": "movimientos autorizados",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 18,
      "action": 3,
      "a": "control",
      "b": "b_pre",
      "text": "historial",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 19,
      "action": 3,
      "a": "b_pre",
      "b": "actor",
      "text": "Mostrar historial",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    }
  ],
  "views": [
    {
      "name": "CU10 - Robustez simplificada",
      "title": "CU10 - Registrar movimientos de inventario - Diagrama de robustez",
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
        "inventario": {
          "x": 4300,
          "y": 289
        },
        "movimiento": {
          "x": 4300,
          "y": 688
        },
        "bitacora": {
          "x": 4300,
          "y": 1060
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
              "y": 902,
              "width": 600,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 7,
              "x": 650,
              "y": 946,
              "width": 600,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 14,
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
              "n": 13,
              "x": 650,
              "y": 1154,
              "width": 600,
              "height": 44,
              "forward": false,
              "rightward": false
            },
            {
              "n": 19,
              "x": 650,
              "y": 1198,
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
              "y": 902,
              "width": 550,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 8,
              "x": 1650,
              "y": 946,
              "width": 550,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 15,
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
              "n": 12,
              "x": 1650,
              "y": 1154,
              "width": 550,
              "height": 44,
              "forward": false,
              "rightward": false
            },
            {
              "n": 18,
              "x": 1650,
              "y": 1198,
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
              1050
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
            "movimiento"
          ],
          "points": [
            [
              2465,
              1050
            ],
            [
              2720,
              688
            ],
            [
              4235,
              688
            ]
          ],
          "rows": [
            {
              "n": 9,
              "x": 3300,
              "y": 584,
              "width": 1050,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 16,
              "x": 3300,
              "y": 628,
              "width": 1050,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 10,
              "x": 3300,
              "y": 748,
              "width": 1050,
              "height": 44,
              "forward": false,
              "rightward": false
            },
            {
              "n": 17,
              "x": 3300,
              "y": 792,
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
              1050
            ],
            [
              2720,
              1060
            ],
            [
              4235,
              1060
            ]
          ],
          "rows": [
            {
              "n": 11,
              "x": 3300,
              "y": 1000,
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
var CU10_SCALE = 0.6;

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
    var definition = CU10_MODEL.nodes[key];
    var element = pkg.Elements.AddNew(definition.name, definition.kind == "actor" ? "Actor" : "Object");
    if (definition.kind != "actor") { element.Stereotype = definition.kind; }
    element.Notes = "FashionStore CU10. Identificador lógico: " + key + ".";
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
    var left = Math.round((point.x - radiusX) * CU10_SCALE);
    var right = Math.round((point.x + radiusX) * CU10_SCALE);
    var top = -Math.round((point.y - radiusY) * CU10_SCALE);
    var bottom = -Math.round((point.y + radiusY) * CU10_SCALE);
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
    connector.Notes = "CU10 mensaje " + message.n + ". Origen: " + message.a + ". Destino: " + message.b + ".";
    if (message.source) {
        connector.Notes += " Fuente: " + message.source + ":" + message.line + ", " + message.symbol + ".";
    }
    checkedUpdate(connector, "Crear mensaje " + message.n);

    var p1 = positions[pair[0]];
    var p2 = positions[pair[1]];
    var offsetX = Math.round((row.x - (p1.x + p2.x) / 2) * CU10_SCALE);
    var offsetY = -Math.round((row.y - (p1.y + p2.y) / 2) * CU10_SCALE);
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
            place(diagram, elements[key], view.nodes[key], CU10_MODEL.nodes[key].kind);
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
    var root = selected.Packages.AddNew("CU10 - Robustez numerada - " + stamp, "");
    checkedUpdate(root, "Crear paquete principal");
    var byNumber = {};
    for (var i = 0; i < CU10_MODEL.messages.length; i++) {
        byNumber[CU10_MODEL.messages[i].n] = CU10_MODEL.messages[i];
    }
    var firstDiagram = 0;
    for (var vi = 0; vi < CU10_MODEL.views.length; vi++) {
        var generated = generateView(root, CU10_MODEL.views[vi], byNumber);
        if (!firstDiagram) { firstDiagram = generated; }
    }
    root.Packages.Refresh();
    selected.Packages.Refresh();
    Repository.RefreshModelView(selected.PackageID);
    Repository.OpenDiagram(firstDiagram);
    Repository.WriteOutput("Script", "CU10 finalizado: " + CU10_MODEL.messages.length + " mensajes en " + CU10_MODEL.views.length + " vista(s).", 0);
}

main();
