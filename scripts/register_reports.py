"""Conecta el módulo P2 y conserva la forma de respuesta del cliente P1."""
import ast
from pathlib import Path
root=Path(__file__).resolve().parents[1]/'Parcial2_backend/app'
p=root/'main.py';s=p.read_text(encoding='utf-8');marker="from app.routers import reportes\napp.include_router(reportes.router,prefix='/api')\n"
if marker not in s:s += '\n'+marker
p.write_text(s,encoding='utf-8')
p=root/'routers/ia.py';s=p.read_text(encoding='utf-8-sig');tree=ast.parse(s);node=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='analizar_voz');lines=s.splitlines(keepends=True)
body='''    from app.services.reports import legacy_response
    return legacy_response(cursor,peticion.texto_voz,peticion.generar_pdf)
'''
lines[node.body[0].lineno-1:node.end_lineno]=[body];p.write_text(''.join(lines),encoding='utf-8')
