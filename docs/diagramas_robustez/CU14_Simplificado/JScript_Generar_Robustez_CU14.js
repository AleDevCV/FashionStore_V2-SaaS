/* FashionStore CU14. Ejecutar como JScript dentro de Enterprise Architect.
 * Genera un paquete nuevo con las vistas del modelo sin modificar diagramas existentes.
 * Las llamadas nativas y sus referencias proceden del modelo compartido con draw.io.
 * El enlace Association se crea antes de sus mensajes Collaboration, como en el
 * JScript de referencia. PDATA4 conserva el número explícito y SeqNo su orden.
 * Los campos internos de EA se escriben solo para conectores recién creados.
 */

var CU14_MODEL = {
  "nodes": {
    "actor": {
      "kind": "actor",
      "name": "Cliente / Personal autorizado"
    },
    "b_pre": {
      "kind": "boundary",
      "name": "Frontend : Comprobantes de compra"
    },
    "control": {
      "kind": "control",
      "name": "Backend : Gestión de comprobantes",
      "note": "Control de análisis que agrupa los módulos indicados en las referencias del caso de uso."
    },
    "venta": {
      "kind": "entity",
      "name": "Venta y detalles",
      "table": "venta / detalle_venta"
    },
    "comprobante": {
      "kind": "entity",
      "name": "Comprobante",
      "table": "comprobante"
    },
    "pdf": {
      "kind": "entity",
      "name": "Archivo PDF",
      "table": "filesystem por tenant",
      "prefix": "Persistencia :"
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
      "text": "Consultar comprobante de una venta",
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
      "text": "comprobante_por_venta(id_venta)",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/routers/comprobantes.py",
      "symbol": "comprobante_por_venta",
      "line": 59
    },
    {
      "n": 3,
      "action": 1,
      "a": "control",
      "b": "comprobante",
      "text": "obtener_comprobante_por_venta(id_venta)",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/services/comprobante_service.py",
      "symbol": "obtener_comprobante_por_venta",
      "line": 411
    },
    {
      "n": 4,
      "action": 1,
      "a": "comprobante",
      "b": "control",
      "text": "comprobante existente",
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
      "text": "datos del comprobante",
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
      "text": "Mostrar comprobante",
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
      "text": "Generar comprobante [si no existe]",
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
      "text": "generar_comprobante(venta y datos)",
      "kind": "invoke",
      "color": "#215D9C",
      "source": "Parcial2_backend/app/routers/comprobantes.py",
      "symbol": "generar_comprobante",
      "line": 32
    },
    {
      "n": 9,
      "action": 2,
      "a": "control",
      "b": "venta",
      "text": "generar_comprobante(id_venta)",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/services/comprobante_service.py",
      "symbol": "generar_comprobante",
      "line": 227
    },
    {
      "n": 10,
      "action": 2,
      "a": "venta",
      "b": "control",
      "text": "venta autorizada y detalles",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 11,
      "action": 2,
      "a": "control",
      "b": "pdf",
      "text": "Construir y guardar PDF",
      "kind": "write",
      "color": "#AC3636",
      "source": "Parcial2_backend/app/services/comprobante_service.py",
      "symbol": "generar_comprobante",
      "line": 227
    },
    {
      "n": 12,
      "action": 2,
      "a": "control",
      "b": "comprobante",
      "text": "Registrar comprobante único y URL",
      "kind": "write",
      "color": "#AC3636",
      "source": "Parcial2_backend/app/services/comprobante_service.py",
      "symbol": "generar_comprobante",
      "line": 227
    },
    {
      "n": 13,
      "action": 2,
      "a": "comprobante",
      "b": "control",
      "text": "comprobante registrado",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 14,
      "action": 2,
      "a": "control",
      "b": "bitacora",
      "text": "registrar_bitacora(comprobante)",
      "kind": "write",
      "color": "#AC3636",
      "source": "Parcial2_backend/app/services/bitacora_service.py",
      "symbol": "registrar_bitacora",
      "line": 65
    },
    {
      "n": 15,
      "action": 2,
      "a": "control",
      "b": "b_pre",
      "text": "comprobante generado",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 16,
      "action": 3,
      "a": "actor",
      "b": "b_pre",
      "text": "Descargar PDF autorizado",
      "kind": "ui",
      "color": "#28343E",
      "source": null,
      "symbol": null
    },
    {
      "n": 17,
      "action": 3,
      "a": "b_pre",
      "b": "control",
      "text": "descargar_pdf_autorizado(número)",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/routers/comprobantes.py",
      "symbol": "descargar_pdf_autorizado",
      "line": 105
    },
    {
      "n": 18,
      "action": 3,
      "a": "control",
      "b": "comprobante",
      "text": "descargar_pdf_autorizado(número)",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/routers/comprobantes.py",
      "symbol": "descargar_pdf_autorizado",
      "line": 105
    },
    {
      "n": 19,
      "action": 3,
      "a": "comprobante",
      "b": "control",
      "text": "comprobante autorizado",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 20,
      "action": 3,
      "a": "control",
      "b": "pdf",
      "text": "Leer PDF del tenant",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/routers/comprobantes.py",
      "symbol": "descargar_pdf_autorizado",
      "line": 105
    },
    {
      "n": 21,
      "action": 3,
      "a": "pdf",
      "b": "control",
      "text": "archivo PDF",
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
      "text": "descarga PDF",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 23,
      "action": 3,
      "a": "b_pre",
      "b": "actor",
      "text": "Abrir o guardar comprobante",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    }
  ],
  "views": [
    {
      "name": "CU14 - Robustez simplificada",
      "title": "CU14 - Obtener comprobantes de compra - Diagrama de robustez",
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
        "venta": {
          "x": 4300,
          "y": 289
        },
        "comprobante": {
          "x": 4300,
          "y": 732
        },
        "pdf": {
          "x": 4300,
          "y": 1192
        },
        "bitacora": {
          "x": 4300,
          "y": 1520
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
              "n": 16,
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
              "n": 23,
              "x": 650,
              "y": 1154,
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
              "n": 17,
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
              "n": 15,
              "x": 1650,
              "y": 1154,
              "width": 550,
              "height": 44,
              "forward": false,
              "rightward": false
            },
            {
              "n": 22,
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
            "comprobante"
          ],
          "points": [
            [
              2465,
              1050
            ],
            [
              2720,
              732
            ],
            [
              4235,
              732
            ]
          ],
          "rows": [
            {
              "n": 3,
              "x": 3300,
              "y": 584,
              "width": 1050,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 12,
              "x": 3300,
              "y": 628,
              "width": 1050,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 18,
              "x": 3300,
              "y": 672,
              "width": 1050,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 4,
              "x": 3300,
              "y": 792,
              "width": 1050,
              "height": 44,
              "forward": false,
              "rightward": false
            },
            {
              "n": 13,
              "x": 3300,
              "y": 836,
              "width": 1050,
              "height": 44,
              "forward": false,
              "rightward": false
            },
            {
              "n": 19,
              "x": 3300,
              "y": 880,
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
              "n": 9,
              "x": 3300,
              "y": 229,
              "width": 1050,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 10,
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
            "pdf"
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
              "n": 11,
              "x": 3300,
              "y": 1088,
              "width": 1050,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 20,
              "x": 3300,
              "y": 1132,
              "width": 1050,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 21,
              "x": 3300,
              "y": 1252,
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
              1520
            ],
            [
              4235,
              1520
            ]
          ],
          "rows": [
            {
              "n": 14,
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
var CU14_SCALE = 0.6;

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
    var definition = CU14_MODEL.nodes[key];
    var element = pkg.Elements.AddNew(definition.name, definition.kind == "actor" ? "Actor" : "Object");
    if (definition.kind != "actor") { element.Stereotype = definition.kind; }
    element.Notes = "FashionStore CU14. Identificador lógico: " + key + ".";
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
    var left = Math.round((point.x - radiusX) * CU14_SCALE);
    var right = Math.round((point.x + radiusX) * CU14_SCALE);
    var top = -Math.round((point.y - radiusY) * CU14_SCALE);
    var bottom = -Math.round((point.y + radiusY) * CU14_SCALE);
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
    connector.Notes = "CU14 mensaje " + message.n + ". Origen: " + message.a + ". Destino: " + message.b + ".";
    if (message.source) {
        connector.Notes += " Fuente: " + message.source + ":" + message.line + ", " + message.symbol + ".";
    }
    checkedUpdate(connector, "Crear mensaje " + message.n);

    var p1 = positions[pair[0]];
    var p2 = positions[pair[1]];
    var offsetX = Math.round((row.x - (p1.x + p2.x) / 2) * CU14_SCALE);
    var offsetY = -Math.round((row.y - (p1.y + p2.y) / 2) * CU14_SCALE);
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
            place(diagram, elements[key], view.nodes[key], CU14_MODEL.nodes[key].kind);
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
    var root = selected.Packages.AddNew("CU14 - Robustez numerada - " + stamp, "");
    checkedUpdate(root, "Crear paquete principal");
    var byNumber = {};
    for (var i = 0; i < CU14_MODEL.messages.length; i++) {
        byNumber[CU14_MODEL.messages[i].n] = CU14_MODEL.messages[i];
    }
    var firstDiagram = 0;
    for (var vi = 0; vi < CU14_MODEL.views.length; vi++) {
        var generated = generateView(root, CU14_MODEL.views[vi], byNumber);
        if (!firstDiagram) { firstDiagram = generated; }
    }
    root.Packages.Refresh();
    selected.Packages.Refresh();
    Repository.RefreshModelView(selected.PackageID);
    Repository.OpenDiagram(firstDiagram);
    Repository.WriteOutput("Script", "CU14 finalizado: " + CU14_MODEL.messages.length + " mensajes en " + CU14_MODEL.views.length + " vista(s).", 0);
}

main();
