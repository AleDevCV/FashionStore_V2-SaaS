"""Adaptadores compatibles con los routers P1, hacia las reglas verificadas del P2."""
import ast
from pathlib import Path
path=Path(__file__).resolve().parents[1]/'Parcial2_backend/app/services/pago_service.py'
source=path.read_text(encoding='utf-8-sig');tree=ast.parse(source);lines=source.splitlines(keepends=True)
functions={'crear_sesion_stripe':('checkout','cursor,datos,id_usuario,ip_address'),'procesar_webhook_stripe':('webhook','cursor,payload,sig_header,ip_address'),'generar_qr_boliviano':('qr','cursor,datos,id_usuario,ip_address'),'confirmar_pago_qr':('confirm_qr','cursor,datos,id_usuario,ip_address')}
for node in sorted((n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in functions),key=lambda n:n.lineno,reverse=True):
    name,args=functions[node.name]
    lines[node.body[0].lineno-1:node.end_lineno]=[f'    from app.services.payments import {name}\n    return {name}({args})\n']
path.write_text(''.join(lines),encoding='utf-8')
