import ast
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/'Parcial2_backend/app'
p=ROOT/'routers/ia.py';s=p.read_text(encoding='utf-8-sig');tree=ast.parse(s);node=next(n for n in tree.body if isinstance(n,ast.AsyncFunctionDef) and n.name=='proxy_image');lines=s.splitlines(keepends=True);lines[node.body[0].lineno-1:node.end_lineno]=['    import asyncio\n    from app.services.safe_images import fetch_image\n    data,media=await asyncio.to_thread(fetch_image,url)\n    return Response(content=data,media_type=media,headers={\'Cache-Control\':\'private, max-age=300\'})\n'];p.write_text(''.join(lines),encoding='utf-8')
p=ROOT/'services/tryon_service.py';s=p.read_text(encoding='utf-8-sig');start=s.index('            # Protección SSRF');end=s.index('\n        else:',start);s=s[:start]+'''            from app.services.safe_images import fetch_image
            raw_bytes,_=fetch_image(url_o_b64)
'''.replace('\n+','\n')+s[end:]
s=s.replace('    # Eliminar posibles encabezados MIME',"    if len(cadena_b64)>12_000_000:raise HTTPException(413,'La imagen supera el límite admitido.')\n    # Eliminar posibles encabezados MIME",1)
s=s.replace('        return datos_bytes','        from app.services.safe_images import validate_image\n        validate_image(datos_bytes)\n        return datos_bytes',1)
p.write_text(s,encoding='utf-8')
