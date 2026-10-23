#!/usr/bin/env bash
# Ensayo nativo privado. No inicia la API, no activa Nginx y no configura el túnel.
set -euo pipefail
ulimit -c 0
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ROOT=/home/alecv/Parcial2_FashionStore
VERSION=${1:?Indique la versión preparada}
[[ $(id -u) == 0 && $VERSION =~ ^[0-9]{8}T[0-9]{6}Z-[a-f0-9]{8}$ ]] || exit 1
RELEASE=$ROOT/releases/$VERSION
[[ $(realpath "$RELEASE") == "$RELEASE" && -x $RELEASE/.venv/bin/python ]] || exit 1
if systemctl is-active --quiet fashionstore-p2-api; then echo 'Detenerse: P2 está activo. Usar la activación normal con respaldo.' >&2; exit 1; fi
exec 9>"$ROOT/.deploy.lock"
flock -n 9 || { echo 'Otra operación de despliegue P2 está en curso.' >&2; exit 1; }
PYTHON=$RELEASE/.venv/bin/python
ENV_RUN=$RELEASE/infra/native/env_run.py
"$PYTHON" "$RELEASE/infra/native/verify_release.py" "$RELEASE"
"$PYTHON" "$ENV_RUN" "$ROOT/shared/admin.env" "$PYTHON" "$RELEASE/infra/native/backup.py"
"$PYTHON" "$ENV_RUN" "$ROOT/shared/admin.env" "$PYTHON" "$RELEASE/scripts/migrate.py"
"$PYTHON" "$ENV_RUN" "$ROOT/shared/api.env" runuser -u fashionstore-p2 -- "$PYTHON" "$RELEASE/infra/native/check_runtime.py"
echo 'Versión nativa comprobada sin iniciar servicios P2 ni publicar el sitio.'
