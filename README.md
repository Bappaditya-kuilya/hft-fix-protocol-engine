# HFT FIX Protocol Engine

Minimal FIX 4.2 reference engine for Tag 35=D (New Order Single). Python 3.12.
C++/Rust would be the real HFT choice; Python is acceptable here because this
is a correctness reference, not a production trading path.

## Quickstart

```bash
python3 -m pytest -q
ruff check .
mypy fix_engine/
```

All three pass on Day-1 (13 tests).

## Structure

```
fix_engine/order_handler.py  # 35=D dict validation (tags 11/55/54/38/40)
fix_engine/auth.py           # thread-safe session registry
tests/fix_samples.py         # 6 wire reference messages (35=D/F/8/A/5/0)
tests/test_*.py              # corpus, auth, validation, smoke
```

## What's real (Day-1)

- `process_new_order_single` validates ClOrdID/Symbol/Side(1|2)/OrderQty(>0)/OrdType,
  rejects with field-specific reason, never raises. Shape: ACCEPTED
  `{"status","order_id","symbol"}` / REJECTED `{"status","reason"}`.
- Session registry is `threading.Lock`-guarded; signatures preserved.
- `tests/fix_samples.py` builds/verifies wire messages with auto
  BodyLength(9) + CheckSum(10); 6-message corpus round-trips.
- 20ms p99 budget covers handler + audit-queue push only (PRD §8 steps 4-5).
  No benchmark numbers yet — bench suite lands Day-6.

## What's not yet (honest gaps)

- Handler takes a dict, not wire bytes — TCP framing + parser land Day-2.
- `validate_session` exists but the handler does not call it yet (v1 dead-code
  bug) — wiring lands Day-3 with per-message seq gap→reject, no ResendRequest.
- No audit queue, no SQLite writer, no server socket, no rate limiting.

## Non-goals

No matching engine, equities-only single instrument, single-process, FIX 4.2
only, no UI, not for real money.

## Daily log

- Day-1: harness, corpus, thread-safe registry, explicit 35=D validation,
  lint gate. 5 commits. `pytest -q`: 13 passed.
- Day-2: _framing + parser (pending)_
- Day-3: _session + seq wiring (pending)_
- Day-4: _35=F + 35=8 encoder (pending)_
- Day-5: _audit queue + writer (pending)_
- Day-6: _benchmark + CI gate (pending)_
- Day-7: _numbers fill-in + final gates (pending)_
