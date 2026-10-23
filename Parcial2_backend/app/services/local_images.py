"""Imágenes públicas del catálogo separadas físicamente por empresa."""
import io,os,re
from pathlib import Path
from uuid import uuid4
from PIL import Image,ImageOps
from fastapi import HTTPException
from app.tenant import require_context
DIRECTORY=Path(os.getenv('CATALOG_IMAGES_DIR',str(Path(__file__).resolve().parents[1]/'static/catalog-images')))
PATTERN=re.compile(r'^[a-f0-9]{32}\.webp$')
def save(data):
    ctx=require_context();directory=DIRECTORY/str(ctx.tenant_id);directory.mkdir(parents=True,exist_ok=True)
    name=uuid4().hex+'.webp'
    with Image.open(io.BytesIO(data)) as source:
        image=ImageOps.exif_transpose(source).convert('RGBA');image.thumbnail((1600,1600));image.save(directory/name,format='WEBP',quality=85)
    return f'/api/catalogo/imagenes/{ctx.slug}/{name}'
def file(slug,name):
    ctx=require_context()
    if slug!=ctx.slug or not PATTERN.fullmatch(name):raise HTTPException(404,'Imagen de catálogo no encontrada.')
    target=DIRECTORY/str(ctx.tenant_id)/name
    if not target.is_file():raise HTTPException(404,'Imagen de catálogo no encontrada.')
    return target
def from_url(url):
    match=re.fullmatch(r'/api/catalogo/imagenes/([a-z0-9-]+)/([a-f0-9]{32}\.webp)',url)
    if not match:raise HTTPException(400,'Ruta de imagen local no válida.')
    return file(*match.groups()).read_bytes()
