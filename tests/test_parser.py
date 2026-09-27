import pytest

from fix_engine.parser import encode_35_8, parse_frame
from tests.fix_samples import CORPUS, verify_fix


def test_all_corpus_parse():
    assert set(CORPUS) == {"D", "F", "8", "A", "5", "0"}
    for typ, raw in CORPUS.items():
        assert verify_fix(raw) is True
        d = parse_frame(raw)
        assert d["8"] == "FIX.4.2"
        assert d["35"] == typ


def test_byte_flip_rejects():
    raw = bytearray(CORPUS["D"])
    raw[len(raw) // 2] ^= 1
    with pytest.raises(ValueError):
        parse_frame(bytes(raw))


def _with_declared_length(raw: bytes, delta: int) -> bytes:
    first = raw.index(b"\x01")
    second = raw.index(b"\x01", first + 1)
    declared = int(raw[first + 1 : second][2:]) + delta
    head = raw[: first + 1] + f"9={declared}\x01".encode("ascii")
    i = raw.rfind(b"\x0110=")
    pre = head + raw[second + 1 : i + 1]
    return pre + f"10={sum(pre) % 256:03d}\x01".encode("ascii")


def test_length_mismatch_rejects():
    bad = _with_declared_length(CORPUS["D"], 1)
    assert verify_fix(bad) is False
    with pytest.raises(ValueError, match="BodyLength"):
        parse_frame(bad)


def _exec_fields(exec_type: str) -> dict[str, str]:
    return {
        "49": "EXCHANGE",
        "56": "CLIENT1",
        "34": "200",
        "52": "20260922-12:00:00.500",
        "11": "ORD1001",
        "37": "EX12345",
        "17": "EXEC1",
        "20": "0",
        "39": exec_type,
        "150": exec_type,
        "55": "AAPL",
        "54": "1",
        "38": "100",
    }


@pytest.mark.parametrize("exec_type", ["0", "8", "4"])
def test_encode_35_8_roundtrip(exec_type: str):
    raw = encode_35_8(_exec_fields(exec_type))
    assert verify_fix(raw) is True
    d = parse_frame(raw)
    assert d["35"] == "8" and d["150"] == exec_type


def test_encode_35_8_missing_exectype_raises():
    fields = _exec_fields("0")
    del fields["150"]
    with pytest.raises(ValueError, match="150"):
        encode_35_8(fields)
