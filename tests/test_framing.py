from fix_engine.framing import FramingBuffer
from tests.fix_samples import CORPUS, verify_fix


def test_single_frame():
    fb = FramingBuffer()
    raw = CORPUS["D"]
    assert verify_fix(raw)
    assert fb.feed(raw) == [raw]
    assert fb.pending_bytes() == 0


def test_coalesced():
    fb = FramingBuffer()
    a = CORPUS["D"]
    b = CORPUS["F"]
    assert verify_fix(a) and verify_fix(b)
    assert fb.feed(a + b) == [a, b]
    assert fb.pending_bytes() == 0


def test_pending_bytes_empty():
    fb = FramingBuffer()
    assert fb.pending_bytes() == 0
    assert fb.feed(b"") == []
