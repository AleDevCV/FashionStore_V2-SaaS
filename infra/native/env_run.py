"""Carga un archivo privado sin interpretarlo como código de shell ni mostrar valores."""
from pathlib import Path
import os
import sys
from dotenv import dotenv_values


def environment(path, parent=None):
    path = Path(path)
    values = dotenv_values(path, interpolate=False)
    if not values:
        raise SystemExit('Configuración privada inexistente o vacía.')
    env = {k: v for k, v in (os.environ if parent is None else parent).items() if k not in {'PYTHONPATH', 'PYTHONHOME'}}
    env.update({k: v for k, v in values.items() if v is not None})
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    env['PYTHON_DOTENV_DISABLED'] = '1'
    # Herramientas nativas de PostgreSQL, siempre sobre la base indicada en admin.env.
    if 'POSTGRES_DB' in values:
        env.update(PGHOST=values['MIGRATION_HOST'], PGPORT=values['MIGRATION_PORT'],
                   PGDATABASE=values['POSTGRES_DB'], PGUSER=values['POSTGRES_USER'],
                   PGPASSWORD=values['POSTGRES_PASSWORD'])
    return env


def main():
    if len(sys.argv) < 3:
        raise SystemExit('Uso: env_run.py archivo.env programa [argumentos]')
    if os.name != 'posix':
        raise SystemExit('env_run.py es un ejecutor del servidor Linux; no se ejecuta en Windows.')
    os.execvpe(sys.argv[2], sys.argv[2:], environment(sys.argv[1]))


if __name__ == '__main__':
    main()
