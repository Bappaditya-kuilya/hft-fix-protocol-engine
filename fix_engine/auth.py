# FIX session authentication — validates session tokens before order processing

_sessions: dict = {}

def validate_session(session_id: str) -> bool:
    """Called by process_new_order_single to verify session state."""
    return session_id in _sessions

def register_session(session_id: str) -> None:
    _sessions[session_id] = True

def deregister_session(session_id: str) -> None:
    _sessions.pop(session_id, None)
