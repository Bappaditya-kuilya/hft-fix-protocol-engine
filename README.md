# HFT FIX Protocol Engine

![CI](https://github.com/Bappaditya-kuilya/hft-fix-protocol-engine/actions/workflows/ci.yml/badge.svg)

Minimal FIX 4.2 reference engine for Tag 35=D (New Order Single). Python 3.12.
C++/Rust would be the real HFT choice; Python is acceptable here because this
is a correctness reference, not a production trading path.

## Quickstart

```bash
python3 -m pytest -q
ruff check .
mypy fix_engine/
```

All three pass on Day-5 (72 tests + 4 benches).

## Structure

```
fix_engine/order_handler.py  # 35=D dict validation (tags 11/55/54/38/40)
fix_engine/auth.py           # thread-safe session registry
fix_engine/framing.py        # TCP buffer: bytes -> frames via BodyLength(9), 64KB cap
fix_engine/parser.py         # frame -> dict + checksum gate, 35=8 encoder
fix_engine/session.py        # Logon/Logout/Heartbeat, per-message seq gap->reject
fix_engine/order_handler.py  # 35=D validation + 35=F cancel, session-checked
fix_engine/reports.py        # 35=8 NEW/REJECTED/CANCELLED builders
fix_engine/audit.py          # bounded queue (10000, drop+count) + WAL writer
fix_engine/engine.py         # hot path: gate->handler->report->push (steps 4-5)
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
- `FramingBuffer.feed` splits stream bytes into frames (split-recv waits,
  coalesced splits, truncated waits, >64KB rejects).
- `parse_frame` validates BodyLength + checksum, returns flat dict;
  `encode_35_8` builds verifiable Execution Reports.
- Session gate: Logon(seq 1)→ACK, per-message seq check (gap/replay→reject,
  no ResendRequest), Logout teardown. Order/cancel handlers reject unknown
  sessions before business logic; full Logon→D→F→Logout flow tested.
- Audit: `try_push` never blocks (QueueFull→drop+count+warn); `run_writer`
  thread drains batches to append-only SQLite WAL. Drops counted, logged,
  and surfaced via `get_stats`.
- Hot path `engine.handle_new_order/handle_cancel`: seq gate → validation →
  35=8 report → queue push. Rejects push nothing.
- 20ms p99 budget covers handler + audit-queue push only (PRD §8 steps 4-5).
  Measured via `make bench` (Python 3.12.11, linux, at `babd0a0`):

  | path | median | p99 (gate) | budget |
  |---|---|---|---|
  | 35=D accept | ~30µs | — | 20ms |
  | 35=F cancel | ~76µs | — | 20ms |
  | reject (bad field) | ~36µs | — | 20ms |
  | seq-reject | ~7µs | — | 20ms |
  | gate (200 calls, perf_counter) | 13µs | 38µs | 20ms |

  Excludes TCP/framing/parser, SQLite writer, socket. CI fails above budget.

## What's not yet (honest gaps)

- Handler takes a dict, not wire bytes — dict→wire orchestration landed Day-4
  (`engine.py`); TCP socket server still out (test client drives engine directly).
- `validate_session` exists but the handler does not call it yet (v1 dead-code
  bug) — wiring lands Day-3 with per-message seq gap→reject, no ResendRequest.
- No audit queue, no SQLite writer, no server socket, no rate limiting.

## Non-goals

No matching engine, equities-only single instrument, single-process, FIX 4.2
only, no UI, not for real money.

## Daily log

- Day-1: harness, corpus, thread-safe registry, explicit 35=D validation,
  lint gate. 5 commits. `pytest -q`: 13 passed.
- Day-2: framing + parser + 35=8 encoder + wire round-trip. 6 commits.
- Day-3: session + seq + cancel + handler wiring + e2e flow. 7 commits.
- Day-4: audit queue + WAL writer + 35=8 builders + hot-path wiring. 8 commits.
- Day-5: benchmark suite + CI gate + real numbers. 6 commits.
- Day-3: _session + seq wiring (pending)_
- Day-4: _35=F + 35=8 encoder (pending)_
- Day-5: _audit queue + writer (pending)_
- Day-6: _benchmark + CI gate (pending)_
- Day-7: _numbers fill-in + final gates (pending)_
