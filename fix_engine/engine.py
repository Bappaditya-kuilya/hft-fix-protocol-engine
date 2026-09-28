"""Hot path: parsed frame -> session gate -> handler -> report -> audit push.

SLA steps 4-5 only (handler + queue push). No I/O, no awaits here.
"""

from fix_engine import audit, reports, session
from fix_engine.order_handler import process_cancel_request, process_new_order_single

_D_MAP = (("11", "ClOrdID"), ("55", "Symbol"), ("54", "Side"), ("38", "OrderQty"), ("40", "OrdType"))


def _map(parsed: dict, *tags: str) -> dict:
    want = set(tags)
    return {name: parsed[t] for t, name in _D_MAP if t in want and t in parsed}


def handle_new_order(parsed: dict, session_id: str) -> tuple[dict, bytes, bool]:
    ok, m, _ = session.gate_session(
        {"SenderCompID": session_id, "MsgSeqNum": parsed.get("34"), "MsgType": "D"}
    )
    if not ok:
        result: dict = {"status": "REJECTED", "reason": m}
        return result, reports.build_rejected(parsed.get("11", ""), m), False
    order = _map(parsed, "11", "55", "54", "38", "40")
    result = process_new_order_single(order, session_id=session_id)
    if result["status"] == "ACCEPTED":
        report = reports.build_new(
            result["order_id"], result["symbol"], order["OrderQty"], order["ClOrdID"]
        )
    else:
        report = reports.build_rejected(order.get("ClOrdID", ""), result["reason"])
    pushed = audit.try_push({"type": "D", "session": session_id, **result})
    return result, report, pushed


def handle_cancel(parsed: dict, session_id: str) -> tuple[dict, bytes, bool]:
    ok, m, _ = session.gate_session(
        {"SenderCompID": session_id, "MsgSeqNum": parsed.get("34"), "MsgType": "F"}
    )
    if not ok:
        result = {"status": "REJECTED", "reason": m}
        return result, reports.build_rejected(parsed.get("11", ""), m), False
    req = {"ClOrdID": parsed.get("11"), "OrigClOrdID": parsed.get("41")}
    result = process_cancel_request(req, session_id=session_id)
    if result["status"] == "CANCELLED":
        report = reports.build_cancelled(result["order_id"], req["ClOrdID"] or "")
    else:
        report = reports.build_rejected(req.get("ClOrdID") or "", result["reason"])
    pushed = audit.try_push({"type": "F", "session": session_id, **result})
    return result, report, pushed
