"""Integridad del artefacto, separación de secretos y literalidad de la configuración."""
from pathlib import Path
import importlib.util
import json
import os
import subprocess
import sys
import tarfile
import time
import pytest
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[2]


def module(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


config = module('native_config', 'scripts/generate_native_config.py')
pack = module('native_package', 'scripts/package_native.py')
verify = module('native_verify', 'infra/native/verify_release.py')


def test_native_secrets_are_distinct_and_webhook_is_not_reused(tmp_path):
    source = tmp_path / 'local.env'
    source.write_text('STRIPE_SECRET_KEY=sk_test_dummy\nSTRIPE_WEBHOOK_SECRET=whsec_previous\nSECRET_KEY=local-secret\nPOSTGRES_PASSWORD=local-password\nGOOGLE_API_KEY=gemini-dummy\n')
    output = config.generate(tmp_path / 'private', source, 'https://fashionstore-v2.example.com')
    api = dotenv_values(output / 'api.env', interpolate=False)
    admin = dotenv_values(output / 'admin.env', interpolate=False)
    assert api['DB_USER'] == 'fashionstore_p2_app'
    assert admin['POSTGRES_USER'] == 'fashionstore_p2_owner'
    assert api['SECRET_KEY'] != 'local-secret'
    assert api['DB_PASSWORD'] not in {'local-password', admin['POSTGRES_PASSWORD']}
    assert api['STRIPE_SECRET_KEY'] == 'sk_test_dummy'
    assert api['STRIPE_WEBHOOK_SECRET'] == ''
    assert api['DB_MAX_CONNECTIONS'] == '3'
    assert api['API_BASE_URL'] == 'https://fashionstore-v2.example.com'
    assert not {'POSTGRES_PASSWORD', 'DEMO_PASSWORD'} & api.keys()
    provision = json.loads((output / 'provision.json').read_text())
    assert provision['app_password'] == api['DB_PASSWORD']
    with pytest.raises(ValueError, match='existe'):
        config.generate(output, source, 'https://example.com')


@pytest.mark.parametrize('url', ['http://example.com', 'https://user:pass@example.com', 'https://example.com/path', 'https://example.com?q=1'])
def test_native_rejects_invalid_public_origin(tmp_path, url):
    with pytest.raises(ValueError):
        config.generate(tmp_path / 'private', tmp_path / 'missing.env', url)
    assert not (tmp_path / 'private').exists()


def test_native_rejects_live_stripe(tmp_path):
    source = tmp_path / 'local.env'
    source.write_text('STRIPE_SECRET_KEY=sk_live_dummy\n')
    with pytest.raises(ValueError, match='prueba'):
        config.generate(tmp_path / 'private', source, 'https://example.com')


def test_private_environment_is_data_not_shell_code(tmp_path):
    private = tmp_path / 'private.env'
    value = 'literal-$(never-execute)-${HOME}-`echo nope`-"-\\'
    config.write_env(private, {'OPAQUE_TEST': value})
    runner = module('native_env', 'infra/native/env_run.py')
    env = runner.environment(private, {'PATH': 'kept', 'PYTHONPATH': 'not-in-child', 'PYTHONHOME': 'not-in-child'})
    assert env['OPAQUE_TEST'] == value
    assert env['PATH'] == 'kept'
    assert 'PYTHONPATH' not in env and 'PYTHONHOME' not in env


def sample_sources(root):
    paths = {'Parcial2_backend/app/main.py': 'app = None',
             'Parcial2_backend/app/static/comprobantes/private.pdf': 'never-package-private',
             'Parcial2_backend/app/.env': 'SECRET_KEY=never-package-private',
             'Parcial2_backend/database/migrations/001_baseline.sql': 'SELECT 1;',
             'Parcial2_backend/ml/artifacts/v1/metadata.json': '{}',
             'Parcial2_backend/requirements.txt': 'fastapi',
             'infra/native/verify_release.py': 'pass',
             'infra/native/api.env': 'never-package-private',
             'scripts/migrate.py': 'pass', 'scripts/seed_demo.py': 'pass', 'scripts/seed_demo_history.py': 'pass', 'scripts/seed_login_accounts.py': 'pass',
             'Parcial2_frontend-web/src/main.ts': 'app',
             'Parcial2_frontend-web/angular.json': '{}', 'Parcial2_frontend-web/package-lock.json': '{}',
             'Parcial2_frontend-web/package.json': '{}', 'Parcial2_frontend-web/ngsw-config.json': '{}',
             'Parcial2_frontend-web/public/icon.svg': '<svg/>',
             'Parcial2_frontend-web/dist/fashionstore-web/browser/index.html': '<html/>',
             'Parcial2_frontend-web/dist/fashionstore-web/browser/ngsw.json': '{}',
             'Parcial2_frontend-web/dist/fashionstore-web/browser/ngsw-worker.js': '// worker'}
    for name, data in paths.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(data, encoding='utf-8')
    index = root / 'Parcial2_frontend-web/dist/fashionstore-web/browser/index.html'
    os.utime(index, (time.time() + 5, time.time() + 5))


def test_native_package_excludes_private_files_and_detects_corruption(tmp_path):
    sample_sources(tmp_path)
    archive = pack.package(tmp_path, tmp_path / 'artifacts')
    extracted = tmp_path / 'extracted'
    with tarfile.open(archive) as package:
        names = package.getnames()
        assert not any('private.pdf' in n or n.endswith('.env') for n in names)
        package.extractall(extracted, filter='data')
    result = verify.verify(extracted)
    assert result['postgresql_target'] == '17'
    assert result['python_target'] == '3.13'
    (extracted / 'Parcial2_backend/app/main.py').write_text('changed')
    with pytest.raises(ValueError, match='manifiesto'):
        verify.verify(extracted)


def test_native_package_rejects_stale_angular(tmp_path):
    sample_sources(tmp_path)
    src = tmp_path / 'Parcial2_frontend-web/src/main.ts'
    os.utime(src, (time.time() + 20, time.time() + 20))
    with pytest.raises(ValueError, match='Angular cambió'):
        pack.collect(tmp_path)


def test_native_manifest_cannot_escape_version(tmp_path):
    (tmp_path / 'release.json').write_text(json.dumps({'deployment': 'native', 'files': {'../secret.env': 'irrelevant'}}))
    with pytest.raises(ValueError, match='Ruta inválida'):
        verify.verify(tmp_path)
