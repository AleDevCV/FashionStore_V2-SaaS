-- =====================================================
-- FashionStore - Script de base de datos (PostgreSQL)
-- =====================================================
-- =============================================================================
-- SISTEMA DE INFORMACIÓN II - PARCIAL 1
-- PROYECTO: FASHIONSTORE
-- MOTOR DE BASE DE DATOS: PostgreSQL 16+
-- AUTOR: Grupo de Desarrollo de Sistemas II
-- DESCRIPCIÓN: Script de creación física e inicialización (Seeders) de la base de datos
--              diseñada de manera modular y extensible bajo la metodología PUDS.
-- =============================================================================

-- Habilitar extensión para UUIDs en caso de que se requiera en el futuro
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- 1. ELIMINACIÓN DE TABLAS (En orden inverso de dependencia para desarrollo limpio)
-- =============================================================================
DROP TABLE IF EXISTS bitacora CASCADE;
DROP TABLE IF EXISTS comprobante CASCADE;
DROP TABLE IF EXISTS pago_transaccion CASCADE;
DROP TABLE IF EXISTS detalle_venta CASCADE;
DROP TABLE IF EXISTS venta CASCADE;
DROP TABLE IF EXISTS detalle_reserva CASCADE;
DROP TABLE IF EXISTS reserva CASCADE;
DROP TABLE IF EXISTS detalle_compra CASCADE;
DROP TABLE IF EXISTS compra CASCADE;
DROP TABLE IF EXISTS movimiento_inventario CASCADE;
DROP TABLE IF EXISTS inventario CASCADE;
DROP TABLE IF EXISTS proveedor CASCADE;
DROP TABLE IF EXISTS imagen_prenda CASCADE;
DROP TABLE IF EXISTS variante_prenda CASCADE;
DROP TABLE IF EXISTS prenda CASCADE;
DROP TABLE IF EXISTS categoria CASCADE;
DROP TABLE IF EXISTS temporada CASCADE;
DROP TABLE IF EXISTS color CASCADE;
DROP TABLE IF EXISTS talla CASCADE;
DROP TABLE IF EXISTS sucursal CASCADE;
DROP TABLE IF EXISTS ciudad CASCADE;
DROP TABLE IF EXISTS cliente CASCADE;
DROP TABLE IF EXISTS usuario_token CASCADE;
DROP TABLE IF EXISTS usuario CASCADE;
DROP TABLE IF EXISTS rol_permiso CASCADE;
DROP TABLE IF EXISTS permiso CASCADE;
DROP TABLE IF EXISTS rol CASCADE;

-- =============================================================================
-- 2. MÓDULO DE SEGURIDAD, ACCESOS Y ROLES (CU01, CU02, CU03, CU04)
-- =============================================================================

CREATE TABLE rol (
    id_rol SERIAL PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE,
    descripcion VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE permiso (
    id_permiso SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    codigo VARCHAR(100) NOT NULL UNIQUE, -- ej: "usuarios.ver", "roles.asignar"
    modulo VARCHAR(100),
    descripcion VARCHAR(255)
);

CREATE TABLE rol_permiso (
    id_rol INT REFERENCES rol(id_rol) ON DELETE CASCADE,
    id_permiso INT REFERENCES permiso(id_permiso) ON DELETE CASCADE,
    PRIMARY KEY (id_rol, id_permiso)
);

CREATE TABLE usuario (
    id_usuario SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    correo VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL, -- Almacenará el hash bcrypt de FastAPI
    telefono VARCHAR(20),
    estado VARCHAR(20) DEFAULT 'Activo' CHECK (estado IN ('Activo', 'Inactivo')),
    id_role INT REFERENCES rol(id_rol) ON DELETE RESTRICT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla para tokens de recuperación de contraseñas de acceso o JWT revocados (CU04)
CREATE TABLE usuario_token (
    id_token SERIAL PRIMARY KEY,
    id_usuario INT REFERENCES usuario(id_usuario) ON DELETE CASCADE,
    token_recuperacion VARCHAR(255),
    expiracion TIMESTAMP,
    usado BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_usuario_token_recuperacion ON usuario_token(token_recuperacion);
CREATE INDEX IF NOT EXISTS idx_usuario_token_id_usuario ON usuario_token(id_usuario);
CREATE INDEX IF NOT EXISTS idx_usuario_token_usuario_usado ON usuario_token(id_usuario, usado);

-- =============================================================================
-- 3. MÓDULO GEOGRÁFICO Y ORGANIZACIONAL (CU06)
-- =============================================================================

CREATE TABLE ciudad (
    id_ciudad SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE sucursal (
    id_sucursal SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    direccion VARCHAR(255) NOT NULL,
    telefono VARCHAR(20),
    id_ciudad INT REFERENCES ciudad(id_ciudad) ON DELETE RESTRICT,
    id_encargado INT REFERENCES usuario(id_usuario) ON DELETE SET NULL, -- Encargado (CU02)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- 4. MÓDULO DE CLIENTES (CU05)
-- =============================================================================

CREATE TABLE cliente (
    id_cliente SERIAL PRIMARY KEY,
    ci VARCHAR(20) NOT NULL UNIQUE,
    nombre_completo VARCHAR(200) NOT NULL,
    telefono VARCHAR(20),
    correo VARCHAR(150) UNIQUE,
    direccion_envio VARCHAR(255),
    estado VARCHAR(20) DEFAULT 'Activo' CHECK (estado IN ('Activo', 'Inactivo')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- 5. MÓDULO DE CATÁLOGO DE ROPA Y VARIANTES MULTIVALUADAS (CU07, CU08, CU09)
-- =============================================================================

CREATE TABLE temporada (
    id_temporada SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE, -- ej: "Primavera-Verano 2026", "Invierno"
    descripcion VARCHAR(255),
    fecha_inicio DATE,
    fecha_fin DATE
);

CREATE TABLE categoria (
    id_categoria SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    descripcion VARCHAR(255),
    id_categoria_padre INT REFERENCES categoria(id_categoria) ON DELETE SET NULL, -- Jerarquía recursiva
    estado VARCHAR(20) DEFAULT 'Activo' CHECK (estado IN ('Activo', 'Inactivo')) -- Baja lógica (CU07)
);

CREATE TABLE talla (
    id_talla SERIAL PRIMARY KEY,
    nombre VARCHAR(10) NOT NULL UNIQUE, -- ej: "S", "M", "L", "XL", "38", "40"
    descripcion VARCHAR(50)
);

CREATE TABLE color (
    id_color SERIAL PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE, -- ej: "Azul Marino", "Negro Mate"
    codigo_hex VARCHAR(10) -- ej: "#000080"
);

CREATE TABLE prenda (
    id_prenda SERIAL PRIMARY KEY,
    sku VARCHAR(50) NOT NULL UNIQUE, -- SKU maestro del diseño de prenda
    nombre VARCHAR(150) NOT NULL,
    descripcion TEXT,
    marca VARCHAR(100) DEFAULT 'FashionStore',
    genero VARCHAR(20) DEFAULT 'Unisex' CHECK (genero IN ('Dama', 'Caballero', 'Unisex', 'Nino')), -- Filtro del catálogo (CU08, CU14)
    precio_base DECIMAL(10, 2) NOT NULL CHECK (precio_base >= 0),
    id_categoria INT REFERENCES categoria(id_categoria) ON DELETE RESTRICT,
    id_temporada INT REFERENCES temporada(id_temporada) ON DELETE SET NULL,
    estado VARCHAR(20) DEFAULT 'Activo' CHECK (estado IN ('Activo', 'Inactivo', 'Borrador')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Variante física de la prenda (La combinación única de Prenda + Talla + Color)
CREATE TABLE variante_prenda (
    id_variante_prenda SERIAL PRIMARY KEY,
    id_prenda INT REFERENCES prenda(id_prenda) ON DELETE CASCADE,
    id_talla INT REFERENCES talla(id_talla) ON DELETE RESTRICT,
    id_color INT REFERENCES color(id_color) ON DELETE RESTRICT,
    sku_variante VARCHAR(100) NOT NULL UNIQUE, -- Código de barras o SKU único de variante física
    precio_adicional DECIMAL(10, 2) DEFAULT 0.00, -- Por si una talla XL o color especial cuesta más
    UNIQUE (id_prenda, id_talla, id_color)
);

CREATE TABLE imagen_prenda (
    id_imagen SERIAL PRIMARY KEY,
    id_prenda INT REFERENCES prenda(id_prenda) ON DELETE CASCADE,
    url_imagen VARCHAR(255) NOT NULL,
    es_principal BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- 6. MÓDULO DE INVENTARIO Y MOVIMIENTOS (CU10, CU11, CU12, CU13)
-- =============================================================================

CREATE TABLE proveedor (
    id_proveedor SERIAL PRIMARY KEY,
    nit VARCHAR(30) NOT NULL UNIQUE,
    razon_social VARCHAR(150) NOT NULL,
    contacto VARCHAR(100),
    telefono VARCHAR(20),
    correo VARCHAR(150),
    direccion VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de existencias multisucursal en tiempo real
CREATE TABLE inventario (
    id_sucursal INT REFERENCES sucursal(id_sucursal) ON DELETE RESTRICT,
    id_variante_prenda INT REFERENCES variante_prenda(id_variante_prenda) ON DELETE RESTRICT,
    stock INT NOT NULL DEFAULT 0 CHECK (stock >= 0),
    PRIMARY KEY (id_sucursal, id_variante_prenda)
);

CREATE TABLE movimiento_inventario (
    id_movimiento SERIAL PRIMARY KEY,
    id_sucursal INT REFERENCES sucursal(id_sucursal) ON DELETE RESTRICT,
    id_variante_prenda INT REFERENCES variante_prenda(id_variante_prenda) ON DELETE RESTRICT,
    tipo VARCHAR(20) NOT NULL CHECK (tipo IN ('Entrada', 'Salida', 'Traspaso')),
    cantidad INT NOT NULL CHECK (cantidad > 0),
    motivo VARCHAR(255) NOT NULL, -- ej: "Adquisición por compra", "Ajuste manual", "Reserva cancelada"
    id_usuario INT REFERENCES usuario(id_usuario) ON DELETE RESTRICT, -- Quién realizó el movimiento
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Registro de compras/adquisiciones a proveedores para stock físico (CU13)
CREATE TABLE compra (
    id_compra SERIAL PRIMARY KEY,
    id_proveedor INT REFERENCES proveedor(id_proveedor) ON DELETE RESTRICT,
    id_sucursal INT REFERENCES sucursal(id_sucursal) ON DELETE RESTRICT,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    id_usuario INT REFERENCES usuario(id_usuario) ON DELETE RESTRICT
);

CREATE TABLE detalle_compra (
    id_compra INT REFERENCES compra(id_compra) ON DELETE CASCADE,
    id_variante_prenda INT REFERENCES variante_prenda(id_variante_prenda) ON DELETE RESTRICT,
    cantidad INT NOT NULL CHECK (cantidad > 0),
    costo_unitario DECIMAL(10, 2) NOT NULL CHECK (costo_unitario >= 0),
    PRIMARY KEY (id_compra, id_variante_prenda)
);

-- =============================================================================
-- 7. MÓDULO DE RESERVAS (APARTADOS EN LÍNEA) (CU16, CU17)
-- =============================================================================

CREATE TABLE reserva (
    id_reserva SERIAL PRIMARY KEY,
    id_cliente INT REFERENCES cliente(id_cliente) ON DELETE RESTRICT,
    id_sucursal INT REFERENCES sucursal(id_sucursal) ON DELETE RESTRICT,
    fecha_reserva TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_limite TIMESTAMP NOT NULL, -- 48 horas de vigencia por política de FashionStore
    estado VARCHAR(30) DEFAULT 'Pendiente' CHECK (estado IN ('Pendiente', 'Preparado', 'Atendido', 'Cancelado')),
    total DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE detalle_reserva (
    id_reserva INT REFERENCES reserva(id_reserva) ON DELETE CASCADE,
    id_variante_prenda INT REFERENCES variante_prenda(id_variante_prenda) ON DELETE RESTRICT,
    cantidad INT NOT NULL DEFAULT 1 CHECK (cantidad > 0),
    precio_unitario DECIMAL(10, 2) NOT NULL,
    PRIMARY KEY (id_reserva, id_variante_prenda)
);

-- =============================================================================
-- 8. MÓDULO DE VENTAS (CAJA POS Y E-COMMERCE) (CU15, CU19, CU20, CU21)
-- =============================================================================

CREATE TABLE venta (
    id_venta SERIAL PRIMARY KEY,
    id_cliente INT REFERENCES cliente(id_cliente) ON DELETE RESTRICT,
    id_sucursal INT REFERENCES sucursal(id_sucursal) ON DELETE RESTRICT,
    id_cajero INT REFERENCES usuario(id_usuario) ON DELETE RESTRICT, -- Cajero que atiende
    id_reserva INT REFERENCES reserva(id_reserva) ON DELETE SET NULL, -- Si la venta proviene de una reserva previa
    tipo_venta VARCHAR(20) NOT NULL CHECK (tipo_venta IN ('Presencial', 'Online')),
    metodo_pago VARCHAR(30) NOT NULL CHECK (metodo_pago IN ('Efectivo', 'Tarjeta', 'QR', 'Transferencia')),
    subtotal DECIMAL(10, 2) NOT NULL,
    descuento DECIMAL(10, 2) DEFAULT 0.00,
    total DECIMAL(10, 2) NOT NULL,
    fecha_venta TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE detalle_venta (
    id_venta INT REFERENCES venta(id_venta) ON DELETE CASCADE,
    id_variante_prenda INT REFERENCES variante_prenda(id_variante_prenda) ON DELETE RESTRICT,
    cantidad INT NOT NULL CHECK (cantidad > 0),
    precio_unitario DECIMAL(10, 2) NOT NULL,
    subtotal DECIMAL(10, 2) NOT NULL,
    PRIMARY KEY (id_venta, id_variante_prenda)
);

-- Tabla de log de confirmaciones transaccionales de pasarelas Stripe/PayPal/Libélula (CU20)
CREATE TABLE pago_transaccion (
    id_pago SERIAL PRIMARY KEY,
    id_venta INT REFERENCES venta(id_venta) ON DELETE CASCADE,
    pasarela VARCHAR(50) NOT NULL, -- "Stripe", "PayPal", "Libelula"
    transaccion_id VARCHAR(100) NOT NULL UNIQUE, -- ID devuelto por el Webhook de la API de pagos
    monto DECIMAL(10, 2) NOT NULL,
    estado_pago VARCHAR(50) NOT NULL, -- "succeeded", "failed", "pending"
    payload_respuesta JSONB, -- Estructura de respuesta de la pasarela para auditoría
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Facturación o Notas de Venta (CU21)
CREATE TABLE comprobante (
    id_comprobante SERIAL PRIMARY KEY,
    id_venta INT REFERENCES venta(id_venta) ON DELETE CASCADE,
    numero_comprobante VARCHAR(50) NOT NULL UNIQUE, -- Formato: FAC-0001 / NOT-0001
    nit_ci VARCHAR(20) NOT NULL,
    razon_social VARCHAR(150) NOT NULL,
    fecha_emision TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    url_pdf VARCHAR(255) -- Almacenará la ruta física o S3 del comprobante generado
);

-- =============================================================================
-- 9. AUDITORÍA GENERAL DE OPERACIONES (CU25)
-- =============================================================================

CREATE TABLE bitacora (
    id_bitacora SERIAL PRIMARY KEY,
    id_usuario INT REFERENCES usuario(id_usuario) ON DELETE SET NULL, -- Quién operó (null si es visitante)
    accion VARCHAR(100) NOT NULL, -- ej: "INSERT", "UPDATE", "DELETE", "LOGIN"
    tabla_afectada VARCHAR(100) NOT NULL,
    registro_id INT,
    detalle TEXT, -- JSON o cadena describiendo los cambios realizados para auditorías
    ip_address VARCHAR(45),
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- 10. DISPARADORES (TRIGGERS) PARA AUTOMATIZACIÓN DE INVENTARIO
-- =============================================================================

-- A) Trigger para actualizar el stock automáticamente al registrar movimientos de inventario
CREATE OR REPLACE FUNCTION actualizar_stock_por_movimiento()
RETURNS TRIGGER AS $$
BEGIN
    -- Verificar si existe el registro de inventario en la sucursal, si no, lo crea con stock 0
    INSERT INTO inventario (id_sucursal, id_variante_prenda, stock)
    VALUES (NEW.id_sucursal, NEW.id_variante_prenda, 0)
    ON CONFLICT (id_sucursal, id_variante_prenda) DO NOTHING;

    -- Aplicar suma o resta al stock físico según el tipo de movimiento
    IF NEW.tipo = 'Entrada' THEN
        UPDATE inventario
        SET stock = stock + NEW.cantidad
        WHERE id_sucursal = NEW.id_sucursal AND id_variante_prenda = NEW.id_variante_prenda;
    ELSIF NEW.tipo = 'Salida' THEN
        -- Validar stock suficiente
        IF (SELECT stock FROM inventario WHERE id_sucursal = NEW.id_sucursal AND id_variante_prenda = NEW.id_variante_prenda) < NEW.cantidad THEN
            RAISE EXCEPTION 'Stock insuficiente en la sucursal para realizar este movimiento.';
        END IF;

        UPDATE inventario
        SET stock = stock - NEW.cantidad
        WHERE id_sucursal = NEW.id_sucursal AND id_variante_prenda = NEW.id_variante_prenda;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_movimiento_inventario
AFTER INSERT ON movimiento_inventario
FOR EACH ROW
EXECUTE FUNCTION actualizar_stock_por_movimiento();


-- B) Trigger para registrar en bitácora automáticamente los accesos a la base de datos (Ejemplo en tabla prendas)
CREATE OR REPLACE FUNCTION auditar_prendas()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'INSERT') THEN
        INSERT INTO bitacora (accion, tabla_afectada, registro_id, detalle)
        VALUES ('INSERT', 'prenda', NEW.id_prenda, 'Se registró una nueva prenda con SKU: ' || NEW.sku || ', Nombre: ' || NEW.nombre);
        RETURN NEW;
    ELSIF (TG_OP = 'UPDATE') THEN
        INSERT INTO bitacora (accion, tabla_afectada, registro_id, detalle)
        VALUES ('UPDATE', 'prenda', NEW.id_prenda, 'Se modificó la prenda. SKU anterior: ' || OLD.sku || ' -> SKU nuevo: ' || NEW.sku);
        RETURN NEW;
    ELSIF (TG_OP = 'DELETE') THEN
        INSERT INTO bitacora (accion, tabla_afectada, registro_id, detalle)
        VALUES ('DELETE', 'prenda', OLD.id_prenda, 'Se eliminó la prenda con SKU: ' || OLD.sku);
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_auditoria_prendas
AFTER INSERT OR UPDATE OR DELETE ON prenda
FOR EACH ROW
EXECUTE FUNCTION auditar_prendas();

-- =============================================================================
-- 11. DATOS SEMILLA (SEEDERS - Para tener datos listos al levantar el Docker)
-- =============================================================================

-- Roles base del sistema
INSERT INTO rol (id_rol, nombre, descripcion) VALUES
(1, 'Administrador', 'Acceso total y administración de la plataforma'),
(2, 'Encargado de Sucursal', 'Gestión de existencias y preparación de reservas en su sucursal'),
(3, 'Cajero (POS)', 'Ventas presenciales en la caja física de sucursal'),
(4, 'Cliente', 'Consulta de catálogo, probador virtual y reserva en línea')
ON CONFLICT (id_rol) DO NOTHING;

-- Catálogo de permisos base agrupados por módulo (CU03)
INSERT INTO permiso (id_permiso, nombre, codigo, modulo, descripcion) VALUES
(1, 'Ver Usuarios', 'usuarios.ver', 'Usuarios', 'Permite listar y consultar detalles de usuarios'),
(2, 'Crear Usuarios', 'usuarios.crear', 'Usuarios', 'Permite registrar nuevas cuentas de usuario'),
(3, 'Editar Usuarios', 'usuarios.editar', 'Usuarios', 'Permite actualizar datos y estados de usuarios'),
(4, 'Inactivar Usuarios', 'usuarios.inactivar', 'Usuarios', 'Permite dar de baja lógica a usuarios'),
(5, 'Ver Roles y Permisos', 'roles.ver', 'Roles y Permisos', 'Permite consultar roles y la matriz de permisos'),
(6, 'Asignar Permisos a Roles', 'roles.asignar', 'Roles y Permisos', 'Permite modificar los permisos asociados a cada rol'),
(7, 'Ver Clientes', 'clientes.ver', 'Clientes', 'Permite listar y consultar fichas de clientes'),
(8, 'Crear Clientes', 'clientes.crear', 'Clientes', 'Permite registrar nuevos clientes'),
(9, 'Editar Clientes', 'clientes.editar', 'Clientes', 'Permite actualizar información de clientes'),
(10, 'Inactivar Clientes', 'clientes.inactivar', 'Clientes', 'Permite dar de baja lógica a clientes'),
(11, 'Ver Geografía', 'geografia.ver', 'Sucursales', 'Permite consultar ciudades y sucursales'),
(12, 'Gestionar Ciudades', 'ciudades.gestionar', 'Sucursales', 'Permite crear y modificar ciudades'),
(13, 'Gestionar Sucursales', 'sucursales.gestionar', 'Sucursales', 'Permite crear y actualizar sucursales'),
(14, 'Ver Categorías', 'categorias.ver', 'Catálogo', 'Permite consultar categorías del catálogo'),
(15, 'Gestionar Categorías', 'categorias.gestionar', 'Catálogo', 'Permite crear, actualizar y dar baja a categorías'),
(16, 'Ver Prendas', 'prendas.ver', 'Catálogo', 'Permite listar prendas del catálogo administrativo'),
(17, 'Gestionar Prendas', 'prendas.gestionar', 'Catálogo', 'Permite crear, modificar y eliminar prendas y variantes'),
(18, 'Realizar Ventas POS', 'pos.vender', 'Ventas/POS', 'Permite registrar ventas presenciales en caja física'),
(19, 'Ver Reportes de Ventas', 'ventas.ver', 'Ventas/POS', 'Permite consultar historial y reportes de ventas'),
(20, 'Ver Bitácora', 'bitacora.ver', 'Auditoría/Bitácora', 'Permite consultar registros inmutables de auditoría del sistema')
ON CONFLICT (id_permiso) DO NOTHING;

-- Asignación inicial de permisos a roles (CU03)
-- Administrador: todos los permisos
INSERT INTO rol_permiso (id_rol, id_permiso)
SELECT 1, id_permiso FROM permiso
ON CONFLICT (id_rol, id_permiso) DO NOTHING;

-- Encargado de Sucursal
INSERT INTO rol_permiso (id_rol, id_permiso)
SELECT 2, id_permiso FROM permiso WHERE codigo IN (
    'usuarios.ver', 'clientes.ver', 'geografia.ver', 'sucursales.gestionar',
    'categorias.ver', 'prendas.ver', 'prendas.gestionar', 'ventas.ver'
)
ON CONFLICT (id_rol, id_permiso) DO NOTHING;

-- Cajero (POS)
INSERT INTO rol_permiso (id_rol, id_permiso)
SELECT 3, id_permiso FROM permiso WHERE codigo IN (
    'clientes.ver', 'clientes.crear', 'prendas.ver', 'pos.vender'
)
ON CONFLICT (id_rol, id_permiso) DO NOTHING;

-- Ciudades iniciales de Bolivia
INSERT INTO ciudad (id_ciudad, nombre) VALUES
(1, 'Santa Cruz de la Sierra'),
(2, 'La Paz'),
(3, 'Cochabamba')
ON CONFLICT (id_ciudad) DO NOTHING;

-- Cuenta de Usuario Administrador por defecto para la primera defensa (CU01 / CU02)
-- Nota: La contraseña hash es un hash bcrypt correspondiente al texto 'admin123'
INSERT INTO usuario (id_usuario, nombre, apellido, correo, password_hash, telefono, estado, id_role) VALUES
(1, 'Alejandro', 'Sistemas', 'admin@fashionstore.com', '$2b$12$zZo3V7AI.OyS0Nr3B.46Rev0BJawpm/pc9jSjS4u5anr.uEAleZX6', '77712345', 'Activo', 1)
ON CONFLICT (id_usuario) DO NOTHING;

-- Sucursales de prueba
INSERT INTO sucursal (id_sucursal, nombre, direccion, telefono, id_ciudad, id_encargado) VALUES
(1, 'Sucursal Equipetrol', 'Av. San Martín, Calle 8 Este #45', '3345678', 1, 1),
(2, 'Sucursal Centro', 'Calle Junín #123, Frente a la Plaza Principal', '3367890', 1, NULL)
ON CONFLICT (id_sucursal) DO NOTHING;

-- Categorías del Catálogo de ropa (CU07)
INSERT INTO categoria (id_categoria, nombre, descripcion, id_categoria_padre) VALUES
(1, 'Damas', 'Prendas de vestir y accesorios para mujeres', NULL),
(2, 'Caballeros', 'Prendas de vestir y accesorios para hombres', NULL),
(3, 'Blusas', 'Blusas de gasa, algodón y lino', 1),
(4, 'Camisas', 'Camisas formales y casuales', 2),
(5, 'Jeans', 'Pantalones de mezclilla de corte clásico y moderno', 1)
ON CONFLICT (id_categoria) DO NOTHING;

-- Tallas estandarizadas de prendas de vestir
INSERT INTO talla (id_talla, nombre, descripcion) VALUES
(1, 'S', 'Talla Pequeña (Small)'),
(2, 'M', 'Talla Mediana (Medium)'),
(3, 'L', 'Talla Grande (Large)'),
(4, 'XL', 'Talla Extra Grande (Extra Large)')
ON CONFLICT (id_talla) DO NOTHING;

-- Colores base del catálogo
INSERT INTO color (id_color, nombre, codigo_hex) VALUES
(1, 'Negro', '#000000'),
(2, 'Blanco', '#FFFFFF'),
(3, 'Azul Denim', '#4682B4'),
(4, 'Rojo Borgoña', '#800020')
ON CONFLICT (id_color) DO NOTHING;

-- Temporada Inicial
INSERT INTO temporada (id_temporada, nombre, descripcion, fecha_inicio, fecha_fin) VALUES
(1, 'Colección Primavera 2026', 'Moda de temporada de transición', '2026-09-01', '2026-11-30')
ON CONFLICT (id_temporada) DO NOTHING;

-- Clientes para pruebas iniciales (CU05)
INSERT INTO cliente (id_cliente, ci, nombre_completo, telefono, correo, direccion_envio) VALUES
(1, '9876543', 'María René Ortiz', '78911223', 'maria@gmail.com', 'Avenida Bush, Condominio El Prado, Dpto 4B')
ON CONFLICT (id_cliente) DO NOTHING;

-- Sincronizar secuencias para evitar colisiones de llaves primarias en futuras inserciones
SELECT setval('rol_id_rol_seq', COALESCE((SELECT MAX(id_rol) FROM rol), 1));
SELECT setval('permiso_id_permiso_seq', COALESCE((SELECT MAX(id_permiso) FROM permiso), 1));
SELECT setval('ciudad_id_ciudad_seq', COALESCE((SELECT MAX(id_ciudad) FROM ciudad), 1));
SELECT setval('usuario_id_usuario_seq', COALESCE((SELECT MAX(id_usuario) FROM usuario), 1));
SELECT setval('sucursal_id_sucursal_seq', COALESCE((SELECT MAX(id_sucursal) FROM sucursal), 1));
SELECT setval('categoria_id_categoria_seq', COALESCE((SELECT MAX(id_categoria) FROM categoria), 1));
SELECT setval('talla_id_talla_seq', COALESCE((SELECT MAX(id_talla) FROM talla), 1));
SELECT setval('color_id_color_seq', COALESCE((SELECT MAX(id_color) FROM color), 1));
SELECT setval('temporada_id_temporada_seq', COALESCE((SELECT MAX(id_temporada) FROM temporada), 1));
SELECT setval('cliente_id_cliente_seq', COALESCE((SELECT MAX(id_cliente) FROM cliente), 1));
