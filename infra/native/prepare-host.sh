#!/usr/bin/env bash
# Preparación nativa; no instala Docker ni cambia el clúster PostgreSQL existente.
set -euo pipefail
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ROOT=/home/alecv/Parcial2_FashionStore
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
[[ $(id -u) == 0 ]] || { echo 'Ejecute con sudo.' >&2; exit 1; }
. /etc/os-release
[[ $ID == debian && $VERSION_ID == 13 ]] || { echo 'Se requiere Debian 13.' >&2; exit 1; }
for command in python3 nginx psql pg_dump pg_restore runuser; do
    command -v "$command" >/dev/null || { echo "Falta una dependencia nativa: $command" >&2; exit 1; }
done
python3 -c 'import venv, ensurepip' || { echo 'Instalar python3-venv antes de continuar.' >&2; exit 1; }
[[ -r $ROOT/shared/provision.json && -r $ROOT/shared/api.env && -r $ROOT/shared/admin.env ]] || {
    echo 'Transfiera primero los tres archivos privados generados a shared/.' >&2; exit 1;
}
if ! id fashionstore-p2 >/dev/null 2>&1; then
    useradd --system --user-group --no-create-home --home-dir /nonexistent --shell /usr/sbin/nologin fashionstore-p2
fi
# No se cambian permisos del directorio personal. Si impiden el acceso, detenerse.
runuser -u fashionstore-p2 -- test -x /home/alecv || {
    echo 'La cuenta P2 necesita permiso de paso sobre /home/alecv. Configurar ACL explícita antes de continuar.' >&2; exit 1;
}
install -d -o alecv -g alecv -m 0755 "$ROOT" "$ROOT/releases" "$ROOT/incoming"
install -d -o root -g fashionstore-p2 -m 0750 "$ROOT/shared"
install -d -o fashionstore-p2 -g fashionstore-p2 -m 0750 "$ROOT/shared/files" "$ROOT/shared/files/comprobantes" "$ROOT/shared/files/catalog-images"
install -d -o root -g root -m 0700 "$ROOT/backups"
chown root:fashionstore-p2 "$ROOT/shared/api.env"
chmod 0640 "$ROOT/shared/api.env"
chown root:root "$ROOT/shared/admin.env" "$ROOT/shared/provision.json"
chmod 0600 "$ROOT/shared/admin.env" "$ROOT/shared/provision.json"
python3 "$SCRIPT_DIR/provision_database.py" "$ROOT/shared/provision.json"
echo 'Entorno nativo preparado. No se inició P2 ni se modificó Nginx o el túnel.'
