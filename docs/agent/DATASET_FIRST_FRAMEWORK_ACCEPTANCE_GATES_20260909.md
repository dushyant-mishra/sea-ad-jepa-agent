# Dataset-first framework acceptance gates — 2026-09-09

## Gate 0 — Current state

`STOP_T0_R5_REAL_POPULATION_AUTHORITY_NOT_MATERIALIZED`

## Gate 1 — Raw-source population authority

Open only when:

- 20,804 rows proven from real H5AD bytes;
- package exists on disk;
- replay verifies stored == recomputed == expected roots;
- artifacts include exact sizes and SHA-256 hashes;
- no pathology fields read or emitted.

## Gate 2 — Technical completeness

Open only when:

- Gate 1 is open;
- technical completeness is materialized from real dataset parents;
- Q_DEPTH is derived from proven source-library values;
- Q_DETECT is derived from 35,076-position B1 projection;
- closure rows/nnz are reconciled against counts payloads;
- package replays from disk.

## Gate 3 — Eligible donors

Open only when:

- Gate 2 is open;
- age/sex authority is replayed;
- AT8 availability authority is replayed;
- estimability preflight is replayed;
- no numeric AT8 confirmation values have been accessed.

## Gate 4 — Teacher/student production

Open only when:

- Gate 3 is open;
- teacher/student inputs are authority-root-bound;
- model/data split identities are immutable;
- GPU pipeline reads from materialized packages, not detached arrays;
- downstream evaluation rules are frozen before response access.
