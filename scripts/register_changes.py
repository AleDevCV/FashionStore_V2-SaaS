from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'Parcial2_backend/app/main.py';s=p.read_text(encoding='utf-8')
if 'from app.routers.cambios' not in s:s=s.replace('from app.routers.saas import router as saas_router','from app.routers.saas import router as saas_router\nfrom app.routers.cambios import router as cambios_router').replace("app.include_router(saas_router, prefix='/api')","app.include_router(saas_router, prefix='/api')\napp.include_router(cambios_router, prefix='/api')")
p.write_text(s,encoding='utf-8')
p=ROOT/'Parcial2_backend/app/services/pago_service.py';s=p.read_text(encoding='utf-8')
needle='    metadata = session.get("metadata", {})'
if 'confirm_difference' not in s:s=s.replace(needle,needle+'''\n    if metadata.get('tipo') == 'cambio':
        from app.services.exchanges import confirm_difference
        return confirm_difference(cursor, session)
''',1)
p.write_text(s,encoding='utf-8')
print('Rutas de cambios y confirmación de diferencias registradas.')
