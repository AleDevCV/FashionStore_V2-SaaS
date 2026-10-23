-- Una instalación solo pertenece a una sesión registrada. No devuelve información de otra empresa.
CREATE FUNCTION bind_push_device(value TEXT) RETURNS VOID
LANGUAGE plpgsql SECURITY DEFINER SET search_path=public,pg_temp AS $$
DECLARE tid INTEGER:=current_tenant(); uid INTEGER:=nullif(current_setting('app.user_id',true),'')::integer;
BEGIN
 IF tid IS NULL OR uid IS NULL OR length(value)<20 OR length(value)>4096 OR NOT EXISTS(SELECT 1 FROM usuario WHERE tenant_id=tid AND id_usuario=uid AND estado='Activo') THEN
  RAISE EXCEPTION 'Sesión o dispositivo no válido';
 END IF;
 PERFORM pg_advisory_xact_lock(hashtextextended(value,262026));
 DELETE FROM dispositivo_push WHERE token=value;
 INSERT INTO dispositivo_push(tenant_id,id_usuario,token) VALUES(tid,uid,value);
END $$;
REVOKE ALL ON FUNCTION bind_push_device(TEXT) FROM PUBLIC;
