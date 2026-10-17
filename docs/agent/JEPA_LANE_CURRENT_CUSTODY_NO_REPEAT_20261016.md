# JEPA lane current custody + no-repeat index — 2026-10-16

Status: `DURABLE_AUDIT_CUSTODY__NON_AUTHORIZING`

Purpose: this is the current read-first index for the JEPA Target Discovery -> unified qualification -> downstream lane. It supersedes the *navigation state* in the 2026-10-15 no-repeat index but does not delete or rewrite historical rejection/audit records. A successor must use this file to avoid repeating settled audits, rebuilding already-qualified mechanics, or treating superseded evidence as current authority.

## Current authority / gate state

Frozen accepted authority:

- Task 0: `e37a22b8059c0a4a93a789a8ca916fb7acde9fe3`
- Task 1: `799d2e235901dfad9ce3b305c767a1c989e362f6`
- Task 2: `c7dfff1cee608e4a101855d42cf0af08491c2aaf`
- Task 3: `117dd51dea827e734b299982da93991b934bdc8f`
- Task 3 freeze branch: `freeze/unified-task3-accepted-117dd51d-20261016`
- Task 3 acceptance PR: #401
- independent Macha acceptance review head: `c33f2bd2`
- verdict: `ACCEPT_UNIFIED_TASK3`
- gate: `TASK3_MAY_BE_FROZEN__UNIFIED_TASK4_MAY_BEGIN_PROSPECTIVELY`

Task 4 is now prospective implementation only. It is **not accepted authority**.

Global authority remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

## Task 3 historical rejection -> repair -> acceptance lineage

Do not repeat these reviews unless the exact bytes or authority context change.

1. Rejected original Task 3 candidate `851544e8dc2a3881193a4d5bbcf07933e1d61149`, PR #392. Original blockers B1-B6 preserved in Macha review artifacts.
2. Rejected successor `68df31584d17f91da2635cdf8e03bbe93695f9d1`; review introduced critical N1 Task-2 binding and N2 declared-KTQ defects plus B3/B5 partial closures.
3. Rejected successor `d9e58a18da5bcfc95d9b9e7484e5686d403c55d4`; Task-2 binding, evidence issuers and privileged actors fixed, but N2/B5-F/nested B3-V still open.
4. Accepted exact Task 3 code `117dd51dea827e734b299982da93991b934bdc8f`; PR #401 head `2448cbcec0964e692c52a24a8b1324e2d388314e` adds only repair-ledger documentation on top.
5. Binding Task 4 carry-forward from acceptance: C1-C9 plus pooled donor-level R5 scope. R4 cross-process persistence and R7 credential identity were not declared solved by Task 3; Task 4 must satisfy them before authority-bearing stages can open.

Preserve the review lesson: after repairing a gate, attack every alternative route to the same state, not only the call originally patched.

## Task 4 design, RED and implementation custody

Design/specification PR #402:

- branch `design/unified-task4-c1-c9-amendment-20261016`
- head `979833a51391248f568426f508cce1d01e3e32a5`
- binding amendment: `docs/superpowers/specs/2026-10-16-unified-task4-c1-c9-binding-amendment.md`
- implementation plan: `docs/superpowers/plans/2026-10-16-unified-task4-sealed-custody-c1-c9-implementation.md`

RED-only PR #403:

- branch `work/unified-task4-red-20261016`
- head `c5e40b04c6dcbb07d3a92edc9f9677ceb7f584ff`
- first valid RED run `38938697657`, job `117100597615`
- result: 14 intentional failures at not-yet-existing Task 4 interfaces under `Contents: read`

Implementation PR #404:

- branch `work/unified-task4-impl-20261016`
- current observed PR head during this custody refresh: `b31371d62f3270c965d321e61c35898ca6be3721`
- last fully verified code/test head: `cfa3b7c4f92a1569639b6733a6956c516d7f4cf4`
- exact diff `cfa3b7c4... -> b31371d...` is documentation/result-only: candidate review packet, execution ledger, attack matrix metadata and candidate-state JSON.
- Task 4 run `38946411134`, job `117126540739`: focused Task 4 PASS, projected 100k replay PASS, full unified regression PASS.
- same-head regressions: Task 1 `38946411299` PASS; Task 2 `38946411331` PASS; Task 3 registry `38946411463` PASS; unified synthetic integration `38946411400` PASS.
- candidate classification: `CANDIDATE_ONLY__INDEPENDENT_EXACT_HEAD_REVIEW_REQUIRED`.
- final authority remains fail-closed because genuine external C5-C9 context evidence is not yet wired.

Preserved later REDs that found real defects and must remain part of the review story:

- terminal accounting: `38943608912` / `117117078319`
- campaign schema drift: `38944319232` / `117119472176`
- incomplete/aliasable C1-C9 vocabulary: `38944836349` / `117121219990`
- trusted signer without actor-action attestation: `38945592644` / `117123776998`
- self-asserted actor/process context: `38946266116` / `117126036930`

Inherited workflow environment failures remain separately classified, not as Task 4 authority failures: Task 0 migration audit `38946411227`, Task 0 B1-B5 verification `38946411361`, Task 3 B6 policy `38946411617`; each failed before intended assertions because NumPy was absent from that frozen workflow environment.

## Task 4 production/assets currently staged on PR #404

Scripts:

- `scripts/v5/td_unified/challenge_custody_v1.py`
- `scripts/v5/td_unified/task4_actor_attestation_v1.py`
- `scripts/v5/td_unified/task4_authority_barrier_v1.py`
- `scripts/v5/td_unified/task4_custody_store_v1.py`
- `scripts/v5/td_unified/task4_publication_guard_v1.py`
- `scripts/v5/td_unified/task4_registry_adapter_v1.py`
- `scripts/v5/td_unified/task4_requirement_policy_v1.py`

Schemas:

- `qualification_campaign_v1.json`
- `qualification_evidence_package_v1.json`
- `sealed_challenge_definition_v1.json`
- `sealed_custody_receipt_v1.json`
- `sealed_qualification_reveal_v1.json`
- `sealed_realization_set_v1.json`
- `exposure_ledger_v1.json`
- `method_output_freeze_receipt_v1.json`
- `task4_actor_action_attestation_v1.json`
- `task4_persistent_custody_head_v1.json`

Results/docs:

- `docs/agent/UNIFIED_TASK4_EXECUTION_LEDGER_20261016.md`
- `docs/agent/UNIFIED_TASK4_CANDIDATE_REVIEW_PACKET_20261016.md`
- `results/target_discovery/unified_qualification_v1/TASK4_ATTACK_MATRIX_V1.json`
- `results/target_discovery/unified_qualification_v1/UNIFIED_TASK4_CANDIDATE_STATE_V1.json`

Tests include focused custody, hostile challenge custody, actor attestation, attack matrix, authority barrier, persistent custody, performance/replay, publication guard, C1-C9 RED, registry adapter, replay mutations, requirement policy, schema contracts, terminal accounting and workflow policy suites under `tests/v5/td_unified/test_task4*.py` and `test_challenge_custody_v1*.py`.

Do not rebuild these interfaces from scratch. Review/repair exact current bytes.

## Historical scientific / ETL / target-discovery custody already settled

The prior index `docs/agent/JEPA_HISTORICAL_NO_REPEAT_INDEX_20261015.md` remains authoritative for historical detail. In particular:

- population/support authority: PR #349, exact head `1ab453e5cb60efb209a8eee2aecb61c5ea0fbfc7`; authenticated population registry SHA-256 `50b29d7e1137c5a457fd0b528580030dedfbeff1b809e2b426f8f640ae38486d`; census 6,351,753 rows / 149 donors / 42 observation operators / 3 sources / 2,028 donor×operator strata / 104 reader-fit / 22 reader-validation / 23 reader-oracle donors.
- repaired TD lineages: G8 PR #364; G6 #365; geometry G9/S1/S2 #366; R1 #367; G2 #368; G7 #362; R4/C6/C4 #358; C4->C6 firewall #351; G12 #360; system battery #369. PRs #375-#378 are superseded duplicate lineages.
- historical teacher/student mechanics: optimizer/gradient flow, teacher no-grad, optimizer-before-EMA, invalid-update EMA blocking, Adam moments, checkpoint/restart, identity RNG, packing/scientific weights, FULL104 support/normalization, donor-primary target, p/q separation, visibility/context, masking, anti-carryover and one-update mechanics are already audited as mechanics evidence.
- unresolved scientific issue retained: trainable target/query identity shortcuts require identity-only/shared/fixed/stop-grad/shuffle comparators.
- observation-operator framing, donor/technology transfer, subspace/axis stability and evidence-vs-depth uncertainty are preserved in `docs/agent/historical_imports/WSL_EXECUTION_ISSUE_AND_FOUNDATION_DESIGN_NOTES_20260824.txt`.
- FULL104/dimension-authority history is preserved in `docs/agent/historical_imports/STATUS_AND_REPAIR_PLAN_20260912.txt`; it explicitly does not establish numeric dimensions or training authority.
- chromVAR/limma motif-program design layer is preserved at `docs/agent/TD_MOTIF_PROGRAM_EVIDENCE_LAYER_CHROMVAR_LIMMA_V1_20261015.md`; it is non-authorizing and must not be double-counted as independent from shared-source ATAC evidence.

## Historical Task 0-2 audit custody

Do not repeat accepted review cycles unless bytes/context change:

- Task 0 rejected predecessor -> repaired/accepted `e37a22b...`.
- Task 1 rejected predecessor -> repaired/accepted `799d2e23...`.
- Task 2 rejected predecessor -> repaired/accepted `c7dfff1c...`.

Frozen code must not be silently repaired on downstream branches. Any inherited workflow/environment defect must be separately classified and handled prospectively without changing frozen authority bytes.

## Local/private binary custody

Large/private artifacts are hash/path-custodied, not copied into Git. Read `results/target_discovery/unified_qualification_v1/LOCAL_ARTIFACT_CUSTODY_MANIFEST_20261015.json` and the 2026-10-16 V2 manifest before use. Verify exact SHA-256 first. Presence of bytes confers no authority.

## No-repeat rules for successor agents

Classify prior work as one of `ALREADY_AUDITED`, `SUPERSEDED`, `OPEN`, or `CHANGED_INPUT_REQUIRES_REQUALIFICATION`.

A successor must:

1. read this file, the 2026-10-15 no-repeat index, the Task 4 execution ledger and current candidate-state JSON before new qualification work;
2. use existing scripts/results/receipts where the bytes and scientific question are unchanged;
3. preserve failures and rejected candidates as evidence rather than rewriting history into a clean narrative;
4. distinguish mechanics evidence from biological evidence and shared-source analyses from independent replication;
5. never use protected validation/oracle data to rescue reader-fit estimability;
6. never infer authority from file presence, CI green alone or a diagnostic readiness function;
7. run self-audit -> RED -> minimal repair -> focused regression -> inherited regression -> hostile re-audit for every new authority boundary;
8. update PR #322 (durable audit) and PR #323 (successor navigation) at each major gate change.
