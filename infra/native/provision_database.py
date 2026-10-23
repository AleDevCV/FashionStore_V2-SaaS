"""Aprovisiona solamente la base y roles P2 mediante la cuenta local postgres."""
from pathlib import Path
import json
import os
import subprocess
import sys

EXPECTED = {'database': 'fashionstore_p2', 'owner': 'fashionstore_p2_owner', 'app': 'fashionstore_p2_app'}


def literal(value):
    return "'" + str(value).replace("'", "''") + "'"


def query(statement, database='postgres'):
    result = subprocess.run(['runuser', '-u', 'postgres', '--', 'psql', '-X', '-qAt',
                             '--set=ON_ERROR_STOP=1', '--dbname=' + database],
                            input=statement, text=True, capture_output=True)
    if result.returncode:
        # El stderr de PostgreSQL podría contener SQL con contraseñas. No imprimirlo.
        raise RuntimeError('Falló el aprovisionamiento PostgreSQL; no se activó P2. Revisar la base/roles con el administrador.')
    return result.stdout.strip()


def provision(config):
    if os.geteuid() != 0:
        raise ValueError('Ejecutar como root a través de prepare-host.sh.')
    if any(config.get(k) != v for k, v in EXPECTED.items()):
        raise ValueError('Este script solo admite los nombres propios de P2.')
    for key in ('owner_password', 'app_password'):
        if len(config.get(key, '')) < 32 or '\n' in config[key] or '\x00' in config[key]:
            raise ValueError('Credenciales P2 incompletas.')
    db = config['database']
    for kind in ('owner', 'app'):
        role = config[kind]
        flags = query(f"SELECT rolsuper OR rolcreaterole OR rolcreatedb OR rolreplication OR rolbypassrls FROM pg_roles WHERE rolname={literal(role)};")
        if flags == 't':
            raise ValueError('Un rol P2 preexistente tiene privilegios elevados; no se reutiliza.')
        allowed_copies = " AND d.datname !~ '^fashionstore_p2_restore_[0-9]{14}$'" if kind == 'owner' else ''
        foreign = query(f"SELECT count(*) FROM pg_database d JOIN pg_roles r ON r.oid=d.datdba WHERE r.rolname={literal(role)} AND d.datname<>{literal(db)}{allowed_copies};")
        members = query(f"SELECT count(*) FROM pg_auth_members m JOIN pg_roles r ON r.oid=m.member WHERE r.rolname={literal(role)};")
        if foreign != '0' or members != '0':
            raise ValueError('Un rol P2 preexistente participa en otro ámbito; no se modifica.')
        if not flags:
            query(f'CREATE ROLE {role} LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS NOINHERIT CONNECTION LIMIT {2 if kind == "owner" else 5} PASSWORD {literal(config[kind + "_password"])};')
    owner = query(f"SELECT pg_get_userbyid(datdba) FROM pg_database WHERE datname={literal(db)};")
    if owner and owner != config['owner']:
        raise ValueError('La base P2 ya existe con otro propietario; no se adopta.')
    if not owner:
        query(f"CREATE DATABASE {db} OWNER {config['owner']} TEMPLATE template0 ENCODING 'UTF8';")
    query(f"REVOKE ALL ON DATABASE {db} FROM PUBLIC; GRANT CONNECT ON DATABASE {db} TO {config['app']};")
    query(f"ALTER ROLE {config['app']} IN DATABASE {db} SET work_mem='4MB'; ALTER ROLE {config['app']} IN DATABASE {db} SET statement_timeout='15s'; ALTER ROLE {config['app']} IN DATABASE {db} SET idle_in_transaction_session_timeout='30s';")
    # No se altera la configuración global, pg_hba, otras bases ni sus propietarios.
    print('Base y roles P2 preparados; las demás bases no se modificaron.')


if __name__ == '__main__':
    provision(json.loads(Path(sys.argv[1]).read_text(encoding='utf-8')))
