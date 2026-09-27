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


def gate_session(msg: dict) -> tuple[bool, str, str]:
    sid = msg.get("SenderCompID", msg.get("49"))
    raw_seq = msg.get("MsgSeqNum", msg.get("34"))
    typ = msg.get("MsgType", msg.get("35"))
    if sid is None or raw_seq is None or typ is None:
        return False, "missing field", "reject"
    try:
        seq = int(raw_seq)  # type: ignore[arg-type]
    except (ValueError, TypeError):
        return False, "bad seq", "reject"
    session_id = str(sid)
    msg_type = str(typ)
    if msg_type == "A":
        ok, m = logon(session_id, seq)
        return ok, m, "logon" if ok else "reject"
    if msg_type == "5":
        ok, m = logout(session_id)
        return ok, m, "logout" if ok else "reject"
    if msg_type == "0":
        ok, m = heartbeat(session_id, seq)
        return ok, m, "heartbeat" if ok else "reject"
    ok, m = check_seq(session_id, seq)
    return ok, m, "seq" if ok else "reject"
