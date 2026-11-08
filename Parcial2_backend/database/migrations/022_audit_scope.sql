ALTER TABLE bitacora ADD COLUMN id_sucursal INTEGER;
ALTER TABLE bitacora ADD COLUMN operation_id UUID;
CREATE INDEX bitacora_sucursal_fecha ON bitacora(tenant_id,id_sucursal,fecha);
CREATE INDEX bitacora_operation_id ON bitacora(tenant_id,operation_id) WHERE operation_id IS NOT NULL;

CREATE OR REPLACE FUNCTION audit_business_row() RETURNS TRIGGER LANGUAGE plpgsql AS $$
DECLARE data JSONB; tid INTEGER; actor INTEGER; record_id INTEGER; branch_id INTEGER;
BEGIN
    IF TG_OP='DELETE' THEN data:=to_jsonb(OLD); ELSE data:=to_jsonb(NEW); END IF;
    tid:=COALESCE((data->>'tenant_id')::integer,(SELECT id_empresa FROM empresa WHERE plataforma LIMIT 1));
    actor:=NULLIF(current_setting('app.user_id',true),'')::integer;
    IF NOT EXISTS(SELECT 1 FROM usuario WHERE tenant_id=tid AND id_usuario=actor) THEN actor:=NULL; END IF;
    record_id:=COALESCE((data->>'id_cambio')::integer,(data->>'id_venta')::integer,(data->>'id_usuario')::integer,
        (data->>'id_movimiento')::integer,(data->>'id_cliente')::integer,(data->>'id_sucursal')::integer,
        (data->>'id_prenda')::integer,(data->>'id_rol')::integer,(data->>'id_suscripcion')::integer,
        (data->>'id_pago')::integer,(data->>'id_empresa')::integer,(data->>'id_plan')::integer);
    branch_id:=(data->>'id_sucursal')::integer;
    IF branch_id IS NULL AND TG_TABLE_NAME='pago_transaccion' THEN
        SELECT id_sucursal INTO branch_id FROM reserva
        WHERE tenant_id=tid AND id_reserva=(data->>'id_reserva')::integer;
    ELSIF branch_id IS NULL AND TG_TABLE_NAME='ajuste_monetario' THEN
        SELECT id_sucursal INTO branch_id FROM cambio
        WHERE tenant_id=tid AND id_cambio=(data->>'id_cambio')::integer;
    END IF;
    INSERT INTO bitacora(tenant_id,id_usuario,accion,tabla_afectada,registro_id,detalle,id_sucursal)
    VALUES(tid,actor,TG_OP,TG_TABLE_NAME,record_id,
        jsonb_build_object('operacion',TG_OP,'actor_sesion',NULLIF(current_setting('app.user_id',true),''))::text,branch_id);
    IF TG_OP='DELETE' THEN RETURN OLD; ELSE RETURN NEW; END IF;
END $$;

-- Los eventos globales sin sucursal se exponen solo a administradores.
-- La empresa comercial ve identidades de su personal, no las cuentas globales de clientes.
CREATE FUNCTION audit_identity_events()
RETURNS TABLE(event_id BIGINT, local_user INTEGER, account_name TEXT, account_email TEXT,
              account_role TEXT, event_action TEXT, event_date TIMESTAMPTZ)
LANGUAGE sql SECURITY DEFINER STABLE SET search_path=pg_catalog,public AS $$
    SELECT a.id, u.id_usuario, NULLIF(trim(concat(c.nombre,' ',c.apellido)),''), c.correo,
           r.nombre::text, a.accion, a.fecha
    FROM public.auditoria_identidad a
    LEFT JOIN public.cuenta_global c ON c.id=a.account_id
    LEFT JOIN public.usuario u ON u.account_id=c.id AND u.tenant_id=public.current_tenant()
    LEFT JOIN public.rol r ON r.id_rol=u.id_role AND r.tenant_id=u.tenant_id
    WHERE current_setting('app.role',true)='Administrador'
      AND EXISTS (
          SELECT 1 FROM public.usuario actor JOIN public.rol ar ON ar.id_rol=actor.id_role AND ar.tenant_id=actor.tenant_id
          WHERE actor.tenant_id=public.current_tenant() AND actor.id_usuario=NULLIF(current_setting('app.user_id',true),'')::integer
            AND actor.estado='Activo' AND ar.nombre='Administrador'
      )
      AND (EXISTS(SELECT 1 FROM public.empresa e WHERE e.id_empresa=public.current_tenant() AND e.plataforma)
           OR (u.id_usuario IS NOT NULL AND c.tipo='PERSONAL'));
$$;
REVOKE ALL ON FUNCTION audit_identity_events() FROM PUBLIC;
