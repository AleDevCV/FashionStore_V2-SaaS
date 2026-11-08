CREATE OR REPLACE FUNCTION check_branch_limit() RETURNS TRIGGER LANGUAGE plpgsql AS $$
DECLARE cap INTEGER; used INTEGER;
BEGIN
    IF NEW.activa AND (TG_OP='INSERT' OR NOT OLD.activa) THEN
        PERFORM 1 FROM empresa WHERE id_empresa=NEW.tenant_id FOR UPDATE;
        SELECT p.max_sucursales INTO cap FROM suscripcion s JOIN plan p USING(id_plan)
        WHERE s.tenant_id=NEW.tenant_id AND now() BETWEEN s.inicio AND s.vencimiento
        FOR SHARE OF p;
        IF cap IS NULL THEN RAISE EXCEPTION 'Suscripción no vigente' USING ERRCODE='23514'; END IF;
        SELECT count(*) INTO used FROM sucursal WHERE tenant_id=NEW.tenant_id AND activa;
        IF used>=cap THEN RAISE EXCEPTION 'Límite de sucursales del plan alcanzado' USING ERRCODE='23514'; END IF;
    END IF;
    RETURN NEW;
END $$;
