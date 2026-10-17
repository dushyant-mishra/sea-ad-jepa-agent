# JEPA lane audit + custody snapshot V4 — 2026-10-17

Status: `DURABLE_AUDIT_CUSTODY__TASK3_FROZEN__TASK4_SUCCESSOR4_REJECTED_BY_HOSTILE_RED__NO_REPEAT`

This is the current durable audit/custody entrypoint for the JEPA Target Discovery -> unified qualification -> downstream lane. Earlier snapshots remain historical evidence. Do not overwrite or reinterpret them as current state.

## 1. Read-first order

1. This file.
2. `results/target_discovery/unified_qualification_v1/JEPA_LANE_AUDIT_SNAPSHOT_V4_20261017.json`.
3. `results/target_discovery/unified_qualification_v1/TASK4_HOSTILE_REVIEW_LINEAGE_INDEX_V1_20261017.json`.
4. `results/target_discovery/unified_qualification_v1/LOCAL_ARTIFACT_CUSTODY_MANIFEST_V4_20261017.json`.
5. `docs/agent/JEPA_LANE_CURRENT_CUSTODY_NO_REPEAT_20261016.md`.
6. `docs/agent/JEPA_HISTORICAL_NO_REPEAT_INDEX_20261015.md`.
7. `results/target_discovery/unified_qualification_v1/INDEPENDENT_REVIEW_CUSTODY_INDEX_20261015.json`.
8. `docs/agent/TASK3_REJECTED_LINEAGE_CUSTODY_HAZARDS_20261015.md`.
9. `docs/agent/historical_imports/` and `docs/agent/TD_MOTIF_PROGRAM_EVIDENCE_LAYER_CHROMVAR_LIMMA_V1_20261015.md`.
10. PRs #402-#417 for the exact Task 4 design, RED, implementation, hostile-review and repair lineage.

Do not restart branch archaeology before reading these custody surfaces.

## 2. Frozen accepted authority

Exact accepted/frozen code identities:

- Task 0: `e37a22b8059c0a4a93a789a8ca916fb7acde9fe3`
- Task 1: `799d2e235901dfad9ce3b305c767a1c989e362f6`
- Task 2: `c7dfff1cee608e4a101855d42cf0af08491c2aaf`
- Task 3: `117dd51dea827e734b299982da93991b934bdc8f`

Task 3 freeze branch: `freeze/unified-task3-accepted-117dd51d-20261016`.
Task 3 acceptance: PR #401, independent review head `c33f2bd2`, verdict `ACCEPT_UNIFIED_TASK3`.

Global authority remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

Task 4 remains custody/mechanics only. Even a future Task 4 mechanical ACCEPT cannot establish biological truth or training authority.

## 3. Task 3 no-repeat rejection lineage

Preserve every rejected predecessor; each exposed a distinct authority class:

- `851544e8dc2a3881193a4d5bbcf07933e1d61149`: original B1-B6 rejection.
- `68df31584d17f91da2635cdf8e03bbe93695f9d1`: Task 2 binding bypass N1, declared-KTQ N2 and partial B3/B5 defects.
- `d9e58a18da5bcfc95d9b9e7484e5686d403c55d4`: remaining N2/nested B3-V/B5-F authority routes.
- `117dd51dea827e734b299982da93991b934bdc8f`: accepted exact code.

Binding Task 3 carry-forward into Task 4: C1-C9, R4 persistence, R7 authenticated actor identity and R5 pooled-donor claim scope. Permanent review lesson: after repairing one gate, attack every sibling route to the same authority state.

## 4. Task 4 chronology and current state

### Design / plan

PR #402, head `979833a51391248f568426f508cce1d01e3e32a5`:

- `docs/superpowers/specs/2026-10-16-unified-task4-c1-c9-binding-amendment.md`
- `docs/superpowers/plans/2026-10-16-unified-task4-sealed-custody-c1-c9-implementation.md`

### Initial RED

PR #403, head `c5e40b04c6dcbb07d3a92edc9f9677ceb7f584ff`.
Valid first RED: run `38938697657`, job `117100597615`, read-only token, 14 intentional failures at not-yet-existing Task 4 interfaces.

### Original implementation lineage

PR #404 contains the prospective implementation ledger, scripts, schemas, tests and result records. The original candidate `b31371d62f3270c965d321e61c35898ca6be3721` is permanently rejected; do not use it as a current candidate.

### Hostile review / repair lineage

1. `b31371d62f3270c965d321e61c35898ca6be3721` — REJECTED.
   - Finding: caller-self-minted trust graph / caller-created verifier-signer-publisher policy objects could manufacture apparent authority.
   - Review: PR #405 and PR #412.
   - Repair: PR #406.

2. `c537db4e7b5b916cb3ddee1872fd4afa623a9b33` — REJECTED.
   - Finding: post-seal challenge definition / realization-set substitution.
   - Review: PR #407.
   - Repair: PR #408.

3. `b5ed724cbc6a39d4f2cd68103c5367c2cfafcff3` — REJECTED.
   - Finding: caller-fabricable advanced `QualificationCampaign` state could bypass lawful lifecycle transitions.
   - Review: PR #409.
   - Repair: PR #410.

4. `d41720be93db27801fdac1ae62cfd608084dce25` — REJECTED.
   - Finding: hidden qualification material could be revealed before exact terminal exposure accounting was frozen, allowing post-reveal terminal classification.
   - Review: PR #413.
   - Repair: PR #414.

5. `56b864e2b944956746771fb5d26040835d093dd5` — mechanically green but superseded review pin because stale predecessor review artifacts remained in the immutable branch.
   - Review surface: PR #415.

6. `068880822bca8036e605e3c5264770ce89057fee` — successor-4 review-ready candidate, now REJECTED/BLOCKED by new hostile RED.
   - Review surface: PR #416.
   - Exact source-head GREEN evidence before the new attack: Task 4 `39000088264` / `117300978493` = 109 passed, 1 skipped focused; projected 100k replay PASS; full unified 300 passed, 1 skipped; Task 2 `39000088288` PASS; Task 3 `39000088311` PASS; synthetic integration `39000088325` PASS.
   - New hostile review: PR #417, head `c543bd7c8b40d89db550dedad3ff5adbfbc356c0`.
   - Valid RED: Task 4 run `39000234158`, job `117301422733`, read-only token; focused result `1 failed, 109 passed, 1 skipped`.
   - Exact failing attack: `test_replaying_preexisting_rows_is_not_deterministic_regeneration_evidence`.
   - Failure: copied already-known sealed realization rows can satisfy `REGENERATION_VERIFIED`; the implementation does not prove that the frozen generator/code/policy/RNG contract actually regenerated the rows.

Current Task 4 state is therefore:

`TASK4_SUCCESSOR4_REJECTED_BY_REGENERATION_PROVENANCE_RED__SUCCESSOR5_REPAIR_REQUIRED__INDEPENDENT_ACCEPTANCE_ABSENT`

Do not call `06888082...` accepted merely because its pre-attack source-head tests were green.

## 5. Exact next Task 4 repair scope

Preserve PR #417 as immutable RED evidence. Build a new successor repair from exact `068880822bca8036e605e3c5264770ce89057fee`; do not patch the review branch or immutable candidate.

The repair must make deterministic regeneration provenance distinguishable from caller-supplied equality/copying. At minimum, attack and bind:

- caller echoes the original realization rows;
- caller copies rows into a fresh object with the same root;
- caller supplies a fake generator implementing the expected interface;
- generator code identity substitution;
- generator policy identity substitution;
- RNG identity/state substitution;
- regeneration attempted before lawful reveal;
- regeneration against a different sealed definition or realization root;
- replay/stale regeneration receipt;
- mutation of claimed generator provenance after reveal.

Write/retain failing tests first. Implement the narrowest authority-safe repair. Then run focused Task 4, projected 100k replay, full unified Task 0-4, Task 1/2/3 regressions and unified synthetic integration on one exact head. Pin a successor-5 immutable candidate only after exact-head GREEN. Independent exact-SHA ACCEPT/REJECT remains mandatory.

## 6. Task 4 implementation inventory already present

Do not rebuild these from scratch. Review/repair current bytes:

- `scripts/v5/td_unified/challenge_custody_v1.py`
- `scripts/v5/td_unified/task4_actor_attestation_v1.py`
- `scripts/v5/td_unified/task4_authority_barrier_v1.py`
- `scripts/v5/td_unified/task4_custody_store_v1.py`
- `scripts/v5/td_unified/task4_publication_guard_v1.py`
- `scripts/v5/td_unified/task4_registry_adapter_v1.py`
- `scripts/v5/td_unified/task4_requirement_policy_v1.py`

Schemas and tests already cover campaign/evidence/sealed challenge/custody/reveal/realization/exposure/output freeze/actor attestation/persistent head; focused hostile custody; C1-C9; replay/performance; publication guard; terminal accounting; schema contracts and workflow policy.

## 7. Historical Target Discovery / ETL / science already custodied

Do not repeat broad audits unless exact input bytes or contracts changed, or a concrete uncovered defect exists.

- Population/support authority: PR #349 / `1ab453e5cb60efb209a8eee2aecb61c5ea0fbfc7`; registry SHA-256 `50b29d7e1137c5a457fd0b528580030dedfbeff1b809e2b426f8f640ae38486d`; 6,351,753 rows / 149 donors / 42 observation operators / 3 sources / 2,028 donor×operator strata / 104 reader-fit / 22 reader-validation / 23 reader-oracle donors.
- Repaired TD units: G8 #364; G6 #365; G9/S1/S2 #366; R1 #367; G2 #368; G7 #362; R4/C6/C4 #358; C4->C6 firewall #351; G12 #360; system battery #369. PRs #375-#378 are superseded duplicates.
- Historical mechanics already audited: optimizer/gradient flow; teacher no-grad; optimizer-before-EMA; invalid-update EMA behavior; Adam moments; checkpoints/restart; identity RNG; packing/scientific weights; FULL104 support/normalization; donor-primary target; p/q separation; masking/context; anti-carryover; one-update mechanics.
- Technology/assay is an observation operator, not biological identity. Donor holdout, matrix holdout, dataset transfer and technology transfer are distinct.
- Query/target identity shortcut risk remains a scientific control issue; use identity-only/shared/fixed/stop-grad/shuffle comparators.
- chromVAR/limma motif-program accessibility is a distinct non-authorizing evidence layer. Peak DA/chromVAR/footprinting/SCENIC+ derived from the same ATAC source are not four independent datasets.
- Measurement evidence, mechanics evidence and biological authority remain separate. Source failures do not average away; no favorable zero-fill.

## 8. Data / artifact custody

Large/private binaries are intentionally hash-custodied rather than duplicated into Git. V4 re-verifies all locally available user-provided artifacts. Exact hashes/sizes are in `LOCAL_ARTIFACT_CUSTODY_MANIFEST_V4_20261017.json`.

Small historical chat-only notes are already imported:

- `docs/agent/historical_imports/WSL_EXECUTION_ISSUE_AND_FOUNDATION_DESIGN_NOTES_20260824.txt`
- `docs/agent/historical_imports/STATUS_AND_REPAIR_PLAN_20260912.txt`

Never infer scientific authority from file presence. Verify hashes and recover semantic provenance before use.

## 9. Known inherited CI/environment defects

Some frozen/inherited workflows fail before intended assertions because NumPy is absent when `canonical_v1.py` imports. Keep these separate from Task 4 scientific/authority findings; do not repair them by changing frozen Task 0-3 production code.

## 10. Permanent no-repeat operating rule

Before starting work classify it as:

`ALREADY_AUDITED | SUPERSEDED | OPEN | CHANGED_INPUT_REQUIRES_REQUALIFICATION`

Only `OPEN` or `CHANGED_INPUT_REQUIRES_REQUALIFICATION` warrants new audit/implementation.

For every new authority boundary:

`assimilate history -> self-audit -> RED -> minimal repair -> focused regression -> inherited regression -> hostile sibling-route audit -> exact-head independent review`

Preserve every rejection and RED. Never convert green mechanics into biological authority.
