import json
import logging
import pathlib
import sqlite3
import threading
import time
from pathlib import Path

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


def test_drop_emits_warning(caplog) -> None:  # type: ignore[no-untyped-def]
    for i in range(audit.MAXSIZE):
        audit.try_push({"i": i})
    with caplog.at_level(logging.WARNING):
        assert audit.try_push({"overflow": True}) is False
    assert any("audit drop" in r.message for r in caplog.records)


def test_stats_reflect_queued_dropped() -> None:
    assert audit.get_stats() == {"queued": 0, "dropped": 0}
    audit.try_push({"a": 1})
    audit.try_push({"b": 2})
    assert audit.get_stats() == {"queued": 2, "dropped": 0}
    for i in range(audit.MAXSIZE - 2):
        audit.try_push({"i": i})
    assert audit.get_stats() == {"queued": audit.MAXSIZE, "dropped": 0}
    audit.try_push({"overflow": True})
    assert audit.get_stats() == {"queued": audit.MAXSIZE, "dropped": 1}


def test_write_batch_persists_1000(tmp_path: Path) -> None:
    db = tmp_path / "audit.db"
    events = [{"i": i} for i in range(1000)]
    assert audit.write_batch(db, events) == 1000
    con = sqlite3.connect(db)
    try:
        (n,) = con.execute("SELECT COUNT(*) FROM audit").fetchone()
        assert n == 1000
        (payload,) = con.execute(
            "SELECT payload FROM audit ORDER BY id LIMIT 1"
        ).fetchone()
        assert json.loads(payload) == {"i": 0}
    finally:
        con.close()


def test_journal_mode_is_wal(tmp_path: Path) -> None:
    db = tmp_path / "audit.db"
    audit.write_batch(db, [{"a": 1}])
    con = sqlite3.connect(db)
    try:
        (mode,) = con.execute("PRAGMA journal_mode;").fetchone()
        assert mode.lower() == "wal"
    finally:
        con.close()


def test_write_batch_single_commit() -> None:
    src = pathlib.Path(audit.__file__).read_text()
    assert src.count(".commit()") == 1


def test_append_only() -> None:
    src = pathlib.Path(audit.__file__).read_text()
    assert "UPDATE" not in src
    assert "DELETE" not in src


def test_run_writer_drains(tmp_path: Path) -> None:
    db = tmp_path / "audit.db"
    for i in range(100):
        audit.try_push({"i": i})
    stop = threading.Event()
    t = threading.Thread(target=audit.run_writer, args=(str(db), stop))
    t.start()
    deadline = time.time() + 2.0
    n = 0
    while time.time() < deadline:
        con = sqlite3.connect(db)
        try:
            try:
                (n,) = con.execute("SELECT COUNT(*) FROM audit").fetchone()
            except sqlite3.OperationalError:
                n = 0
        finally:
            con.close()
        if n == 100:
            break
        time.sleep(0.05)
    stop.set()
    t.join(timeout=2.0)
    assert n == 100
    assert not t.is_alive()
