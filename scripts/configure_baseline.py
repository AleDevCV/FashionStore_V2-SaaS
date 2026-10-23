"""Adaptaciones iniciales pequeñas sobre la copia, con comprobación de anclas."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def edit(path,old,new):
 p=ROOT/path;s=p.read_text(encoding='utf-8-sig')
 if new in s:return
 if old not in s:raise RuntimeError(f'No se encontró ancla en {path}')
 p.write_text(s.replace(old,new,1),encoding='utf-8')

edit('Parcial2_backend/app/services/auth_service.py','claims = datos.copy()', '''claims = datos.copy()
    from app.tenant import require_context
    ctx = require_context()
    claims['tenant_id'] = ctx.tenant_id
    claims.setdefault('token_version', 0)''')
edit('Parcial2_backend/app/services/auth_service.py','return dict(usuario)','''result = dict(usuario)
    from app.tenant import require_context
    result['tenant_id'] = require_context().tenant_id
    return result''')
edit('Parcial2_backend/app/main.py','app.include_router(auth.router, prefix="/api")','''from app.tenant_middleware import tenant_middleware
from app.routers.saas import router as saas_router
app.middleware('http')(tenant_middleware)
app.include_router(saas_router, prefix='/api')
app.include_router(auth.router, prefix="/api")''')
edit('Parcial2_backend/app/main.py','app.include_router(test_db.router)','# Ruta de diagnóstico SQL del prototipo retirada del despliegue SaaS.')
edit('Parcial2_backend/app/main.py','app.mount("/static/comprobantes", StaticFiles(directory=str(_static_dir)), name="comprobantes")','# Los comprobantes se descargan por rutas autenticadas; no se publican como StaticFiles.')
edit('Parcial2_backend/app/main.py','"detalle": str(exc).strip(),','"detalle": "Servicio de datos temporalmente no disponible.",')
edit('Parcial2_backend/app/routers/auth.py','"sub": str(usuario["id_usuario"]),','"sub": str(usuario["id_usuario"]),\n        "token_version": usuario["token_version"],')
edit('Parcial2_backend/app/routers/auth.py','u.password_hash,','u.password_hash,\n                u.token_version,')
print('Adaptaciones tenant y descargas aplicadas sobre la copia P2.')
