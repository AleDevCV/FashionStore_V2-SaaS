from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'Parcial2_backend/app/routers/auth.py';s=p.read_text(encoding='utf-8')
if 'import hashlib' not in s:s=s.replace('import secrets','import secrets\nimport hashlib',1)
s=s.replace('(id_usuario, token, expiracion),','(id_usuario, hashlib.sha256(token.encode()).hexdigest(), expiracion),')
s=s.replace('token_str = solicitud.token.strip()','token_str = hashlib.sha256(solicitud.token.strip().encode()).hexdigest()')
s=s.replace('WHERE ut.token_recuperacion = %s;','WHERE ut.token_recuperacion = %s FOR UPDATE OF ut;')
s=s.replace('SET password_hash = %s, updated_at = CURRENT_TIMESTAMP','SET password_hash = %s, token_version = token_version + 1, updated_at = CURRENT_TIMESTAMP')
p.write_text(s,encoding='utf-8')
p=ROOT/'Parcial2_backend/app/services/email_service.py';s=p.read_text(encoding='utf-8')
start=s.index('    # Registro seguro en el log')
end=s.index('    try:',start)
s=s[:start]+'''    # Nunca registrar enlaces, tokens ni destinatarios en logs.
    if not SMTP_HOST or SMTP_HOST == "test":
        logger.warning("SMTP no configurado; recuperación no despachada.")
        return False

'''+s[end:]
s=s.replace('            servidor.login(SMTP_USER, SMTP_PASSWORD)','            if SMTP_USER:\n                servidor.login(SMTP_USER, SMTP_PASSWORD)')
s=s.replace('return True\n', 'return True\n',1)
s=s.replace('logger.info("[EMAIL] Correo enviado exitosamente a %s vía SMTP.", destinatario)','logger.info("Correo de recuperación despachado.")')
start=s.index('    except Exception as exc:')
s=s[:start]+'''    except Exception:
        logger.error("Falló la entrega de recuperación por SMTP.")
        return False
'''
s=s.replace('enlace_recuperacion = f"{FRONTEND_URL}/restablecer-password?token={token}"','''from app.tenant import require_context
    from app.database import get_connection
    from urllib.parse import urlencode
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT slug FROM empresa WHERE id_empresa=%s", (require_context().tenant_id,))
        slug = cur.fetchone()[0]
    enlace_recuperacion = FRONTEND_URL + "/restablecer-password?" + urlencode({"token": token, "empresa": slug})''')
p.write_text(s,encoding='utf-8')
p=ROOT/'Parcial2_frontend-web/src/index.html';s=p.read_text(encoding='utf-8')
if 'Tipografías de marca' in s:
 start=s.index('  <!--\n    Tipografías');end=s.index('</head>',start)
 s=s[:start]+'  <meta name="theme-color" content="#204d36">\n'+s[end:];p.write_text(s,encoding='utf-8')
p=ROOT/'Parcial2_frontend-web/src/styles.scss';s=p.read_text(encoding='utf-8')
if '@fontsource' not in s:s="@import '@fontsource/dm-sans/400.css';\n@import '@fontsource/dm-sans/500.css';\n@import '@fontsource/dm-sans/700.css';\n@import '@fontsource/playfair-display/400.css';\n@import '@fontsource/playfair-display/500.css';\n"+s
p.write_text(s,encoding='utf-8')
p=ROOT/'Parcial2_frontend-web/src/app/core/interceptors/auth.interceptor.ts';s=p.read_text(encoding='utf-8');s=s.replace("localStorage.getItem('fashionstore_p2_empresa') || 'demo-a'","new URLSearchParams(location.search).get('empresa') || localStorage.getItem('fashionstore_p2_empresa') || 'demo-a'");p.write_text(s,encoding='utf-8')
print('Recuperación con hash y revocación; SMTP sin tokens en logs; fuentes locales.')
