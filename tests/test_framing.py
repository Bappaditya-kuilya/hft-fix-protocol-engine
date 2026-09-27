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


def test_split_header_wait():
    fb = FramingBuffer()
    raw = CORPUS["A"]
    part = raw[:8]
    assert fb.feed(part) == []
    assert fb.pending_bytes() == len(part)
    assert fb.feed(raw[8:]) == [raw]
    assert fb.pending_bytes() == 0


def test_truncated_body_wait():
    fb = FramingBuffer()
    raw = CORPUS["8"]
    cut = len(raw) - 10
    assert fb.feed(raw[:cut]) == []
    assert fb.pending_bytes() == cut
    assert fb.feed(raw[cut:]) == [raw]
    assert fb.pending_bytes() == 0


def test_oversized_reject():
    fb = FramingBuffer()
    bad = b"8=FIX.4.2\x019=70000\x01" + b"X" * 100
    assert fb.feed(bad) == []
    assert fb.pending_bytes() == 0
    raw = CORPUS["D"]
    assert fb.feed(raw) == [raw]


def test_garbage_before_8_resync():
    fb = FramingBuffer()
    raw = CORPUS["5"]
    assert fb.feed(b"\x00\xffGARBAGE" + raw) == [raw]
    assert fb.pending_bytes() == 0
