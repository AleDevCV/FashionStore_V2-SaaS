"""Inicializa exclusivamente el PostgreSQL efímero definido en compose.test.yaml."""
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
COMMAND=['docker','compose','-f',str(ROOT/'compose.test.yaml'),'exec','-T','db','psql','-v','ON_ERROR_STOP=1','-U','p2_test_owner','-d','fashionstore_p2_test']
def execute(sql):
    result=subprocess.run(COMMAND,input=sql.encode(),stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    if result.returncode:
        print(result.stdout.decode(errors='replace'));raise SystemExit(result.returncode)

def main():
    # Este reset no acepta parámetros: solo afecta al contenedor temporal de pruebas.
    execute('DROP SCHEMA public CASCADE; CREATE SCHEMA public;')
    for p in sorted((ROOT/'Parcial2_backend/database/migrations').glob('*.sql')):
        execute(p.read_text(encoding='utf-8'));print('Aplicada',p.name)
    execute("""DO $$ BEGIN IF NOT EXISTS(SELECT FROM pg_roles WHERE rolname='fashionstore_app') THEN CREATE ROLE fashionstore_app LOGIN PASSWORD 'p2-test-app-only'; END IF; END $$;
    GRANT USAGE ON SCHEMA public TO fashionstore_app;
    GRANT SELECT,INSERT,UPDATE,DELETE ON ALL TABLES IN SCHEMA public TO fashionstore_app;
    GRANT USAGE,SELECT ON ALL SEQUENCES IN SCHEMA public TO fashionstore_app;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT,INSERT,UPDATE,DELETE ON TABLES TO fashionstore_app;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE,SELECT ON SEQUENCES TO fashionstore_app;""")
    execute('REVOKE UPDATE,DELETE ON bitacora FROM fashionstore_app;')
    execute('GRANT EXECUTE ON FUNCTION bind_push_device(TEXT) TO fashionstore_app;')
    for signature in ('identity_lookup(TEXT,BIGINT)', 'identity_index_user(INTEGER)', 'identity_register(JSONB)',
                      'identity_customer_profile(BIGINT,INTEGER)', 'identity_revoke(BIGINT)',
                      'identity_reset_issue(BIGINT,TEXT)', 'identity_reset_lookup(TEXT)', 'identity_reset_apply(TEXT,TEXT)', 'identity_event(BIGINT,TEXT)'):
        execute('GRANT EXECUTE ON FUNCTION '+signature+' TO fashionstore_app;')
    print('Base temporal y rol no propietario preparados.')
if __name__=='__main__':main()
