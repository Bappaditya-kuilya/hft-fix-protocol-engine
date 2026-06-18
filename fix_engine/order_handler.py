# FIX Protocol — Tag 35=D New Order Single handler
# Latency SLA: all processing must complete within 20ms (JIRA-802)

def process_new_order_single(tag35d_message: dict) -> dict:
    order_id = tag35d_message.get("ClOrdID")
    symbol   = tag35d_message.get("Symbol")
    qty      = tag35d_message.get("OrderQty")

    if not all([order_id, symbol, qty]):
        return {"status": "REJECTED", "reason": "Missing required FIX fields"}

    return {"status": "ACCEPTED", "order_id": order_id, "symbol": symbol}
