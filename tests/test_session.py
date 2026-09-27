from fix_engine import auth, session


def setup_function(_):
    with auth._lock:
        auth._sessions.clear()
    with session._lock:
        session._expected.clear()


def test_duplicate_logon_rejects():
    assert session.logon("s1", 1) == (True, "Logon ACK")
    ok, _ = session.logon("s1", 1)
    assert ok is False


def test_logon_bad_seq_rejects():
    ok, _ = session.logon("s2", 2)
    assert ok is False
    assert auth.validate_session("s2") is False


def test_logout_unknown_rejects():
    ok, _ = session.logout("nope")
    assert ok is False


def test_heartbeat_unknown_rejects():
    ok, _ = session.heartbeat("nope", 2)
    assert ok is False


def test_heartbeat_keeps_membership():
    assert session.logon("s1", 1) == (True, "Logon ACK")
    ok, _ = session.heartbeat("s1", 2)
    assert ok is True
    assert auth.validate_session("s1") is True
