"""FIX 35=8 execution report builders — pure, no I/O."""

from fix_engine.parser import encode_35_8


def _req(name: str, v: object) -> str:
    if not isinstance(v, str) or not v.strip():
        raise ValueError(f"missing {name}")
    s = v.strip()
    try:
        s.encode("ascii")
    except UnicodeEncodeError:
        raise ValueError(f"{name}: non-ascii") from None
    return s


def _qty(qty: int | str) -> str:
    if isinstance(qty, bool):
        raise ValueError("missing qty")  # noqa: TRY004 - spec: missing -> ValueError
    if isinstance(qty, int):
        if qty <= 0:
            raise ValueError("qty: must be a positive number")
        return str(qty)
    if isinstance(qty, str):
        s = qty.strip()
        if not s:
            raise ValueError("missing qty")
        try:
            if not float(s) > 0:
                raise ValueError("qty: must be a positive number")
        except ValueError as e:
            if "qty" in str(e):
                raise
            raise ValueError("qty: must be a positive number") from None
        try:
            s.encode("ascii")
        except UnicodeEncodeError:
            raise ValueError("qty: non-ascii") from None
        return s
    raise ValueError("missing qty")


def _order_id(order_id: object, cl: str) -> str:
    if order_id is None or (isinstance(order_id, str) and not order_id.strip()):
        return f"EX-{cl}"
    if not isinstance(order_id, str):
        raise ValueError("missing order_id")  # noqa: TRY004 - spec: missing -> ValueError
    return _req("order_id", order_id)


def build_new(order_id: str, symbol: str, qty: int | str, cl_ord_id: str) -> bytes:
    """NEW ack 35=8, OrdStatus 39=0 / ExecType 150=0."""
    cl = _req("ClOrdID (cl_ord_id)", cl_ord_id)
    sym = _req("Symbol (symbol)", symbol)
    q = _qty(qty)
    oid = _order_id(order_id, cl)
    return encode_35_8(
        {
            "11": cl,
            "37": oid,
            "17": f"E-{cl}",
            "20": "0",
            "39": "0",
            "150": "0",
            "55": sym,
            "54": "1",
            "38": q,
            "40": "2",
        }
    )


def build_rejected(cl_ord_id: str, reason: str) -> bytes:
    """Reject 35=8, OrdStatus 39=8 / ExecType 150=8 with Text(58)."""
    cl = _req("ClOrdID (cl_ord_id)", cl_ord_id)
    if not isinstance(reason, str) or not reason.strip():
        raise ValueError("missing Text(58)/reason")
    try:
        reason.encode("ascii")
    except UnicodeEncodeError:
        raise ValueError("Text(58)/reason: non-ascii") from None
    return encode_35_8(
        {
            "11": cl,
            "37": f"EX-{cl}",
            "17": f"E-{cl}",
            "20": "0",
            "39": "8",
            "150": "8",
            "58": reason,
        }
    )


def build_cancelled(orig_cl_ord_id: str, cl_ord_id: str) -> bytes:
    """Cancel ack 35=8, OrdStatus 39=4 / ExecType 150=4 with OrigClOrdID(41)."""
    orig = _req("OrigClOrdID (orig_cl_ord_id)", orig_cl_ord_id)
    cl = _req("ClOrdID (cl_ord_id)", cl_ord_id)
    return encode_35_8(
        {
            "11": cl,
            "41": orig,
            "37": f"EX-{cl}",
            "17": f"E-{cl}",
            "20": "0",
            "39": "4",
            "150": "4",
        }
    )
