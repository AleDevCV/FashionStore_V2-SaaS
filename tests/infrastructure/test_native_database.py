"""Ensayo en el PostgreSQL efímero local; nunca conecta al servidor doméstico ni al P1."""
from pathlib import Path
from contextlib import closing
import os
import re
import secrets
import subprocess
import sys
import psycopg2
from psycopg2 import sql

ROOT = Path(__file__).resolve().parents[2]


def test_full_migration_as_restricted_native_owner():
    suffix = secrets.token_hex(5)
    database = 'fashionstore_p2_native_test_' + suffix
    owner = 'p2_native_owner_' + suffix
    app = 'p2_native_app_' + suffix
    restored = 'fashionstore_p2_native_restore_' + suffix
    owner_password = secrets.token_urlsafe(32)
    app_password = secrets.token_urlsafe(32)
    assert re.fullmatch(r'fashionstore_p2_native_test_[a-f0-9]{10}', database)
    conn = psycopg2.connect(host='127.0.0.1', port=55432, dbname='fashionstore_p2_test',
                           user='p2_test_owner', password='p2-test-only-password')
    conn.autocommit = True
    created_db = False
    created_copy = False
    created_roles = []
    try:
        with conn.cursor() as cur:
            cur.execute('SHOW server_version_num')
            assert 170000 <= int(cur.fetchone()[0]) < 180000
            for role, password in ((owner, owner_password), (app, app_password)):
                cur.execute(sql.SQL('CREATE ROLE {} LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS NOINHERIT PASSWORD {}').format(sql.Identifier(role), sql.Literal(password)))
                created_roles.append(role)
            cur.execute(sql.SQL('CREATE DATABASE {} OWNER {}').format(sql.Identifier(database), sql.Identifier(owner)))
            created_db = True
        env = os.environ.copy()
        env.update(POSTGRES_DB=database, POSTGRES_USER=owner, POSTGRES_PASSWORD=owner_password,
                   APP_DB_USER=app, APP_DB_PASSWORD=app_password, MIGRATION_HOST='127.0.0.1',
                   MIGRATION_PORT='55432', PYTHON_DOTENV_DISABLED='1', SECRET_KEY='isolated-native-test-secret-with-more-than-forty-eight-characters',
                   DEMO_PASSWORD='isolated-native-demo-password', DB_HOST='127.0.0.1', DB_PORT='55432',
                   DB_NAME=database, DB_USER=app, DB_PASSWORD=app_password)
        for script in ('migrate.py', 'seed_demo.py'):
            result = subprocess.run([sys.executable, str(ROOT / 'scripts' / script)], env=env,
                                    capture_output=True, text=True, timeout=60)
            assert result.returncode == 0, result.stdout + result.stderr
        with closing(psycopg2.connect(host='127.0.0.1', port=55432, dbname=database, user=owner, password=owner_password)) as native, native.cursor() as cur:
            cur.execute('SELECT count(*) FROM schema_migrations')
            assert cur.fetchone()[0] == len(list((ROOT / 'Parcial2_backend/database/migrations').glob('*.sql')))
            cur.execute("SELECT count(*) FROM empresa WHERE slug IN ('demo-a','demo-b')")
            assert cur.fetchone()[0] == 2
            cur.execute('SELECT count(*) FROM prenda')
            assert cur.fetchone()[0] == 8
        with closing(psycopg2.connect(host='127.0.0.1', port=55432, dbname=database, user=app, password=app_password)) as native, native.cursor() as cur:
            cur.execute('SELECT count(*) FROM prenda')
            assert cur.fetchone()[0] == 0
            cur.execute('SELECT rolsuper,rolcreaterole,rolcreatedb,rolbypassrls FROM pg_roles WHERE rolname=current_user')
            assert cur.fetchone() == (False, False, False, False)
        # FORCE RLS impide un pg_dump íntegro incluso al propietario. El respaldo
        # administrativo debe conservar todas las empresas sin cambiar sus políticas.
        docker = ['docker','compose','-f',str(ROOT/'compose.test.yaml'),'exec','-T','db']
        dump = ['pg_dump','--dbname='+database,'--format=custom','--no-owner','--no-acl']
        limited = subprocess.run(docker+dump+['--username='+owner],capture_output=True,timeout=30)
        assert limited.returncode != 0 and b'reporte_resultado' in limited.stderr
        archive = subprocess.run(docker+dump+['--username=p2_test_owner'],capture_output=True,timeout=30)
        assert archive.returncode == 0,archive.stderr.decode(errors='replace')
        assert archive.stdout.startswith(b'PGDMP')
        with conn.cursor() as cur:
            cur.execute(sql.SQL('CREATE DATABASE {} OWNER {}').format(sql.Identifier(restored),sql.Identifier(owner)))
            created_copy=True
        recovery = subprocess.run(docker+['pg_restore','--username=p2_test_owner','--dbname='+restored,
                                          '--role='+owner,'--exit-on-error','--single-transaction',
                                          '--no-owner','--no-acl'],input=archive.stdout,capture_output=True,timeout=30)
        assert recovery.returncode == 0,recovery.stderr.decode(errors='replace')
        with closing(psycopg2.connect(host='127.0.0.1',port=55432,dbname=restored,user=owner,password=owner_password)) as native,native.cursor() as cur:
            cur.execute('SELECT count(*) FROM prenda');assert cur.fetchone()[0]==8
            cur.execute('SELECT sum(stock) FROM inventario');assert cur.fetchone()[0]==480
            cur.execute("SELECT relforcerowsecurity FROM pg_class WHERE oid='reporte_resultado'::regclass")
            assert cur.fetchone()[0] is True
    finally:
        with conn.cursor() as cur:
            if created_copy:
                cur.execute(sql.SQL('DROP DATABASE {}').format(sql.Identifier(restored)))
            if created_db:
                cur.execute(sql.SQL('DROP DATABASE {}').format(sql.Identifier(database)))
            for role in reversed(created_roles):
                cur.execute(sql.SQL('DROP ROLE {}').format(sql.Identifier(role)))
        conn.close()
