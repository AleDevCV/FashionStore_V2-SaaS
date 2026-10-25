-- Identidad global; los perfiles y las operaciones conservan tenant e IDs.
CREATE TABLE cuenta_global (
 id BIGSERIAL PRIMARY KEY, correo TEXT NOT NULL, password_hash TEXT NOT NULL,
 nombre TEXT NOT NULL, apellido TEXT NOT NULL DEFAULT '', telefono TEXT,
 ci TEXT, direccion_envio TEXT, correo_recuperacion TEXT,
 tipo TEXT NOT NULL CHECK(tipo IN ('CLIENTE','PERSONAL','PLATAFORMA')),
 estado TEXT NOT NULL DEFAULT 'Activo' CHECK(estado IN ('Activo','Inactivo')),
 token_version INTEGER NOT NULL DEFAULT 0, creada TIMESTAMPTZ NOT NULL DEFAULT now(),
 CHECK(correo=lower(trim(correo)))
);
CREATE UNIQUE INDEX cuenta_global_correo ON cuenta_global(lower(correo));
ALTER TABLE cuenta_global ENABLE ROW LEVEL SECURITY;
-- Sin políticas: la aplicación solo accede mediante funciones acotadas.
ALTER TABLE usuario ADD COLUMN account_id BIGINT REFERENCES cuenta_global;
CREATE UNIQUE INDEX usuario_identidad_empresa ON usuario(tenant_id,account_id);
CREATE TABLE cuenta_recuperacion (
 token_hash TEXT PRIMARY KEY, account_id BIGINT NOT NULL REFERENCES cuenta_global,
 expiracion TIMESTAMPTZ NOT NULL DEFAULT now()+interval '30 minutes', usado BOOLEAN NOT NULL DEFAULT false
);
ALTER TABLE cuenta_recuperacion ENABLE ROW LEVEL SECURITY;
CREATE TABLE auditoria_identidad (
 id BIGSERIAL PRIMARY KEY, account_id BIGINT REFERENCES cuenta_global,
 accion TEXT NOT NULL, fecha TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE auditoria_identidad ENABLE ROW LEVEL SECURITY;

-- Las colisiones heredadas se conservan como identidades distintas; nunca fusionar personas por correo.
DO $$ DECLARE u RECORD; email TEXT; aid BIGINT; BEGIN
 FOR u IN SELECT v.*,r.nombre AS rol,e.plataforma FROM usuario v JOIN rol r ON r.id_rol=v.id_role JOIN empresa e ON e.id_empresa=v.tenant_id ORDER BY v.id_usuario LOOP
  email:=lower(trim(u.correo));
  IF EXISTS(SELECT 1 FROM cuenta_global WHERE correo=email) THEN
   email:='legado-'||u.tenant_id||'-'||u.id_usuario||'@fashionstore.invalid';
   UPDATE cliente SET correo=email WHERE tenant_id=u.tenant_id AND lower(correo)=lower(u.correo);
   UPDATE usuario SET correo=email WHERE id_usuario=u.id_usuario;
  END IF;
  INSERT INTO cuenta_global(correo,password_hash,nombre,apellido,telefono,tipo,estado)
   VALUES(email,u.password_hash,u.nombre,u.apellido,u.telefono,CASE WHEN u.rol='Cliente' THEN 'CLIENTE' WHEN u.plataforma THEN 'PLATAFORMA' ELSE 'PERSONAL' END,u.estado) RETURNING id INTO aid;
  UPDATE usuario SET account_id=aid,token_version=token_version+1 WHERE id_usuario=u.id_usuario;
 END LOOP;
END $$;

CREATE FUNCTION identity_lookup(p_correo TEXT DEFAULT NULL,p_id BIGINT DEFAULT NULL) RETURNS JSONB
LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
 SELECT to_jsonb(a)||jsonb_build_object('tenant_id',u.tenant_id,'id_usuario',u.id_usuario,'rol',r.nombre,'slug',e.slug,'empresa_activa',e.activa,'local_estado',u.estado,'local_version',u.token_version)
 FROM public.cuenta_global a LEFT JOIN public.usuario u ON u.account_id=a.id AND a.tipo<>'CLIENTE'
 LEFT JOIN public.rol r ON r.id_rol=u.id_role LEFT JOIN public.empresa e ON e.id_empresa=u.tenant_id
 WHERE (p_id IS NOT NULL AND a.id=p_id) OR (p_id IS NULL AND a.correo=lower(trim(p_correo))) LIMIT 1
$$;

CREATE FUNCTION identity_index_user(p_user INTEGER) RETURNS BIGINT
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
DECLARE u RECORD; a public.cuenta_global; aid BIGINT; kind TEXT; BEGIN
 SELECT v.*,r.nombre AS rol,e.plataforma INTO u FROM public.usuario v JOIN public.rol r ON r.id_rol=v.id_role JOIN public.empresa e ON e.id_empresa=v.tenant_id WHERE v.id_usuario=p_user AND v.tenant_id=public.current_tenant();
 IF NOT FOUND THEN RAISE EXCEPTION 'Usuario fuera de la empresa' USING ERRCODE='42501'; END IF;
 kind:=CASE WHEN u.rol='Cliente' THEN 'CLIENTE' WHEN u.plataforma THEN 'PLATAFORMA' ELSE 'PERSONAL' END;
 IF u.account_id IS NULL THEN
  INSERT INTO public.cuenta_global(correo,password_hash,nombre,apellido,telefono,tipo,estado) VALUES(lower(trim(u.correo)),u.password_hash,u.nombre,u.apellido,u.telefono,kind,u.estado) RETURNING id INTO aid;
  UPDATE public.usuario SET account_id=aid,correo=lower(trim(correo)) WHERE id_usuario=p_user;
 ELSE
  SELECT * INTO a FROM public.cuenta_global WHERE id=u.account_id FOR UPDATE;
  aid:=a.id;
  IF a.tipo='CLIENTE' THEN
   IF kind<>'CLIENTE' OR lower(trim(u.correo))<>a.correo OR u.password_hash<>a.password_hash THEN
    RAISE EXCEPTION 'La identidad del cliente se administra desde su propia cuenta global' USING ERRCODE='42501';
   END IF;
  ELSE
   UPDATE public.cuenta_global SET correo=lower(trim(u.correo)),password_hash=u.password_hash,nombre=u.nombre,apellido=u.apellido,telefono=u.telefono,tipo=kind,estado=u.estado,
    token_version=token_version+CASE WHEN correo<>lower(trim(u.correo)) OR password_hash<>u.password_hash OR tipo<>kind OR estado<>u.estado THEN 1 ELSE 0 END WHERE id=aid;
  END IF;
 END IF;
 RETURN aid;
END $$;

CREATE FUNCTION identity_register(p_data JSONB) RETURNS BIGINT
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
DECLARE aid BIGINT; BEGIN
 INSERT INTO public.cuenta_global(correo,password_hash,nombre,apellido,telefono,ci,direccion_envio,correo_recuperacion,tipo)
 VALUES(lower(trim(p_data->>'correo')),p_data->>'password_hash',p_data->>'nombre',p_data->>'apellido',p_data->>'telefono',p_data->>'ci',p_data->>'direccion_envio',p_data->>'correo_recuperacion','CLIENTE') RETURNING id INTO aid;
 INSERT INTO public.auditoria_identidad(account_id,accion) VALUES(aid,'REGISTRO'); RETURN aid;
END $$;

CREATE FUNCTION identity_customer_profile(p_account BIGINT,p_tenant INTEGER) RETURNS INTEGER
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
DECLARE a public.cuenta_global; uid INTEGER; rid INTEGER; existing_state TEXT; BEGIN
 IF NULLIF(current_setting('app.account_id',true),'')::BIGINT IS DISTINCT FROM p_account THEN RAISE EXCEPTION 'Identidad no autorizada' USING ERRCODE='42501'; END IF;
 SELECT * INTO a FROM public.cuenta_global WHERE id=p_account AND tipo='CLIENTE' AND estado='Activo' FOR UPDATE;
 IF NOT FOUND THEN RAISE EXCEPTION 'Cuenta no disponible' USING ERRCODE='42501'; END IF;
 IF NOT EXISTS(SELECT 1 FROM public.empresa WHERE id_empresa=p_tenant AND activa AND NOT plataforma) THEN RAISE EXCEPTION 'Tienda no disponible' USING ERRCODE='42501'; END IF;
 SELECT id_usuario,estado INTO uid,existing_state FROM public.usuario WHERE tenant_id=p_tenant AND account_id=p_account;
 IF uid IS NOT NULL THEN
  IF existing_state<>'Activo' THEN RAISE EXCEPTION 'Acceso desactivado en esta tienda' USING ERRCODE='42501'; END IF;
  RETURN uid;
 END IF;
 SELECT id_rol INTO rid FROM public.rol WHERE tenant_id=p_tenant AND nombre='Cliente';
 IF rid IS NULL THEN RAISE EXCEPTION 'Tienda sin rol de cliente' USING ERRCODE='42501'; END IF;
 INSERT INTO public.usuario(tenant_id,account_id,nombre,apellido,correo,password_hash,telefono,id_role) VALUES(p_tenant,a.id,a.nombre,a.apellido,a.correo,a.password_hash,a.telefono,rid) RETURNING id_usuario INTO uid;
 INSERT INTO public.cliente(tenant_id,ci,nombre_completo,telefono,correo,direccion_envio)
 VALUES(p_tenant,'WEB-'||a.id,a.nombre||' '||a.apellido,a.telefono,a.correo,a.direccion_envio);
 RETURN uid;
END $$;

CREATE FUNCTION identity_revoke(p_id BIGINT) RETURNS VOID
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
BEGIN
 IF NULLIF(current_setting('app.account_id',true),'')::BIGINT IS DISTINCT FROM p_id THEN RAISE EXCEPTION 'Identidad no autorizada' USING ERRCODE='42501'; END IF;
 UPDATE public.cuenta_global SET token_version=token_version+1 WHERE id=p_id;
 INSERT INTO public.auditoria_identidad(account_id,accion) VALUES(p_id,'LOGOUT');
END $$;

CREATE FUNCTION identity_reset_issue(p_id BIGINT,p_hash TEXT) RETURNS VOID
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
BEGIN
 UPDATE public.cuenta_recuperacion SET usado=true WHERE account_id=p_id AND NOT usado;
 INSERT INTO public.cuenta_recuperacion(token_hash,account_id) VALUES(p_hash,p_id);
 INSERT INTO public.auditoria_identidad(account_id,accion) VALUES(p_id,'SOLICITUD_RECUPERACION');
END $$;
CREATE FUNCTION identity_reset_lookup(p_hash TEXT) RETURNS JSONB
LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
 SELECT jsonb_build_object('id',a.id,'correo',a.correo,'valido',NOT t.usado AND t.expiracion>now() AND a.estado='Activo') FROM public.cuenta_recuperacion t JOIN public.cuenta_global a ON a.id=t.account_id WHERE token_hash=p_hash
$$;
CREATE FUNCTION identity_reset_apply(p_hash TEXT,p_password_hash TEXT) RETURNS BOOLEAN
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
DECLARE aid BIGINT; BEGIN
 SELECT t.account_id INTO aid FROM public.cuenta_recuperacion t JOIN public.cuenta_global a ON a.id=t.account_id WHERE t.token_hash=p_hash AND NOT t.usado AND t.expiracion>now() AND a.estado='Activo' FOR UPDATE OF t;
 IF aid IS NULL THEN RETURN false; END IF;
 UPDATE public.cuenta_global SET password_hash=p_password_hash,token_version=token_version+1 WHERE id=aid;
 UPDATE public.usuario SET password_hash=p_password_hash,token_version=token_version+1 WHERE account_id=aid;
 UPDATE public.cuenta_recuperacion SET usado=true WHERE account_id=aid;
 INSERT INTO public.auditoria_identidad(account_id,accion) VALUES(aid,'PASSWORD_RESTABLECIDA'); RETURN true;
END $$;

-- Ejecutables por el rol de aplicación específico mediante el migrador; nunca PUBLIC.
REVOKE ALL ON FUNCTION identity_lookup(TEXT,BIGINT),identity_index_user(INTEGER),identity_register(JSONB),identity_customer_profile(BIGINT,INTEGER),identity_revoke(BIGINT),identity_reset_issue(BIGINT,TEXT),identity_reset_lookup(TEXT),identity_reset_apply(TEXT,TEXT) FROM PUBLIC;

CREATE FUNCTION identity_event(p_id BIGINT,p_action TEXT) RETURNS VOID
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
BEGIN
 IF p_action NOT IN ('LOGIN_EXITOSO','LOGIN_FALLIDO') THEN RAISE EXCEPTION 'Evento no permitido' USING ERRCODE='42501'; END IF;
 INSERT INTO public.auditoria_identidad(account_id,accion) VALUES(p_id,p_action);
END $$;
REVOKE ALL ON FUNCTION identity_event(BIGINT,TEXT) FROM PUBLIC;
