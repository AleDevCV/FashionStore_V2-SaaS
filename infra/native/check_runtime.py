"""Verifica imports, artefactos y aislamiento del rol sin crear datos comerciales."""
from pathlib import Path
import os
import sys


def main():
    import resource
    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root / 'Parcial2_backend'))
    import cv2
    import firebase_admin
    from app.main import app
    from app.services.analytics import artifact
    import psycopg2
    # Se usan exactamente las versiones y hashes que entrenaron los modelos.
    artifact('demand.joblib')
    artifact('segments.joblib')
    with psycopg2.connect(host=os.environ['DB_HOST'], port=os.environ['DB_PORT'],
                          dbname=os.environ['DB_NAME'], user=os.environ['DB_USER'],
                          password=os.environ['DB_PASSWORD']) as conn, conn.cursor() as cur:
        cur.execute('SELECT rolsuper,rolcreaterole,rolcreatedb,rolreplication,rolbypassrls FROM pg_roles WHERE rolname=current_user')
        if any(cur.fetchone()):
            raise ValueError('El rol de ejecución tiene privilegios elevados.')
        cur.execute("SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND c.relowner=(SELECT oid FROM pg_roles WHERE rolname=current_user)")
        if cur.fetchone()[0]:
            raise ValueError('El rol de ejecución es propietario de objetos.')
        cur.execute("SELECT relrowsecurity FROM pg_class WHERE oid='prenda'::regclass")
        if not cur.fetchone()[0]:
            raise ValueError('RLS no está habilitado en el catálogo.')
        cur.execute('SELECT count(*) FROM prenda')
        if cur.fetchone()[0] != 0:
            raise ValueError('RLS debe denegar datos comerciales cuando no hay contexto.')
    print('Runtime nativo: imports, modelos y denegación RLS sin contexto verificados.')
    print('Memoria máxima del proceso de comprobación (KiB):', resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)


if __name__ == '__main__':
    main()
