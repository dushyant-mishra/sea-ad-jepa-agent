# Macha Task 0 final independent review packet V2 — 2026-10-14

Status: `CONTROLLING_REVIEW_PACKET__ROLE_INDEPENDENCE_CORRECTED`

Supersedes V1 for current instructions. V1 remains historical provenance.

## Purpose

Provide the exact current instructions for Macha after old PR #356 Tasks 1–2 were implemented by Macha, independently rerun by the controller, and incorporated into Task 0 custody.

Global authority remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

No candidate outcomes, `reader_validation`, or `reader_oracle` may be opened for this review.

## Critical role split

Macha authored/implemented old synthetic Tasks 1–2 at exact head:

`ff597faf2182522a320ec5322f8db9b67c9c6094`

Therefore Macha cannot be the independent reviewer/qualifier of those same implementation bytes.

For old Tasks 1–2, Macha may:

- attest exact provenance and design intent;
- point out any defect he knows about;
- reproduce behavior if asked;
- challenge the controller's migration interpretation.

Those are author/provenance inputs, not independent qualification.

Independent controller verification of the old Task 1–2 bytes is already represented by PR #382:

- focused run `38644641042`, job `116128364543`: `332 passed in 8.94s`;
- inherited run `38644640881`: success.

Macha's independent-review target is the controller-authored Task 0 custody/consolidation and its treatment of the historical substrate.

## 1. Exact Task 0 object to review independently

PR #381

Exact head:
`c80d7398b41f10208ec1622bc52599383b940be6`

Base:
`9328f1c00faee8a0ebf1910d412ea129bab566be`

Exact-head GREEN:

- focused run `38645994312`, job `116132861396`: success, `29 passed in 0.07s`;
- inherited `unified synthetic integration v1` run `38645994388`: success.

Read first:

1. `results/target_discovery/unified_qualification_v1/PREMERGER_ARTIFACT_MIGRATION_MATRIX_V1.json`
2. `results/target_discovery/unified_qualification_v1/PREMERGER_MIXED_ARTIFACT_DECOMPOSITION_V1.json`
3. `results/target_discovery/unified_qualification_v1/PREMERGER_MACHA_DUAL_STREAM_CUSTODY_V1.json`
4. `results/target_discovery/unified_qualification_v1/PREMERGER_UNRESOLVED_WORK_LEDGER_V1.json`
5. `results/target_discovery/unified_qualification_v1/PREMERGER_MERGED_CUSTODY_COMPLETENESS_V1.json`
6. `scripts/v5/td_unified/premerger_migration_task0.py`
7. `scripts/v5/td_unified/premerger_custody_completeness_v1.py`
8. `tests/v5/td_unified/test_premerger_migration_task0.py`
9. `tests/v5/td_unified/test_premerger_custody_completeness_v1.py`
10. `docs/agent/UNIFIED_TD_PREMERGER_REAUDIT_COMPLETENESS_ADDENDUM_20261014.md`
11. `docs/agent/MACHA_ROLE_INDEPENDENCE_CORRECTION_V1_20261014.md`

## 2. What Macha must independently adjudicate

### F1

Confirm mixed historical parents are decomposed into machine-readable children with independently classified migration/authority states. Prose-only decomposition must not satisfy the validator.

### F2

Confirm `exact_identity_available` is mandatory/boolean, deletion fails closed, and available identity requires exact source/artifact binding without inventing identity for unavailable bytes.

### F5–F9

Confirm Task 0 preserves without promotion:

- F5: old Tasks 1–2 at exact Macha-authored head with controller verification; old Tasks 3–4 stopped after merger with requirements migrating only; old Tasks 5–12 stopped independently;
- F6: `SUBSPACE_ONLY`, technology invariance not qualified, partial matrix/source-acquisition limits;
- F7: multimodal/SCENIC+/ATAC same-vs-separate nucleus and independent-measurement boundaries;
- F8: runtime safety is post-science training prerequisite, not target authority;
- F9: FULL104 denominator/source channel, evidence burden, estimability/zero-fill and metric-blindness obligations.

### Migration treatment of Macha's old Tasks 1–2

Macha should review the **controller's proposed migration classification**, not claim independent qualification of his own code.

Controller proposal:

- old Task 1 → `ADAPT_AND_WRAP__DIRECT_REUSE_CANDIDATE_FOR_CANONICAL_PRIMITIVES`;
- old Task 2 → `ADAPT_AND_WRAP__SEALED_CUSTODY_RNG_SUBSTRATE`.

Challenge whether these destinations are scientifically/governance-correct, whether anything important is missing, and whether any old Task 1–2 behavior should instead be test-only or rejected.

Do not claim that this review makes the Task 1–2 implementation independently qualified.

### Stop law

Confirm explicitly:

- old Task 3: `STOPPED_AFTER_MERGER__REQUIREMENTS_MIGRATE_ONLY`;
- old Task 4: `STOPPED_AFTER_MERGER__REQUIREMENTS_MIGRATE_ONLY`;
- old Tasks 5–12: no independent continuation;
- unified Task 1 has not started.

## 3. No GPU execution is required for this Task 0 review

Macha is the project's GPU execution agent, but this review is custody/governance review only.

Do not launch a new GPU qualification/training run merely to review Task 0.

Historical/current GPU execution capability is separately custodied in:

`docs/agent/MACHA_GPU_EXECUTION_ENVIRONMENT_AND_RUNTIME_CUSTODY_V1_20261014.md`

Future GPU qualification has its own role law:

`Macha executes -> exact receipts freeze -> different reviewer/adjudicator reviews -> only then possible promotion`.

A same-agent later pass is not independent review of the agent's own execution.

## 4. What NOT to recompute or reopen

Do not:

- reopen current candidate outcomes;
- access `reader_validation` or `reader_oracle`;
- redownload/recompute authenticated real support/calibration assets;
- rerun PR #314 corrected replay;
- rerun V79/Q00–Q11;
- regenerate historical references merely for migration;
- start old Task 3/4;
- start old Tasks 5–12;
- start unified Task 1;
- run production training.

## 5. Required Macha verdict format

Return:

1. exact Task 0 head reviewed: `c80d7398b41f10208ec1622bc52599383b940be6`;
2. confirmation that old Task 1–2 author head is `ff597faf2182522a320ec5322f8db9b67c9c6094`;
3. Task 0 findings as `CRITICAL | IMPORTANT | MINOR`, each with file/contract locus;
4. explicit F1 verdict;
5. explicit F2 verdict;
6. explicit F5–F9 completeness verdict;
7. migration-classification opinion for old Task 1: `DIRECT_REUSE | ADAPT_AND_WRAP | TEST_ONLY | REJECT`, clearly labeled as review of controller migration treatment, not independent qualification of own code;
8. same for old Task 2;
9. explicit confirmation/refutation of old Task 3/4 stop law;
10. explicit decision whether Task 0 custody/consolidation can be accepted/frozen;
11. explicit statement whether unified Task 1 may begin RED-first after Task 0 acceptance;
12. explicit statement that no human/training authority changed.

If no Critical/Important Task 0 custody finding remains, terminal verdict may be equivalent to:

`TASK0_CUSTODY_INDEPENDENTLY_ACCEPTED__MACHA_AUTHORED_TASK1_2_CONTROLLER_VERIFICATION_RECOGNIZED__MIGRATION_TREATMENT_ACCEPTED__FREEZE_EXACT_TASK0_HEAD__UNIFIED_TASK1_MAY_BEGIN_RED_FIRST__NO_HUMAN_OUTCOMES__NO_TRAINING_AUTHORITY`

If a blocker remains, return a fail-closed verdict naming exact repair loci.
