CREATE TABLE operacion_idempotente (
    tenant_id INTEGER NOT NULL DEFAULT current_tenant() REFERENCES empresa,
    tipo TEXT NOT NULL CHECK (tipo IN ('compra', 'pos', 'movimiento')),
    operation_id UUID NOT NULL,
    payload_hash TEXT NOT NULL,
    resultado JSONB NOT NULL,
    PRIMARY KEY (tenant_id, tipo, operation_id)
);
ALTER TABLE operacion_idempotente ENABLE ROW LEVEL SECURITY;
ALTER TABLE operacion_idempotente FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON operacion_idempotente
    USING (tenant_id=current_tenant()) WITH CHECK (tenant_id=current_tenant());

ALTER TABLE movimiento_inventario DROP CONSTRAINT movimiento_inventario_tipo_check;
ALTER TABLE movimiento_inventario DROP CONSTRAINT movimiento_inventario_cantidad_check;
ALTER TABLE movimiento_inventario ADD CONSTRAINT movimiento_inventario_tipo_check
    CHECK (tipo IN ('Entrada','Salida','Ajuste','Traspaso'));
ALTER TABLE movimiento_inventario ADD CONSTRAINT movimiento_inventario_cantidad_check
    CHECK (cantidad > 0 OR (tipo='Ajuste' AND cantidad=0));

CREATE OR REPLACE FUNCTION actualizar_stock_por_movimiento() RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    INSERT INTO inventario(tenant_id,id_sucursal,id_variante_prenda,stock)
    VALUES(NEW.tenant_id,NEW.id_sucursal,NEW.id_variante_prenda,0)
    ON CONFLICT(id_sucursal,id_variante_prenda) DO NOTHING;
    IF NEW.tipo='Entrada' THEN
        UPDATE inventario SET stock=stock+NEW.cantidad
        WHERE tenant_id=NEW.tenant_id AND id_sucursal=NEW.id_sucursal AND id_variante_prenda=NEW.id_variante_prenda;
    ELSIF NEW.tipo='Salida' THEN
        UPDATE inventario SET stock=stock-NEW.cantidad
        WHERE tenant_id=NEW.tenant_id AND id_sucursal=NEW.id_sucursal AND id_variante_prenda=NEW.id_variante_prenda AND stock>=NEW.cantidad;
        IF NOT FOUND THEN RAISE EXCEPTION 'Stock insuficiente' USING ERRCODE='23514'; END IF;
    ELSIF NEW.tipo='Ajuste' THEN
        UPDATE inventario SET stock=NEW.cantidad
        WHERE tenant_id=NEW.tenant_id AND id_sucursal=NEW.id_sucursal AND id_variante_prenda=NEW.id_variante_prenda;
    END IF;
    RETURN NEW;
END $$;
