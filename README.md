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

All three pass on Day-6 (74 tests + 4 benches).

## Structure

```
fix_engine/order_handler.py  # 35=D validation + 35=F cancel, session-checked
fix_engine/auth.py           # thread-safe session registry
fix_engine/framing.py        # stream buffer (no socket): bytes -> frames via BodyLength(9), 64KB cap
fix_engine/parser.py         # frame -> dict + checksum gate, 35=8 encoder
fix_engine/session.py        # Logon/Logout/Heartbeat, per-message seq gap->reject
fix_engine/reports.py        # 35=8 NEW/REJECTED/CANCELLED builders
fix_engine/audit.py          # bounded queue (10000, drop+count) + WAL writer
fix_engine/engine.py         # hot path: gate->handler->report->push (steps 4-5)
tests/fix_samples.py         # 6 wire reference messages (35=D/F/8/A/5/0)
tests/test_*.py              # 16 files: corpus, framing, parser, auth, session,
                             # validation, cancel, flow, engine, audit, reports,
                             # round-trip, bench gate, smoke
```

## What's real (Day-1)

- `process_new_order_single` validates ClOrdID/Symbol/Side(1|2)/OrderQty(>0)/OrdType,
  rejects with field-specific reason, never raises (unhashable ClOrdID →
  REJECTED; report ids stringified). Shape: ACCEPTED
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
  35=8 report → queue push. Validation rejects are audited too; only
  seq/unknown-session gate rejects skip the queue.
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

- No TCP socket server (test client feeds bytes directly); no rate limiting.
- Single equities-style order model — Symbol is not allow-listed, no
  multi-asset logic (and none planned).

## Non-goals

No matching engine, equities-only single instrument, single-process, FIX 4.2
only, no UI, not for real money.

## Daily log

- Day-1: harness, corpus, thread-safe registry, explicit 35=D validation,
  lint gate. 6 commits, harness green.
- Day-2: framing + parser + 35=8 encoder + wire round-trip. 6 commits.
- Day-3: session + seq + cancel + handler wiring + e2e flow. 7 commits.
- Day-4: audit queue + WAL writer + 35=8 builders + hot-path wiring. 8 commits.
- Day-5: benchmark suite + CI gate + real numbers. 5 commits.
- Day-6: 1:1 audit fixes + done-gate. Commits below.

## Done-gate (5-set, Day-6)

- Code quality: pass — 74 green + ruff + mypy + CI success on `ebe6d85`.
- Architecture: pass — framing/parser/session/engine/audit split matches
  hot-path steps 4-5 scope; bounded queue never blocks.
- Domain credibility: pass after Day-6 fixes — never-raises proven by tests,
  rejects-audited stated exactly, no allow-list claimed.
- Resume signal: pass after Day-6 fixes — no duplicates, no stale gaps,
  counts match `git log`.
- Git hygiene: pass — small commits, no manufactured history, no force-pushes.
