#!/usr/bin/env bash
# Ensayo no destructivo: solo crea una base nueva con prefijo reservado a restauraciones P2.
set -euo pipefail
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ROOT=/home/alecv/Parcial2_FashionStore
BACKUP=${1:?Indique la carpeta de respaldo P2}
TARGET=${2:?Indique fashionstore_p2_restore_YYYYMMDDHHMMSS}
[[ $(id -u) == 0 ]] || { echo 'Ejecute con sudo.' >&2; exit 1; }
[[ $TARGET =~ ^fashionstore_p2_restore_[0-9]{14}$ ]] || { echo 'Nombre de copia inválido.' >&2; exit 1; }
BACKUP=$(realpath "$BACKUP")
[[ $BACKUP == "$ROOT/backups/"* && -f $BACKUP/database.dump && -f $BACKUP/files.tar.gz && -f $BACKUP/backup.json ]] || exit 1
python3 - "$BACKUP" <<'PY'
from pathlib import Path
import hashlib,json,sys
root=Path(sys.argv[1]);info=json.loads((root/'backup.json').read_text())
if info.get('database')!='fashionstore_p2':raise SystemExit('Manifiesto de otra base.')
for name in ('database.dump','files.tar.gz'):
    with (root/name).open('rb') as stream:actual=hashlib.file_digest(stream,'sha256').hexdigest()
    if actual!=info.get('files',{}).get(name):raise SystemExit('Respaldo incompleto o alterado: '+name)
PY
# createdb falla si ya existe. Nunca se ejecuta DROP, --clean ni una restauración sobre producción.
runuser -u postgres -- createdb --template=template0 --owner=fashionstore_p2_owner "$TARGET"
runuser -u postgres -- psql -X --set=ON_ERROR_STOP=1 --dbname=postgres --command="REVOKE ALL ON DATABASE $TARGET FROM PUBLIC;"
# stdin permite leer el respaldo root:0600 sin dar acceso a postgres a backups/.
runuser -u postgres -- pg_restore --exit-on-error --single-transaction --no-owner --no-acl --role=fashionstore_p2_owner --dbname="$TARGET" < "$BACKUP/database.dump"
tar -tzf "$BACKUP/files.tar.gz" >/dev/null
runuser -u postgres -- psql -X --set=ON_ERROR_STOP=1 --dbname="$TARGET" --command='SELECT count(*) AS migraciones FROM schema_migrations; SELECT count(*) AS ventas FROM venta;'
echo "Copia restaurada en $TARGET. Los archivos se verificaron, pero no reemplazaron shared/files."
