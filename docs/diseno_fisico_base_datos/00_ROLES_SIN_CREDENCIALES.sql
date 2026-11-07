-- Roles de propiedad y autorización; sin contraseñas. No altera roles existentes.
DO $roles$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='fashionstore_p2_app') THEN CREATE ROLE "fashionstore_p2_app" NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS; END IF; END $roles$;
DO $roles$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='fashionstore_p2_owner') THEN CREATE ROLE "fashionstore_p2_owner" NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS; END IF; END $roles$;
