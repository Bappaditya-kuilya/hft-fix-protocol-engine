# FIX Protocol — Tag 35=D New Order Single handler
# Latency SLA: all processing must complete within 20ms (JIRA-802)


def process_new_order_single(tag35d_message: dict) -> dict:
    cl_ord_id = tag35d_message.get("ClOrdID")
    if cl_ord_id is None or (isinstance(cl_ord_id, str) and not cl_ord_id.strip()):
        return {"status": "REJECTED", "reason": "ClOrdID: missing or empty"}

    symbol = tag35d_message.get("Symbol")
    if symbol is None or (isinstance(symbol, str) and not symbol.strip()):
        return {"status": "REJECTED", "reason": "Symbol: missing or empty"}

    side = tag35d_message.get("Side")
    if side not in (1, 2, "1", "2"):
        return {"status": "REJECTED", "reason": "Side: must be 1 or 2"}

    qty = tag35d_message.get("OrderQty")
    if qty is None:
        return {"status": "REJECTED", "reason": "OrderQty: must be a positive number"}
    try:
        qty_val = float(qty) if not isinstance(qty, bool) else float("nan")
    except (TypeError, ValueError):
        return {"status": "REJECTED", "reason": "OrderQty: must be a positive number"}
    if not qty_val > 0:
        return {"status": "REJECTED", "reason": "OrderQty: must be a positive number"}

    ord_type = tag35d_message.get("OrdType")
    if ord_type is None or (isinstance(ord_type, str) and not ord_type.strip()):
        return {"status": "REJECTED", "reason": "OrdType: missing or empty"}

    _accepted.add(cl_ord_id)
    return {"status": "ACCEPTED", "order_id": cl_ord_id, "symbol": symbol}


_accepted: set[str] = set()


def process_cancel_request(msg: dict) -> dict:
    orig = msg.get("OrigClOrdID")
    if orig is None or (isinstance(orig, str) and not orig.strip()):
        return {"status": "REJECTED", "reason": "OrigClOrdID: missing"}
    cl_ord_id = msg.get("ClOrdID")
    if cl_ord_id is None or (isinstance(cl_ord_id, str) and not cl_ord_id.strip()):
        return {"status": "REJECTED", "reason": "ClOrdID: missing or empty"}
    if orig not in _accepted:
        return {"status": "REJECTED", "reason": "unknown OrigClOrdID"}
    _accepted.discard(orig)
    return {"status": "CANCELLED", "order_id": orig}
