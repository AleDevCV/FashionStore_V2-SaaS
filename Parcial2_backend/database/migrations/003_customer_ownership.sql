-- El aislamiento de empresa se combina con el control de propiedad del cliente.
CREATE FUNCTION own_customer() RETURNS INTEGER LANGUAGE sql STABLE AS $$
 SELECT id_cliente FROM cliente WHERE tenant_id=current_tenant()
 AND correo=NULLIF(current_setting('app.email',true),'') LIMIT 1
$$;
CREATE POLICY customer_sales ON venta AS RESTRICTIVE
 USING(current_setting('app.role',true)<>'Cliente' OR id_cliente=own_customer())
 WITH CHECK(current_setting('app.role',true)<>'Cliente' OR id_cliente=own_customer());
CREATE POLICY customer_reservations ON reserva AS RESTRICTIVE
 USING(current_setting('app.role',true)<>'Cliente' OR id_cliente=own_customer())
 WITH CHECK(current_setting('app.role',true)<>'Cliente' OR id_cliente=own_customer());
CREATE POLICY customer_sale_lines ON detalle_venta AS RESTRICTIVE
 USING(current_setting('app.role',true)<>'Cliente' OR EXISTS(SELECT 1 FROM venta v WHERE v.id_venta=detalle_venta.id_venta));
CREATE POLICY customer_reservation_lines ON detalle_reserva AS RESTRICTIVE
 USING(current_setting('app.role',true)<>'Cliente' OR EXISTS(SELECT 1 FROM reserva r WHERE r.id_reserva=detalle_reserva.id_reserva));
CREATE POLICY customer_receipts ON comprobante AS RESTRICTIVE
 USING(current_setting('app.role',true)<>'Cliente' OR EXISTS(SELECT 1 FROM venta v WHERE v.id_venta=comprobante.id_venta));
CREATE POLICY customer_payments ON pago_transaccion AS RESTRICTIVE
 USING(current_setting('app.role',true)<>'Cliente' OR EXISTS(SELECT 1 FROM venta v WHERE v.id_venta=pago_transaccion.id_venta));
