"""Carga y validacion de imagenes de prendas mediante Cloudinary."""

import os
from io import BytesIO

import cloudinary
import cloudinary.uploader
from fastapi import HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError


FORMATOS_PERMITIDOS = {"JPEG", "PNG", "WEBP"}
TIPOS_MIME_PERMITIDOS = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024


def _configurar_cloudinary() -> None:
    variables = {
        "CLOUDINARY_CLOUD_NAME": os.getenv("CLOUDINARY_CLOUD_NAME"),
        "CLOUDINARY_API_KEY": os.getenv("CLOUDINARY_API_KEY"),
        "CLOUDINARY_API_SECRET": os.getenv("CLOUDINARY_API_SECRET"),
    }
    faltantes = [nombre for nombre, valor in variables.items() if not valor]
    if faltantes:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "El almacenamiento de imagenes no esta configurado. "
                f"Faltan: {', '.join(faltantes)}."
            ),
        )

    cloudinary.config(
        cloud_name=variables["CLOUDINARY_CLOUD_NAME"],
        api_key=variables["CLOUDINARY_API_KEY"],
        api_secret=variables["CLOUDINARY_API_SECRET"],
        secure=True,
    )


def _validar_contenido(contenido: bytes, tipo_mime: str | None) -> None:
    if not contenido:
        raise HTTPException(status_code=400, detail="El archivo de imagen esta vacio.")
    if len(contenido) > MAX_IMAGE_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail="La imagen supera el tamano maximo permitido de 5 MB.",
        )
    if tipo_mime not in TIPOS_MIME_PERMITIDOS:
        raise HTTPException(
            status_code=415,
            detail="Formato no permitido. Use una imagen JPG, PNG o WebP.",
        )

    try:
        with Image.open(BytesIO(contenido)) as imagen:
            formato = imagen.format
            imagen.verify()
    except (UnidentifiedImageError, OSError, SyntaxError) as exc:
        raise HTTPException(
            status_code=415,
            detail="El archivo no contiene una imagen valida.",
        ) from exc

    if formato not in FORMATOS_PERMITIDOS:
        raise HTTPException(
            status_code=415,
            detail="El contenido real del archivo no es JPG, PNG ni WebP.",
        )


async def subir_imagen_prenda(archivo: UploadFile) -> str:
    """Valida el archivo y devuelve la URL HTTPS persistente de Cloudinary."""
    contenido = await archivo.read(MAX_IMAGE_SIZE_BYTES + 1)
    await archivo.close()
    _validar_contenido(contenido, archivo.content_type)
    from app.services.safe_images import validate_image
    validate_image(contenido)
    if os.getenv('IMAGE_STORAGE','local')=='local':
        import asyncio
        from app.services.local_images import save
        return await asyncio.to_thread(save,contenido)
    _configurar_cloudinary()

    try:
        resultado = cloudinary.uploader.upload(
            BytesIO(contenido),
            folder=os.getenv("CLOUDINARY_FOLDER", "fashionstore/prendas"),
            resource_type="image",
            unique_filename=True,
            overwrite=False,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Cloudinary no pudo almacenar la imagen. Intente nuevamente.",
        ) from exc

    url_imagen = resultado.get("secure_url")
    if not url_imagen:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Cloudinary no devolvio una URL para la imagen.",
        )
    return url_imagen
