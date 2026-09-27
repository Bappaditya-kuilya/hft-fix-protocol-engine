"""FIX session Logon/Logout/Heartbeat — stdlib only, no I/O."""

import threading

from fix_engine.auth import deregister_session, register_session, validate_session

_expected: dict[str, int] = {}
_lock = threading.Lock()


def logon(session_id: str, seq: int) -> tuple[bool, str]:
    if seq != 1:
        return False, "expected seq 1"
    if validate_session(session_id):
        return False, "duplicate logon"
    register_session(session_id)
    with _lock:
        _expected[session_id] = 2
    return True, "Logon ACK"


def logout(session_id: str) -> tuple[bool, str]:
    if not validate_session(session_id):
        return False, "unknown session"
    deregister_session(session_id)
    with _lock:
        _expected.pop(session_id, None)
    return True, "Logout confirm"


def check_seq(session_id: str, seq: int) -> tuple[bool, str]:
    if not validate_session(session_id):
        return False, "unknown session"
    with _lock:
        exp = _expected.get(session_id)
        if exp is None:
            return False, "unknown session"
        if seq < exp:
            return False, "duplicate/replay"
        if seq > exp:
            return False, "gap"
        _expected[session_id] = exp + 1
        return True, "ok"


def heartbeat(session_id: str, seq: int) -> tuple[bool, str]:
    if not validate_session(session_id):
        return False, "unknown session"
    return check_seq(session_id, seq)
