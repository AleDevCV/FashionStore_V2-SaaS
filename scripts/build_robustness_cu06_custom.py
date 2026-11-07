"""
=============================================================================
GENERADOR Y VALIDADOR DE DIAGRAMA DE ROBUSTEZ (ICONIX) - CU06
"CU06 - Administrar catálogo de prendas"
FashionStore SaaS - Sistemas de Información II (UAGRM)
=============================================================================
Cumplimiento estricto de las 4 reglas fundamentales de robustez:
1. Actores solo se comunican con Fronteras (Boundary).
2. Fronteras solo se conectan con Actores y Controles.
3. Entidades solo se conectan con Controles.
4. Controles pueden conectarse con Fronteras, Entidades y otros Controles.
=============================================================================
"""

import os
import sys
import json
import math
import html
from pathlib import Path
import xml.etree.ElementTree as ET

# Definición de rutas
ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "diagramas_robustez"
OUT_DIR.mkdir(parents=True, exist_ok=True)

DRAWIO_FILE = OUT_DIR / "CU06_Diagrama_Robustez.drawio"
VALIDATION_FILE = OUT_DIR / "CU06_Diagrama_Robustez_Validacion.json"
TRACE_FILE = OUT_DIR / "CU06_Diagrama_Robustez_Trazabilidad.json"

# Dimensiones generales del lienzo Draw.io
CANVAS_W = 3400
CANVAS_H = 2200

# Paleta de colores formal y profesional
COLOR_ACTOR = "#7B1FA2"      # Púrpura formal
COLOR_BOUNDARY = "#0288D1"   # Azul interfaces
COLOR_CONTROL = "#2E7D32"    # Verde controles de negocio
COLOR_ENTITY = "#E65100"     # Ámbar/Naranja entidades persistentes
COLOR_TEXT_MAIN = "#263238"  # Gris oscuro tipografía
COLOR_LINE_ACT = "#546E7A"   # Líneas de interacción actor-frontera
COLOR_LINE_CTRL = "#1565C0"  # Flujo entre controles
COLOR_LINE_ENT = "#E65100"   # Acceso a datos
COLOR_LINE_REPLY = "#00838F" # Retorno a interfaces
COLOR_LINE_ERR = "#C62828"   # Excepciones / errores

# Definición exhaustiva de Nodos
NODES = [
    # ------------------ ZONA 1: ACTORES ------------------
    {
        "id": "act_admin",
        "kind": "actor",
        "title": "Administrador de Empresa",
        "sub": "«actor»\nGestión integral del catálogo,\nprecios, ofertas y clasificación",
        "x": 160,
        "y": 660,
        "w": 60,
        "h": 90,
        "fill": "#F3E5F5",
        "stroke": COLOR_ACTOR
    },
    {
        "id": "act_inventario",
        "kind": "actor",
        "title": "Encargado de Inventario",
        "sub": "«actor»\nGestión de prendas, variantes,\nmedidas y stock por sucursal",
        "x": 160,
        "y": 1360,
        "w": 60,
        "h": 90,
        "fill": "#F3E5F5",
        "stroke": COLOR_ACTOR
    },

    # ------------------ ZONA 2: FRONTERAS ------------------
    {
        "id": "bnd_notificaciones",
        "kind": "boundary",
        "title": "UI_Notificaciones",
        "sub": "«boundary»\nPanel de Retroalimentación\n(Toast / Alertas Éxito y Error)",
        "x": 640,
        "y": 240,
        "w": 80,
        "h": 80,
        "fill": "#E1F5FE",
        "stroke": COLOR_BOUNDARY
    },
    {
        "id": "bnd_panel_catalogo",
        "kind": "boundary",
        "title": "UI_PanelCatalogo",
        "sub": "«boundary»\nPanel Catálogo de Prendas\n(Prendas / Tabla Maestra)",
        "x": 640,
        "y": 600,
        "w": 80,
        "h": 80,
        "fill": "#E1F5FE",
        "stroke": COLOR_BOUNDARY
    },
    {
        "id": "bnd_modal_prenda",
        "kind": "boundary",
        "title": "UI_ModalPrenda",
        "sub": "«boundary»\nFormulario Prenda y Variantes\n(PrendaModal / Matriz Talla-Color)",
        "x": 640,
        "y": 1020,
        "w": 80,
        "h": 80,
        "fill": "#E1F5FE",
        "stroke": COLOR_BOUNDARY
    },
    {
        "id": "bnd_modal_categoria",
        "kind": "boundary",
        "title": "UI_ModalCategoria",
        "sub": "«boundary»\nGestor de Categorías\n(CategoriaModal / Jerarquía)",
        "x": 640,
        "y": 1480,
        "w": 80,
        "h": 80,
        "fill": "#E1F5FE",
        "stroke": COLOR_BOUNDARY
    },
    {
        "id": "bnd_modal_temporada",
        "kind": "boundary",
        "title": "UI_ModalTemporada",
        "sub": "«boundary»\nGestor de Temporadas\n(TemporadaModal / Vigencias)",
        "x": 640,
        "y": 1840,
        "w": 80,
        "h": 80,
        "fill": "#E1F5FE",
        "stroke": COLOR_BOUNDARY
    },

    # ------------------ ZONA 3: CONTROLES PRIMARIOS ------------------
    {
        "id": "ctrl_consultar_catalogo",
        "kind": "control",
        "title": "Ctrl_ConsultarCatalogo",
        "sub": "«control»\nConsultar Catálogo y Filtros\n(catalogo.py / svc.listar_prendas)",
        "x": 1240,
        "y": 500,
        "w": 80,
        "h": 80,
        "fill": "#E8F5E9",
        "stroke": COLOR_CONTROL
    },
    {
        "id": "ctrl_gestionar_prenda",
        "kind": "control",
        "title": "Ctrl_GestionarPrenda",
        "sub": "«control»\nGestionar Prenda Maestra\n(prendas.py / svc.crear_prenda)",
        "x": 1240,
        "y": 1020,
        "w": 80,
        "h": 80,
        "fill": "#E8F5E9",
        "stroke": COLOR_CONTROL
    },
    {
        "id": "ctrl_gestionar_clasificacion",
        "kind": "control",
        "title": "Ctrl_GestionarClasificacion",
        "sub": "«control»\nGestionar Categorías y Períodos\n(categorias.py / temporadas.py)",
        "x": 1240,
        "y": 1660,
        "w": 80,
        "h": 80,
        "fill": "#E8F5E9",
        "stroke": COLOR_CONTROL
    },

    # ------------------ ZONA 4: CONTROLES ESPECIALIZADOS ------------------
    {
        "id": "ctrl_validar_reglas",
        "kind": "control",
        "title": "Ctrl_ValidarReglasNegocio",
        "sub": "«control»\nValidar Reglas y Unicidad SKU\n(svc.existe_sku / validaciones)",
        "x": 1850,
        "y": 740,
        "w": 80,
        "h": 80,
        "fill": "#E8F5E9",
        "stroke": COLOR_CONTROL
    },
    {
        "id": "ctrl_procesar_imagen",
        "kind": "control",
        "title": "Ctrl_ProcesarImagen",
        "sub": "«control»\nProcesar Fotografía Principal\n(image_storage_service)",
        "x": 1850,
        "y": 940,
        "w": 80,
        "h": 80,
        "fill": "#E8F5E9",
        "stroke": COLOR_CONTROL
    },
    {
        "id": "ctrl_generar_variantes",
        "kind": "control",
        "title": "Ctrl_GenerarVariantesSKU",
        "sub": "«control»\nGenerar Variantes y Multicolores\n(svc._crear_variante / SKU derivado)",
        "x": 1850,
        "y": 1140,
        "w": 80,
        "h": 80,
        "fill": "#E8F5E9",
        "stroke": COLOR_CONTROL
    },
    {
        "id": "ctrl_inicializar_stock",
        "kind": "control",
        "title": "Ctrl_InicializarInventario",
        "sub": "«control»\nInicializar Stock en Sucursales\n(inventario / stock_inicial)",
        "x": 1850,
        "y": 1340,
        "w": 80,
        "h": 80,
        "fill": "#E8F5E9",
        "stroke": COLOR_CONTROL
    },
    {
        "id": "ctrl_registrar_auditoria",
        "kind": "control",
        "title": "Ctrl_RegistrarAuditoria",
        "sub": "«control»\nRegistrar Bitácora Forense\n(bitacora_service / IP y Acción)",
        "x": 1850,
        "y": 1800,
        "w": 80,
        "h": 80,
        "fill": "#E8F5E9",
        "stroke": COLOR_CONTROL
    },

    # ------------------ ZONA 5: ENTIDADES ------------------
    {
        "id": "ent_categoria",
        "kind": "entity",
        "title": "Categoría",
        "sub": "«entity»\nCategoría de Prenda\n(categoria)",
        "x": 2700,
        "y": 280,
        "w": 80,
        "h": 80,
        "fill": "#FFF3E0",
        "stroke": COLOR_ENTITY
    },
    {
        "id": "ent_temporada",
        "kind": "entity",
        "title": "Temporada / Colección",
        "sub": "«entity»\nTemporada y Colección\n(temporada)",
        "x": 2700,
        "y": 440,
        "w": 80,
        "h": 80,
        "fill": "#FFF3E0",
        "stroke": COLOR_ENTITY
    },
    {
        "id": "ent_prenda",
        "kind": "entity",
        "title": "Prenda",
        "sub": "«entity»\nPrenda Maestra del Catálogo\n(prenda)",
        "x": 2700,
        "y": 640,
        "w": 80,
        "h": 80,
        "fill": "#FFF3E0",
        "stroke": COLOR_ENTITY
    },
    {
        "id": "ent_imagen",
        "kind": "entity",
        "title": "Imagen de Prenda",
        "sub": "«entity»\nFotografía Principal / Galería\n(imagen_prenda)",
        "x": 2700,
        "y": 820,
        "w": 80,
        "h": 80,
        "fill": "#FFF3E0",
        "stroke": COLOR_ENTITY
    },
    {
        "id": "ent_talla",
        "kind": "entity",
        "title": "Talla",
        "sub": "«entity»\nTalla Comercial\n(talla)",
        "x": 2700,
        "y": 980,
        "w": 80,
        "h": 80,
        "fill": "#FFF3E0",
        "stroke": COLOR_ENTITY
    },
    {
        "id": "ent_color",
        "kind": "entity",
        "title": "Color",
        "sub": "«entity»\nColor y Código HEX\n(color)",
        "x": 2700,
        "y": 1120,
        "w": 80,
        "h": 80,
        "fill": "#FFF3E0",
        "stroke": COLOR_ENTITY
    },
    {
        "id": "ent_variante",
        "kind": "entity",
        "title": "Variante de Prenda",
        "sub": "«entity»\nVariante Física Talla-Color\n(variante_prenda)",
        "x": 2700,
        "y": 1280,
        "w": 80,
        "h": 80,
        "fill": "#FFF3E0",
        "stroke": COLOR_ENTITY
    },
    {
        "id": "ent_sucursal",
        "kind": "entity",
        "title": "Sucursal",
        "sub": "«entity»\nSucursales Activas\n(sucursal)",
        "x": 2700,
        "y": 1440,
        "w": 80,
        "h": 80,
        "fill": "#FFF3E0",
        "stroke": COLOR_ENTITY
    },
    {
        "id": "ent_inventario",
        "kind": "entity",
        "title": "Inventario",
        "sub": "«entity»\nStock por Sucursal y Variante\n(inventario)",
        "x": 2700,
        "y": 1600,
        "w": 80,
        "h": 80,
        "fill": "#FFF3E0",
        "stroke": COLOR_ENTITY
    },
    {
        "id": "ent_movimiento",
        "kind": "entity",
        "title": "Movimiento de Inventario",
        "sub": "«entity»\nKardex y Entrada Inicial\n(movimiento_inventario)",
        "x": 2700,
        "y": 1760,
        "w": 80,
        "h": 80,
        "fill": "#FFF3E0",
        "stroke": COLOR_ENTITY
    },
    {
        "id": "ent_bitacora",
        "kind": "entity",
        "title": "Bitácora",
        "sub": "«entity»\nRegistro Forense de Auditoría\n(bitacora)",
        "x": 2700,
        "y": 1940,
        "w": 80,
        "h": 80,
        "fill": "#FFF3E0",
        "stroke": COLOR_ENTITY
    }
]

BY_ID = {n["id"]: n for n in NODES}

# Definición de conexiones (Edges) con trazabilidad funcional
EDGES = [
    # --- ACTORES A FRONTERAS ---
    {
        "id": "e_01",
        "source": "act_admin",
        "target": "bnd_panel_catalogo",
        "label": "1: Solicitar gestión de catálogo",
        "color": COLOR_LINE_ACT
    },
    {
        "id": "e_02",
        "source": "act_admin",
        "target": "bnd_modal_prenda",
        "label": "2: Abrir formulario alta / edición de prenda",
        "color": COLOR_LINE_ACT
    },
    {
        "id": "e_03",
        "source": "act_admin",
        "target": "bnd_modal_categoria",
        "label": "Gestionar árbol de categorías",
        "color": COLOR_LINE_ACT
    },
    {
        "id": "e_04",
        "source": "act_admin",
        "target": "bnd_modal_temporada",
        "label": "Gestionar temporadas y colecciones",
        "color": COLOR_LINE_ACT
    },
    {
        "id": "e_05",
        "source": "act_inventario",
        "target": "bnd_panel_catalogo",
        "label": "Consultar catálogo y existencias",
        "color": COLOR_LINE_ACT
    },
    {
        "id": "e_06",
        "source": "act_inventario",
        "target": "bnd_modal_prenda",
        "label": "Registrar variantes, medidas y stock inicial",
        "color": COLOR_LINE_ACT
    },
    {
        "id": "e_07",
        "source": "bnd_notificaciones",
        "target": "act_admin",
        "label": "Visualizar confirmaciones y alertas",
        "color": COLOR_LINE_REPLY
    },
    {
        "id": "e_08",
        "source": "bnd_notificaciones",
        "target": "act_inventario",
        "label": "Visualizar confirmaciones y alertas",
        "color": COLOR_LINE_REPLY
    },

    # --- FRONTERAS A CONTROLES (Y RETORNOS) ---
    {
        "id": "e_09",
        "source": "bnd_panel_catalogo",
        "target": "ctrl_consultar_catalogo",
        "label": "3: Enviar parámetros de búsqueda y filtros",
        "color": COLOR_LINE_ACT
    },
    {
        "id": "e_10",
        "source": "ctrl_consultar_catalogo",
        "target": "bnd_panel_catalogo",
        "label": "4: Devolver lista de prendas con stock consolidado",
        "color": COLOR_LINE_REPLY
    },
    {
        "id": "e_11",
        "source": "bnd_modal_prenda",
        "target": "ctrl_gestionar_prenda",
        "label": "5: Enviar formulario de prenda, variantes y foto",
        "color": COLOR_LINE_ACT
    },
    {
        "id": "e_12",
        "source": "ctrl_gestionar_prenda",
        "target": "bnd_modal_prenda",
        "label": "Cargar selectores de tallas y colores",
        "color": COLOR_LINE_REPLY
    },
    {
        "id": "e_13",
        "source": "bnd_modal_categoria",
        "target": "ctrl_gestionar_clasificacion",
        "label": "Enviar datos de categoría y categoría padre",
        "color": COLOR_LINE_ACT
    },
    {
        "id": "e_14",
        "source": "bnd_modal_temporada",
        "target": "ctrl_gestionar_clasificacion",
        "label": "Enviar temporada, descripción y fechas de vigencia",
        "color": COLOR_LINE_ACT
    },
    {
        "id": "e_15",
        "source": "ctrl_validar_reglas",
        "target": "bnd_notificaciones",
        "label": "[Alt: Error]: Alerta SKU duplicado / precio negativo",
        "color": COLOR_LINE_ERR
    },
    {
        "id": "e_16",
        "source": "ctrl_gestionar_prenda",
        "target": "bnd_notificaciones",
        "label": "12: [Éxito]: Notificar confirmación de guardado",
        "color": COLOR_LINE_REPLY
    },
    {
        "id": "e_17",
        "source": "ctrl_gestionar_prenda",
        "target": "bnd_panel_catalogo",
        "label": "13: Refrescar catálogo maestro actualizado",
        "color": COLOR_LINE_REPLY
    },
    {
        "id": "e_18",
        "source": "ctrl_gestionar_clasificacion",
        "target": "bnd_notificaciones",
        "label": "Notificar resultado de clasificación",
        "color": COLOR_LINE_REPLY
    },

    # --- CONTROLES A OTROS CONTROLES ---
    {
        "id": "e_19",
        "source": "ctrl_gestionar_prenda",
        "target": "ctrl_validar_reglas",
        "label": "6: Validar unicidad SKU, categoría y precios",
        "color": COLOR_LINE_CTRL
    },
    {
        "id": "e_20",
        "source": "ctrl_gestionar_prenda",
        "target": "ctrl_procesar_imagen",
        "label": "8: Procesar y almacenar fotografía principal",
        "color": COLOR_LINE_CTRL
    },
    {
        "id": "e_21",
        "source": "ctrl_gestionar_prenda",
        "target": "ctrl_generar_variantes",
        "label": "9: Generar matriz de variantes y multicolores",
        "color": COLOR_LINE_CTRL
    },
    {
        "id": "e_22",
        "source": "ctrl_gestionar_prenda",
        "target": "ctrl_inicializar_stock",
        "label": "10: Inicializar inventario en sucursales activas",
        "color": COLOR_LINE_CTRL
    },
    {
        "id": "e_23",
        "source": "ctrl_gestionar_prenda",
        "target": "ctrl_registrar_auditoria",
        "label": "11: Auditar alta/edición (INSERT/UPDATE)",
        "color": COLOR_LINE_CTRL
    },
    {
        "id": "e_24",
        "source": "ctrl_gestionar_clasificacion",
        "target": "ctrl_registrar_auditoria",
        "label": "Auditar cambios en categorías / temporadas",
        "color": COLOR_LINE_CTRL
    },

    # --- CONTROLES A ENTIDADES ---
    {
        "id": "e_25",
        "source": "ctrl_consultar_catalogo",
        "target": "ent_prenda",
        "label": "SELECT * FROM prenda WHERE filtros",
        "color": COLOR_LINE_ENT
    },
    {
        "id": "e_26",
        "source": "ctrl_consultar_catalogo",
        "target": "ent_categoria",
        "label": "Resolver nombre de categorías",
        "color": COLOR_LINE_ENT
    },
    {
        "id": "e_27",
        "source": "ctrl_consultar_catalogo",
        "target": "ent_temporada",
        "label": "Resolver temporadas comerciales activas",
        "color": COLOR_LINE_ENT
    },
    {
        "id": "e_28",
        "source": "ctrl_consultar_catalogo",
        "target": "ent_inventario",
        "label": "SUM(stock) consolidado por variante",
        "color": COLOR_LINE_ENT
    },
    {
        "id": "e_29",
        "source": "ctrl_validar_reglas",
        "target": "ent_prenda",
        "label": "SELECT 1 WHERE sku = %s (existe_sku)",
        "color": COLOR_LINE_ENT
    },
    {
        "id": "e_30",
        "source": "ctrl_validar_reglas",
        "target": "ent_categoria",
        "label": "Verificar categoría activa del tenant",
        "color": COLOR_LINE_ENT
    },
    {
        "id": "e_31",
        "source": "ctrl_validar_reglas",
        "target": "ent_temporada",
        "label": "Verificar temporada comercial existente",
        "color": COLOR_LINE_ENT
    },
    {
        "id": "e_32",
        "source": "ctrl_gestionar_prenda",
        "target": "ent_prenda",
        "label": "7: INSERT / UPDATE datos maestros y precios",
        "color": COLOR_LINE_ENT
    },
    {
        "id": "e_33",
        "source": "ctrl_gestionar_prenda",
        "target": "ent_talla",
        "label": "SELECT tallas disponibles (listar_tallas)",
        "color": COLOR_LINE_ENT
    },
    {
        "id": "e_34",
        "source": "ctrl_gestionar_prenda",
        "target": "ent_color",
        "label": "SELECT colores disponibles (listar_colores)",
        "color": COLOR_LINE_ENT
    },
    {
        "id": "e_35",
        "source": "ctrl_procesar_imagen",
        "target": "ent_imagen",
        "label": "INSERT imagen_prenda (url, es_principal)",
        "color": COLOR_LINE_ENT
    },
    {
        "id": "e_36",
        "source": "ctrl_generar_variantes",
        "target": "ent_variante",
        "label": "INSERT variante_prenda (sku_variante, color_ids)",
        "color": COLOR_LINE_ENT
    },
    {
        "id": "e_37",
        "source": "ctrl_inicializar_stock",
        "target": "ent_sucursal",
        "label": "SELECT sucursales activas autorizadas",
        "color": COLOR_LINE_ENT
    },
    {
        "id": "e_38",
        "source": "ctrl_inicializar_stock",
        "target": "ent_inventario",
        "label": "INSERT inventario (sucursal, variante, stock)",
        "color": COLOR_LINE_ENT
    },
    {
        "id": "e_39",
        "source": "ctrl_inicializar_stock",
        "target": "ent_movimiento",
        "label": "INSERT movimiento_inventario (Entrada inicial)",
        "color": COLOR_LINE_ENT
    },
    {
        "id": "e_40",
        "source": "ctrl_gestionar_clasificacion",
        "target": "ent_categoria",
        "label": "INSERT / UPDATE categoria (validar sin ciclos)",
        "color": COLOR_LINE_ENT
    },
    {
        "id": "e_41",
        "source": "ctrl_gestionar_clasificacion",
        "target": "ent_temporada",
        "label": "INSERT / UPDATE temporada (validar inicio <= fin)",
        "color": COLOR_LINE_ENT
    },
    {
        "id": "e_42",
        "source": "ctrl_registrar_auditoria",
        "target": "ent_bitacora",
        "label": "INSERT bitacora (usuario, ip, accion, detalle)",
        "color": COLOR_LINE_ENT
    }
]


def validar_reglas_robustez():
    """Valida programáticamente las 4 reglas fundamentales del diagrama."""
    errores = []
    kind_by_id = {n["id"]: n["kind"] for n in NODES}

    for e in EDGES:
        s_id = e["source"]
        t_id = e["target"]
        s_kind = kind_by_id.get(s_id)
        t_kind = kind_by_id.get(t_id)

        if not s_kind or not t_kind:
            errores.append(f"Conexión con nodo no definido: {s_id} -> {t_id}")
            continue

        # Regla 1: Actores solo con Frontera
        if s_kind == "actor" and t_kind != "boundary":
            errores.append(f"Regla 1 violada: Actor '{s_id}' conectado a '{t_id}' de tipo '{t_kind}'")
        if t_kind == "actor" and s_kind != "boundary":
            errores.append(f"Regla 1 violada: '{s_id}' de tipo '{s_kind}' conectado a Actor '{t_id}'")

        # Regla 2: Fronteras solo con Actores y Controles
        if s_kind == "boundary" and t_kind not in ("actor", "control"):
            errores.append(f"Regla 2 violada: Frontera '{s_id}' conectada a '{t_id}' de tipo '{t_kind}'")
        if t_kind == "boundary" and s_kind not in ("actor", "control"):
            errores.append(f"Regla 2 violada: '{s_id}' de tipo '{s_kind}' conectado a Frontera '{t_id}'")

        # Regla 3: Entidades solo con Controles
        if s_kind == "entity" and t_kind != "control":
            errores.append(f"Regla 3 violada: Entidad '{s_id}' conectada a '{t_id}' de tipo '{t_kind}'")
        if t_kind == "entity" and s_kind != "control":
            errores.append(f"Regla 3 violada: '{s_id}' de tipo '{s_kind}' conectado a Entidad '{t_id}'")

    return errores


def generar_drawio_xml():
    """Genera el XML en formato Draw.io (.drawio) con layout limpio y legible."""
    mxfile = ET.Element("mxfile", {
        "host": "app.diagrams.net",
        "version": "24.0.0",
        "type": "device"
    })
    diagram = ET.SubElement(mxfile, "diagram", {
        "id": "cu06-robustez-iconix",
        "name": "CU06 - Administrar Catálogo de Prendas"
    })
    graph_model = ET.SubElement(diagram, "mxGraphModel", {
        "dx": "2000",
        "dy": "1400",
        "grid": "1",
        "gridSize": "10",
        "guides": "1",
        "tooltips": "1",
        "connect": "1",
        "arrows": "1",
        "fold": "1",
        "page": "1",
        "pageScale": "1",
        "pageWidth": str(CANVAS_W),
        "pageHeight": str(CANVAS_H),
        "math": "0",
        "shadow": "0"
    })
    root = ET.SubElement(graph_model, "root")
    ET.SubElement(root, "mxCell", {"id": "0"})
    ET.SubElement(root, "mxCell", {"id": "1", "parent": "0"})

    # Marco exterior y fondo blanco
    frame = ET.SubElement(root, "mxCell", {
        "id": "frame_bg",
        "value": "",
        "style": "fillColor=#FFFFFF;strokeColor=#B0BEC5;strokeWidth=1.5;pointerEvents=0;",
        "vertex": "1",
        "parent": "1",
        "connectable": "0"
    })
    ET.SubElement(frame, "mxGeometry", {"x": "20", "y": "20", "width": str(CANVAS_W - 40), "height": str(CANVAS_H - 40), "as": "geometry"})

    # Encabezado Banner
    banner = ET.SubElement(root, "mxCell", {
        "id": "banner_header",
        "value": "",
        "style": "fillColor=#1E293B;strokeColor=none;rounded=0;",
        "vertex": "1",
        "parent": "1",
        "connectable": "0"
    })
    ET.SubElement(banner, "mxGeometry", {"x": "20", "y": "20", "width": str(CANVAS_W - 40), "height": "110", "as": "geometry"})

    title_text = (
        "&lt;font color='#FFFFFF' style='font-size:26px;font-weight:bold;'&gt;"
        "DIAGRAMA DE ROBUSTEZ (ICONIX): CU06 - ADMINISTRAR CATÁLOGO DE PRENDAS"
        "&lt;/font&gt;&lt;br&gt;"
        "&lt;font color='#94A3B8' style='font-size:15px;'&gt;"
        "FashionStore SaaS · Arquitectura de Casos de Uso del 2do Parcial · Separación Estricta: Actores, Fronteras, Controles y Entidades"
        "&lt;/font&gt;"
    )
    title_cell = ET.SubElement(root, "mxCell", {
        "id": "title_text",
        "value": title_text,
        "style": "text;html=1;align=center;verticalAlign=middle;fillColor=none;strokeColor=none;",
        "vertex": "1",
        "parent": "1",
        "connectable": "0"
    })
    ET.SubElement(title_cell, "mxGeometry", {"x": "40", "y": "30", "width": str(CANVAS_W - 80), "height": "90", "as": "geometry"})

    # Bounding Boxes de Zonas Arquitectónicas (Swimlanes / Tarjetas suaves)
    zones = [
        ("zone_act", "ZONA 1: ACTORES", 50, 150, 310, CANVAS_H - 190, "#FAF5FF", "#D8B4FE"),
        ("zone_bnd", "ZONA 2: OBJETOS DE FRONTERA (INTERFACES)", 400, 150, 560, CANVAS_H - 190, "#F0F9FF", "#BAE6FD"),
        ("zone_ctrl", "ZONA 3: CONTROLES DE NEGOCIO Y ORQUESTACIÓN", 1000, 150, 1340, CANVAS_H - 190, "#F0FDF4", "#BBF7D0"),
        ("zone_ent", "ZONA 4: ENTIDADES DE DOMINIO Y PERSISTENCIA", 2380, 150, 970, CANVAS_H - 190, "#FFFBEB", "#FDE68A"),
    ]
    for zid, ztitle, zx, zy, zw, zh, zfill, zstroke in zones:
        zbox = ET.SubElement(root, "mxCell", {
            "id": zid,
            "value": f"&lt;b&gt;{ztitle}&lt;/b&gt;",
            "style": f"rounded=1;fillColor={zfill};strokeColor={zstroke};strokeWidth=1.5;verticalAlign=top;align=left;spacingLeft=15;spacingTop=12;fontFamily=Arial;fontSize=13;fontColor=#475569;dashed=1;",
            "vertex": "1",
            "parent": "1",
            "connectable": "0"
        })
        ET.SubElement(zbox, "mxGeometry", {"x": str(zx), "y": str(zy), "width": str(zw), "height": str(zh), "as": "geometry"})

    # Tarjeta de Reglas de Robustez y Leyenda (Esquina inferior izquierda)
    rules_card_text = (
        "&lt;b style='font-size:15px;color:#0F172A;'&gt;REGLAS FUNDAMENTALES DE ROBUSTEZ (ICONIX)&lt;/b&gt;&lt;br&gt;&lt;br&gt;"
        "&lt;b style='color:#7B1FA2;'&gt;1. Actores solo hablan con Frontera:&lt;/b&gt;&lt;br&gt;"
        "&amp;nbsp;&amp;nbsp;Un actor no interactúa directamente con controles o entidades.&lt;br&gt;&lt;br&gt;"
        "&lt;b style='color:#0288D1;'&gt;2. Fronteras solo conectan con Actores y Controles:&lt;/b&gt;&lt;br&gt;"
        "&amp;nbsp;&amp;nbsp;Dos interfaces nunca se comunican directamente sin un control intermedio.&lt;br&gt;&lt;br&gt;"
        "&lt;b style='color:#E65100;'&gt;3. Entidades solo conectan con Controles:&lt;/b&gt;&lt;br&gt;"
        "&amp;nbsp;&amp;nbsp;Las tablas no se comunican directamente; toda lógica pasa por un control.&lt;br&gt;&lt;br&gt;"
        "&lt;b style='color:#2E7D32;'&gt;4. Controles pueden conectar con todo:&lt;/b&gt;&lt;br&gt;"
        "&amp;nbsp;&amp;nbsp;Tienen capacidad de enlazarse con fronteras, entidades y otros controles.&lt;br&gt;&lt;br&gt;"
        "&lt;i style='color:#64748B;'&gt;Verificado: 100% de cumplimiento en las 42 conexiones.&lt;/i&gt;"
    )
    rules_card = ET.SubElement(root, "mxCell", {
        "id": "rules_card",
        "value": rules_card_text,
        "style": "rounded=1;fillColor=#FFFFFF;strokeColor=#CBD5E1;strokeWidth=1.5;align=left;verticalAlign=top;spacing=12;fontFamily=Arial;fontSize=12;html=1;shadow=1;",
        "vertex": "1",
        "parent": "1",
        "connectable": "0"
    })
    ET.SubElement(rules_card, "mxGeometry", {"x": "60", "y": "1640", "width": "290", "height": "480", "as": "geometry"})

    # Renderizar Nodos
    for n in NODES:
        nid = n["id"]
        x, y, w, h = n["x"], n["y"], n["w"], n["h"]
        kind = n["kind"]

        # Estilo del símbolo Draw.io
        if kind == "actor":
            style = (
                f"shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;html=1;outlineConnect=0;"
                f"fillColor={n['fill']};strokeColor={n['stroke']};strokeWidth=2;fontFamily=Arial;"
            )
        elif kind == "boundary":
            style = (
                f"shape=umlBoundary;whiteSpace=wrap;html=1;verticalAlign=top;verticalLabelPosition=bottom;"
                f"fillColor={n['fill']};strokeColor={n['stroke']};strokeWidth=2;aspect=fixed;fontFamily=Arial;"
            )
        elif kind == "control":
            style = (
                f"shape=umlControl;whiteSpace=wrap;html=1;verticalAlign=top;verticalLabelPosition=bottom;"
                f"fillColor={n['fill']};strokeColor={n['stroke']};strokeWidth=2;aspect=fixed;fontFamily=Arial;"
            )
        elif kind == "entity":
            style = (
                f"shape=umlEntity;whiteSpace=wrap;html=1;verticalAlign=top;verticalLabelPosition=bottom;"
                f"fillColor={n['fill']};strokeColor={n['stroke']};strokeWidth=2;aspect=fixed;fontFamily=Arial;"
            )

        # Nodo visual principal
        cell = ET.SubElement(root, "mxCell", {
            "id": nid,
            "value": "",
            "style": style,
            "vertex": "1",
            "parent": "1"
        })
        ET.SubElement(cell, "mxGeometry", {
            "x": str(x - w // 2),
            "y": str(y - h // 2),
            "width": str(w),
            "height": str(h),
            "as": "geometry"
        })

        # Etiqueta tipográfica nítida debajo del símbolo
        label_text = f"&lt;b style='font-size:13px;color:#0F172A;'&gt;{n['title']}&lt;/b&gt;&lt;br&gt;&lt;span style='font-size:11px;color:#475569;'&gt;{n['sub'].replace(chr(10), '&lt;br&gt;')}&lt;/span&gt;"
        lbl = ET.SubElement(root, "mxCell", {
            "id": f"lbl_{nid}",
            "value": label_text,
            "style": "text;html=1;align=center;verticalAlign=top;whiteSpace=wrap;fillColor=none;strokeColor=none;fontFamily=Arial;",
            "vertex": "1",
            "parent": "1",
            "connectable": "0"
        })
        lbl_w = 260
        lbl_h = 75
        ET.SubElement(lbl, "mxGeometry", {
            "x": str(x - lbl_w // 2),
            "y": str(y + h // 2 + 10),
            "width": str(lbl_w),
            "height": str(lbl_h),
            "as": "geometry"
        })

    # Renderizar Conexiones (Edges)
    for e in EDGES:
        eid = e["id"]
        s_id = e["source"]
        t_id = e["target"]
        lbl = e["label"]
        color = e["color"]

        edge_style = (
            f"edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;"
            f"strokeColor={color};strokeWidth=1.8;endArrow=classic;endFill=1;startArrow=none;"
            f"fontFamily=Arial;fontSize=11;fontColor={color};labelBackgroundColor=#FFFFFF;labelBorderColor={color};spacing=3;"
        )

        edge = ET.SubElement(root, "mxCell", {
            "id": eid,
            "value": lbl,
            "style": edge_style,
            "edge": "1",
            "parent": "1",
            "source": s_id,
            "target": t_id
        })
        ET.SubElement(edge, "mxGeometry", {"relative": "1", "as": "geometry"})

    ET.indent(mxfile, space="  ")
    return ET.tostring(mxfile, encoding="utf-8", xml_declaration=True).decode("utf-8")


def main():
    print("=" * 70)
    print("EJECUTANDO CONSTRUCTOR DE DIAGRAMA DE ROBUSTEZ (ICONIX) - CU06")
    print("=" * 70)

    # 1. Validación de reglas
    errores = validar_reglas_robustez()
def generar_svg():
    """Genera una versión vectorial SVG pura para visualización directa."""
    SVG_FILE = OUT_DIR / "CU06_Diagrama_Robustez.svg"
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS_W}" height="{CANVAS_H}" viewBox="0 0 {CANVAS_W} {CANVAS_H}">',
        '<defs>',
        '<marker id="arrow_act" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto"><polygon points="0 0, 10 3.5, 0 7" fill="' + COLOR_LINE_ACT + '"/></marker>',
        '<marker id="arrow_ctrl" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto"><polygon points="0 0, 10 3.5, 0 7" fill="' + COLOR_LINE_CTRL + '"/></marker>',
        '<marker id="arrow_ent" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto"><polygon points="0 0, 10 3.5, 0 7" fill="' + COLOR_LINE_ENT + '"/></marker>',
        '<marker id="arrow_reply" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto"><polygon points="0 0, 10 3.5, 0 7" fill="' + COLOR_LINE_REPLY + '"/></marker>',
        '<marker id="arrow_err" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto"><polygon points="0 0, 10 3.5, 0 7" fill="' + COLOR_LINE_ERR + '"/></marker>',
        '</defs>',
        f'<rect width="{CANVAS_W}" height="{CANVAS_H}" fill="#FFFFFF"/>',
        f'<rect x="20" y="20" width="{CANVAS_W-40}" height="{CANVAS_H-40}" fill="none" stroke="#B0BEC5" stroke-width="1.5"/>',
        f'<rect x="20" y="20" width="{CANVAS_W-40}" height="110" fill="#1E293B"/>',
        f'<text x="{CANVAS_W/2}" y="65" text-anchor="middle" fill="#FFFFFF" font-family="Arial, sans-serif" font-size="26" font-weight="bold">DIAGRAMA DE ROBUSTEZ (ICONIX): CU06 - ADMINISTRAR CATÁLOGO DE PRENDAS</text>',
        f'<text x="{CANVAS_W/2}" y="100" text-anchor="middle" fill="#94A3B8" font-family="Arial, sans-serif" font-size="15">FashionStore SaaS · Arquitectura de Casos de Uso del 2do Parcial · Separación Estricta: Actores, Fronteras, Controles y Entidades</text>'
    ]

    # Zonas
    zones = [
        ("ZONA 1: ACTORES", 50, 150, 310, CANVAS_H - 190, "#FAF5FF", "#D8B4FE"),
        ("ZONA 2: OBJETOS DE FRONTERA (INTERFACES)", 400, 150, 560, CANVAS_H - 190, "#F0F9FF", "#BAE6FD"),
        ("ZONA 3: CONTROLES DE NEGOCIO Y ORQUESTACIÓN", 1000, 150, 1340, CANVAS_H - 190, "#F0FDF4", "#BBF7D0"),
        ("ZONA 4: ENTIDADES DE DOMINIO Y PERSISTENCIA", 2380, 150, 970, CANVAS_H - 190, "#FFFBEB", "#FDE68A"),
    ]
    for ztitle, zx, zy, zw, zh, zfill, zstroke in zones:
        parts.append(f'<rect x="{zx}" y="{zy}" width="{zw}" height="{zh}" rx="8" fill="{zfill}" stroke="{zstroke}" stroke-width="1.5" stroke-dasharray="6,6"/>')
        parts.append(f'<text x="{zx+15}" y="{zy+28}" fill="#475569" font-family="Arial, sans-serif" font-size="13" font-weight="bold">{ztitle}</text>')

    # Tarjeta de reglas
    parts.append(f'<rect x="60" y="1640" width="290" height="480" rx="8" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="1.5"/>')
    parts.append(f'<text x="75" y="1670" fill="#0F172A" font-family="Arial, sans-serif" font-size="14" font-weight="bold">REGLAS DE ROBUSTEZ (ICONIX)</text>')
    reglas_texto = [
        ("1. Actores solo hablan con Frontera:", COLOR_ACTOR, "   No interactúan con control o entidad."),
        ("2. Fronteras solo conectan con:", COLOR_BOUNDARY, "   Actores y Controles (no pantallas directas)."),
        ("3. Entidades solo conectan con:", COLOR_ENTITY, "   Controles (lógica media persistencia)."),
        ("4. Controles conectan con todo:", COLOR_CONTROL, "   Fronteras, Entidades y otros Controles.")
    ]
    ry = 1710
    for r_tit, r_col, r_desc in reglas_texto:
        parts.append(f'<text x="75" y="{ry}" fill="{r_col}" font-family="Arial, sans-serif" font-size="12" font-weight="bold">{r_tit}</text>')
        parts.append(f'<text x="75" y="{ry+20}" fill="#475569" font-family="Arial, sans-serif" font-size="11">{r_desc}</text>')
        ry += 50
    parts.append(f'<text x="75" y="{ry+20}" fill="#059669" font-family="Arial, sans-serif" font-size="12" font-style="italic">✓ Verificado: 100% de cumplimiento.</text>')

    # Conexiones (Edges)
    for e in EDGES:
        s = BY_ID[e["source"]]
        t = BY_ID[e["target"]]
        color = e["color"]
        marker = "arrow_act"
        if color == COLOR_LINE_CTRL:
            marker = "arrow_ctrl"
        elif color == COLOR_LINE_ENT:
            marker = "arrow_ent"
        elif color == COLOR_LINE_REPLY:
            marker = "arrow_reply"
        elif color == COLOR_LINE_ERR:
            marker = "arrow_err"

        # Trazo ortogonal suave
        sx, sy = s["x"], s["y"]
        tx, ty = t["x"], t["y"]

        # Determinar punto de anclaje simple
        if sx < tx:
            p1x, p1y = sx + s["w"] // 2, sy
            p2x, p2y = tx - t["w"] // 2, ty
        else:
            p1x, p1y = sx - s["w"] // 2, sy
            p2x, p2y = tx + t["w"] // 2, ty

        mid_x = (p1x + p2x) // 2
        path_d = f"M{p1x},{p1y} C{mid_x},{p1y} {mid_x},{p2y} {p2x},{p2y}"
        parts.append(f'<path d="{path_d}" fill="none" stroke="{color}" stroke-width="1.8" marker-end="url(#{marker})"/>')

        # Etiqueta de la conexión con fondo blanco
        lbl_x = (p1x + p2x) / 2
        lbl_y = (p1y + p2y) / 2 - 8
        lbl_text = html.escape(e["label"])
        lbl_w = len(lbl_text) * 7 + 16
        parts.append(f'<rect x="{lbl_x - lbl_w/2}" y="{lbl_y - 12}" width="{lbl_w}" height="20" rx="4" fill="#FFFFFF" stroke="{color}" stroke-width="1"/>')
        parts.append(f'<text x="{lbl_x}" y="{lbl_y+2}" text-anchor="middle" fill="{color}" font-family="Arial, sans-serif" font-size="10.5" font-weight="bold">{lbl_text}</text>')

    # Nodos
    R = 36
    for n in NODES:
        x, y = n["x"], n["y"]
        kind = n["kind"]
        fill = n["fill"]
        stroke = n["stroke"]

        if kind == "actor":
            parts.append(f'<g stroke="{stroke}" stroke-width="2" fill="{fill}">')
            parts.append(f'<circle cx="{x}" cy="{y-33}" r="12"/>')
            parts.append(f'<line x1="{x}" y1="{y-21}" x2="{x}" y2="{y+15}"/>')
            parts.append(f'<line x1="{x-26}" y1="{y-5}" x2="{x+26}" y2="{y-5}"/>')
            parts.append(f'<line x1="{x}" y1="{y+15}" x2="{x-24}" y2="{y+45}"/>')
            parts.append(f'<line x1="{x}" y1="{y+15}" x2="{x+24}" y2="{y+45}"/>')
            parts.append('</g>')
        elif kind == "boundary":
            parts.append(f'<circle cx="{x}" cy="{y}" r="{R}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
            parts.append(f'<line x1="{x-R-12}" y1="{y-R}" x2="{x-R-12}" y2="{y+R}" stroke="{stroke}" stroke-width="2.5"/>')
            parts.append(f'<line x1="{x-R-12}" y1="{y}" x2="{x-R}" y2="{y}" stroke="{stroke}" stroke-width="2.5"/>')
        elif kind == "control":
            parts.append(f'<circle cx="{x}" cy="{y}" r="{R}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
            parts.append(f'<path d="M{x+18},{y-R-4} C{x+2},{y-R-8} {x-14},{y-R+2} {x-22},{y-R+10}" fill="none" stroke="{stroke}" stroke-width="2.5"/>')
            parts.append(f'<polygon points="{x-24},{y-R+2} {x-20},{y-R+15} {x-11},{y-R+7}" fill="{stroke}"/>')
        elif kind == "entity":
            parts.append(f'<circle cx="{x}" cy="{y}" r="{R}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
            parts.append(f'<line x1="{x-R-8}" y1="{y+R+6}" x2="{x+R+8}" y2="{y+R+6}" stroke="{stroke}" stroke-width="3"/>')

        # Textos debajo del nodo
        parts.append(f'<text x="{x}" y="{y+R+24}" text-anchor="middle" fill="#0F172A" font-family="Arial, sans-serif" font-size="13" font-weight="bold">{html.escape(n["title"])}</text>')
        lines = n["sub"].splitlines()
        for idx, l in enumerate(lines):
            parts.append(f'<text x="{x}" y="{y+R+42+idx*16}" text-anchor="middle" fill="#475569" font-family="Arial, sans-serif" font-size="10.5">{html.escape(l)}</text>')

    parts.append('</svg>')
    svg_code = '\n'.join(parts)
    with open(SVG_FILE, "w", encoding="utf-8") as f:
        f.write(svg_code)
    print(f"[OK] Archivo SVG generado exitosamente:")
    print(f"     -> {SVG_FILE}")


def main():
    print("=" * 70)
    print("EJECUTANDO CONSTRUCTOR DE DIAGRAMA DE ROBUSTEZ (ICONIX) - CU06")
    print("=" * 70)

    # 1. Validación de reglas
    errores = validar_reglas_robustez()
    if errores:
        print(f"ERROR: Se detectaron {len(errores)} infracciones de las reglas de robustez:")
        for err in errores:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print("[OK] Verificación matemática superada: 0 infracciones.")
        print(f"     Total de Nodos: {len(NODES)} (Actores: 2, Fronteras: 5, Controles: 8, Entidades: 11)")
        print(f"     Total de Conexiones: {len(EDGES)} rigurosamente conformes.")

    # 2. Generación del XML Draw.io
    xml_content = generar_drawio_xml()
    with open(DRAWIO_FILE, "w", encoding="utf-8") as f:
        f.write(xml_content)
    print(f"[OK] Archivo Draw.io generado exitosamente:")
    print(f"     -> {DRAWIO_FILE}")

    # 3. Generación del SVG Vectorial
    generar_svg()

    # 4. Guardar archivo de validación JSON
    validacion_data = {
        "caso_uso": "CU06 - Administrar catálogo de prendas",
        "metodologia": "ICONIX Robustness Analysis",
        "cumplimiento_estricto_4_reglas": True,
        "regla_1_actores_solo_frontera": True,
        "regla_2_fronteras_solo_actores_y_controles": True,
        "regla_3_entidades_solo_controles": True,
        "regla_4_controles_interconectables": True,
        "total_actores": 2,
        "total_fronteras": 5,
        "total_controles": 8,
        "total_entidades": 11,
        "total_conexiones": len(EDGES),
        "infracciones": 0,
        "archivo_drawio": str(DRAWIO_FILE.name),
        "archivo_svg": "CU06_Diagrama_Robustez.svg"
    }
    with open(VALIDATION_FILE, "w", encoding="utf-8") as f:
        json.dump(validacion_data, f, indent=2, ensure_ascii=False)
    print(f"[OK] Archivo de validación JSON actualizado:")
    print(f"     -> {VALIDATION_FILE}")

    # 5. Guardar archivo de trazabilidad JSON
    trazabilidad_data = {
        "caso_uso": "CU06 - Administrar catálogo de prendas",
        "subcasos_consolidados": [
            {"id": "CU-10", "nombre": "Gestionar categorías", "responsable": "Administrador"},
            {"id": "CU-11", "nombre": "Gestionar temporadas y colecciones", "responsable": "Administrador"},
            {"id": "CU-12", "nombre": "Gestionar prendas y variantes", "responsable": "Administrador y Encargado de Inventario"}
        ],
        "nodos": NODES,
        "conexiones": EDGES
    }
    with open(TRACE_FILE, "w", encoding="utf-8") as f:
        json.dump(trazabilidad_data, f, indent=2, ensure_ascii=False)
    print(f"[OK] Archivo de trazabilidad JSON actualizado:")
    print(f"     -> {TRACE_FILE}")
    print("=" * 70)


if __name__ == "__main__":
    main()

