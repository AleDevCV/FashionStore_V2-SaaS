"""Sustituye cuerpos concretos de P1 conservando sus contratos de respuesta."""
from pathlib import Path
import ast
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'Parcial2_backend/app/services/venta_service.py';s=p.read_text(encoding='utf-8')
replacements={
'crear_reserva':'''def crear_reserva(cursor, datos, id_usuario, ip_address):
    from app.services.commerce import reserve
    rid = reserve(cursor, datos.id_cliente, datos.id_sucursal, [x.model_dump() for x in datos.items], id_usuario)
    return obtener_reserva_por_id(cursor, rid)
''',
'crear_reserva_probador':'''def crear_reserva_probador(cursor, datos, id_usuario, ip_address):
    from app.services.commerce import reserve
    rid = reserve(cursor, datos.id_cliente, datos.id_sucursal, [x.model_dump() for x in datos.items], id_usuario)
    return obtener_ticket_reserva_qr(cursor, rid)
''',
'actualizar_estado_reserva_probador':'''def actualizar_estado_reserva_probador(cursor, id_reserva, datos, id_usuario, ip_address):
    from app.services.commerce import transition_reservation
    transition_reservation(cursor, id_reserva, datos.nuevo_estado)
    return obtener_ticket_reserva_qr(cursor, id_reserva)
''',
'confirmar_venta':'''def confirmar_venta(cursor, datos, id_usuario, ip_address, payment_verified=False):
    from app.services.commerce import confirm_reservation
    vid = confirm_reservation(cursor, datos, id_usuario, payment_verified)
    return obtener_venta_por_id(cursor, vid)
''',
}
lines=s.splitlines(keepends=True)
nodes=[n for n in ast.parse(s).body if isinstance(n,ast.FunctionDef) and n.name in replacements]
if len(nodes)!=len(replacements):raise RuntimeError('Los servicios heredados no coinciden con el inventario.')
for node in sorted(nodes,key=lambda n:n.lineno,reverse=True):lines[node.lineno-1:node.end_lineno]=[replacements[node.name]]
p.write_text(''.join(lines),encoding='utf-8')
p=ROOT/'Parcial2_backend/app/services/pos_service.py';s=p.read_text(encoding='utf-8')
if '    prepare_pos(cursor, datos)' not in s:
 s=s.replace('    # 1. Validar o resolver cliente','    from app.services.commerce import prepare_pos\n    prepare_pos(cursor, datos)\n\n    # 1. Validar o resolver cliente',1)
s=s.replace("WHERE ci = '1122334' OR nombre_completo ILIKE '%Mostrador%'", "WHERE ci = 'MOSTRADOR'")
start=s.index('            # Fallback al primer cliente activo') if '            # Fallback al primer cliente activo' in s else -1
if start>=0:
 end=s.index('    else:\n        cursor.execute("SELECT id_cliente',start)
 s=s[:start]+'''            raise HTTPException(409, "Configure el cliente mostrador de la empresa antes de vender.")
'''+s[end:]
needle='    # 8. Generar comprobante fiscal digital PDF'
if 'DELETE FROM retencion WHERE' not in s:s=s.replace(needle,'''    if datos.id_reserva:
        cursor.execute("DELETE FROM retencion WHERE id_reserva=%s", (datos.id_reserva,))
    cursor.execute("UPDATE venta SET fecha_entrega=now() WHERE id_venta=%s", (id_venta,))

'''+needle,1)
if 'SAVEPOINT receipt_optional' not in s:s=s.replace('    try:\n        req_comp =', '    cursor.execute("SAVEPOINT receipt_optional")\n    try:\n        req_comp =',1).replace('    except Exception as exc:\n        pass','    except Exception:\n        cursor.execute("ROLLBACK TO SAVEPOINT receipt_optional")\n    finally:\n        cursor.execute("RELEASE SAVEPOINT receipt_optional")',1)
p.write_text(s,encoding='utf-8')
p=ROOT/'Parcial2_backend/app/services/pago_service.py';s=p.read_text(encoding='utf-8')
s=s.replace('confirmar_venta(cursor, datos_venta, None, ip_address)','confirmar_venta(cursor, datos_venta, None, ip_address, payment_verified=True)').replace('confirmar_venta(cursor, datos_venta, id_usuario, ip_address)','confirmar_venta(cursor, datos_venta, id_usuario, ip_address, payment_verified=True)')
s=s.replace('str(__import__("app.tenant", fromlist=["require_context"]).require_context().tenant_id)','str(require_context().tenant_id)')
if 'from app.tenant import require_context\n' not in s[:2000]:s='from app.tenant import require_context\n'+s
p.write_text(s,encoding='utf-8')
p=ROOT/'Parcial2_backend/app/services/catalogo_service.py';s=p.read_text(encoding='utf-8');s=s.replace('JOIN inventario ', 'JOIN inventario_catalogo ').replace('FROM inventario ', 'FROM inventario_catalogo ');p.write_text(s,encoding='utf-8')
print('Reservas sin movimientos ficticios, cobro central, POS validado y firma de pagos integrados.')
