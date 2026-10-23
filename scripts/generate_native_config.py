"""Prepara secretos de producción nuevos; reutiliza solo Gemini y Stripe TEST autorizados."""
from pathlib import Path
import argparse
import json
import os
import secrets
from urllib.parse import urlsplit
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]
SERVER = '/home/alecv/Parcial2_FashionStore'


def write_env(path, values):
    content = ''.join(f'{key}={json.dumps(str(value), ensure_ascii=True)}\n' for key, value in values.items())
    # Creación exclusiva: nunca regenerar silenciosamente claves de un despliegue existente.
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(content)
    os.chmod(path, 0o600)


def generate(output, source, base_url):
    parsed = urlsplit(base_url)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in {'', '/'}:
        raise ValueError('La URL pública debe ser un origen HTTPS sin credenciales ni rutas.')
    output = Path(output)
    if output.exists():
        raise ValueError('La carpeta ya existe. Conservar sus secretos o elegir otra carpeta vacía.')
    source = dotenv_values(source, interpolate=False)
    stripe_key = source.get('STRIPE_SECRET_KEY') or ''
    if stripe_key and not stripe_key.startswith('sk_test_'):
        raise ValueError('Solo se autoriza una clave Stripe de prueba.')
    output.mkdir(parents=True, mode=0o700)
    provision = {'database': 'fashionstore_p2', 'owner': 'fashionstore_p2_owner',
                 'app': 'fashionstore_p2_app', 'owner_password': secrets.token_urlsafe(48),
                 'app_password': secrets.token_urlsafe(48)}
    session_key = secrets.token_urlsafe(64)
    admin = {'POSTGRES_DB': provision['database'], 'POSTGRES_USER': provision['owner'],
             'POSTGRES_PASSWORD': provision['owner_password'], 'APP_DB_USER': provision['app'],
             'APP_DB_PASSWORD': provision['app_password'], 'MIGRATION_HOST': '127.0.0.1',
             'MIGRATION_PORT': '5432', 'DEMO_PASSWORD': secrets.token_urlsafe(20), 'SECRET_KEY': session_key}
    api = {'DB_HOST': '127.0.0.1', 'DB_PORT': '5432', 'DB_NAME': provision['database'],
           'DB_USER': provision['app'], 'DB_PASSWORD': provision['app_password'],
           'DB_MIN_CONNECTIONS': '1', 'DB_MAX_CONNECTIONS': '3',
           'SECRET_KEY': session_key, 'ALLOWED_ORIGINS': base_url.rstrip('/'),
           'FRONTEND_URL': base_url.rstrip('/'), 'API_BASE_URL': base_url.rstrip('/'),
           'GOOGLE_API_KEY': source.get('GOOGLE_API_KEY') or source.get('GEMINI_API_KEY') or '',
           'GEMINI_API_KEY': source.get('GEMINI_API_KEY') or source.get('GOOGLE_API_KEY') or '',
           'STRIPE_SECRET_KEY': stripe_key, 'STRIPE_WEBHOOK_SECRET': '',
           'COMPROBANTES_DIR': SERVER + '/shared/files/comprobantes',
           'CATALOG_IMAGES_DIR': SERVER + '/shared/files/catalog-images',
           'IMAGE_STORAGE': 'local', 'FIREBASE_CREDENTIALS_FILE': '',
           'SMTP_HOST': '', 'SMTP_PORT': '587', 'SMTP_USER': '', 'SMTP_PASSWORD': '',
           'SMTP_FROM': 'noreply@example.invalid', 'SMTP_USE_TLS': 'true'}
    write_env(output / 'admin.env', admin)
    write_env(output / 'api.env', api)
    with (output / 'provision.json').open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(provision, stream, indent=2)
    os.chmod(output / 'provision.json', 0o600)
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT / 'infra/secrets/native')
    parser.add_argument('--source', type=Path, default=ROOT / '.env')
    parser.add_argument('--base-url', default='https://fashionstore-v2.aledevcv.me')
    args = parser.parse_args()
    result = generate(args.output, args.source, args.base_url)
    print('Configuración privada preparada en', result)
    print('El webhook Stripe de producción TEST requiere su propio secreto. SMTP y Firebase siguen pendientes.')


if __name__ == '__main__':
    main()
