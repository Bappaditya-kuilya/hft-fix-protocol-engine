"""Wire integration: bytes -> FramingBuffer -> parse_frame."""

from fix_engine.framing import FramingBuffer
from fix_engine.parser import parse_frame
from tests.fix_samples import CORPUS


def test_split_feed_roundtrip():
    for key, raw in CORPUS.items():
        buf = FramingBuffer()
        half = len(raw) // 2
        assert buf.feed(raw[:half]) == []
        frames = buf.feed(raw[half:])
        assert len(frames) == 1
        msg = parse_frame(frames[0])
        assert msg["35"] == key


def test_coalesced_feed_roundtrip():
    blob = b"".join(CORPUS[k] for k in ("D", "F", "8"))
    buf = FramingBuffer()
    frames = buf.feed(blob)
    assert len(frames) == 3
    assert [parse_frame(f)["35"] for f in frames] == ["D", "F", "8"]
    assert parse_frame(frames[0])["11"] == "ORD1001"
