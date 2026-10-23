"""Reutiliza únicamente Gemini/Stripe autorizados; nunca imprime sus valores."""
from pathlib import Path
import secrets
from dotenv import dotenv_values,set_key
ROOT=Path(__file__).resolve().parents[1]
target=ROOT/'.env'
if not target.exists():target.touch()
existing=dotenv_values(target)
defaults=dict(POSTGRES_DB='fashionstore_p2',POSTGRES_USER='fashionstore_owner',POSTGRES_PASSWORD=secrets.token_urlsafe(32),APP_DB_PASSWORD=secrets.token_urlsafe(32),SECRET_KEY=secrets.token_urlsafe(64),DEMO_PASSWORD=secrets.token_urlsafe(18),FRONTEND_URL='http://localhost:8082')
for key,value in defaults.items():
    if not existing.get(key):set_key(str(target),key,value)
source=dotenv_values(Path(r'C:\SISTEMAS DE INFORMACION 2\fashionstore-backend\.env'))
for key in ['GEMINI_API_KEY','STRIPE_SECRET_KEY','STRIPE_WEBHOOK_SECRET']:
    value=source.get(key)
    if value:
        if key=='STRIPE_SECRET_KEY' and not value.startswith('sk_test_'):
            print('Stripe: credencial no identificada como sandbox; no se reutilizó.');continue
        set_key(str(target),key,value)
        print(key+': configurada de forma privada.')
    else:print(key+': pendiente de configuración.')
print('Configuración privada guardada; .env está excluido de Git.')
