"""Conexión a PostgreSQL.

Lee la configuración desde el archivo .env y expone un pool de conexiones
junto con la dependencia `get_db` que usan los routers de FastAPI.
"""

import os
import threading
from contextlib import contextmanager

from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "fashionstore")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

DB_MIN_CONNECTIONS = int(os.getenv("DB_MIN_CONNECTIONS", "1"))
DB_MAX_CONNECTIONS = int(os.getenv("DB_MAX_CONNECTIONS", "10"))
DB_POOL_WAIT_SECONDS = float(os.getenv("DB_POOL_WAIT_SECONDS", "5"))

# El pool se crea en el primer uso, no al importar, para que la API pueda
# arrancar aunque PostgreSQL todavía no esté disponible.
_connection_pool = None
_pool_lock = threading.Lock()
_pool_slots = threading.BoundedSemaphore(DB_MAX_CONNECTIONS)


def get_pool():
    """Devuelve el pool, creándolo la primera vez que se necesita."""
    global _connection_pool
    if _connection_pool is None:
        with _pool_lock:
            if _connection_pool is None:
                _connection_pool = pool.ThreadedConnectionPool(
                    DB_MIN_CONNECTIONS, DB_MAX_CONNECTIONS, host=DB_HOST,
                    port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD,
                )
    return _connection_pool


@contextmanager
def get_connection():
    """Toma una conexión del pool y la devuelve al terminar.

    Hace commit si el bloque termina sin errores y rollback si algo falla.
    """
    current_pool = get_pool()
    # ThreadedConnectionPool falla inmediatamente cuando está lleno. Los
    # finales de dependencias HTTP pueden solaparse con la petición siguiente;
    # esperar brevemente mantiene el límite de conexiones sin rechazar ese pico.
    if not _pool_slots.acquire(timeout=DB_POOL_WAIT_SECONDS):
        raise pool.PoolError('Tiempo de espera de conexión agotado.')
    conn = None
    try:
        conn = current_pool.getconn()
        from app.tenant import context
        tenant = context.get()
        with conn.cursor() as setup:
            setup.execute("SELECT set_config('app.tenant_id', %s, true), set_config('app.user_id', %s, true), set_config('app.role', %s, true), set_config('app.email', %s, true)",
                          (str(tenant.tenant_id) if tenant else '', str(tenant.user_id or '') if tenant else '', tenant.role if tenant else '', tenant.email if tenant else ''))
        yield conn
        conn.commit()
    except Exception:
        if conn is not None:
            conn.rollback()
        raise
    finally:
        try:
            if conn is not None:
                current_pool.putconn(conn)
        finally:
            _pool_slots.release()


def get_db():
    """Dependencia de FastAPI: entrega un cursor que devuelve dicts."""
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                yield cursor
    except pool.PoolError:
        from fastapi import HTTPException
        raise HTTPException(503, 'Servicio de datos temporalmente ocupado. Conserve la operación y reintente.',
                            headers={'Retry-After': '5'})


def close_pool():
    """Cierra todas las conexiones del pool (al apagar la API)."""
    global _connection_pool
    if _connection_pool is not None:
        _connection_pool.closeall()
        _connection_pool = None
