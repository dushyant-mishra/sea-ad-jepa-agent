# JEPA project lane — detailed successor handoff — 2026-10-17

Status: `SUCCESSOR_READY__READ_HISTORY_FIRST__NO_REPEAT`

This handoff is for a new agent taking over the Target Discovery -> unified qualification -> downstream JEPA lane. It is intentionally detailed so the successor can continue from current work rather than restart historical audits, reconstruct authority, or rediscover already-known failure modes.

## 1. Read these first, in this exact order

1. This file.
2. PR #322: `docs/agent/JEPA_LANE_AUDIT_AND_CUSTODY_SNAPSHOT_20261017.md`.
3. PR #322: `docs/agent/JEPA_LANE_CURRENT_CUSTODY_NO_REPEAT_20261016.md`.
4. PR #322: `results/target_discovery/unified_qualification_v1/JEPA_LANE_AUDIT_SNAPSHOT_V3_20261017.json`.
5. PR #322: `results/target_discovery/unified_qualification_v1/LOCAL_ARTIFACT_CUSTODY_MANIFEST_V3_20261017.json`.
6. PR #404: `docs/agent/UNIFIED_TASK4_EXECUTION_LEDGER_20261016.md`.
7. PR #404: `docs/agent/UNIFIED_TASK4_CANDIDATE_REVIEW_PACKET_20261016.md`.
8. PR #404: `results/target_discovery/unified_qualification_v1/UNIFIED_TASK4_CANDIDATE_STATE_V1.json` and `TASK4_ATTACK_MATRIX_V1.json`.
9. Only then use `docs/agent/JEPA_HISTORICAL_NO_REPEAT_INDEX_20261015.md` for deeper historical archaeology.

Do not begin with branch archaeology. The audit branch already did it.

## 2. Current authority — do not reinterpret

Accepted/frozen exact code:

- Task 0: `e37a22b8059c0a4a93a789a8ca916fb7acde9fe3`
- Task 1: `799d2e235901dfad9ce3b305c767a1c989e362f6`
- Task 2: `c7dfff1cee608e4a101855d42cf0af08491c2aaf`
- Task 3: `117dd51dea827e734b299982da93991b934bdc8f`

Task 3 freeze branch: `freeze/unified-task3-accepted-117dd51d-20261016`.

Task 3 independent acceptance is on PR #401 / Macha review head `c33f2bd2` with verdict `ACCEPT_UNIFIED_TASK3`.

Global authority is still:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

Do not infer any additional authority from Task 4 code, green CI, local artifacts, historical checkpoints or diagnostic readiness functions.

## 3. Why Task 3 history matters

Task 3 went through multiple independent hostile reviews. Keep all rejected candidates because each exposed a different class of authority bug.

- `851544e8dc2a3881193a4d5bbcf07933e1d61149`: original B1-B6 failure set.
- `68df31584d17f91da2635cdf8e03bbe93695f9d1`: rejected after N1 Task-2 validator bypass, N2 declared-KTQ route and remaining B3/B5 defects.
- `d9e58a18da5bcfc95d9b9e7484e5686d403c55d4`: rejected because revoked/declared units and nested validator paths could still reach RRR.
- `117dd51dea827e734b299982da93991b934bdc8f`: accepted.

Permanent lesson: when one gate is repaired, attack every other route to the same state: construction, reload, fork, replay, legacy route, nested prerequisite, revocation, supersession and campaign restart.

Task 4 inherits C1-C9, R4 cross-process persistence, R7 authenticated actor identity, and R5 pooled donor-level claim scope.

## 4. Task 4: exact current state

### Design/plan

PR #402, branch `design/unified-task4-c1-c9-amendment-20261016`, head `979833a51391248f568426f508cce1d01e3e32a5`.

Contains the approved C1-C9 binding amendment and the 11-task implementation plan.

### RED history

PR #403, branch `work/unified-task4-red-20261016`, head `c5e40b04c6dcbb07d3a92edc9f9677ceb7f584ff`.

First valid RED: run `38938697657`, job `117100597615`, read-only token, 14 intentional failures. Preserve this evidence.

Additional REDs already found and repaired:

- terminal-accounting gap: `38943608912` / `117117078319`;
- schema drift: `38944319232` / `117119472176`;
- incomplete/aliasable C1-C9 vocabulary: `38944836349` / `117121219990`;
- signer object without actor-action attestation: `38945592644` / `117123776998`;
- caller self-asserted actor/process context: `38946266116` / `117126036930`.

Do not delete, squash away or restate these as if the implementation was always correct.

### Implementation candidate

PR #404, branch `work/unified-task4-impl-20261016`.

Live head at handoff: `b31371d62f3270c965d321e61c35898ca6be3721`.

Last fully verified code/test head: `cfa3b7c4f92a1569639b6733a6956c516d7f4cf4`.

The live head is four commits ahead of the verified head, and the delta is documentation/result metadata only. It changes no script, schema, test, workflow or frozen Task 0-3 production byte.

Last exact code/test verification at `cfa3b7c4...`:

- Task 4 `38946411134` / `117126540739`: focused Task 4 PASS, projected 100k replay PASS, full unified PASS.
- Task 1 `38946411299`: PASS.
- Task 2 `38946411331`: PASS.
- Task 3 registry `38946411463`: PASS.
- unified synthetic integration `38946411400`: PASS.

Current classification:

`CANDIDATE_ONLY__INDEPENDENT_EXACT_HEAD_REVIEW_REQUIRED`

Final authority remains fail-closed because genuine external C5-C9 authority context has not been wired.

## 5. Task 4 implementation already exists — do not rebuild

Review/repair these exact modules rather than writing replacements from the design:

- `challenge_custody_v1.py`
- `task4_actor_attestation_v1.py`
- `task4_authority_barrier_v1.py`
- `task4_custody_store_v1.py`
- `task4_publication_guard_v1.py`
- `task4_registry_adapter_v1.py`
- `task4_requirement_policy_v1.py`

Schemas already exist for campaign, evidence package, sealed challenge, custody receipt, reveal, realization set, exposure ledger, method-output freeze, actor-action attestation and persistent custody head.

Test families already cover focused custody, hostile custody, actor attestations, C1-C9 barrier, persistent custody, replay mutation, requirement policy, publication guard, schema contracts, terminal accounting, attack matrix and performance/replay.

Task 4 design goals already implemented include persistent append-only custody, expected-head anchoring, replay/rechain/truncation refusal, actor-action attestation, closed issuer law, exact C1-C9 vocabulary, finite sealed challenge lifecycle, exposure accounting, immutable method-output freeze, reveal-after-freeze, terminal accounting and NO-ECHO scanning.

## 6. Historical Target Discovery / ETL / scientific work already audited

Do not redo this work unless exact inputs changed or a concrete defect is found.

Population/support authority is custodied at PR #349 / exact head `1ab453e5cb60efb209a8eee2aecb61c5ea0fbfc7`; population registry SHA-256 `50b29d7e1137c5a457fd0b528580030dedfbeff1b809e2b426f8f640ae38486d`. The authenticated census is 6,351,753 rows / 149 donors / 42 observation operators / 3 sources / 2,028 donor×operator strata, with 104 reader-fit / 22 reader-validation / 23 reader-oracle donors.

Repaired TD units already handled: G8 #364; G6 #365; geometry G9/S1/S2 #366; R1 #367; G2 #368; G7 #362; R4/C6/C4 #358; C4->C6 firewall #351; G12 #360; system battery #369. PRs #375-#378 are superseded duplicates.

Historical mechanics already audited include optimizer/gradient flow, teacher no-grad, optimizer-before-EMA, invalid-update behavior, Adam moments, checkpoints/restart, identity RNG, packing/scientific weights, FULL104 support/normalization, donor-primary target, p/q separation, masking/context, anti-carryover and one-update mechanics. Treat all of this as mechanics evidence, not biological proof.

Historical scientific framing already retained:

- technology/assay is an observation operator, not biological identity;
- donor holdout, matrix holdout, dataset transfer and technology transfer are distinct;
- basis/subspace stability and evidence-response vs measurement-depth uncertainty are separate questions;
- hierarchical dataset -> donor -> cell sampling matters;
- query/target identity shortcut risk remains a real scientific control issue;
- chromVAR/limma motif-program accessibility is a distinct evidence channel but shared-source ATAC analyses cannot be double-counted as independent replication;
- SCENIC+, peak DA, footprinting, expression, perturbation and external datasets must keep source dependence explicit.

## 7. Local/private artifacts

Large binaries are intentionally not committed to Git. Exact names, byte sizes and SHA-256 are in PR #322 `LOCAL_ARTIFACT_CUSTODY_MANIFEST_V3_20261017.json`.

The set includes the split foundation discovery expression archive, supplied part-hash manifest, calibration bundle, expression archive, checkpoint bundles, NPZ artifact and focused Task 3 pytest artifact. Two small historical text notes are already imported into Git under `docs/agent/historical_imports/`.

Always verify hash before use and then recover semantic provenance. Presence of bytes is not evidence of current scientific authority.

## 8. Known inherited CI defect

Three inherited/frozen workflow runs can fail before assertions because NumPy is not installed before importing `canonical_v1.py`:

- Task 0 migration audit `38946411227`;
- Task 0 B1-B5 verification `38946411361`;
- Task 3 B6 workflow policy `38946411617`.

Do not call these Task 4 failures. Do not silently repair frozen authority bytes. If a future workflow-only repair is needed, isolate it prospectively and preserve the frozen accepted code identity.

## 9. Immediate next action items

### A. Reconcile and pin final Task 4 candidate

1. Confirm live PR #404 still equals or descends from `b31371d62f3270c965d321e61c35898ca6be3721`.
2. If any script/test/schema/workflow bytes changed after this handoff, classify the delta before proceeding.
3. Run focused Task 4 + projected 100k replay + full unified regression on one exact candidate head.
4. Run inherited Task 1, Task 2, Task 3 registry and unified synthetic integration against that same code/test head.
5. Only after exact-head GREEN, create an immutable candidate branch and bind the candidate-state JSON to that SHA.

### B. Independent hostile Task 4 review

Review the exact pinned candidate without modifying it. Attacks must include:

- all sibling routes to KTQ/RRR/HE and later states;
- restart/reload/fork/replay/rechain/truncation/stale-head routes;
- legacy registry aliases/import paths;
- cosmetic restriction changes, reordering and target forks;
- nested prerequisite revocation and validator/issuer substitution;
- actor-name / credential substitution and caller-created signer objects;
- caller self-asserted process/policy/status context;
- exposure, reveal, frozen-output and campaign-terminal mutation;
- missing terminal outcomes;
- NO-ECHO leakage in text, logs, artifacts, paths and binary material;
- Task 0-3 byte preservation.

The reviewer must return explicit ACCEPT or REJECT bound to the exact SHA. Review attacks belong on a separate review branch.

### C. If Task 4 is rejected

Preserve the rejection, add the hostile probe as failing tests first, repair only the identified authority/custody defect, run focused + inherited regressions, then request a narrow independent re-review. Do not rewrite the rejected evidence away.

### D. If Task 4 is accepted

Freeze the exact accepted Task 4 bytes and update PR #322 and PR #323. Acceptance of Task 4 means custody/mechanics are accepted; it still does not select a biological target, representation, Stage 4 execution or training authority.

The next scientific/downstream phase must separately decide which qualified target/representation evidence is actually strong enough, using the multi-layer evidence/dependency framework rather than a naive additive score.

## 10. Scientific next-stage priorities after Task 4 mechanics acceptance

These are planning priorities, not current authority:

1. Formalize the evidence-dependency graph so shared-source ATAC analyses do not receive false independence credit.
2. Separate within-source analytical convergence, cross-assay convergence, cross-dataset replication, perturbational/causal evidence and external replication.
3. Keep contradiction, missingness, unsupported and unresolved as distinct states; never favorable-zero-fill missing evidence.
4. Revisit teacher/target construction with the correct asymmetry: teacher constructs a measured target from richer evidence; student predicts it from allowed less-rich evidence. A second predictor is not a teacher.
5. Include query-identity shortcut comparators: identity-only/shared/fixed/stop-grad/shuffle controls.
6. Preserve donor as the biological replicate for donor-level inference; do not use cells as independent replicates.
7. Use motif-family language for chromVAR by default; chromVAR alone is not direct TF binding or causality.
8. Require target adjudication to meet minimum evidence-channel classes, not only a scalar score.

## 11. Operating protocol for the next agent

Before doing new work, classify it as:

`ALREADY_AUDITED` / `SUPERSEDED` / `OPEN` / `CHANGED_INPUT_REQUIRES_REQUALIFICATION`.

For every new authority boundary use:

history assimilation -> self-audit -> RED -> minimal repair -> focused regression -> inherited regression -> hostile sibling-route audit -> exact-head independent review.

Never mix mechanics evidence with biological authority. Never let one source failure average away. Never treat multiple methods on the same ATAC observations as multiple independent datasets. Keep rejected candidates and failed attacks as permanent evidence.

Update PR #322 for durable audit/custody and PR #323 for successor navigation at each major gate transition.
