"""La espera acotada conserva el límite y libera cupos incluso si falla getconn."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import nullcontext
import threading
import pytest
from psycopg2.pool import PoolError
from app import database


class Connection:
    def cursor(self):
        return nullcontext(self)

    def execute(self, *args):
        pass

    def commit(self):
        pass

    def rollback(self):
        pass


def test_pool_waits_for_previous_request_without_extra_connection(monkeypatch):
    class LimitedPool:
        def __init__(self):
            self.active = 0
            self.peak = 0

        def getconn(self):
            if self.active:
                raise PoolError('pool lleno')
            self.active += 1
            self.peak = max(self.peak, self.active)
            return Connection()

        def putconn(self, conn):
            self.active -= 1

    limited = LimitedPool()
    monkeypatch.setattr(database, 'get_pool', lambda: limited)
    monkeypatch.setattr(database, '_pool_slots', threading.BoundedSemaphore(1))
    monkeypatch.setattr(database, 'DB_POOL_WAIT_SECONDS', 2)
    entered = threading.Event()

    def next_request():
        entered.set()
        with database.get_connection():
            return 'atendida'

    with ThreadPoolExecutor(max_workers=1) as executor:
        with database.get_connection():
            waiting = executor.submit(next_request)
            assert entered.wait(1)
            assert not waiting.done()
        assert waiting.result(timeout=2) == 'atendida'
    assert limited.peak == 1 and limited.active == 0


def test_pool_timeout_and_failed_checkout_do_not_leak_slots(monkeypatch):
    slots = threading.BoundedSemaphore(1)
    monkeypatch.setattr(database, '_pool_slots', slots)
    monkeypatch.setattr(database, 'DB_POOL_WAIT_SECONDS', 0.01)

    class BrokenPool:
        def getconn(self):
            raise PoolError('conexión no disponible')

    monkeypatch.setattr(database, 'get_pool', lambda: BrokenPool())
    slots.acquire()
    with pytest.raises(PoolError, match='espera'):
        with database.get_connection():
            pass
    slots.release()
    with pytest.raises(PoolError, match='no disponible'):
        with database.get_connection():
            pass
    assert slots.acquire(blocking=False)
    slots.release()
