"""
=============================================================================
FASHIONSTORE - SERVICIO DE COMPROBANTES DIGITALES (CU21)
Sistemas de Información II - UAGRM
-----------------------------------------------------------------------------
Generación de comprobantes de venta en formato PDF con:
1. Datos fiscales del comprador (NIT/CI y razón social).
2. Desglose de ítems vendidos con precios y subtotales.
3. Código QR de verificación embebido en el PDF.
4. Número único de comprobante (FS-YYYY-NNNNNN).
5. Envío por correo electrónico al cliente (si está configurado).
6. Descarga pública mediante endpoint de archivos estáticos.
=============================================================================
"""

import io
import os
import smtplib
from datetime import datetime
from decimal import Decimal
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any

import qrcode
from fastapi import HTTPException, status
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    Image as RLImage,
)

from app.schemas.comprobante import ComprobanteGenerarPeticion
from app.services.bitacora_service import ACCION_INSERT, registrar_bitacora

# Directorio donde se guardan los PDFs
STATIC_DIR = Path(os.getenv("COMPROBANTES_DIR", str(Path(__file__).parent.parent / "static" / "comprobantes")))
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


def _asegurar_directorio() -> Path:
    """Crea el directorio de comprobantes si no existe."""
    from app.tenant import require_context
    directory = STATIC_DIR / str(require_context().tenant_id)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _numero_comprobante(cursor, id_venta):
    return f"FS-{datetime.now().year}-{id_venta:08d}"


def _generar_qr_verificacion(numero: str) -> io.BytesIO:
    """Genera imagen QR de verificación del comprobante."""
    from app.tenant import require_context
    url = f"{API_BASE_URL}/api/comprobantes/verificar/{numero}?empresa={require_context().slug}"
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=4, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


def _construir_pdf(
    numero: str,
    nit_ci: str,
    razon_social: str,
    fecha_emision: datetime,
    items: list[dict],
    subtotal: Decimal,
    descuento: Decimal,
    total: Decimal,
    metodo_pago: str,
) -> bytes:
    """Construye el PDF del comprobante en memoria usando ReportLab."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    titulo_style = ParagraphStyle(
        "Titulo",
        parent=styles["Heading1"],
        fontSize=18,
        textColor=colors.HexColor("#1a1a1a"),
        spaceAfter=6,
    )
    subtitulo_style = ParagraphStyle(
        "Subtitulo",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#555555"),
    )
    normal = styles["Normal"]
    bold_style = ParagraphStyle("Bold", parent=normal, fontName="Helvetica-Bold")

    elementos = []

    # ── Encabezado ─────────────────────────────────────────────────────────────
    elementos.append(Paragraph("FashionStore", titulo_style))
    elementos.append(Paragraph("Comprobante de Venta Digital", subtitulo_style))
    elementos.append(Spacer(1, 0.4 * cm))

    # ── Datos del comprobante ──────────────────────────────────────────────────
    datos_comprobante = [
        [Paragraph("<b>N° Comprobante:</b>", normal), Paragraph(numero, normal)],
        [Paragraph("<b>Fecha de emisión:</b>", normal), Paragraph(fecha_emision.strftime("%d/%m/%Y %H:%M"), normal)],
        [Paragraph("<b>NIT / CI:</b>", normal), Paragraph(nit_ci, normal)],
        [Paragraph("<b>Razón social:</b>", normal), Paragraph(razon_social, normal)],
        [Paragraph("<b>Método de pago:</b>", normal), Paragraph(metodo_pago, normal)],
    ]
    tabla_datos = Table(datos_comprobante, colWidths=[5 * cm, 10 * cm])
    tabla_datos.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("LINEBELOW", (0, -1), (-1, -1), 0.5, colors.HexColor("#dddddd")),
    ]))
    elementos.append(tabla_datos)
    elementos.append(Spacer(1, 0.5 * cm))

    # ── Línea separadora ───────────────────────────────────────────────────────
    elementos.append(Table([[""]], colWidths=[17 * cm], rowHeights=[0.5]))
    elementos[-1].setStyle(TableStyle([("LINEABOVE", (0, 0), (-1, -1), 1, colors.HexColor("#cccccc"))]))
    elementos.append(Spacer(1, 0.4 * cm))

    # ── Detalle de ítems ───────────────────────────────────────────────────────
    encabezado = [
        Paragraph("<b>Producto</b>", bold_style),
        Paragraph("<b>SKU</b>", bold_style),
        Paragraph("<b>Talla</b>", bold_style),
        Paragraph("<b>Color</b>", bold_style),
        Paragraph("<b>Cant.</b>", bold_style),
        Paragraph("<b>P. Unit. (Bs)</b>", bold_style),
        Paragraph("<b>Subtotal (Bs)</b>", bold_style),
    ]
    filas = [encabezado]
    for it in items:
        filas.append([
            Paragraph(str(it.get("prenda_nombre", "")), normal),
            Paragraph(str(it.get("sku_variante", "")), normal),
            Paragraph(str(it.get("talla", "")), normal),
            Paragraph(str(it.get("color", "")), normal),
            Paragraph(str(it.get("cantidad", "")), normal),
            Paragraph(f"{Decimal(str(it.get('precio_unitario', 0))):.2f}", normal),
            Paragraph(f"{Decimal(str(it.get('subtotal', 0))):.2f}", normal),
        ])

    tabla_items = Table(filas, colWidths=[4.5*cm, 2.5*cm, 1.5*cm, 2*cm, 1.2*cm, 2.5*cm, 2.8*cm])
    tabla_items.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1a1a")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f9f9f9")]),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#eeeeee")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("ALIGN", (4, 0), (-1, -1), "RIGHT"),
    ]))
    elementos.append(tabla_items)
    elementos.append(Spacer(1, 0.5 * cm))

    # ── Totales ────────────────────────────────────────────────────────────────
    totales = [
        ["Subtotal:", f"Bs {subtotal:.2f}"],
        ["Descuento:", f"Bs {descuento:.2f}"],
        ["TOTAL:", f"Bs {total:.2f}"],
    ]
    tabla_totales = Table(totales, colWidths=[13 * cm, 4 * cm])
    tabla_totales.setStyle(TableStyle([
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, -1), (-1, -1), 11),
        ("LINEABOVE", (0, -1), (-1, -1), 1, colors.HexColor("#1a1a1a")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elementos.append(tabla_totales)
    elementos.append(Spacer(1, 1 * cm))

    # ── QR de verificación ────────────────────────────────────────────────────
    qr_buf = _generar_qr_verificacion(numero)
    qr_img = RLImage(qr_buf, width=3 * cm, height=3 * cm)
    tabla_qr = Table([[qr_img, Paragraph(
        f"<font size='8' color='#555555'>Escanea para verificar<br/>el comprobante #{numero}</font>",
        normal,
    )]], colWidths=[3.5 * cm, 13.5 * cm])
    tabla_qr.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elementos.append(tabla_qr)
    elementos.append(Spacer(1, 0.5 * cm))

    # ── Pie ────────────────────────────────────────────────────────────────────
    elementos.append(Paragraph(
        "<font size='7' color='#888888'>Este documento es un comprobante digital válido. "
        "FashionStore — Sistemas de Información II, UAGRM.</font>",
        normal,
    ))

    doc.build(elementos)
    return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# FUNCIÓN PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────

def generar_comprobante(
    cursor: Any,
    datos: ComprobanteGenerarPeticion,
    id_usuario: int | None,
    ip_address: str,
) -> dict:
    """Genera y almacena el comprobante PDF de una venta.

    Parámetros:
        cursor: cursor activo de PostgreSQL.
        datos: id_venta, nit_ci, razon_social, enviar_email.
        id_usuario: ID del usuario autenticado.
        ip_address: IP para auditoría.

    Retorna:
        dict: comprobante completo con url_pdf.

    Errores:
        HTTP 404: venta inexistente.
        HTTP 409: ya existe un comprobante para esta venta.
    """
    # Verificar que la venta existe
    cursor.execute(
        """
        SELECT v.id_venta, v.id_cliente, v.metodo_pago,
               v.subtotal, v.descuento, v.total, v.fecha_venta,
               c.correo AS cliente_correo, c.nombre_completo AS cliente_nombre
        FROM venta v
        LEFT JOIN cliente c ON v.id_cliente = c.id_cliente
        WHERE v.id_venta = %s;
        """,
        (datos.id_venta,),
    )
    venta = cursor.fetchone()
    if not venta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La venta especificada no existe",
        )

    # Verificar que no haya comprobante previo
    cursor.execute(
        "SELECT id_comprobante FROM comprobante WHERE id_venta = %s;",
        (datos.id_venta,),
    )
    if cursor.fetchone():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un comprobante para esta venta",
        )

    # Obtener ítems de la venta
    cursor.execute(
        """
        SELECT
            dv.id_variante_prenda, vp.sku_variante,
            p.nombre AS prenda_nombre, t.nombre AS talla, col.nombre AS color,
            dv.cantidad, dv.precio_unitario, dv.subtotal
        FROM detalle_venta dv
        JOIN variante_prenda vp ON dv.id_variante_prenda = vp.id_variante_prenda
        JOIN prenda p ON vp.id_prenda = p.id_prenda
        JOIN talla t ON vp.id_talla = t.id_talla
        JOIN color col ON vp.id_color = col.id_color
        WHERE dv.id_venta = %s
        ORDER BY dv.id_variante_prenda;
        """,
        (datos.id_venta,),
    )
    items = cursor.fetchall()

    # Generar número único
    numero = _numero_comprobante(cursor, datos.id_venta)

    # Construir PDF
    pdf_bytes = _construir_pdf(
        numero=numero,
        nit_ci=datos.nit_ci,
        razon_social=datos.razon_social,
        fecha_emision=datetime.now(),
        items=items,
        subtotal=Decimal(str(venta["subtotal"])),
        descuento=Decimal(str(venta["descuento"])),
        total=Decimal(str(venta["total"])),
        metodo_pago=venta["metodo_pago"],
    )

    # Guardar en disco
    directorio = _asegurar_directorio()
    nombre_archivo = f"{numero}.pdf"
    ruta_archivo = directorio / nombre_archivo
    ruta_archivo.write_bytes(pdf_bytes)
    url_pdf = f"/api/comprobantes/{numero}/pdf"

    # Insertar en BD
    cursor.execute(
        """
        INSERT INTO comprobante
            (id_venta, numero_comprobante, nit_ci, razon_social, url_pdf)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id_comprobante, fecha_emision;
        """,
        (datos.id_venta, numero, datos.nit_ci, datos.razon_social, url_pdf),
    )
    comp_row = cursor.fetchone()

    # Auditoría
    registrar_bitacora(
        cursor=cursor,
        accion=ACCION_INSERT,
        tabla_afectada="comprobante",
        registro_id=comp_row["id_comprobante"],
        detalle=f"Comprobante {numero} generado para venta #{datos.id_venta}. Razón: {datos.razon_social}.",
        id_usuario=id_usuario,
        ip_address=ip_address,
    )

    resultado = {
        "id_comprobante": comp_row["id_comprobante"],
        "id_venta": datos.id_venta,
        "numero_comprobante": numero,
        "nit_ci": datos.nit_ci,
        "razon_social": datos.razon_social,
        "fecha_emision": comp_row["fecha_emision"],
        "url_pdf": url_pdf,
    }

    # Enviar email si el cliente tiene correo
    if datos.enviar_email and venta["cliente_correo"]:
        try:
            _enviar_email_comprobante(
                destinatario=venta["cliente_correo"],
                nombre_cliente=venta["cliente_nombre"] or datos.razon_social,
                numero=numero,
                pdf_bytes=pdf_bytes,
            )
        except Exception:
            # El email falla silenciosamente — el comprobante ya está en BD
            pass

    return resultado


def _enviar_email_comprobante(
    destinatario: str,
    nombre_cliente: str,
    numero: str,
    pdf_bytes: bytes,
) -> None:
    """Envía el comprobante PDF al correo del cliente."""
    smtp_host = os.getenv("SMTP_HOST", "localhost")
    smtp_port = int(os.getenv("SMTP_PORT", "1025"))
    smtp_from = os.getenv("SMTP_FROM", "no-reply@fashionstore.com")
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_pass = os.getenv("SMTP_PASSWORD", "")
    use_tls = os.getenv("SMTP_USE_TLS", "false").lower() == "true"

    msg = MIMEMultipart()
    msg["From"] = smtp_from
    msg["To"] = destinatario
    msg["Subject"] = f"Tu comprobante FashionStore — {numero}"

    cuerpo = f"""
    <html><body>
    <p>Hola <b>{nombre_cliente}</b>,</p>
    <p>Gracias por tu compra en <b>FashionStore</b>. Adjuntamos tu comprobante digital.</p>
    <p>Número de comprobante: <b>{numero}</b></p>
    <p>¡Hasta pronto!</p>
    <p><i>El equipo de FashionStore</i></p>
    </body></html>
    """
    msg.attach(MIMEText(cuerpo, "html"))

    adjunto = MIMEApplication(pdf_bytes, _subtype="pdf")
    adjunto.add_header("Content-Disposition", "attachment", filename=f"{numero}.pdf")
    msg.attach(adjunto)

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        if use_tls:
            server.starttls()
        if smtp_user:
            server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_from, destinatario, msg.as_string())


def obtener_comprobante_por_venta(cursor: Any, id_venta: int) -> dict:
    """Recupera el comprobante asociado a una venta."""
    cursor.execute(
        """
        SELECT id_comprobante, id_venta, numero_comprobante,
               nit_ci, razon_social, fecha_emision, url_pdf
        FROM comprobante
        WHERE id_venta = %s;
        """,
        (id_venta,),
    )
    comp = cursor.fetchone()
    if not comp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No existe comprobante para esta venta",
        )
    return dict(comp)


def obtener_comprobante_por_numero(cursor: Any, numero: str) -> dict:
    """Recupera un comprobante por su número único."""
    cursor.execute(
        """
        SELECT id_comprobante, id_venta, numero_comprobante,
               nit_ci, razon_social, fecha_emision, url_pdf
        FROM comprobante
        WHERE numero_comprobante = %s;
        """,
        (numero,),
    )
    comp = cursor.fetchone()
    if not comp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comprobante no encontrado",
        )
    return dict(comp)
