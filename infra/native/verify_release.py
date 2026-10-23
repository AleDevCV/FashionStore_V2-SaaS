"""Comprueba integridad y rutas del paquete antes de ejecutar su código."""
from pathlib import Path, PurePosixPath
import hashlib
import json
import sys


def verify(root):
    root = Path(root).resolve(strict=True)
    manifest = json.loads((root / 'release.json').read_text(encoding='utf-8'))
    if manifest.get('deployment') != 'native' or not isinstance(manifest.get('files'), dict):
        raise ValueError('Manifiesto nativo inválido.')
    for name, expected in manifest['files'].items():
        path = PurePosixPath(name)
        if path.is_absolute() or '..' in path.parts or '\\' in name or not path.parts:
            raise ValueError('Ruta inválida en el manifiesto.')
        file = root.joinpath(*path.parts)
        if file.is_symlink() or not file.resolve().is_relative_to(root):
            raise ValueError('El paquete no admite enlaces fuera de la versión.')
        if hashlib.sha256(file.read_bytes()).hexdigest() != expected:
            raise ValueError('La versión no coincide con su manifiesto: ' + name)
    required = {'web/index.html', 'web/ngsw.json', 'Parcial2_backend/app/main.py',
                'Parcial2_backend/requirements.txt', 'scripts/migrate.py'}
    if not required.issubset(manifest['files']):
        raise ValueError('El paquete está incompleto.')
    return manifest


if __name__ == '__main__':
    manifest = verify(sys.argv[1])
    print('Paquete nativo verificado:', manifest['version'], '-', len(manifest['files']), 'archivos.')
