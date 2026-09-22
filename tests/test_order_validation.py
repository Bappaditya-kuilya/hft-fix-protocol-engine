from fix_engine.order_handler import process_new_order_single


def valid_order():
    return {
        "ClOrdID": "ORD1",
        "Symbol": "AAPL",
        "Side": 1,
        "OrderQty": 100,
        "OrdType": "2",
    }


def test_valid_accept():
    res = process_new_order_single(valid_order())
    assert res == {"status": "ACCEPTED", "order_id": "ORD1", "symbol": "AAPL"}


def test_missing_clordid():
    msg = valid_order()
    del msg["ClOrdID"]
    res = process_new_order_single(msg)
    assert res["status"] == "REJECTED" and "ClOrdID" in res["reason"]


def test_empty_symbol():
    msg = valid_order()
    msg["Symbol"] = "  "
    res = process_new_order_single(msg)
    assert res["status"] == "REJECTED" and "Symbol" in res["reason"]


def test_bad_side():
    res = process_new_order_single({**valid_order(), "Side": 3})
    assert res["status"] == "REJECTED" and "Side" in res["reason"]


def test_zero_qty():
    res = process_new_order_single({**valid_order(), "OrderQty": 0})
    assert res["status"] == "REJECTED" and "OrderQty" in res["reason"]


def test_missing_ordtype():
    msg = valid_order()
    del msg["OrdType"]
    res = process_new_order_single(msg)
    assert res["status"] == "REJECTED" and "OrdType" in res["reason"]


def test_never_raises():
    for bad in [
        {},
        {
            "ClOrdID": None,
            "Symbol": None,
            "Side": None,
            "OrderQty": None,
            "OrdType": None,
        },
        {**valid_order(), "OrderQty": "abc"},
        {**valid_order(), "OrderQty": -5},
    ]:
        res = process_new_order_single(bad)
        assert res["status"] == "REJECTED" and "reason" in res
