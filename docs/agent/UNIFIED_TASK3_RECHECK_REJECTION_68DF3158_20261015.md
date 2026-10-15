# Unified Task 3 focused re-check rejection — 2026-10-15

Controlling independent re-check verdict: `REJECT_UNIFIED_TASK3`.

Reviewed exact code candidate:
`68df31584d17f91da2635cdf8e03bbe93695f9d1`

Independent review branch/head:
`review/macha-task0-independent-review-20261014` at `6825f53d`.

PR #392 head at review was `0a25f72cdf5ab408c8ed08878636bb3ba3467151`; commits above the reviewed code candidate were documentation-ledger only and do not change the reviewed code bytes.

Closed: B1, B4, B6.

Still blocking:
- N1 CRITICAL: Task 3 does not apply frozen Task 2 manifest/population validators; forged authenticated-reader inputs can reach RRR.
- N2 CRITICAL: KNOWN_TRUTH_QUALIFIED can be declared at genesis and consumed without sealed-challenge evidence.
- B3-V IMPORTANT: content validator is not bound to the closed actor registry; producer-as-validator passes.
- B3-E IMPORTANT: prerequisite/process-isolation/ledger evidence issuer is not actor-bound.
- B3-R IMPORTANT: actor registry itself is unanchored; producer can mint a registry containing its own controller/reviewer.
- B5-F IMPORTANT: fresh custody can forget prior revocation and re-qualify the same unit.

Task 2 residuals after re-check: R1 OPEN, R2 OPEN, R3 OPEN, R4 OPEN, R5 PASS, R6 CLOSED.

Carry forward: actor hashes are identifiers rather than credentials; custody state remains editable in-process; `registry_v1_legacy.promote_unit` is a custody-free public path; `RegistryUnit` should enforce Task 1 law at construction; workflow should explicitly declare `permissions: contents: read`.

Hostile re-check: 38 checks total; 31 expected, 7 bad, 4 notes. Local full suite: 177 passed using a non-mutating wrapper to force the repository `tests` package ahead of an unrelated installed PyMC `tests` package; this is local, not CI, evidence.

Next repair scope: first preserve the new hostile probes as RED tests, then repair only `N1, N2, B3-V, B3-E, B3-R, B5-F`. Do not reopen B1/B4/B6 absent changed-byte regressions.

Gate: `TASK3_REMAINS_OPEN__UNIFIED_TASK4_REMAINS_BLOCKED`.

Global authority remains `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`.