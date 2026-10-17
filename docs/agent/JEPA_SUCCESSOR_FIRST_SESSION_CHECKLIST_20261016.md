# JEPA successor first-session checklist — 2026-10-16

Status: `CURRENT_READ_FIRST_HANDOFF`

Do **not** begin by re-auditing the full repository. The historical lane is already custodied. Re-open settled work only when exact bytes changed, authority/scientific context changed, or a concrete defect is demonstrated.

## Read in this order

1. this checklist;
2. PR #322 `docs/agent/JEPA_LANE_CURRENT_CUSTODY_NO_REPEAT_20261016.md`;
3. PR #322 `results/target_discovery/unified_qualification_v1/JEPA_LANE_CURRENT_CUSTODY_STATE_V2_20261016.json`;
4. PR #404 `docs/agent/UNIFIED_TASK4_EXECUTION_LEDGER_20261016.md`;
5. PR #404 `docs/agent/UNIFIED_TASK4_CANDIDATE_REVIEW_PACKET_20261016.md`;
6. PR #404 `results/target_discovery/unified_qualification_v1/UNIFIED_TASK4_CANDIDATE_STATE_V1.json`;
7. PR #322 `docs/agent/JEPA_HISTORICAL_NO_REPEAT_INDEX_20261015.md` only for older historical detail;
8. PR #322 local artifact custody manifests before touching any local/private bundle.

The older 2026-10-15 handoff/checklist is historical and its Task 3 rejection state is superseded by this file.

## Current frozen authority

- Task 0: `e37a22b8059c0a4a93a789a8ca916fb7acde9fe3`
- Task 1: `799d2e235901dfad9ce3b305c767a1c989e362f6`
- Task 2: `c7dfff1cee608e4a101855d42cf0af08491c2aaf`
- Task 3: `117dd51dea827e734b299982da93991b934bdc8f`
- freeze branch: `freeze/unified-task3-accepted-117dd51d-20261016`
- acceptance PR #401
- Macha acceptance head `c33f2bd2`
- verdict `ACCEPT_UNIFIED_TASK3`

Task 3's rejected predecessors remain evidence and must not be erased or reused as authority: `851544e8...`, `68df3158...`, `d9e58a18...`.

Global authority remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

## Current Task 4 state

Task 4 may proceed prospectively but is not accepted authority.

Design PR #402:
- head `979833a51391248f568426f508cce1d01e3e32a5`
- C1-C9 binding amendment and implementation plan.

RED PR #403:
- head `c5e40b04c6dcbb07d3a92edc9f9677ceb7f584ff`
- first valid RED `38938697657` / `117100597615`: 14 intentional missing-interface failures, read-only token.

Implementation PR #404:
- branch `work/unified-task4-impl-20261016`
- observed current PR head at custody refresh `b31371d62f3270c965d321e61c35898ca6be3721`
- last fully verified code/test head `cfa3b7c4f92a1569639b6733a6956c516d7f4cf4`
- Task 4 run `38946411134` / `117126540739`: focused PASS, projected 100k replay PASS, full unified regression PASS
- same-head Task 1/2/3/synthetic integration regressions PASS
- classification `CANDIDATE_ONLY__INDEPENDENT_EXACT_HEAD_REVIEW_REQUIRED`
- final authority intentionally fail-closed because genuine external C5-C9 context is not wired.

Do not regenerate Task 4 from the design. Review/repair the staged modules already on PR #404.

## Task 4 interfaces already implemented

Current staged modules:

- `challenge_custody_v1.py`
- `task4_actor_attestation_v1.py`
- `task4_authority_barrier_v1.py`
- `task4_custody_store_v1.py`
- `task4_publication_guard_v1.py`
- `task4_registry_adapter_v1.py`
- `task4_requirement_policy_v1.py`

Strict schemas and focused/hostile/performance/replay/publication/terminal-accounting/workflow-policy tests are already present on PR #404. Do not rebuild them from scratch.

## Preserved RED defects already found and repaired

Do not repeat these discoveries as new work:

- initial missing interfaces: `38938697657`
- terminal-accounting hole: `38943608912`
- campaign schema drift: `38944319232`
- incomplete/aliasable C1-C9 vocabulary: `38944836349`
- signer accepted without actor-action attestation: `38945592644`
- caller self-asserted actor/process authority context: `38946266116`

A future reviewer must keep these as historical failure evidence, not rewrite the lane as initially green.

## Historical work not to redo

Use PR #322 no-repeat index for exact details. Already audited/repaired history includes:

- authenticated population/support census and split authority, PR #349;
- G8/G6/G9-S1-S2/R1/G2/G7/R4-C6-C4/C4->C6/G12/system-battery target-discovery lineages;
- Task 0-3 rejection/repair/acceptance histories;
- canonicalization/custody substrate;
- optimizer/EMA/checkpoint/RNG/packing/FULL104 support mechanics;
- observation-operator scientific framing and basis-stability/evidence-depth design;
- FULL104/dimension-authority historical planning and blockers;
- chromVAR/limma motif-program evidence-layer design.

Use classifications:

`ALREADY_AUDITED | SUPERSEDED | OPEN | CHANGED_INPUT_REQUIRES_REQUALIFICATION`

## Local/private artifacts

Read the PR #322 V2 local artifact manifest before use. The expression/calibration/checkpoint/NPZ archives are hash-custodied rather than copied into Git. The two small historical text notes are already imported into Git. Verify SHA-256 before use; presence is not authority.

Protected validation/oracle values remain closed.

## Known inherited CI environment issue

Three inherited frozen workflows can fail before their intended assertions because they install pytest without NumPy while importing `canonical_v1.py`: Task 0 migration audit, Task 0 B1-B5 verification and Task 3 B6 workflow policy. These are separately classified environment defects. Do not mislabel them as Task 4 authority regressions and do not silently mutate frozen Task 0-3 authority code to fix them.

## Immediate successor mission

1. inspect live PR #404 head against the custodied `b31371d...` snapshot;
2. if code/test bytes changed after `cfa3b7c4...`, classify the delta and run the required Task 4/inherited regressions on one exact immutable head;
3. pin the final exact Task 4 candidate branch only after a fresh exact-head Task 4 GREEN run;
4. obtain independent hostile review using `UNIFIED_TASK4_CANDIDATE_REVIEW_PACKET_20261016.md`;
5. do not create target/representation/training/Stage4 authority merely from a Task 4 mechanics acceptance.

Every substantive session must update PR #322 durable custody and PR #323 navigation with exact heads, runs, failures, repairs, data/result identities and no-repeat classification.
