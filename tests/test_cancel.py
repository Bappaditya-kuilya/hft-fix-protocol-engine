from fix_engine.order_handler import _accepted, process_cancel_request


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
