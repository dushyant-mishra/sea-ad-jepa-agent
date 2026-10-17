# JEPA project lane — detailed successor handoff V4 — 2026-10-17

Status: `SUCCESSOR_READY__TASK3_FROZEN__TASK4_SUCCESSOR5_REPAIR_REQUIRED__READ_HISTORY_FIRST__NO_REPEAT`

This is the current operational handoff for a new agent taking over the JEPA Target Discovery -> unified qualification -> downstream lane. Earlier handoffs are historical snapshots. The purpose of this file is to let the successor continue immediately without repeating broad audits, losing rejection evidence, or mistaking mechanical readiness for biological authority.

## 1. Start here — exact read order

1. This file.
2. `results/target_discovery/unified_qualification_v1/JEPA_SUCCESSOR_POINTER_V4_20261017.json`.
3. PR #322 `docs/agent/JEPA_LANE_AUDIT_AND_CUSTODY_SNAPSHOT_V4_20261017.md`.
4. PR #322 `results/target_discovery/unified_qualification_v1/JEPA_LANE_AUDIT_SNAPSHOT_V4_20261017.json`.
5. PR #322 `results/target_discovery/unified_qualification_v1/TASK4_HOSTILE_REVIEW_LINEAGE_INDEX_V1_20261017.json`.
6. PR #322 `results/target_discovery/unified_qualification_v1/LOCAL_ARTIFACT_CUSTODY_MANIFEST_V4_20261017.json`.
7. PR #322 `docs/agent/JEPA_LANE_CURRENT_CUSTODY_NO_REPEAT_20261016.md`.
8. PR #322 `docs/agent/JEPA_HISTORICAL_NO_REPEAT_INDEX_20261015.md` only when deeper historical context is necessary.
9. PR #402 for approved Task 4 architecture/plan.
10. PRs #403-#417 for Task 4 RED -> implementation -> hostile-review -> repair chronology.

Do not begin with a repository-wide historical audit. That work is already custodied.

## 2. Authority that is settled

Accepted/frozen exact code identities:

- Task 0: `e37a22b8059c0a4a93a789a8ca916fb7acde9fe3`
- Task 1: `799d2e235901dfad9ce3b305c767a1c989e362f6`
- Task 2: `c7dfff1cee608e4a101855d42cf0af08491c2aaf`
- Task 3: `117dd51dea827e734b299982da93991b934bdc8f`

Task 3 freeze branch: `freeze/unified-task3-accepted-117dd51d-20261016`.
Task 3 independent acceptance: PR #401, Macha review head `c33f2bd2`, verdict `ACCEPT_UNIFIED_TASK3`.

Do not modify frozen Task 0-3 production code while repairing Task 4.

Global authority is still exactly:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

No Task 4 result, checkpoint, local binary, historical target result or diagnostic function overrides that string.

## 3. Task 3 history — assimilate, do not repeat

Rejected predecessors are permanent evidence:

- `851544e8dc2a3881193a4d5bbcf07933e1d61149`: original B1-B6 authority/custody failure set.
- `68df31584d17f91da2635cdf8e03bbe93695f9d1`: Task 2 binding bypass N1, declared-KTQ N2 and remaining B3/B5 defects.
- `d9e58a18da5bcfc95d9b9e7484e5686d403c55d4`: remaining N2/nested validator B3-V/B5-F routes.
- `117dd51dea827e734b299982da93991b934bdc8f`: accepted.

Task 4 inherits C1-C9, R4 cross-process persistence, R7 authenticated actor identity and R5 pooled donor-level claim scope.

Permanent audit lesson: when one call/gate is repaired, attack every alternative route to the same state: direct construction, restart, reload, fork, replay, rechain, legacy path, nested prerequisite, revocation, supersession and state mutation.

## 4. Task 4 — current state, corrected for latest hostile review

### Design and implementation plan

PR #402, exact plan head `979833a51391248f568426f508cce1d01e3e32a5`.

Do not redesign Task 4 from scratch unless a hostile finding demonstrates the architecture itself is wrong. The approved model already requires persistent custody, external authority separation, actor attestation, closed issuer law, sealed finite challenge lifecycle, immutable output freeze, reveal discipline, terminal accounting, replay protection and RED-first hostile review.

### First RED

PR #403; valid RED run `38938697657`, job `117100597615`, read-only token, 14 intentional failures before Task 4 modules existed.

### Existing implementation

PR #404 contains the core Task 4 scripts/schemas/tests/results. Review current bytes; do not rebuild them from the plan.

Key scripts:

- `scripts/v5/td_unified/challenge_custody_v1.py`
- `scripts/v5/td_unified/task4_actor_attestation_v1.py`
- `scripts/v5/td_unified/task4_authority_barrier_v1.py`
- `scripts/v5/td_unified/task4_custody_store_v1.py`
- `scripts/v5/td_unified/task4_publication_guard_v1.py`
- `scripts/v5/td_unified/task4_registry_adapter_v1.py`
- `scripts/v5/td_unified/task4_requirement_policy_v1.py`

### Rejected Task 4 candidates — do not rediscover these defects

1. `b31371d62f3270c965d321e61c35898ca6be3721` — caller-created trust objects could self-mint the trust graph. Reviews #405/#412; repair #406.
2. `c537db4e7b5b916cb3ddee1872fd4afa623a9b33` — post-seal definition/realization substitution. Review #407; repair #408.
3. `b5ed724cbc6a39d4f2cd68103c5367c2cfafcff3` — advanced campaign state could be directly fabricated. Review #409; repair #410.
4. `d41720be93db27801fdac1ae62cfd608084dce25` — terminal classifications could be chosen after hidden reveal. Review #413; repair #414.
5. `56b864e2b944956746771fb5d26040835d093dd5` — mechanically green but superseded because stale predecessor review artifacts remained in the review pin.
6. `068880822bca8036e605e3c5264770ce89057fee` — successor-4, pre-attack GREEN but now rejected by PR #417 regeneration-provenance RED.

### Current blocker — this is where the new agent starts

PR #417, head `c543bd7c8b40d89db550dedad3ff5adbfbc356c0`, attacks successor-4 `068880822...`.

Valid Task 4 RED:

- run `39000234158`
- job `117301422733`
- token `Contents: read`
- focused result: `1 failed, 109 passed, 1 skipped`
- failing test: `test_replaying_preexisting_rows_is_not_deterministic_regeneration_evidence`
- exact problem: `verify_regeneration` can accept already-known sealed rows simply replayed/copied by the caller. Equality/root matching does not prove that the frozen challenge generator/code/policy/RNG contract performed deterministic regeneration.

Therefore current state is:

`TASK4_SUCCESSOR4_REJECTED_BY_REGENERATION_PROVENANCE_RED__SUCCESSOR5_REPAIR_REQUIRED__INDEPENDENT_ACCEPTANCE_ABSENT`

Do not request acceptance of `06888082...` without repairing this blocker.

## 5. Immediate next action items — execute in this order

### Action 1 — preserve the RED

Treat PR #417 as immutable review evidence. Do not repair on the review branch and do not modify the successor-4 candidate branch.

### Action 2 — cut successor-5 repair from exact `068880822...`

Create a new repair branch rooted exactly at `068880822bca8036e605e3c5264770ce89057fee`.

The current PR #417 test must exist as failing evidence before production repair.

### Action 3 — define regeneration provenance narrowly

The fix must establish *who/what regenerated*, not merely that supplied rows equal the sealed rows. Bind regeneration to the frozen generator execution contract: challenge definition identity, realization-set identity/root, generator code identity, generator policy identity, RNG identity/state/seed contract, lawful reveal state and a non-caller-self-mintable provenance/receipt boundary.

Do not convert a magic string, caller-supplied protocol object or copied receipt into authority.

### Action 4 — hostile sibling-route matrix before GREEN claim

At minimum add/retain attacks for:

- caller returns original rows unchanged;
- caller deep-copies rows with the same root;
- fake generator implements the expected interface;
- generator code SHA substituted;
- generator policy SHA substituted;
- RNG identity/state/seed substituted;
- regeneration invoked before hidden reveal;
- regeneration uses another sealed definition/root;
- stale regeneration receipt replayed into a new campaign;
- provenance object mutated or swapped after reveal;
- legitimate regeneration result reused across campaign identity/fork.

Every route must fail closed unless exact trusted provenance is satisfied.

### Action 5 — run exact-head regressions

On one exact repair head run:

1. focused Task 4 custody/hostile suites;
2. projected 100k replay qualification;
3. full `tests/v5/td_unified` Task 0-4 regression;
4. Task 1 regression;
5. Task 2 manifest/access regression;
6. Task 3 registry regression;
7. unified synthetic integration;
8. verify Task 0-3 production bytes remain identical to their frozen identities/contracts.

Inherited workflow-environment defects that fail before intended assertions due missing NumPy must be classified separately. Do not repair frozen production code to make those unrelated workflows green.

### Action 6 — self-audit before pinning

Attack all sibling routes to `REGENERATION_VERIFIED`, not only the public method just repaired. Inspect direct object construction, load/reload, campaign fork, receipt replay, stale head, alias/root substitution and legacy helper routes.

### Action 7 — immutable successor-5 candidate

Only after exact-head GREEN, pin an immutable candidate branch. Bind review packet/state JSON to that exact SHA. Do not add docs-only commits on top of the review SHA unless a new review-ready pin is made deliberately.

### Action 8 — independent exact-SHA hostile review

Review attacks belong on a separate branch. Reviewer returns explicit:

`ACCEPT_TASK4_CUSTODY_CANDIDATE` or `REJECT_TASK4_CUSTODY_CANDIDATE`

bound to the exact candidate SHA.

If rejected: preserve RED, port attack first, narrow repair, repeat.
If accepted: freeze Task 4 mechanics and update PR #322/#323. Do not interpret Task 4 acceptance as biological target/representation/training authorization.

## 6. What historical science/data work is already done

Do not restart the following unless inputs changed.

### Population/support/ETL authority

PR #349 / exact head `1ab453e5cb60efb209a8eee2aecb61c5ea0fbfc7`.
Population registry SHA-256 `50b29d7e1137c5a457fd0b528580030dedfbeff1b809e2b426f8f640ae38486d`.
Custodied census: 6,351,753 rows, 149 donors, 42 observation operators, 3 sources, 2,028 donor×operator strata; 104 reader-fit / 22 validation / 23 oracle donors.

### Repaired Target Discovery units

Already handled: G8 #364; G6 #365; G9/S1/S2 #366; R1 #367; G2 #368; G7 #362; R4/C6/C4 #358; C4->C6 firewall #351; G12 #360; system battery #369. PRs #375-#378 are superseded duplicates.

### Teacher/student and runtime mechanics

Already audited: optimizer/gradient flow, teacher no-grad, optimizer-before-EMA, invalid-update EMA blocking, Adam moments, restart/checkpoint behavior, identity RNG, packing/scientific weights, FULL104 support/normalization, donor-primary target, p/q separation, visibility/context/masking and anti-carryover. These are mechanics evidence, not biological proof.

### Scientific framing already established

- Multiple evidence layers are intentional; use convergence across partially independent evidence, not one assay as sole authority.
- RNA, peak accessibility/DA, chromVAR motif-program accessibility, footprinting, SCENIC+, expression programs, perturbation and external replication are separate claim layers.
- DA/chromVAR/footprinting/SCENIC+ that reuse the same ATAC source share dependency; do not count them as independent datasets.
- chromVAR supports motif-associated accessibility, generally motif-family language; it does not alone prove TF binding or causality.
- donor is the replicate for donor-level inference; cells are not independent donors.
- source failures do not average away; missing/conflicting/unsupported remain distinct and are never favorable-zero-filled.
- technology/assay is an observation operator, not biological identity.
- teacher must construct the target from richer assigned biological evidence; another predictor is not automatically a teacher.
- target/query identity shortcut controls remain required: identity-only/shared/fixed/stop-grad/shuffle comparators.
- actual ETL exposure/leakage history determines external-validation independence; prior viewing of a dataset does not automatically answer the question.

## 7. Local/private artifacts — do not duplicate or lose them

PR #322 V4 artifact manifest reverified all currently mounted user-provided files. Large binaries are intentionally hash-custodied instead of pushed into Git.

Includes:

- split `FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip` parts and combined archive identity;
- supplied parts SHA manifest;
- `FOUNDATION_CALIBRATION_BUNDLE_20260824.zip`;
- `expression.zip`;
- `checkpoints.zip`;
- `t1_checkpoint_u0200.zip`;
- `66e64913-959f-4a7c-bbfe-6ff906fb281d.npz`;
- imported historical Status/Repair and WSL/foundation notes.

Hash verify before use. Recover semantic provenance before interpreting any binary. Checkpoint presence is mechanics evidence only.

## 8. How to avoid duplicated work

Before touching a topic classify it:

`ALREADY_AUDITED | SUPERSEDED | OPEN | CHANGED_INPUT_REQUIRES_REQUALIFICATION`

Examples:

- re-auditing accepted Task 3 B1-B6 from scratch: `ALREADY_AUDITED`.
- using PR #400 downstream preflight based on rejected Task 3: `SUPERSEDED`.
- regeneration provenance in Task 4: `OPEN`.
- rerunning a qualification after raw reader split bytes change: `CHANGED_INPUT_REQUIRES_REQUALIFICATION`.

Only the latter two justify new substantive work.

## 9. After Task 4 mechanics eventually pass

Task 4 acceptance is not a biological decision. The next downstream/scientific work should formalize an evidence-dependency graph before selecting targets/representations:

- distinguish within-source analytical convergence from cross-assay and cross-dataset replication;
- explicitly model source dependence so ATAC-derived channels are not double-counted;
- keep perturbational/causal and external evidence separate;
- preserve contradictions rather than averaging them away;
- require minimum evidence-channel classes rather than a naive scalar total;
- revisit teacher/target construction and shortcut controls;
- only then adjudicate target/representation qualification under the frozen governance machinery.

## 10. Operating discipline

Use this sequence for every new authority surface:

`history assimilation -> self-audit -> RED -> minimal repair -> focused regression -> inherited regression -> hostile sibling-route audit -> exact-head independent review`

Keep candidate branches immutable during independent review. Keep hostile attacks separate. Never erase rejected evidence. Never allow a mechanical PASS to become a biological claim without the evidence layer that supports it.
