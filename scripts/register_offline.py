from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'Parcial2_backend/app/main.py';s=p.read_text(encoding='utf-8')
if 'from app.routers.offline' not in s:s=s.replace('from app.routers.saas import router as saas_router','from app.routers.saas import router as saas_router\nfrom app.routers.offline import router as offline_router').replace("app.include_router(saas_router, prefix='/api')","app.include_router(saas_router, prefix='/api')\napp.include_router(offline_router, prefix='/api')")
p.write_text(s,encoding='utf-8')
p=ROOT/'Parcial2_backend/app/services/auth_service.py';s=p.read_text(encoding='utf-8')
if "claims.setdefault('token_use', 'access')" not in s:s=s.replace('claims = datos.copy()',"claims = datos.copy()\n    claims.setdefault('token_use', 'access')",1)
s=s.replace('return jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])',"claims = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])\n        return claims if claims.get('token_use', 'access') == 'access' else None")
p.write_text(s,encoding='utf-8')
print('Contrato offline y transacciones por operación registrados; lease no sirve como sesión API.')
