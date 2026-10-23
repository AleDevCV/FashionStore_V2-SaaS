ALTER TABLE prenda ADD COLUMN admite_cambio BOOLEAN NOT NULL DEFAULT true;
CREATE UNIQUE INDEX sale_detail_tenant_reference ON detalle_venta(tenant_id,id_venta,id_variante_prenda);
CREATE TABLE cambio (
 id_cambio SERIAL PRIMARY KEY, tenant_id INTEGER NOT NULL DEFAULT current_tenant() REFERENCES empresa,
 id_venta INTEGER NOT NULL, id_cliente INTEGER NOT NULL, id_sucursal INTEGER NOT NULL,
 id_variante_original INTEGER NOT NULL, cantidad INTEGER NOT NULL CHECK(cantidad>0), motivo TEXT NOT NULL,
 estado TEXT NOT NULL DEFAULT 'Solicitado' CHECK(estado IN ('Solicitado','Recibido','PagoPendiente','ReembolsoPendiente','Listo','Entregado','Reembolsado','Cancelado','Rechazado')),
 credito NUMERIC(12,2) NOT NULL CHECK(credito>=0), diferencia NUMERIC(12,2),
 id_reserva_reemplazo INTEGER, recibido_at TIMESTAMPTZ, entregado_at TIMESTAMPTZ,
 cancelar BOOLEAN NOT NULL DEFAULT false, pago_diferencia JSONB,
 created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 FOREIGN KEY(tenant_id,id_venta,id_variante_original) REFERENCES detalle_venta(tenant_id,id_venta,id_variante_prenda),
 FOREIGN KEY(tenant_id,id_cliente) REFERENCES cliente(tenant_id,id_cliente),
 FOREIGN KEY(tenant_id,id_sucursal) REFERENCES sucursal(tenant_id,id_sucursal),
 FOREIGN KEY(tenant_id,id_reserva_reemplazo) REFERENCES reserva(tenant_id,id_reserva)
);
CREATE UNIQUE INDEX change_tenant_reference ON cambio(tenant_id,id_cambio);
CREATE TABLE ajuste_monetario (
 id_ajuste SERIAL PRIMARY KEY, tenant_id INTEGER NOT NULL DEFAULT current_tenant() REFERENCES empresa,
 id_cambio INTEGER NOT NULL, tipo TEXT NOT NULL CHECK(tipo IN ('Cobro','Reembolso')),
 importe NUMERIC(12,2) NOT NULL CHECK(importe>0), origen TEXT NOT NULL, referencia TEXT NOT NULL,
 created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 UNIQUE(tenant_id,referencia), FOREIGN KEY(tenant_id,id_cambio) REFERENCES cambio(tenant_id,id_cambio)
);
CREATE TABLE notificacion (
 id_notificacion SERIAL PRIMARY KEY, tenant_id INTEGER NOT NULL DEFAULT current_tenant() REFERENCES empresa,
 id_cliente INTEGER NOT NULL, titulo TEXT NOT NULL, mensaje TEXT NOT NULL, id_cambio INTEGER,
 leida BOOLEAN NOT NULL DEFAULT false, push_enviado BOOLEAN NOT NULL DEFAULT false,
 intentos INTEGER NOT NULL DEFAULT 0, created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 FOREIGN KEY(tenant_id,id_cliente) REFERENCES cliente(tenant_id,id_cliente),
 FOREIGN KEY(tenant_id,id_cambio) REFERENCES cambio(tenant_id,id_cambio)
);
CREATE TABLE dispositivo_push (
 tenant_id INTEGER NOT NULL DEFAULT current_tenant() REFERENCES empresa,
 id_usuario INTEGER NOT NULL, token TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 PRIMARY KEY(tenant_id,id_usuario,token), FOREIGN KEY(tenant_id,id_usuario) REFERENCES usuario(tenant_id,id_usuario)
);
DO $$ DECLARE t TEXT; BEGIN
 FOREACH t IN ARRAY ARRAY['cambio','ajuste_monetario','notificacion','dispositivo_push'] LOOP
  EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY',t);
  EXECUTE format('CREATE POLICY tenant_isolation ON %I USING(tenant_id=current_tenant()) WITH CHECK(tenant_id=current_tenant())',t);
 END LOOP;
END $$;
CREATE POLICY own_changes ON cambio AS RESTRICTIVE USING(current_setting('app.role',true)<>'Cliente' OR id_cliente=own_customer());
CREATE POLICY own_notifications ON notificacion AS RESTRICTIVE USING(current_setting('app.role',true)<>'Cliente' OR id_cliente=own_customer());
-- Repara secuencias al adoptar una copia que usó INSERT con IDs explícitos.
DO $$ DECLARE r RECORD; seq TEXT; maximum BIGINT; BEGIN
 FOR r IN SELECT table_name,column_name FROM information_schema.columns WHERE table_schema='public' AND column_default LIKE 'nextval(%' LOOP
  seq:=pg_get_serial_sequence(r.table_name,r.column_name);
  IF seq IS NOT NULL THEN
   EXECUTE format('SELECT max(%I) FROM %I',r.column_name,r.table_name) INTO maximum;
   IF maximum IS NOT NULL THEN PERFORM setval(seq,maximum,true); END IF;
  END IF;
 END LOOP;
END $$;
