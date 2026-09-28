"""T7: hot path is handler + queue push only, 20ms scope steps 4-5."""

from fix_engine import audit, session
from fix_engine.engine import handle_cancel, handle_new_order
from fix_engine.parser import parse_frame

SID = "ENG-1"


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


def test_accept_pushes_audit_and_report_parses():
    session.logon(SID, 1)
    result, report, pushed = handle_new_order(_d(2, "ENG-ORD-1"), SID)
    assert result["status"] == "ACCEPTED" and pushed is True
    assert parse_frame(report)["35"] == "8"
    assert audit.get_stats()["queued"] >= 1


def test_gap_rejects_without_push_or_handler():
    before = audit.get_stats()["queued"] + audit.dropped_counter()
    result, _report, pushed = handle_new_order(_d(99, "ENG-ORD-2"), SID)
    assert result["status"] == "REJECTED" and pushed is False
    after = audit.get_stats()["queued"] + audit.dropped_counter()
    assert after == before


def test_unknown_session_rejects():
    result, _report, pushed = handle_new_order(_d(2, "ENG-ORD-3"), "GHOST")
    assert result["reason"] == "unknown session" and pushed is False


def test_cancel_flow():
    session.logon("ENG-2", 1)
    handle_new_order({**_d(2, "ENG-ORD-9"), "49": "ENG-2"}, "ENG-2")
    result, report, pushed = handle_cancel(
        {"35": "F", "49": "ENG-2", "34": "3", "11": "ENG-CXL-1", "41": "ENG-ORD-9"},
        "ENG-2",
    )
    assert result["status"] == "CANCELLED" and pushed is True
    assert parse_frame(report)["39"] == "4"
