"""El rol nativo configurable conserva el aislamiento sobre PostgreSQL real efímero."""
import importlib.util
from pathlib import Path
import secrets
import pytest
import psycopg2
from conftest import owner_connection

spec = importlib.util.spec_from_file_location('p2_migrate', Path(__file__).resolve().parents[2] / 'scripts/migrate.py')
migration = importlib.util.module_from_spec(spec)
spec.loader.exec_module(migration)


def test_configurable_application_role_cannot_see_unscoped_catalogue(companies):
    role = 'p2_native_' + secrets.token_hex(5)
    with owner_connection() as conn:
        try:
            with conn.cursor(cursor_factory=psycopg2.extensions.cursor) as cur:
                cur.execute('CREATE TABLE IF NOT EXISTS schema_migrations(version TEXT PRIMARY KEY,checksum TEXT NOT NULL)')
                migration.grant_application_access(cur, role, 'isolated-test-only-password')
                cur.execute('SET LOCAL ROLE ' + role)
                cur.execute('SELECT current_user')
                assert cur.fetchone()[0] == role
                cur.execute('SELECT count(*) FROM prenda')
                assert cur.fetchone()[0] == 0
                cur.execute("SELECT set_config('app.tenant_id',%s,true)", (str(companies[0]['tenant']),))
                cur.execute('SELECT DISTINCT tenant_id FROM prenda')
                assert cur.fetchall() == [(companies[0]['tenant'],)]
                with pytest.raises(psycopg2.errors.InsufficientPrivilege):
                    cur.execute('DELETE FROM bitacora')
        finally:
            # La creación de rol y sus permisos se revierten juntos en la base efímera.
            conn.rollback()


def test_application_role_rejects_owner_and_memberships():
    role = 'p2_native_' + secrets.token_hex(5)
    with owner_connection() as conn:
        try:
            with conn.cursor(cursor_factory=psycopg2.extensions.cursor) as cur:
                with pytest.raises(ValueError, match='diferentes'):
                    migration.grant_application_access(cur, 'p2_test_owner', 'unused')
                cur.execute('CREATE ROLE ' + role)
                cur.execute('GRANT pg_monitor TO ' + role)
                with pytest.raises(ValueError, match='pertenecer'):
                    migration.grant_application_access(cur, role, 'unused')
        finally:
            conn.rollback()


def test_application_role_rejects_sql_identifier_injection():
    with pytest.raises(ValueError, match='identificador'):
        migration.grant_application_access(None, 'app; DROP SCHEMA public', 'unused')
