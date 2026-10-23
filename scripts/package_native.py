"""Empaqueta fuentes permitidas, modelos y Angular compilado; excluye secretos y dependencias."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import io
import json
import tarfile

ROOT = Path(__file__).resolve().parents[1]


def collect(root):
    root = Path(root)
    files = {}
    groups = [('Parcial2_backend/app', 'Parcial2_backend/app'),
              ('Parcial2_backend/database/migrations', 'Parcial2_backend/database/migrations'),
              ('Parcial2_backend/ml/artifacts', 'Parcial2_backend/ml/artifacts'),
              ('infra/native', 'infra/native'),
              ('Parcial2_frontend-web/dist/fashionstore-web/browser', 'web')]
    for source, target in groups:
        directory = root / source
        if not directory.is_dir():
            raise ValueError('Falta contenido de la versión: ' + source)
        for path in sorted(directory.rglob('*')):
            if '__pycache__' in path.parts or path.suffix in {'.pyc', '.pyo'}:
                continue
            if source == 'Parcial2_backend/app' and path.relative_to(directory).parts[0] == 'static':
                # Documentos e imágenes de usuarios viajan en respaldos privados, nunca en fuentes.
                continue
            allowed = {'.py'} if source.endswith('/app') else {'.sql'} if source.endswith('/migrations') else {'.joblib', '.json'} if source.endswith('/artifacts') else {'.py', '.sh', '.service', '.conf', '.lock'} if source == 'infra/native' else None
            if path.is_file() and allowed is not None and path.suffix not in allowed:
                continue
            if path.is_file() and (path.name.startswith('.env') or path.suffix in {'.env', '.pem', '.key', '.sqlite', '.dump'}):
                raise ValueError('El paquete no admite configuración privada: ' + str(path))
            if path.is_symlink():
                raise ValueError('El paquete no admite enlaces simbólicos: ' + str(path))
            if path.is_file():
                files[(Path(target) / path.relative_to(directory)).as_posix()] = path.read_bytes()
    for name in ('Parcial2_backend/requirements.txt', 'scripts/migrate.py',
                 'scripts/seed_demo.py', 'scripts/seed_demo_history.py'):
        files[name] = (root / name).read_bytes()
    if not {'web/index.html', 'web/ngsw.json', 'web/ngsw-worker.js'}.issubset(files):
        raise ValueError('Se requiere una compilación Angular de producción con Service Worker.')
    # No distribuir inadvertidamente una compilación anterior a los fuentes.
    build_stamp = (root / 'Parcial2_frontend-web/dist/fashionstore-web/browser/index.html').stat().st_mtime
    source = root / 'Parcial2_frontend-web'
    watched = list((source / 'src').rglob('*')) + list((source / 'public').rglob('*'))
    watched += [source / name for name in ('angular.json', 'package-lock.json', 'ngsw-config.json', 'package.json')]
    if any(p.is_file() and p.stat().st_mtime > build_stamp for p in watched):
        raise ValueError('Angular cambió después de compilar. Ejecute npm run build antes de empaquetar.')
    return files


def package(root, output):
    files = collect(root)
    hashes = {name: hashlib.sha256(data).hexdigest() for name, data in sorted(files.items())}
    source_hash = hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    version = stamp + '-' + source_hash[:8]
    manifest = {'version': version, 'deployment': 'native', 'source_sha256': source_hash,
                'python_target': '3.13', 'postgresql_target': '17', 'files': hashes}
    files['release.json'] = (json.dumps(manifest, ensure_ascii=False, indent=2) + '\n').encode()
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    target = output / (version + '.tar.gz')
    with tarfile.open(target, 'w:gz') as archive:
        for name, data in sorted(files.items()):
            entry = tarfile.TarInfo(name)
            entry.size = len(data)
            entry.mode = 0o755 if name.endswith('.sh') else 0o644
            entry.mtime = 0
            archive.addfile(entry, io.BytesIO(data))
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    (output / (target.name + '.sha256')).write_text(digest + '  ' + target.name + '\n', encoding='utf-8')
    return target


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT / 'tmp/native-releases')
    args = parser.parse_args()
    print('Versión nativa preparada:', package(ROOT, args.output))
