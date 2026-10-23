ALTER TABLE venta ADD COLUMN origen_datos TEXT NOT NULL DEFAULT 'operativo' CHECK(origen_datos IN ('operativo','demostracion'));
ALTER TABLE venta ADD COLUMN referencia_demo TEXT;
CREATE UNIQUE INDEX venta_demo_reference ON venta(tenant_id,referencia_demo) WHERE referencia_demo IS NOT NULL;
