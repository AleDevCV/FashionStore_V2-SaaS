"""
=============================================================================
FASHIONSTORE - SERVICIO DE NOTIFICACIONES Y CORREO ELECTRÓNICO (CU04)
Sistemas de Información II - UAGRM
-----------------------------------------------------------------------------
Gestiona el envío de correos transaccionales para la recuperación de contraseñas.
Integra soporte para envío mediante servidor SMTP real con fallback seguro a
logger en consola para entornos de desarrollo local y suites de prueba.
=============================================================================
"""

import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("fashionstore.email")

SMTP_HOST = os.getenv("SMTP_HOST", "localhost")
SMTP_PORT = int(os.getenv("SMTP_PORT", "1025"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", "no-reply@fashionstore.com")
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "false").lower() in ("true", "1", "yes")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:4200").rstrip("/")


def enviar_correo_recuperacion(
    destinatario: str,
    nombre_usuario: str,
    token: str,
) -> bool:
    """Envía un correo electrónico con el enlace para restablecer la contraseña.

    En entornos locales o cuando no se dispone de un servidor SMTP activo,
    emite un log informativo con el enlace de recuperación para facilitar las
    pruebas sin interrumpir el flujo del usuario ni generar errores 500.

    Parámetros:
        destinatario: dirección de correo electrónico del usuario.
        nombre_usuario: nombre de pila del usuario para personalizar el mensaje.
        token: token criptográfico de un solo uso generado por el backend.

    Retorna:
        bool: True si el correo fue despachado por SMTP o procesado por el fallback.
    """
    from urllib.parse import urlencode
    enlace_recuperacion = FRONTEND_URL + "/restablecer-password?" + urlencode({"token": token})

    # Nunca registrar enlaces, tokens ni destinatarios en logs.
    if not SMTP_HOST or SMTP_HOST == "test":
        logger.warning("SMTP no configurado; recuperación no despachada.")
        return False

    try:
        mensaje = MIMEMultipart("alternative")
        mensaje["Subject"] = "Recuperación de contraseña - FashionStore"
        mensaje["From"] = SMTP_FROM
        mensaje["To"] = destinatario

        texto_plano = (
            f"Hola {nombre_usuario},\n\n"
            f"Hemos recibido una solicitud para restablecer la contraseña de su cuenta en FashionStore.\n\n"
            f"Para definir una nueva contraseña, ingrese al siguiente enlace:\n"
            f"{enlace_recuperacion}\n\n"
            f"Este enlace tiene una vigencia de 30 minutos y solo puede ser utilizado una vez.\n"
            f"Si usted no solicitó este cambio, puede ignorar este mensaje de forma segura.\n\n"
            f"Atentamente,\n"
            f"Equipo FashionStore"
        )

        texto_html = f"""
        <html>
          <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #eaeaea; border-radius: 8px;">
              <h2 style="color: #1a1a1a;">Recuperación de Contraseña</h2>
              <p>Hola <strong>{nombre_usuario}</strong>,</p>
              <p>Recibimos una solicitud para restablecer la contraseña de acceso a su cuenta en <strong>FashionStore</strong>.</p>
              <div style="text-align: center; margin: 30px 0;">
                <a href="{enlace_recuperacion}" 
                   style="background-color: #111; color: #fff; padding: 12px 24px; text-decoration: none; border-radius: 4px; font-weight: bold; display: inline-block;">
                  Restablecer mi Contraseña
                </a>
              </div>
              <p style="font-size: 13px; color: #666;">
                Si el botón anterior no funciona, copie y pegue la siguiente URL en su navegador:<br>
                <a href="{enlace_recuperacion}" style="color: #666;">{enlace_recuperacion}</a>
              </p>
              <p style="font-size: 12px; color: #999; margin-top: 30px; border-top: 1px solid #eaeaea; padding-top: 15px;">
                Este enlace expirará en 30 minutos y quedará invalidado tras su primer uso.<br>
                Si usted no solicitó este restablecimiento, desestime este mensaje.
              </p>
            </div>
          </body>
        </html>
        """

        mensaje.attach(MIMEText(texto_plano, "plain", "utf-8"))
        mensaje.attach(MIMEText(texto_html, "html", "utf-8"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=5) as servidor:
            if SMTP_USE_TLS:
                servidor.starttls()
            if SMTP_USER:
                servidor.login(SMTP_USER, SMTP_PASSWORD)
            servidor.sendmail(SMTP_FROM, [destinatario], mensaje.as_string())

        logger.info("Correo de recuperación despachado.")
        return True

    except Exception:
        logger.error("Falló la entrega de recuperación por SMTP.")
        return False
