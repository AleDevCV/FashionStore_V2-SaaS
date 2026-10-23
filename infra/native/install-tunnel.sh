#!/usr/bin/env bash
# Instala solamente el conector P2; nunca ejecuta cloudflared service install.
set -euo pipefail
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ROOT=/home/alecv/Parcial2_FashionStore
TOKEN=${1:?Indique el archivo privado transferido con el token P2}
[[ $(id -u) == 0 ]] || { echo 'Ejecute con sudo.' >&2; exit 1; }
[[ -x /usr/local/bin/cloudflared ]] || { echo 'Falta cloudflared en /usr/local/bin.' >&2; exit 1; }
[[ -f $TOKEN && ! -L $TOKEN ]] || { echo 'Token ausente o enlace inesperado.' >&2; exit 1; }
python3 - "$TOKEN" <<'PY'
import base64, json, pathlib, sys
try:
    token = pathlib.Path(sys.argv[1]).read_text().strip()
    data = json.loads(base64.b64decode(token, validate=True))
    assert data['t'] == '9a7b9898-27eb-4ae0-bda4-7977eb3159c9'
    assert all(isinstance(data[key], str) and data[key] for key in ('a', 't', 's'))
except Exception:
    raise SystemExit('El token no corresponde al túnel P2 esperado o tiene formato inválido.')
print('Identidad del túnel FashionStore_Parcial2 comprobada, sin mostrar el token.')
PY
UNIT=$(dirname "$(realpath "$0")")/fashionstore-p2-tunnel.service
[[ -f $UNIT ]] || { echo 'Falta la unidad propia del túnel.' >&2; exit 1; }
if ! systemctl is-active --quiet fashionstore-p2-tunnel; then
    if ss -H -ltn 'sport = :20245' | grep -q .; then
        echo 'Puerto de métricas 20245 ocupado; no se altera otro servicio.' >&2
        exit 1
    fi
fi
install -o root -g root -m 0600 "$TOKEN" "$ROOT/shared/cloudflared-p2.token"
install -o root -g root -m 0644 "$UNIT" /etc/systemd/system/fashionstore-p2-tunnel.service
systemctl daemon-reload
systemctl enable fashionstore-p2-tunnel
systemctl restart fashionstore-p2-tunnel
OK=0
for attempt in {1..30}; do
    if curl --fail --silent --max-time 2 http://127.0.0.1:20245/ready >/dev/null; then OK=1; break; fi
    sleep 1
done
[[ $OK == 1 ]] || { echo 'El conector aún no confirma conexión. Revisar solo su journal.' >&2; exit 1; }
echo 'Túnel P2 conectado. Destino HTTP: http://127.0.0.1:2468. La ruta pública se asigna en Cloudflare.'
