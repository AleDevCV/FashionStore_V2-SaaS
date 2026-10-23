-- =============================================================================
-- FASHIONSTORE - MIGRACIÓN BASE DE DATOS: BLOQUE 3 (CU09, CU10, CU25)
-- Expansión del Catálogo y Monitoreo Multisucursal
-- =============================================================================

-- 1. Asegurar la tabla temporada y sus columnas requeridas
CREATE TABLE IF NOT EXISTS temporada (
    id_temporada SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    descripcion VARCHAR(255),
    fecha_inicio DATE,
    fecha_fin DATE,
    estado BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Agregar columnas en caso de que la tabla ya existiese sin ellas
ALTER TABLE temporada 
ADD COLUMN IF NOT EXISTS estado BOOLEAN NOT NULL DEFAULT TRUE;

ALTER TABLE temporada 
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Establecer fechas por defecto si existen registros previos con fechas NULL
UPDATE temporada 
SET fecha_inicio = CURRENT_DATE 
WHERE fecha_inicio IS NULL;

UPDATE temporada 
SET fecha_fin = CURRENT_DATE + INTERVAL '90 days' 
WHERE fecha_fin IS NULL;

-- Asegurar NOT NULL en fechas de temporada
ALTER TABLE temporada ALTER COLUMN fecha_inicio SET NOT NULL;
ALTER TABLE temporada ALTER COLUMN fecha_fin SET NOT NULL;

-- Restricción CHECK de coherencia de fechas (fecha_inicio <= fecha_fin)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_temporada_fechas'
    ) THEN
        ALTER TABLE temporada 
        ADD CONSTRAINT chk_temporada_fechas CHECK (fecha_inicio <= fecha_fin);
    END IF;
END $$;

-- 2. Asegurar la columna id_temporada en la tabla prenda con ON DELETE SET NULL
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'prenda' AND column_name = 'id_temporada'
    ) THEN
        ALTER TABLE prenda 
        ADD COLUMN id_temporada INT REFERENCES temporada(id_temporada) ON DELETE SET NULL;
    ELSE
        -- Si la columna ya existe, asegurarse de que la restricción FK tenga ON DELETE SET NULL
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint c
            JOIN pg_class t ON c.conrelid = t.oid
            WHERE t.relname = 'prenda' AND c.conname = 'prenda_id_temporada_fkey'
        ) THEN
            ALTER TABLE prenda 
            ADD CONSTRAINT prenda_id_temporada_fkey 
            FOREIGN KEY (id_temporada) REFERENCES temporada(id_temporada) ON DELETE SET NULL;
        END IF;
    END IF;
END $$;

-- 3. Índices de optimización para consultas analíticas y filtrado
CREATE INDEX IF NOT EXISTS idx_prenda_id_temporada ON prenda(id_temporada);
CREATE INDEX IF NOT EXISTS idx_temporada_fechas ON temporada(fecha_inicio, fecha_fin);
CREATE INDEX IF NOT EXISTS idx_inventario_sucursal_variante ON inventario(id_sucursal, id_variante_prenda);
CREATE INDEX IF NOT EXISTS idx_variante_prenda_id_prenda ON variante_prenda(id_prenda);
