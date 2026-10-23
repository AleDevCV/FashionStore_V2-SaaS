from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'Parcial2_backend/app/services/pago_service.py';s=p.read_text(encoding='utf-8')
start=s.index('    event = None\n',s.index('def procesar_webhook_stripe'))
end=s.index('    if hasattr(event, "to_dict"):',start)
s=s[:start]+'''    secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    if not secret:
        raise HTTPException(503, "Webhook de pagos no configurado.")
    if not sig_header:
        raise HTTPException(400, "Firma de webhook requerida.")
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, secret, tolerance=300)
    except Exception:
        raise HTTPException(400, "Firma de webhook inválida.")

'''+s[end:]
if '"tenant_id": str(' not in s:
 s=s.replace('metadata={','metadata={\n                "tenant_id": str(__import__("app.tenant", fromlist=["require_context"]).require_context().tenant_id),',1)
# No confirmar pagos de otra empresa ni importes diferentes a la reserva.
needle='    session_id = session.get("id", "")'
if 'El evento no corresponde a esta empresa' not in s:
 s=s.replace(needle,'''    from app.tenant import require_context
    if str(metadata.get("tenant_id")) != str(require_context().tenant_id):
        raise HTTPException(400, "El evento no corresponde a esta empresa.")
'''+needle)
needle='    if not id_reserva:'
if 'Importe de pago no coincide' not in s:
 s=s.replace(needle,'''    cursor.execute("SELECT total, id_cliente FROM reserva WHERE id_reserva=%s", (id_reserva,))
    expected = cursor.fetchone()
    if not expected or expected['id_cliente'] != id_cliente or Decimal(str(expected['total'])) != monto or session.get('payment_status') != 'paid':
        raise HTTPException(400, "Importe de pago no coincide con la reserva o pago no confirmado.")
'''+needle,1)
p.write_text(s,encoding='utf-8')
p=ROOT/'Parcial2_backend/app/routers/pagos.py';s=p.read_text(encoding='utf-8')
start=s.index('def confirmar_qr(');end=s.index('):',start)
part=s[start:end].replace('Depends(get_current_user)', 'Depends(requiere_rol(["Administrador", "Encargado de Sucursal", "Cajero (POS)"]))')
s=s[:start]+part+s[end:]
if 'get_current_user, requiere_rol' not in s:s=s.replace('from app.services.auth_service import get_current_user','from app.services.auth_service import get_current_user, requiere_rol')
p.write_text(s,encoding='utf-8')
print('Webhook con firma obligatoria, ventana temporal, tenant e importe; QR restringido al personal.')
