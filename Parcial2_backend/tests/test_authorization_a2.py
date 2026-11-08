"""A2: real FastAPI, tenant middleware and non-owner PostgreSQL, no auth mocks."""
from datetime import datetime, timezone
import hashlib
import json
from uuid import uuid4

import pytest
from psycopg2.extras import Json

from conftest import owner_connection
from app.permissions import provision_permissions
from app.schemas.offline import Operation
from app.services.auth_service import crear_token_acceso
from app.services.synchronization import issue_lease
from app.tenant import TenantContext, context


class Actor(dict):
    def __repr__(self):
        return repr({'user': self.get('user'), 'role': self.get('role'), 'header': '[omitted]'})


class SyncRow(dict):
    def __repr__(self):
        return repr({'id': self['id'], 'result': self['result'], 'raw': '[omitted]'})


class World(dict):
    def __repr__(self):
        return '<A2 isolated companies, actors and operations>'


def header(company, uid, role, email):
    marker = context.set(TenantContext(company['tenant']))
    try:
        token = crear_token_acceso({'id_usuario': uid, 'rol': role, 'correo': email})
    finally:
        context.reset(marker)
    return {'Authorization': 'Bearer '+token}


@pytest.fixture
def world(client, companies, headers):
    c, foreign = companies
    actors = {'admin': Actor(user=c['user'], role='Administrador', header=headers[0])}
    with owner_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT set_config('app.tenant_id',%s,true)", (str(c['tenant']),))
        cur.execute('SELECT id_ciudad FROM sucursal WHERE tenant_id=%s AND id_sucursal=%s', (c['tenant'], c['branch']))
        city = cur.fetchone()['id_ciudad']
        cur.execute("INSERT INTO sucursal(nombre,direccion,id_ciudad) VALUES('Segunda','Prueba A2',%s) RETURNING id_sucursal", (city,))
        second = cur.fetchone()['id_sucursal']
        cur.execute('INSERT INTO inventario(id_sucursal,id_variante_prenda,stock) VALUES(%s,%s,5)', (second, c['variant']))
        roles = {}
        for name in ['Encargado de Sucursal', 'Cajero (POS)', 'Cliente']:
            cur.execute('INSERT INTO rol(nombre) VALUES(%s) RETURNING id_rol', (name,))
            roles[name] = cur.fetchone()['id_rol']
        provision_permissions(cur, roles)
        for key, role, branches in [
            ('single', 'Encargado de Sucursal', [c['branch']]),
            ('both', 'Encargado de Sucursal', [c['branch'], second]),
            ('cashier', 'Cajero (POS)', [c['branch']]),
            ('customer', 'Cliente', []),
        ]:
            email = key+'-'+c['slug']+'@example.com'
            cur.execute("INSERT INTO usuario(nombre,apellido,correo,password_hash,id_role) SELECT %s,'A2',%s,password_hash,%s FROM usuario WHERE tenant_id=%s AND id_usuario=%s RETURNING id_usuario",
                        (key, email, roles[role], c['tenant'], c['user']))
            uid = cur.fetchone()['id_usuario']
            cur.execute('SELECT identity_index_user(%s)', (uid,))
            for bid in branches:
                cur.execute('INSERT INTO usuario_sucursal(id_usuario,id_sucursal) VALUES(%s,%s)', (uid, bid))
            actors[key] = Actor(user=uid, role=role, header=header(c, uid, role, email))
    # Historical rows exercise access independently from business execution.
    # All UUIDs and JSON envelopes are valid; business flows are also tested below.
    rows = {}
    for key in ['admin', 'single', 'cashier', 'customer']:
        actor = actors[key]
        for branch_key, branch in [('first', c['branch']), ('second', second), ('none', None)]:
            for state in (['RECHAZADA'] if branch is None else ['RECHAZADA', 'CONFIRMADA', 'EN_CONFLICTO']):
                oid = str(uuid4())
                marker = context.set(TenantContext(c['tenant'], user_id=actor['user'], role=actor['role']))
                try:
                    with owner_connection() as conn, conn.cursor() as cur:
                        cur.execute("SELECT set_config('app.tenant_id',%s,true)", (str(c['tenant']),))
                        lease, _ = issue_lease(cur, branch or c['branch'])
                finally:
                    context.reset(marker)
                raw = {'operation_id': oid, 'version': 1, 'tenant_id': c['tenant'], 'author_id': actor['user'],
                       'branch_id': branch or c['branch'], 'device_id': str(uuid4()), 'kind': 'reserva',
                       'occurred_at': datetime.now(timezone.utc).isoformat(), 'lease': lease,
                       'customer_id': c['customer'], 'cash_received': None,
                       'items': [{'id_variante_prenda': c['variant'], 'cantidad': 1, 'precio_unitario': '50.00'}],
                       'original_operation': None}
                if branch is None:
                    raw['items'][0]['cantidad'] = -1
                    normalized = raw
                    payload = 'invalid:'+json.dumps(raw, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
                else:
                    normalized = Operation.model_validate(raw).model_dump(mode='json')
                    payload = json.dumps(normalized, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
                result = {'operation_id': oid, 'state': state, 'kind': 'reserva'}
                with owner_connection() as conn, conn.cursor() as cur:
                    cur.execute("SELECT set_config('app.tenant_id',%s,true)", (str(c['tenant']),))
                    cur.execute('INSERT INTO operacion_sync(operation_id,author_id,branch_id,device_id,kind,payload_hash,envelope,state,result) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                                (oid, actor['user'], branch, raw['device_id'], 'reserva', hashlib.sha256(payload.encode()).hexdigest(), Json(normalized), state, Json(result)))
                rows[key, branch_key, state] = SyncRow(id=oid, raw=normalized, result=result)
    foreign_ids = set()
    with owner_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT set_config('app.tenant_id',%s,true)", (str(foreign['tenant']),))
        for state in ['RECHAZADA', 'EN_CONFLICTO', 'CONFIRMADA']:
            oid = str(uuid4())
            cur.execute('INSERT INTO operacion_sync(operation_id,author_id,branch_id,device_id,kind,payload_hash,envelope,state,result) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                        (oid, foreign['user'], foreign['branch'], str(uuid4()), 'reserva', 'a2-fixture', Json({}), state, Json({'operation_id':oid, 'state':state})))
            if state != 'CONFIRMADA': foreign_ids.add(oid)
    return World(company=c, foreign=foreign, foreign_actor=Actor(header=headers[1]), foreign_ids=foreign_ids,
                 actors=actors, rows=rows, branches={'first': c['branch'], 'second': second})


def get(client, actor, row):
    return client.get('/api/sincronizacion/operaciones/'+row['id'], headers=actor['header'])


def replay(client, actor, row):
    return client.post('/api/sincronizacion/lote', headers=actor['header'], json={'operations': [row['raw']]})


def compensate(client, actor, row, amount='0.00'):
    return client.post('/api/conflictos/'+row['id']+'/compensar', headers=actor['header'],
                       json={'motivo': 'Resolucion controlada A2', 'compensacion': amount})


def stored(world):
    with owner_connection() as conn, conn.cursor() as cur:
        cur.execute('SELECT row_to_json(o) AS row FROM operacion_sync o WHERE tenant_id=ANY(%s) ORDER BY tenant_id,operation_id',
                    ([world['company']['tenant'], world['foreign']['tenant']],))
        return [r['row'] for r in cur.fetchall()]


def listed(client, actor):
    response = client.get('/api/conflictos', headers=actor['header'])
    assert response.status_code == 200, response.text
    return {r['operation_id'] for r in response.json()}


def test_list_filters_other_authors_by_assigned_branch_before_limit(client, world):
    w = world; a = w['actors']; rows = w['rows']
    actual = listed(client, a['single'])
    assert rows['admin', 'first', 'EN_CONFLICTO']['id'] in actual
    assert rows['admin', 'second', 'EN_CONFLICTO']['id'] not in actual
    assert rows['admin', 'none', 'RECHAZADA']['id'] not in actual
    assert rows['single', 'none', 'RECHAZADA']['id'] in actual
    assert rows['single', 'second', 'RECHAZADA']['id'] in actual
    assert rows['admin', 'first', 'CONFIRMADA']['id'] not in actual


def test_unauthorized_recent_rows_do_not_hide_authorized_conflicts(client, world):
    c = world['company']
    with owner_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT set_config('app.tenant_id',%s,true)", (str(c['tenant']),))
        for _ in range(105):
            oid = str(uuid4())
            cur.execute("INSERT INTO operacion_sync(operation_id,author_id,branch_id,device_id,kind,payload_hash,envelope,state,result,created_at) VALUES(%s,%s,%s,%s,'reserva','a2-pagination','{}','EN_CONFLICTO',%s,now()+interval '1 minute')",
                        (oid, c['user'], world['branches']['second'], str(uuid4()), Json({'operation_id':oid, 'state':'EN_CONFLICTO'})))
    actual = listed(client, world['actors']['single'])
    assert world['rows']['admin', 'first', 'EN_CONFLICTO']['id'] in actual
    assert len(actual) < 100


@pytest.mark.parametrize('state', ['RECHAZADA', 'CONFIRMADA', 'EN_CONFLICTO'])
def test_direct_uuid_denies_other_branch_without_changing_rows(client, world, state):
    before = stored(world)
    response = get(client, world['actors']['single'], world['rows']['admin', 'second', state])
    assert response.status_code == 404, response.text
    assert stored(world) == before


@pytest.mark.parametrize('branch', ['second', 'none'])
def test_batch_replay_cannot_bypass_uuid_access(client, world, branch):
    before = stored(world)
    response = replay(client, world['actors']['single'], world['rows']['admin', branch, 'RECHAZADA'])
    assert response.status_code == 404, response.text
    assert stored(world) == before


def test_own_results_and_retries_survive_branch_or_permission_revocation(client, world):
    a = world['actors']['cashier']
    before = stored(world)
    for branch, state in [('first', 'CONFIRMADA'), ('second', 'EN_CONFLICTO'), ('second', 'RECHAZADA'), ('none', 'RECHAZADA')]:
        row = world['rows']['cashier', branch, state]
        assert get(client, a, row).json() == row['result']
        assert replay(client, a, row).json() == {'results': [row['result']]}
    assert stored(world) == before


def test_supervision_requires_permission_and_branch_but_handles_both_assignments(client, world):
    rows, a = world['rows'], world['actors']
    for branch in ['first', 'second']:
        for state in ['CONFIRMADA', 'EN_CONFLICTO', 'RECHAZADA']:
            row = rows['admin', branch, state]
            assert get(client, a['both'], row).status_code == 200
            assert replay(client, a['both'], row).json() == {'results': [row['result']]}
            assert get(client, a['cashier'], row).status_code == 404
    response = client.get('/api/conflictos', headers=a['cashier']['header'])
    assert response.status_code == 403
    ids = listed(client, a['both'])
    assert rows['admin', 'first', 'EN_CONFLICTO']['id'] in ids
    assert rows['admin', 'second', 'EN_CONFLICTO']['id'] in ids
    assert rows['admin', 'none', 'RECHAZADA']['id'] not in ids


def test_cross_company_uuid_and_list_never_expose_operations(client, world):
    actor = world['foreign_actor']
    before = stored(world)
    for row in world['rows'].values():
        assert get(client, actor, row).status_code == 404
    row = world['rows']['admin', 'first', 'EN_CONFLICTO']
    assert compensate(client, actor, row).status_code == 404
    assert listed(client, actor) == world['foreign_ids']
    assert stored(world) == before


@pytest.mark.parametrize('state', ['RECHAZADA', 'CONFIRMADA', 'EN_CONFLICTO'])
def test_compensation_checks_access_before_state_or_cash_details(client, world, state):
    before = stored(world)
    response = compensate(client, world['actors']['single'], world['rows']['admin', 'second', state])
    assert response.status_code == 404, response.text
    assert stored(world) == before


def test_author_with_permission_and_admin_can_handle_unassigned_rejections_only(client, world):
    rows, a = world['rows'], world['actors']
    own = rows['single', 'none', 'RECHAZADA']
    other = rows['admin', 'none', 'RECHAZADA']
    before = stored(world)
    assert get(client, a['both'], own).status_code == 404
    assert compensate(client, a['both'], own).status_code == 404
    assert compensate(client, a['cashier'], rows['cashier', 'none', 'RECHAZADA']).status_code == 403
    assert stored(world) == before
    assert get(client, a['single'], own).status_code == 200
    assert compensate(client, a['single'], own).status_code == 200
    assert compensate(client, a['admin'], other).status_code == 200
    assert get(client, a['single'], own).json()['resolved'] is True
    assert len(stored(world)) == len(before)


def test_compensation_cannot_close_another_authors_unassigned_rejection(client, world):
    before = stored(world)
    response = compensate(client, world['actors']['both'], world['rows']['single', 'none', 'RECHAZADA'])
    assert response.status_code == 404, response.text
    assert stored(world) == before


def test_forged_branch_in_replay_cannot_override_stored_branch(client, world):
    original = world['rows']['admin', 'second', 'RECHAZADA']
    forged = SyncRow(**original)
    forged['raw'] = {**original['raw'], 'branch_id': world['branches']['first']}
    before = stored(world)
    response = replay(client, world['actors']['single'], forged)
    assert response.status_code == 404, response.text
    assert stored(world) == before


@pytest.mark.parametrize('state', ['CONFIRMADA', 'EN_CONFLICTO'])
def test_revision_cannot_disclose_an_original_in_another_branch(client, world, state):
    w = world
    original = w['rows']['admin', 'second', state]
    own = w['rows']['single', 'first', 'RECHAZADA']
    new = SyncRow(**own)
    new['raw'] = {**own['raw'], 'operation_id': str(uuid4()), 'original_operation': original['id']}
    before = stored(w)
    response = replay(client, w['actors']['single'], new)
    assert response.status_code == 200, response.text
    result = response.json()['results'][0]
    assert result['state'] == 'RECHAZADA'
    assert result['reason'] == 'Operación no encontrada.'
    after = stored(w)
    assert len(after) == len(before)+1
    assert all(old in after for old in before)


def test_compensation_authorized_branch_and_existing_commercial_rules(client, world):
    a, rows = world['actors'], world['rows']
    row = rows['admin', 'first', 'EN_CONFLICTO']
    assert compensate(client, a['single'], row, '1.00').status_code == 422
    assert compensate(client, a['single'], row).status_code == 200
    assert compensate(client, a['single'], row).status_code == 409
    assert compensate(client, a['single'], rows['admin', 'first', 'CONFIRMADA']).status_code == 409
    assert compensate(client, a['both'], rows['admin', 'second', 'EN_CONFLICTO']).status_code == 200


def test_inactive_branch_history_remains_readable_but_cannot_be_compensated(client, world):
    w = world; row = w['rows']['admin', 'first', 'EN_CONFLICTO']
    with owner_connection() as conn, conn.cursor() as cur:
        cur.execute('UPDATE sucursal SET activa=false WHERE tenant_id=%s AND id_sucursal=%s', (w['company']['tenant'], w['branches']['first']))
    before = stored(w)
    assert get(client, w['actors']['single'], row).status_code == 200
    assert row['id'] in listed(client, w['actors']['single'])
    assert compensate(client, w['actors']['single'], row).status_code == 404
    assert get(client, w['actors']['admin'], row).status_code == 200
    assert stored(w) == before


def test_current_db_assignments_and_permissions_apply_without_new_session(client, world):
    a, c = world['actors']['single'], world['company']
    row = world['rows']['admin', 'first', 'EN_CONFLICTO']
    assert get(client, a, row).status_code == 200
    with owner_connection() as conn, conn.cursor() as cur:
        cur.execute('DELETE FROM usuario_sucursal WHERE tenant_id=%s AND id_usuario=%s', (c['tenant'], a['user']))
    assert get(client, a, row).status_code == 404
    assert row['id'] not in listed(client, a)
    own = world['rows']['single', 'first', 'EN_CONFLICTO']
    assert get(client, a, own).status_code == 200
    assert compensate(client, a, own).status_code == 403
    with owner_connection() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM rol_permiso WHERE tenant_id=%s AND id_rol IN (SELECT id_role FROM usuario WHERE tenant_id=%s AND id_usuario=%s) AND id_permiso IN (SELECT id_permiso FROM permiso WHERE codigo='conflictos.resolver')", (c['tenant'], c['tenant'], a['user']))
    assert client.get('/api/conflictos', headers=a['header']).status_code == 403
    assert get(client, a, own).status_code == 200


def test_customer_can_recover_own_but_neither_list_nor_compensate(client, world):
    a = world['actors']['customer']
    own = world['rows']['customer', 'none', 'RECHAZADA']
    assert get(client, a, own).status_code == 200
    assert replay(client, a, own).json() == {'results': [own['result']]}
    assert get(client, a, world['rows']['admin', 'first', 'EN_CONFLICTO']).status_code == 404
    assert client.get('/api/conflictos', headers=a['header']).status_code == 403
    assert compensate(client, a, own).status_code == 403


def test_unknown_or_invalid_uuid_does_not_change_history(client, world):
    a = world['actors']['single']; before = stored(world)
    assert client.get('/api/sincronizacion/operaciones/'+str(uuid4()), headers=a['header']).status_code == 404
    assert client.get('/api/sincronizacion/operaciones/not-a-uuid', headers=a['header']).status_code == 422
    assert client.post('/api/conflictos/'+str(uuid4())+'/compensar', headers=a['header'], json={'motivo':'Prueba segura', 'compensacion':'0'}).status_code == 404
    assert stored(world) == before


def test_unsent_pending_and_rejected_operations_are_not_deleted_by_reads(client, world):
    # PENDIENTE exists on devices, not in the central SQL state constraint.
    # Keep the unsent envelope intact; only send after access probes complete.
    w = world; pending = dict(w['rows']['admin', 'first', 'CONFIRMADA']['raw'])
    pending['operation_id'] = str(uuid4())
    saved = json.dumps(pending, sort_keys=True)
    before = stored(w)
    assert client.get('/api/sincronizacion/operaciones/'+pending['operation_id'], headers=w['actors']['admin']['header']).status_code == 404
    listed(client, w['actors']['single'])
    assert stored(w) == before and json.dumps(pending, sort_keys=True) == saved
    response = client.post('/api/sincronizacion/lote', headers=w['actors']['admin']['header'], json={'operations':[pending]})
    assert response.status_code == 200, response.text
    result = response.json()['results'][0]
    assert result['state'] == 'CONFIRMADA'
    again = client.post('/api/sincronizacion/lote', headers=w['actors']['admin']['header'], json={'operations':[pending]})
    assert again.json()['results'][0] == result
    after = stored(w)
    assert len(after) == len(before)+1
    for old in before:
        assert old in after


def test_authorized_revision_preserves_original_uuid_and_history(client, world):
    w = world; original = w['rows']['single', 'first', 'EN_CONFLICTO']
    raw = {**original['raw'], 'operation_id': str(uuid4()), 'original_operation': original['id']}
    response = client.post('/api/sincronizacion/lote', headers=w['actors']['single']['header'], json={'operations':[raw]})
    assert response.status_code == 200, response.text
    result = response.json()['results'][0]
    assert result['state'] == 'CONFIRMADA'
    recovered = get(client, w['actors']['single'], original).json()
    assert recovered['operation_id'] == original['id'] and recovered['state'] == 'EN_CONFLICTO'
    assert recovered['resolved'] is True
    saved = {row['operation_id']:row for row in stored(w)}
    assert saved[raw['operation_id']]['original_operation'] == original['id']
    assert saved[original['id']]['payload_hash'] == hashlib.sha256(json.dumps(original['raw'], sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


def test_cash_compensation_is_validated_only_after_branch_access(client, world):
    w = world; row = w['rows']['admin', 'second', 'EN_CONFLICTO']
    with owner_connection() as conn, conn.cursor() as cur:
        cur.execute("UPDATE operacion_sync SET kind='venta',envelope=envelope||%s WHERE tenant_id=%s AND operation_id=%s",
                    (Json({'kind':'venta', 'cash_received':'50.00'}), w['company']['tenant'], row['id']))
    before = stored(w)
    assert compensate(client, w['actors']['single'], row, '0.00').status_code == 404
    assert compensate(client, w['actors']['both'], row, '0.00').status_code == 422
    assert stored(w) == before
    assert compensate(client, w['actors']['both'], row, '50.00').status_code == 200
    recovered = get(client, w['actors']['both'], row).json()
    assert recovered['resolved'] and recovered['compensation'] == 50.0


def test_denied_accesses_do_not_modify_inventory_sales_or_reservations(client, world):
    w = world; c = w['company']; a = w['actors']['single']
    def business():
        result = {}
        with owner_connection() as conn, conn.cursor() as cur:
            for table in ['inventario', 'venta', 'detalle_venta', 'reserva', 'detalle_reserva', 'movimiento_inventario', 'retencion', 'operacion_sync']:
                cur.execute(f'SELECT row_to_json(t) AS row FROM {table} t WHERE tenant_id=%s', (c['tenant'],))
                result[table] = sorted(json.dumps(r['row'], sort_keys=True) for r in cur.fetchall())
        return result
    before = business()
    for state in ['RECHAZADA', 'CONFIRMADA', 'EN_CONFLICTO']:
        row = w['rows']['admin', 'second', state]
        assert get(client, a, row).status_code == 404
        assert replay(client, a, row).status_code == 404
        assert compensate(client, a, row).status_code == 404
    assert business() == before
