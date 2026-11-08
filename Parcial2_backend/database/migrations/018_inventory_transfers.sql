-- A3: una operación online, dos movimientos existentes, un UUID por empresa.
-- No cambia el trigger de stock ni reescribe movimientos históricos.
CREATE UNIQUE INDEX movement_tenant_reference ON movimiento_inventario(tenant_id,id_movimiento);

CREATE TABLE traspaso_inventario (
 tenant_id INTEGER NOT NULL DEFAULT current_tenant() REFERENCES empresa,
 operation_id UUID NOT NULL,
 id_sucursal_origen INTEGER NOT NULL,
 id_sucursal_destino INTEGER NOT NULL,
 id_variante_prenda INTEGER NOT NULL,
 cantidad INTEGER NOT NULL CHECK(cantidad>0),
 id_usuario INTEGER NOT NULL,
 id_movimiento_salida INTEGER NOT NULL,
 id_movimiento_entrada INTEGER NOT NULL,
 payload_hash TEXT NOT NULL CHECK(length(payload_hash)=64),
 result JSONB NOT NULL,
 created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 PRIMARY KEY(tenant_id,operation_id),
 UNIQUE(tenant_id,id_movimiento_salida),
 UNIQUE(tenant_id,id_movimiento_entrada),
 CHECK(id_sucursal_origen<>id_sucursal_destino),
 CHECK(id_movimiento_salida<>id_movimiento_entrada),
 FOREIGN KEY(tenant_id,id_sucursal_origen) REFERENCES sucursal(tenant_id,id_sucursal),
 FOREIGN KEY(tenant_id,id_sucursal_destino) REFERENCES sucursal(tenant_id,id_sucursal),
 FOREIGN KEY(tenant_id,id_variante_prenda) REFERENCES variante_prenda(tenant_id,id_variante_prenda),
 FOREIGN KEY(tenant_id,id_usuario) REFERENCES usuario(tenant_id,id_usuario),
 FOREIGN KEY(tenant_id,id_movimiento_salida) REFERENCES movimiento_inventario(tenant_id,id_movimiento),
 FOREIGN KEY(tenant_id,id_movimiento_entrada) REFERENCES movimiento_inventario(tenant_id,id_movimiento)
);
ALTER TABLE traspaso_inventario ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON traspaso_inventario
 USING(tenant_id=current_tenant()) WITH CHECK(tenant_id=current_tenant());
CREATE POLICY transfer_branch_scope ON traspaso_inventario AS RESTRICTIVE
 USING(current_setting('app.role',true)='Administrador' OR (
   EXISTS(SELECT 1 FROM usuario_sucursal us WHERE us.tenant_id=traspaso_inventario.tenant_id
     AND us.id_usuario=NULLIF(current_setting('app.user_id',true),'')::integer AND us.id_sucursal=id_sucursal_origen)
   AND EXISTS(SELECT 1 FROM usuario_sucursal us WHERE us.tenant_id=traspaso_inventario.tenant_id
     AND us.id_usuario=NULLIF(current_setting('app.user_id',true),'')::integer AND us.id_sucursal=id_sucursal_destino)))
 WITH CHECK(current_setting('app.role',true) IN ('Administrador','Encargado de Sucursal') AND
   (current_setting('app.role',true)='Administrador' OR (
   EXISTS(SELECT 1 FROM usuario_sucursal us WHERE us.tenant_id=traspaso_inventario.tenant_id
     AND us.id_usuario=NULLIF(current_setting('app.user_id',true),'')::integer AND us.id_sucursal=id_sucursal_origen)
   AND EXISTS(SELECT 1 FROM usuario_sucursal us WHERE us.tenant_id=traspaso_inventario.tenant_id
     AND us.id_usuario=NULLIF(current_setting('app.user_id',true),'')::integer AND us.id_sucursal=id_sucursal_destino))));

CREATE FUNCTION validate_transfer_movements() RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
 IF NOT EXISTS(SELECT 1 FROM movimiento_inventario s JOIN movimiento_inventario e ON e.tenant_id=s.tenant_id
   WHERE s.tenant_id=NEW.tenant_id AND s.id_movimiento=NEW.id_movimiento_salida
   AND e.id_movimiento=NEW.id_movimiento_entrada AND s.tipo='Salida' AND e.tipo='Entrada'
   AND s.id_sucursal=NEW.id_sucursal_origen AND e.id_sucursal=NEW.id_sucursal_destino
   AND s.id_variante_prenda=NEW.id_variante_prenda AND e.id_variante_prenda=NEW.id_variante_prenda
   AND s.cantidad=NEW.cantidad AND e.cantidad=NEW.cantidad
   AND s.id_usuario=NEW.id_usuario AND e.id_usuario=NEW.id_usuario)
 THEN RAISE EXCEPTION 'Las patas del traspaso no coinciden.' USING ERRCODE='23514'; END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER validate_transfer_movements BEFORE INSERT ON traspaso_inventario
 FOR EACH ROW EXECUTE FUNCTION validate_transfer_movements();

-- La consulta privilegiada solo protege filas ya vinculadas, incluso si RLS
-- oculta la otra sucursal. No devuelve datos comerciales al invocador.
CREATE FUNCTION protect_transfer_history() RETURNS TRIGGER LANGUAGE plpgsql
 SECURITY DEFINER SET search_path=pg_catalog,public AS $$
BEGIN
 IF TG_TABLE_NAME='traspaso_inventario' THEN
   RAISE EXCEPTION 'El historial de traspasos es inmutable.' USING ERRCODE='23514';
 END IF;
 IF TG_OP='INSERT' THEN
   IF NEW.tipo='Traspaso' THEN
     RAISE EXCEPTION 'Traspaso requiere Salida y Entrada vinculadas.' USING ERRCODE='23514';
   END IF;
   RETURN NEW;
 END IF;
 IF EXISTS(SELECT 1 FROM public.traspaso_inventario t WHERE t.tenant_id=OLD.tenant_id
   AND OLD.id_movimiento IN (t.id_movimiento_salida,t.id_movimiento_entrada)) THEN
   RAISE EXCEPTION 'No se modifica un movimiento vinculado a traspaso.' USING ERRCODE='23514';
 END IF;
 IF TG_OP='DELETE' THEN RETURN OLD; END IF;
 RETURN NEW;
END $$;
REVOKE ALL ON FUNCTION protect_transfer_history() FROM PUBLIC;
CREATE TRIGGER protect_transfer_history BEFORE UPDATE OR DELETE ON traspaso_inventario
 FOR EACH ROW EXECUTE FUNCTION protect_transfer_history();
CREATE TRIGGER protect_transfer_movements BEFORE INSERT OR UPDATE OR DELETE ON movimiento_inventario
 FOR EACH ROW EXECUTE FUNCTION protect_transfer_history();
