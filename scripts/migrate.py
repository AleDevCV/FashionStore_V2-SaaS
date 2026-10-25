"""Migraciones versionadas sin DROP; ejecutable con credenciales del propietario."""
from pathlib import Path
import hashlib
import os
import argparse
import re
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

ROOT=Path(__file__).resolve().parents[1]


def grant_application_access(cur, app_user, password):
    """El rol de ejecución es configurable y nunca puede ser propietario ni privilegiado."""
    if not re.fullmatch(r'[a-z][a-z0-9_]{0,62}', app_user):
        raise ValueError('APP_DB_USER debe ser un identificador PostgreSQL simple.')
    cur.execute('SELECT current_user')
    if cur.fetchone()[0] == app_user:
        raise ValueError('Migraciones y aplicación requieren roles diferentes.')
    cur.execute('SELECT rolsuper,rolcreaterole,rolcreatedb,rolreplication,rolbypassrls FROM pg_roles WHERE rolname=%s', (app_user,))
    flags = cur.fetchone()
    if flags is None:
        cur.execute(sql.SQL('CREATE ROLE {} LOGIN PASSWORD {}').format(sql.Identifier(app_user), sql.Literal(password)))
    elif any(flags):
        raise ValueError('El rol de aplicación preexistente tiene privilegios incompatibles con RLS.')
    cur.execute('SELECT EXISTS(SELECT 1 FROM pg_auth_members m JOIN pg_roles r ON r.oid=m.member WHERE r.rolname=%s)', (app_user,))
    if cur.fetchone()[0]:
        raise ValueError('El rol de aplicación no debe pertenecer a otros roles.')
    cur.execute("SELECT EXISTS(SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace JOIN pg_roles r ON r.oid=c.relowner WHERE n.nspname='public' AND r.rolname=%s)", (app_user,))
    if cur.fetchone()[0]:
        raise ValueError('El rol de aplicación no puede ser propietario de objetos comerciales.')
    for statement in (
        'GRANT USAGE ON SCHEMA public TO {}',
        'GRANT SELECT,INSERT,UPDATE,DELETE ON ALL TABLES IN SCHEMA public TO {}',
        'GRANT USAGE,SELECT ON ALL SEQUENCES IN SCHEMA public TO {}',
        'REVOKE ALL ON schema_migrations FROM {}',
        'REVOKE UPDATE,DELETE ON bitacora FROM {}',
        'GRANT EXECUTE ON FUNCTION bind_push_device(TEXT) TO {}',
    ):
        cur.execute(sql.SQL(statement).format(sql.Identifier(app_user)))
    for signature in ('identity_lookup(TEXT,BIGINT)', 'identity_index_user(INTEGER)', 'identity_register(JSONB)',
                      'identity_customer_profile(BIGINT,INTEGER)', 'identity_revoke(BIGINT)',
                      'identity_reset_issue(BIGINT,TEXT)', 'identity_reset_lookup(TEXT)', 'identity_reset_apply(TEXT,TEXT)', 'identity_event(BIGINT,TEXT)'):
        cur.execute(sql.SQL('GRANT EXECUTE ON FUNCTION ' + signature + ' TO {}').format(sql.Identifier(app_user)))

def executable_content(content,adopt_legacy=False):
    # Bloque 3 del P1 puede haber creado estado/created_at; conservar sus valores.
    if adopt_legacy:return re.sub(r'(?im)^(ALTER TABLE\s+\w+\s+ADD COLUMN)(?! IF NOT EXISTS)',r'\1 IF NOT EXISTS',content)
    return content
def main():
    args=argparse.ArgumentParser();args.add_argument('--adopt-legacy',action='store_true');options=args.parse_args()
    load_dotenv(ROOT/'.env')
    name=os.environ.get('POSTGRES_DB','fashionstore_p2')
    if name in {'postgres','fashionstore'}:raise SystemExit('La migración requiere una base P2 explícita o una copia; no la base original.')
    with psycopg2.connect(host=os.getenv('MIGRATION_HOST','127.0.0.1'),port=os.getenv('MIGRATION_PORT','55433'),dbname=name,user=os.environ['POSTGRES_USER'],password=os.environ['POSTGRES_PASSWORD']) as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT pg_advisory_xact_lock(82261022)')
            cur.execute('CREATE TABLE IF NOT EXISTS schema_migrations(version TEXT PRIMARY KEY,checksum TEXT NOT NULL,applied_at TIMESTAMPTZ NOT NULL DEFAULT now())')
            cur.execute("SELECT to_regclass('usuario') IS NOT NULL");legacy=cur.fetchone()[0]
            for path in sorted((ROOT/'Parcial2_backend/database/migrations').glob('*.sql')):
                content=path.read_text(encoding='utf-8');checksum=hashlib.sha256(content.encode()).hexdigest()
                cur.execute('SELECT checksum FROM schema_migrations WHERE version=%s',(path.name,));applied=cur.fetchone()
                if applied:
                    if applied[0]!=checksum:raise SystemExit('Checksum diferente para '+path.name)
                    continue
                if path.name.startswith('001_') and legacy:
                    if not options.adopt_legacy:raise SystemExit('Base preexistente sin historial. Ensayar sobre copia y usar --adopt-legacy explícitamente.')
                else:cur.execute(executable_content(content,options.adopt_legacy))
                cur.execute('INSERT INTO schema_migrations(version,checksum) VALUES(%s,%s)',(path.name,checksum));print('Registrada',path.name)
            grant_application_access(cur, os.getenv('APP_DB_USER', 'fashionstore_app'), os.environ['APP_DB_PASSWORD'])
    print('Migraciones completadas sin eliminar datos.')
if __name__=='__main__':main()
