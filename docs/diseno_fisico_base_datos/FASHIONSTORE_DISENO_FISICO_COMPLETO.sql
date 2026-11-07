-- FASHIONSTORE: DISENO FISICO COMPLETO
-- Fuente: PostgreSQL 17 del servidor P2. Solo estructura, sin filas ni credenciales.
-- Aplicar conectado a una BASE VACIA, como administrador PostgreSQL.
-- No contiene CREATE DATABASE, DROP DATABASE ni DROP TABLE para reemplazar una instalación.
BEGIN;
-- Roles de propiedad y autorización; sin contraseñas. No altera roles existentes.
DO $roles$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='fashionstore_p2_app') THEN CREATE ROLE "fashionstore_p2_app" NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS; END IF; END $roles$;
DO $roles$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='fashionstore_p2_owner') THEN CREATE ROLE "fashionstore_p2_owner" NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS; END IF; END $roles$;
--
-- PostgreSQL database dump
--
-- Dumped from database version 17.11 (Debian 17.11-0+deb13u1)
-- Dumped by pg_dump version 17.11 (Debian 17.11-0+deb13u1)
SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;
--
-- Name: uuid-ossp; Type: EXTENSION; Schema: -; Owner: -
--
CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;
--
-- Name: EXTENSION "uuid-ossp"; Type: COMMENT; Schema: -; Owner: 
--
COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';
--
-- Name: actualizar_stock_por_movimiento(); Type: FUNCTION; Schema: public; Owner: fashionstore_p2_owner
--
CREATE FUNCTION public.actualizar_stock_por_movimiento() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
 INSERT INTO inventario(tenant_id,id_sucursal,id_variante_prenda,stock)
 VALUES(NEW.tenant_id,NEW.id_sucursal,NEW.id_variante_prenda,0)
 ON CONFLICT(id_sucursal,id_variante_prenda) DO NOTHING;
 IF NEW.tipo='Entrada' THEN
  UPDATE inventario SET stock=stock+NEW.cantidad WHERE tenant_id=NEW.tenant_id AND id_sucursal=NEW.id_sucursal AND id_variante_prenda=NEW.id_variante_prenda;
 ELSIF NEW.tipo='Salida' THEN
  UPDATE inventario SET stock=stock-NEW.cantidad WHERE tenant_id=NEW.tenant_id AND id_sucursal=NEW.id_sucursal AND id_variante_prenda=NEW.id_variante_prenda AND stock>=NEW.cantidad;
  IF NOT FOUND THEN RAISE EXCEPTION 'Stock insuficiente' USING ERRCODE='23514'; END IF;
 END IF;
 RETURN NEW;
END $$;
ALTER FUNCTION public.actualizar_stock_por_movimiento() OWNER TO fashionstore_p2_owner;
--
-- Name: audit_business_row(); Type: FUNCTION; Schema: public; Owner: fashionstore_p2_owner
--
CREATE FUNCTION public.audit_business_row() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
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
ALTER FUNCTION public.audit_business_row() OWNER TO fashionstore_p2_owner;
--
-- Name: bind_push_device(text); Type: FUNCTION; Schema: public; Owner: fashionstore_p2_owner
--
CREATE FUNCTION public.bind_push_device(value text) RETURNS void
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'public', 'pg_temp'
    AS $$
DECLARE tid INTEGER:=current_tenant(); uid INTEGER:=nullif(current_setting('app.user_id',true),'')::integer;
BEGIN
 IF tid IS NULL OR uid IS NULL OR length(value)<20 OR length(value)>4096 OR NOT EXISTS(SELECT 1 FROM usuario WHERE tenant_id=tid AND id_usuario=uid AND estado='Activo') THEN
  RAISE EXCEPTION 'Sesión o dispositivo no válido';
 END IF;
 PERFORM pg_advisory_xact_lock(hashtextextended(value,262026));
 DELETE FROM dispositivo_push WHERE token=value;
 INSERT INTO dispositivo_push(tenant_id,id_usuario,token) VALUES(tid,uid,value);
END $$;
ALTER FUNCTION public.bind_push_device(value text) OWNER TO fashionstore_p2_owner;
--
-- Name: branch_visible(integer); Type: FUNCTION; Schema: public; Owner: fashionstore_p2_owner
--
CREATE FUNCTION public.branch_visible(value integer) RETURNS boolean
    LANGUAGE sql STABLE
    AS $$
 SELECT COALESCE(current_setting('app.role',true),'') IN ('','Administrador','Cliente','Servicio push')
 OR EXISTS(SELECT 1 FROM usuario_sucursal WHERE id_usuario=nullif(current_setting('app.user_id',true),'')::integer AND id_sucursal=value AND tenant_id=current_tenant())
$$;
ALTER FUNCTION public.branch_visible(value integer) OWNER TO fashionstore_p2_owner;
--
-- Name: canonical_variant_colors(); Type: FUNCTION; Schema: public; Owner: fashionstore_p2_owner
--
CREATE FUNCTION public.canonical_variant_colors() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
 NEW.color_ids:=ARRAY(SELECT DISTINCT n FROM unnest(array_append(COALESCE(NEW.color_ids,'{}'::integer[]),NEW.id_color)) n ORDER BY n);
 IF cardinality(NEW.color_ids)>10 OR EXISTS(SELECT 1 FROM unnest(NEW.color_ids) n WHERE NOT EXISTS(SELECT 1 FROM color c WHERE c.tenant_id=NEW.tenant_id AND c.id_color=n)) THEN RAISE EXCEPTION 'Colores de variante no válidos para esta empresa' USING ERRCODE='23503'; END IF;
 RETURN NEW;
END $$;
ALTER FUNCTION public.canonical_variant_colors() OWNER TO fashionstore_p2_owner;
--
-- Name: check_branch_limit(); Type: FUNCTION; Schema: public; Owner: fashionstore_p2_owner
--
CREATE FUNCTION public.check_branch_limit() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE cap INTEGER; used INTEGER;
BEGIN
 IF NEW.activa AND (TG_OP='INSERT' OR NOT OLD.activa) THEN
  PERFORM 1 FROM empresa WHERE id_empresa=NEW.tenant_id FOR UPDATE;
  SELECT p.max_sucursales INTO cap FROM suscripcion s JOIN plan p USING(id_plan)
   WHERE s.tenant_id=NEW.tenant_id AND now() BETWEEN s.inicio AND s.vencimiento;
  IF cap IS NULL THEN RAISE EXCEPTION 'Suscripción no vigente' USING ERRCODE='23514'; END IF;
  SELECT count(*) INTO used FROM sucursal WHERE tenant_id=NEW.tenant_id AND activa;
  IF used>=cap THEN RAISE EXCEPTION 'Límite de sucursales del plan alcanzado' USING ERRCODE='23514'; END IF;
 END IF;
 RETURN NEW;
END $$;
ALTER FUNCTION public.check_branch_limit() OWNER TO fashionstore_p2_owner;
--
-- Name: current_tenant(); Type: FUNCTION; Schema: public; Owner: fashionstore_p2_owner
--
CREATE FUNCTION public.current_tenant() RETURNS integer
    LANGUAGE sql STABLE
    AS $$
 SELECT NULLIF(current_setting('app.tenant_id',true),'')::integer
$$;
ALTER FUNCTION public.current_tenant() OWNER TO fashionstore_p2_owner;
--
-- Name: identity_customer_profile(bigint, integer); Type: FUNCTION; Schema: public; Owner: fashionstore_p2_owner
--
CREATE FUNCTION public.identity_customer_profile(p_account bigint, p_tenant integer) RETURNS integer
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog', 'public'
    AS $$
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
ALTER FUNCTION public.identity_customer_profile(p_account bigint, p_tenant integer) OWNER TO fashionstore_p2_owner;
--
-- Name: identity_event(bigint, text); Type: FUNCTION; Schema: public; Owner: fashionstore_p2_owner
--
CREATE FUNCTION public.identity_event(p_id bigint, p_action text) RETURNS void
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog', 'public'
    AS $$
BEGIN
 IF p_action NOT IN ('LOGIN_EXITOSO','LOGIN_FALLIDO') THEN RAISE EXCEPTION 'Evento no permitido' USING ERRCODE='42501'; END IF;
 INSERT INTO public.auditoria_identidad(account_id,accion) VALUES(p_id,p_action);
END $$;
ALTER FUNCTION public.identity_event(p_id bigint, p_action text) OWNER TO fashionstore_p2_owner;
--
-- Name: identity_index_user(integer); Type: FUNCTION; Schema: public; Owner: fashionstore_p2_owner
--
CREATE FUNCTION public.identity_index_user(p_user integer) RETURNS bigint
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog', 'public'
    AS $$
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
ALTER FUNCTION public.identity_index_user(p_user integer) OWNER TO fashionstore_p2_owner;
--
-- Name: identity_lookup(text, bigint); Type: FUNCTION; Schema: public; Owner: fashionstore_p2_owner
--
CREATE FUNCTION public.identity_lookup(p_correo text DEFAULT NULL::text, p_id bigint DEFAULT NULL::bigint) RETURNS jsonb
    LANGUAGE sql SECURITY DEFINER
    SET search_path TO 'pg_catalog', 'public'
    AS $$
 SELECT to_jsonb(a)||jsonb_build_object('tenant_id',u.tenant_id,'id_usuario',u.id_usuario,'rol',r.nombre,'slug',e.slug,'empresa_activa',e.activa,'local_estado',u.estado,'local_version',u.token_version)
 FROM public.cuenta_global a LEFT JOIN public.usuario u ON u.account_id=a.id AND a.tipo<>'CLIENTE'
 LEFT JOIN public.rol r ON r.id_rol=u.id_role LEFT JOIN public.empresa e ON e.id_empresa=u.tenant_id
 WHERE (p_id IS NOT NULL AND a.id=p_id) OR (p_id IS NULL AND a.correo=lower(trim(p_correo))) LIMIT 1
$$;
ALTER FUNCTION public.identity_lookup(p_correo text, p_id bigint) OWNER TO fashionstore_p2_owner;
--
-- Name: identity_register(jsonb); Type: FUNCTION; Schema: public; Owner: fashionstore_p2_owner
--
CREATE FUNCTION public.identity_register(p_data jsonb) RETURNS bigint
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog', 'public'
    AS $$
DECLARE aid BIGINT; BEGIN
 INSERT INTO public.cuenta_global(correo,password_hash,nombre,apellido,telefono,ci,direccion_envio,correo_recuperacion,tipo)
 VALUES(lower(trim(p_data->>'correo')),p_data->>'password_hash',p_data->>'nombre',p_data->>'apellido',p_data->>'telefono',p_data->>'ci',p_data->>'direccion_envio',p_data->>'correo_recuperacion','CLIENTE') RETURNING id INTO aid;
 INSERT INTO public.auditoria_identidad(account_id,accion) VALUES(aid,'REGISTRO'); RETURN aid;
END $$;
ALTER FUNCTION public.identity_register(p_data jsonb) OWNER TO fashionstore_p2_owner;
--
-- Name: identity_reset_apply(text, text); Type: FUNCTION; Schema: public; Owner: fashionstore_p2_owner
--
CREATE FUNCTION public.identity_reset_apply(p_hash text, p_password_hash text) RETURNS boolean
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog', 'public'
    AS $$
DECLARE aid BIGINT; BEGIN
 SELECT t.account_id INTO aid FROM public.cuenta_recuperacion t JOIN public.cuenta_global a ON a.id=t.account_id WHERE t.token_hash=p_hash AND NOT t.usado AND t.expiracion>now() AND a.estado='Activo' FOR UPDATE OF t;
 IF aid IS NULL THEN RETURN false; END IF;
 UPDATE public.cuenta_global SET password_hash=p_password_hash,token_version=token_version+1 WHERE id=aid;
 UPDATE public.usuario SET password_hash=p_password_hash,token_version=token_version+1 WHERE account_id=aid;
 UPDATE public.cuenta_recuperacion SET usado=true WHERE account_id=aid;
 INSERT INTO public.auditoria_identidad(account_id,accion) VALUES(aid,'PASSWORD_RESTABLECIDA'); RETURN true;
END $$;
ALTER FUNCTION public.identity_reset_apply(p_hash text, p_password_hash text) OWNER TO fashionstore_p2_owner;
--
-- Name: identity_reset_issue(bigint, text); Type: FUNCTION; Schema: public; Owner: fashionstore_p2_owner
--
CREATE FUNCTION public.identity_reset_issue(p_id bigint, p_hash text) RETURNS void
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog', 'public'
    AS $$
BEGIN
 UPDATE public.cuenta_recuperacion SET usado=true WHERE account_id=p_id AND NOT usado;
 INSERT INTO public.cuenta_recuperacion(token_hash,account_id) VALUES(p_hash,p_id);
 INSERT INTO public.auditoria_identidad(account_id,accion) VALUES(p_id,'SOLICITUD_RECUPERACION');
END $$;
ALTER FUNCTION public.identity_reset_issue(p_id bigint, p_hash text) OWNER TO fashionstore_p2_owner;
--
-- Name: identity_reset_lookup(text); Type: FUNCTION; Schema: public; Owner: fashionstore_p2_owner
--
CREATE FUNCTION public.identity_reset_lookup(p_hash text) RETURNS jsonb
    LANGUAGE sql SECURITY DEFINER
    SET search_path TO 'pg_catalog', 'public'
    AS $$
 SELECT jsonb_build_object('id',a.id,'correo',a.correo,'valido',NOT t.usado AND t.expiracion>now() AND a.estado='Activo') FROM public.cuenta_recuperacion t JOIN public.cuenta_global a ON a.id=t.account_id WHERE token_hash=p_hash
$$;
ALTER FUNCTION public.identity_reset_lookup(p_hash text) OWNER TO fashionstore_p2_owner;
--
-- Name: identity_revoke(bigint); Type: FUNCTION; Schema: public; Owner: fashionstore_p2_owner
--
CREATE FUNCTION public.identity_revoke(p_id bigint) RETURNS void
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog', 'public'
    AS $$
BEGIN
 IF NULLIF(current_setting('app.account_id',true),'')::BIGINT IS DISTINCT FROM p_id THEN RAISE EXCEPTION 'Identidad no autorizada' USING ERRCODE='42501'; END IF;
 UPDATE public.cuenta_global SET token_version=token_version+1 WHERE id=p_id;
 INSERT INTO public.auditoria_identidad(account_id,accion) VALUES(p_id,'LOGOUT');
END $$;
ALTER FUNCTION public.identity_revoke(p_id bigint) OWNER TO fashionstore_p2_owner;
--
-- Name: own_customer(); Type: FUNCTION; Schema: public; Owner: fashionstore_p2_owner
--
CREATE FUNCTION public.own_customer() RETURNS integer
    LANGUAGE sql STABLE
    AS $$
 SELECT id_cliente FROM cliente WHERE tenant_id=current_tenant()
 AND correo=NULLIF(current_setting('app.email',true),'') LIMIT 1
$$;
ALTER FUNCTION public.own_customer() OWNER TO fashionstore_p2_owner;
--
-- Name: sync_variant_colors(); Type: FUNCTION; Schema: public; Owner: fashionstore_p2_owner
--
CREATE FUNCTION public.sync_variant_colors() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
 DELETE FROM variante_color WHERE tenant_id=NEW.tenant_id AND id_variante_prenda=NEW.id_variante_prenda;
 INSERT INTO variante_color(tenant_id,id_variante_prenda,id_color) SELECT NEW.tenant_id,NEW.id_variante_prenda,unnest(NEW.color_ids);
 RETURN NEW;
END $$;
ALTER FUNCTION public.sync_variant_colors() OWNER TO fashionstore_p2_owner;
--
-- Name: variant_color_label(integer); Type: FUNCTION; Schema: public; Owner: fashionstore_p2_owner
--
CREATE FUNCTION public.variant_color_label(variant integer) RETURNS text
    LANGUAGE sql STABLE
    AS $$
 SELECT string_agg(c.nombre,' / ' ORDER BY c.nombre) FROM variante_color vc JOIN color c USING(tenant_id,id_color) WHERE vc.id_variante_prenda=variant
$$;
ALTER FUNCTION public.variant_color_label(variant integer) OWNER TO fashionstore_p2_owner;
SET default_tablespace = '';
SET default_table_access_method = heap;
--
-- Name: ajuste_monetario; Type: TABLE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE TABLE public.ajuste_monetario (
    id_ajuste integer NOT NULL,
    tenant_id integer DEFAULT public.current_tenant() NOT NULL,
    id_cambio integer NOT NULL,
    tipo text NOT NULL,
    importe numeric(12,2) NOT NULL,
    origen text NOT NULL,
    referencia text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ajuste_monetario_importe_check CHECK ((importe > (0)::numeric)),
    CONSTRAINT ajuste_monetario_tipo_check CHECK ((tipo = ANY (ARRAY['Cobro'::text, 'Reembolso'::text])))
);
ALTER TABLE public.ajuste_monetario OWNER TO fashionstore_p2_owner;
--
-- Name: ajuste_monetario_id_ajuste_seq; Type: SEQUENCE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE SEQUENCE public.ajuste_monetario_id_ajuste_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE public.ajuste_monetario_id_ajuste_seq OWNER TO fashionstore_p2_owner;
--
-- Name: ajuste_monetario_id_ajuste_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fashionstore_p2_owner
--
ALTER SEQUENCE public.ajuste_monetario_id_ajuste_seq OWNED BY public.ajuste_monetario.id_ajuste;
--
-- Name: auditoria_identidad; Type: TABLE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE TABLE public.auditoria_identidad (
    id bigint NOT NULL,
    account_id bigint,
    accion text NOT NULL,
    fecha timestamp with time zone DEFAULT now() NOT NULL
);
ALTER TABLE public.auditoria_identidad OWNER TO fashionstore_p2_owner;
--
-- Name: auditoria_identidad_id_seq; Type: SEQUENCE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE SEQUENCE public.auditoria_identidad_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE public.auditoria_identidad_id_seq OWNER TO fashionstore_p2_owner;
--
-- Name: auditoria_identidad_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fashionstore_p2_owner
--
ALTER SEQUENCE public.auditoria_identidad_id_seq OWNED BY public.auditoria_identidad.id;
--
-- Name: bitacora; Type: TABLE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE TABLE public.bitacora (
    id_bitacora integer NOT NULL,
    id_usuario integer,
    accion character varying(100) NOT NULL,
    tabla_afectada character varying(100) NOT NULL,
    registro_id integer,
    detalle text,
    ip_address character varying(45),
    fecha timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    tenant_id integer DEFAULT public.current_tenant() NOT NULL
);
ALTER TABLE public.bitacora OWNER TO fashionstore_p2_owner;
--
-- Name: bitacora_id_bitacora_seq; Type: SEQUENCE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE SEQUENCE public.bitacora_id_bitacora_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE public.bitacora_id_bitacora_seq OWNER TO fashionstore_p2_owner;
--
-- Name: bitacora_id_bitacora_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fashionstore_p2_owner
--
ALTER SEQUENCE public.bitacora_id_bitacora_seq OWNED BY public.bitacora.id_bitacora;
--
-- Name: cambio; Type: TABLE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE TABLE public.cambio (
    id_cambio integer NOT NULL,
    tenant_id integer DEFAULT public.current_tenant() NOT NULL,
    id_venta integer NOT NULL,
    id_cliente integer NOT NULL,
    id_sucursal integer NOT NULL,
    id_variante_original integer NOT NULL,
    cantidad integer NOT NULL,
    motivo text NOT NULL,
    estado text DEFAULT 'Solicitado'::text NOT NULL,
    credito numeric(12,2) NOT NULL,
    diferencia numeric(12,2),
    id_reserva_reemplazo integer,
    recibido_at timestamp with time zone,
    entregado_at timestamp with time zone,
    cancelar boolean DEFAULT false NOT NULL,
    pago_diferencia jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT cambio_cantidad_check CHECK ((cantidad > 0)),
    CONSTRAINT cambio_credito_check CHECK ((credito >= (0)::numeric)),
    CONSTRAINT cambio_estado_check CHECK ((estado = ANY (ARRAY['Solicitado'::text, 'Recibido'::text, 'PagoPendiente'::text, 'ReembolsoPendiente'::text, 'Listo'::text, 'Entregado'::text, 'Reembolsado'::text, 'Cancelado'::text, 'Rechazado'::text])))
);
ALTER TABLE public.cambio OWNER TO fashionstore_p2_owner;
--
-- Name: cambio_id_cambio_seq; Type: SEQUENCE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE SEQUENCE public.cambio_id_cambio_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE public.cambio_id_cambio_seq OWNER TO fashionstore_p2_owner;
--
-- Name: cambio_id_cambio_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fashionstore_p2_owner
--
ALTER SEQUENCE public.cambio_id_cambio_seq OWNED BY public.cambio.id_cambio;
--
-- Name: categoria; Type: TABLE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE TABLE public.categoria (
    id_categoria integer NOT NULL,
    nombre character varying(100) NOT NULL,
    descripcion character varying(255),
    id_categoria_padre integer,
    estado character varying(20) DEFAULT 'Activo'::character varying,
    tenant_id integer DEFAULT public.current_tenant() NOT NULL,
    CONSTRAINT categoria_estado_check CHECK (((estado)::text = ANY ((ARRAY['Activo'::character varying, 'Inactivo'::character varying])::text[])))
);
ALTER TABLE public.categoria OWNER TO fashionstore_p2_owner;
--
-- Name: categoria_id_categoria_seq; Type: SEQUENCE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE SEQUENCE public.categoria_id_categoria_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE public.categoria_id_categoria_seq OWNER TO fashionstore_p2_owner;
--
-- Name: categoria_id_categoria_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fashionstore_p2_owner
--
ALTER SEQUENCE public.categoria_id_categoria_seq OWNED BY public.categoria.id_categoria;
--
-- Name: ciudad; Type: TABLE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE TABLE public.ciudad (
    id_ciudad integer NOT NULL,
    nombre character varying(100) NOT NULL,
    tenant_id integer DEFAULT public.current_tenant() NOT NULL
);
ALTER TABLE public.ciudad OWNER TO fashionstore_p2_owner;
--
-- Name: ciudad_id_ciudad_seq; Type: SEQUENCE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE SEQUENCE public.ciudad_id_ciudad_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE public.ciudad_id_ciudad_seq OWNER TO fashionstore_p2_owner;
--
-- Name: ciudad_id_ciudad_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fashionstore_p2_owner
--
ALTER SEQUENCE public.ciudad_id_ciudad_seq OWNED BY public.ciudad.id_ciudad;
--
-- Name: cliente; Type: TABLE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE TABLE public.cliente (
    id_cliente integer NOT NULL,
    ci character varying(20) NOT NULL,
    nombre_completo character varying(200) NOT NULL,
    telefono character varying(20),
    correo character varying(150),
    direccion_envio character varying(255),
    estado character varying(20) DEFAULT 'Activo'::character varying,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    tenant_id integer DEFAULT public.current_tenant() NOT NULL,
    CONSTRAINT cliente_estado_check CHECK (((estado)::text = ANY ((ARRAY['Activo'::character varying, 'Inactivo'::character varying])::text[])))
);
ALTER TABLE public.cliente OWNER TO fashionstore_p2_owner;
--
-- Name: cliente_id_cliente_seq; Type: SEQUENCE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE SEQUENCE public.cliente_id_cliente_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE public.cliente_id_cliente_seq OWNER TO fashionstore_p2_owner;
--
-- Name: cliente_id_cliente_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fashionstore_p2_owner
--
ALTER SEQUENCE public.cliente_id_cliente_seq OWNED BY public.cliente.id_cliente;
--
-- Name: color; Type: TABLE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE TABLE public.color (
    id_color integer NOT NULL,
    nombre character varying(50) NOT NULL,
    codigo_hex character varying(10),
    tenant_id integer DEFAULT public.current_tenant() NOT NULL
);
ALTER TABLE public.color OWNER TO fashionstore_p2_owner;
--
-- Name: color_id_color_seq; Type: SEQUENCE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE SEQUENCE public.color_id_color_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE public.color_id_color_seq OWNER TO fashionstore_p2_owner;
--
-- Name: color_id_color_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fashionstore_p2_owner
--
ALTER SEQUENCE public.color_id_color_seq OWNED BY public.color.id_color;
--
-- Name: compra; Type: TABLE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE TABLE public.compra (
    id_compra integer NOT NULL,
    id_proveedor integer,
    id_sucursal integer,
    fecha timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    total numeric(12,2) DEFAULT 0.00 NOT NULL,
    id_usuario integer,
    tenant_id integer DEFAULT public.current_tenant() NOT NULL
);
ALTER TABLE public.compra OWNER TO fashionstore_p2_owner;
--
-- Name: compra_id_compra_seq; Type: SEQUENCE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE SEQUENCE public.compra_id_compra_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE public.compra_id_compra_seq OWNER TO fashionstore_p2_owner;
--
-- Name: compra_id_compra_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fashionstore_p2_owner
--
ALTER SEQUENCE public.compra_id_compra_seq OWNED BY public.compra.id_compra;
--
-- Name: comprobante; Type: TABLE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE TABLE public.comprobante (
    id_comprobante integer NOT NULL,
    id_venta integer,
    numero_comprobante character varying(50) NOT NULL,
    nit_ci character varying(20) NOT NULL,
    razon_social character varying(150) NOT NULL,
    fecha_emision timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    url_pdf character varying(255),
    tenant_id integer DEFAULT public.current_tenant() NOT NULL
);
ALTER TABLE public.comprobante OWNER TO fashionstore_p2_owner;
--
-- Name: comprobante_id_comprobante_seq; Type: SEQUENCE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE SEQUENCE public.comprobante_id_comprobante_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE public.comprobante_id_comprobante_seq OWNER TO fashionstore_p2_owner;
--
-- Name: comprobante_id_comprobante_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fashionstore_p2_owner
--
ALTER SEQUENCE public.comprobante_id_comprobante_seq OWNED BY public.comprobante.id_comprobante;
--
-- Name: cuenta_global; Type: TABLE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE TABLE public.cuenta_global (
    id bigint NOT NULL,
    correo text NOT NULL,
    password_hash text NOT NULL,
    nombre text NOT NULL,
    apellido text DEFAULT ''::text NOT NULL,
    telefono text,
    ci text,
    direccion_envio text,
    correo_recuperacion text,
    tipo text NOT NULL,
    estado text DEFAULT 'Activo'::text NOT NULL,
    token_version integer DEFAULT 0 NOT NULL,
    creada timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT cuenta_global_correo_check CHECK ((correo = lower(TRIM(BOTH FROM correo)))),
    CONSTRAINT cuenta_global_estado_check CHECK ((estado = ANY (ARRAY['Activo'::text, 'Inactivo'::text]))),
    CONSTRAINT cuenta_global_tipo_check CHECK ((tipo = ANY (ARRAY['CLIENTE'::text, 'PERSONAL'::text, 'PLATAFORMA'::text])))
);
ALTER TABLE public.cuenta_global OWNER TO fashionstore_p2_owner;
--
-- Name: cuenta_global_id_seq; Type: SEQUENCE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE SEQUENCE public.cuenta_global_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE public.cuenta_global_id_seq OWNER TO fashionstore_p2_owner;
--
-- Name: cuenta_global_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fashionstore_p2_owner
--
ALTER SEQUENCE public.cuenta_global_id_seq OWNED BY public.cuenta_global.id;
--
-- Name: cuenta_recuperacion; Type: TABLE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE TABLE public.cuenta_recuperacion (
    token_hash text NOT NULL,
    account_id bigint NOT NULL,
    expiracion timestamp with time zone DEFAULT (now() + '00:30:00'::interval) NOT NULL,
    usado boolean DEFAULT false NOT NULL
);
ALTER TABLE public.cuenta_recuperacion OWNER TO fashionstore_p2_owner;
--
-- Name: detalle_compra; Type: TABLE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE TABLE public.detalle_compra (
    id_compra integer NOT NULL,
    id_variante_prenda integer NOT NULL,
    cantidad integer NOT NULL,
    costo_unitario numeric(10,2) NOT NULL,
    tenant_id integer DEFAULT public.current_tenant() NOT NULL,
    CONSTRAINT detalle_compra_cantidad_check CHECK ((cantidad > 0)),
    CONSTRAINT detalle_compra_costo_unitario_check CHECK ((costo_unitario >= (0)::numeric))
);
ALTER TABLE public.detalle_compra OWNER TO fashionstore_p2_owner;
--
-- Name: detalle_reserva; Type: TABLE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE TABLE public.detalle_reserva (
    id_reserva integer NOT NULL,
    id_variante_prenda integer NOT NULL,
    cantidad integer DEFAULT 1 NOT NULL,
    precio_unitario numeric(10,2) NOT NULL,
    tenant_id integer DEFAULT public.current_tenant() NOT NULL,
    CONSTRAINT detalle_reserva_cantidad_check CHECK ((cantidad > 0))
);
ALTER TABLE public.detalle_reserva OWNER TO fashionstore_p2_owner;
--
-- Name: detalle_venta; Type: TABLE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE TABLE public.detalle_venta (
    id_venta integer NOT NULL,
    id_variante_prenda integer NOT NULL,
    cantidad integer NOT NULL,
    precio_unitario numeric(10,2) NOT NULL,
    subtotal numeric(10,2) NOT NULL,
    tenant_id integer DEFAULT public.current_tenant() NOT NULL,
    CONSTRAINT detalle_venta_cantidad_check CHECK ((cantidad > 0))
);
ALTER TABLE public.detalle_venta OWNER TO fashionstore_p2_owner;
--
-- Name: dispositivo_push; Type: TABLE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE TABLE public.dispositivo_push (
    tenant_id integer DEFAULT public.current_tenant() NOT NULL,
    id_usuario integer NOT NULL,
    token text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);
ALTER TABLE public.dispositivo_push OWNER TO fashionstore_p2_owner;
--
-- Name: empresa; Type: TABLE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE TABLE public.empresa (
    id_empresa integer NOT NULL,
    slug text NOT NULL,
    nombre text NOT NULL,
    activa boolean DEFAULT true NOT NULL,
    plataforma boolean DEFAULT false NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT empresa_slug_check CHECK ((slug ~ '^[a-z0-9][a-z0-9-]{1,60}$'::text))
);
ALTER TABLE public.empresa OWNER TO fashionstore_p2_owner;
--
-- Name: empresa_id_empresa_seq; Type: SEQUENCE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE SEQUENCE public.empresa_id_empresa_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE public.empresa_id_empresa_seq OWNER TO fashionstore_p2_owner;
--
-- Name: empresa_id_empresa_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fashionstore_p2_owner
--
ALTER SEQUENCE public.empresa_id_empresa_seq OWNED BY public.empresa.id_empresa;
--
-- Name: imagen_prenda; Type: TABLE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE TABLE public.imagen_prenda (
    id_imagen integer NOT NULL,
    id_prenda integer,
    url_imagen character varying(255) NOT NULL,
    es_principal boolean DEFAULT false,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    tenant_id integer DEFAULT public.current_tenant() NOT NULL
);
ALTER TABLE public.imagen_prenda OWNER TO fashionstore_p2_owner;
--
-- Name: imagen_prenda_id_imagen_seq; Type: SEQUENCE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE SEQUENCE public.imagen_prenda_id_imagen_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE public.imagen_prenda_id_imagen_seq OWNER TO fashionstore_p2_owner;
--
-- Name: imagen_prenda_id_imagen_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fashionstore_p2_owner
--
ALTER SEQUENCE public.imagen_prenda_id_imagen_seq OWNED BY public.imagen_prenda.id_imagen;
--
-- Name: inventario; Type: TABLE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE TABLE public.inventario (
    id_sucursal integer NOT NULL,
    id_variante_prenda integer NOT NULL,
    stock integer DEFAULT 0 NOT NULL,
    tenant_id integer DEFAULT public.current_tenant() NOT NULL,
    CONSTRAINT inventario_stock_check CHECK ((stock >= 0))
);
ALTER TABLE public.inventario OWNER TO fashionstore_p2_owner;
--
-- Name: retencion; Type: TABLE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE TABLE public.retencion (
    tenant_id integer DEFAULT public.current_tenant() NOT NULL,
    id_reserva integer NOT NULL,
    id_sucursal integer NOT NULL,
    id_variante_prenda integer NOT NULL,
    cantidad integer NOT NULL,
    vence timestamp with time zone NOT NULL,
    CONSTRAINT retencion_cantidad_check CHECK ((cantidad > 0))
);
ALTER TABLE public.retencion OWNER TO fashionstore_p2_owner;
--
-- Name: inventario_catalogo; Type: VIEW; Schema: public; Owner: fashionstore_p2_owner
--
CREATE VIEW public.inventario_catalogo WITH (security_invoker='true') AS
 SELECT tenant_id,
    id_sucursal,
    id_variante_prenda,
    (GREATEST((stock - COALESCE(( SELECT sum(r.cantidad) AS sum
           FROM public.retencion r
          WHERE ((r.tenant_id = i.tenant_id) AND (r.id_sucursal = i.id_sucursal) AND (r.id_variante_prenda = i.id_variante_prenda) AND (r.vence > now()))), (0)::bigint)), (0)::bigint))::integer AS stock
   FROM public.inventario i;
ALTER VIEW public.inventario_catalogo OWNER TO fashionstore_p2_owner;
--
-- Name: movimiento_inventario; Type: TABLE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE TABLE public.movimiento_inventario (
    id_movimiento integer NOT NULL,
    id_sucursal integer,
    id_variante_prenda integer,
    tipo character varying(20) NOT NULL,
    cantidad integer NOT NULL,
    motivo character varying(255) NOT NULL,
    id_usuario integer,
    fecha timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    tenant_id integer DEFAULT public.current_tenant() NOT NULL,
    CONSTRAINT movimiento_inventario_cantidad_check CHECK ((cantidad > 0)),
    CONSTRAINT movimiento_inventario_tipo_check CHECK (((tipo)::text = ANY ((ARRAY['Entrada'::character varying, 'Salida'::character varying, 'Traspaso'::character varying])::text[])))
);
ALTER TABLE public.movimiento_inventario OWNER TO fashionstore_p2_owner;
--
-- Name: movimiento_inventario_id_movimiento_seq; Type: SEQUENCE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE SEQUENCE public.movimiento_inventario_id_movimiento_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE public.movimiento_inventario_id_movimiento_seq OWNER TO fashionstore_p2_owner;
--
-- Name: movimiento_inventario_id_movimiento_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fashionstore_p2_owner
--
ALTER SEQUENCE public.movimiento_inventario_id_movimiento_seq OWNED BY public.movimiento_inventario.id_movimiento;
--
-- Name: notificacion; Type: TABLE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE TABLE public.notificacion (
    id_notificacion integer NOT NULL,
    tenant_id integer DEFAULT public.current_tenant() NOT NULL,
    id_cliente integer NOT NULL,
    titulo text NOT NULL,
    mensaje text NOT NULL,
    id_cambio integer,
    leida boolean DEFAULT false NOT NULL,
    push_enviado boolean DEFAULT false NOT NULL,
    intentos integer DEFAULT 0 NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);
ALTER TABLE public.notificacion OWNER TO fashionstore_p2_owner;
--
-- Name: notificacion_id_notificacion_seq; Type: SEQUENCE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE SEQUENCE public.notificacion_id_notificacion_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE public.notificacion_id_notificacion_seq OWNER TO fashionstore_p2_owner;
--
-- Name: notificacion_id_notificacion_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fashionstore_p2_owner
--
ALTER SEQUENCE public.notificacion_id_notificacion_seq OWNED BY public.notificacion.id_notificacion;
--
-- Name: operacion_sync; Type: TABLE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE TABLE public.operacion_sync (
    tenant_id integer DEFAULT public.current_tenant() NOT NULL,
    operation_id uuid NOT NULL,
    author_id integer NOT NULL,
    branch_id integer,
    device_id uuid NOT NULL,
    kind text NOT NULL,
    payload_hash text NOT NULL,
    envelope jsonb NOT NULL,
    state text NOT NULL,
    result jsonb NOT NULL,
    original_operation uuid,
    resolved_by integer,
    resolution text,
    compensation numeric(12,2),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    resolved_at timestamp with time zone,
    CONSTRAINT operacion_sync_check CHECK (((branch_id IS NOT NULL) OR (state = 'RECHAZADA'::text))),
    CONSTRAINT operacion_sync_kind_check CHECK ((kind = ANY (ARRAY['venta'::text, 'reserva'::text]))),
    CONSTRAINT operacion_sync_state_check CHECK ((state = ANY (ARRAY['CONFIRMADA'::text, 'RECHAZADA'::text, 'EN_CONFLICTO'::text])))
);
ALTER TABLE public.operacion_sync OWNER TO fashionstore_p2_owner;
--
-- Name: pago_transaccion; Type: TABLE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE TABLE public.pago_transaccion (
    id_pago integer NOT NULL,
    id_venta integer,
    pasarela character varying(50) NOT NULL,
    transaccion_id character varying(100) NOT NULL,
    monto numeric(10,2) NOT NULL,
    estado_pago character varying(50) NOT NULL,
    payload_respuesta jsonb,
    fecha timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    tenant_id integer DEFAULT public.current_tenant() NOT NULL,
    id_reserva integer,
    url_pago text,
    vence timestamp with time zone
);
ALTER TABLE public.pago_transaccion OWNER TO fashionstore_p2_owner;
--
-- Name: pago_transaccion_id_pago_seq; Type: SEQUENCE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE SEQUENCE public.pago_transaccion_id_pago_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE public.pago_transaccion_id_pago_seq OWNER TO fashionstore_p2_owner;
--
-- Name: pago_transaccion_id_pago_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fashionstore_p2_owner
--
ALTER SEQUENCE public.pago_transaccion_id_pago_seq OWNED BY public.pago_transaccion.id_pago;
--
-- Name: permiso; Type: TABLE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE TABLE public.permiso (
    id_permiso integer NOT NULL,
    nombre character varying(100) NOT NULL,
    codigo character varying(100) NOT NULL,
    modulo character varying(100),
    descripcion character varying(255)
);
ALTER TABLE public.permiso OWNER TO fashionstore_p2_owner;
--
-- Name: permiso_id_permiso_seq; Type: SEQUENCE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE SEQUENCE public.permiso_id_permiso_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE public.permiso_id_permiso_seq OWNER TO fashionstore_p2_owner;
--
-- Name: permiso_id_permiso_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fashionstore_p2_owner
--
ALTER SEQUENCE public.permiso_id_permiso_seq OWNED BY public.permiso.id_permiso;
--
-- Name: plan; Type: TABLE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE TABLE public.plan (
    id_plan integer NOT NULL,
    nombre text NOT NULL,
    max_sucursales integer NOT NULL,
    reportes_ia boolean DEFAULT false NOT NULL,
    CONSTRAINT plan_max_sucursales_check CHECK ((max_sucursales > 0))
);
ALTER TABLE public.plan OWNER TO fashionstore_p2_owner;
--
-- Name: plan_id_plan_seq; Type: SEQUENCE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE SEQUENCE public.plan_id_plan_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE public.plan_id_plan_seq OWNER TO fashionstore_p2_owner;
--
-- Name: plan_id_plan_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fashionstore_p2_owner
--
ALTER SEQUENCE public.plan_id_plan_seq OWNED BY public.plan.id_plan;
--
-- Name: prenda; Type: TABLE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE TABLE public.prenda (
    id_prenda integer NOT NULL,
    sku character varying(50) NOT NULL,
    nombre character varying(150) NOT NULL,
    descripcion text,
    marca character varying(100) DEFAULT 'FashionStore'::character varying,
    genero character varying(20) DEFAULT 'Unisex'::character varying,
    precio_base numeric(10,2) NOT NULL,
    id_categoria integer,
    id_temporada integer,
    estado character varying(20) DEFAULT 'Activo'::character varying,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    tenant_id integer DEFAULT public.current_tenant() NOT NULL,
    material text,
    medidas text,
    precio_mayorista numeric(10,2),
    umbral_mayorista integer DEFAULT 6 NOT NULL,
    precio_oferta numeric(10,2),
    oferta_inicio date,
    oferta_fin date,
    admite_cambio boolean DEFAULT true NOT NULL,
    CONSTRAINT offer_dates CHECK (((oferta_fin IS NULL) OR (oferta_inicio IS NULL) OR (oferta_fin >= oferta_inicio))),
    CONSTRAINT prenda_estado_check CHECK (((estado)::text = ANY ((ARRAY['Activo'::character varying, 'Inactivo'::character varying, 'Borrador'::character varying])::text[]))),
    CONSTRAINT prenda_genero_check CHECK (((genero)::text = ANY ((ARRAY['Dama'::character varying, 'Caballero'::character varying, 'Unisex'::character varying, 'Nino'::character varying])::text[]))),
    CONSTRAINT prenda_precio_base_check CHECK ((precio_base >= (0)::numeric)),
    CONSTRAINT prenda_precio_mayorista_check CHECK ((precio_mayorista >= (0)::numeric)),
    CONSTRAINT prenda_precio_oferta_check CHECK ((precio_oferta >= (0)::numeric)),
    CONSTRAINT prenda_umbral_mayorista_check CHECK ((umbral_mayorista > 0))
);
ALTER TABLE public.prenda OWNER TO fashionstore_p2_owner;
--
-- Name: prenda_id_prenda_seq; Type: SEQUENCE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE SEQUENCE public.prenda_id_prenda_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE public.prenda_id_prenda_seq OWNER TO fashionstore_p2_owner;
--
-- Name: prenda_id_prenda_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fashionstore_p2_owner
--
ALTER SEQUENCE public.prenda_id_prenda_seq OWNED BY public.prenda.id_prenda;
--
-- Name: proveedor; Type: TABLE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE TABLE public.proveedor (
    id_proveedor integer NOT NULL,
    nit character varying(30) NOT NULL,
    razon_social character varying(150) NOT NULL,
    contacto character varying(100),
    telefono character varying(20),
    correo character varying(150),
    direccion character varying(255),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    tenant_id integer DEFAULT public.current_tenant() NOT NULL
);
ALTER TABLE public.proveedor OWNER TO fashionstore_p2_owner;
--
-- Name: proveedor_id_proveedor_seq; Type: SEQUENCE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE SEQUENCE public.proveedor_id_proveedor_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE public.proveedor_id_proveedor_seq OWNER TO fashionstore_p2_owner;
--
-- Name: proveedor_id_proveedor_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fashionstore_p2_owner
--
ALTER SEQUENCE public.proveedor_id_proveedor_seq OWNED BY public.proveedor.id_proveedor;
--
-- Name: push_entrega; Type: TABLE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE TABLE public.push_entrega (
    tenant_id integer DEFAULT public.current_tenant() NOT NULL,
    id_notificacion integer NOT NULL,
    token_hash text NOT NULL,
    enviado boolean DEFAULT false NOT NULL,
    intentos integer DEFAULT 0 NOT NULL,
    proximo_intento timestamp with time zone DEFAULT now() NOT NULL,
    ultimo_estado text
);
ALTER TABLE public.push_entrega OWNER TO fashionstore_p2_owner;
--
-- Name: reporte_resultado; Type: TABLE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE TABLE public.reporte_resultado (
    id uuid NOT NULL,
    tenant_id bigint DEFAULT (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::bigint NOT NULL,
    author_id integer NOT NULL,
    filters jsonb NOT NULL,
    result jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    expires_at timestamp with time zone DEFAULT (now() + '24:00:00'::interval) NOT NULL
);
ALTER TABLE ONLY public.reporte_resultado FORCE ROW LEVEL SECURITY;
ALTER TABLE public.reporte_resultado OWNER TO fashionstore_p2_owner;
--
-- Name: reserva; Type: TABLE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE TABLE public.reserva (
    id_reserva integer NOT NULL,
    id_cliente integer,
    id_sucursal integer,
    fecha_reserva timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    fecha_limite timestamp without time zone NOT NULL,
    estado character varying(30) DEFAULT 'Pendiente'::character varying,
    total numeric(10,2) DEFAULT 0.00 NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    tenant_id integer DEFAULT public.current_tenant() NOT NULL,
    checkout_generation integer DEFAULT 1 NOT NULL,
    CONSTRAINT reserva_estado_check CHECK (((estado)::text = ANY ((ARRAY['Pendiente'::character varying, 'Preparado'::character varying, 'Atendido'::character varying, 'Cancelado'::character varying])::text[])))
);
ALTER TABLE public.reserva OWNER TO fashionstore_p2_owner;
--
-- Name: reserva_id_reserva_seq; Type: SEQUENCE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE SEQUENCE public.reserva_id_reserva_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE public.reserva_id_reserva_seq OWNER TO fashionstore_p2_owner;
--
-- Name: reserva_id_reserva_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fashionstore_p2_owner
--
ALTER SEQUENCE public.reserva_id_reserva_seq OWNED BY public.reserva.id_reserva;
--
-- Name: rol; Type: TABLE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE TABLE public.rol (
    id_rol integer NOT NULL,
    nombre character varying(50) NOT NULL,
    descripcion character varying(255),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    tenant_id integer DEFAULT public.current_tenant() NOT NULL
);
ALTER TABLE public.rol OWNER TO fashionstore_p2_owner;
--
-- Name: rol_id_rol_seq; Type: SEQUENCE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE SEQUENCE public.rol_id_rol_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE public.rol_id_rol_seq OWNER TO fashionstore_p2_owner;
--
-- Name: rol_id_rol_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fashionstore_p2_owner
--
ALTER SEQUENCE public.rol_id_rol_seq OWNED BY public.rol.id_rol;
--
-- Name: rol_permiso; Type: TABLE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE TABLE public.rol_permiso (
    id_rol integer NOT NULL,
    id_permiso integer NOT NULL,
    tenant_id integer DEFAULT public.current_tenant() NOT NULL
);
ALTER TABLE public.rol_permiso OWNER TO fashionstore_p2_owner;
--
-- Name: schema_migrations; Type: TABLE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE TABLE public.schema_migrations (
    version text NOT NULL,
    checksum text NOT NULL,
    applied_at timestamp with time zone DEFAULT now() NOT NULL
);
ALTER TABLE public.schema_migrations OWNER TO fashionstore_p2_owner;
--
-- Name: stripe_event; Type: TABLE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE TABLE public.stripe_event (
    tenant_id integer DEFAULT public.current_tenant() NOT NULL,
    event_id text NOT NULL,
    event_type text NOT NULL,
    result jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);
ALTER TABLE public.stripe_event OWNER TO fashionstore_p2_owner;
--
-- Name: sucursal; Type: TABLE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE TABLE public.sucursal (
    id_sucursal integer NOT NULL,
    nombre character varying(100) NOT NULL,
    direccion character varying(255) NOT NULL,
    telefono character varying(20),
    id_ciudad integer,
    id_encargado integer,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    tenant_id integer DEFAULT public.current_tenant() NOT NULL,
    activa boolean DEFAULT true NOT NULL
);
ALTER TABLE public.sucursal OWNER TO fashionstore_p2_owner;
--
-- Name: sucursal_id_sucursal_seq; Type: SEQUENCE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE SEQUENCE public.sucursal_id_sucursal_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE public.sucursal_id_sucursal_seq OWNER TO fashionstore_p2_owner;
--
-- Name: sucursal_id_sucursal_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fashionstore_p2_owner
--
ALTER SEQUENCE public.sucursal_id_sucursal_seq OWNED BY public.sucursal.id_sucursal;
--
-- Name: suscripcion; Type: TABLE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE TABLE public.suscripcion (
    id_suscripcion integer NOT NULL,
    tenant_id integer NOT NULL,
    id_plan integer NOT NULL,
    inicio timestamp with time zone NOT NULL,
    vencimiento timestamp with time zone NOT NULL,
    CONSTRAINT suscripcion_check CHECK ((vencimiento > inicio))
);
ALTER TABLE public.suscripcion OWNER TO fashionstore_p2_owner;
--
-- Name: suscripcion_id_suscripcion_seq; Type: SEQUENCE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE SEQUENCE public.suscripcion_id_suscripcion_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE public.suscripcion_id_suscripcion_seq OWNER TO fashionstore_p2_owner;
--
-- Name: suscripcion_id_suscripcion_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fashionstore_p2_owner
--
ALTER SEQUENCE public.suscripcion_id_suscripcion_seq OWNED BY public.suscripcion.id_suscripcion;
--
-- Name: talla; Type: TABLE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE TABLE public.talla (
    id_talla integer NOT NULL,
    nombre character varying(10) NOT NULL,
    descripcion character varying(50),
    tenant_id integer DEFAULT public.current_tenant() NOT NULL
);
ALTER TABLE public.talla OWNER TO fashionstore_p2_owner;
--
-- Name: talla_id_talla_seq; Type: SEQUENCE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE SEQUENCE public.talla_id_talla_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE public.talla_id_talla_seq OWNER TO fashionstore_p2_owner;
--
-- Name: talla_id_talla_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fashionstore_p2_owner
--
ALTER SEQUENCE public.talla_id_talla_seq OWNED BY public.talla.id_talla;
--
-- Name: temporada; Type: TABLE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE TABLE public.temporada (
    id_temporada integer NOT NULL,
    nombre character varying(100) NOT NULL,
    descripcion character varying(255),
    fecha_inicio date,
    fecha_fin date,
    tenant_id integer DEFAULT public.current_tenant() NOT NULL,
    estado boolean DEFAULT true NOT NULL,
    created_at timestamp without time zone DEFAULT now()
);
ALTER TABLE public.temporada OWNER TO fashionstore_p2_owner;
--
-- Name: temporada_id_temporada_seq; Type: SEQUENCE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE SEQUENCE public.temporada_id_temporada_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE public.temporada_id_temporada_seq OWNER TO fashionstore_p2_owner;
--
-- Name: temporada_id_temporada_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fashionstore_p2_owner
--
ALTER SEQUENCE public.temporada_id_temporada_seq OWNED BY public.temporada.id_temporada;
--
-- Name: usuario; Type: TABLE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE TABLE public.usuario (
    id_usuario integer NOT NULL,
    nombre character varying(100) NOT NULL,
    apellido character varying(100) NOT NULL,
    correo character varying(150) NOT NULL,
    password_hash character varying(255) NOT NULL,
    telefono character varying(20),
    estado character varying(20) DEFAULT 'Activo'::character varying,
    id_role integer,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    tenant_id integer DEFAULT public.current_tenant() NOT NULL,
    token_version integer DEFAULT 0 NOT NULL,
    account_id bigint,
    CONSTRAINT usuario_estado_check CHECK (((estado)::text = ANY ((ARRAY['Activo'::character varying, 'Inactivo'::character varying])::text[])))
);
ALTER TABLE public.usuario OWNER TO fashionstore_p2_owner;
--
-- Name: usuario_id_usuario_seq; Type: SEQUENCE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE SEQUENCE public.usuario_id_usuario_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE public.usuario_id_usuario_seq OWNER TO fashionstore_p2_owner;
--
-- Name: usuario_id_usuario_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fashionstore_p2_owner
--
ALTER SEQUENCE public.usuario_id_usuario_seq OWNED BY public.usuario.id_usuario;
--
-- Name: usuario_sucursal; Type: TABLE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE TABLE public.usuario_sucursal (
    tenant_id integer DEFAULT public.current_tenant() NOT NULL,
    id_usuario integer NOT NULL,
    id_sucursal integer NOT NULL
);
ALTER TABLE public.usuario_sucursal OWNER TO fashionstore_p2_owner;
--
-- Name: usuario_token; Type: TABLE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE TABLE public.usuario_token (
    id_token integer NOT NULL,
    id_usuario integer,
    token_recuperacion character varying(255),
    expiracion timestamp without time zone,
    usado boolean DEFAULT false,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    tenant_id integer DEFAULT public.current_tenant() NOT NULL
);
ALTER TABLE public.usuario_token OWNER TO fashionstore_p2_owner;
--
-- Name: usuario_token_id_token_seq; Type: SEQUENCE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE SEQUENCE public.usuario_token_id_token_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE public.usuario_token_id_token_seq OWNER TO fashionstore_p2_owner;
--
-- Name: usuario_token_id_token_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fashionstore_p2_owner
--
ALTER SEQUENCE public.usuario_token_id_token_seq OWNED BY public.usuario_token.id_token;
--
-- Name: variante_color; Type: TABLE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE TABLE public.variante_color (
    tenant_id integer DEFAULT public.current_tenant() NOT NULL,
    id_variante_prenda integer NOT NULL,
    id_color integer NOT NULL
);
ALTER TABLE public.variante_color OWNER TO fashionstore_p2_owner;
--
-- Name: variante_prenda; Type: TABLE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE TABLE public.variante_prenda (
    id_variante_prenda integer NOT NULL,
    id_prenda integer,
    id_talla integer,
    id_color integer,
    sku_variante character varying(100) NOT NULL,
    precio_adicional numeric(10,2) DEFAULT 0.00,
    tenant_id integer DEFAULT public.current_tenant() NOT NULL,
    color_ids integer[] DEFAULT '{}'::integer[] NOT NULL
);
ALTER TABLE public.variante_prenda OWNER TO fashionstore_p2_owner;
--
-- Name: variante_prenda_id_variante_prenda_seq; Type: SEQUENCE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE SEQUENCE public.variante_prenda_id_variante_prenda_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE public.variante_prenda_id_variante_prenda_seq OWNER TO fashionstore_p2_owner;
--
-- Name: variante_prenda_id_variante_prenda_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fashionstore_p2_owner
--
ALTER SEQUENCE public.variante_prenda_id_variante_prenda_seq OWNED BY public.variante_prenda.id_variante_prenda;
--
-- Name: venta; Type: TABLE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE TABLE public.venta (
    id_venta integer NOT NULL,
    id_cliente integer,
    id_sucursal integer,
    id_cajero integer,
    id_reserva integer,
    tipo_venta character varying(20) NOT NULL,
    metodo_pago character varying(30) NOT NULL,
    subtotal numeric(10,2) NOT NULL,
    descuento numeric(10,2) DEFAULT 0.00,
    total numeric(10,2) NOT NULL,
    fecha_venta timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    tenant_id integer DEFAULT public.current_tenant() NOT NULL,
    fecha_entrega timestamp with time zone,
    origen_datos text DEFAULT 'operativo'::text NOT NULL,
    referencia_demo text,
    CONSTRAINT venta_metodo_pago_check CHECK (((metodo_pago)::text = ANY ((ARRAY['Efectivo'::character varying, 'Tarjeta'::character varying, 'QR'::character varying, 'Transferencia'::character varying])::text[]))),
    CONSTRAINT venta_origen_datos_check CHECK ((origen_datos = ANY (ARRAY['operativo'::text, 'demostracion'::text]))),
    CONSTRAINT venta_tipo_venta_check CHECK (((tipo_venta)::text = ANY ((ARRAY['Presencial'::character varying, 'Online'::character varying])::text[])))
);
ALTER TABLE public.venta OWNER TO fashionstore_p2_owner;
--
-- Name: venta_id_venta_seq; Type: SEQUENCE; Schema: public; Owner: fashionstore_p2_owner
--
CREATE SEQUENCE public.venta_id_venta_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE public.venta_id_venta_seq OWNER TO fashionstore_p2_owner;
--
-- Name: venta_id_venta_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fashionstore_p2_owner
--
ALTER SEQUENCE public.venta_id_venta_seq OWNED BY public.venta.id_venta;
--
-- Name: ajuste_monetario id_ajuste; Type: DEFAULT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.ajuste_monetario ALTER COLUMN id_ajuste SET DEFAULT nextval('public.ajuste_monetario_id_ajuste_seq'::regclass);
--
-- Name: auditoria_identidad id; Type: DEFAULT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.auditoria_identidad ALTER COLUMN id SET DEFAULT nextval('public.auditoria_identidad_id_seq'::regclass);
--
-- Name: bitacora id_bitacora; Type: DEFAULT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.bitacora ALTER COLUMN id_bitacora SET DEFAULT nextval('public.bitacora_id_bitacora_seq'::regclass);
--
-- Name: cambio id_cambio; Type: DEFAULT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.cambio ALTER COLUMN id_cambio SET DEFAULT nextval('public.cambio_id_cambio_seq'::regclass);
--
-- Name: categoria id_categoria; Type: DEFAULT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.categoria ALTER COLUMN id_categoria SET DEFAULT nextval('public.categoria_id_categoria_seq'::regclass);
--
-- Name: ciudad id_ciudad; Type: DEFAULT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.ciudad ALTER COLUMN id_ciudad SET DEFAULT nextval('public.ciudad_id_ciudad_seq'::regclass);
--
-- Name: cliente id_cliente; Type: DEFAULT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.cliente ALTER COLUMN id_cliente SET DEFAULT nextval('public.cliente_id_cliente_seq'::regclass);
--
-- Name: color id_color; Type: DEFAULT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.color ALTER COLUMN id_color SET DEFAULT nextval('public.color_id_color_seq'::regclass);
--
-- Name: compra id_compra; Type: DEFAULT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.compra ALTER COLUMN id_compra SET DEFAULT nextval('public.compra_id_compra_seq'::regclass);
--
-- Name: comprobante id_comprobante; Type: DEFAULT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.comprobante ALTER COLUMN id_comprobante SET DEFAULT nextval('public.comprobante_id_comprobante_seq'::regclass);
--
-- Name: cuenta_global id; Type: DEFAULT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.cuenta_global ALTER COLUMN id SET DEFAULT nextval('public.cuenta_global_id_seq'::regclass);
--
-- Name: empresa id_empresa; Type: DEFAULT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.empresa ALTER COLUMN id_empresa SET DEFAULT nextval('public.empresa_id_empresa_seq'::regclass);
--
-- Name: imagen_prenda id_imagen; Type: DEFAULT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.imagen_prenda ALTER COLUMN id_imagen SET DEFAULT nextval('public.imagen_prenda_id_imagen_seq'::regclass);
--
-- Name: movimiento_inventario id_movimiento; Type: DEFAULT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.movimiento_inventario ALTER COLUMN id_movimiento SET DEFAULT nextval('public.movimiento_inventario_id_movimiento_seq'::regclass);
--
-- Name: notificacion id_notificacion; Type: DEFAULT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.notificacion ALTER COLUMN id_notificacion SET DEFAULT nextval('public.notificacion_id_notificacion_seq'::regclass);
--
-- Name: pago_transaccion id_pago; Type: DEFAULT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.pago_transaccion ALTER COLUMN id_pago SET DEFAULT nextval('public.pago_transaccion_id_pago_seq'::regclass);
--
-- Name: permiso id_permiso; Type: DEFAULT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.permiso ALTER COLUMN id_permiso SET DEFAULT nextval('public.permiso_id_permiso_seq'::regclass);
--
-- Name: plan id_plan; Type: DEFAULT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.plan ALTER COLUMN id_plan SET DEFAULT nextval('public.plan_id_plan_seq'::regclass);
--
-- Name: prenda id_prenda; Type: DEFAULT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.prenda ALTER COLUMN id_prenda SET DEFAULT nextval('public.prenda_id_prenda_seq'::regclass);
--
-- Name: proveedor id_proveedor; Type: DEFAULT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.proveedor ALTER COLUMN id_proveedor SET DEFAULT nextval('public.proveedor_id_proveedor_seq'::regclass);
--
-- Name: reserva id_reserva; Type: DEFAULT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.reserva ALTER COLUMN id_reserva SET DEFAULT nextval('public.reserva_id_reserva_seq'::regclass);
--
-- Name: rol id_rol; Type: DEFAULT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.rol ALTER COLUMN id_rol SET DEFAULT nextval('public.rol_id_rol_seq'::regclass);
--
-- Name: sucursal id_sucursal; Type: DEFAULT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.sucursal ALTER COLUMN id_sucursal SET DEFAULT nextval('public.sucursal_id_sucursal_seq'::regclass);
--
-- Name: suscripcion id_suscripcion; Type: DEFAULT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.suscripcion ALTER COLUMN id_suscripcion SET DEFAULT nextval('public.suscripcion_id_suscripcion_seq'::regclass);
--
-- Name: talla id_talla; Type: DEFAULT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.talla ALTER COLUMN id_talla SET DEFAULT nextval('public.talla_id_talla_seq'::regclass);
--
-- Name: temporada id_temporada; Type: DEFAULT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.temporada ALTER COLUMN id_temporada SET DEFAULT nextval('public.temporada_id_temporada_seq'::regclass);
--
-- Name: usuario id_usuario; Type: DEFAULT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.usuario ALTER COLUMN id_usuario SET DEFAULT nextval('public.usuario_id_usuario_seq'::regclass);
--
-- Name: usuario_token id_token; Type: DEFAULT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.usuario_token ALTER COLUMN id_token SET DEFAULT nextval('public.usuario_token_id_token_seq'::regclass);
--
-- Name: variante_prenda id_variante_prenda; Type: DEFAULT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.variante_prenda ALTER COLUMN id_variante_prenda SET DEFAULT nextval('public.variante_prenda_id_variante_prenda_seq'::regclass);
--
-- Name: venta id_venta; Type: DEFAULT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.venta ALTER COLUMN id_venta SET DEFAULT nextval('public.venta_id_venta_seq'::regclass);
--
-- Name: ajuste_monetario ajuste_monetario_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.ajuste_monetario
    ADD CONSTRAINT ajuste_monetario_pkey PRIMARY KEY (id_ajuste);
--
-- Name: ajuste_monetario ajuste_monetario_tenant_id_referencia_key; Type: CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.ajuste_monetario
    ADD CONSTRAINT ajuste_monetario_tenant_id_referencia_key UNIQUE (tenant_id, referencia);
--
-- Name: auditoria_identidad auditoria_identidad_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.auditoria_identidad
    ADD CONSTRAINT auditoria_identidad_pkey PRIMARY KEY (id);
--
-- Name: bitacora bitacora_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.bitacora
    ADD CONSTRAINT bitacora_pkey PRIMARY KEY (id_bitacora);
--
-- Name: cambio cambio_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.cambio
    ADD CONSTRAINT cambio_pkey PRIMARY KEY (id_cambio);
--
-- Name: categoria categoria_nombre_key; Type: CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.categoria
    ADD CONSTRAINT categoria_nombre_key UNIQUE (tenant_id, nombre);
--
-- Name: categoria categoria_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.categoria
    ADD CONSTRAINT categoria_pkey PRIMARY KEY (id_categoria);
--
-- Name: ciudad ciudad_nombre_key; Type: CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.ciudad
    ADD CONSTRAINT ciudad_nombre_key UNIQUE (tenant_id, nombre);
--
-- Name: ciudad ciudad_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.ciudad
    ADD CONSTRAINT ciudad_pkey PRIMARY KEY (id_ciudad);
--
-- Name: cliente cliente_ci_key; Type: CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.cliente
    ADD CONSTRAINT cliente_ci_key UNIQUE (tenant_id, ci);
--
-- Name: cliente cliente_correo_key; Type: CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.cliente
    ADD CONSTRAINT cliente_correo_key UNIQUE (tenant_id, correo);
--
-- Name: cliente cliente_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.cliente
    ADD CONSTRAINT cliente_pkey PRIMARY KEY (id_cliente);
--
-- Name: color color_nombre_key; Type: CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.color
    ADD CONSTRAINT color_nombre_key UNIQUE (tenant_id, nombre);
--
-- Name: color color_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.color
    ADD CONSTRAINT color_pkey PRIMARY KEY (id_color);
--
-- Name: compra compra_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.compra
    ADD CONSTRAINT compra_pkey PRIMARY KEY (id_compra);
--
-- Name: comprobante comprobante_numero_comprobante_key; Type: CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.comprobante
    ADD CONSTRAINT comprobante_numero_comprobante_key UNIQUE (tenant_id, numero_comprobante);
--
-- Name: comprobante comprobante_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.comprobante
    ADD CONSTRAINT comprobante_pkey PRIMARY KEY (id_comprobante);
--
-- Name: cuenta_global cuenta_global_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.cuenta_global
    ADD CONSTRAINT cuenta_global_pkey PRIMARY KEY (id);
--
-- Name: cuenta_recuperacion cuenta_recuperacion_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.cuenta_recuperacion
    ADD CONSTRAINT cuenta_recuperacion_pkey PRIMARY KEY (token_hash);
--
-- Name: detalle_compra detalle_compra_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.detalle_compra
    ADD CONSTRAINT detalle_compra_pkey PRIMARY KEY (id_compra, id_variante_prenda);
--
-- Name: detalle_reserva detalle_reserva_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.detalle_reserva
    ADD CONSTRAINT detalle_reserva_pkey PRIMARY KEY (id_reserva, id_variante_prenda);
--
-- Name: detalle_venta detalle_venta_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.detalle_venta
    ADD CONSTRAINT detalle_venta_pkey PRIMARY KEY (id_venta, id_variante_prenda);
--
-- Name: dispositivo_push dispositivo_push_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.dispositivo_push
    ADD CONSTRAINT dispositivo_push_pkey PRIMARY KEY (tenant_id, id_usuario, token);
--
-- Name: empresa empresa_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.empresa
    ADD CONSTRAINT empresa_pkey PRIMARY KEY (id_empresa);
--
-- Name: empresa empresa_slug_key; Type: CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.empresa
    ADD CONSTRAINT empresa_slug_key UNIQUE (slug);
--
-- Name: imagen_prenda imagen_prenda_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.imagen_prenda
    ADD CONSTRAINT imagen_prenda_pkey PRIMARY KEY (id_imagen);
--
-- Name: inventario inventario_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.inventario
    ADD CONSTRAINT inventario_pkey PRIMARY KEY (id_sucursal, id_variante_prenda);
--
-- Name: movimiento_inventario movimiento_inventario_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.movimiento_inventario
    ADD CONSTRAINT movimiento_inventario_pkey PRIMARY KEY (id_movimiento);
--
-- Name: notificacion notificacion_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.notificacion
    ADD CONSTRAINT notificacion_pkey PRIMARY KEY (id_notificacion);
--
-- Name: operacion_sync operacion_sync_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.operacion_sync
    ADD CONSTRAINT operacion_sync_pkey PRIMARY KEY (tenant_id, operation_id);
--
-- Name: pago_transaccion pago_transaccion_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.pago_transaccion
    ADD CONSTRAINT pago_transaccion_pkey PRIMARY KEY (id_pago);
--
-- Name: pago_transaccion pago_transaccion_transaccion_id_key; Type: CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.pago_transaccion
    ADD CONSTRAINT pago_transaccion_transaccion_id_key UNIQUE (tenant_id, transaccion_id);
--
-- Name: permiso permiso_codigo_key; Type: CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.permiso
    ADD CONSTRAINT permiso_codigo_key UNIQUE (codigo);
--
-- Name: permiso permiso_nombre_key; Type: CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.permiso
    ADD CONSTRAINT permiso_nombre_key UNIQUE (nombre);
--
-- Name: permiso permiso_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.permiso
    ADD CONSTRAINT permiso_pkey PRIMARY KEY (id_permiso);
--
-- Name: plan plan_nombre_key; Type: CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.plan
    ADD CONSTRAINT plan_nombre_key UNIQUE (nombre);
--
-- Name: plan plan_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.plan
    ADD CONSTRAINT plan_pkey PRIMARY KEY (id_plan);
--
-- Name: prenda prenda_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.prenda
    ADD CONSTRAINT prenda_pkey PRIMARY KEY (id_prenda);
--
-- Name: prenda prenda_sku_key; Type: CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.prenda
    ADD CONSTRAINT prenda_sku_key UNIQUE (tenant_id, sku);
--
-- Name: proveedor proveedor_nit_key; Type: CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.proveedor
    ADD CONSTRAINT proveedor_nit_key UNIQUE (tenant_id, nit);
--
-- Name: proveedor proveedor_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.proveedor
    ADD CONSTRAINT proveedor_pkey PRIMARY KEY (id_proveedor);
--
-- Name: push_entrega push_entrega_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.push_entrega
    ADD CONSTRAINT push_entrega_pkey PRIMARY KEY (tenant_id, id_notificacion, token_hash);
--
-- Name: reporte_resultado reporte_resultado_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.reporte_resultado
    ADD CONSTRAINT reporte_resultado_pkey PRIMARY KEY (id);
--
-- Name: reserva reserva_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.reserva
    ADD CONSTRAINT reserva_pkey PRIMARY KEY (id_reserva);
--
-- Name: retencion retencion_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.retencion
    ADD CONSTRAINT retencion_pkey PRIMARY KEY (tenant_id, id_reserva, id_variante_prenda);
--
-- Name: rol rol_nombre_key; Type: CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.rol
    ADD CONSTRAINT rol_nombre_key UNIQUE (tenant_id, nombre);
--
-- Name: rol_permiso rol_permiso_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.rol_permiso
    ADD CONSTRAINT rol_permiso_pkey PRIMARY KEY (id_rol, id_permiso);
--
-- Name: rol rol_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.rol
    ADD CONSTRAINT rol_pkey PRIMARY KEY (id_rol);
--
-- Name: schema_migrations schema_migrations_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.schema_migrations
    ADD CONSTRAINT schema_migrations_pkey PRIMARY KEY (version);
--
-- Name: stripe_event stripe_event_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.stripe_event
    ADD CONSTRAINT stripe_event_pkey PRIMARY KEY (tenant_id, event_id);
--
-- Name: sucursal sucursal_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.sucursal
    ADD CONSTRAINT sucursal_pkey PRIMARY KEY (id_sucursal);
--
-- Name: suscripcion suscripcion_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.suscripcion
    ADD CONSTRAINT suscripcion_pkey PRIMARY KEY (id_suscripcion);
--
-- Name: suscripcion suscripcion_tenant_id_key; Type: CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.suscripcion
    ADD CONSTRAINT suscripcion_tenant_id_key UNIQUE (tenant_id);
--
-- Name: talla talla_nombre_key; Type: CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.talla
    ADD CONSTRAINT talla_nombre_key UNIQUE (tenant_id, nombre);
--
-- Name: talla talla_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.talla
    ADD CONSTRAINT talla_pkey PRIMARY KEY (id_talla);
--
-- Name: temporada temporada_nombre_key; Type: CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.temporada
    ADD CONSTRAINT temporada_nombre_key UNIQUE (tenant_id, nombre);
--
-- Name: temporada temporada_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.temporada
    ADD CONSTRAINT temporada_pkey PRIMARY KEY (id_temporada);
--
-- Name: usuario usuario_correo_key; Type: CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.usuario
    ADD CONSTRAINT usuario_correo_key UNIQUE (tenant_id, correo);
--
-- Name: usuario usuario_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.usuario
    ADD CONSTRAINT usuario_pkey PRIMARY KEY (id_usuario);
--
-- Name: usuario_sucursal usuario_sucursal_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.usuario_sucursal
    ADD CONSTRAINT usuario_sucursal_pkey PRIMARY KEY (tenant_id, id_usuario, id_sucursal);
--
-- Name: usuario_token usuario_token_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.usuario_token
    ADD CONSTRAINT usuario_token_pkey PRIMARY KEY (id_token);
--
-- Name: variante_prenda variant_color_combination; Type: CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.variante_prenda
    ADD CONSTRAINT variant_color_combination UNIQUE (tenant_id, id_prenda, id_talla, color_ids);
--
-- Name: variante_color variante_color_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.variante_color
    ADD CONSTRAINT variante_color_pkey PRIMARY KEY (tenant_id, id_variante_prenda, id_color);
--
-- Name: variante_prenda variante_prenda_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.variante_prenda
    ADD CONSTRAINT variante_prenda_pkey PRIMARY KEY (id_variante_prenda);
--
-- Name: variante_prenda variante_prenda_sku_variante_key; Type: CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.variante_prenda
    ADD CONSTRAINT variante_prenda_sku_variante_key UNIQUE (tenant_id, sku_variante);
--
-- Name: venta venta_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.venta
    ADD CONSTRAINT venta_pkey PRIMARY KEY (id_venta);
--
-- Name: bitacora_tenant_id_idx; Type: INDEX; Schema: public; Owner: fashionstore_p2_owner
--
CREATE INDEX bitacora_tenant_id_idx ON public.bitacora USING btree (tenant_id);
--
-- Name: categoria_tenant_id_idx; Type: INDEX; Schema: public; Owner: fashionstore_p2_owner
--
CREATE INDEX categoria_tenant_id_idx ON public.categoria USING btree (tenant_id);
--
-- Name: change_tenant_reference; Type: INDEX; Schema: public; Owner: fashionstore_p2_owner
--
CREATE UNIQUE INDEX change_tenant_reference ON public.cambio USING btree (tenant_id, id_cambio);
--
-- Name: ciudad_tenant_id_idx; Type: INDEX; Schema: public; Owner: fashionstore_p2_owner
--
CREATE INDEX ciudad_tenant_id_idx ON public.ciudad USING btree (tenant_id);
--
-- Name: cliente_tenant_id_idx; Type: INDEX; Schema: public; Owner: fashionstore_p2_owner
--
CREATE INDEX cliente_tenant_id_idx ON public.cliente USING btree (tenant_id);
--
-- Name: color_tenant_id_idx; Type: INDEX; Schema: public; Owner: fashionstore_p2_owner
--
CREATE INDEX color_tenant_id_idx ON public.color USING btree (tenant_id);
--
-- Name: compra_tenant_id_idx; Type: INDEX; Schema: public; Owner: fashionstore_p2_owner
--
CREATE INDEX compra_tenant_id_idx ON public.compra USING btree (tenant_id);
--
-- Name: comprobante_tenant_id_idx; Type: INDEX; Schema: public; Owner: fashionstore_p2_owner
--
CREATE INDEX comprobante_tenant_id_idx ON public.comprobante USING btree (tenant_id);
--
-- Name: cuenta_global_correo; Type: INDEX; Schema: public; Owner: fashionstore_p2_owner
--
CREATE UNIQUE INDEX cuenta_global_correo ON public.cuenta_global USING btree (lower(correo));
--
-- Name: detalle_compra_tenant_id_idx; Type: INDEX; Schema: public; Owner: fashionstore_p2_owner
--
CREATE INDEX detalle_compra_tenant_id_idx ON public.detalle_compra USING btree (tenant_id);
--
-- Name: detalle_reserva_tenant_id_idx; Type: INDEX; Schema: public; Owner: fashionstore_p2_owner
--
CREATE INDEX detalle_reserva_tenant_id_idx ON public.detalle_reserva USING btree (tenant_id);
--
-- Name: detalle_venta_tenant_id_idx; Type: INDEX; Schema: public; Owner: fashionstore_p2_owner
--
CREATE INDEX detalle_venta_tenant_id_idx ON public.detalle_venta USING btree (tenant_id);
--
-- Name: holds_availability; Type: INDEX; Schema: public; Owner: fashionstore_p2_owner
--
CREATE INDEX holds_availability ON public.retencion USING btree (tenant_id, id_sucursal, id_variante_prenda, vence);
--
-- Name: idx_usuario_token_id_usuario; Type: INDEX; Schema: public; Owner: fashionstore_p2_owner
--
CREATE INDEX idx_usuario_token_id_usuario ON public.usuario_token USING btree (id_usuario);
--
-- Name: idx_usuario_token_recuperacion; Type: INDEX; Schema: public; Owner: fashionstore_p2_owner
--
CREATE UNIQUE INDEX idx_usuario_token_recuperacion ON public.usuario_token USING btree (token_recuperacion);
--
-- Name: idx_usuario_token_usuario_usado; Type: INDEX; Schema: public; Owner: fashionstore_p2_owner
--
CREATE INDEX idx_usuario_token_usuario_usado ON public.usuario_token USING btree (id_usuario, usado);
--
-- Name: imagen_prenda_tenant_id_idx; Type: INDEX; Schema: public; Owner: fashionstore_p2_owner
--
CREATE INDEX imagen_prenda_tenant_id_idx ON public.imagen_prenda USING btree (tenant_id);
--
-- Name: inventario_tenant_id_idx; Type: INDEX; Schema: public; Owner: fashionstore_p2_owner
--
CREATE INDEX inventario_tenant_id_idx ON public.inventario USING btree (tenant_id);
--
-- Name: movimiento_inventario_tenant_id_idx; Type: INDEX; Schema: public; Owner: fashionstore_p2_owner
--
CREATE INDEX movimiento_inventario_tenant_id_idx ON public.movimiento_inventario USING btree (tenant_id);
--
-- Name: notification_tenant_reference; Type: INDEX; Schema: public; Owner: fashionstore_p2_owner
--
CREATE UNIQUE INDEX notification_tenant_reference ON public.notificacion USING btree (tenant_id, id_notificacion);
--
-- Name: one_revision_per_operation; Type: INDEX; Schema: public; Owner: fashionstore_p2_owner
--
CREATE UNIQUE INDEX one_revision_per_operation ON public.operacion_sync USING btree (tenant_id, original_operation) WHERE (original_operation IS NOT NULL);
--
-- Name: one_sale_per_reservation; Type: INDEX; Schema: public; Owner: fashionstore_p2_owner
--
CREATE UNIQUE INDEX one_sale_per_reservation ON public.venta USING btree (tenant_id, id_reserva) WHERE (id_reserva IS NOT NULL);
--
-- Name: pago_transaccion_tenant_id_idx; Type: INDEX; Schema: public; Owner: fashionstore_p2_owner
--
CREATE INDEX pago_transaccion_tenant_id_idx ON public.pago_transaccion USING btree (tenant_id);
--
-- Name: prenda_tenant_id_idx; Type: INDEX; Schema: public; Owner: fashionstore_p2_owner
--
CREATE INDEX prenda_tenant_id_idx ON public.prenda USING btree (tenant_id);
--
-- Name: proveedor_tenant_id_idx; Type: INDEX; Schema: public; Owner: fashionstore_p2_owner
--
CREATE INDEX proveedor_tenant_id_idx ON public.proveedor USING btree (tenant_id);
--
-- Name: reporte_expiration; Type: INDEX; Schema: public; Owner: fashionstore_p2_owner
--
CREATE INDEX reporte_expiration ON public.reporte_resultado USING btree (expires_at);
--
-- Name: reserva_tenant_id_idx; Type: INDEX; Schema: public; Owner: fashionstore_p2_owner
--
CREATE INDEX reserva_tenant_id_idx ON public.reserva USING btree (tenant_id);
--
-- Name: rol_permiso_tenant_id_idx; Type: INDEX; Schema: public; Owner: fashionstore_p2_owner
--
CREATE INDEX rol_permiso_tenant_id_idx ON public.rol_permiso USING btree (tenant_id);
--
-- Name: rol_tenant_id_idx; Type: INDEX; Schema: public; Owner: fashionstore_p2_owner
--
CREATE INDEX rol_tenant_id_idx ON public.rol USING btree (tenant_id);
--
-- Name: sale_detail_tenant_reference; Type: INDEX; Schema: public; Owner: fashionstore_p2_owner
--
CREATE UNIQUE INDEX sale_detail_tenant_reference ON public.detalle_venta USING btree (tenant_id, id_venta, id_variante_prenda);
--
-- Name: sucursal_tenant_id_idx; Type: INDEX; Schema: public; Owner: fashionstore_p2_owner
--
CREATE INDEX sucursal_tenant_id_idx ON public.sucursal USING btree (tenant_id);
--
-- Name: sync_history; Type: INDEX; Schema: public; Owner: fashionstore_p2_owner
--
CREATE INDEX sync_history ON public.operacion_sync USING btree (tenant_id, author_id, created_at DESC);
--
-- Name: talla_tenant_id_idx; Type: INDEX; Schema: public; Owner: fashionstore_p2_owner
--
CREATE INDEX talla_tenant_id_idx ON public.talla USING btree (tenant_id);
--
-- Name: temporada_tenant_id_idx; Type: INDEX; Schema: public; Owner: fashionstore_p2_owner
--
CREATE INDEX temporada_tenant_id_idx ON public.temporada USING btree (tenant_id);
--
-- Name: tenant_ref_categoria_id_categoria; Type: INDEX; Schema: public; Owner: fashionstore_p2_owner
--
CREATE UNIQUE INDEX tenant_ref_categoria_id_categoria ON public.categoria USING btree (tenant_id, id_categoria);
--
-- Name: tenant_ref_ciudad_id_ciudad; Type: INDEX; Schema: public; Owner: fashionstore_p2_owner
--
CREATE UNIQUE INDEX tenant_ref_ciudad_id_ciudad ON public.ciudad USING btree (tenant_id, id_ciudad);
--
-- Name: tenant_ref_cliente_id_cliente; Type: INDEX; Schema: public; Owner: fashionstore_p2_owner
--
CREATE UNIQUE INDEX tenant_ref_cliente_id_cliente ON public.cliente USING btree (tenant_id, id_cliente);
--
-- Name: tenant_ref_color_id_color; Type: INDEX; Schema: public; Owner: fashionstore_p2_owner
--
CREATE UNIQUE INDEX tenant_ref_color_id_color ON public.color USING btree (tenant_id, id_color);
--
-- Name: tenant_ref_compra_id_compra; Type: INDEX; Schema: public; Owner: fashionstore_p2_owner
--
CREATE UNIQUE INDEX tenant_ref_compra_id_compra ON public.compra USING btree (tenant_id, id_compra);
--
-- Name: tenant_ref_prenda_id_prenda; Type: INDEX; Schema: public; Owner: fashionstore_p2_owner
--
CREATE UNIQUE INDEX tenant_ref_prenda_id_prenda ON public.prenda USING btree (tenant_id, id_prenda);
--
-- Name: tenant_ref_proveedor_id_proveedor; Type: INDEX; Schema: public; Owner: fashionstore_p2_owner
--
CREATE UNIQUE INDEX tenant_ref_proveedor_id_proveedor ON public.proveedor USING btree (tenant_id, id_proveedor);
--
-- Name: tenant_ref_reserva_id_reserva; Type: INDEX; Schema: public; Owner: fashionstore_p2_owner
--
CREATE UNIQUE INDEX tenant_ref_reserva_id_reserva ON public.reserva USING btree (tenant_id, id_reserva);
--
-- Name: tenant_ref_rol_id_rol; Type: INDEX; Schema: public; Owner: fashionstore_p2_owner
--
CREATE UNIQUE INDEX tenant_ref_rol_id_rol ON public.rol USING btree (tenant_id, id_rol);
--
-- Name: tenant_ref_sucursal_id_sucursal; Type: INDEX; Schema: public; Owner: fashionstore_p2_owner
--
CREATE UNIQUE INDEX tenant_ref_sucursal_id_sucursal ON public.sucursal USING btree (tenant_id, id_sucursal);
--
-- Name: tenant_ref_talla_id_talla; Type: INDEX; Schema: public; Owner: fashionstore_p2_owner
--
CREATE UNIQUE INDEX tenant_ref_talla_id_talla ON public.talla USING btree (tenant_id, id_talla);
--
-- Name: tenant_ref_temporada_id_temporada; Type: INDEX; Schema: public; Owner: fashionstore_p2_owner
--
CREATE UNIQUE INDEX tenant_ref_temporada_id_temporada ON public.temporada USING btree (tenant_id, id_temporada);
--
-- Name: tenant_ref_usuario_id_usuario; Type: INDEX; Schema: public; Owner: fashionstore_p2_owner
--
CREATE UNIQUE INDEX tenant_ref_usuario_id_usuario ON public.usuario USING btree (tenant_id, id_usuario);
--
-- Name: tenant_ref_variante_prenda_id_variante_prenda; Type: INDEX; Schema: public; Owner: fashionstore_p2_owner
--
CREATE UNIQUE INDEX tenant_ref_variante_prenda_id_variante_prenda ON public.variante_prenda USING btree (tenant_id, id_variante_prenda);
--
-- Name: tenant_ref_venta_id_venta; Type: INDEX; Schema: public; Owner: fashionstore_p2_owner
--
CREATE UNIQUE INDEX tenant_ref_venta_id_venta ON public.venta USING btree (tenant_id, id_venta);
--
-- Name: usuario_identidad_empresa; Type: INDEX; Schema: public; Owner: fashionstore_p2_owner
--
CREATE UNIQUE INDEX usuario_identidad_empresa ON public.usuario USING btree (tenant_id, account_id);
--
-- Name: usuario_tenant_id_idx; Type: INDEX; Schema: public; Owner: fashionstore_p2_owner
--
CREATE INDEX usuario_tenant_id_idx ON public.usuario USING btree (tenant_id);
--
-- Name: usuario_token_tenant_id_idx; Type: INDEX; Schema: public; Owner: fashionstore_p2_owner
--
CREATE INDEX usuario_token_tenant_id_idx ON public.usuario_token USING btree (tenant_id);
--
-- Name: variante_prenda_tenant_id_idx; Type: INDEX; Schema: public; Owner: fashionstore_p2_owner
--
CREATE INDEX variante_prenda_tenant_id_idx ON public.variante_prenda USING btree (tenant_id);
--
-- Name: venta_demo_reference; Type: INDEX; Schema: public; Owner: fashionstore_p2_owner
--
CREATE UNIQUE INDEX venta_demo_reference ON public.venta USING btree (tenant_id, referencia_demo) WHERE (referencia_demo IS NOT NULL);
--
-- Name: venta_tenant_id_idx; Type: INDEX; Schema: public; Owner: fashionstore_p2_owner
--
CREATE INDEX venta_tenant_id_idx ON public.venta USING btree (tenant_id);
--
-- Name: sucursal branch_limit; Type: TRIGGER; Schema: public; Owner: fashionstore_p2_owner
--
CREATE TRIGGER branch_limit BEFORE INSERT OR UPDATE ON public.sucursal FOR EACH ROW EXECUTE FUNCTION public.check_branch_limit();
--
-- Name: variante_prenda canonical_colors; Type: TRIGGER; Schema: public; Owner: fashionstore_p2_owner
--
CREATE TRIGGER canonical_colors BEFORE INSERT OR UPDATE OF color_ids, id_color ON public.variante_prenda FOR EACH ROW EXECUTE FUNCTION public.canonical_variant_colors();
--
-- Name: variante_prenda sync_colors; Type: TRIGGER; Schema: public; Owner: fashionstore_p2_owner
--
CREATE TRIGGER sync_colors AFTER INSERT OR UPDATE OF color_ids, id_color ON public.variante_prenda FOR EACH ROW EXECUTE FUNCTION public.sync_variant_colors();
--
-- Name: ajuste_monetario transactional_audit; Type: TRIGGER; Schema: public; Owner: fashionstore_p2_owner
--
CREATE TRIGGER transactional_audit AFTER INSERT OR DELETE OR UPDATE ON public.ajuste_monetario FOR EACH ROW EXECUTE FUNCTION public.audit_business_row();
--
-- Name: cambio transactional_audit; Type: TRIGGER; Schema: public; Owner: fashionstore_p2_owner
--
CREATE TRIGGER transactional_audit AFTER INSERT OR DELETE OR UPDATE ON public.cambio FOR EACH ROW EXECUTE FUNCTION public.audit_business_row();
--
-- Name: cliente transactional_audit; Type: TRIGGER; Schema: public; Owner: fashionstore_p2_owner
--
CREATE TRIGGER transactional_audit AFTER INSERT OR DELETE OR UPDATE ON public.cliente FOR EACH ROW EXECUTE FUNCTION public.audit_business_row();
--
-- Name: empresa transactional_audit; Type: TRIGGER; Schema: public; Owner: fashionstore_p2_owner
--
CREATE TRIGGER transactional_audit AFTER INSERT OR DELETE OR UPDATE ON public.empresa FOR EACH ROW EXECUTE FUNCTION public.audit_business_row();
--
-- Name: movimiento_inventario transactional_audit; Type: TRIGGER; Schema: public; Owner: fashionstore_p2_owner
--
CREATE TRIGGER transactional_audit AFTER INSERT OR DELETE OR UPDATE ON public.movimiento_inventario FOR EACH ROW EXECUTE FUNCTION public.audit_business_row();
--
-- Name: pago_transaccion transactional_audit; Type: TRIGGER; Schema: public; Owner: fashionstore_p2_owner
--
CREATE TRIGGER transactional_audit AFTER INSERT OR DELETE OR UPDATE ON public.pago_transaccion FOR EACH ROW EXECUTE FUNCTION public.audit_business_row();
--
-- Name: plan transactional_audit; Type: TRIGGER; Schema: public; Owner: fashionstore_p2_owner
--
CREATE TRIGGER transactional_audit AFTER INSERT OR DELETE OR UPDATE ON public.plan FOR EACH ROW EXECUTE FUNCTION public.audit_business_row();
--
-- Name: prenda transactional_audit; Type: TRIGGER; Schema: public; Owner: fashionstore_p2_owner
--
CREATE TRIGGER transactional_audit AFTER INSERT OR DELETE OR UPDATE ON public.prenda FOR EACH ROW EXECUTE FUNCTION public.audit_business_row();
--
-- Name: rol transactional_audit; Type: TRIGGER; Schema: public; Owner: fashionstore_p2_owner
--
CREATE TRIGGER transactional_audit AFTER INSERT OR DELETE OR UPDATE ON public.rol FOR EACH ROW EXECUTE FUNCTION public.audit_business_row();
--
-- Name: rol_permiso transactional_audit; Type: TRIGGER; Schema: public; Owner: fashionstore_p2_owner
--
CREATE TRIGGER transactional_audit AFTER INSERT OR DELETE OR UPDATE ON public.rol_permiso FOR EACH ROW EXECUTE FUNCTION public.audit_business_row();
--
-- Name: sucursal transactional_audit; Type: TRIGGER; Schema: public; Owner: fashionstore_p2_owner
--
CREATE TRIGGER transactional_audit AFTER INSERT OR DELETE OR UPDATE ON public.sucursal FOR EACH ROW EXECUTE FUNCTION public.audit_business_row();
--
-- Name: suscripcion transactional_audit; Type: TRIGGER; Schema: public; Owner: fashionstore_p2_owner
--
CREATE TRIGGER transactional_audit AFTER INSERT OR DELETE OR UPDATE ON public.suscripcion FOR EACH ROW EXECUTE FUNCTION public.audit_business_row();
--
-- Name: usuario transactional_audit; Type: TRIGGER; Schema: public; Owner: fashionstore_p2_owner
--
CREATE TRIGGER transactional_audit AFTER INSERT OR DELETE OR UPDATE ON public.usuario FOR EACH ROW EXECUTE FUNCTION public.audit_business_row();
--
-- Name: venta transactional_audit; Type: TRIGGER; Schema: public; Owner: fashionstore_p2_owner
--
CREATE TRIGGER transactional_audit AFTER INSERT OR DELETE OR UPDATE ON public.venta FOR EACH ROW EXECUTE FUNCTION public.audit_business_row();
--
-- Name: movimiento_inventario trg_movimiento_inventario; Type: TRIGGER; Schema: public; Owner: fashionstore_p2_owner
--
CREATE TRIGGER trg_movimiento_inventario AFTER INSERT ON public.movimiento_inventario FOR EACH ROW EXECUTE FUNCTION public.actualizar_stock_por_movimiento();
--
-- Name: ajuste_monetario ajuste_monetario_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.ajuste_monetario
    ADD CONSTRAINT ajuste_monetario_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.empresa(id_empresa);
--
-- Name: ajuste_monetario ajuste_monetario_tenant_id_id_cambio_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.ajuste_monetario
    ADD CONSTRAINT ajuste_monetario_tenant_id_id_cambio_fkey FOREIGN KEY (tenant_id, id_cambio) REFERENCES public.cambio(tenant_id, id_cambio);
--
-- Name: auditoria_identidad auditoria_identidad_account_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.auditoria_identidad
    ADD CONSTRAINT auditoria_identidad_account_id_fkey FOREIGN KEY (account_id) REFERENCES public.cuenta_global(id);
--
-- Name: bitacora bitacora_id_usuario_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.bitacora
    ADD CONSTRAINT bitacora_id_usuario_fkey FOREIGN KEY (id_usuario) REFERENCES public.usuario(id_usuario) ON DELETE SET NULL;
--
-- Name: bitacora bitacora_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.bitacora
    ADD CONSTRAINT bitacora_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.empresa(id_empresa);
--
-- Name: cambio cambio_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.cambio
    ADD CONSTRAINT cambio_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.empresa(id_empresa);
--
-- Name: cambio cambio_tenant_id_id_cliente_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.cambio
    ADD CONSTRAINT cambio_tenant_id_id_cliente_fkey FOREIGN KEY (tenant_id, id_cliente) REFERENCES public.cliente(tenant_id, id_cliente);
--
-- Name: cambio cambio_tenant_id_id_reserva_reemplazo_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.cambio
    ADD CONSTRAINT cambio_tenant_id_id_reserva_reemplazo_fkey FOREIGN KEY (tenant_id, id_reserva_reemplazo) REFERENCES public.reserva(tenant_id, id_reserva);
--
-- Name: cambio cambio_tenant_id_id_sucursal_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.cambio
    ADD CONSTRAINT cambio_tenant_id_id_sucursal_fkey FOREIGN KEY (tenant_id, id_sucursal) REFERENCES public.sucursal(tenant_id, id_sucursal);
--
-- Name: cambio cambio_tenant_id_id_venta_id_variante_original_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.cambio
    ADD CONSTRAINT cambio_tenant_id_id_venta_id_variante_original_fkey FOREIGN KEY (tenant_id, id_venta, id_variante_original) REFERENCES public.detalle_venta(tenant_id, id_venta, id_variante_prenda);
--
-- Name: categoria categoria_id_categoria_padre_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.categoria
    ADD CONSTRAINT categoria_id_categoria_padre_fkey FOREIGN KEY (id_categoria_padre) REFERENCES public.categoria(id_categoria) ON DELETE SET NULL;
--
-- Name: categoria categoria_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.categoria
    ADD CONSTRAINT categoria_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.empresa(id_empresa);
--
-- Name: ciudad ciudad_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.ciudad
    ADD CONSTRAINT ciudad_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.empresa(id_empresa);
--
-- Name: cliente cliente_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.cliente
    ADD CONSTRAINT cliente_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.empresa(id_empresa);
--
-- Name: color color_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.color
    ADD CONSTRAINT color_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.empresa(id_empresa);
--
-- Name: compra compra_id_proveedor_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.compra
    ADD CONSTRAINT compra_id_proveedor_fkey FOREIGN KEY (id_proveedor) REFERENCES public.proveedor(id_proveedor) ON DELETE RESTRICT;
--
-- Name: compra compra_id_sucursal_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.compra
    ADD CONSTRAINT compra_id_sucursal_fkey FOREIGN KEY (id_sucursal) REFERENCES public.sucursal(id_sucursal) ON DELETE RESTRICT;
--
-- Name: compra compra_id_usuario_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.compra
    ADD CONSTRAINT compra_id_usuario_fkey FOREIGN KEY (id_usuario) REFERENCES public.usuario(id_usuario) ON DELETE RESTRICT;
--
-- Name: compra compra_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.compra
    ADD CONSTRAINT compra_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.empresa(id_empresa);
--
-- Name: comprobante comprobante_id_venta_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.comprobante
    ADD CONSTRAINT comprobante_id_venta_fkey FOREIGN KEY (id_venta) REFERENCES public.venta(id_venta) ON DELETE CASCADE;
--
-- Name: comprobante comprobante_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.comprobante
    ADD CONSTRAINT comprobante_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.empresa(id_empresa);
--
-- Name: cuenta_recuperacion cuenta_recuperacion_account_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.cuenta_recuperacion
    ADD CONSTRAINT cuenta_recuperacion_account_id_fkey FOREIGN KEY (account_id) REFERENCES public.cuenta_global(id);
--
-- Name: detalle_compra detalle_compra_id_compra_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.detalle_compra
    ADD CONSTRAINT detalle_compra_id_compra_fkey FOREIGN KEY (id_compra) REFERENCES public.compra(id_compra) ON DELETE CASCADE;
--
-- Name: detalle_compra detalle_compra_id_variante_prenda_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.detalle_compra
    ADD CONSTRAINT detalle_compra_id_variante_prenda_fkey FOREIGN KEY (id_variante_prenda) REFERENCES public.variante_prenda(id_variante_prenda) ON DELETE RESTRICT;
--
-- Name: detalle_compra detalle_compra_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.detalle_compra
    ADD CONSTRAINT detalle_compra_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.empresa(id_empresa);
--
-- Name: detalle_reserva detalle_reserva_id_reserva_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.detalle_reserva
    ADD CONSTRAINT detalle_reserva_id_reserva_fkey FOREIGN KEY (id_reserva) REFERENCES public.reserva(id_reserva) ON DELETE CASCADE;
--
-- Name: detalle_reserva detalle_reserva_id_variante_prenda_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.detalle_reserva
    ADD CONSTRAINT detalle_reserva_id_variante_prenda_fkey FOREIGN KEY (id_variante_prenda) REFERENCES public.variante_prenda(id_variante_prenda) ON DELETE RESTRICT;
--
-- Name: detalle_reserva detalle_reserva_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.detalle_reserva
    ADD CONSTRAINT detalle_reserva_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.empresa(id_empresa);
--
-- Name: detalle_venta detalle_venta_id_variante_prenda_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.detalle_venta
    ADD CONSTRAINT detalle_venta_id_variante_prenda_fkey FOREIGN KEY (id_variante_prenda) REFERENCES public.variante_prenda(id_variante_prenda) ON DELETE RESTRICT;
--
-- Name: detalle_venta detalle_venta_id_venta_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.detalle_venta
    ADD CONSTRAINT detalle_venta_id_venta_fkey FOREIGN KEY (id_venta) REFERENCES public.venta(id_venta) ON DELETE CASCADE;
--
-- Name: detalle_venta detalle_venta_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.detalle_venta
    ADD CONSTRAINT detalle_venta_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.empresa(id_empresa);
--
-- Name: dispositivo_push dispositivo_push_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.dispositivo_push
    ADD CONSTRAINT dispositivo_push_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.empresa(id_empresa);
--
-- Name: dispositivo_push dispositivo_push_tenant_id_id_usuario_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.dispositivo_push
    ADD CONSTRAINT dispositivo_push_tenant_id_id_usuario_fkey FOREIGN KEY (tenant_id, id_usuario) REFERENCES public.usuario(tenant_id, id_usuario);
--
-- Name: imagen_prenda imagen_prenda_id_prenda_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.imagen_prenda
    ADD CONSTRAINT imagen_prenda_id_prenda_fkey FOREIGN KEY (id_prenda) REFERENCES public.prenda(id_prenda) ON DELETE CASCADE;
--
-- Name: imagen_prenda imagen_prenda_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.imagen_prenda
    ADD CONSTRAINT imagen_prenda_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.empresa(id_empresa);
--
-- Name: inventario inventario_id_sucursal_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.inventario
    ADD CONSTRAINT inventario_id_sucursal_fkey FOREIGN KEY (id_sucursal) REFERENCES public.sucursal(id_sucursal) ON DELETE RESTRICT;
--
-- Name: inventario inventario_id_variante_prenda_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.inventario
    ADD CONSTRAINT inventario_id_variante_prenda_fkey FOREIGN KEY (id_variante_prenda) REFERENCES public.variante_prenda(id_variante_prenda) ON DELETE RESTRICT;
--
-- Name: inventario inventario_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.inventario
    ADD CONSTRAINT inventario_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.empresa(id_empresa);
--
-- Name: movimiento_inventario movimiento_inventario_id_sucursal_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.movimiento_inventario
    ADD CONSTRAINT movimiento_inventario_id_sucursal_fkey FOREIGN KEY (id_sucursal) REFERENCES public.sucursal(id_sucursal) ON DELETE RESTRICT;
--
-- Name: movimiento_inventario movimiento_inventario_id_usuario_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.movimiento_inventario
    ADD CONSTRAINT movimiento_inventario_id_usuario_fkey FOREIGN KEY (id_usuario) REFERENCES public.usuario(id_usuario) ON DELETE RESTRICT;
--
-- Name: movimiento_inventario movimiento_inventario_id_variante_prenda_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.movimiento_inventario
    ADD CONSTRAINT movimiento_inventario_id_variante_prenda_fkey FOREIGN KEY (id_variante_prenda) REFERENCES public.variante_prenda(id_variante_prenda) ON DELETE RESTRICT;
--
-- Name: movimiento_inventario movimiento_inventario_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.movimiento_inventario
    ADD CONSTRAINT movimiento_inventario_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.empresa(id_empresa);
--
-- Name: notificacion notificacion_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.notificacion
    ADD CONSTRAINT notificacion_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.empresa(id_empresa);
--
-- Name: notificacion notificacion_tenant_id_id_cambio_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.notificacion
    ADD CONSTRAINT notificacion_tenant_id_id_cambio_fkey FOREIGN KEY (tenant_id, id_cambio) REFERENCES public.cambio(tenant_id, id_cambio);
--
-- Name: notificacion notificacion_tenant_id_id_cliente_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.notificacion
    ADD CONSTRAINT notificacion_tenant_id_id_cliente_fkey FOREIGN KEY (tenant_id, id_cliente) REFERENCES public.cliente(tenant_id, id_cliente);
--
-- Name: operacion_sync operacion_sync_tenant_id_author_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.operacion_sync
    ADD CONSTRAINT operacion_sync_tenant_id_author_id_fkey FOREIGN KEY (tenant_id, author_id) REFERENCES public.usuario(tenant_id, id_usuario);
--
-- Name: operacion_sync operacion_sync_tenant_id_branch_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.operacion_sync
    ADD CONSTRAINT operacion_sync_tenant_id_branch_id_fkey FOREIGN KEY (tenant_id, branch_id) REFERENCES public.sucursal(tenant_id, id_sucursal);
--
-- Name: operacion_sync operacion_sync_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.operacion_sync
    ADD CONSTRAINT operacion_sync_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.empresa(id_empresa);
--
-- Name: operacion_sync operacion_sync_tenant_id_original_operation_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.operacion_sync
    ADD CONSTRAINT operacion_sync_tenant_id_original_operation_fkey FOREIGN KEY (tenant_id, original_operation) REFERENCES public.operacion_sync(tenant_id, operation_id);
--
-- Name: operacion_sync operacion_sync_tenant_id_resolved_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.operacion_sync
    ADD CONSTRAINT operacion_sync_tenant_id_resolved_by_fkey FOREIGN KEY (tenant_id, resolved_by) REFERENCES public.usuario(tenant_id, id_usuario);
--
-- Name: pago_transaccion pago_transaccion_id_venta_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.pago_transaccion
    ADD CONSTRAINT pago_transaccion_id_venta_fkey FOREIGN KEY (id_venta) REFERENCES public.venta(id_venta) ON DELETE CASCADE;
--
-- Name: pago_transaccion pago_transaccion_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.pago_transaccion
    ADD CONSTRAINT pago_transaccion_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.empresa(id_empresa);
--
-- Name: pago_transaccion payment_reservation_tenant; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.pago_transaccion
    ADD CONSTRAINT payment_reservation_tenant FOREIGN KEY (tenant_id, id_reserva) REFERENCES public.reserva(tenant_id, id_reserva);
--
-- Name: prenda prenda_id_categoria_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.prenda
    ADD CONSTRAINT prenda_id_categoria_fkey FOREIGN KEY (id_categoria) REFERENCES public.categoria(id_categoria) ON DELETE RESTRICT;
--
-- Name: prenda prenda_id_temporada_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.prenda
    ADD CONSTRAINT prenda_id_temporada_fkey FOREIGN KEY (id_temporada) REFERENCES public.temporada(id_temporada) ON DELETE SET NULL;
--
-- Name: prenda prenda_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.prenda
    ADD CONSTRAINT prenda_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.empresa(id_empresa);
--
-- Name: proveedor proveedor_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.proveedor
    ADD CONSTRAINT proveedor_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.empresa(id_empresa);
--
-- Name: push_entrega push_entrega_id_notificacion_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.push_entrega
    ADD CONSTRAINT push_entrega_id_notificacion_fkey FOREIGN KEY (id_notificacion) REFERENCES public.notificacion(id_notificacion);
--
-- Name: push_entrega push_entrega_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.push_entrega
    ADD CONSTRAINT push_entrega_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.empresa(id_empresa);
--
-- Name: push_entrega push_notification_tenant; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.push_entrega
    ADD CONSTRAINT push_notification_tenant FOREIGN KEY (tenant_id, id_notificacion) REFERENCES public.notificacion(tenant_id, id_notificacion);
--
-- Name: reporte_resultado reporte_resultado_tenant_id_author_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.reporte_resultado
    ADD CONSTRAINT reporte_resultado_tenant_id_author_id_fkey FOREIGN KEY (tenant_id, author_id) REFERENCES public.usuario(tenant_id, id_usuario);
--
-- Name: reporte_resultado reporte_resultado_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.reporte_resultado
    ADD CONSTRAINT reporte_resultado_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.empresa(id_empresa);
--
-- Name: reserva reserva_id_cliente_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.reserva
    ADD CONSTRAINT reserva_id_cliente_fkey FOREIGN KEY (id_cliente) REFERENCES public.cliente(id_cliente) ON DELETE RESTRICT;
--
-- Name: reserva reserva_id_sucursal_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.reserva
    ADD CONSTRAINT reserva_id_sucursal_fkey FOREIGN KEY (id_sucursal) REFERENCES public.sucursal(id_sucursal) ON DELETE RESTRICT;
--
-- Name: reserva reserva_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.reserva
    ADD CONSTRAINT reserva_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.empresa(id_empresa);
--
-- Name: retencion retencion_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.retencion
    ADD CONSTRAINT retencion_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.empresa(id_empresa);
--
-- Name: retencion retencion_tenant_id_id_reserva_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.retencion
    ADD CONSTRAINT retencion_tenant_id_id_reserva_fkey FOREIGN KEY (tenant_id, id_reserva) REFERENCES public.reserva(tenant_id, id_reserva);
--
-- Name: retencion retencion_tenant_id_id_sucursal_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.retencion
    ADD CONSTRAINT retencion_tenant_id_id_sucursal_fkey FOREIGN KEY (tenant_id, id_sucursal) REFERENCES public.sucursal(tenant_id, id_sucursal);
--
-- Name: retencion retencion_tenant_id_id_variante_prenda_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.retencion
    ADD CONSTRAINT retencion_tenant_id_id_variante_prenda_fkey FOREIGN KEY (tenant_id, id_variante_prenda) REFERENCES public.variante_prenda(tenant_id, id_variante_prenda);
--
-- Name: rol_permiso rol_permiso_id_permiso_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.rol_permiso
    ADD CONSTRAINT rol_permiso_id_permiso_fkey FOREIGN KEY (id_permiso) REFERENCES public.permiso(id_permiso) ON DELETE CASCADE;
--
-- Name: rol_permiso rol_permiso_id_rol_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.rol_permiso
    ADD CONSTRAINT rol_permiso_id_rol_fkey FOREIGN KEY (id_rol) REFERENCES public.rol(id_rol) ON DELETE CASCADE;
--
-- Name: rol_permiso rol_permiso_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.rol_permiso
    ADD CONSTRAINT rol_permiso_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.empresa(id_empresa);
--
-- Name: rol rol_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.rol
    ADD CONSTRAINT rol_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.empresa(id_empresa);
--
-- Name: stripe_event stripe_event_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.stripe_event
    ADD CONSTRAINT stripe_event_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.empresa(id_empresa);
--
-- Name: sucursal sucursal_id_ciudad_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.sucursal
    ADD CONSTRAINT sucursal_id_ciudad_fkey FOREIGN KEY (id_ciudad) REFERENCES public.ciudad(id_ciudad) ON DELETE RESTRICT;
--
-- Name: sucursal sucursal_id_encargado_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.sucursal
    ADD CONSTRAINT sucursal_id_encargado_fkey FOREIGN KEY (id_encargado) REFERENCES public.usuario(id_usuario) ON DELETE SET NULL;
--
-- Name: sucursal sucursal_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.sucursal
    ADD CONSTRAINT sucursal_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.empresa(id_empresa);
--
-- Name: suscripcion suscripcion_id_plan_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.suscripcion
    ADD CONSTRAINT suscripcion_id_plan_fkey FOREIGN KEY (id_plan) REFERENCES public.plan(id_plan);
--
-- Name: suscripcion suscripcion_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.suscripcion
    ADD CONSTRAINT suscripcion_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.empresa(id_empresa);
--
-- Name: talla talla_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.talla
    ADD CONSTRAINT talla_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.empresa(id_empresa);
--
-- Name: temporada temporada_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.temporada
    ADD CONSTRAINT temporada_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.empresa(id_empresa);
--
-- Name: bitacora tenant_bitacora_id_usuario_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.bitacora
    ADD CONSTRAINT tenant_bitacora_id_usuario_fkey FOREIGN KEY (tenant_id, id_usuario) REFERENCES public.usuario(tenant_id, id_usuario);
--
-- Name: categoria tenant_categoria_id_categoria_padre_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.categoria
    ADD CONSTRAINT tenant_categoria_id_categoria_padre_fkey FOREIGN KEY (tenant_id, id_categoria_padre) REFERENCES public.categoria(tenant_id, id_categoria);
--
-- Name: compra tenant_compra_id_proveedor_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.compra
    ADD CONSTRAINT tenant_compra_id_proveedor_fkey FOREIGN KEY (tenant_id, id_proveedor) REFERENCES public.proveedor(tenant_id, id_proveedor);
--
-- Name: compra tenant_compra_id_sucursal_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.compra
    ADD CONSTRAINT tenant_compra_id_sucursal_fkey FOREIGN KEY (tenant_id, id_sucursal) REFERENCES public.sucursal(tenant_id, id_sucursal);
--
-- Name: compra tenant_compra_id_usuario_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.compra
    ADD CONSTRAINT tenant_compra_id_usuario_fkey FOREIGN KEY (tenant_id, id_usuario) REFERENCES public.usuario(tenant_id, id_usuario);
--
-- Name: comprobante tenant_comprobante_id_venta_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.comprobante
    ADD CONSTRAINT tenant_comprobante_id_venta_fkey FOREIGN KEY (tenant_id, id_venta) REFERENCES public.venta(tenant_id, id_venta);
--
-- Name: detalle_compra tenant_detalle_compra_id_compra_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.detalle_compra
    ADD CONSTRAINT tenant_detalle_compra_id_compra_fkey FOREIGN KEY (tenant_id, id_compra) REFERENCES public.compra(tenant_id, id_compra);
--
-- Name: detalle_compra tenant_detalle_compra_id_variante_prenda_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.detalle_compra
    ADD CONSTRAINT tenant_detalle_compra_id_variante_prenda_fkey FOREIGN KEY (tenant_id, id_variante_prenda) REFERENCES public.variante_prenda(tenant_id, id_variante_prenda);
--
-- Name: detalle_reserva tenant_detalle_reserva_id_reserva_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.detalle_reserva
    ADD CONSTRAINT tenant_detalle_reserva_id_reserva_fkey FOREIGN KEY (tenant_id, id_reserva) REFERENCES public.reserva(tenant_id, id_reserva);
--
-- Name: detalle_reserva tenant_detalle_reserva_id_variante_prenda_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.detalle_reserva
    ADD CONSTRAINT tenant_detalle_reserva_id_variante_prenda_fkey FOREIGN KEY (tenant_id, id_variante_prenda) REFERENCES public.variante_prenda(tenant_id, id_variante_prenda);
--
-- Name: detalle_venta tenant_detalle_venta_id_variante_prenda_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.detalle_venta
    ADD CONSTRAINT tenant_detalle_venta_id_variante_prenda_fkey FOREIGN KEY (tenant_id, id_variante_prenda) REFERENCES public.variante_prenda(tenant_id, id_variante_prenda);
--
-- Name: detalle_venta tenant_detalle_venta_id_venta_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.detalle_venta
    ADD CONSTRAINT tenant_detalle_venta_id_venta_fkey FOREIGN KEY (tenant_id, id_venta) REFERENCES public.venta(tenant_id, id_venta);
--
-- Name: imagen_prenda tenant_imagen_prenda_id_prenda_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.imagen_prenda
    ADD CONSTRAINT tenant_imagen_prenda_id_prenda_fkey FOREIGN KEY (tenant_id, id_prenda) REFERENCES public.prenda(tenant_id, id_prenda);
--
-- Name: inventario tenant_inventario_id_sucursal_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.inventario
    ADD CONSTRAINT tenant_inventario_id_sucursal_fkey FOREIGN KEY (tenant_id, id_sucursal) REFERENCES public.sucursal(tenant_id, id_sucursal);
--
-- Name: inventario tenant_inventario_id_variante_prenda_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.inventario
    ADD CONSTRAINT tenant_inventario_id_variante_prenda_fkey FOREIGN KEY (tenant_id, id_variante_prenda) REFERENCES public.variante_prenda(tenant_id, id_variante_prenda);
--
-- Name: movimiento_inventario tenant_movimiento_inventario_id_sucursal_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.movimiento_inventario
    ADD CONSTRAINT tenant_movimiento_inventario_id_sucursal_fkey FOREIGN KEY (tenant_id, id_sucursal) REFERENCES public.sucursal(tenant_id, id_sucursal);
--
-- Name: movimiento_inventario tenant_movimiento_inventario_id_usuario_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.movimiento_inventario
    ADD CONSTRAINT tenant_movimiento_inventario_id_usuario_fkey FOREIGN KEY (tenant_id, id_usuario) REFERENCES public.usuario(tenant_id, id_usuario);
--
-- Name: movimiento_inventario tenant_movimiento_inventario_id_variante_prenda_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.movimiento_inventario
    ADD CONSTRAINT tenant_movimiento_inventario_id_variante_prenda_fkey FOREIGN KEY (tenant_id, id_variante_prenda) REFERENCES public.variante_prenda(tenant_id, id_variante_prenda);
--
-- Name: pago_transaccion tenant_pago_transaccion_id_venta_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.pago_transaccion
    ADD CONSTRAINT tenant_pago_transaccion_id_venta_fkey FOREIGN KEY (tenant_id, id_venta) REFERENCES public.venta(tenant_id, id_venta);
--
-- Name: prenda tenant_prenda_id_categoria_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.prenda
    ADD CONSTRAINT tenant_prenda_id_categoria_fkey FOREIGN KEY (tenant_id, id_categoria) REFERENCES public.categoria(tenant_id, id_categoria);
--
-- Name: prenda tenant_prenda_id_temporada_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.prenda
    ADD CONSTRAINT tenant_prenda_id_temporada_fkey FOREIGN KEY (tenant_id, id_temporada) REFERENCES public.temporada(tenant_id, id_temporada);
--
-- Name: reserva tenant_reserva_id_cliente_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.reserva
    ADD CONSTRAINT tenant_reserva_id_cliente_fkey FOREIGN KEY (tenant_id, id_cliente) REFERENCES public.cliente(tenant_id, id_cliente);
--
-- Name: reserva tenant_reserva_id_sucursal_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.reserva
    ADD CONSTRAINT tenant_reserva_id_sucursal_fkey FOREIGN KEY (tenant_id, id_sucursal) REFERENCES public.sucursal(tenant_id, id_sucursal);
--
-- Name: rol_permiso tenant_rol_permiso_id_rol_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.rol_permiso
    ADD CONSTRAINT tenant_rol_permiso_id_rol_fkey FOREIGN KEY (tenant_id, id_rol) REFERENCES public.rol(tenant_id, id_rol);
--
-- Name: sucursal tenant_sucursal_id_ciudad_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.sucursal
    ADD CONSTRAINT tenant_sucursal_id_ciudad_fkey FOREIGN KEY (tenant_id, id_ciudad) REFERENCES public.ciudad(tenant_id, id_ciudad);
--
-- Name: sucursal tenant_sucursal_id_encargado_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.sucursal
    ADD CONSTRAINT tenant_sucursal_id_encargado_fkey FOREIGN KEY (tenant_id, id_encargado) REFERENCES public.usuario(tenant_id, id_usuario);
--
-- Name: usuario tenant_usuario_id_role_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.usuario
    ADD CONSTRAINT tenant_usuario_id_role_fkey FOREIGN KEY (tenant_id, id_role) REFERENCES public.rol(tenant_id, id_rol);
--
-- Name: usuario_token tenant_usuario_token_id_usuario_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.usuario_token
    ADD CONSTRAINT tenant_usuario_token_id_usuario_fkey FOREIGN KEY (tenant_id, id_usuario) REFERENCES public.usuario(tenant_id, id_usuario);
--
-- Name: variante_prenda tenant_variante_prenda_id_color_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.variante_prenda
    ADD CONSTRAINT tenant_variante_prenda_id_color_fkey FOREIGN KEY (tenant_id, id_color) REFERENCES public.color(tenant_id, id_color);
--
-- Name: variante_prenda tenant_variante_prenda_id_prenda_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.variante_prenda
    ADD CONSTRAINT tenant_variante_prenda_id_prenda_fkey FOREIGN KEY (tenant_id, id_prenda) REFERENCES public.prenda(tenant_id, id_prenda);
--
-- Name: variante_prenda tenant_variante_prenda_id_talla_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.variante_prenda
    ADD CONSTRAINT tenant_variante_prenda_id_talla_fkey FOREIGN KEY (tenant_id, id_talla) REFERENCES public.talla(tenant_id, id_talla);
--
-- Name: venta tenant_venta_id_cajero_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.venta
    ADD CONSTRAINT tenant_venta_id_cajero_fkey FOREIGN KEY (tenant_id, id_cajero) REFERENCES public.usuario(tenant_id, id_usuario);
--
-- Name: venta tenant_venta_id_cliente_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.venta
    ADD CONSTRAINT tenant_venta_id_cliente_fkey FOREIGN KEY (tenant_id, id_cliente) REFERENCES public.cliente(tenant_id, id_cliente);
--
-- Name: venta tenant_venta_id_reserva_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.venta
    ADD CONSTRAINT tenant_venta_id_reserva_fkey FOREIGN KEY (tenant_id, id_reserva) REFERENCES public.reserva(tenant_id, id_reserva);
--
-- Name: venta tenant_venta_id_sucursal_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.venta
    ADD CONSTRAINT tenant_venta_id_sucursal_fkey FOREIGN KEY (tenant_id, id_sucursal) REFERENCES public.sucursal(tenant_id, id_sucursal);
--
-- Name: usuario usuario_account_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.usuario
    ADD CONSTRAINT usuario_account_id_fkey FOREIGN KEY (account_id) REFERENCES public.cuenta_global(id);
--
-- Name: usuario usuario_id_role_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.usuario
    ADD CONSTRAINT usuario_id_role_fkey FOREIGN KEY (id_role) REFERENCES public.rol(id_rol) ON DELETE RESTRICT;
--
-- Name: usuario_sucursal usuario_sucursal_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.usuario_sucursal
    ADD CONSTRAINT usuario_sucursal_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.empresa(id_empresa);
--
-- Name: usuario_sucursal usuario_sucursal_tenant_id_id_sucursal_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.usuario_sucursal
    ADD CONSTRAINT usuario_sucursal_tenant_id_id_sucursal_fkey FOREIGN KEY (tenant_id, id_sucursal) REFERENCES public.sucursal(tenant_id, id_sucursal);
--
-- Name: usuario_sucursal usuario_sucursal_tenant_id_id_usuario_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.usuario_sucursal
    ADD CONSTRAINT usuario_sucursal_tenant_id_id_usuario_fkey FOREIGN KEY (tenant_id, id_usuario) REFERENCES public.usuario(tenant_id, id_usuario);
--
-- Name: usuario usuario_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.usuario
    ADD CONSTRAINT usuario_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.empresa(id_empresa);
--
-- Name: usuario_token usuario_token_id_usuario_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.usuario_token
    ADD CONSTRAINT usuario_token_id_usuario_fkey FOREIGN KEY (id_usuario) REFERENCES public.usuario(id_usuario) ON DELETE CASCADE;
--
-- Name: usuario_token usuario_token_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.usuario_token
    ADD CONSTRAINT usuario_token_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.empresa(id_empresa);
--
-- Name: variante_color variante_color_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.variante_color
    ADD CONSTRAINT variante_color_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.empresa(id_empresa);
--
-- Name: variante_color variante_color_tenant_id_id_color_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.variante_color
    ADD CONSTRAINT variante_color_tenant_id_id_color_fkey FOREIGN KEY (tenant_id, id_color) REFERENCES public.color(tenant_id, id_color);
--
-- Name: variante_color variante_color_tenant_id_id_variante_prenda_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.variante_color
    ADD CONSTRAINT variante_color_tenant_id_id_variante_prenda_fkey FOREIGN KEY (tenant_id, id_variante_prenda) REFERENCES public.variante_prenda(tenant_id, id_variante_prenda);
--
-- Name: variante_prenda variante_prenda_id_color_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.variante_prenda
    ADD CONSTRAINT variante_prenda_id_color_fkey FOREIGN KEY (id_color) REFERENCES public.color(id_color) ON DELETE RESTRICT;
--
-- Name: variante_prenda variante_prenda_id_prenda_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.variante_prenda
    ADD CONSTRAINT variante_prenda_id_prenda_fkey FOREIGN KEY (id_prenda) REFERENCES public.prenda(id_prenda) ON DELETE CASCADE;
--
-- Name: variante_prenda variante_prenda_id_talla_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.variante_prenda
    ADD CONSTRAINT variante_prenda_id_talla_fkey FOREIGN KEY (id_talla) REFERENCES public.talla(id_talla) ON DELETE RESTRICT;
--
-- Name: variante_prenda variante_prenda_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.variante_prenda
    ADD CONSTRAINT variante_prenda_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.empresa(id_empresa);
--
-- Name: venta venta_id_cajero_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.venta
    ADD CONSTRAINT venta_id_cajero_fkey FOREIGN KEY (id_cajero) REFERENCES public.usuario(id_usuario) ON DELETE RESTRICT;
--
-- Name: venta venta_id_cliente_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.venta
    ADD CONSTRAINT venta_id_cliente_fkey FOREIGN KEY (id_cliente) REFERENCES public.cliente(id_cliente) ON DELETE RESTRICT;
--
-- Name: venta venta_id_reserva_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.venta
    ADD CONSTRAINT venta_id_reserva_fkey FOREIGN KEY (id_reserva) REFERENCES public.reserva(id_reserva) ON DELETE SET NULL;
--
-- Name: venta venta_id_sucursal_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.venta
    ADD CONSTRAINT venta_id_sucursal_fkey FOREIGN KEY (id_sucursal) REFERENCES public.sucursal(id_sucursal) ON DELETE RESTRICT;
--
-- Name: venta venta_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE ONLY public.venta
    ADD CONSTRAINT venta_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.empresa(id_empresa);
--
-- Name: ajuste_monetario; Type: ROW SECURITY; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE public.ajuste_monetario ENABLE ROW LEVEL SECURITY;
--
-- Name: auditoria_identidad; Type: ROW SECURITY; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE public.auditoria_identidad ENABLE ROW LEVEL SECURITY;
--
-- Name: bitacora; Type: ROW SECURITY; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE public.bitacora ENABLE ROW LEVEL SECURITY;
--
-- Name: cambio branch_scope; Type: POLICY; Schema: public; Owner: fashionstore_p2_owner
--
CREATE POLICY branch_scope ON public.cambio AS RESTRICTIVE USING (public.branch_visible(id_sucursal)) WITH CHECK (public.branch_visible(id_sucursal));
--
-- Name: compra branch_scope; Type: POLICY; Schema: public; Owner: fashionstore_p2_owner
--
CREATE POLICY branch_scope ON public.compra AS RESTRICTIVE USING (public.branch_visible(id_sucursal)) WITH CHECK (public.branch_visible(id_sucursal));
--
-- Name: inventario branch_scope; Type: POLICY; Schema: public; Owner: fashionstore_p2_owner
--
CREATE POLICY branch_scope ON public.inventario AS RESTRICTIVE USING (public.branch_visible(id_sucursal)) WITH CHECK (public.branch_visible(id_sucursal));
--
-- Name: movimiento_inventario branch_scope; Type: POLICY; Schema: public; Owner: fashionstore_p2_owner
--
CREATE POLICY branch_scope ON public.movimiento_inventario AS RESTRICTIVE USING (public.branch_visible(id_sucursal)) WITH CHECK (public.branch_visible(id_sucursal));
--
-- Name: reserva branch_scope; Type: POLICY; Schema: public; Owner: fashionstore_p2_owner
--
CREATE POLICY branch_scope ON public.reserva AS RESTRICTIVE USING (public.branch_visible(id_sucursal)) WITH CHECK (public.branch_visible(id_sucursal));
--
-- Name: retencion branch_scope; Type: POLICY; Schema: public; Owner: fashionstore_p2_owner
--
CREATE POLICY branch_scope ON public.retencion AS RESTRICTIVE USING (public.branch_visible(id_sucursal)) WITH CHECK (public.branch_visible(id_sucursal));
--
-- Name: venta branch_scope; Type: POLICY; Schema: public; Owner: fashionstore_p2_owner
--
CREATE POLICY branch_scope ON public.venta AS RESTRICTIVE USING (public.branch_visible(id_sucursal)) WITH CHECK (public.branch_visible(id_sucursal));
--
-- Name: cambio; Type: ROW SECURITY; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE public.cambio ENABLE ROW LEVEL SECURITY;
--
-- Name: categoria; Type: ROW SECURITY; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE public.categoria ENABLE ROW LEVEL SECURITY;
--
-- Name: ciudad; Type: ROW SECURITY; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE public.ciudad ENABLE ROW LEVEL SECURITY;
--
-- Name: cliente; Type: ROW SECURITY; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE public.cliente ENABLE ROW LEVEL SECURITY;
--
-- Name: color; Type: ROW SECURITY; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE public.color ENABLE ROW LEVEL SECURITY;
--
-- Name: compra; Type: ROW SECURITY; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE public.compra ENABLE ROW LEVEL SECURITY;
--
-- Name: comprobante; Type: ROW SECURITY; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE public.comprobante ENABLE ROW LEVEL SECURITY;
--
-- Name: cuenta_global; Type: ROW SECURITY; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE public.cuenta_global ENABLE ROW LEVEL SECURITY;
--
-- Name: cuenta_recuperacion; Type: ROW SECURITY; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE public.cuenta_recuperacion ENABLE ROW LEVEL SECURITY;
--
-- Name: pago_transaccion customer_payments; Type: POLICY; Schema: public; Owner: fashionstore_p2_owner
--
CREATE POLICY customer_payments ON public.pago_transaccion AS RESTRICTIVE USING (((current_setting('app.role'::text, true) <> 'Cliente'::text) OR (EXISTS ( SELECT 1
   FROM public.reserva r
  WHERE (r.id_reserva = pago_transaccion.id_reserva))) OR (EXISTS ( SELECT 1
   FROM public.venta v
  WHERE (v.id_venta = pago_transaccion.id_venta)))));
--
-- Name: comprobante customer_receipts; Type: POLICY; Schema: public; Owner: fashionstore_p2_owner
--
CREATE POLICY customer_receipts ON public.comprobante AS RESTRICTIVE USING (((current_setting('app.role'::text, true) <> 'Cliente'::text) OR (EXISTS ( SELECT 1
   FROM public.venta v
  WHERE (v.id_venta = comprobante.id_venta)))));
--
-- Name: detalle_reserva customer_reservation_lines; Type: POLICY; Schema: public; Owner: fashionstore_p2_owner
--
CREATE POLICY customer_reservation_lines ON public.detalle_reserva AS RESTRICTIVE USING (((current_setting('app.role'::text, true) <> 'Cliente'::text) OR (EXISTS ( SELECT 1
   FROM public.reserva r
  WHERE (r.id_reserva = detalle_reserva.id_reserva)))));
--
-- Name: reserva customer_reservations; Type: POLICY; Schema: public; Owner: fashionstore_p2_owner
--
CREATE POLICY customer_reservations ON public.reserva AS RESTRICTIVE USING (((current_setting('app.role'::text, true) <> 'Cliente'::text) OR (id_cliente = public.own_customer()))) WITH CHECK (((current_setting('app.role'::text, true) <> 'Cliente'::text) OR (id_cliente = public.own_customer())));
--
-- Name: detalle_venta customer_sale_lines; Type: POLICY; Schema: public; Owner: fashionstore_p2_owner
--
CREATE POLICY customer_sale_lines ON public.detalle_venta AS RESTRICTIVE USING (((current_setting('app.role'::text, true) <> 'Cliente'::text) OR (EXISTS ( SELECT 1
   FROM public.venta v
  WHERE (v.id_venta = detalle_venta.id_venta)))));
--
-- Name: venta customer_sales; Type: POLICY; Schema: public; Owner: fashionstore_p2_owner
--
CREATE POLICY customer_sales ON public.venta AS RESTRICTIVE USING (((current_setting('app.role'::text, true) <> 'Cliente'::text) OR (id_cliente = public.own_customer()))) WITH CHECK (((current_setting('app.role'::text, true) <> 'Cliente'::text) OR (id_cliente = public.own_customer())));
--
-- Name: detalle_compra; Type: ROW SECURITY; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE public.detalle_compra ENABLE ROW LEVEL SECURITY;
--
-- Name: detalle_reserva; Type: ROW SECURITY; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE public.detalle_reserva ENABLE ROW LEVEL SECURITY;
--
-- Name: detalle_venta; Type: ROW SECURITY; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE public.detalle_venta ENABLE ROW LEVEL SECURITY;
--
-- Name: dispositivo_push; Type: ROW SECURITY; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE public.dispositivo_push ENABLE ROW LEVEL SECURITY;
--
-- Name: imagen_prenda; Type: ROW SECURITY; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE public.imagen_prenda ENABLE ROW LEVEL SECURITY;
--
-- Name: inventario; Type: ROW SECURITY; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE public.inventario ENABLE ROW LEVEL SECURITY;
--
-- Name: movimiento_inventario; Type: ROW SECURITY; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE public.movimiento_inventario ENABLE ROW LEVEL SECURITY;
--
-- Name: notificacion; Type: ROW SECURITY; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE public.notificacion ENABLE ROW LEVEL SECURITY;
--
-- Name: operacion_sync; Type: ROW SECURITY; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE public.operacion_sync ENABLE ROW LEVEL SECURITY;
--
-- Name: cambio own_changes; Type: POLICY; Schema: public; Owner: fashionstore_p2_owner
--
CREATE POLICY own_changes ON public.cambio AS RESTRICTIVE USING (((current_setting('app.role'::text, true) <> 'Cliente'::text) OR (id_cliente = public.own_customer())));
--
-- Name: notificacion own_notifications; Type: POLICY; Schema: public; Owner: fashionstore_p2_owner
--
CREATE POLICY own_notifications ON public.notificacion AS RESTRICTIVE USING (((current_setting('app.role'::text, true) <> 'Cliente'::text) OR (id_cliente = public.own_customer())));
--
-- Name: operacion_sync own_operations; Type: POLICY; Schema: public; Owner: fashionstore_p2_owner
--
CREATE POLICY own_operations ON public.operacion_sync AS RESTRICTIVE USING (((current_setting('app.role'::text, true) <> 'Cliente'::text) OR (author_id = (NULLIF(current_setting('app.user_id'::text, true), ''::text))::integer)));
--
-- Name: pago_transaccion; Type: ROW SECURITY; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE public.pago_transaccion ENABLE ROW LEVEL SECURITY;
--
-- Name: pago_transaccion payment_branch; Type: POLICY; Schema: public; Owner: fashionstore_p2_owner
--
CREATE POLICY payment_branch ON public.pago_transaccion AS RESTRICTIVE USING ((((id_reserva IS NOT NULL) AND (EXISTS ( SELECT 1
   FROM public.reserva r
  WHERE (r.id_reserva = pago_transaccion.id_reserva)))) OR ((id_venta IS NOT NULL) AND (EXISTS ( SELECT 1
   FROM public.venta v
  WHERE (v.id_venta = pago_transaccion.id_venta)))) OR ((id_reserva IS NULL) AND (id_venta IS NULL) AND (current_setting('app.role'::text, true) <> 'Cliente'::text))));
--
-- Name: prenda; Type: ROW SECURITY; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE public.prenda ENABLE ROW LEVEL SECURITY;
--
-- Name: proveedor; Type: ROW SECURITY; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE public.proveedor ENABLE ROW LEVEL SECURITY;
--
-- Name: detalle_compra purchase_detail_branch; Type: POLICY; Schema: public; Owner: fashionstore_p2_owner
--
CREATE POLICY purchase_detail_branch ON public.detalle_compra AS RESTRICTIVE USING ((EXISTS ( SELECT 1
   FROM public.compra c
  WHERE (c.id_compra = detalle_compra.id_compra)))) WITH CHECK ((EXISTS ( SELECT 1
   FROM public.compra c
  WHERE (c.id_compra = detalle_compra.id_compra))));
--
-- Name: push_entrega; Type: ROW SECURITY; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE public.push_entrega ENABLE ROW LEVEL SECURITY;
--
-- Name: push_entrega push_tenant; Type: POLICY; Schema: public; Owner: fashionstore_p2_owner
--
CREATE POLICY push_tenant ON public.push_entrega USING ((tenant_id = public.current_tenant())) WITH CHECK ((tenant_id = public.current_tenant()));
--
-- Name: comprobante receipt_branch; Type: POLICY; Schema: public; Owner: fashionstore_p2_owner
--
CREATE POLICY receipt_branch ON public.comprobante AS RESTRICTIVE USING ((EXISTS ( SELECT 1
   FROM public.venta v
  WHERE (v.id_venta = comprobante.id_venta)))) WITH CHECK ((EXISTS ( SELECT 1
   FROM public.venta v
  WHERE (v.id_venta = comprobante.id_venta))));
--
-- Name: reporte_resultado; Type: ROW SECURITY; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE public.reporte_resultado ENABLE ROW LEVEL SECURITY;
--
-- Name: reporte_resultado reporte_tenant; Type: POLICY; Schema: public; Owner: fashionstore_p2_owner
--
CREATE POLICY reporte_tenant ON public.reporte_resultado USING (((tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::bigint) AND (author_id = (NULLIF(current_setting('app.user_id'::text, true), ''::text))::integer))) WITH CHECK (((tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::bigint) AND (author_id = (NULLIF(current_setting('app.user_id'::text, true), ''::text))::integer)));
--
-- Name: reserva; Type: ROW SECURITY; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE public.reserva ENABLE ROW LEVEL SECURITY;
--
-- Name: detalle_reserva reservation_detail_branch; Type: POLICY; Schema: public; Owner: fashionstore_p2_owner
--
CREATE POLICY reservation_detail_branch ON public.detalle_reserva AS RESTRICTIVE USING ((EXISTS ( SELECT 1
   FROM public.reserva r
  WHERE (r.id_reserva = detalle_reserva.id_reserva)))) WITH CHECK ((EXISTS ( SELECT 1
   FROM public.reserva r
  WHERE (r.id_reserva = detalle_reserva.id_reserva))));
--
-- Name: retencion; Type: ROW SECURITY; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE public.retencion ENABLE ROW LEVEL SECURITY;
--
-- Name: rol; Type: ROW SECURITY; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE public.rol ENABLE ROW LEVEL SECURITY;
--
-- Name: rol_permiso; Type: ROW SECURITY; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE public.rol_permiso ENABLE ROW LEVEL SECURITY;
--
-- Name: detalle_venta sale_detail_branch; Type: POLICY; Schema: public; Owner: fashionstore_p2_owner
--
CREATE POLICY sale_detail_branch ON public.detalle_venta AS RESTRICTIVE USING ((EXISTS ( SELECT 1
   FROM public.venta v
  WHERE (v.id_venta = detalle_venta.id_venta)))) WITH CHECK ((EXISTS ( SELECT 1
   FROM public.venta v
  WHERE (v.id_venta = detalle_venta.id_venta))));
--
-- Name: stripe_event; Type: ROW SECURITY; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE public.stripe_event ENABLE ROW LEVEL SECURITY;
--
-- Name: stripe_event stripe_event_tenant; Type: POLICY; Schema: public; Owner: fashionstore_p2_owner
--
CREATE POLICY stripe_event_tenant ON public.stripe_event USING ((tenant_id = public.current_tenant())) WITH CHECK ((tenant_id = public.current_tenant()));
--
-- Name: sucursal; Type: ROW SECURITY; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE public.sucursal ENABLE ROW LEVEL SECURITY;
--
-- Name: suscripcion; Type: ROW SECURITY; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE public.suscripcion ENABLE ROW LEVEL SECURITY;
--
-- Name: talla; Type: ROW SECURITY; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE public.talla ENABLE ROW LEVEL SECURITY;
--
-- Name: temporada; Type: ROW SECURITY; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE public.temporada ENABLE ROW LEVEL SECURITY;
--
-- Name: ajuste_monetario tenant_isolation; Type: POLICY; Schema: public; Owner: fashionstore_p2_owner
--
CREATE POLICY tenant_isolation ON public.ajuste_monetario USING ((tenant_id = public.current_tenant())) WITH CHECK ((tenant_id = public.current_tenant()));
--
-- Name: bitacora tenant_isolation; Type: POLICY; Schema: public; Owner: fashionstore_p2_owner
--
CREATE POLICY tenant_isolation ON public.bitacora USING ((tenant_id = public.current_tenant())) WITH CHECK ((tenant_id = public.current_tenant()));
--
-- Name: cambio tenant_isolation; Type: POLICY; Schema: public; Owner: fashionstore_p2_owner
--
CREATE POLICY tenant_isolation ON public.cambio USING ((tenant_id = public.current_tenant())) WITH CHECK ((tenant_id = public.current_tenant()));
--
-- Name: categoria tenant_isolation; Type: POLICY; Schema: public; Owner: fashionstore_p2_owner
--
CREATE POLICY tenant_isolation ON public.categoria USING ((tenant_id = public.current_tenant())) WITH CHECK ((tenant_id = public.current_tenant()));
--
-- Name: ciudad tenant_isolation; Type: POLICY; Schema: public; Owner: fashionstore_p2_owner
--
CREATE POLICY tenant_isolation ON public.ciudad USING ((tenant_id = public.current_tenant())) WITH CHECK ((tenant_id = public.current_tenant()));
--
-- Name: cliente tenant_isolation; Type: POLICY; Schema: public; Owner: fashionstore_p2_owner
--
CREATE POLICY tenant_isolation ON public.cliente USING ((tenant_id = public.current_tenant())) WITH CHECK ((tenant_id = public.current_tenant()));
--
-- Name: color tenant_isolation; Type: POLICY; Schema: public; Owner: fashionstore_p2_owner
--
CREATE POLICY tenant_isolation ON public.color USING ((tenant_id = public.current_tenant())) WITH CHECK ((tenant_id = public.current_tenant()));
--
-- Name: compra tenant_isolation; Type: POLICY; Schema: public; Owner: fashionstore_p2_owner
--
CREATE POLICY tenant_isolation ON public.compra USING ((tenant_id = public.current_tenant())) WITH CHECK ((tenant_id = public.current_tenant()));
--
-- Name: comprobante tenant_isolation; Type: POLICY; Schema: public; Owner: fashionstore_p2_owner
--
CREATE POLICY tenant_isolation ON public.comprobante USING ((tenant_id = public.current_tenant())) WITH CHECK ((tenant_id = public.current_tenant()));
--
-- Name: detalle_compra tenant_isolation; Type: POLICY; Schema: public; Owner: fashionstore_p2_owner
--
CREATE POLICY tenant_isolation ON public.detalle_compra USING ((tenant_id = public.current_tenant())) WITH CHECK ((tenant_id = public.current_tenant()));
--
-- Name: detalle_reserva tenant_isolation; Type: POLICY; Schema: public; Owner: fashionstore_p2_owner
--
CREATE POLICY tenant_isolation ON public.detalle_reserva USING ((tenant_id = public.current_tenant())) WITH CHECK ((tenant_id = public.current_tenant()));
--
-- Name: detalle_venta tenant_isolation; Type: POLICY; Schema: public; Owner: fashionstore_p2_owner
--
CREATE POLICY tenant_isolation ON public.detalle_venta USING ((tenant_id = public.current_tenant())) WITH CHECK ((tenant_id = public.current_tenant()));
--
-- Name: dispositivo_push tenant_isolation; Type: POLICY; Schema: public; Owner: fashionstore_p2_owner
--
CREATE POLICY tenant_isolation ON public.dispositivo_push USING ((tenant_id = public.current_tenant())) WITH CHECK ((tenant_id = public.current_tenant()));
--
-- Name: imagen_prenda tenant_isolation; Type: POLICY; Schema: public; Owner: fashionstore_p2_owner
--
CREATE POLICY tenant_isolation ON public.imagen_prenda USING ((tenant_id = public.current_tenant())) WITH CHECK ((tenant_id = public.current_tenant()));
--
-- Name: inventario tenant_isolation; Type: POLICY; Schema: public; Owner: fashionstore_p2_owner
--
CREATE POLICY tenant_isolation ON public.inventario USING ((tenant_id = public.current_tenant())) WITH CHECK ((tenant_id = public.current_tenant()));
--
-- Name: movimiento_inventario tenant_isolation; Type: POLICY; Schema: public; Owner: fashionstore_p2_owner
--
CREATE POLICY tenant_isolation ON public.movimiento_inventario USING ((tenant_id = public.current_tenant())) WITH CHECK ((tenant_id = public.current_tenant()));
--
-- Name: notificacion tenant_isolation; Type: POLICY; Schema: public; Owner: fashionstore_p2_owner
--
CREATE POLICY tenant_isolation ON public.notificacion USING ((tenant_id = public.current_tenant())) WITH CHECK ((tenant_id = public.current_tenant()));
--
-- Name: operacion_sync tenant_isolation; Type: POLICY; Schema: public; Owner: fashionstore_p2_owner
--
CREATE POLICY tenant_isolation ON public.operacion_sync USING ((tenant_id = public.current_tenant())) WITH CHECK ((tenant_id = public.current_tenant()));
--
-- Name: pago_transaccion tenant_isolation; Type: POLICY; Schema: public; Owner: fashionstore_p2_owner
--
CREATE POLICY tenant_isolation ON public.pago_transaccion USING ((tenant_id = public.current_tenant())) WITH CHECK ((tenant_id = public.current_tenant()));
--
-- Name: prenda tenant_isolation; Type: POLICY; Schema: public; Owner: fashionstore_p2_owner
--
CREATE POLICY tenant_isolation ON public.prenda USING ((tenant_id = public.current_tenant())) WITH CHECK ((tenant_id = public.current_tenant()));
--
-- Name: proveedor tenant_isolation; Type: POLICY; Schema: public; Owner: fashionstore_p2_owner
--
CREATE POLICY tenant_isolation ON public.proveedor USING ((tenant_id = public.current_tenant())) WITH CHECK ((tenant_id = public.current_tenant()));
--
-- Name: reserva tenant_isolation; Type: POLICY; Schema: public; Owner: fashionstore_p2_owner
--
CREATE POLICY tenant_isolation ON public.reserva USING ((tenant_id = public.current_tenant())) WITH CHECK ((tenant_id = public.current_tenant()));
--
-- Name: retencion tenant_isolation; Type: POLICY; Schema: public; Owner: fashionstore_p2_owner
--
CREATE POLICY tenant_isolation ON public.retencion USING ((tenant_id = public.current_tenant())) WITH CHECK ((tenant_id = public.current_tenant()));
--
-- Name: rol tenant_isolation; Type: POLICY; Schema: public; Owner: fashionstore_p2_owner
--
CREATE POLICY tenant_isolation ON public.rol USING ((tenant_id = public.current_tenant())) WITH CHECK ((tenant_id = public.current_tenant()));
--
-- Name: rol_permiso tenant_isolation; Type: POLICY; Schema: public; Owner: fashionstore_p2_owner
--
CREATE POLICY tenant_isolation ON public.rol_permiso USING ((tenant_id = public.current_tenant())) WITH CHECK ((tenant_id = public.current_tenant()));
--
-- Name: sucursal tenant_isolation; Type: POLICY; Schema: public; Owner: fashionstore_p2_owner
--
CREATE POLICY tenant_isolation ON public.sucursal USING ((tenant_id = public.current_tenant())) WITH CHECK ((tenant_id = public.current_tenant()));
--
-- Name: suscripcion tenant_isolation; Type: POLICY; Schema: public; Owner: fashionstore_p2_owner
--
CREATE POLICY tenant_isolation ON public.suscripcion USING ((tenant_id = public.current_tenant())) WITH CHECK ((tenant_id = public.current_tenant()));
--
-- Name: talla tenant_isolation; Type: POLICY; Schema: public; Owner: fashionstore_p2_owner
--
CREATE POLICY tenant_isolation ON public.talla USING ((tenant_id = public.current_tenant())) WITH CHECK ((tenant_id = public.current_tenant()));
--
-- Name: temporada tenant_isolation; Type: POLICY; Schema: public; Owner: fashionstore_p2_owner
--
CREATE POLICY tenant_isolation ON public.temporada USING ((tenant_id = public.current_tenant())) WITH CHECK ((tenant_id = public.current_tenant()));
--
-- Name: usuario tenant_isolation; Type: POLICY; Schema: public; Owner: fashionstore_p2_owner
--
CREATE POLICY tenant_isolation ON public.usuario USING ((tenant_id = public.current_tenant())) WITH CHECK ((tenant_id = public.current_tenant()));
--
-- Name: usuario_sucursal tenant_isolation; Type: POLICY; Schema: public; Owner: fashionstore_p2_owner
--
CREATE POLICY tenant_isolation ON public.usuario_sucursal USING ((tenant_id = public.current_tenant())) WITH CHECK ((tenant_id = public.current_tenant()));
--
-- Name: usuario_token tenant_isolation; Type: POLICY; Schema: public; Owner: fashionstore_p2_owner
--
CREATE POLICY tenant_isolation ON public.usuario_token USING ((tenant_id = public.current_tenant())) WITH CHECK ((tenant_id = public.current_tenant()));
--
-- Name: variante_color tenant_isolation; Type: POLICY; Schema: public; Owner: fashionstore_p2_owner
--
CREATE POLICY tenant_isolation ON public.variante_color USING ((tenant_id = public.current_tenant())) WITH CHECK ((tenant_id = public.current_tenant()));
--
-- Name: variante_prenda tenant_isolation; Type: POLICY; Schema: public; Owner: fashionstore_p2_owner
--
CREATE POLICY tenant_isolation ON public.variante_prenda USING ((tenant_id = public.current_tenant())) WITH CHECK ((tenant_id = public.current_tenant()));
--
-- Name: venta tenant_isolation; Type: POLICY; Schema: public; Owner: fashionstore_p2_owner
--
CREATE POLICY tenant_isolation ON public.venta USING ((tenant_id = public.current_tenant())) WITH CHECK ((tenant_id = public.current_tenant()));
--
-- Name: usuario; Type: ROW SECURITY; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE public.usuario ENABLE ROW LEVEL SECURITY;
--
-- Name: usuario_sucursal; Type: ROW SECURITY; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE public.usuario_sucursal ENABLE ROW LEVEL SECURITY;
--
-- Name: usuario_token; Type: ROW SECURITY; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE public.usuario_token ENABLE ROW LEVEL SECURITY;
--
-- Name: variante_color; Type: ROW SECURITY; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE public.variante_color ENABLE ROW LEVEL SECURITY;
--
-- Name: variante_prenda; Type: ROW SECURITY; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE public.variante_prenda ENABLE ROW LEVEL SECURITY;
--
-- Name: venta; Type: ROW SECURITY; Schema: public; Owner: fashionstore_p2_owner
--
ALTER TABLE public.venta ENABLE ROW LEVEL SECURITY;
--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: pg_database_owner
--
GRANT USAGE ON SCHEMA public TO fashionstore_p2_app;
--
-- Name: FUNCTION bind_push_device(value text); Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
REVOKE ALL ON FUNCTION public.bind_push_device(value text) FROM PUBLIC;
GRANT ALL ON FUNCTION public.bind_push_device(value text) TO fashionstore_p2_app;
--
-- Name: FUNCTION identity_customer_profile(p_account bigint, p_tenant integer); Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
REVOKE ALL ON FUNCTION public.identity_customer_profile(p_account bigint, p_tenant integer) FROM PUBLIC;
GRANT ALL ON FUNCTION public.identity_customer_profile(p_account bigint, p_tenant integer) TO fashionstore_p2_app;
--
-- Name: FUNCTION identity_event(p_id bigint, p_action text); Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
REVOKE ALL ON FUNCTION public.identity_event(p_id bigint, p_action text) FROM PUBLIC;
GRANT ALL ON FUNCTION public.identity_event(p_id bigint, p_action text) TO fashionstore_p2_app;
--
-- Name: FUNCTION identity_index_user(p_user integer); Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
REVOKE ALL ON FUNCTION public.identity_index_user(p_user integer) FROM PUBLIC;
GRANT ALL ON FUNCTION public.identity_index_user(p_user integer) TO fashionstore_p2_app;
--
-- Name: FUNCTION identity_lookup(p_correo text, p_id bigint); Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
REVOKE ALL ON FUNCTION public.identity_lookup(p_correo text, p_id bigint) FROM PUBLIC;
GRANT ALL ON FUNCTION public.identity_lookup(p_correo text, p_id bigint) TO fashionstore_p2_app;
--
-- Name: FUNCTION identity_register(p_data jsonb); Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
REVOKE ALL ON FUNCTION public.identity_register(p_data jsonb) FROM PUBLIC;
GRANT ALL ON FUNCTION public.identity_register(p_data jsonb) TO fashionstore_p2_app;
--
-- Name: FUNCTION identity_reset_apply(p_hash text, p_password_hash text); Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
REVOKE ALL ON FUNCTION public.identity_reset_apply(p_hash text, p_password_hash text) FROM PUBLIC;
GRANT ALL ON FUNCTION public.identity_reset_apply(p_hash text, p_password_hash text) TO fashionstore_p2_app;
--
-- Name: FUNCTION identity_reset_issue(p_id bigint, p_hash text); Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
REVOKE ALL ON FUNCTION public.identity_reset_issue(p_id bigint, p_hash text) FROM PUBLIC;
GRANT ALL ON FUNCTION public.identity_reset_issue(p_id bigint, p_hash text) TO fashionstore_p2_app;
--
-- Name: FUNCTION identity_reset_lookup(p_hash text); Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
REVOKE ALL ON FUNCTION public.identity_reset_lookup(p_hash text) FROM PUBLIC;
GRANT ALL ON FUNCTION public.identity_reset_lookup(p_hash text) TO fashionstore_p2_app;
--
-- Name: FUNCTION identity_revoke(p_id bigint); Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
REVOKE ALL ON FUNCTION public.identity_revoke(p_id bigint) FROM PUBLIC;
GRANT ALL ON FUNCTION public.identity_revoke(p_id bigint) TO fashionstore_p2_app;
--
-- Name: TABLE ajuste_monetario; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.ajuste_monetario TO fashionstore_p2_app;
--
-- Name: SEQUENCE ajuste_monetario_id_ajuste_seq; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,USAGE ON SEQUENCE public.ajuste_monetario_id_ajuste_seq TO fashionstore_p2_app;
--
-- Name: TABLE auditoria_identidad; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.auditoria_identidad TO fashionstore_p2_app;
--
-- Name: SEQUENCE auditoria_identidad_id_seq; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,USAGE ON SEQUENCE public.auditoria_identidad_id_seq TO fashionstore_p2_app;
--
-- Name: TABLE bitacora; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,INSERT ON TABLE public.bitacora TO fashionstore_p2_app;
--
-- Name: SEQUENCE bitacora_id_bitacora_seq; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,USAGE ON SEQUENCE public.bitacora_id_bitacora_seq TO fashionstore_p2_app;
--
-- Name: TABLE cambio; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.cambio TO fashionstore_p2_app;
--
-- Name: SEQUENCE cambio_id_cambio_seq; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,USAGE ON SEQUENCE public.cambio_id_cambio_seq TO fashionstore_p2_app;
--
-- Name: TABLE categoria; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.categoria TO fashionstore_p2_app;
--
-- Name: SEQUENCE categoria_id_categoria_seq; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,USAGE ON SEQUENCE public.categoria_id_categoria_seq TO fashionstore_p2_app;
--
-- Name: TABLE ciudad; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.ciudad TO fashionstore_p2_app;
--
-- Name: SEQUENCE ciudad_id_ciudad_seq; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,USAGE ON SEQUENCE public.ciudad_id_ciudad_seq TO fashionstore_p2_app;
--
-- Name: TABLE cliente; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.cliente TO fashionstore_p2_app;
--
-- Name: SEQUENCE cliente_id_cliente_seq; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,USAGE ON SEQUENCE public.cliente_id_cliente_seq TO fashionstore_p2_app;
--
-- Name: TABLE color; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.color TO fashionstore_p2_app;
--
-- Name: SEQUENCE color_id_color_seq; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,USAGE ON SEQUENCE public.color_id_color_seq TO fashionstore_p2_app;
--
-- Name: TABLE compra; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.compra TO fashionstore_p2_app;
--
-- Name: SEQUENCE compra_id_compra_seq; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,USAGE ON SEQUENCE public.compra_id_compra_seq TO fashionstore_p2_app;
--
-- Name: TABLE comprobante; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.comprobante TO fashionstore_p2_app;
--
-- Name: SEQUENCE comprobante_id_comprobante_seq; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,USAGE ON SEQUENCE public.comprobante_id_comprobante_seq TO fashionstore_p2_app;
--
-- Name: TABLE cuenta_global; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.cuenta_global TO fashionstore_p2_app;
--
-- Name: SEQUENCE cuenta_global_id_seq; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,USAGE ON SEQUENCE public.cuenta_global_id_seq TO fashionstore_p2_app;
--
-- Name: TABLE cuenta_recuperacion; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.cuenta_recuperacion TO fashionstore_p2_app;
--
-- Name: TABLE detalle_compra; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.detalle_compra TO fashionstore_p2_app;
--
-- Name: TABLE detalle_reserva; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.detalle_reserva TO fashionstore_p2_app;
--
-- Name: TABLE detalle_venta; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.detalle_venta TO fashionstore_p2_app;
--
-- Name: TABLE dispositivo_push; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.dispositivo_push TO fashionstore_p2_app;
--
-- Name: TABLE empresa; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.empresa TO fashionstore_p2_app;
--
-- Name: SEQUENCE empresa_id_empresa_seq; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,USAGE ON SEQUENCE public.empresa_id_empresa_seq TO fashionstore_p2_app;
--
-- Name: TABLE imagen_prenda; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.imagen_prenda TO fashionstore_p2_app;
--
-- Name: SEQUENCE imagen_prenda_id_imagen_seq; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,USAGE ON SEQUENCE public.imagen_prenda_id_imagen_seq TO fashionstore_p2_app;
--
-- Name: TABLE inventario; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.inventario TO fashionstore_p2_app;
--
-- Name: TABLE retencion; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.retencion TO fashionstore_p2_app;
--
-- Name: TABLE inventario_catalogo; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.inventario_catalogo TO fashionstore_p2_app;
--
-- Name: TABLE movimiento_inventario; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.movimiento_inventario TO fashionstore_p2_app;
--
-- Name: SEQUENCE movimiento_inventario_id_movimiento_seq; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,USAGE ON SEQUENCE public.movimiento_inventario_id_movimiento_seq TO fashionstore_p2_app;
--
-- Name: TABLE notificacion; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.notificacion TO fashionstore_p2_app;
--
-- Name: SEQUENCE notificacion_id_notificacion_seq; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,USAGE ON SEQUENCE public.notificacion_id_notificacion_seq TO fashionstore_p2_app;
--
-- Name: TABLE operacion_sync; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.operacion_sync TO fashionstore_p2_app;
--
-- Name: TABLE pago_transaccion; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.pago_transaccion TO fashionstore_p2_app;
--
-- Name: SEQUENCE pago_transaccion_id_pago_seq; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,USAGE ON SEQUENCE public.pago_transaccion_id_pago_seq TO fashionstore_p2_app;
--
-- Name: TABLE permiso; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.permiso TO fashionstore_p2_app;
--
-- Name: SEQUENCE permiso_id_permiso_seq; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,USAGE ON SEQUENCE public.permiso_id_permiso_seq TO fashionstore_p2_app;
--
-- Name: TABLE plan; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.plan TO fashionstore_p2_app;
--
-- Name: SEQUENCE plan_id_plan_seq; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,USAGE ON SEQUENCE public.plan_id_plan_seq TO fashionstore_p2_app;
--
-- Name: TABLE prenda; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.prenda TO fashionstore_p2_app;
--
-- Name: SEQUENCE prenda_id_prenda_seq; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,USAGE ON SEQUENCE public.prenda_id_prenda_seq TO fashionstore_p2_app;
--
-- Name: TABLE proveedor; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.proveedor TO fashionstore_p2_app;
--
-- Name: SEQUENCE proveedor_id_proveedor_seq; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,USAGE ON SEQUENCE public.proveedor_id_proveedor_seq TO fashionstore_p2_app;
--
-- Name: TABLE push_entrega; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.push_entrega TO fashionstore_p2_app;
--
-- Name: TABLE reporte_resultado; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.reporte_resultado TO fashionstore_p2_app;
--
-- Name: TABLE reserva; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.reserva TO fashionstore_p2_app;
--
-- Name: SEQUENCE reserva_id_reserva_seq; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,USAGE ON SEQUENCE public.reserva_id_reserva_seq TO fashionstore_p2_app;
--
-- Name: TABLE rol; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.rol TO fashionstore_p2_app;
--
-- Name: SEQUENCE rol_id_rol_seq; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,USAGE ON SEQUENCE public.rol_id_rol_seq TO fashionstore_p2_app;
--
-- Name: TABLE rol_permiso; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.rol_permiso TO fashionstore_p2_app;
--
-- Name: TABLE stripe_event; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.stripe_event TO fashionstore_p2_app;
--
-- Name: TABLE sucursal; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.sucursal TO fashionstore_p2_app;
--
-- Name: SEQUENCE sucursal_id_sucursal_seq; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,USAGE ON SEQUENCE public.sucursal_id_sucursal_seq TO fashionstore_p2_app;
--
-- Name: TABLE suscripcion; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.suscripcion TO fashionstore_p2_app;
--
-- Name: SEQUENCE suscripcion_id_suscripcion_seq; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,USAGE ON SEQUENCE public.suscripcion_id_suscripcion_seq TO fashionstore_p2_app;
--
-- Name: TABLE talla; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.talla TO fashionstore_p2_app;
--
-- Name: SEQUENCE talla_id_talla_seq; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,USAGE ON SEQUENCE public.talla_id_talla_seq TO fashionstore_p2_app;
--
-- Name: TABLE temporada; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.temporada TO fashionstore_p2_app;
--
-- Name: SEQUENCE temporada_id_temporada_seq; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,USAGE ON SEQUENCE public.temporada_id_temporada_seq TO fashionstore_p2_app;
--
-- Name: TABLE usuario; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.usuario TO fashionstore_p2_app;
--
-- Name: SEQUENCE usuario_id_usuario_seq; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,USAGE ON SEQUENCE public.usuario_id_usuario_seq TO fashionstore_p2_app;
--
-- Name: TABLE usuario_sucursal; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.usuario_sucursal TO fashionstore_p2_app;
--
-- Name: TABLE usuario_token; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.usuario_token TO fashionstore_p2_app;
--
-- Name: SEQUENCE usuario_token_id_token_seq; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,USAGE ON SEQUENCE public.usuario_token_id_token_seq TO fashionstore_p2_app;
--
-- Name: TABLE variante_color; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.variante_color TO fashionstore_p2_app;
--
-- Name: TABLE variante_prenda; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.variante_prenda TO fashionstore_p2_app;
--
-- Name: SEQUENCE variante_prenda_id_variante_prenda_seq; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,USAGE ON SEQUENCE public.variante_prenda_id_variante_prenda_seq TO fashionstore_p2_app;
--
-- Name: TABLE venta; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.venta TO fashionstore_p2_app;
--
-- Name: SEQUENCE venta_id_venta_seq; Type: ACL; Schema: public; Owner: fashionstore_p2_owner
--
GRANT SELECT,USAGE ON SEQUENCE public.venta_id_venta_seq TO fashionstore_p2_app;
--
-- PostgreSQL database dump complete
--
COMMIT;
