# HFT FIX Protocol Engine

![CI](https://github.com/Bappaditya-kuilya/hft-fix-protocol-engine/actions/workflows/ci.yml/badge.svg)

A minimal FIX 4.2 reference engine: bytes in, Execution Reports out, every
order audited without blocking the hot path. Python 3.12, stdlib only
(+ `pytest-benchmark` for measurement).

C++/Rust would be the real HFT choice; Python is the right call here because
this is a correctness reference you can read end to end, not a production
trading path. Not for real money.

## What it does

- Parses real FIX 4.2 wire messages (`SOH`-delimited `tag=value`,
  `BodyLength(9)`, `CheckSum(10)`) — never trusts a bare dict off the socket.
- Handles `New Order Single (35=D)`, `Order Cancel Request (35=F)`, and
  session traffic (`Logon 35=A`, `Logout 35=5`, `Heartbeat 35=0`).
- Validates `ClOrdID(11)`, `Symbol(55)`, `Side(54)`, `OrderQty(38)`,
  `OrdType(40)` with field-specific rejects; sequence gaps reject
  (`No ResendRequest` — deliberately out of scope).
- Answers every request with an `Execution Report (35=8)`:
  `NEW`, `REJECTED` (with `Text(58)` reason), or `CANCELLED`.
- Audits every accepted/rejected order through a bounded non-blocking queue
  into append-only SQLite (WAL mode). Drops — only under sustained overload —
  are counted, logged, and surfaced, never silent.

## Architecture

```
bytes ──▶ Framing Buffer ──▶ Parser ──▶ Session Gate ──▶ Handler ──▶ 35=8 Encoder ──▶ wire
              │                │              │               │                            │
              │                │              │               └──────▶ Audit Queue ──▶ SQLite (WAL)
              │                │              │                        (maxsize 10000, drop+count)
              │                │              └── Logon/Logout/Heartbeat + per-message seq check
              │                └── BodyLength + checksum validation
              └── stream → frames via BodyLength(9); 1MB buffer cap, 64KB message cap
```

The timed hot path is handler + queue push only (see Performance).
Framing, parsing, SQLite writes, and sockets stay outside the budget.

## Quickstart

```bash
python3 -m pytest -q        # full suite
make bench                  # one-command benchmark + 20ms gate
ruff check .                # lint
mypy fix_engine/            # types
```

## Performance

`make bench`, Python 3.12, Linux — medians:

| path | median | budget (p99) |
|---|---|---|
| 35=D accept | ~30µs | 20ms |
| 35=F cancel | ~76µs | 20ms |
| reject (bad field) | ~36µs | 20ms |
| seq-reject | ~7µs | 20ms |
| gate, 200 calls (`perf_counter`) | p50 10µs | p99 29µs / 20ms |

CI runs the suite, the benchmarks, and the gate on every push and fails
above budget.

## Configuration

| knob | default | where |
|---|---|---|
| audit queue bound | 10000, drop + `dropped_counter` | `fix_engine/audit.py` |
| framing buffer cap | 1MB, drop flood | `fix_engine/framing.py` |
| max message size | 64KB `BodyLength` | `fix_engine/framing.py` |
| latency budget | 20ms p99, handler + push | `tests/test_bench_gate.py` |

## Structure

```
fix_engine/framing.py        # stream bytes -> frames
fix_engine/parser.py         # frame <-> dict, checksum, 35=8 wire codec
fix_engine/session.py        # Logon/Logout/Heartbeat + seq gap->reject
fix_engine/auth.py           # thread-safe session registry
fix_engine/order_handler.py  # 35=D / 35=F validation, session-checked
fix_engine/reports.py        # 35=8 NEW / REJECTED / CANCELLED builders
fix_engine/audit.py          # bounded queue + background WAL writer
fix_engine/engine.py         # hot path: gate -> handler -> report -> push
benchmarks/                  # pytest-benchmark suite (handler + push only)
tests/                       # 75 tests incl. framing edge cases + e2e flow
```

## Security

Session auth is mandatory — unknown sessions are rejected before business
logic. See [SECURITY.md](SECURITY.md) for sequence handling, parser-boundary
rules, audit integrity, and the one known gap: no rate limiting (stated,
not hidden).

## Limitations

- No TCP server: a test client feeds bytes; the engine owns bytes onward.
- Single equities-style order model: `Symbol` is not allow-listed, and there
  is no book, no matching, no multi-asset logic.
- FIX 4.2 only. No UI. Single process, single node.
