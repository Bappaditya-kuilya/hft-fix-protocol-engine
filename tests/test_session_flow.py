"""End-to-end session-gated flow: Logon -> D/F -> Logout (PRD section 7)."""

from fix_engine import session
from fix_engine.order_handler import (
    _accepted,
    process_cancel_request,
    process_new_order_single,
)

SID = "E2E-1"

ORDER = {
    "ClOrdID": "E2E-ORD-1",
    "Symbol": "AAPL",
    "Side": 1,
    "OrderQty": 100,
    "OrdType": "2",
}


def test_full_flow():
    ok, m = session.logon(SID, 1)
    assert (ok, m) == (True, "Logon ACK")

    ok, m, action = session.gate_session(
        {"SenderCompID": SID, "MsgSeqNum": 2, "MsgType": "D"}
    )
    assert ok and action == "seq"
    assert process_new_order_single(ORDER, session_id=SID)["status"] == "ACCEPTED"

    ok, m, action = session.gate_session(
        {"SenderCompID": SID, "MsgSeqNum": 3, "MsgType": "F"}
    )
    assert ok and action == "seq"
    assert (
        process_cancel_request(
            {"ClOrdID": "E2E-CXL-1", "OrigClOrdID": "E2E-ORD-1"}, session_id=SID
        )["status"]
        == "CANCELLED"
    )

    ok, m = session.logout(SID)
    assert ok
    assert process_new_order_single(ORDER, session_id=SID)["reason"] == "unknown session"


def test_out_of_order_seq_rejected_before_handler():
    session.logon("E2E-2", 1)
    ok, _m, action = session.gate_session(
        {"SenderCompID": "E2E-2", "MsgSeqNum": 5, "MsgType": "D"}
    )
    assert not ok and action == "reject"
    session.logout("E2E-2")


def test_unknown_session_order_rejected():
    before = set(_accepted)
    assert process_new_order_single(ORDER, session_id="NOPE")["reason"] == "unknown session"
    assert process_cancel_request(
        {"ClOrdID": "X", "OrigClOrdID": "E2E-ORD-1"}, session_id="NOPE"
    )["reason"] == "unknown session"
    assert set(_accepted) == before
