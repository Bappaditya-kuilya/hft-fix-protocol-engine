import pytest

from fix_engine.parser import parse_frame
from fix_engine.reports import build_new, build_rejected


def test_new_roundtrip_verifies_length_checksum():
    raw = build_new("EX1", "AAPL", 100, "C1")
    d = parse_frame(raw)  # raises on bad 9/10
    assert d["35"] == "8"
    assert d["11"] == "C1" and d["37"] == "EX1"
    assert d["17"] == "E-C1" and d["20"] == "0"
    assert d["39"] == "0" and d["150"] == "0"
    assert d["55"] == "AAPL" and d["54"] == "1"
    assert d["38"] == "100" and d["40"] == "2"


def test_new_37_auto():
    d = parse_frame(build_new("", "AAPL", "100", "C9"))
    assert d["37"] == "EX-C9"


@pytest.mark.parametrize("kw", [{"symbol": ""}, {"cl_ord_id": " "}, {"qty": ""}, {"qty": 0}])
def test_new_missing_raises_with_field(kw):
    base = {"order_id": "EX1", "symbol": "AAPL", "qty": 100, "cl_ord_id": "C1"}
    base.update(kw)
    with pytest.raises(ValueError):
        build_new(**base)


def test_rejected_preserves_11_and_text():
    raw = build_rejected("C1", "bad price")
    d = parse_frame(raw)
    assert d["35"] == "8" and d["11"] == "C1"
    assert d["39"] == "8" and d["150"] == "8"
    assert d["58"] == "bad price"


def test_rejected_missing_raises():
    with pytest.raises(ValueError, match="ClOrdID|cl_ord_id"):
        build_rejected("", "x")
    with pytest.raises(ValueError, match="58|reason"):
        build_rejected("C1", " ")
