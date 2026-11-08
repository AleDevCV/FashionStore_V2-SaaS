"""C1/A1: real HTTP authorization and PostgreSQL effects in the test DB only."""
from dataclasses import dataclass
import json

import pytest

from conftest import owner_connection
from app.permissions import provision_permissions
from test_commerce import pos_body
from test_global_identity import register, choose


@dataclass(frozen=True)
class Action:
    name: str
    method: str
    path: str
    kind: str
    success: int


ACTIONS = [
    Action('provider-create-slash', 'POST', '/api/proveedores/', 'provider-create', 201),
    Action('provider-create', 'POST', '/api/proveedores', 'provider-create', 201),
    Action('provider-update', 'PUT', '/api/proveedores/{provider}', 'provider-update', 200),
    Action('provider-delete', 'DELETE', '/api/proveedores/{provider}', 'delete', 200),
    Action('season-create-slash', 'POST', '/api/temporadas/', 'season-create', 201),
    Action('season-create', 'POST', '/api/temporadas', 'season-create', 201),
    Action('season-update', 'PUT', '/api/temporadas/{season}', 'season-update', 200),
    Action('season-delete', 'DELETE', '/api/temporadas/{season}', 'delete', 200),
    Action('purchase-create-slash', 'POST', '/api/compras/', 'purchase', 201),
    Action('purchase-create', 'POST', '/api/compras', 'purchase', 201),
] + [
    Action(f'movement-{kind}-{index}', 'POST', path, kind, 201)
    for index, path in enumerate((
        '/api/movimientos-inventario/', '/api/movimientos-inventario',
        '/api/inventario/movimientos/', '/api/inventario/movimientos',
    ))
    for kind in ('Entrada', 'Salida')
] + [
    Action('pos-sale', 'POST', '/api/pos/ventas', 'pos', 201),
    Action('pos-sale-slash', 'POST', '/api/pos/ventas/', 'pos', 201),
]


@pytest.fixture
def records(companies):
    with owner_connection() as conn, conn.cursor() as cur:
        for company in companies:
            cur.execute("SELECT set_config('app.tenant_id',%s,true)", (str(company['tenant']),))
            cur.execute("INSERT INTO proveedor(nit,razon_social) VALUES('AUTH-BASE','Proveedor prueba') RETURNING id_proveedor")
            company['provider'] = cur.fetchone()['id_proveedor']
            cur.execute("INSERT INTO temporada(nombre,fecha_inicio,fecha_fin) VALUES('Coleccion prueba','2026-01-01','2027-12-31') RETURNING id_temporada")
            company['season'] = cur.fetchone()['id_temporada']
    return companies


@pytest.fixture
def buyer(client, records):
    with owner_connection() as conn, conn.cursor() as cur:
        for company in records:
            cur.execute("SELECT set_config('app.tenant_id',%s,true)", (str(company['tenant']),))
            cur.execute("INSERT INTO rol(nombre) VALUES('Cliente')")
    header, _ = register(client)
    return choose(client, header, records[0])


def staff(company, role, can_sell=True, assigned=True):
    """Use existing roles and the real role-permission tables, not auth overrides."""
    with owner_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT set_config('app.tenant_id',%s,true)", (str(company['tenant']),))
        cur.execute('SELECT id_rol FROM rol WHERE tenant_id=%s AND nombre=%s', (company['tenant'], role))
        found = cur.fetchone()
        if found:
            rid = found['id_rol']
        else:
            cur.execute('INSERT INTO rol(nombre) VALUES(%s) RETURNING id_rol', (role,))
            rid = cur.fetchone()['id_rol']
        provision_permissions(cur, {role: rid})
        cur.execute('UPDATE usuario SET id_role=%s WHERE id_usuario=%s', (rid, company['user']))
        if assigned:
            cur.execute('INSERT INTO usuario_sucursal(id_usuario,id_sucursal) VALUES(%s,%s) ON CONFLICT DO NOTHING', (company['user'], company['branch']))
        if not can_sell:
            cur.execute("DELETE FROM rol_permiso WHERE id_rol=%s AND id_permiso IN (SELECT id_permiso FROM permiso WHERE codigo='pos.vender')", (rid,))


def business_state(companies):
    """Snapshot business rows, excluding credentials and incidental access audits."""
    tables = ('proveedor', 'temporada', 'compra', 'detalle_compra', 'inventario',
              'movimiento_inventario', 'venta', 'detalle_venta')
    result = {}
    with owner_connection() as conn, conn.cursor() as cur:
        for company in companies:
            for table in tables:
                cur.execute(f'SELECT row_to_json(t) AS data FROM {table} t WHERE tenant_id=%s', (company['tenant'],))
                result[company['tenant'], table] = sorted(
                    json.dumps(row['data'], sort_keys=True, default=str) for row in cur.fetchall()
                )
    return result


def body(action, company):
    if action.kind == 'provider-create':
        return {'nit': 'AUTH-NEW', 'razon_social': 'Proveedor nuevo'}
    if action.kind == 'provider-update':
        return {'razon_social': 'Proveedor actualizado'}
    if action.kind == 'season-create':
        return {'nombre': 'Coleccion nueva', 'fecha_inicio': '2026-01-01', 'fecha_fin': '2027-12-31'}
    if action.kind == 'season-update':
        return {'descripcion': 'Descripcion actualizada'}
    if action.kind == 'purchase':
        return {'id_proveedor': company['provider'], 'id_sucursal': company['branch'],
                'items': [{'id_variante_prenda': company['variant'], 'cantidad': 1, 'costo_unitario': '10.00'}]}
    if action.kind in ('Entrada', 'Salida'):
        return {'id_sucursal': company['branch'], 'id_variante_prenda': company['variant'],
                'tipo': action.kind, 'cantidad': 1, 'motivo': 'Prueba autorizacion'}
    if action.kind == 'pos':
        return pos_body(company)
    return None


def request(client, action, company, header, payload=None):
    kwargs = {'headers': header}
    value = body(action, company) if payload is None else payload
    if value is not None:
        kwargs['json'] = value
    return client.request(action.method, action.path.format(**company), **kwargs)


@pytest.mark.parametrize('action', ACTIONS, ids=lambda a: a.name)
def test_customer_cannot_write_administration_or_pos(client, records, buyer, action):
    before = business_state(records)
    response = request(client, action, records[0], buyer)
    assert response.status_code == 403, f'{action.name}: HTTP {response.status_code}'
    assert business_state(records) == before


@pytest.mark.parametrize('action', ACTIONS, ids=lambda a: a.name)
def test_cashier_without_permission_cannot_write_administration_or_pos(client, records, headers, action):
    staff(records[0], 'Cajero (POS)', can_sell=False)
    before = business_state(records)
    response = request(client, action, records[0], headers[0])
    assert response.status_code == 403, f'{action.name}: HTTP {response.status_code}'
    assert business_state(records) == before


@pytest.mark.parametrize('role', ['Administrador', 'Encargado de Sucursal'])
@pytest.mark.parametrize('action', ACTIONS, ids=lambda a: a.name)
def test_existing_authorized_roles_keep_writes(client, records, headers, action, role):
    staff(records[0], role)
    before_other = business_state([records[1]])
    response = request(client, action, records[0], headers[0])
    assert response.status_code == action.success, f'{action.name}: HTTP {response.status_code}'
    assert business_state([records[1]]) == before_other


@pytest.mark.parametrize('action', ACTIONS, ids=lambda a: a.name)
def test_anonymous_write_is_rejected(client, records, action):
    before = business_state(records)
    response = request(client, action, records[0], {'X-Empresa': records[0]['slug']})
    assert response.status_code == 401
    assert business_state(records) == before


FOREIGN_CASES = (
    'provider-update', 'provider-delete', 'season-update', 'season-delete',
    'purchase-provider', 'purchase-branch', 'purchase-variant',
    'movement-branch', 'movement-variant', 'pos-branch', 'pos-variant', 'pos-customer',
)


@pytest.mark.parametrize('role', ['Administrador', 'Encargado de Sucursal'])
@pytest.mark.parametrize('case', FOREIGN_CASES)
def test_authorized_user_cannot_mutate_other_company(client, records, headers, role, case):
    own, other = records
    staff(own, role)
    if case.startswith(('provider-', 'season-')):
        action = next(a for a in ACTIONS if a.name == case)
        target = dict(own)
        key = 'provider' if case.startswith('provider-') else 'season'
        target[key] = other[key]
        payload = body(action, target)
    else:
        kind, key = case.split('-')
        action = next(a for a in ACTIONS if a.name == {'purchase': 'purchase-create', 'movement': 'movement-Entrada-0', 'pos': 'pos-sale'}[kind])
        target = own
        payload = body(action, own)
        if key == 'variant' and kind in ('purchase', 'pos'):
            payload['items'][0]['id_variante_prenda'] = other['variant']
        else:
            payload[{'provider': 'id_proveedor', 'branch': 'id_sucursal', 'variant': 'id_variante_prenda', 'customer': 'id_cliente'}[key]] = other[key]
    before = business_state(records)
    response = request(client, action, target, {**headers[0], 'X-Empresa': other['slug']}, payload)
    assert response.status_code in (404, 422), f'{case}: HTTP {response.status_code}'
    assert business_state(records) == before


@pytest.mark.parametrize('path', ['/api/pos/ventas', '/api/pos/ventas/'])
def test_cashier_with_existing_permission_can_sell(client, records, headers, path):
    staff(records[0], 'Cajero (POS)')
    response = client.post(path, headers=headers[0], json=pos_body(records[0]))
    assert response.status_code == 201


@pytest.mark.parametrize('path', ['/api/pos/ventas', '/api/pos/ventas/'])
def test_pos_revocation_applies_to_existing_session(client, records, headers, path):
    company = records[0]
    staff(company, 'Cajero (POS)')
    assert client.post(path, headers=headers[0], json=pos_body(company)).status_code == 201
    staff(company, 'Cajero (POS)', can_sell=False)
    before = business_state(records)
    response = client.post(path, headers=headers[0], json=pos_body(company))
    assert response.status_code == 403
    assert business_state(records) == before


@pytest.mark.parametrize('path', ['/api/pos/ventas', '/api/pos/ventas/'])
def test_pos_permission_does_not_replace_branch_assignment(client, records, headers, path):
    staff(records[0], 'Cajero (POS)', assigned=False)
    before = business_state(records)
    assert client.post(path, headers=headers[0], json=pos_body(records[0])).status_code == 403
    assert business_state(records) == before


def test_season_lookup_remains_available_for_cashier_inventory(client, records, headers):
    staff(records[0], 'Cajero (POS)', can_sell=False)
    response = client.get('/api/temporadas/', headers=headers[0])
    assert response.status_code == 200
    assert any(row['id_temporada'] == records[0]['season'] for row in response.json())
