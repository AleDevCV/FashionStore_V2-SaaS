#!/usr/bin/env bash
# Acceso mínimo al padre del despliegue. No cambia propietarios ni permisos de archivos personales.
set -euo pipefail
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
[[ $(id -u) == 0 && $(realpath /home/alecv) == /home/alecv ]] || exit 1
id fashionstore-p2 >/dev/null
id www-data >/dev/null
if ! command -v setfacl >/dev/null; then
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends acl
fi
setfacl -m u:fashionstore-p2:--x,u:www-data:--x /home/alecv
runuser -u fashionstore-p2 -- test -x /home/alecv
runuser -u www-data -- test -x /home/alecv
echo 'Paso ACL concedido solo a fashionstore-p2 y www-data; no se habilitó lectura del directorio personal.'
