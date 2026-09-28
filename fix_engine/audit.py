"""Bounded audit queue — stdlib only, never blocks."""

import asyncio
import json
import logging
import sqlite3
import threading
from pathlib import Path

MAXSIZE = 10000

_queue: asyncio.Queue = asyncio.Queue(MAXSIZE)
_dropped = 0
_lock = threading.Lock()
_log = logging.getLogger(__name__)


def try_push(event: dict) -> bool:
    global _dropped
    try:
        _queue.put_nowait(event)
        return True
    except asyncio.QueueFull:
        with _lock:
            _dropped += 1
            total = _dropped
        _log.warning("audit drop queue full dropped=%d", total)
        return False


def get_stats() -> dict[str, int]:
    return {"queued": _queue.qsize(), "dropped": dropped_counter()}


def dropped_counter() -> int:
    with _lock:
        return _dropped


def drain_batch(max_n: int = 500) -> list[dict]:
    out: list[dict] = []
    for _ in range(max_n):
        try:
            out.append(_queue.get_nowait())
        except asyncio.QueueEmpty:
            break
    return out


def write_batch(db_path: str | Path, events: list[dict]) -> int:
    if not events:
        return 0
    con = sqlite3.connect(db_path)
    try:
        con.execute("PRAGMA journal_mode=WAL;")
        con.execute(
            "CREATE TABLE IF NOT EXISTS audit"
            " (id INTEGER PRIMARY KEY, payload TEXT)"
        )
        con.executemany(
            "INSERT INTO audit (payload) VALUES (?)",
            [(json.dumps(e),) for e in events],
        )
        con.commit()
        return len(events)
    finally:
        con.close()


def run_writer(db_path: str | Path, stop: threading.Event, poll_s: float = 0.05) -> None:
    while not stop.is_set():
        batch = drain_batch()
        if batch:
            write_batch(db_path, batch)
        else:
            stop.wait(poll_s)
