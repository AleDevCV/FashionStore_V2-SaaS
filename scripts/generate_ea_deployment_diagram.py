"""
==============================================================================
GENERADOR DE DIAGRAMA DE DESPLIEGUE - FASHIONSTORE (PARCIAL 2)
Script de Automatización COM para Enterprise Architect (EA)
Basado en las especificaciones de:
- SEGUNDO_EXAMEN_PARCIAL-FASHIONSTORE.docx
- docs/DESPLIEGUE_NATIVO.md
- docs/04_arquitectura_y_contratos.md
==============================================================================
"""

import os
import sys
import time
import win32com.client

EAP_PATH = r"C:\Sistemas_Informacion2-Parcial2\docs\Enterprise Architect\Parcial 2.eap"
IMG_PATH = r"C:\Sistemas_Informacion2-Parcial2\docs\Enterprise Architect\FashionStore_Diagrama_Despliegue.png"

# Colores en formato BGR para Enterprise Architect
C_BLUE   = 16111540  # RGB(180, 215, 245) - Nodos Servidor, Cloud, Internet, Switch
C_PEACH  = 14150655  # RGB(255, 235, 215) - Nodos «device» Dispositivos Cliente y Atacante
C_PINK   = 13499903  # RGB(255, 205, 205) - Entornos de Ejecución (OS / Containers / Runtimes)
C_WHITE  = 16777215  # RGB(255, 255, 255) - Componentes y Módulos de Software

class SequenceGenerator:
    def __init__(self):
        self.node_seq = 80
        self.env_seq = 50
        self.comp_seq = 1

    def next_node(self):
        val = self.node_seq
        self.node_seq += 1
        return val

    def next_env(self):
        val = self.env_seq
        self.env_seq += 1
        return val

    def next_comp(self):
        val = self.comp_seq
        self.comp_seq += 1
        return val

def crear_elemento(parent_pkg, tipo, nombre, estereotipo, color_fondo):
    elem = parent_pkg.Elements.AddNew(nombre, tipo)
    if estereotipo and estereotipo != "":
        elem.Stereotype = estereotipo
    elem.Update()
    if color_fondo:
        try:
            elem.SetAppearance(1, color_fondo, 0)
            elem.Update()
        except Exception:
            pass
    return elem

def crear_sub_elemento(parent_elem, tipo, nombre, estereotipo, color_fondo):
    elem = parent_elem.Elements.AddNew(nombre, tipo)
    if estereotipo and estereotipo != "":
        elem.Stereotype = estereotipo
    elem.Update()
    if color_fondo:
        try:
            elem.SetAppearance(1, color_fondo, 0)
            elem.Update()
        except Exception:
            pass
    return elem

def agregar_al_diagrama(diagram, elem, left, top, right, bottom, sequence):
    diag_obj = diagram.DiagramObjects.AddNew("", "")
    diag_obj.ElementID = elem.ElementID
    diag_obj.left = int(left)
    diag_obj.top = int(top)
    diag_obj.right = int(right)
    diag_obj.bottom = int(bottom)
    diag_obj.Sequence = int(sequence)
    diag_obj.Update()
    return diag_obj

def crear_enlace(repo, diagram, src, dst, label, c_src, c_dst):
    con = src.Connectors.AddNew(label, "Association")
    con.SupplierID = dst.ElementID
    con.Update()
    try:
        sql = f"UPDATE t_connector SET SourceCard = '{c_src}', DestCard = '{c_dst}' WHERE Connector_ID = {con.ConnectorID}"
        repo.Execute(sql)
    except Exception as ex:
        print(f"Error actualizando cardinalidad: {ex}")
    diagram.DiagramLinks.Refresh()
    return con

def main():
    print("=" * 75)
    print("INICIANDO CONSTRUCCIÓN DEL DIAGRAMA DE DESPLIEGUE EN ENTERPRISE ARCHITECT")
    print(f"Archivo destino: {EAP_PATH}")
    print("=" * 75)

    ea_app = win32com.client.Dispatch("EA.App")
    repo = ea_app.Repository
    
    if not repo.OpenFile(EAP_PATH):
        print("ERROR: No se pudo abrir el archivo .eap en Enterprise Architect.")
        sys.exit(1)

    try:
        seq_gen = SequenceGenerator()

        root_model = repo.Models.GetAt(0)
        
        # Eliminar paquetes previos para asegurar consistencia e idéntica numeración limpia
        for i in range(root_model.Packages.Count - 1, -1, -1):
            p = root_model.Packages.GetAt(i)
            if "despliegue" in p.Name.lower() or "testmini" in p.Name.lower():
                root_model.Packages.Delete(i)
                root_model.Packages.Refresh()
                print(f"Eliminado paquete antiguo: {p.Name}")

        target_pkg = root_model.Packages.AddNew("Diagrama de Despliegue - FashionStore (UML 2.5)", "")
        target_pkg.Update()

        diagram_name = "Arquitectura Física de Despliegue - FashionStore"
        diagram = target_pkg.Diagrams.AddNew(diagram_name, "Deployment")
        diagram.Update()

        print("[1/8] Construyendo Nodo 1: Servidor Base de Datos Central (PostgreSQL 17.11 / RLS)...")
        # 1. NODO BASE DE DATOS (Top-Left: left=50, top=-100, right=440, bottom=-720)
        n_db = crear_elemento(target_pkg, "Node", "«cloud»\nServidor Base de Datos Central\n(PostgreSQL 17.11 · Host Linux Debian 13)", "", C_BLUE)
        agregar_al_diagrama(diagram, n_db, 50, -100, 440, -720, sequence=seq_gen.next_node())

        env_db = crear_sub_elemento(n_db, "ExecutionEnvironment", "Managed Database Engine (PostgreSQL 17.11 Multi-Tenant VPC)", "executionEnvironment", C_PINK)
        agregar_al_diagrama(diagram, env_db, 70, -145, 420, -700, sequence=seq_gen.next_env())

        c_db1 = crear_sub_elemento(env_db, "Component", "PostgreSQL 17.11 (+ PostGIS Extension)\nPuerto 5432 SSL · Multi-Tenant con RLS", "database", C_WHITE)
        agregar_al_diagrama(diagram, c_db1, 85, -170, 405, -235, sequence=seq_gen.next_comp())

        c_db2 = crear_sub_elemento(env_db, "Component", "Motor Row Level Security (RLS) & Conexiones\nAislamiento lógico estricto por tenant_id", "service", C_WHITE)
        agregar_al_diagrama(diagram, c_db2, 85, -250, 405, -315, sequence=seq_gen.next_comp())

        c_db3 = crear_sub_elemento(env_db, "Component", "Pool de Conexiones psycopg2 & Transacciones ACID\nGestión de concurrencia y atomicidad transaccional", "service", C_WHITE)
        agregar_al_diagrama(diagram, c_db3, 85, -330, 405, -395, sequence=seq_gen.next_comp())

        c_db4 = crear_sub_elemento(env_db, "Component", "Almacén Local de Archivos y Comprobantes\nCustodia de respaldos, PDFs y assets en shared/files", "storage", C_WHITE)
        agregar_al_diagrama(diagram, c_db4, 85, -410, 405, -475, sequence=seq_gen.next_comp())

        note_db = target_pkg.Elements.AddNew("", "Note")
        note_db.Notes = "<b>Servidor Nativo Debian 13 (Trixie):</b>\n• Host Físico: 2 vCPU · 2 GB RAM · SSD NVMe\n• Base central: fashionstore_p2 en PostgreSQL 17\n• Cifrado AES-256 en Reposo · Backups PITR Diarios"
        note_db.ParentID = env_db.ElementID
        note_db.Update()
        agregar_al_diagrama(diagram, note_db, 85, -490, 405, -680, sequence=seq_gen.next_comp())

        print("[2/8] Construyendo Nodo 2: Servidor Backend Core (FastAPI / Python 3.13 / Uvicorn)...")
        # 2. NODO BACKEND CORE (Top-Center: left=480, top=-100, right=980, bottom=-720)
        n_be = crear_elemento(target_pkg, "Node", "«cloud»\nServidor Backend Core\n(FastAPI / Python 3.13 · Systemd Service · Uvicorn)", "", C_BLUE)
        agregar_al_diagrama(diagram, n_be, 480, -100, 980, -720, sequence=seq_gen.next_node())

        env_be = crear_sub_elemento(n_be, "ExecutionEnvironment", "Linux Service Runtime (Python 3.13.5 Virtualenv / Systemd)", "executionEnvironment", C_PINK)
        agregar_al_diagrama(diagram, env_be, 500, -145, 960, -700, sequence=seq_gen.next_env())

        c_be1 = crear_sub_elemento(env_be, "Component", "FastAPI ASGI Core & Router Hub (Python 3.13)\nUvicorn Worker 127.0.0.1:8002 · ASGI REST · HTTPS 443", "web", C_WHITE)
        agregar_al_diagrama(diagram, c_be1, 515, -170, 945, -230, sequence=seq_gen.next_comp())

        c_p1 = crear_sub_elemento(env_be, "Component", "P1: Seguridad, SaaS y Cuentas Globales\n(Auth JWT, Roles, Empresas CU01-CU05)", "package", C_WHITE)
        agregar_al_diagrama(diagram, c_p1, 515, -245, 720, -295, sequence=seq_gen.next_comp())

        c_p2 = crear_sub_elemento(env_be, "Component", "P2: Catálogo de Prendas y Clasificación\n(Variantes, Tallas, Colores CU06)", "package", C_WHITE)
        agregar_al_diagrama(diagram, c_p2, 740, -245, 945, -295, sequence=seq_gen.next_comp())

        c_p3 = crear_sub_elemento(env_be, "Component", "P3: Inventario Multisucursal y Proveedores (Kardex, Compras, Alertas CU07-10)", "package", C_WHITE)
        agregar_al_diagrama(diagram, c_p3, 515, -310, 945, -360, sequence=seq_gen.next_comp())

        c_p4 = crear_sub_elemento(env_be, "Component", "P4: Ventas POS, Carrito y Reservas (Checkout, Transacciones ACID, Retención 24h CU11-13)", "package", C_WHITE)
        agregar_al_diagrama(diagram, c_p4, 515, -375, 945, -425, sequence=seq_gen.next_comp())

        c_p5 = crear_sub_elemento(env_be, "Component", "P5: Sincronización Offline & Resiliencia (PWA / Mobile Sync, Resolución Conflictos CU16)", "package", C_WHITE)
        agregar_al_diagrama(diagram, c_p5, 515, -440, 945, -490, sequence=seq_gen.next_comp())

        c_p6 = crear_sub_elemento(env_be, "Component", "P6: Inteligencia Artificial & Modelos ML (Demanda, K-Means, Reportes Generativos CU17-18)", "package", C_WHITE)
        agregar_al_diagrama(diagram, c_p6, 515, -505, 945, -555, sequence=seq_gen.next_comp())

        note_be = target_pkg.Elements.AddNew("", "Note")
        note_be.Notes = "<b>Servicio Nativo Systemd (fashionstore-p2-api):</b>\n• Presupuesto: MemoryMax 512 MB · CPUQuota 75% · 1 Hilo Numérico\n• Deploy Automatizado vía SSH/SCP · Auto-Restart ante Fallos"
        note_be.ParentID = env_be.ElementID
        note_be.Update()
        agregar_al_diagrama(diagram, note_be, 515, -570, 945, -680, sequence=seq_gen.next_comp())

        print("[3/8] Construyendo Nodo 3: Servidor Web Frontend (Angular 20 PWA / Nginx)...")
        # 3. NODO FRONTEND (Top-Right: left=1020, top=-100, right=1460, bottom=-380)
        n_fe = crear_elemento(target_pkg, "Node", "«cloud»\nServidor Web Frontend & Reverse Proxy\n(Nginx 1.26+ · Cloudflared Tunnel)", "", C_BLUE)
        agregar_al_diagrama(diagram, n_fe, 1020, -100, 1460, -380, sequence=seq_gen.next_node())

        env_fe = crear_sub_elemento(n_fe, "ExecutionEnvironment", "Nginx Web Server & Edge Connector (Puerto 2468 / Cloudflare)", "executionEnvironment", C_PINK)
        agregar_al_diagrama(diagram, env_fe, 1040, -145, 1440, -360, sequence=seq_gen.next_env())

        c_fe1 = crear_sub_elemento(env_fe, "Component", "Portal Web FashionStore (Angular 20 Standalone / PWA)\nPanel Administrativo, Catálogo, Caja POS y Reportes", "web application", C_WHITE)
        agregar_al_diagrama(diagram, c_fe1, 1055, -170, 1425, -225, sequence=seq_gen.next_comp())

        c_fe2 = crear_sub_elemento(env_fe, "Component", "Módulo de Gestión Comercial y Clientes (Sprint 2)\nFichas de Clientes, Inventario, Reservas y Ventas", "component", C_WHITE)
        agregar_al_diagrama(diagram, c_fe2, 1055, -240, 1425, -295, sequence=seq_gen.next_comp())

        c_fe3 = crear_sub_elemento(env_fe, "Component", "Nginx Reverse Proxy & Cloudflare Tunnel (HTTPS 443)\nEnrutamiento /api/ -> 8002 · Entrega en fashionstore.aledevcv.me", "service", C_WHITE)
        agregar_al_diagrama(diagram, c_fe3, 1055, -310, 1425, -350, sequence=seq_gen.next_comp())

        print("[4/8] Construyendo Nodo 4: Servicios Cloud & IA Externos...")
        # 4. SERVICIOS CLOUD & IA (Mid-Right: left=1020, top=-410, right=1460, bottom=-720)
        n_ext = crear_elemento(target_pkg, "Node", "«IA y RA» / Servicios Cloud Externos\n(Google Gemini / Stripe / Decart / FCM / Cloudinary)", "", C_BLUE)
        agregar_al_diagrama(diagram, n_ext, 1020, -410, 1460, -720, sequence=seq_gen.next_node())

        ec1 = crear_sub_elemento(n_ext, "Component", "Cloudinary Media Storage\nAlmacenamiento y optimización de fotos", "storage", C_WHITE)
        agregar_al_diagrama(diagram, ec1, 1040, -460, 1230, -520, sequence=seq_gen.next_comp())

        ec2 = crear_sub_elemento(n_ext, "Component", "Google Gemini Pro / Flash API\nReportes generativos e intención estructurada", "ia & vision", C_WHITE)
        agregar_al_diagrama(diagram, ec2, 1250, -460, 1440, -520, sequence=seq_gen.next_comp())

        ec3 = crear_sub_elemento(n_ext, "Component", "Decart Virtual Try-On API (lucy-vton)\nVestidor virtual interactivo y prueba AR", "augmented reality", C_WHITE)
        agregar_al_diagrama(diagram, ec3, 1040, -535, 1230, -595, sequence=seq_gen.next_comp())

        ec4 = crear_sub_elemento(n_ext, "Component", "Firebase Cloud Messaging (FCM)\nNotificaciones push transaccionales móviles", "streaming & push", C_WHITE)
        agregar_al_diagrama(diagram, ec4, 1250, -535, 1440, -595, sequence=seq_gen.next_comp())

        ec5 = crear_sub_elemento(n_ext, "Component", "Pasarela Stripe (Modo Test) & Webhooks\nProcesamiento de pagos con tarjeta y firmas criptográficas", "pagos", C_WHITE)
        agregar_al_diagrama(diagram, ec5, 1040, -610, 1440, -700, sequence=seq_gen.next_comp())

        print("[5/8] Construyendo Nodos de Red: Internet y Switch...")
        # 5. RED: INTERNET Y SWITCH
        n_net = crear_elemento(target_pkg, "Node", "Internet\n(Cloudflare Global Network)", "", C_BLUE)
        agregar_al_diagrama(diagram, n_net, 280, -790, 460, -900, sequence=seq_gen.next_node())

        n_sw = crear_elemento(target_pkg, "Node", "Switch\n(Router Red / Wi-Fi / Fibra)", "", C_BLUE)
        agregar_al_diagrama(diagram, n_sw, 580, -790, 750, -900, sequence=seq_gen.next_node())

        print("[6/8] Construyendo Nodo 6: Computadora Empresa / Sucursal...")
        # 6. COMPUTADORA EMPRESA (left=1020, top=-760, right=1460, bottom=-980)
        n_pc = crear_elemento(target_pkg, "Device", "Computadora Empresa / Sucursal\n(Puesto de Trabajo Admin, Encargado y Cajero)", "device", C_PEACH)
        agregar_al_diagrama(diagram, n_pc, 1020, -760, 1460, -980, sequence=seq_gen.next_node())

        env_win = crear_sub_elemento(n_pc, "ExecutionEnvironment", "Windows 10 / 11 / macOS / Linux", "executionEnvironment", C_PINK)
        agregar_al_diagrama(diagram, env_win, 1040, -800, 1440, -965, sequence=seq_gen.next_env())

        c_angular = crear_sub_elemento(env_win, "Component", "Navegador Web (Angular 20 Standalone / TypeScript)\nPanel Admin, Caja POS, Inventario y Reportes IA", "web application", C_WHITE)
        agregar_al_diagrama(diagram, c_angular, 1055, -820, 1425, -875, sequence=seq_gen.next_comp())

        c_idb = crear_sub_elemento(env_win, "Component", "Almacén IndexedDB & Service Worker (PWA Offline)\nDexie.js para catálogo local, ventas y reservas offline", "database", C_WHITE)
        agregar_al_diagrama(diagram, c_idb, 1055, -890, 1425, -950, sequence=seq_gen.next_comp())

        print("[7/8] Construyendo Nodo 7: Dispositivo Móvil...")
        # 7. DISPOSITIVO MOVIL (left=1020, top=-1010, right=1460, bottom=-1250)
        n_mov = crear_elemento(target_pkg, "Device", "Dispositivo móvil\n(Smartphone del Cliente y Personal de Tienda)", "device", C_PEACH)
        agregar_al_diagrama(diagram, n_mov, 1020, -1010, 1460, -1250, sequence=seq_gen.next_node())

        env_and = crear_sub_elemento(n_mov, "ExecutionEnvironment", "Android 8.0+ / iOS 14.0+", "executionEnvironment", C_PINK)
        agregar_al_diagrama(diagram, env_and, 1040, -1050, 1440, -1235, sequence=seq_gen.next_env())

        c_flut = crear_sub_elemento(env_and, "Component", "Aplicación Móvil FashionStore (Flutter / Dart)\nCatálogo, Carrito, Reservas, Búsqueda por Voz y Vestidor AR", "mobile application", C_WHITE)
        agregar_al_diagrama(diagram, c_flut, 1055, -1065, 1425, -1115, sequence=seq_gen.next_comp())

        c_sql = crear_sub_elemento(env_and, "Component", "SQLite Database (Almacén Local / Cache Offline)\nsqflite para catálogo descargado y cola de sincronización", "database", C_WHITE)
        agregar_al_diagrama(diagram, c_sql, 1055, -1125, 1425, -1170, sequence=seq_gen.next_comp())

        c_sec = crear_sub_elemento(env_and, "Component", "Flutter Secure Storage (Tokens JWT)\nAlmacenamiento seguro de credenciales y claves de sesión", "security", C_WHITE)
        agregar_al_diagrama(diagram, c_sec, 1055, -1180, 1425, -1225, sequence=seq_gen.next_comp())

        print("[8/8] Construyendo Nodo 8: Computadora Atacante (Pentesting)...")
        # 8. COMPUTADORA ATACANTE (left=200, top=-980, right=780, bottom=-1230)
        n_kali = crear_elemento(target_pkg, "Device", "Computadora Atacante\n(Estación de Auditoría de Seguridad y Pentesting)", "device", C_PEACH)
        agregar_al_diagrama(diagram, n_kali, 200, -980, 780, -1230, sequence=seq_gen.next_node())

        env_kali = crear_sub_elemento(n_kali, "ExecutionEnvironment", "Kali Linux 2026.x (Auditoría de Seguridad y Pentesting)", "executionEnvironment", C_PINK)
        agregar_al_diagrama(diagram, env_kali, 220, -1025, 760, -1215, sequence=seq_gen.next_env())

        t1 = crear_sub_elemento(env_kali, "Component", "nmap\nEscaneo de Puertos y Detección de Servicios", "tool", C_WHITE)
        agregar_al_diagrama(diagram, t1, 235, -1045, 475, -1115, sequence=seq_gen.next_comp())

        t2 = crear_sub_elemento(env_kali, "Component", "OWASP ZAP / Burp Suite\nAnálisis de Vulnerabilidades Web y APIs REST", "tool", C_WHITE)
        agregar_al_diagrama(diagram, t2, 500, -1045, 740, -1115, sequence=seq_gen.next_comp())

        t3 = crear_sub_elemento(env_kali, "Component", "metasploit framework\nPruebas de Penetración de Endpoints y JWT", "tool", C_WHITE)
        agregar_al_diagrama(diagram, t3, 235, -1130, 475, -1200, sequence=seq_gen.next_comp())

        t4 = crear_sub_elemento(env_kali, "Component", "Hydra / John The Ripper\nPruebas de Fuerza Bruta y Hashes bcrypt", "tool", C_WHITE)
        agregar_al_diagrama(diagram, t4, 500, -1130, 740, -1200, sequence=seq_gen.next_comp())

        print("Creando Enlaces y Conectores de Comunicación con Multiplicidad...")
        # -------------------------------------------------------------
        # CONECTORES CON CARDINALIDADES (UML 2.5)
        # -------------------------------------------------------------
        crear_enlace(repo, diagram, n_db, n_be, "TCP/IP SSL (Puerto 5432)", "1", "1")
        crear_enlace(repo, diagram, n_be, n_fe, "HTTPS REST / Proxy (443 / 2468)", "1", "1")
        crear_enlace(repo, diagram, n_be, n_ext, "API HTTPS / REST (443)", "1", "1..*")
        crear_enlace(repo, diagram, n_be, n_net, "HTTPS 443 / WSS", "1", "1")
        crear_enlace(repo, diagram, n_net, n_sw, "TCP/IP", "1", "1")
        crear_enlace(repo, diagram, n_sw, n_pc, "Ethernet 100/1000 Mbps", "1", "*")
        crear_enlace(repo, diagram, n_sw, n_mov, "Wi-Fi / 4G / 5G", "1", "*")
        crear_enlace(repo, diagram, n_sw, n_kali, "TCP/IP", "1", "1")

        diagram.Update()
        repo.ReloadDiagram(diagram.DiagramID)
        target_pkg.Packages.Refresh()
        target_pkg.Update()

        # Guardar imagen del diagrama
        try:
            proj = repo.GetProjectInterface()
            proj.PutDiagramImageToFile(diagram.DiagramGUID, IMG_PATH, 1)
            print(f"[OK] Imagen del diagrama exportada a: {IMG_PATH}")
        except Exception as ex:
            print(f"Aviso al exportar imagen: {ex}")

        print("=" * 75)
        print("DIAGRAMA DE DESPLIEGUE GENERADO EXITOSAMENTE EN ENTERPRISE ARCHITECT!")
        print(f"Paquete: {target_pkg.Name}")
        print(f"Diagrama: {diagram.Name} (ID: {diagram.DiagramID})")
        print("=" * 75)

    finally:
        repo.CloseFile()
        repo.Exit()

if __name__ == "__main__":
    main()
