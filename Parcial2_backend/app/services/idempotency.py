"""Serializa solicitudes con la misma clave dentro de la transacción comercial."""
import hashlib
import json
from decimal import Decimal

from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from psycopg2.extras import Json

from app.tenant import require_context


def replay(cursor, kind, key, payload):
    tenant = require_context().tenant_id
    canonical = jsonable_encoder(payload, custom_encoder={Decimal: lambda value: format(value.normalize(), 'f')})
    digest = hashlib.sha256(json.dumps(canonical, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    namespace = 'transfer' if kind == 'movimiento' else kind
    cursor.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,0))', (f'{namespace}:{tenant}:{key}',))
    if kind == 'movimiento':
        cursor.execute('SELECT 1 FROM traspaso_inventario WHERE operation_id=%s AND tenant_id=%s', (str(key), tenant))
        if cursor.fetchone():
            raise HTTPException(409, 'El UUID pertenece a un traspaso.')
    cursor.execute('''SELECT payload_hash,resultado FROM operacion_idempotente
                      WHERE tenant_id=%s AND tipo=%s AND operation_id=%s''', (tenant, kind, str(key)))
    existing = cursor.fetchone()
    if existing and existing['payload_hash'] != digest:
        raise HTTPException(409, 'La clave de idempotencia ya se utilizó con datos diferentes.')
    return digest, existing['resultado'] if existing else None


def remember(cursor, kind, key, digest, result):
    cursor.execute('''INSERT INTO operacion_idempotente(tipo,operation_id,payload_hash,resultado)
                      VALUES(%s,%s,%s,%s)''',
                   (kind, str(key), digest, Json(jsonable_encoder(result, custom_encoder={Decimal: str}))))
