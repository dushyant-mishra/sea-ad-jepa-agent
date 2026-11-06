# Unified Task 3 controller review checkpoint — exact head 851544e8 — 2026-10-15

Status: `TASK3_OPEN__INDEPENDENT_REVIEW_REQUIRED`
Authority effect: **NONE**

## Exact lineage

- Frozen Task 0: `e37a22b8059c0a4a93a789a8ca916fb7acde9fe3`.
- Frozen Task 1: `799d2e235901dfad9ce3b305c767a1c989e362f6`.
- Frozen Task 2: `c7dfff1cee608e4a101855d42cf0af08491c2aaf`.
- Task 3 implementation PR: #392.
- Exact controller review candidate: `851544e8dc2a3881193a4d5bbcf07933e1d61149`.
- Original preserved RED branch/PR: #391, exact RED `9456553d7352bb4f620baaba95051f85aab448ae`.

Task 3 has **not** been independently accepted or frozen. Unified Task 4 implementation remains blocked.

Global authority remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

## Scope implemented

Task 3 implements the prospective `TD_QUALIFICATION_REGISTRY_V1` authority layer for A2/A5/A6:

- exact Task-1 stage and lineage vocabularies;
- immutable promotion history;
- active revocation/supersession;
- one-stage-at-a-time promotion;
- recursively authenticated prerequisite graphs;
- no authoritative stored `ready=true` override;
- exact Task-2 manifest/access/per-unit identity binding;
- dependency-object recomputation rather than trusted digest strings;
- content-validation receipt binding where content qualification is required;
- explicit external-evidence semantics for process isolation and cross-process ledger custody;
- population-authority and claim-scope restrictions inherited from frozen Task 2;
- identity-bound recursive-verification cache invalidation, including reverse dependencies.

## Task 2 carry-forward R1–R6

The registry keeps the accepted Task 2 residuals binding rather than converting them into prose-only caveats:

- **R1:** `HUMAN_EXECUTABLE` requires process-isolation evidence: producer process isolated, harness-driven finalization, reader-fit values outside producer process, and protected partitions physically absent.
- **R2:** content-bearing nested contracts require owning-task content qualification; role/digest labels alone do not create substantive authority.
- **R3:** `FIXTURE_UNBOUND` cannot satisfy current-TD real-reference authority; authoritative use requires the frozen Task 2 population authority.
- **R4:** cross-process receipt use requires persistent ledger and signing-key custody evidence.
- **R5:** pooled donor-level cross-fit scope cannot be relabelled as per-fold source-stratified authority; fold 4 has one held-out NPH52 donor.
- **R6:** recursive verification uses identity-bound caching with invalidation on dependency mutation.

## Iterative RED/GREEN history

The owner followed the standing iterative operating rule instead of freezing the first GREEN.

### Initial RED

Exact RED: `9456553d7352bb4f620baaba95051f85aab448ae`.

Result: 19 intended Task 3 failures because `registry_v1.py` did not exist; inherited synthetic integration stayed green.

### Hostile self-audit cycles 1–5

Historical commits/RED branches preserve attacks and repairs covering, among other issues:

- exact dependency authentication versus matching digest strings;
- controller/reviewer object authentication and actor identity;
- promotion-receipt provenance;
- exact prerequisite record binding;
- supersession/revocation identities;
- reverse-dependency cache invalidation;
- R1/R4 semantic evidence rather than role labels alone.

Pre-RED6 controller GREEN head `a2d403beb019a4e02e523cac36171772dbacc5ce` passed 46 focused Task 3 tests and 149 unified tests, but was **not frozen**.

### RED6 — actor-level self-qualification attack

Final owner audit found a genuine A5 hole: comparing a 64-hex controller object identity with 40-hex producer/executor code identities could never prove that the underlying actor was independent.

Preserved RED6 exact head:

`eff7afe99163fc7b18a5adda52bd17a6c3f89174`

RED6 result:

- 3 new intended actor-independence failures;
- 46 prior Task 3 tests remained green.

The attack demonstrated that the same actor could otherwise wear a `QUALIFICATION_CONTROLLER` role object while also being the scientific producer/executor.

### GREEN6

`RegistryUnit` now binds exact canonical identities for:

- `producer_actor_identity` with role `SCIENTIFIC_PRODUCER`;
- `executor_actor_identity` with role `SCIENTIFIC_EXECUTOR`.

Promotion/revocation resolve those objects and compare their underlying `actor_id` values against controller/reviewer actor identities.

Required separations:

- qualification controller actor != producer actor;
- qualification controller actor != executor actor;
- independent reviewer actor != controller actor;
- independent reviewer actor != producer actor;
- independent reviewer actor != executor actor;
- revocation controller actor != producer/executor actors.

Actor identity is decision-bearing. Changing producer/executor actor identity through `reidentify_unit(...)` resets the unit to `SEMANTICS_ONLY` and `REQUIRES_REQUALIFICATION`.

Historical pre-RED6 fixtures were migrated to resolve the exact actor objects they hash; actor identity was **not** made optional for backward compatibility.

One-shot repair/migration scripts are historical implementation evidence only and must not be treated as reusable authority entry points:

- `scripts/agent/task3_red6_actor_identity_repair.py`;
- `scripts/agent/task3_green6_actor_resolver_patch.py`;
- `scripts/agent/task3_green6_fixture_migration.py`;
- `.github/workflows/task3-red6-actor-repair.yml`.

## Fresh exact-head controller verification

Exact candidate: `851544e8dc2a3881193a4d5bbcf07933e1d61149`.

Task 3 workflow run `38754803093`, job `116490276627`:

- focused `tests/v5/td_unified/test_registry_v1*.py`: **51 passed**;
- full `tests/v5/td_unified`: **154 passed**;
- checkout uses full history (`fetch-depth: 0`).

On the same exact head:

- frozen Task 2 workflow `38754803025`: **SUCCESS**;
- frozen Task 1 workflow `38754803012`: **SUCCESS**;
- inherited unified synthetic integration `38754803248`: **SUCCESS**.

Diff from frozen Task 2 `c7dfff1c...` is Task-3-only: registry implementation/schema, Task 3 tests/fixtures, Task 3 workflows, and historical hardening/migration scripts/docs. No frozen Task 0–2 production file is modified.

Controller GREEN is **not** independent acceptance.

## Required next gate

Only an independent exact-head Macha review of `851544e8dc2a3881193a4d5bbcf07933e1d61149` may decide whether Task 3 can freeze.

If accepted, the lawful transition is:

`TASK3_MAY_BE_FROZEN__UNIFIED_TASK4_MAY_BEGIN_PROSPECTIVELY`

If rejected:

`TASK3_REMAINS_OPEN__UNIFIED_TASK4_REMAINS_BLOCKED`

No later authority is implied by Task 3 acceptance.

## Standing owner protocol for every successor

Every successor must continue iterative self-audit → RED → minimal repair → focused regression → inherited regression → renewed self-audit. Preserve all historical audits, scripts, results, exact identities, failures, decisions and no-repeat classifications in PR #322 and PR #323 so no future agent repeats settled work. Heavy/private data stay hash/path-custodied rather than duplicated into Git.
