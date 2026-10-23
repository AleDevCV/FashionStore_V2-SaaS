"""Respaldo P2 privado. Ejecutar con API detenida y admin.env, sin modificar otras bases."""
from datetime import datetime, timezone
from pathlib import Path
import json
import hashlib
import os
import subprocess
import tarfile

ROOT = Path('/home/alecv/Parcial2_FashionStore')


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def main():
    if os.geteuid() != 0 or os.environ.get('PGDATABASE') != 'fashionstore_p2':
        raise SystemExit('Respaldo reservado a root y la base propia fashionstore_p2.')
    state = subprocess.run(['systemctl', 'is-active', '--quiet', 'fashionstore-p2-api'], check=False)
    if state.returncode == 0:
        raise SystemExit('Detenga la API P2 antes de respaldar juntos base y archivos.')
    os.umask(0o077)
    output = ROOT / 'backups' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    output.mkdir(mode=0o700)
    # FORCE RLS también restringe al propietario. El respaldo usa autenticación
    # local del administrador del sistema, solo para esta base fija; la API nunca
    # recibe ese rol ni se debilitan sus políticas.
    dump = output / 'database.dump'
    pg_env = {key:value for key,value in os.environ.items() if not key.startswith('PG')}
    with dump.open('xb') as stream:
        subprocess.run(['runuser','-u','postgres','--','pg_dump',
                        '--host=/var/run/postgresql','--port=5432','--username=postgres',
                        '--dbname=fashionstore_p2','--no-password',
                        '--format=custom','--no-owner','--no-acl'],
                       stdout=stream,env=pg_env,check=True)
    with tarfile.open(output / 'files.tar.gz', 'w:gz', dereference=False) as archive:
        archive.add(ROOT / 'shared/files', arcname='files')
    current = ROOT / 'current'
    info = {'database': 'fashionstore_p2', 'release': current.resolve().name if current.exists() else None,
            'configuration_secrets_included': False, 'sensitive_business_data': True,
            'files':{name:digest(output/name) for name in ('database.dump','files.tar.gz')},
            'restore': 'Restaurar primero a una base nueva; nunca sobre VecinoMarket.'}
    (output / 'backup.json').write_text(json.dumps(info, indent=2), encoding='utf-8')
    print('Respaldo P2 creado en', output)


if __name__ == '__main__':
    main()
