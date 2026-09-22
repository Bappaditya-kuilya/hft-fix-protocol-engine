SOH = chr(1)


def build_fix(body_fields: list[tuple[str, str]], msg_type: str) -> bytes:
    body = f"35={msg_type}{SOH}" + "".join(f"{t}={v}{SOH}" for t, v in body_fields)
    body_b = body.encode("ascii")
    head = f"8=FIX.4.2{SOH}9={len(body_b)}{SOH}".encode("ascii")
    pre = head + body_b
    return pre + f"10={sum(pre) % 256:03d}{SOH}".encode("ascii")


def verify_fix(msg: bytes) -> bool:
    try:
        if not msg.startswith(b"8=FIX.4.2\x01") or not msg.endswith(b"\x01"):
            return False
        i = msg.rfind(b"\x0110=")
        if i < 0:
            return False
        if sum(msg[: i + 1]) % 256 != int(msg[i + 4 : -1]):
            return False
        first = msg.index(b"\x01")
        second = msg.index(b"\x01", first + 1)
        tag9 = msg[first + 1 : second]
        if not tag9.startswith(b"9="):
            return False
        return len(msg[second + 1 : i + 1]) == int(tag9[2:])
    except Exception:
        return False


CORPUS: dict[str, bytes] = {
    "D": build_fix(
        [
            ("49", "CLIENT1"),
            ("56", "EXCHANGE"),
            ("34", "100"),
            ("52", "20260922-12:00:00.000"),
            ("11", "ORD1001"),
            ("55", "AAPL"),
            ("54", "1"),
            ("38", "100"),
            ("40", "2"),
            ("44", "150.25"),
            ("59", "0"),
        ],
        "D",
    ),
    "F": build_fix(
        [
            ("49", "CLIENT1"),
            ("56", "EXCHANGE"),
            ("34", "101"),
            ("52", "20260922-12:00:01.000"),
            ("11", "ORD1002"),
            ("41", "ORD1001"),
            ("55", "AAPL"),
            ("54", "1"),
            ("38", "100"),
        ],
        "F",
    ),
    "8": build_fix(
        [
            ("49", "EXCHANGE"),
            ("56", "CLIENT1"),
            ("34", "200"),
            ("52", "20260922-12:00:00.500"),
            ("11", "ORD1001"),
            ("37", "EX12345"),
            ("17", "EXEC1"),
            ("20", "0"),
            ("39", "0"),
            ("150", "0"),
            ("55", "AAPL"),
            ("54", "1"),
            ("38", "100"),
            ("40", "2"),
            ("44", "150.25"),
            ("6", "0"),
            ("14", "0"),
            ("151", "100"),
        ],
        "8",
    ),
    "A": build_fix(
        [
            ("49", "CLIENT1"),
            ("56", "EXCHANGE"),
            ("34", "1"),
            ("52", "20260922-11:59:59.000"),
            ("98", "0"),
            ("108", "30"),
        ],
        "A",
    ),
    "5": build_fix(
        [
            ("49", "CLIENT1"),
            ("56", "EXCHANGE"),
            ("34", "102"),
            ("52", "20260922-12:05:00.000"),
            ("58", "Session shutdown"),
        ],
        "5",
    ),
    "0": build_fix(
        [
            ("49", "EXCHANGE"),
            ("56", "CLIENT1"),
            ("34", "201"),
            ("52", "20260922-12:00:30.000"),
        ],
        "0",
    ),
}
