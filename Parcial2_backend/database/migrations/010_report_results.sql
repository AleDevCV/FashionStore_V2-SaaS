CREATE TABLE reporte_resultado (
 id UUID PRIMARY KEY,
 tenant_id BIGINT NOT NULL DEFAULT nullif(current_setting('app.tenant_id',true),'')::bigint REFERENCES empresa(id_empresa),
 author_id INTEGER NOT NULL,
 filters JSONB NOT NULL,
 result JSONB NOT NULL,
 created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 expires_at TIMESTAMPTZ NOT NULL DEFAULT now()+interval '24 hours',
 FOREIGN KEY(tenant_id,author_id) REFERENCES usuario(tenant_id,id_usuario)
);
ALTER TABLE reporte_resultado ENABLE ROW LEVEL SECURITY;
ALTER TABLE reporte_resultado FORCE ROW LEVEL SECURITY;
CREATE POLICY reporte_tenant ON reporte_resultado USING(tenant_id=nullif(current_setting('app.tenant_id',true),'')::bigint AND author_id=nullif(current_setting('app.user_id',true),'')::integer) WITH CHECK(tenant_id=nullif(current_setting('app.tenant_id',true),'')::bigint AND author_id=nullif(current_setting('app.user_id',true),'')::integer);
CREATE INDEX reporte_expiration ON reporte_resultado(expires_at);
