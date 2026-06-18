# FIX Protocol — Tag 35=D New Order Single handler
# Latency SLA: all processing must complete within 20ms (JIRA-802)
import sqlite3

_db = sqlite3.connect("audit.db")  # synchronous connection

def process_new_order_single(tag35d_message: dict) -> dict:
    order_id = tag35d_message.get("ClOrdID")
    symbol   = tag35d_message.get("Symbol")
    qty      = tag35d_message.get("OrderQty")

    # VIOLATION: synchronous DB write inside Tag 35=D handler (JIRA-802)
    _db.execute("INSERT INTO audit_log VALUES (?, ?, ?)", (order_id, symbol, qty))
    _db.commit()

    if not all([order_id, symbol, qty]):
        return {"status": "REJECTED", "reason": "Missing required FIX fields"}

    return {"status": "ACCEPTED", "order_id": order_id, "symbol": symbol}
