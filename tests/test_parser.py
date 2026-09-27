import pytest

from fix_engine.parser import parse_frame
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
