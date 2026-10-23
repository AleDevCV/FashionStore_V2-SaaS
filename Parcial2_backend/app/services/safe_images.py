"""Descarga limitada de imágenes públicas de proveedores expresamente configurados."""
import io,ipaddress,os,socket
from urllib.parse import urlsplit
import httpx
from PIL import Image
from fastapi import HTTPException
MAX_BYTES=8*1024*1024
MAX_PIXELS=8_000_000

def validate_image(data):
    if len(data)>MAX_BYTES:raise HTTPException(413,'La imagen supera ocho MB.')
    try:
        with Image.open(io.BytesIO(data)) as image:
            if image.width*image.height>MAX_PIXELS or image.width<1 or image.height<1:raise ValueError('dimensiones')
            if image.format not in {'JPEG','PNG','WEBP','GIF'}:raise ValueError('formato')
            media=Image.MIME[image.format];image.verify()
            return media
    except Exception:raise HTTPException(422,'Imagen no válida o resolución superior al límite de ocho megapíxeles.')

def allowed_url(url):
    target=urlsplit(url);hosts={h.strip().lower() for h in os.getenv('IMAGE_ALLOWED_HOSTS','res.cloudinary.com,images.unsplash.com,images.pexels.com').split(',') if h.strip()}
    try:port=target.port
    except ValueError:raise HTTPException(400,'URL de imagen no válida.')
    if target.scheme!='https' or not target.hostname or target.hostname.lower() not in hosts or target.username or target.password or port not in (None,443):raise HTTPException(400,'Use una imagen HTTPS de un proveedor de catálogo autorizado.')
    try:
        addresses=socket.getaddrinfo(target.hostname,443,type=socket.SOCK_STREAM)
        if not addresses or any(not ipaddress.ip_address(row[4][0]).is_global for row in addresses):raise ValueError('red privada')
    except (OSError,ValueError):raise HTTPException(400,'El proveedor de imagen no resuelve a una dirección pública permitida.')
    return url

def fetch_image(url):
    if url.startswith('/api/catalogo/imagenes/'):
        from app.services.local_images import from_url
        raw=from_url(url);return raw,validate_image(raw)
    allowed_url(url);data=bytearray()
    try:
        with httpx.Client(timeout=8,follow_redirects=False,trust_env=False) as client,client.stream('GET',url) as response:
            if response.status_code!=200:raise HTTPException(400,'No se pudo obtener la imagen del proveedor autorizado.')
            for chunk in response.iter_bytes():
                data.extend(chunk)
                if len(data)>MAX_BYTES:raise HTTPException(413,'La imagen supera ocho MB.')
    except HTTPException:raise
    except Exception:raise HTTPException(502,'El proveedor de imágenes no está disponible.')
    raw=bytes(data);return raw,validate_image(raw)
