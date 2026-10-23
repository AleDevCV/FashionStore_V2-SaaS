ALTER TABLE prenda ADD CONSTRAINT offer_dates CHECK(oferta_fin IS NULL OR oferta_inicio IS NULL OR oferta_fin>=oferta_inicio);
CREATE UNIQUE INDEX one_sale_per_reservation ON venta(tenant_id,id_reserva) WHERE id_reserva IS NOT NULL;
CREATE TABLE variante_color (
 tenant_id INTEGER NOT NULL DEFAULT current_tenant() REFERENCES empresa,
 id_variante_prenda INTEGER NOT NULL, id_color INTEGER NOT NULL,
 PRIMARY KEY(tenant_id,id_variante_prenda,id_color),
 FOREIGN KEY(tenant_id,id_variante_prenda) REFERENCES variante_prenda(tenant_id,id_variante_prenda),
 FOREIGN KEY(tenant_id,id_color) REFERENCES color(tenant_id,id_color)
);
ALTER TABLE variante_color ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON variante_color USING(tenant_id=current_tenant()) WITH CHECK(tenant_id=current_tenant());
