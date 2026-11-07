/*
 * ==============================================================================
 * PROYECTO: FashionStore (Plataforma SaaS Multitenant para Tiendas de Ropa)
 * MATERIA:  Sistemas de Información II (INF412 - Semestre 2/2026)
 * MODULO:   DIAGRAMA DE DESPLIEGUE (ARQUITECTURA FÍSICA) - 2DO PARCIAL (UML 2.5)
 * 
 * DIRECTRICES METODOLÓGICAS Y ARQUITECTÓNICAS (INGENIERA DE SI2 / UAGRM):
 *   1. Nodos Formales («node» y «device»):
 *      - Servidores modelados como Cubos 3D estándar («node») con nombre explícito del proveedor,
 *        entorno y SO (Servidor Host Debian 13 / Nginx / PostgreSQL 17 / Cloudflare).
 *      - Prohibido dejar "Servidor" genérico a secas.
 *   2. Contenedores y Entornos de Ejecución Reales («executionEnvironment»):
 *      - Debian 13 (Trixie) Linux Native Runtime, Android 8.0+/iOS 14+, Windows 10/11/macOS, Kali Linux.
 *   3. Artefactos y Componentes Internos del Proyecto FashionStore («component»):
 *      - Base de Datos: PostgreSQL 17.11 (+ PostGIS Extension) [Puerto 5432 SSL · Multi-Tenant con RLS].
 *      - Backend Web: FastAPI ASGI Core (Python 3.13) [Uvicorn 127.0.0.1:8002 · systemd].
 *      - Paquetes de Casos de Uso: P1 (SaaS/Auth), P2 (Catálogo), P3 (Inventario), P4 (POS/Reservas), P5 (Sync Offline), P6 (IA & ML).
 *      - Frontend Web: Angular 20 Standalone (SPA / PWA con Service Worker e IndexedDB Dexie.js).
 *      - Reverse Proxy & Tunnel: Nginx 1.26+ (Puerto 2468) + Cloudflared Tunnel (fashionstore.aledevcv.me).
 *      - App Móvil: FashionStore Mobile App (Flutter / Dart) con SQLite (sqflite) y Flutter Secure Storage.
 *      - Auditoría de Seguridad: Kali Linux con nmap, OWASP ZAP, Metasploit, Hydra, John the Ripper.
 *      - Servicios Cloud Externos: Google Gemini AI, Stripe (Modo Test), Decart VTON (AR), Firebase FCM, Cloudinary.
 *   4. Multiplicidad Explícita en Enlaces (1 a *):
 *      - Cumplimiento estricto de la regla de la ingeniera: Enlaces con '1' en servidor
 *        y '*' (muchos clientes concurrentes) en Dispositivos Móviles y Computadores Empresa.
 *   5. Protocolos de Comunicación sobre las Asociaciones:
 *      - TCP/IP SSL (5432), HTTPS REST / Proxy (443 / 2468), API HTTPS (443),
 *        Ethernet LAN 100/1000 Mbps, Wi-Fi / 4G / 5G, TCP/IP.
 *   6. Paleta Cromática Institucional (Formato BGR para Enterprise Architect):
 *      - Nodos Servidor / Red / Cloud: Azul pastel (#B4D7F5 -> BGR: 16111540).
 *      - Nodos Dispositivos de Cliente y Atacante: Crema / Melocotón pastel (#FFEBD7 -> BGR: 14150655).
 *      - Entornos de Ejecución: Rosa / Salmón suave (#FFCDCD -> BGR: 13499903).
 *      - Componentes y Artefactos: Blanco (#FFFFFF -> BGR: 16777215).
 *      - Notas Explicativas de Hardware: Gris suave (#F0F0F0 -> BGR: 15790320).
 * ==============================================================================
 */

// Paleta de Colores en formato BGR para Enterprise Architect
var C_BLUE   = 16111540; // RGB(180, 215, 245) - Nodos Servidor, Cloud, Internet, Switch
var C_PEACH  = 14150655; // RGB(255, 235, 215) - Nodos «device» Dispositivos Cliente y Atacante
var C_PINK   = 13499903; // RGB(255, 205, 205) - Entornos de Ejecución (OS / Containers / Runtimes)
var C_WHITE  = 16777215; // RGB(255, 255, 255) - Componentes y Módulos de Software
var C_NOTE   = 15790320; // RGB(240, 240, 240) - Notas explicativas de hardware

// Generador de Z-Order / Sequence para Enterprise Architect
// En EA: números menores están al frente (componentes) y mayores atrás (nodos contenedores)
var nodeSeq = 80;
var envSeq  = 50;
var compSeq = 1;

function getNextNodeSeq() { return nodeSeq++; }
function getNextEnvSeq()  { return envSeq++; }
function getNextCompSeq() { return compSeq++; }

function crearElemento(parentPkg, tipo, nombre, estereotipo, colorFondo) {
    var elem = parentPkg.Elements.AddNew(nombre, tipo);
    if (estereotipo && estereotipo.length > 0) {
        elem.Stereotype = estereotipo;
    }
    elem.Update();
    if (colorFondo) {
        try {
            elem.SetAppearance(1, colorFondo, 0);
            elem.Update();
        } catch(e) {}
    }
    return elem;
}

function crearSubElemento(parentElem, tipo, nombre, estereotipo, colorFondo) {
    var elem = parentElem.Elements.AddNew(nombre, tipo);
    if (estereotipo && estereotipo.length > 0) {
        elem.Stereotype = estereotipo;
    }
    elem.Update();
    if (colorFondo) {
        try {
            elem.SetAppearance(1, colorFondo, 0);
            elem.Update();
        } catch(e) {}
    }
    return elem;
}

function agregarAlDiagrama(diagram, elem, left, top, right, bottom, sequence) {
    var diagObj = diagram.DiagramObjects.AddNew("", "");
    diagObj.ElementID = elem.ElementID;
    diagObj.left = left;
    diagObj.top = top;
    diagObj.right = right;
    diagObj.bottom = bottom;
    if (sequence) {
        diagObj.Sequence = sequence;
    }
    diagObj.Update();
    return diagObj;
}

function crearEnlace(diagram, src, dst, label, cSrc, cDst) {
    var con = src.Connectors.AddNew(label, "Association");
    con.SupplierID = dst.ElementID;
    con.Update();
    try {
        Repository.Execute("UPDATE t_connector SET SourceCard = '" + cSrc + "', DestCard = '" + cDst + "' WHERE Connector_ID = " + con.ConnectorID);
    } catch(e) {}
    diagram.DiagramLinks.Refresh();
    return con;
}

function main() {
    Repository.EnsureOutputVisible("Script");
    Session.Output("=== INICIANDO GENERACIÓN DE DIAGRAMA DE DESPLIEGUE - FASHIONSTORE (PARCIAL 2) ===");

    var currentPackage = Repository.GetTreeSelectedPackage();
    if (currentPackage == null) {
        if (Repository.Models.Count > 0) {
            var rootModel = Repository.Models.GetAt(0);
            currentPackage = rootModel.Packages.Count > 0 ? rootModel.Packages.GetAt(0) : rootModel;
        }
    }
    if (currentPackage == null) {
        Session.Prompt("Por favor seleccione un Paquete en el Explorador de Proyectos antes de ejecutar.", 0);
        return;
    }

    var subPkg = currentPackage.Packages.AddNew("Diagrama de Despliegue - FashionStore (UML 2.5)", "");
    subPkg.Update();

    var diagram = subPkg.Diagrams.AddNew("Arquitectura Física de Despliegue - FashionStore", "Deployment");
    diagram.Update();

    // =========================================================================
    // 1. NODO: SERVIDOR BASE DE DATOS CENTRAL (PostgreSQL 17.11 / RLS)
    // =========================================================================
    Session.Output("[1/8] Construyendo Nodo Servidor Base de Datos Central...");
    var n_db = crearElemento(subPkg, "Node", "«cloud»\nServidor Base de Datos Central\n(PostgreSQL 17.11 · Host Linux Debian 13)", "", C_BLUE);
    agregarAlDiagrama(diagram, n_db, 50, -100, 440, -720, getNextNodeSeq());

    var env_db = crearSubElemento(n_db, "ExecutionEnvironment", "Managed Database Engine (PostgreSQL 17.11 Multi-Tenant VPC)", "executionEnvironment", C_PINK);
    agregarAlDiagrama(diagram, env_db, 70, -145, 420, -700, getNextEnvSeq());

    var c_db1 = crearSubElemento(env_db, "Component", "PostgreSQL 17.11 (+ PostGIS Extension)\nPuerto 5432 SSL · Multi-Tenant con RLS", "database", C_WHITE);
    agregarAlDiagrama(diagram, c_db1, 85, -170, 405, -235, getNextCompSeq());

    var c_db2 = crearSubElemento(env_db, "Component", "Motor Row Level Security (RLS) & Conexiones\nAislamiento lógico estricto por tenant_id", "service", C_WHITE);
    agregarAlDiagrama(diagram, c_db2, 85, -250, 405, -315, getNextCompSeq());

    var c_db3 = crearSubElemento(env_db, "Component", "Pool de Conexiones psycopg2 & Transacciones ACID\nGestión de concurrencia y atomicidad transaccional", "service", C_WHITE);
    agregarAlDiagrama(diagram, c_db3, 85, -330, 405, -395, getNextCompSeq());

    var c_db4 = crearSubElemento(env_db, "Component", "Almacén Local de Archivos y Comprobantes\nCustodia de respaldos, PDFs y assets en shared/files", "storage", C_WHITE);
    agregarAlDiagrama(diagram, c_db4, 85, -410, 405, -475, getNextCompSeq());

    var note_db = subPkg.Elements.AddNew("", "Note");
    note_db.Notes = "<b>Servidor Nativo Debian 13 (Trixie):</b>\n" +
                    "• Host Físico: 2 vCPU · 2 GB RAM · SSD NVMe\n" +
                    "• Base central: fashionstore_p2 en PostgreSQL 17\n" +
                    "• Cifrado AES-256 en Reposo · Backups PITR Diarios";
    note_db.ParentID = env_db.ElementID;
    note_db.Update();
    agregarAlDiagrama(diagram, note_db, 85, -490, 405, -680, getNextCompSeq());

    // =========================================================================
    // 2. NODO: SERVIDOR BACKEND CORE (FastAPI / Python 3.13 / Uvicorn)
    // =========================================================================
    Session.Output("[2/8] Construyendo Nodo Servidor Backend Core...");
    var n_be = crearElemento(subPkg, "Node", "«cloud»\nServidor Backend Core\n(FastAPI / Python 3.13 · Systemd Service · Uvicorn)", "", C_BLUE);
    agregarAlDiagrama(diagram, n_be, 480, -100, 980, -720, getNextNodeSeq());

    var env_be = crearSubElemento(n_be, "ExecutionEnvironment", "Linux Service Runtime (Python 3.13.5 Virtualenv / Systemd)", "executionEnvironment", C_PINK);
    agregarAlDiagrama(diagram, env_be, 500, -145, 960, -700, getNextEnvSeq());

    var c_be1 = crearSubElemento(env_be, "Component", "FastAPI ASGI Core & Router Hub (Python 3.13)\nUvicorn Worker 127.0.0.1:8002 · ASGI REST · HTTPS 443", "web", C_WHITE);
    agregarAlDiagrama(diagram, c_be1, 515, -170, 945, -230, getNextCompSeq());

    var c_p1 = crearSubElemento(env_be, "Component", "P1: Seguridad, SaaS y Cuentas Globales\n(Auth JWT, Roles, Empresas CU01-CU05)", "package", C_WHITE);
    agregarAlDiagrama(diagram, c_p1, 515, -245, 720, -295, getNextCompSeq());

    var c_p2 = crearSubElemento(env_be, "Component", "P2: Catálogo de Prendas y Clasificación\n(Variantes, Tallas, Colores CU06)", "package", C_WHITE);
    agregarAlDiagrama(diagram, c_p2, 740, -245, 945, -295, getNextCompSeq());

    var c_p3 = crearSubElemento(env_be, "Component", "P3: Inventario Multisucursal y Proveedores (Kardex, Compras, Alertas CU07-10)", "package", C_WHITE);
    agregarAlDiagrama(diagram, c_p3, 515, -310, 945, -360, getNextCompSeq());

    var c_p4 = crearSubElemento(env_be, "Component", "P4: Ventas POS, Carrito y Reservas (Checkout, Transacciones ACID, Retención 24h CU11-13)", "package", C_WHITE);
    agregarAlDiagrama(diagram, c_p4, 515, -375, 945, -425, getNextCompSeq());

    var c_p5 = crearSubElemento(env_be, "Component", "P5: Sincronización Offline & Resiliencia (PWA / Mobile Sync, Resolución Conflictos CU16)", "package", C_WHITE);
    agregarAlDiagrama(diagram, c_p5, 515, -440, 945, -490, getNextCompSeq());

    var c_p6 = crearSubElemento(env_be, "Component", "P6: Inteligencia Artificial & Modelos ML (Demanda, K-Means, Reportes Generativos CU17-18)", "package", C_WHITE);
    agregarAlDiagrama(diagram, c_p6, 515, -505, 945, -555, getNextCompSeq());

    var note_be = subPkg.Elements.AddNew("", "Note");
    note_be.Notes = "<b>Servicio Nativo Systemd (fashionstore-p2-api):</b>\n" +
                    "• Presupuesto: MemoryMax 512 MB · CPUQuota 75% · 1 Hilo Numérico\n" +
                    "• Deploy Automatizado vía SSH/SCP · Auto-Restart ante Fallos";
    note_be.ParentID = env_be.ElementID;
    note_be.Update();
    agregarAlDiagrama(diagram, note_be, 515, -570, 945, -680, getNextCompSeq());

    // =========================================================================
    // 3. NODO: SERVIDOR WEB FRONTEND (Angular 20 Standalone / PWA / Nginx)
    // =========================================================================
    Session.Output("[3/8] Construyendo Nodo Servidor Web Frontend...");
    var n_fe = crearElemento(subPkg, "Node", "«cloud»\nServidor Web Frontend & Reverse Proxy\n(Nginx 1.26+ · Cloudflared Tunnel)", "", C_BLUE);
    agregarAlDiagrama(diagram, n_fe, 1020, -100, 1460, -380, getNextNodeSeq());

    var env_fe = crearSubElemento(n_fe, "ExecutionEnvironment", "Nginx Web Server & Edge Connector (Puerto 2468 / Cloudflare)", "executionEnvironment", C_PINK);
    agregarAlDiagrama(diagram, env_fe, 1040, -145, 1440, -360, getNextEnvSeq());

    var c_fe1 = crearSubElemento(env_fe, "Component", "Portal Web FashionStore (Angular 20 Standalone / PWA)\nPanel Administrativo, Catálogo, Caja POS y Reportes", "web application", C_WHITE);
    agregarAlDiagrama(diagram, c_fe1, 1055, -170, 1425, -225, getNextCompSeq());

    var c_fe2 = crearSubElemento(env_fe, "Component", "Módulo de Gestión Comercial y Clientes (Sprint 2)\nFichas de Clientes, Inventario, Reservas y Ventas", "component", C_WHITE);
    agregarAlDiagrama(diagram, c_fe2, 1055, -240, 1425, -295, getNextCompSeq());

    var c_fe3 = crearSubElemento(env_fe, "Component", "Nginx Reverse Proxy & Cloudflare Tunnel (HTTPS 443)\nEnrutamiento /api/ -> 8002 · Entrega en fashionstore.aledevcv.me", "service", C_WHITE);
    agregarAlDiagrama(diagram, c_fe3, 1055, -310, 1425, -350, getNextCompSeq());

    // =========================================================================
    // 4. NODO: «IA y RA» / SERVICIOS CLOUD EXTERNOS
    // =========================================================================
    Session.Output("[4/8] Construyendo Nodo Servicios Cloud e IA Externos...");
    var n_ext = crearElemento(subPkg, "Node", "«IA y RA» / Servicios Cloud Externos\n(Google Gemini / Stripe / Decart / FCM / Cloudinary)", "", C_BLUE);
    agregarAlDiagrama(diagram, n_ext, 1020, -410, 1460, -720, getNextNodeSeq());

    var ec1 = crearSubElemento(n_ext, "Component", "Cloudinary Media Storage\nAlmacenamiento y optimización de fotos", "storage", C_WHITE);
    agregarAlDiagrama(diagram, ec1, 1040, -460, 1230, -520, getNextCompSeq());

    var ec2 = crearSubElemento(n_ext, "Component", "Google Gemini Pro / Flash API\nReportes generativos e intención estructurada", "ia & vision", C_WHITE);
    agregarAlDiagrama(diagram, ec2, 1250, -460, 1440, -520, getNextCompSeq());

    var ec3 = crearSubElemento(n_ext, "Component", "Decart Virtual Try-On API (lucy-vton)\nVestidor virtual interactivo y prueba AR", "augmented reality", C_WHITE);
    agregarAlDiagrama(diagram, ec3, 1040, -535, 1230, -595, getNextCompSeq());

    var ec4 = crearSubElemento(n_ext, "Component", "Firebase Cloud Messaging (FCM)\nNotificaciones push transaccionales móviles", "streaming & push", C_WHITE);
    agregarAlDiagrama(diagram, ec4, 1250, -535, 1440, -595, getNextCompSeq());

    var ec5 = crearSubElemento(n_ext, "Component", "Pasarela Stripe (Modo Test) & Webhooks\nProcesamiento de pagos con tarjeta y firmas criptográficas", "pagos", C_WHITE);
    agregarAlDiagrama(diagram, ec5, 1040, -610, 1440, -700, getNextCompSeq());

    // =========================================================================
    // 5. NODOS DE RED: INTERNET Y SWITCH
    // =========================================================================
    Session.Output("[5/8] Construyendo Nodos de Red (Internet y Switch)...");
    var n_net = crearElemento(subPkg, "Node", "Internet\n(Cloudflare Global Network)", "", C_BLUE);
    agregarAlDiagrama(diagram, n_net, 280, -790, 460, -900, getNextNodeSeq());

    var n_sw = crearElemento(subPkg, "Node", "Switch\n(Router Red / Wi-Fi / Fibra)", "", C_BLUE);
    agregarAlDiagrama(diagram, n_sw, 580, -790, 750, -900, getNextNodeSeq());

    // =========================================================================
    // 6. DISPOSITIVO: COMPUTADORA EMPRESA / SUCURSAL (ADMIN, ENCARGADO, CAJERO)
    // =========================================================================
    Session.Output("[6/8] Construyendo Nodo Computadora Empresa / Sucursal...");
    var n_pc = crearElemento(subPkg, "Device", "Computadora Empresa / Sucursal\n(Puesto de Trabajo Admin, Encargado y Cajero)", "device", C_PEACH);
    agregarAlDiagrama(diagram, n_pc, 1020, -760, 1460, -980, getNextNodeSeq());

    var env_win = crearSubElemento(n_pc, "ExecutionEnvironment", "Windows 10 / 11 / macOS / Linux", "executionEnvironment", C_PINK);
    agregarAlDiagrama(diagram, env_win, 1040, -800, 1440, -965, getNextEnvSeq());

    var c_angular = crearSubElemento(env_win, "Component", "Navegador Web (Angular 20 Standalone / TypeScript)\nPanel Admin, Caja POS, Inventario y Reportes IA", "web application", C_WHITE);
    agregarAlDiagrama(diagram, c_angular, 1055, -820, 1425, -875, getNextCompSeq());

    var c_idb = crearSubElemento(env_win, "Component", "Almacén IndexedDB & Service Worker (PWA Offline)\nDexie.js para catálogo local, ventas y reservas offline", "database", C_WHITE);
    agregarAlDiagrama(diagram, c_idb, 1055, -890, 1425, -950, getNextCompSeq());

    // =========================================================================
    // 7. DISPOSITIVO: DISPOSITIVO MÓVIL (CLIENTE Y PERSONAL DE TIENDA)
    // =========================================================================
    Session.Output("[7/8] Construyendo Nodo Dispositivo Móvil...");
    var n_mov = crearElemento(subPkg, "Device", "Dispositivo móvil\n(Smartphone del Cliente y Personal de Tienda)", "device", C_PEACH);
    agregarAlDiagrama(diagram, n_mov, 1020, -1010, 1460, -1250, getNextNodeSeq());

    var env_and = crearSubElemento(n_mov, "ExecutionEnvironment", "Android 8.0+ / iOS 14.0+", "executionEnvironment", C_PINK);
    agregarAlDiagrama(diagram, env_and, 1040, -1050, 1440, -1235, getNextEnvSeq());

    var c_flut = crearSubElemento(env_and, "Component", "Aplicación Móvil FashionStore (Flutter / Dart)\nCatálogo, Carrito, Reservas, Búsqueda por Voz y Vestidor AR", "mobile application", C_WHITE);
    agregarAlDiagrama(diagram, c_flut, 1055, -1065, 1425, -1115, getNextCompSeq());

    var c_sql = crearSubElemento(env_and, "Component", "SQLite Database (Almacén Local / Cache Offline)\nsqflite para catálogo descargado y cola de sincronización", "database", C_WHITE);
    agregarAlDiagrama(diagram, c_sql, 1055, -1125, 1425, -1170, getNextCompSeq());

    var c_sec = crearSubElemento(env_and, "Component", "Flutter Secure Storage (Tokens JWT)\nAlmacenamiento seguro de credenciales y claves de sesión", "security", C_WHITE);
    agregarAlDiagrama(diagram, c_sec, 1055, -1180, 1425, -1225, getNextCompSeq());

    // =========================================================================
    // 8. DISPOSITIVO: COMPUTADORA ATACANTE (PENTESTING Y AUDITORÍA DE SEGURIDAD)
    // =========================================================================
    Session.Output("[8/8] Construyendo Nodo Computadora Atacante...");
    var n_kali = crearElemento(subPkg, "Device", "Computadora Atacante\n(Estación de Auditoría de Seguridad y Pentesting)", "device", C_PEACH);
    agregarAlDiagrama(diagram, n_kali, 200, -980, 780, -1230, getNextNodeSeq());

    var env_kali = crearSubElemento(n_kali, "ExecutionEnvironment", "Kali Linux 2026.x (Auditoría de Seguridad y Pentesting)", "executionEnvironment", C_PINK);
    agregarAlDiagrama(diagram, env_kali, 220, -1025, 760, -1215, getNextEnvSeq());

    var t1 = crearSubElemento(env_kali, "Component", "nmap\nEscaneo de Puertos y Detección de Servicios", "tool", C_WHITE);
    agregarAlDiagrama(diagram, t1, 235, -1045, 475, -1115, getNextCompSeq());

    var t2 = crearSubElemento(env_kali, "Component", "OWASP ZAP / Burp Suite\nAnálisis de Vulnerabilidades Web y APIs REST", "tool", C_WHITE);
    agregarAlDiagrama(diagram, t2, 500, -1045, 740, -1115, getNextCompSeq());

    var t3 = crearSubElemento(env_kali, "Component", "metasploit framework\nPruebas de Penetración de Endpoints y JWT", "tool", C_WHITE);
    agregarAlDiagrama(diagram, t3, 235, -1130, 475, -1200, getNextCompSeq());

    var t4 = crearSubElemento(env_kali, "Component", "Hydra / John The Ripper\nPruebas de Fuerza Bruta y Hashes bcrypt", "tool", C_WHITE);
    agregarAlDiagrama(diagram, t4, 500, -1130, 740, -1200, getNextCompSeq());

    // =========================================================================
    // 9. CONECTORES Y ASOCIACIONES CON PROTOCOLOS Y MULTIPLICIDAD (UML 2.5)
    // =========================================================================
    Session.Output("Trazando conectores de comunicación con multiplicidades 1 a *...");
    crearEnlace(diagram, n_db, n_be, "TCP/IP SSL (Puerto 5432)", "1", "1");
    crearEnlace(diagram, n_be, n_fe, "HTTPS REST / Proxy (443 / 2468)", "1", "1");
    crearEnlace(diagram, n_be, n_ext, "API HTTPS / REST (443)", "1", "1..*");
    crearEnlace(diagram, n_be, n_net, "HTTPS 443 / WSS", "1", "1");
    crearEnlace(diagram, n_net, n_sw, "TCP/IP", "1", "1");
    crearEnlace(diagram, n_sw, n_pc, "Ethernet 100/1000 Mbps", "1", "*");
    crearEnlace(diagram, n_sw, n_mov, "Wi-Fi / 4G / 5G", "1", "*");
    crearEnlace(diagram, n_sw, n_kali, "TCP/IP", "1", "1");

    diagram.Update();
    Repository.ReloadDiagram(diagram.DiagramID);
    currentPackage.Packages.Refresh();

    Session.Output("=== DIAGRAMA DE DESPLIEGUE GENERADO CON ÉXITO ===");
    Session.Prompt("Diagrama de Despliegue de FashionStore generado exitosamente en el paquete: " + subPkg.Name, 0);
}

main();
