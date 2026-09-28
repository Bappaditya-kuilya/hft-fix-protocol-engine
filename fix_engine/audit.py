"""Bounded audit queue — stdlib only, never blocks."""

import asyncio
import logging
import threading

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
