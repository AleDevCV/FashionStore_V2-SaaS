CREATE TABLE operacion_sync (
 tenant_id INTEGER NOT NULL DEFAULT current_tenant() REFERENCES empresa,
 operation_id UUID NOT NULL, author_id INTEGER NOT NULL,
 branch_id INTEGER, device_id UUID NOT NULL, kind TEXT NOT NULL CHECK(kind IN ('venta','reserva')),
 payload_hash TEXT NOT NULL, envelope JSONB NOT NULL,
 state TEXT NOT NULL CHECK(state IN ('CONFIRMADA','RECHAZADA','EN_CONFLICTO')),
 result JSONB NOT NULL, original_operation UUID,
 resolved_by INTEGER, resolution TEXT, compensation NUMERIC(12,2),
 created_at TIMESTAMPTZ NOT NULL DEFAULT now(), resolved_at TIMESTAMPTZ,
 PRIMARY KEY(tenant_id,operation_id),
 FOREIGN KEY(tenant_id,author_id) REFERENCES usuario(tenant_id,id_usuario),
 FOREIGN KEY(tenant_id,branch_id) REFERENCES sucursal(tenant_id,id_sucursal),
 FOREIGN KEY(tenant_id,original_operation) REFERENCES operacion_sync(tenant_id,operation_id),
 FOREIGN KEY(tenant_id,resolved_by) REFERENCES usuario(tenant_id,id_usuario),
 CHECK(branch_id IS NOT NULL OR state='RECHAZADA')
);
ALTER TABLE operacion_sync ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON operacion_sync USING(tenant_id=current_tenant()) WITH CHECK(tenant_id=current_tenant());
CREATE POLICY own_operations ON operacion_sync AS RESTRICTIVE USING(current_setting('app.role',true)<>'Cliente' OR author_id=NULLIF(current_setting('app.user_id',true),'')::integer);
CREATE INDEX sync_history ON operacion_sync(tenant_id,author_id,created_at DESC);
CREATE UNIQUE INDEX one_revision_per_operation ON operacion_sync(tenant_id,original_operation) WHERE original_operation IS NOT NULL;
