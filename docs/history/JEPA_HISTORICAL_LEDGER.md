# JEPA HISTORICAL LEDGER

Chronology class for material recovered and committed now:

`RECOVERED_HISTORICAL_BYTES__BACKFILLED_20260902`

This ledger separates **historical scientific chronology** from **Git chronology**. A 2026-09-02 backfill commit proves only that the referenced bytes were mirrored on or after that date. It does not prove that they were committed when the scientific work originally occurred.

## Status vocabulary

- `ACTIVE` — current authority or active execution lane.
- `CLOSED_PASS` — completed gate whose conclusions remain binding.
- `CLOSED_FAIL` — scientifically closed failed branch; no rescue unless a new prospectively authorized branch explicitly supersedes it.
- `SUPERSEDED` — historically important but no longer current authority.
- `RECOVERED` — exact or hash-bound historical material recovered after the fact.
- `PENDING_BACKFILL` — known authority not yet mirrored into the GitHub tree.

## Ledger

| Approx. date | Historical stage | Status | Key conclusion / role | Key hash or binding | Git mirror state |
|---|---|---|---|---|---|
| 2026-08-07 | Stage81A2 split/data freeze | CLOSED_PASS | 149 foundation train / 19 development / 19 sealed firewall; zero leakage | commit `808ce4f170055c5568cc5c1e0e3a56415b52f908` | present on `main` |
| 2026-08-20/21 | u100/u205/T1 adjudication | SUPERSEDED_DIAGNOSTIC | optimization improved while contextual biology eroded; u0 retained stronger query-local geometry | historical handoff/review hashes pending path recovery | PENDING_BACKFILL |
| 2026-08-25 | H-space V2 | CLOSED_PASS_DIAGNOSTIC | u0 correct-cell H beats donor-distinct wrong-cell for all protected programs at protected evidence levels; u205 erodes context | historical decision package pending path recovery | PENDING_BACKFILL |
| 2026-08-25/26 | V6R5A rare-label/cohort recovery | RECOVERED | exact protected program/rare-label/cohort authority recovered | program weights `001375ec77c5b606ad0972073c1daa6ad14b0e517f05ea23c6c9b3110203ff70`; cohort labels `ba50eb0a6683621fc60fd30f2126bb9fb4a609286360463a964dfb8a7b4af52b` | PENDING_BACKFILL |
| 2026-08-26 | adaptive FULL104 calibration preflight | CLOSED_FAIL | small-cohort/scope mismatch blocked lawful derivation | stop authorities pending path recovery | PENDING_BACKFILL |
| 2026-08-28 | FULL104 metadata scope reconciliation | CLOSED_PASS | 4,553,407 lawful rows; 104 fit donors; 42 operators; three-state observation semantics | reconciliation authority pending mirror | PENDING_BACKFILL |
| 2026-08-28+ | failed D_shared/shared-latent branch | CLOSED_FAIL | `TEACHER_BIOLOGY_LIMIT`; D_shared rescue permanently closed | closed root `0641735d6619ff3cfdc3cce8673c38f678591d1a4a685ea229470737c9311e6d` | PENDING_BACKFILL |
| 2026-08-29/30 | CONTEXTUAL_TEACHER_TARGET_V1 F0 | CLOSED_PASS | safe q-scalar withholding and gradient/firewall semantics established | F0 root `e45dd8d885c4f6918bcaf0b24bde971c08c16322b27555e112693f46e42ddb4b` | PENDING_BACKFILL |
| 2026-08-30/31 | early F1 query-prefix/knee design | CLOSED_FAIL_SUPERSEDED | near-exhaustive prefix design computationally invalid; knee framework discarded | stop packages pending path recovery | PENDING_BACKFILL |
| 2026-09-01 | F1 frozen two-draw design | ACTIVE | 2,781 cells; 44,496 assignments; design-sampled w² estimand; 43,108 unique compute pairs after safe dedup | assignment SHA `12fd5f1549bb600e6bf52605196024f91bae28d7d20cb35a327d67c383f2c617` | PENDING_BACKFILL |
| 2026-09-01 | F1 final truth table / decision v4 | ACTIVE | one authoritative gate per endpoint; current claim scope and QID-v2 semantics | truth table `76d420a0aa71f9b062b7394453f1f33282f7c78a956fc950fceb7ead682dcf5e`; decision `5215faffe1e90b6567054fd7fb4d62d501787dbacd704e09ff28af9c65d45913` | PENDING_BACKFILL |
| 2026-09-01/02 | HC3 15A3/15A4 frontier | CLOSED_PASS_AFTER_REPAIR | 15A3 premature frontier termination repaired; exhaustive 70-triple replication frontier established | 15A4 manifest `a112bd4907f2c20b4346179264391ceb8d3e9ceee42f7a8bcb1bcd153e4cb09f` | PENDING_BACKFILL |
| 2026-09-02 | HC3 15B selection | CLOSED_PASS | unique componentwise-maximal replicated nuisance triple `(5,0,4)` selected | design `5d2fda2e81a6edd63241ccf996fe0e5086275233e765daae19509be24cd518e3`; contract `3fc95316ad51205dd758bf93c6425ecfaebe3ed52e2bfacd6f03bb0406d0a4ac` | PENDING_BACKFILL |
| 2026-09-02 | 15B provenance repair | CLOSED_PASS | review bindings structured/hash-bound; chronology not overclaimed | supplement manifest `6b0abab515b847fda5724b3194efdd4ad1f58ec0a7e3ad20fa9941f24e6e513d` | PENDING_BACKFILL |
| 2026-09-02 | HC3 15C decision integration | CLOSED_PASS | frozen nuisance design integrated without changing reviewed decision engine; real execution remains gated | decision integration `5dfd5858f1e8865f871b633a033e400f2d7fb5e2fb52bebbc613f7efed1bce2a` | PENDING_BACKFILL |
| 2026-09-02 | real F1 reader/forward/executor preflight | ACTIVE_NEXT | bind current population to safe forward execution, sharding, sufficient statistics and resume | not frozen yet | not applicable |

## Backfill rules

1. Preserve exact historical bytes whenever available.
2. Preserve multiple meaningful historical versions under distinct stage/version/run paths.
3. Never flatten different hashes onto one destination basename.
4. A reconstructed narrative must be labelled reconstructed; do not present it as recovered exact historical wording.
5. Generated pytest output, staging copies, cache replicas and duplicate extraction trees are excluded unless they are the sole recoverable copy of a known authority.
6. Large public data may be mirrored if materially necessary; otherwise preserve exact source identity, hash and reconstruction provenance.
7. Every approved historical backfill batch should update this ledger with its Git commit SHA.
