ALTER TABLE reserva ADD COLUMN checkout_generation INTEGER NOT NULL DEFAULT 1;
ALTER TABLE pago_transaccion ADD COLUMN id_reserva INTEGER;
ALTER TABLE pago_transaccion ADD COLUMN url_pago TEXT;
ALTER TABLE pago_transaccion ADD COLUMN vence TIMESTAMPTZ;
UPDATE pago_transaccion p SET id_reserva=(p.payload_respuesta->>'id_reserva')::integer
WHERE (p.payload_respuesta->>'id_reserva')~'^[0-9]+$' AND EXISTS(SELECT 1 FROM reserva r WHERE r.tenant_id=p.tenant_id AND r.id_reserva=(p.payload_respuesta->>'id_reserva')::integer);
ALTER TABLE pago_transaccion ADD CONSTRAINT payment_reservation_tenant FOREIGN KEY(tenant_id,id_reserva) REFERENCES reserva(tenant_id,id_reserva);
DROP POLICY customer_payments ON pago_transaccion;
CREATE POLICY customer_payments ON pago_transaccion AS RESTRICTIVE USING(current_setting('app.role',true)<>'Cliente' OR EXISTS(SELECT 1 FROM reserva r WHERE r.id_reserva=pago_transaccion.id_reserva) OR EXISTS(SELECT 1 FROM venta v WHERE v.id_venta=pago_transaccion.id_venta));
CREATE POLICY payment_branch ON pago_transaccion AS RESTRICTIVE USING((id_reserva IS NOT NULL AND EXISTS(SELECT 1 FROM reserva r WHERE r.id_reserva=pago_transaccion.id_reserva)) OR (id_venta IS NOT NULL AND EXISTS(SELECT 1 FROM venta v WHERE v.id_venta=pago_transaccion.id_venta)) OR (id_reserva IS NULL AND id_venta IS NULL AND current_setting('app.role',true)<>'Cliente'));
CREATE TABLE stripe_event (
 tenant_id INTEGER NOT NULL DEFAULT current_tenant() REFERENCES empresa,
 event_id TEXT NOT NULL,
 event_type TEXT NOT NULL,
 result JSONB NOT NULL,
 created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 PRIMARY KEY(tenant_id,event_id)
);
ALTER TABLE stripe_event ENABLE ROW LEVEL SECURITY;
CREATE POLICY stripe_event_tenant ON stripe_event USING(tenant_id=current_tenant()) WITH CHECK(tenant_id=current_tenant());
