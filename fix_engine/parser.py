"""FIX 4.2 frame parser — pure stdlib, no I/O."""

SOH = b"\x01"


def parse_frame(frame: bytes) -> dict[str, str]:
    """Parse one raw FIX frame into a flat str dict, verifying 8/9/10."""
    if not frame.endswith(SOH):
        raise ValueError("missing trailing SOH")
    if not frame.startswith(b"8=FIX.4.2\x01"):
        raise ValueError("bad BeginString, want 8=FIX.4.2")
    first = frame.index(SOH)
    second = frame.find(SOH, first + 1)
    if second < 0 or not frame[first + 1 : second].startswith(b"9="):
        raise ValueError("missing 9= BodyLength")
    try:
        declared = int(frame[first + 1 : second][2:])
    except ValueError:
        raise ValueError("bad BodyLength value") from None
    i = frame.rfind(b"\x0110=")
    if i < 0:
        raise ValueError("missing 10= checksum")
    if len(frame[second + 1 : i + 1]) != declared:
        raise ValueError("BodyLength mismatch")
    try:
        want = int(frame[i + 4 : -1])
    except ValueError:
        raise ValueError("bad checksum value") from None
    if sum(frame[: i + 1]) % 256 != want:
        raise ValueError("checksum mismatch")
    out: dict[str, str] = {}
    for raw in frame[:-1].split(SOH):
        if b"=" not in raw:
            raise ValueError(f"bad field {raw!r}: missing '='")
        tag, val = raw.split(b"=", 1)
        try:
            out[tag.decode("ascii")] = val.decode("ascii")
        except UnicodeDecodeError:
            raise ValueError("non-ascii field") from None
    if out.get("8") != "FIX.4.2":
        raise ValueError("bad BeginString, want 8=FIX.4.2")
    return out


def encode_35_8(body_fields: dict[str, str] | list[tuple[str, str]]) -> bytes:
    """Build a 35=8 execution report with auto BodyLength + checksum."""
    items = list(body_fields.items()) if isinstance(body_fields, dict) else list(body_fields)
    tags = {t for t, _ in items}
    if "150" not in tags:
        raise ValueError("missing ExecType 150")
    if tags & {"8", "9", "10", "35"}:
        raise ValueError("reserved tag in body_fields: 8/9/10/35")
    body = "35=8\x01" + "".join(f"{t}={v}\x01" for t, v in items)
    body_b = body.encode("ascii")
    pre = f"8=FIX.4.2\x019={len(body_b)}\x01".encode("ascii") + body_b
    return pre + f"10={sum(pre) % 256:03d}\x01".encode("ascii")
