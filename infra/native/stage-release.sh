#!/usr/bin/env bash
# Ejecutar como alecv tras extraer el paquete verificado en releases/VERSION.
set -euo pipefail
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ROOT=/home/alecv/Parcial2_FashionStore
VERSION=${1:?Indique la versión a preparar}
[[ $VERSION =~ ^[0-9]{8}T[0-9]{6}Z-[a-f0-9]{8}$ ]] || { echo 'Versión inválida.' >&2; exit 1; }
RELEASE=$ROOT/releases/$VERSION
[[ $(id -un) == alecv && -d $RELEASE && ! -L $RELEASE ]] || { echo 'Preparar como alecv sobre una versión existente.' >&2; exit 1; }
[[ $(realpath "$RELEASE") == "$RELEASE" ]] || { echo 'Ruta de versión inesperada.' >&2; exit 1; }
python3 "$RELEASE/infra/native/verify_release.py" "$RELEASE"
python3 -m venv "$RELEASE/.venv"
# Las ruedas evitan compilar NumPy/OpenCV en el servidor pequeño. Fallar si falta alguna.
"$RELEASE/.venv/bin/python" -m pip install --disable-pip-version-check --only-binary=:all: -r "$RELEASE/Parcial2_backend/requirements.txt" --constraint "$RELEASE/infra/native/requirements-linux-py313.lock"
"$RELEASE/.venv/bin/python" -m pip check
"$RELEASE/.venv/bin/python" -m pip freeze > "$RELEASE/installed-dependencies.txt"
echo 'Dependencias nativas preparadas. Todavía no se activó la versión.'
