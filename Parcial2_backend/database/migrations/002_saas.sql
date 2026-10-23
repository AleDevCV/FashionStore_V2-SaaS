CREATE TABLE empresa (
 id_empresa SERIAL PRIMARY KEY, slug TEXT NOT NULL UNIQUE CHECK(slug ~ '^[a-z0-9][a-z0-9-]{1,60}$'),
 nombre TEXT NOT NULL, activa BOOLEAN NOT NULL DEFAULT true, plataforma BOOLEAN NOT NULL DEFAULT false,
 created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE plan (
 id_plan SERIAL PRIMARY KEY, nombre TEXT NOT NULL UNIQUE,
 max_sucursales INTEGER NOT NULL CHECK(max_sucursales>0), reportes_ia BOOLEAN NOT NULL DEFAULT false
);
CREATE TABLE suscripcion (
 id_suscripcion SERIAL PRIMARY KEY, tenant_id INTEGER NOT NULL UNIQUE REFERENCES empresa,
 id_plan INTEGER NOT NULL REFERENCES plan, inicio TIMESTAMPTZ NOT NULL,
 vencimiento TIMESTAMPTZ NOT NULL, CHECK(vencimiento>inicio)
);
INSERT INTO empresa(slug,nombre,plataforma) VALUES ('plataforma','FashionStore Plataforma',true);
INSERT INTO plan(nombre,max_sucursales,reportes_ia) VALUES ('Básico',2,false),('Profesional',10,true);

-- El tenant original se asigna a un tenant explícito durante una migración de copia.
-- En una inicialización nueva las tablas comerciales aún no tienen datos.
CREATE FUNCTION current_tenant() RETURNS INTEGER LANGUAGE sql STABLE AS $$
 SELECT NULLIF(current_setting('app.tenant_id',true),'')::integer
$$;
-- Adopción del prototipo single-tenant sobre una COPIA: backfill explícito.
DO $$
DECLARE legacy_id INTEGER;
BEGIN
 IF EXISTS(SELECT 1 FROM usuario) THEN
  INSERT INTO empresa(slug,nombre) VALUES('fashionstore-legado','FashionStore Legado') RETURNING id_empresa INTO legacy_id;
  PERFORM set_config('app.tenant_id',legacy_id::text,true);
  INSERT INTO suscripcion(tenant_id,id_plan,inicio,vencimiento) VALUES(legacy_id,2,now(),now()+interval '30 days');
 END IF;
END $$;
DO $$
DECLARE t TEXT; c RECORD; cols TEXT;
BEGIN
 FOREACH t IN ARRAY ARRAY['rol','rol_permiso','usuario','usuario_token','ciudad','sucursal','cliente','temporada','categoria','talla','color','prenda','variante_prenda','imagen_prenda','proveedor','inventario','movimiento_inventario','compra','detalle_compra','reserva','detalle_reserva','venta','detalle_venta','pago_transaccion','comprobante','bitacora'] LOOP
  EXECUTE format('ALTER TABLE %I ADD COLUMN tenant_id INTEGER NOT NULL DEFAULT current_tenant() REFERENCES empresa',t);
  EXECUTE format('CREATE INDEX ON %I(tenant_id)',t);
  -- Unicidades de negocio pasan a ser por empresa; las PK seriales se conservan.
  FOR c IN SELECT conname,conkey FROM pg_constraint WHERE conrelid=t::regclass AND contype='u' LOOP
   SELECT string_agg(quote_ident(a.attname),',' ORDER BY k.ord) INTO cols
    FROM unnest(c.conkey) WITH ORDINALITY k(num,ord) JOIN pg_attribute a ON a.attrelid=t::regclass AND a.attnum=k.num;
   EXECUTE format('ALTER TABLE %I DROP CONSTRAINT %I',t,c.conname);
   EXECUTE format('ALTER TABLE %I ADD CONSTRAINT %I UNIQUE(tenant_id,%s)',t,c.conname,cols);
  END LOOP;
 END LOOP;
 -- Las FK compuestas impiden enlazar cabeceras, usuarios o variantes de otra empresa.
 FOR c IN
  SELECT con.oid,con.conname,con.conrelid::regclass AS child,con.confrelid::regclass AS parent,
   (SELECT string_agg(quote_ident(a.attname),',' ORDER BY k.ord) FROM unnest(con.conkey) WITH ORDINALITY k(num,ord) JOIN pg_attribute a ON a.attrelid=con.conrelid AND a.attnum=k.num) AS childcols,
   (SELECT string_agg(quote_ident(a.attname),',' ORDER BY k.ord) FROM unnest(con.confkey) WITH ORDINALITY k(num,ord) JOIN pg_attribute a ON a.attrelid=con.confrelid AND a.attnum=k.num) AS parentcols
  FROM pg_constraint con WHERE con.contype='f'
   AND EXISTS(SELECT 1 FROM pg_attribute a WHERE a.attrelid=con.conrelid AND a.attname='tenant_id')
   AND EXISTS(SELECT 1 FROM pg_attribute a WHERE a.attrelid=con.confrelid AND a.attname='tenant_id')
 LOOP
  EXECUTE format('CREATE UNIQUE INDEX IF NOT EXISTS %I ON %s(tenant_id,%s)', 'tenant_ref_'||c.parent||'_'||c.parentcols,c.parent,c.parentcols);
  EXECUTE format('ALTER TABLE %s ADD CONSTRAINT %I FOREIGN KEY(tenant_id,%s) REFERENCES %s(tenant_id,%s)',c.child,'tenant_'||c.conname,c.childcols,c.parent,c.parentcols);
 END LOOP;
 FOREACH t IN ARRAY ARRAY['rol','rol_permiso','usuario','usuario_token','ciudad','sucursal','cliente','temporada','categoria','talla','color','prenda','variante_prenda','imagen_prenda','proveedor','inventario','movimiento_inventario','compra','detalle_compra','reserva','detalle_reserva','venta','detalle_venta','pago_transaccion','comprobante','bitacora'] LOOP
  EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY',t);
  EXECUTE format('CREATE POLICY tenant_isolation ON %I USING(tenant_id=current_tenant()) WITH CHECK(tenant_id=current_tenant())',t);
 END LOOP;
END $$;

ALTER TABLE usuario ADD COLUMN token_version INTEGER NOT NULL DEFAULT 0;
ALTER TABLE sucursal ADD COLUMN activa BOOLEAN NOT NULL DEFAULT true;
ALTER TABLE temporada ADD COLUMN estado BOOLEAN NOT NULL DEFAULT true;
ALTER TABLE temporada ADD COLUMN created_at TIMESTAMP DEFAULT now();
ALTER TABLE prenda ADD COLUMN material TEXT;
ALTER TABLE prenda ADD COLUMN medidas TEXT;
ALTER TABLE prenda ADD COLUMN precio_mayorista NUMERIC(10,2) CHECK(precio_mayorista>=0);
ALTER TABLE prenda ADD COLUMN umbral_mayorista INTEGER NOT NULL DEFAULT 6 CHECK(umbral_mayorista>0);
ALTER TABLE prenda ADD COLUMN precio_oferta NUMERIC(10,2) CHECK(precio_oferta>=0);
ALTER TABLE prenda ADD COLUMN oferta_inicio DATE;
ALTER TABLE prenda ADD COLUMN oferta_fin DATE;
CREATE TABLE usuario_sucursal (
 tenant_id INTEGER NOT NULL DEFAULT current_tenant() REFERENCES empresa,
 id_usuario INTEGER NOT NULL, id_sucursal INTEGER NOT NULL,
 PRIMARY KEY(tenant_id,id_usuario,id_sucursal),
 FOREIGN KEY(tenant_id,id_usuario) REFERENCES usuario(tenant_id,id_usuario),
 FOREIGN KEY(tenant_id,id_sucursal) REFERENCES sucursal(tenant_id,id_sucursal)
);
ALTER TABLE usuario_sucursal ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON usuario_sucursal USING(tenant_id=current_tenant()) WITH CHECK(tenant_id=current_tenant());
ALTER TABLE suscripcion ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON suscripcion USING(tenant_id=current_tenant()) WITH CHECK(tenant_id=current_tenant());

-- También restringe cambios realizados por los routers heredados de sucursales.
CREATE FUNCTION check_branch_limit() RETURNS TRIGGER LANGUAGE plpgsql AS $$
DECLARE cap INTEGER; used INTEGER;
BEGIN
 IF NEW.activa AND (TG_OP='INSERT' OR NOT OLD.activa) THEN
  PERFORM 1 FROM empresa WHERE id_empresa=NEW.tenant_id FOR UPDATE;
  SELECT p.max_sucursales INTO cap FROM suscripcion s JOIN plan p USING(id_plan)
   WHERE s.tenant_id=NEW.tenant_id AND now() BETWEEN s.inicio AND s.vencimiento;
  IF cap IS NULL THEN RAISE EXCEPTION 'Suscripción no vigente' USING ERRCODE='23514'; END IF;
  SELECT count(*) INTO used FROM sucursal WHERE tenant_id=NEW.tenant_id AND activa;
  IF used>=cap THEN RAISE EXCEPTION 'Límite de sucursales del plan alcanzado' USING ERRCODE='23514'; END IF;
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER branch_limit BEFORE INSERT OR UPDATE ON sucursal FOR EACH ROW EXECUTE FUNCTION check_branch_limit();

-- El UPDATE condicional bloquea la fila y comprueba el saldo de forma atómica.
CREATE OR REPLACE FUNCTION actualizar_stock_por_movimiento() RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
 INSERT INTO inventario(tenant_id,id_sucursal,id_variante_prenda,stock)
 VALUES(NEW.tenant_id,NEW.id_sucursal,NEW.id_variante_prenda,0)
 ON CONFLICT(id_sucursal,id_variante_prenda) DO NOTHING;
 IF NEW.tipo='Entrada' THEN
  UPDATE inventario SET stock=stock+NEW.cantidad WHERE tenant_id=NEW.tenant_id AND id_sucursal=NEW.id_sucursal AND id_variante_prenda=NEW.id_variante_prenda;
 ELSIF NEW.tipo='Salida' THEN
  UPDATE inventario SET stock=stock-NEW.cantidad WHERE tenant_id=NEW.tenant_id AND id_sucursal=NEW.id_sucursal AND id_variante_prenda=NEW.id_variante_prenda AND stock>=NEW.cantidad;
  IF NOT FOUND THEN RAISE EXCEPTION 'Stock insuficiente' USING ERRCODE='23514'; END IF;
 END IF;
 RETURN NEW;
END $$;
