# Security

## Session auth

Mandatory, not decorative. Order/cancel handlers call `validate_session`
before field validation — unknown sessions get REJECTED without touching
business logic or `_accepted` state. Proven by `tests/test_session_flow.py`.

## Sequence numbers

Session Manager checks seq on every message via `gate_session` (not just Logon); gap → reject.
No ResendRequest/PossDup — out of scope by design. Landed Day-3.

## Parser boundary

Malformed input (bad checksum, wrong BodyLength, missing tags) is rejected
before business logic; the handler never raises. Wire-message fixtures live
in `tests/fix_samples.py`; framing edge tests (split/coalesced/truncated/
oversized >64KB) landed Day-2 in `tests/test_framing.py`.

## Secrets

None in repo. Demo credentials (if ever added) go in env vars with a
committed `.env.example`. Never commit live secrets.

## Audit integrity

Writes are append-only, no delete/update path. Bounded queue
(maxsize=10000): on full, drop + increment `dropped_counter`, log every drop,
surface the counter in benchmark output. Silent drops fail review.

## Known gaps

No rate limiting yet — stated openly, not hidden. Not production-hardened;
do not trade real money on this.

## Daily log

- Day-1: registry lock, field validation, corpus verify. Wiring + queue
  still pending (see gaps above).
- Day-2: framing + parser boundary landed, audited via round-trip tests.
- Day-3: session wiring + seq gate landed, proven by e2e flow test.
