-- Los operadores SaaS actúan con un identificador propio dentro de la empresa.
-- Su identidad global principal sigue vinculada únicamente a la plataforma.
ALTER TABLE usuario ADD COLUMN platform_account_id BIGINT REFERENCES cuenta_global(id);
ALTER TABLE usuario ADD CONSTRAINT usuario_platform_identity
 CHECK (platform_account_id IS NULL OR account_id IS NULL);
CREATE UNIQUE INDEX usuario_platform_workspace_role
 ON usuario (tenant_id, platform_account_id, id_role)
 WHERE platform_account_id IS NOT NULL;
