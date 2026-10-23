import io,socket
import pytest
from PIL import Image
from fastapi import HTTPException
from app.services.safe_images import allowed_url,validate_image

@pytest.mark.parametrize('url',['http://127.0.0.1/','https://localhost/','file:///etc/passwd','https://169.254.169.254/','https://res.cloudinary.com@127.0.0.1/a','https://res.cloudinary.com:8080/a','https://attacker.invalid/a'])
def test_internal_and_unlisted_targets_never_download(url):
    with pytest.raises(HTTPException):allowed_url(url)

def test_trusted_host_cannot_resolve_to_private_address(monkeypatch):
    monkeypatch.setattr(socket,'getaddrinfo',lambda *a,**kw:[(socket.AF_INET,socket.SOCK_STREAM,6,'',('192.168.1.100',443))])
    with pytest.raises(HTTPException):allowed_url('https://res.cloudinary.com/demo/image.png')

def test_images_are_decoded_as_images_and_size_checked():
    stream=io.BytesIO();Image.new('RGB',(32,32)).save(stream,format='PNG');assert validate_image(stream.getvalue())=='image/png'
    with pytest.raises(HTTPException):validate_image(b'<html>Not an image</html>')
