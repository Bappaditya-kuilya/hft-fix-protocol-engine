"""20ms budget gate without pytest-benchmark (stdlib perf_counter only)."""

import time

from fix_engine import session
from fix_engine.engine import handle_new_order

SID = "GATE-1"
N = 200
BUDGET = 0.020


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


def test_gate_p99_under_20ms() -> None:
    session.logout(SID)
    ok, msg = session.logon(SID, 1)
    assert ok, msg
    durs: list[float] = []
    seq = 2
    for i in range(N):
        t0 = time.perf_counter()
        result, _, _ = handle_new_order(_d(seq, f"GATE-{i}"), SID)
        durs.append(time.perf_counter() - t0)
        assert result["status"] == "ACCEPTED"
        seq += 1
    durs.sort()
    p50 = durs[len(durs) // 2]
    p99 = durs[min(len(durs) - 1, int(0.99 * len(durs)))]
    print(f"gate p50={p50 * 1000:.3f}ms p99={p99 * 1000:.3f}ms n={len(durs)}")
    assert p99 < BUDGET, f"p99 {p99 * 1000:.3f}ms exceeds 20ms budget"
