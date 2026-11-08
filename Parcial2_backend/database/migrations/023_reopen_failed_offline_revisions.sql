-- Conserva los intentos fallidos y garantiza una sola confirmación por original.
DROP INDEX one_revision_per_operation;
CREATE INDEX sync_revision_history ON operacion_sync(tenant_id,original_operation)
    WHERE original_operation IS NOT NULL;
CREATE UNIQUE INDEX one_confirmed_revision_per_operation ON operacion_sync(tenant_id,original_operation)
    WHERE original_operation IS NOT NULL AND state='CONFIRMADA';

-- Reabre solo las resoluciones automáticas legadas que nunca confirmaron su revisión.
DO $$
DECLARE company INTEGER; previous TEXT:=COALESCE(current_setting('app.tenant_id',true),'');
BEGIN
    FOR company IN SELECT id_empresa FROM empresa LOOP
        PERFORM set_config('app.tenant_id',company::text,true);
        WITH RECURSIVE completed(id) AS (
            SELECT original_operation FROM operacion_sync
            WHERE tenant_id=company AND original_operation IS NOT NULL
              AND (state='CONFIRMADA' OR compensation IS NOT NULL)
            UNION
            SELECT o.original_operation FROM operacion_sync o JOIN completed c ON o.operation_id=c.id
            WHERE o.tenant_id=company AND o.original_operation IS NOT NULL
        )
        UPDATE operacion_sync original SET resolved_at=NULL,resolved_by=NULL,resolution=NULL
        WHERE original.tenant_id=company AND original.resolution='Revisada mediante nueva operación'
          AND NOT EXISTS (SELECT 1 FROM completed WHERE id=original.operation_id);
    END LOOP;
    PERFORM set_config('app.tenant_id',previous,true);
END $$;
