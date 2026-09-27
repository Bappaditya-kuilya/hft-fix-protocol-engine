# Security

## Session auth

Mandatory, not decorative. Every order-bearing message must pass
`validate_session` before processing. Status Day-1: registry is thread-safe,
wiring into the handler lands Day-3. Unwired paths are rejected in review
until then.

## Sequence numbers

Session Manager checks seq on every message (not just Logon); gap → reject.
No ResendRequest/PossDup — out of scope by design.

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
