# SDD ledger — plan: docs/superpowers/plans/2026-10-10-td-g6-g7-standalone-v2-v3-preflight.md

Execution mode: inline/native coordinator session.

Pre-flight interfaces:
- Task 1 common gate -> Tasks 2/3 runtime consumers: exact V3 preflight/mapping schemas and V2 runtime authority; no conflict after controlling amendment.
- Task 2 G6 -> Task 4 cross-entrypoint binding: both use the common authority validator; exact script SHA binding must be symmetric.
- Task 3 G7 -> Task 4 cross-entrypoint binding: both use the common authority validator; G7 remains independently source-authenticating.
- Task 5 documentation consumes exact candidate SHAs/test evidence from Tasks 1-4.

Ruling: original standalone V2 spec's V2 preflight schemas are superseded by the V3-preflight amendment because PR #252/#254 exposed the contract defect and PR #255 prospectively repaired it.

Environment limitation: coordinator cannot execute repository pytest in its container; no RED/GREEN or PASS claims may be made here.

## Upstream G4/G5 evidence now available

PR #259 produced a reviewed value-blind V3 PASS from exact code `bf253a4dd62d943398f9ff59ed8b1e74777140a5`.

Exact audited evidence bytes:
- driver receipt SHA-256 `62f2af4a97ce77c72907992dff673dcdea74ac17bcd080bd4d77d39e483e8bae`;
- mapping receipt SHA-256 `6a97cb30ae1899fa249e2d4b6d292ed900283cc3c434749688de99a9cd8828e0`;
- replay manifest SHA-256 `4bde5f8041394410bf81e9c7c7edbf8553767a87bb31956f0b47bb50026f7660`.

This proves mapping/custody readiness only. It does not authorize values.

## PR #258 current disposition

Exact head `c5d9c64cf42dc8c12d91672458689c0a0a67f472` is now:

`SUPERSEDED_BEFORE_QUALIFICATION__DO_NOT_QUALIFY_OR_EXECUTE`

Static audit after PR #259 found three additional G7 custody defects before any execution:

1. S174 `meta.npz` / `counts.npz` are globally hash-authenticated, but overlap shards are not re-hashed immediately before later metadata/count value use (TOCTOU gap).
2. duplicate S174 `cell_id` values would silently collapse when constructing the row lookup dictionary.
3. duplicate CSR address indices within one S174 row could silently overwrite during dictionary conversion.

Controlling audit:
`docs/agent/TD_G7_S174_IMMEDIATE_REAUTH_AUDIT_20261010.md`

No result is affected because G7 has never run.

A successor must implement only the fail-closed custody repairs and tests, then be qualified against the exact PR #259 bytes above. No V2 runtime authorization may be created as part of qualification.

## Corrected biological replay prefreeze

Before any corrected value outcome is opened, the downstream historical replay has also been prospectively frozen:
- science spec: `docs/superpowers/specs/2026-10-10-td-corrected-biological-replay-prefreeze.md`;
- machine prefreeze: `custody/target_discovery/TD_CORRECTED_BIOLOGICAL_REPLAY_PREFREEZE_20261010.json`;
- adapter qualification plan: `docs/superpowers/plans/2026-10-10-td-corrected-replay-adapter-qualification.md`.

This prefreeze requires replay of all already-opened historical TD56/TD57B/TD57C/TD59 objects after future reviewed G6/G7 PASS and a second owner authorization, while preserving each stage's internal historical stop rules. TD57C remains an immutable historical prospective FAIL.

## Current sequence

1. Preserve PR #259 PASS evidence byte-for-byte.
2. Build a successor to superseded PR #258 head with the G7 immediate-use custody repairs.
3. Qualify successor focused tests + exact PR #259 receipt compatibility only.
4. STOP for owner review.
5. Only an explicit owner decision may authorize G6/G7 integrity execution.
6. G6 PASS then G7 PASS required; mismatch/NOT_ESTIMABLE stops.
7. Review G6/G7 receipts.
8. A second explicit owner decision is required for corrected TD56/TD57B/TD57C/TD59 biological replay.
9. Replay all four under the frozen prefreeze; then STOP again.
10. No target selection, TD60 or training without new authority.

Hard terminal:
`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
