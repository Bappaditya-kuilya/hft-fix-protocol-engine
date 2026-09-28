"""Day-5 handler+push microbenchmarks (pytest-benchmark 5.3.0)."""

import itertools
from typing import Any

import pytest

from fix_engine import audit, session
from fix_engine.engine import handle_cancel, handle_new_order

SID = "BENCH-1"

_seq = itertools.count(2)
_ids = itertools.count(0)


@pytest.fixture(scope="module")
def bench_sid() -> str:
    session.logout(SID)
    ok, msg = session.logon(SID, 1)
    assert ok, msg
    while audit.drain_batch(1000):
        pass
    return SID


def _d(seq: int, cl: str) -> dict:
    return {
        "8": "FIX.4.2",
        "35": "D",
        "49": SID,
        "34": str(seq),
        "11": cl,
        "55": "AAPL",
        "54": "1",
        "38": "100",
        "40": "2",
    }


def _f(seq: int, cl: str, orig: str) -> dict:
    return {"35": "F", "49": SID, "34": str(seq), "11": cl, "41": orig}


def test_bench_new_order(benchmark: Any, bench_sid: str) -> None:
    assert bench_sid == SID
    while audit.drain_batch(1000):
        pass
    result, _report, pushed = handle_new_order(
        _d(next(_seq), f"BENCH-N-{next(_ids)}"), SID
    )
    assert result["status"] == "ACCEPTED" and pushed is True
    benchmark(
        lambda: handle_new_order(
            _d(next(_seq), f"BENCH-N-{next(_ids)}"), SID
        )
    )
    stats = audit.get_stats()
    print(f"bench_new_order dropped={stats['dropped']} queued={stats['queued']}")


def test_bench_cancel(benchmark: Any, bench_sid: str) -> None:
    assert bench_sid == SID
    while audit.drain_batch(1000):
        pass

    def _round() -> tuple:
        orig = f"BENCH-O-{next(_ids)}"
        cxl = f"BENCH-X-{next(_ids)}"
        handle_new_order(_d(next(_seq), orig), SID)
        return handle_cancel(_f(next(_seq), cxl, orig), SID)

    result, _report, pushed = _round()
    assert result["status"] == "CANCELLED" and pushed is True
    benchmark(_round)
    stats = audit.get_stats()
    print(f"bench_cancel dropped={stats['dropped']} queued={stats['queued']}")
