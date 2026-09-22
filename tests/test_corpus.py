from tests.fix_samples import CORPUS, verify_fix


def test_corpus_roundtrip():
    assert set(CORPUS) == {"D", "F", "8", "A", "5", "0"}
    for raw in CORPUS.values():
        assert isinstance(raw, bytes)
        assert bytes(raw) == raw
        assert verify_fix(raw) is True
