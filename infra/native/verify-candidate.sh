#!/usr/bin/env bash
# Comprobación privada; el sitio y la API de producción no se activan.
set -euo pipefail
ulimit -c 0
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
ROOT=/home/alecv/Parcial2_FashionStore
VERSION=${1:?Indique la versión nativa}
[[ $(id -u) == 0 && $VERSION =~ ^[0-9]{8}T[0-9]{6}Z-[a-f0-9]{8}$ ]] || exit 1
RELEASE=$ROOT/releases/$VERSION
[[ $(realpath "$RELEASE") == "$RELEASE" ]] || exit 1
# Usar los verificadores del host permite diagnosticar un candidato rechazado
# sin modificar sus fuentes ni su manifiesto.
PYTHON=$RELEASE/.venv/bin/python
ENV_RUN=$RELEASE/infra/native/env_run.py
if systemctl is-active --quiet fashionstore-p2-api; then echo 'La API P2 debe estar detenida.' >&2; exit 1; fi
"$PYTHON" "$RELEASE/infra/native/verify_release.py" "$RELEASE"
"$PYTHON" "$ENV_RUN" "$ROOT/shared/admin.env" "$PYTHON" "$ROOT/infra/native/backup.py"
"$PYTHON" "$ENV_RUN" "$ROOT/shared/admin.env" "$PYTHON" "$RELEASE/scripts/migrate.py"
"$PYTHON" "$ENV_RUN" "$ROOT/shared/api.env" runuser -u fashionstore-p2 -- "$PYTHON" "$RELEASE/infra/native/check_runtime.py"
"$RELEASE/.venv/bin/python" "$RELEASE/infra/native/env_run.py" "$ROOT/shared/api.env" runuser -u fashionstore-p2 -- "$RELEASE/.venv/bin/python" "$ROOT/infra/native/smoke_models.py" "$RELEASE"
