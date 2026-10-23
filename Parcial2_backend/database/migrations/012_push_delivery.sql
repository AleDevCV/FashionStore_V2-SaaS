CREATE TABLE push_entrega (
 tenant_id INTEGER NOT NULL DEFAULT current_tenant() REFERENCES empresa,
 id_notificacion INTEGER NOT NULL REFERENCES notificacion(id_notificacion),
 token_hash TEXT NOT NULL,
 enviado BOOLEAN NOT NULL DEFAULT false,
 intentos INTEGER NOT NULL DEFAULT 0,
 proximo_intento TIMESTAMPTZ NOT NULL DEFAULT now(),
 ultimo_estado TEXT,
 PRIMARY KEY(tenant_id,id_notificacion,token_hash)
);
ALTER TABLE push_entrega ENABLE ROW LEVEL SECURITY;
CREATE POLICY push_tenant ON push_entrega USING(tenant_id=current_tenant()) WITH CHECK(tenant_id=current_tenant());
CREATE UNIQUE INDEX notification_tenant_reference ON notificacion(tenant_id,id_notificacion);
ALTER TABLE push_entrega ADD CONSTRAINT push_notification_tenant FOREIGN KEY(tenant_id,id_notificacion) REFERENCES notificacion(tenant_id,id_notificacion);
