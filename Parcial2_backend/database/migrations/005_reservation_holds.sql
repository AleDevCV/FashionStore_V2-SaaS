CREATE TABLE retencion (
 tenant_id INTEGER NOT NULL DEFAULT current_tenant() REFERENCES empresa,
 id_reserva INTEGER NOT NULL, id_sucursal INTEGER NOT NULL, id_variante_prenda INTEGER NOT NULL,
 cantidad INTEGER NOT NULL CHECK(cantidad>0), vence TIMESTAMPTZ NOT NULL,
 PRIMARY KEY(tenant_id,id_reserva,id_variante_prenda),
 FOREIGN KEY(tenant_id,id_reserva) REFERENCES reserva(tenant_id,id_reserva),
 FOREIGN KEY(tenant_id,id_sucursal) REFERENCES sucursal(tenant_id,id_sucursal),
 FOREIGN KEY(tenant_id,id_variante_prenda) REFERENCES variante_prenda(tenant_id,id_variante_prenda)
);
ALTER TABLE retencion ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON retencion USING(tenant_id=current_tenant()) WITH CHECK(tenant_id=current_tenant());
CREATE INDEX holds_availability ON retencion(tenant_id,id_sucursal,id_variante_prenda,vence);
ALTER TABLE venta ADD COLUMN fecha_entrega TIMESTAMPTZ;
CREATE VIEW inventario_catalogo WITH(security_invoker=true) AS
 SELECT i.tenant_id,i.id_sucursal,i.id_variante_prenda,
 GREATEST(i.stock-COALESCE((SELECT sum(r.cantidad) FROM retencion r WHERE r.tenant_id=i.tenant_id AND r.id_sucursal=i.id_sucursal AND r.id_variante_prenda=i.id_variante_prenda AND r.vence>now()),0),0)::integer AS stock
 FROM inventario i;
