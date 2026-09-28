"""Bounded audit queue — stdlib only, never blocks."""

import asyncio
import threading

MAXSIZE = 10000

_queue: asyncio.Queue = asyncio.Queue(MAXSIZE)
_dropped = 0
_lock = threading.Lock()


def try_push(event: dict) -> bool:
    global _dropped
    try:
        _queue.put_nowait(event)
        return True
    except asyncio.QueueFull:
        with _lock:
            _dropped += 1
        return False


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
