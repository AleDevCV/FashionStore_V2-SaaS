CREATE FUNCTION audit_business_row() RETURNS TRIGGER LANGUAGE plpgsql AS $$
DECLARE data JSONB; tid INTEGER; actor INTEGER; record_id INTEGER;
BEGIN
 IF TG_OP='DELETE' THEN data:=to_jsonb(OLD); ELSE data:=to_jsonb(NEW); END IF;
 tid:=COALESCE((data->>'tenant_id')::integer,(SELECT id_empresa FROM empresa WHERE plataforma LIMIT 1));
 actor:=NULLIF(current_setting('app.user_id',true),'')::integer;
 IF NOT EXISTS(SELECT 1 FROM usuario WHERE tenant_id=tid AND id_usuario=actor) THEN actor:=NULL; END IF;
 record_id:=COALESCE((data->>'id_cambio')::integer,(data->>'id_venta')::integer,(data->>'id_usuario')::integer,
  (data->>'id_movimiento')::integer,(data->>'id_cliente')::integer,(data->>'id_sucursal')::integer,(data->>'id_prenda')::integer,(data->>'id_rol')::integer,(data->>'id_suscripcion')::integer,(data->>'id_pago')::integer,(data->>'id_empresa')::integer,(data->>'id_plan')::integer);
 INSERT INTO bitacora(tenant_id,id_usuario,accion,tabla_afectada,registro_id,detalle)
 VALUES(tid,actor,TG_OP,TG_TABLE_NAME,record_id,
  jsonb_build_object('operacion',TG_OP,'actor_sesion',NULLIF(current_setting('app.user_id',true),''))::text);
 IF TG_OP='DELETE' THEN RETURN OLD; ELSE RETURN NEW; END IF;
END $$;
DROP TRIGGER trg_auditoria_prendas ON prenda;
DROP FUNCTION auditar_prendas();
DO $$ DECLARE t TEXT; BEGIN
 FOREACH t IN ARRAY ARRAY['prenda','usuario','rol','rol_permiso','cliente','sucursal','suscripcion','cambio','ajuste_monetario','movimiento_inventario','venta','pago_transaccion','empresa','plan'] LOOP
  EXECUTE format('CREATE TRIGGER transactional_audit AFTER INSERT OR UPDATE OR DELETE ON %I FOR EACH ROW EXECUTE FUNCTION audit_business_row()',t);
 END LOOP;
END $$;
