class FramingBuffer:
    MAX_BUFFER = 1 << 20

    def __init__(self) -> None:
        self._buf = bytearray()

    def feed(self, data: bytes) -> list[bytes]:
        self._buf += data
        if len(self._buf) > self.MAX_BUFFER:
            self._buf.clear()
        out: list[bytes] = []
        while True:
            if len(self._buf) == 0:
                break
            if not self._buf.startswith(b"8="):
                idx = self._buf.find(b"8=")
                if idx == -1:
                    if self._buf.endswith(b"8"):
                        del self._buf[:-1]
                    else:
                        self._buf.clear()
                    break
                del self._buf[:idx]
                if len(self._buf) == 0:
                    break
            first = self._buf.find(b"\x01")
            if first == -1:
                break
            second = self._buf.find(b"\x01", first + 1)
            if second == -1:
                break
            tag9 = bytes(self._buf[first + 1 : second])
            if not tag9.startswith(b"9="):
                self._drop_to_next_msg()
                break
            try:
                body_len = int(tag9[2:])
            except ValueError:
                self._drop_to_next_msg()
                break
            if body_len < 0 or body_len > 65536:
                self._drop_to_next_msg()
                break
            total = second + 1 + body_len + 7
            if len(self._buf) < total:
                break
            out.append(bytes(self._buf[:total]))
            del self._buf[:total]
        return out

    def _drop_to_next_msg(self) -> None:
        nxt = self._buf.find(b"8=", 1)
        if nxt == -1:
            if self._buf.endswith(b"8"):
                del self._buf[:-1]
            else:
                self._buf.clear()
        else:
            del self._buf[:nxt]

    def pending_bytes(self) -> int:
        return len(self._buf)
