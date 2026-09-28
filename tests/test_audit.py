import time

from fix_engine import audit


def _reset() -> None:
    while audit.drain_batch(1000):
        pass
    with audit._lock:
        audit._dropped = 0


def setup_function(_: object) -> None:
    _reset()


def teardown_function(_: object) -> None:
    _reset()


def test_fill_to_maxsize_then_drop() -> None:
    for i in range(audit.MAXSIZE):
        assert audit.try_push({"i": i}) is True
    assert audit.dropped_counter() == 0
    t0 = time.perf_counter()
    ok = audit.try_push({"overflow": True})
    dt = time.perf_counter() - t0
    assert ok is False
    assert audit.dropped_counter() == 1
    assert dt < 0.1


def test_drop_never_raises_and_stays_bounded() -> None:
    for i in range(audit.MAXSIZE):
        audit.try_push({"i": i})
    for _ in range(10):
        assert audit.try_push({"x": 1}) is False
    assert audit.dropped_counter() == 10
