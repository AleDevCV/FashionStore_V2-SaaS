/* FashionStore CU06. Ejecutar como JScript dentro de Enterprise Architect.
 * Genera un paquete nuevo con las vistas del modelo sin modificar diagramas existentes.
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
    "b_pre": {
      "kind": "boundary",
      "name": "Frontend : Administración del catálogo",
      "sources": [
        "Parcial2_frontend-web/src/app/features/categorias/categorias.ts",
        "Parcial2_frontend-web/src/app/features/temporadas/temporadas.ts",
        "Parcial2_frontend-web/src/app/features/prendas/prendas.ts"
      ]
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
      "area": "catalogo",
      "a": "actor",
      "b": "b_pre",
      "text": "Consultar catálogo",
      "kind": "ui",
      "color": "#28343E",
      "source": null,
      "symbol": null
    },
    {
      "n": 2,
      "action": 1,
      "area": "catalogo",
      "a": "b_pre",
      "b": "control",
      "text": "listar_prendas(filtros)",
      "kind": "read",
      "color": "#28343E",
      "source": "Parcial2_backend/app/routers/prendas.py",
      "symbol": "listar_prendas",
      "line": 101
    },
    {
      "n": 3,
      "action": 1,
      "area": "catalogo",
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
      "n": 4,
      "action": 1,
      "area": "catalogo",
      "a": "prenda",
      "b": "control",
      "text": "prendas",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 5,
      "action": 1,
      "area": "catalogo",
      "a": "control",
      "b": "b_pre",
      "text": "catálogo",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 6,
      "action": 1,
      "area": "catalogo",
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
      "area": "catalogo",
      "a": "actor",
      "b": "b_pre",
      "text": "Registrar categoría",
      "kind": "ui",
      "color": "#28343E",
      "source": null,
      "symbol": null
    },
    {
      "n": 8,
      "action": 2,
      "area": "catalogo",
      "a": "b_pre",
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
      "area": "catalogo",
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
      "n": 10,
      "action": 2,
      "area": "catalogo",
      "a": "categoria",
      "b": "control",
      "text": "id_categoria",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 11,
      "action": 2,
      "area": "catalogo",
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
      "n": 12,
      "action": 2,
      "area": "catalogo",
      "a": "control",
      "b": "b_pre",
      "text": "categoría registrada",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 13,
      "action": 3,
      "area": "catalogo",
      "a": "actor",
      "b": "b_pre",
      "text": "Registrar temporada o colección",
      "kind": "ui",
      "color": "#28343E",
      "source": null,
      "symbol": null
    },
    {
      "n": 14,
      "action": 3,
      "area": "catalogo",
      "a": "b_pre",
      "b": "control",
      "text": "crear_temporada(datos)",
      "kind": "invoke",
      "color": "#215D9C",
      "source": "Parcial2_backend/app/routers/temporadas.py",
      "symbol": "crear_temporada",
      "line": 100
    },
    {
      "n": 15,
      "action": 3,
      "area": "catalogo",
      "a": "control",
      "b": "temporada",
      "text": "crear_temporada(datos)",
      "kind": "write",
      "color": "#AC3636",
      "source": "Parcial2_backend/app/services/temporada_service.py",
      "symbol": "crear_temporada",
      "line": 131
    },
    {
      "n": 16,
      "action": 3,
      "area": "catalogo",
      "a": "temporada",
      "b": "control",
      "text": "temporada creada",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 17,
      "action": 3,
      "area": "catalogo",
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
      "n": 18,
      "action": 3,
      "area": "catalogo",
      "a": "control",
      "b": "b_pre",
      "text": "temporada registrada",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 19,
      "action": 4,
      "area": "catalogo",
      "a": "actor",
      "b": "b_pre",
      "text": "Registrar prenda y variantes",
      "kind": "ui",
      "color": "#28343E",
      "source": null,
      "symbol": null
    },
    {
      "n": 20,
      "action": 4,
      "area": "catalogo",
      "a": "b_pre",
      "b": "control",
      "text": "crear_prenda(datos)",
      "kind": "invoke",
      "color": "#215D9C",
      "source": "Parcial2_backend/app/routers/prendas.py",
      "symbol": "crear_prenda",
      "line": 170
    },
    {
      "n": 21,
      "action": 4,
      "area": "catalogo",
      "a": "control",
      "b": "prenda",
      "text": "crear_prenda(datos)",
      "kind": "write",
      "color": "#AC3636",
      "source": "Parcial2_backend/app/services/prenda_service.py",
      "symbol": "crear_prenda",
      "line": 217
    },
    {
      "n": 22,
      "action": 4,
      "area": "catalogo",
      "a": "prenda",
      "b": "control",
      "text": "id_prenda",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 23,
      "action": 4,
      "area": "catalogo",
      "a": "control",
      "b": "variante",
      "text": "_crear_variante(datos) [por variante]",
      "kind": "write",
      "color": "#AC3636",
      "source": "Parcial2_backend/app/services/prenda_service.py",
      "symbol": "_crear_variante",
      "line": 288
    },
    {
      "n": 24,
      "action": 4,
      "area": "catalogo",
      "a": "variante",
      "b": "control",
      "text": "variante creada",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 25,
      "action": 4,
      "area": "catalogo",
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
      "n": 26,
      "action": 4,
      "area": "catalogo",
      "a": "control",
      "b": "b_pre",
      "text": "prenda con variantes",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 27,
      "action": 4,
      "area": "catalogo",
      "a": "b_pre",
      "b": "actor",
      "text": "Mostrar prenda registrada",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 28,
      "action": 5,
      "area": "catalogo",
      "a": "actor",
      "b": "b_pre",
      "text": "Editar datos, precios y ofertas",
      "kind": "ui",
      "color": "#28343E",
      "source": null,
      "symbol": null
    },
    {
      "n": 29,
      "action": 5,
      "area": "catalogo",
      "a": "b_pre",
      "b": "control",
      "text": "actualizar_prenda(id, cambios)",
      "kind": "invoke",
      "color": "#215D9C",
      "source": "Parcial2_backend/app/routers/prendas.py",
      "symbol": "actualizar_prenda",
      "line": 274
    },
    {
      "n": 30,
      "action": 5,
      "area": "catalogo",
      "a": "control",
      "b": "prenda",
      "text": "actualizar_prenda(id, cambios)",
      "kind": "write",
      "color": "#AC3636",
      "source": "Parcial2_backend/app/services/prenda_service.py",
      "symbol": "actualizar_prenda",
      "line": 363
    },
    {
      "n": 31,
      "action": 5,
      "area": "catalogo",
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
      "n": 32,
      "action": 5,
      "area": "catalogo",
      "a": "control",
      "b": "b_pre",
      "text": "prenda actualizada",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    },
    {
      "n": 33,
      "action": 6,
      "area": "catalogo",
      "a": "actor",
      "b": "b_pre",
      "text": "Inhabilitar prenda",
      "kind": "ui",
      "color": "#28343E",
      "source": null,
      "symbol": null
    },
    {
      "n": 34,
      "action": 6,
      "area": "catalogo",
      "a": "b_pre",
      "b": "control",
      "text": "inhabilitar_prenda(id)",
      "kind": "invoke",
      "color": "#215D9C",
      "source": "Parcial2_backend/app/routers/prendas.py",
      "symbol": "inhabilitar_prenda",
      "line": 362
    },
    {
      "n": 35,
      "action": 6,
      "area": "catalogo",
      "a": "control",
      "b": "prenda",
      "text": "inhabilitar_prenda(id)",
      "kind": "write",
      "color": "#AC3636",
      "source": "Parcial2_backend/app/services/prenda_service.py",
      "symbol": "inhabilitar_prenda",
      "line": 437
    },
    {
      "n": 36,
      "action": 6,
      "area": "catalogo",
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
      "n": 37,
      "action": 6,
      "area": "catalogo",
      "a": "control",
      "b": "b_pre",
      "text": "prenda inactiva",
      "kind": "reply",
      "color": "#287947",
      "source": null,
      "symbol": null
    }
  ],
  "views": [
    {
      "name": "CU06 - Robustez simplificada",
      "title": "CU06 - Administrar catálogo de prendas - Diagrama de robustez",
      "width": 4600,
      "height": 2350,
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
        "categoria": {
          "x": 4300,
          "y": 260
        },
        "temporada": {
          "x": 4300,
          "y": 650
        },
        "prenda": {
          "x": 4300,
          "y": 1050
        },
        "variante": {
          "x": 4300,
          "y": 1490
        },
        "bitacora": {
          "x": 4300,
          "y": 2050
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
              "y": 770,
              "width": 600,
              "height": 44,
              "forward": true
            },
            {
              "n": 7,
              "x": 650,
              "y": 814,
              "width": 600,
              "height": 44,
              "forward": true
            },
            {
              "n": 13,
              "x": 650,
              "y": 858,
              "width": 600,
              "height": 44,
              "forward": true
            },
            {
              "n": 19,
              "x": 650,
              "y": 902,
              "width": 600,
              "height": 44,
              "forward": true
            },
            {
              "n": 28,
              "x": 650,
              "y": 946,
              "width": 600,
              "height": 44,
              "forward": true
            },
            {
              "n": 33,
              "x": 650,
              "y": 990,
              "width": 600,
              "height": 44,
              "forward": true
            },
            {
              "n": 6,
              "x": 650,
              "y": 1110,
              "width": 600,
              "height": 44,
              "forward": false
            },
            {
              "n": 27,
              "x": 650,
              "y": 1154,
              "width": 600,
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
              "y": 770,
              "width": 550,
              "height": 44,
              "forward": true
            },
            {
              "n": 8,
              "x": 1650,
              "y": 814,
              "width": 550,
              "height": 44,
              "forward": true
            },
            {
              "n": 14,
              "x": 1650,
              "y": 858,
              "width": 550,
              "height": 44,
              "forward": true
            },
            {
              "n": 20,
              "x": 1650,
              "y": 902,
              "width": 550,
              "height": 44,
              "forward": true
            },
            {
              "n": 29,
              "x": 1650,
              "y": 946,
              "width": 550,
              "height": 44,
              "forward": true
            },
            {
              "n": 34,
              "x": 1650,
              "y": 990,
              "width": 550,
              "height": 44,
              "forward": true
            },
            {
              "n": 5,
              "x": 1650,
              "y": 1110,
              "width": 550,
              "height": 44,
              "forward": false
            },
            {
              "n": 12,
              "x": 1650,
              "y": 1154,
              "width": 550,
              "height": 44,
              "forward": false
            },
            {
              "n": 18,
              "x": 1650,
              "y": 1198,
              "width": 550,
              "height": 44,
              "forward": false
            },
            {
              "n": 26,
              "x": 1650,
              "y": 1242,
              "width": 550,
              "height": 44,
              "forward": false
            },
            {
              "n": 32,
              "x": 1650,
              "y": 1286,
              "width": 550,
              "height": 44,
              "forward": false
            },
            {
              "n": 37,
              "x": 1650,
              "y": 1330,
              "width": 550,
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
              2465,
              1050
            ],
            [
              2720,
              1050
            ],
            [
              4235,
              1050
            ]
          ],
          "rows": [
            {
              "n": 3,
              "x": 3300,
              "y": 858,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 21,
              "x": 3300,
              "y": 902,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 30,
              "x": 3300,
              "y": 946,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 35,
              "x": 3300,
              "y": 990,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 4,
              "x": 3300,
              "y": 1110,
              "width": 1050,
              "height": 44,
              "forward": false
            },
            {
              "n": 22,
              "x": 3300,
              "y": 1154,
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
              2465,
              1050
            ],
            [
              2720,
              260
            ],
            [
              4235,
              260
            ]
          ],
          "rows": [
            {
              "n": 9,
              "x": 3300,
              "y": 200,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 10,
              "x": 3300,
              "y": 320,
              "width": 1050,
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
              2465,
              1050
            ],
            [
              2720,
              2050
            ],
            [
              4235,
              2050
            ]
          ],
          "rows": [
            {
              "n": 11,
              "x": 3300,
              "y": 1814,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 17,
              "x": 3300,
              "y": 1858,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 25,
              "x": 3300,
              "y": 1902,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 31,
              "x": 3300,
              "y": 1946,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 36,
              "x": 3300,
              "y": 1990,
              "width": 1050,
              "height": 44,
              "forward": true
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
              2465,
              1050
            ],
            [
              2720,
              650
            ],
            [
              4235,
              650
            ]
          ],
          "rows": [
            {
              "n": 15,
              "x": 3300,
              "y": 590,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 16,
              "x": 3300,
              "y": 710,
              "width": 1050,
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
              2465,
              1050
            ],
            [
              2720,
              1490
            ],
            [
              4235,
              1490
            ]
          ],
          "rows": [
            {
              "n": 23,
              "x": 3300,
              "y": 1430,
              "width": 1050,
              "height": 44,
              "forward": true
            },
            {
              "n": 24,
              "x": 3300,
              "y": 1550,
              "width": 1050,
              "height": 44,
              "forward": false
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
    Repository.WriteOutput("Script", "CU06 finalizado: " + CU06_MODEL.messages.length + " mensajes en " + CU06_MODEL.views.length + " vista(s).", 0);
}

main();
