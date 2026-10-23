from pathlib import Path
import ast,re,os
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'Parcial2_backend/app/services/comprobante_service.py';s=p.read_text(encoding='utf-8')
s=s.replace('STATIC_DIR = Path(__file__).parent.parent / "static" / "comprobantes"','STATIC_DIR = Path(os.getenv("COMPROBANTES_DIR", str(Path(__file__).parent.parent / "static" / "comprobantes")))')
s=s.replace('    STATIC_DIR.mkdir(parents=True, exist_ok=True)\n    return STATIC_DIR','    from app.tenant import require_context\n    directory = STATIC_DIR / str(require_context().tenant_id)\n    directory.mkdir(parents=True, exist_ok=True)\n    return directory')
node=next(n for n in ast.parse(s).body if isinstance(n,ast.FunctionDef) and n.name=='_numero_comprobante')
lines=s.splitlines(keepends=True);lines[node.lineno-1:node.end_lineno]=['''def _numero_comprobante(cursor, id_venta):
    return f"FS-{datetime.now().year}-{id_venta:08d}"
'''];s=''.join(lines)
s=s.replace('_numero_comprobante(cursor)','_numero_comprobante(cursor, datos.id_venta)')
s=s.replace('url_pdf = f"{API_BASE_URL}/static/comprobantes/{nombre_archivo}"','url_pdf = f"/api/comprobantes/{numero}/pdf"')
s=s.replace('url = f"{API_BASE_URL}/api/comprobantes/verificar/{numero}"','from app.tenant import require_context\n    url = f"{API_BASE_URL}/api/comprobantes/verificar/{numero}?empresa={require_context().slug}"')
p.write_text(s,encoding='utf-8')
p=ROOT/'Parcial2_backend/app/routers/comprobantes.py';s=p.read_text(encoding='utf-8')
if 'def descargar_pdf_autorizado' not in s:s+='''

@router.get('/{numero}/pdf', response_class=FileResponse)
def descargar_pdf_autorizado(numero: str, cursor=Depends(get_db), usuario=Depends(get_current_user)):
    from fastapi import HTTPException
    from app.tenant import require_context
    import re
    if not re.fullmatch(r'FS-[0-9]{4}-[0-9]+', numero):
        raise HTTPException(404, 'Comprobante no encontrado.')
    cursor.execute('SELECT id_comprobante FROM comprobante WHERE numero_comprobante=%s', (numero,))
    if not cursor.fetchone():
        raise HTTPException(404, 'Comprobante no encontrado.')
    path = svc.STATIC_DIR / str(require_context().tenant_id) / (numero + '.pdf')
    if not path.is_file():
        raise HTTPException(404, 'Archivo no disponible; solicite regeneración autorizada.')
    return FileResponse(path, media_type='application/pdf', filename=numero + '.pdf', headers={'Cache-Control': 'no-store'})
'''
p.write_text(s,encoding='utf-8')
for relative in ['features/checkout/checkout.ts','features/pago/pago-exitoso/pago-exitoso.ts','features/cliente/mis-pedidos/mis-pedidos.ts','features/pos/pos.ts']:
 p=ROOT/'Parcial2_frontend-web/src/app'/relative;s=p.read_text(encoding='utf-8')
 pattern=r"window\.open\((url|c\.url_pdf|urlPdf),\s*['_\"]blank['_\"]\)"
 # El segundo argumento real es '_blank'.
 pattern=r'''window\.open\((url|c\.url_pdf|urlPdf),\s*['"]_blank['"]\)'''
 if re.search(pattern,s):
  s=re.sub(pattern,r'this.descarga.abrir(\1)',s)
  if 'injectDownload' not in s:
   rel=os.path.relpath(ROOT/'Parcial2_frontend-web/src/app/core/services/descarga.service',p.parent).replace('\\','/')
   s="import { inject as injectDownload } from '@angular/core';\nimport { DescargaService } from '"+rel+"';\n"+s
   s=re.sub(r'(export class [^{]+\{)',r'\1\n  private readonly descarga = injectDownload(DescargaService);',s,count=1)
  p.write_text(s,encoding='utf-8')
print('PDF separados por empresa y descarga autenticada; enlaces web adaptados.')
