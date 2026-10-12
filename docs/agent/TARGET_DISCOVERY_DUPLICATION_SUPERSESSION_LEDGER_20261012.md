# Target Discovery — Duplication / Supersession Ledger — 2026-10-12

Status: **CANONICAL ANTI-DUPLICATION LEDGER — NON-AUTHORIZING**

Purpose: prevent future agents from repeating audits, reviving superseded executors, or implementing parallel versions of work already assigned to another lane.

## Canonical rule

Before creating a new target-discovery implementation or audit branch, search this ledger and `TARGET_DISCOVERY_MASTER_AUDIT_INDEX_20261012.md`. Historical branches are evidence; they are not invitations to restart their work.

## Live corrected-replay owner

**Canonical production candidate:** Macha

- implementation: `feat/td-corrected-replay-turnkey-20261012@f74632ed51a0ffc28ac46daf240debbb8c2d6e01`
- launch authority package: `authority/td-corrected-replay-launch-f74632ed-20261012@635f9f00050234f4e90306e97bce131bf741d73c`
- replay executed: **NO** at this ledger freeze
- audit action: review exact package; do not build an alternate executor.

## Quarantined duplicate created by this audit chat

Branch:
`science/td-corrected-replay-turnkey-20261012`

Disposition:
`QUARANTINED_DUPLICATE__REFERENCE_ONLY__DO_NOT_CONTINUE__DO_NOT_MERGE__DO_NOT_USE_FOR_AUTHORITY`

Reason: this chat began implementing the same corrected-replay turnkey stage after Macha had already been explicitly assigned that work. The duplication was caught by the owner and stopped.

Known commits produced before stop include:
- `e547320f4084c1fc2e5a0505488d450090c3c264` — implementation plan
- `dc145746...`, `b98191c9...`, `cb2fdf4...` — contract/test work
- `2910e9c...`, `5a42f934...` — predecessor authentication/test work
- `8b9dc33...`, `9c3e4efa...` — qualification/test work
- `de8dda9...`, `a5b149ef...` — replay-only authority/test work
- `79fc82af...`, `c46929ba...` — orchestrator/test work
- `5b3a66d...` — launcher tests when duplication was stopped

These bytes may be consulted only as non-authoritative reference during an audit. They must never be promoted after observing Macha's results, never be merged into Macha's lane, and never become a fallback implementation without a new prospective owner decision.

## Superseded / immutable target-discovery execution lineages

| Surface | Historical meaning | Current disposition |
|---|---|---|
| PR #245 | CRLF manifest serialization failure before G4/G5 | Immutable failure evidence; superseded by #248/#255/#259 |
| PR #252 | Sample-A label/geometry failure | Immutable failure evidence |
| PR #254 | Independent rerun reproducing #252 | Immutable failure evidence; do not rerun unchanged code |
| PR #248 | Hardened G4/G5 predecessor | Historical implementation; final accepted technical result is #259 |
| PR #255 | `A_NATURAL_MIXTURE` + 35-file/34-matrix repair | Historical repair leading to #259 |
| PR #259 | Value-blind G4/G5 technical PASS | Accepted technical/custody evidence; no biology authority |
| PR #258 | Standalone G6/G7 V2 candidate | Superseded before qualification; preserve defects |
| PR #263 | G7 successor candidate | Superseded before qualification by counterpart-auth sequencing audit |
| PR #266 | Qualification STOP from message assertion | Process evidence only; not biology |
| PR #267/#268 | Counterpart authentication / atomic attempt custody evolution | Superseded for execution by #296/#298 |
| PR #277 | Earlier G6/G7 owner-authorized lane at `fafd4309` | Superseded by spent G6 failure and ff4a21f9 successor |
| PR #281 | First real G6 spent failure: no physical `global_row` | Immutable spent-attempt evidence |
| PR #282 | G6 historical-global-row successor | Accepted producer `ff4a21f9`; no need to rebuild |
| PR #296 | G7 global-row + accepted-G6 bridge successor | Qualified implementation `8d41fb98` |
| PR #298 | G7 one-shot launch package | Executed once; authority spent; preserve package |
| `evidence/td-g7-successor-execution-8d41fb98-20261012` | executed G7 result | `NOT_ESTIMABLE_NO_NATURAL_S174_CELL_OVERLAP`; do not rerun |
| `diag/td-g7-cell-id-namespace-20261012@0b50938e...` | metadata-only disjointness diagnostic | accepted cause: genuinely disjoint natural cell sets |

## Historical science / methods not to reopen without a new hypothesis

### Row binding
TD23/TD33 established that freeze-file global row is assigned before filter/merge. Reset/sample-local row aliases invalidated historical apparent positives. Do not redesign this rule.

### Historical relational stages
TD56/TD57B/TD57C/TD59 definitions and interpretation are frozen for corrected replay. Do not alter thresholds/statistics/locality after seeing corrected outcomes.

### TD57C
Historical FAIL is immutable. Do not rescue or relabel it. A corrected PASS means divergence and triggers a new prospective locality experiment.

### TD59
Original executor remains unrecovered. Use only the pre-admitted replay-closure successor SHA-256 `870ddea0f84f0c868cbce772c9f7506b4c1b35b55e4cd09f9f9e62dbf7425085`; never call it the original.

### TD60
Never qualifyingly executed. Do not call it failed and do not construct outcome history that does not exist.

### Historical Bayesian replication spike
PR #249 terminal `SAMPLER_NOT_ESTIMABLE`. The prospectively tested formulation did not estimate the intended source-general replication object. Do not tune chains/priors/estimand against historical outcomes to make it pass.

### Coordinate/loading/subspace target families
Historical TD13-TD55 work closed multiple universal-coordinate/proxy families. A new attempt requires a materially new biological hypothesis, not a new implementation of the same failed idea.

## Target-scaffold duplication guard

PR #275 is the canonical prospective decision/routing scaffold. Before writing candidate-routing, V79 crosswalk, protected H2H, C6 dependency, or convergence logic, inspect its current files and tests. Do not create a second tournament state machine.

## Synthetic-lane duplication guard

V79 realization/generator/fitting/scoring engineering is a separate lane. Target discovery consumes frozen audited artifacts; it does not rebuild them.

Canonical synthetic realization consumed by target discovery is PR #297 / `bb892356...`. Later synthetic engineering PRs #299-#301 are not target-discovery implementation work.

## Future-agent checklist before starting work

1. Read the master audit index.
2. Check this supersession ledger.
3. Search the exact PR/branch path for an existing implementation, result, or failed attempt.
4. Check whether the work is owned by Macha or another lane.
5. Preserve historical STOP/FAIL/NOT_ESTIMABLE states verbatim.
6. Build only if the current live lane genuinely lacks the required component.

Failure to perform this check is itself a process defect because it risks outcome-aware implementation choice and duplicate scientific machinery.