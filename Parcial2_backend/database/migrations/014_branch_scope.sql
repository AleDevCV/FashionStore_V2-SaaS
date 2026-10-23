CREATE FUNCTION branch_visible(value INTEGER) RETURNS BOOLEAN LANGUAGE sql STABLE AS $$
 SELECT COALESCE(current_setting('app.role',true),'') IN ('','Administrador','Cliente','Servicio push')
 OR EXISTS(SELECT 1 FROM usuario_sucursal WHERE id_usuario=nullif(current_setting('app.user_id',true),'')::integer AND id_sucursal=value AND tenant_id=current_tenant())
$$;
DO $$ DECLARE t TEXT; BEGIN
 FOREACH t IN ARRAY ARRAY['venta','reserva','compra','inventario','movimiento_inventario','retencion','cambio'] LOOP
  EXECUTE format('CREATE POLICY branch_scope ON %I AS RESTRICTIVE USING(branch_visible(id_sucursal)) WITH CHECK(branch_visible(id_sucursal))',t);
 END LOOP;
END $$;
CREATE POLICY sale_detail_branch ON detalle_venta AS RESTRICTIVE USING(EXISTS(SELECT 1 FROM venta v WHERE v.id_venta=detalle_venta.id_venta)) WITH CHECK(EXISTS(SELECT 1 FROM venta v WHERE v.id_venta=detalle_venta.id_venta));
CREATE POLICY reservation_detail_branch ON detalle_reserva AS RESTRICTIVE USING(EXISTS(SELECT 1 FROM reserva r WHERE r.id_reserva=detalle_reserva.id_reserva)) WITH CHECK(EXISTS(SELECT 1 FROM reserva r WHERE r.id_reserva=detalle_reserva.id_reserva));
CREATE POLICY purchase_detail_branch ON detalle_compra AS RESTRICTIVE USING(EXISTS(SELECT 1 FROM compra c WHERE c.id_compra=detalle_compra.id_compra)) WITH CHECK(EXISTS(SELECT 1 FROM compra c WHERE c.id_compra=detalle_compra.id_compra));
CREATE POLICY receipt_branch ON comprobante AS RESTRICTIVE USING(EXISTS(SELECT 1 FROM venta v WHERE v.id_venta=comprobante.id_venta)) WITH CHECK(EXISTS(SELECT 1 FROM venta v WHERE v.id_venta=comprobante.id_venta));
