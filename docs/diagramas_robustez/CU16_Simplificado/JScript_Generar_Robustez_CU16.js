/* FashionStore CU16. Ejecutar como JScript dentro de Enterprise Architect.
 * Genera un paquete nuevo con las vistas del modelo sin modificar diagramas existentes.
 * Las llamadas nativas y sus referencias proceden del modelo compartido con draw.io.
 * El enlace Association se crea antes de sus mensajes Collaboration, como en el
 * JScript de referencia. PDATA4 conserva el número explícito y SeqNo su orden.
 * Los campos internos de EA se escriben solo para conectores recién creados.
 */

var CU16_MODEL = {
  "nodes": {
    "actor": {
      "kind": "actor",
      "name": "Usuario autorizado"
    },
    "b_pre": {
      "kind": "boundary",
      "name": "Frontend : Operación offline web / móvil"
    },
    "control": {
      "kind": "control",
      "name": "Dispositivo : Gestión offline",
      "note": "Servicio local OfflineService en Angular y OfflineController/LocalDatabase en Flutter. No necesita servidor para registrar pendientes."
    },
    "backend": {
      "kind": "control",
      "name": "Backend : Catálogo offline",
      "note": "Router offline.snapshot: se utiliza solo al descargar con conexión."
    },
    "central": {
      "kind": "entity",
      "name": "Catálogo autorizado",
      "table": "agregado PostgreSQL"
    },
    "snapshot": {
      "kind": "entity",
      "name": "Catálogo local y permiso",
      "table": "IndexedDB / SQLite"
    },
    "operacion": {
      "kind": "entity",
      "name": "Operación local",
      "table": "operations / operation"
    },
    "detalle": {
      "kind": "entity",
      "name": "Detalle de operación",
      "table": "details / detail"
    }
  },
  "messages": [
    {
      "n": 1,
      "action": 1,
      "a": "actor",
      "b": "b_pre",
      "text": "Preparar dispositivo con conexión",
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
      "text": "download(sucursal)",
      "kind": "invoke",
      "color": "#215D9C",
      "source": "Parcial2_frontend-web/src/app/core/services/offline.service.ts",
      "symbol": "download",
      "line": 39
    },
    {
      "n": 3,
      "action": 1,
      "a": "control",
      "b": "backend",
      "text": "snapshot(sucursal)",
      "kind": "invoke",
      "color": "#215D9C",
      "source": "Parcial2_backend/app/routers/offline.py",
      "symbol": "snapshot",
      "line": 15
    },
    {
      "n": 4,
      "action": 1,
      "a": "backend",
      "b": "central",
      "text": "snapshot(sucursal)",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/routers/offline.py",
      "symbol": "snapshot",
      "line": 15
    },
    {
      "n": 5,
      "action": 1,
      "a": "central",
      "b": "backend",
      "text": "catálogo y autorización",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 6,
      "action": 1,
      "a": "backend",
      "b": "control",
      "text": "snapshot autorizado",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 7,
      "action": 1,
      "a": "control",
      "b": "snapshot",
      "text": "saveSnapshot(datos)",
      "kind": "write",
      "color": "#AC3636",
      "source": "Parcial2_mobile/lib/features/offline/local_database.dart",
      "symbol": "saveSnapshot",
      "line": 72
    },
    {
      "n": 8,
      "action": 1,
      "a": "control",
      "b": "b_pre",
      "text": "catálogo guardado",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 9,
      "action": 1,
      "a": "b_pre",
      "b": "actor",
      "text": "Dispositivo preparado",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 10,
      "action": 2,
      "a": "actor",
      "b": "b_pre",
      "text": "Consultar catálogo sin conexión",
      "kind": "ui",
      "color": "#28343E",
      "source": null,
      "symbol": null
    },
    {
      "n": 11,
      "action": 2,
      "a": "b_pre",
      "b": "control",
      "text": "refresh()",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_frontend-web/src/app/core/services/offline.service.ts",
      "symbol": "refresh",
      "line": 24
    },
    {
      "n": 12,
      "action": 2,
      "a": "control",
      "b": "snapshot",
      "text": "catalog(sucursal)",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_mobile/lib/features/offline/local_database.dart",
      "symbol": "catalog",
      "line": 68
    },
    {
      "n": 13,
      "action": 2,
      "a": "snapshot",
      "b": "control",
      "text": "catálogo y disponible local",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 14,
      "action": 2,
      "a": "control",
      "b": "b_pre",
      "text": "catálogo local",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 15,
      "action": 2,
      "a": "b_pre",
      "b": "actor",
      "text": "Mostrar copia descargada",
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
      "text": "Registrar reserva offline",
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
      "text": "capture(reserva, ítems)",
      "kind": "invoke",
      "color": "#215D9C",
      "source": "Parcial2_frontend-web/src/app/core/services/offline.service.ts",
      "symbol": "capture",
      "line": 56
    },
    {
      "n": 18,
      "action": 3,
      "a": "control",
      "b": "operacion",
      "text": "Guardar UUID y estado PENDIENTE",
      "kind": "write",
      "color": "#AC3636",
      "source": "Parcial2_mobile/lib/features/offline/local_database.dart",
      "symbol": "capture",
      "line": 99
    },
    {
      "n": 19,
      "action": 3,
      "a": "control",
      "b": "detalle",
      "text": "Guardar detalles [misma transacción]",
      "kind": "write",
      "color": "#AC3636",
      "source": "Parcial2_mobile/lib/features/offline/local_database.dart",
      "symbol": "capture",
      "line": 99
    },
    {
      "n": 20,
      "action": 3,
      "a": "control",
      "b": "b_pre",
      "text": "reserva provisional",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 21,
      "action": 3,
      "a": "b_pre",
      "b": "actor",
      "text": "Mostrar operación pendiente",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 22,
      "action": 4,
      "a": "actor",
      "b": "b_pre",
      "text": "Registrar venta de contado offline",
      "kind": "ui",
      "color": "#28343E",
      "source": null,
      "symbol": null
    },
    {
      "n": 23,
      "action": 4,
      "a": "b_pre",
      "b": "control",
      "text": "capture(venta, ítems)",
      "kind": "invoke",
      "color": "#215D9C",
      "source": "Parcial2_frontend-web/src/app/core/services/offline.service.ts",
      "symbol": "capture",
      "line": 56
    },
    {
      "n": 24,
      "action": 4,
      "a": "control",
      "b": "operacion",
      "text": "Guardar UUID y estado PENDIENTE",
      "kind": "write",
      "color": "#AC3636",
      "source": "Parcial2_mobile/lib/features/offline/local_database.dart",
      "symbol": "capture",
      "line": 99
    },
    {
      "n": 25,
      "action": 4,
      "a": "control",
      "b": "detalle",
      "text": "Guardar detalles [misma transacción]",
      "kind": "write",
      "color": "#AC3636",
      "source": "Parcial2_mobile/lib/features/offline/local_database.dart",
      "symbol": "capture",
      "line": 99
    },
    {
      "n": 26,
      "action": 4,
      "a": "control",
      "b": "b_pre",
      "text": "venta provisional",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 27,
      "action": 4,
      "a": "b_pre",
      "b": "actor",
      "text": "Mostrar operación pendiente",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 28,
      "action": 5,
      "a": "actor",
      "b": "b_pre",
      "text": "Reabrir y consultar pendientes",
      "kind": "ui",
      "color": "#28343E",
      "source": null,
      "symbol": null
    },
    {
      "n": 29,
      "action": 5,
      "a": "b_pre",
      "b": "control",
      "text": "open()",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_frontend-web/src/app/core/services/offline.service.ts",
      "symbol": "open",
      "line": 13
    },
    {
      "n": 30,
      "action": 5,
      "a": "control",
      "b": "operacion",
      "text": "operations()",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_mobile/lib/features/offline/local_database.dart",
      "symbol": "operations",
      "line": 66
    },
    {
      "n": 31,
      "action": 5,
      "a": "operacion",
      "b": "control",
      "text": "pendientes y estados guardados",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 32,
      "action": 5,
      "a": "control",
      "b": "detalle",
      "text": "details(UUID)",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_frontend-web/src/app/core/services/offline.service.ts",
      "symbol": "details",
      "line": 71
    },
    {
      "n": 33,
      "action": 5,
      "a": "detalle",
      "b": "control",
      "text": "detalles guardados",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 34,
      "action": 5,
      "a": "control",
      "b": "b_pre",
      "text": "operaciones recuperadas",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 35,
      "action": 5,
      "a": "b_pre",
      "b": "actor",
      "text": "Mostrar operaciones tras reinicio",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    }
  ],
  "views": [
    {
      "name": "CU16 - Robustez simplificada",
      "title": "CU16 - Registrar y consultar operaciones offline - Diagrama de robustez",
      "width": 4600,
      "height": 2400,
      "nodes": {
        "actor": {
          "x": 180,
          "y": 1200
        },
        "b_pre": {
          "x": 1100,
          "y": 1200
        },
        "control": {
          "x": 2400,
          "y": 1200
        },
        "snapshot": {
          "x": 4300,
          "y": 800
        },
        "operacion": {
          "x": 4300,
          "y": 1370
        },
        "detalle": {
          "x": 4300,
          "y": 1940
        },
        "backend": {
          "x": 3300,
          "y": 290
        },
        "central": {
          "x": 4300,
          "y": 290
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
              1200
            ],
            [
              1035,
              1200
            ]
          ],
          "rows": [
            {
              "n": 1,
              "x": 650,
              "y": 964,
              "width": 600,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 10,
              "x": 650,
              "y": 1008,
              "width": 600,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 16,
              "x": 650,
              "y": 1052,
              "width": 600,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 22,
              "x": 650,
              "y": 1096,
              "width": 600,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 28,
              "x": 650,
              "y": 1140,
              "width": 600,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 9,
              "x": 650,
              "y": 1260,
              "width": 600,
              "height": 44,
              "forward": false,
              "rightward": false
            },
            {
              "n": 15,
              "x": 650,
              "y": 1304,
              "width": 600,
              "height": 44,
              "forward": false,
              "rightward": false
            },
            {
              "n": 21,
              "x": 650,
              "y": 1348,
              "width": 600,
              "height": 44,
              "forward": false,
              "rightward": false
            },
            {
              "n": 27,
              "x": 650,
              "y": 1392,
              "width": 600,
              "height": 44,
              "forward": false,
              "rightward": false
            },
            {
              "n": 35,
              "x": 650,
              "y": 1436,
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
              1200
            ],
            [
              2335,
              1200
            ]
          ],
          "rows": [
            {
              "n": 2,
              "x": 1650,
              "y": 964,
              "width": 550,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 11,
              "x": 1650,
              "y": 1008,
              "width": 550,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 17,
              "x": 1650,
              "y": 1052,
              "width": 550,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 23,
              "x": 1650,
              "y": 1096,
              "width": 550,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 29,
              "x": 1650,
              "y": 1140,
              "width": 550,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 8,
              "x": 1650,
              "y": 1260,
              "width": 550,
              "height": 44,
              "forward": false,
              "rightward": false
            },
            {
              "n": 14,
              "x": 1650,
              "y": 1304,
              "width": 550,
              "height": 44,
              "forward": false,
              "rightward": false
            },
            {
              "n": 20,
              "x": 1650,
              "y": 1348,
              "width": 550,
              "height": 44,
              "forward": false,
              "rightward": false
            },
            {
              "n": 26,
              "x": 1650,
              "y": 1392,
              "width": 550,
              "height": 44,
              "forward": false,
              "rightward": false
            },
            {
              "n": 34,
              "x": 1650,
              "y": 1436,
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
            "backend"
          ],
          "points": [
            [
              2465,
              1200
            ],
            [
              2700,
              290
            ],
            [
              3235,
              290
            ]
          ],
          "rows": [
            {
              "n": 3,
              "x": 2800,
              "y": 230,
              "width": 500,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 6,
              "x": 2800,
              "y": 350,
              "width": 500,
              "height": 44,
              "forward": false,
              "rightward": false
            }
          ]
        },
        {
          "pair": [
            "backend",
            "central"
          ],
          "points": [
            [
              3365,
              290
            ],
            [
              4235,
              290
            ]
          ],
          "rows": [
            {
              "n": 4,
              "x": 3800,
              "y": 230,
              "width": 550,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 5,
              "x": 3800,
              "y": 350,
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
            "snapshot"
          ],
          "points": [
            [
              2465,
              1200
            ],
            [
              2720,
              800
            ],
            [
              4235,
              800
            ]
          ],
          "rows": [
            {
              "n": 7,
              "x": 3300,
              "y": 696,
              "width": 1050,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 12,
              "x": 3300,
              "y": 740,
              "width": 1050,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 13,
              "x": 3300,
              "y": 860,
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
            "operacion"
          ],
          "points": [
            [
              2465,
              1200
            ],
            [
              2720,
              1370
            ],
            [
              4235,
              1370
            ]
          ],
          "rows": [
            {
              "n": 18,
              "x": 3300,
              "y": 1222,
              "width": 1050,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 24,
              "x": 3300,
              "y": 1266,
              "width": 1050,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 30,
              "x": 3300,
              "y": 1310,
              "width": 1050,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 31,
              "x": 3300,
              "y": 1430,
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
              1200
            ],
            [
              2720,
              1940
            ],
            [
              4235,
              1940
            ]
          ],
          "rows": [
            {
              "n": 19,
              "x": 3300,
              "y": 1792,
              "width": 1050,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 25,
              "x": 3300,
              "y": 1836,
              "width": 1050,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 32,
              "x": 3300,
              "y": 1880,
              "width": 1050,
              "height": 44,
              "forward": true,
              "rightward": true
            },
            {
              "n": 33,
              "x": 3300,
              "y": 2000,
              "width": 1050,
              "height": 44,
              "forward": false,
              "rightward": false
            }
          ]
        }
      ]
    }
  ]
};
var CU16_SCALE = 0.6;

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
    var definition = CU16_MODEL.nodes[key];
    var element = pkg.Elements.AddNew(definition.name, definition.kind == "actor" ? "Actor" : "Object");
    if (definition.kind != "actor") { element.Stereotype = definition.kind; }
    element.Notes = "FashionStore CU16. Identificador lógico: " + key + ".";
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
    var left = Math.round((point.x - radiusX) * CU16_SCALE);
    var right = Math.round((point.x + radiusX) * CU16_SCALE);
    var top = -Math.round((point.y - radiusY) * CU16_SCALE);
    var bottom = -Math.round((point.y + radiusY) * CU16_SCALE);
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
    connector.Notes = "CU16 mensaje " + message.n + ". Origen: " + message.a + ". Destino: " + message.b + ".";
    if (message.source) {
        connector.Notes += " Fuente: " + message.source + ":" + message.line + ", " + message.symbol + ".";
    }
    checkedUpdate(connector, "Crear mensaje " + message.n);

    var p1 = positions[pair[0]];
    var p2 = positions[pair[1]];
    var offsetX = Math.round((row.x - (p1.x + p2.x) / 2) * CU16_SCALE);
    var offsetY = -Math.round((row.y - (p1.y + p2.y) / 2) * CU16_SCALE);
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
            place(diagram, elements[key], view.nodes[key], CU16_MODEL.nodes[key].kind);
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
    var root = selected.Packages.AddNew("CU16 - Robustez numerada - " + stamp, "");
    checkedUpdate(root, "Crear paquete principal");
    var byNumber = {};
    for (var i = 0; i < CU16_MODEL.messages.length; i++) {
        byNumber[CU16_MODEL.messages[i].n] = CU16_MODEL.messages[i];
    }
    var firstDiagram = 0;
    for (var vi = 0; vi < CU16_MODEL.views.length; vi++) {
        var generated = generateView(root, CU16_MODEL.views[vi], byNumber);
        if (!firstDiagram) { firstDiagram = generated; }
    }
    root.Packages.Refresh();
    selected.Packages.Refresh();
    Repository.RefreshModelView(selected.PackageID);
    Repository.OpenDiagram(firstDiagram);
    Repository.WriteOutput("Script", "CU16 finalizado: " + CU16_MODEL.messages.length + " mensajes en " + CU16_MODEL.views.length + " vista(s).", 0);
}

main();
