ALTER TABLE variante_prenda ADD COLUMN color_ids INTEGER[] NOT NULL DEFAULT '{}';
UPDATE variante_prenda v SET color_ids=ARRAY(SELECT DISTINCT n FROM (SELECT v.id_color AS n UNION SELECT vc.id_color FROM variante_color vc WHERE vc.tenant_id=v.tenant_id AND vc.id_variante_prenda=v.id_variante_prenda) q ORDER BY n);
DO $$ DECLARE r RECORD; BEGIN
 FOR r IN SELECT conname FROM pg_constraint WHERE conrelid='variante_prenda'::regclass AND contype='u' AND position('id_talla, id_color' in pg_get_constraintdef(oid))>0 LOOP
  EXECUTE format('ALTER TABLE variante_prenda DROP CONSTRAINT %I',r.conname);
 END LOOP;
END $$;
ALTER TABLE variante_prenda ADD CONSTRAINT variant_color_combination UNIQUE(tenant_id,id_prenda,id_talla,color_ids);
CREATE FUNCTION canonical_variant_colors() RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
 NEW.color_ids:=ARRAY(SELECT DISTINCT n FROM unnest(array_append(COALESCE(NEW.color_ids,'{}'::integer[]),NEW.id_color)) n ORDER BY n);
 IF cardinality(NEW.color_ids)>10 OR EXISTS(SELECT 1 FROM unnest(NEW.color_ids) n WHERE NOT EXISTS(SELECT 1 FROM color c WHERE c.tenant_id=NEW.tenant_id AND c.id_color=n)) THEN RAISE EXCEPTION 'Colores de variante no válidos para esta empresa' USING ERRCODE='23503'; END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER canonical_colors BEFORE INSERT OR UPDATE OF color_ids,id_color ON variante_prenda FOR EACH ROW EXECUTE FUNCTION canonical_variant_colors();
CREATE FUNCTION sync_variant_colors() RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
 DELETE FROM variante_color WHERE tenant_id=NEW.tenant_id AND id_variante_prenda=NEW.id_variante_prenda;
 INSERT INTO variante_color(tenant_id,id_variante_prenda,id_color) SELECT NEW.tenant_id,NEW.id_variante_prenda,unnest(NEW.color_ids);
 RETURN NEW;
END $$;
CREATE TRIGGER sync_colors AFTER INSERT OR UPDATE OF color_ids,id_color ON variante_prenda FOR EACH ROW EXECUTE FUNCTION sync_variant_colors();
INSERT INTO variante_color(tenant_id,id_variante_prenda,id_color) SELECT tenant_id,id_variante_prenda,unnest(color_ids) FROM variante_prenda ON CONFLICT DO NOTHING;
CREATE FUNCTION variant_color_label(variant INTEGER) RETURNS TEXT LANGUAGE sql STABLE AS $$
 SELECT string_agg(c.nombre,' / ' ORDER BY c.nombre) FROM variante_color vc JOIN color c USING(tenant_id,id_color) WHERE vc.id_variante_prenda=variant
$$;
