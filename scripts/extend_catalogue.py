from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'Parcial2_backend/app/schemas/prenda.py';s=p.read_text(encoding='utf-8')
s=s.replace('from datetime import datetime','from datetime import datetime, date')
fields='''    material: str | None = Field(default=None, max_length=300)
    medidas: str | None = Field(default=None, max_length=500)
    precio_mayorista: Decimal | None = Field(default=None, ge=0)
    umbral_mayorista: int | None = Field(default=None, gt=0)
    precio_oferta: Decimal | None = Field(default=None, ge=0)
    oferta_inicio: date | None = None
    oferta_fin: date | None = None
'''
if 'class ComercialFields' not in s:
 s=s.replace('class PrendaCrear(BaseModel):','class ComercialFields(BaseModel):\n'+fields+'\n\nclass PrendaCrear(ComercialFields):')
 s=s.replace('class PrendaActualizar(BaseModel):','class PrendaActualizar(ComercialFields):')
 s=s.replace('class PrendaRespuesta(BaseModel):','class PrendaRespuesta(ComercialFields):')
p.write_text(s,encoding='utf-8')
p=ROOT/'Parcial2_backend/app/services/prenda_service.py';s=p.read_text(encoding='utf-8')
if 'p.material,' not in s:s=s.replace('p.precio_base,','p.precio_base, p.material, p.medidas, p.precio_mayorista, p.umbral_mayorista, p.precio_oferta, p.oferta_inicio, p.oferta_fin,')
needle='    id_prenda = cursor.fetchone()["id_prenda"]'
if 'commercial = {' not in s:
 s=s.replace(needle,needle+'''
    commercial = {k: datos[k] for k in ('material','medidas','precio_mayorista','umbral_mayorista','precio_oferta','oferta_inicio','oferta_fin') if datos.get(k) is not None}
    if commercial:
        from psycopg2 import sql
        query = sql.SQL('UPDATE prenda SET {} WHERE id_prenda=%s').format(sql.SQL(',').join(sql.SQL('{}=%s').format(sql.Identifier(k)) for k in commercial))
        cursor.execute(query, [*commercial.values(), id_prenda])
''',1)
p.write_text(s,encoding='utf-8')
p=ROOT/'Parcial2_backend/app/main.py';s=p.read_text(encoding='utf-8')
if 'administracion_ext' not in s:s=s.replace('from app.routers.saas import router as saas_router','from app.routers.saas import router as saas_router\nfrom app.routers.administracion_ext import router as administracion_router').replace("app.include_router(saas_router, prefix='/api')","app.include_router(saas_router, prefix='/api')\napp.include_router(administracion_router, prefix='/api')")
if '@app.exception_handler(IntegrityError)' not in s:
 s=s.replace('from psycopg2 import OperationalError','from psycopg2 import OperationalError, IntegrityError')
 s += '''

@app.exception_handler(IntegrityError)
async def integrity_error(request: Request, exc: IntegrityError):
    code = 409 if exc.pgcode == '23505' else 422
    return JSONResponse(status_code=code, content={'detail': 'La operación incumple una regla de integridad o un límite del plan.'})
'''
p.write_text(s,encoding='utf-8')
print('Administración y propiedades comerciales ampliadas.')
