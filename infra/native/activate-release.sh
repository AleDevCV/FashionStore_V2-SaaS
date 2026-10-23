#!/usr/bin/env bash
# Activación explícita con corte breve de P2. No publica DNS ni altera otros sitios.
set -euo pipefail
ulimit -c 0
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ROOT=/home/alecv/Parcial2_FashionStore
VERSION=${1:?Indique la versión previamente preparada}
[[ $(id -u) == 0 ]] || { echo 'Ejecute con sudo.' >&2; exit 1; }
[[ $VERSION =~ ^[0-9]{8}T[0-9]{6}Z-[a-f0-9]{8}$ ]] || { echo 'Versión inválida.' >&2; exit 1; }
RELEASE=$ROOT/releases/$VERSION
[[ $(realpath "$RELEASE") == "$RELEASE" && -x $RELEASE/.venv/bin/python ]] || { echo 'Versión nativa sin preparar.' >&2; exit 1; }
exec 9>"$ROOT/.deploy.lock"
flock -n 9 || { echo 'Otra activación de P2 está en curso.' >&2; exit 1; }
PYTHON=$RELEASE/.venv/bin/python
ENV_RUN=$RELEASE/infra/native/env_run.py
"$PYTHON" "$RELEASE/infra/native/verify_release.py" "$RELEASE"
[[ -d $RELEASE/web && -f $ROOT/shared/api.env && -f $ROOT/shared/admin.env ]] || exit 1
OLD=$(readlink "$ROOT/current" 2>/dev/null || true)
WAS_ACTIVE=0
systemctl is-active --quiet fashionstore-p2-api && WAS_ACTIVE=1
STOPPED=0
SWITCHED=0
MIGRATED=0
NGINX_CHANGED=0
NGINX_WAS_ENABLED=0
PREVIOUS_NGINX=
if [[ -L /etc/nginx/sites-enabled/fashionstore-p2 ]]; then
    [[ $(readlink -f /etc/nginx/sites-enabled/fashionstore-p2) == /etc/nginx/sites-available/fashionstore-p2 ]] || { echo 'El nombre del sitio P2 apunta a otro archivo.' >&2; exit 1; }
    NGINX_WAS_ENABLED=1
else
    [[ ! -e /etc/nginx/sites-enabled/fashionstore-p2 ]] || { echo 'Sitio P2 preexistente de tipo inesperado.' >&2; exit 1; }
fi
[[ ! -L /etc/nginx/sites-available/fashionstore-p2 ]] || { echo 'El archivo P2 no debe ser enlace a otro sitio.' >&2; exit 1; }
rollback() {
    status=$?
    trap - ERR
    if (( NGINX_CHANGED )); then
        if [[ -n $PREVIOUS_NGINX ]]; then
            install -m 0644 "$PREVIOUS_NGINX" /etc/nginx/sites-available/fashionstore-p2
        else
            rm -f -- /etc/nginx/sites-available/fashionstore-p2
        fi
        if (( ! NGINX_WAS_ENABLED )); then rm -f -- /etc/nginx/sites-enabled/fashionstore-p2; fi
        if nginx -t; then systemctl reload nginx || true; fi
    fi
    if (( SWITCHED )); then
        systemctl stop fashionstore-p2-api || true
        if [[ -n $OLD ]]; then
            ln -s "$OLD" "$ROOT/.current-recovery"
            mv -Tf "$ROOT/.current-recovery" "$ROOT/current"
        else
            rm -f -- "$ROOT/current"
        fi
    fi
    if (( STOPPED && WAS_ACTIVE && ! MIGRATED )); then systemctl start fashionstore-p2-api || true; fi
    echo 'Activación fallida. El respaldo queda en backups/. No se restaura una base automáticamente.' >&2
    if (( MIGRATED )); then echo 'La base ya fue migrada: verificar compatibilidad antes de iniciar la versión anterior.' >&2; fi
    exit "$status"
}
trap rollback ERR
systemctl stop fashionstore-p2-api 2>/dev/null || [[ ! -f /etc/systemd/system/fashionstore-p2-api.service ]]
STOPPED=1
"$PYTHON" "$ENV_RUN" "$ROOT/shared/admin.env" "$PYTHON" "$RELEASE/infra/native/backup.py"
"$PYTHON" "$ENV_RUN" "$ROOT/shared/admin.env" "$PYTHON" "$RELEASE/scripts/migrate.py"
MIGRATED=1
# Se comprueba con las credenciales limitadas, nunca con el propietario.
"$PYTHON" "$ENV_RUN" "$ROOT/shared/api.env" "$PYTHON" "$RELEASE/infra/native/check_runtime.py"
runuser -u fashionstore-p2 -- test -r "$RELEASE/Parcial2_backend/app/main.py"
runuser -u www-data -- test -r "$RELEASE/web/index.html"
install -m 0644 "$RELEASE/infra/native/fashionstore-p2-api.service" /etc/systemd/system/fashionstore-p2-api.service
ln -s "$RELEASE" "$ROOT/.current-next"
mv -Tf "$ROOT/.current-next" "$ROOT/current"
SWITCHED=1
systemctl daemon-reload
systemctl start fashionstore-p2-api
OK=0
for attempt in {1..20}; do
    if curl --fail --silent --max-time 2 http://127.0.0.1:8002/health >/dev/null; then OK=1; break; fi
    sleep 1
done
[[ $OK == 1 ]]
# Validar el archivo P2 en un Nginx temporal antes de escribir en sites-enabled.
NGINX_CHECK=$(mktemp)
printf 'pid /tmp/fashionstore-p2-nginx-check.pid; events {} http { include /etc/nginx/mime.types; include %s; }\n' "$RELEASE/infra/native/fashionstore-p2.nginx.conf" > "$NGINX_CHECK"
nginx -t -c "$NGINX_CHECK"
rm -f -- "$NGINX_CHECK"
if [[ -f /etc/nginx/sites-available/fashionstore-p2 ]]; then
    PREVIOUS_NGINX=$ROOT/backups/nginx-$VERSION.conf
    cp -- /etc/nginx/sites-available/fashionstore-p2 "$PREVIOUS_NGINX"
fi
NGINX_CHANGED=1
install -m 0644 "$RELEASE/infra/native/fashionstore-p2.nginx.conf" /etc/nginx/sites-available/fashionstore-p2
ln -sfn /etc/nginx/sites-available/fashionstore-p2 /etc/nginx/sites-enabled/fashionstore-p2
nginx -t
systemctl reload nginx
# reload devuelve antes de que los nuevos workers abran el listener.
# Una conexión rechazada durante ese intervalo no debe deshacer la activación.
curl --fail --silent --show-error --retry 8 --retry-delay 1 --retry-connrefused \
    --retry-max-time 20 --max-time 5 http://127.0.0.1:2468/health >/dev/null
systemctl enable fashionstore-p2-api
printf '%s\n' "$OLD" > "$ROOT/previous-release"
trap - ERR
echo "Versión nativa $VERSION activa en 127.0.0.1:2468. HTTPS público se verifica por separado."
