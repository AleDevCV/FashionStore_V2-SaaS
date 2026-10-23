#!/usr/bin/env bash
# Validación sin sudo: no instala paquetes, no activa sitios ni inicia P2.
set -euo pipefail
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ROOT=/home/alecv/Parcial2_FashionStore
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
for file in "$SCRIPT_DIR"/*.sh; do bash -n "$file"; done
python3 - "$SCRIPT_DIR" <<'PY'
from pathlib import Path
import ast,sys
files=list(Path(sys.argv[1]).glob('*.py'))
for path in files:ast.parse(path.read_text(encoding='utf-8'),filename=str(path))
print('Python: sintaxis válida en',len(files),'archivos; entorno virtual todavía no comprobado.')
PY
mkdir -p "$ROOT/incoming"
CHECK=$(mktemp -d "$ROOT/incoming/native-check.XXXXXX")
trap 'rm -f -- "$CHECK/nginx.conf" "$CHECK/fashionstore-p2-api.service" "$CHECK/nginx.pid"; rmdir -- "$CHECK"' EXIT
printf 'error_log stderr; pid %s/nginx.pid; events {} http { access_log off; include /etc/nginx/mime.types; include %s/fashionstore-p2.nginx.conf; }\n' "$CHECK" "$SCRIPT_DIR" > "$CHECK/nginx.conf"
nginx -t -p "$CHECK/" -c "$CHECK/nginx.conf" -e stderr
# Comprobar directivas soportadas aunque el ejecutable de una versión aún no exista.
sed 's|^ExecStart=.*|ExecStart=/usr/bin/true|' "$SCRIPT_DIR/fashionstore-p2-api.service" > "$CHECK/fashionstore-p2-api.service"
systemd-analyze verify --man=no "$CHECK/fashionstore-p2-api.service"
echo 'Bash, Python, sitio Nginx y directivas systemd verificados sin activar P2.'
echo 'Pendientes: dependencias Python 3.13, base P2, runtime, consumo real y HTTPS.'
