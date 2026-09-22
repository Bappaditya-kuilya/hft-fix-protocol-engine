# FIX session authentication — validates session tokens before order processing
import threading

_sessions: dict = {}
_lock = threading.Lock()

def validate_session(session_id: str) -> bool:
    """Called by process_new_order_single to verify session state."""
    with _lock:
        return session_id in _sessions

def register_session(session_id: str) -> None:
    with _lock:
        _sessions[session_id] = True

def deregister_session(session_id: str) -> None:
    with _lock:
        _sessions.pop(session_id, None)
