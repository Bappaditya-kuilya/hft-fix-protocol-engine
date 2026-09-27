from fix_engine.order_handler import (
    _accepted,
    process_cancel_request,
    process_new_order_single,
)


def test_known_ref_cancelled():
    _accepted.clear()
    _accepted.add("ORD1")
    res = process_cancel_request({"ClOrdID": "CX1", "OrigClOrdID": "ORD1"})
    assert res == {"status": "CANCELLED", "order_id": "ORD1"}
    assert "ORD1" not in _accepted


def test_unknown_ref_rejected_no_state_change():
    _accepted.clear()
    _accepted.add("ORD1")
    res = process_cancel_request({"ClOrdID": "CX2", "OrigClOrdID": "NOPE"})
    assert res["status"] == "REJECTED" and "unknown OrigClOrdID" in res["reason"]
    assert _accepted == {"ORD1"}


def test_missing_orig_rejected():
    _accepted.clear()
    res = process_cancel_request({"ClOrdID": "CX3"})
    assert res["status"] == "REJECTED" and "OrigClOrdID" in res["reason"]
    assert _accepted == set()


def test_accept_records_clordid():
    _accepted.clear()
    res = process_new_order_single(
        {
            "ClOrdID": "ORD-D",
            "Symbol": "AAPL",
            "Side": 1,
            "OrderQty": 100,
            "OrdType": "2",
        }
    )
    assert res["status"] == "ACCEPTED"
    assert "ORD-D" in _accepted


def test_double_cancel_idempotent():
    _accepted.clear()
    process_new_order_single(
        {
            "ClOrdID": "ORD-D",
            "Symbol": "AAPL",
            "Side": 1,
            "OrderQty": 100,
            "OrdType": "2",
        }
    )
    first = process_cancel_request({"ClOrdID": "CX-D1", "OrigClOrdID": "ORD-D"})
    assert first == {"status": "CANCELLED", "order_id": "ORD-D"}
    assert "ORD-D" not in _accepted
    second = process_cancel_request({"ClOrdID": "CX-D2", "OrigClOrdID": "ORD-D"})
    assert second["status"] == "REJECTED" and "unknown OrigClOrdID" in second["reason"]
