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


def test_exact_advances():
    session.logon("s1", 1)
    assert session.check_seq("s1", 2) == (True, "ok")
    assert session.check_seq("s1", 3) == (True, "ok")
    with session._lock:
        assert session._expected["s1"] == 4


def test_gap_rejects_without_advancing():
    session.logon("s1", 1)
    ok, msg = session.check_seq("s1", 5)
    assert ok is False
    assert "gap" in msg
    with session._lock:
        assert session._expected["s1"] == 2
    assert session.check_seq("s1", 2) == (True, "ok")


def test_replay_rejects_without_advancing():
    session.logon("s1", 1)
    assert session.check_seq("s1", 2) == (True, "ok")
    ok, msg = session.check_seq("s1", 2)
    assert ok is False
    assert "replay" in msg or "duplicate" in msg
    with session._lock:
        assert session._expected["s1"] == 3


def test_no_resend_emitted():
    import inspect
    import pathlib

    src = pathlib.Path(session.__file__).read_text()
    assert "esend" not in src.lower()
    assert "PossDup" not in src
    assert not hasattr(session, "send_resend_request")
    assert not hasattr(session, "resend_request")
    sig = inspect.signature(session.check_seq)
    assert list(sig.parameters) == ["session_id", "seq"]


def test_gate_logon_heartbeat_logout():
    assert session.gate_session(
        {"SenderCompID": "g1", "MsgSeqNum": 1, "MsgType": "A"}
    ) == (True, "Logon ACK", "logon")
    ok, _, action = session.gate_session(
        {"SenderCompID": "g1", "MsgSeqNum": 2, "MsgType": "0"}
    )
    assert (ok, action) == (True, "heartbeat")
    ok, _, action = session.gate_session(
        {"SenderCompID": "g1", "MsgSeqNum": 3, "MsgType": "D"}
    )
    assert (ok, action) == (True, "seq")
    assert session.gate_session(
        {"SenderCompID": "g1", "MsgSeqNum": 0, "MsgType": "5"}
    ) == (True, "Logout confirm", "logout")


def test_gate_rejects_gap_and_unknown():
    session.logon("g2", 1)
    ok, _, action = session.gate_session(
        {"SenderCompID": "g2", "MsgSeqNum": 9, "MsgType": "D"}
    )
    assert ok is False and action == "reject"
    ok, _, action = session.gate_session(
        {"SenderCompID": "nope", "MsgSeqNum": 2, "MsgType": "D"}
    )
    assert ok is False and action == "reject"
