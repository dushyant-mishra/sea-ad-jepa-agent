# Macha Task 0 final independent review packet V1 — 2026-10-14

## Purpose

Fresh-context, minimal-token hostile review packet for the final Task 0 custody decision after old PR #356 Tasks 1–2 were located and controller-verified.

This packet is navigation/evidence only. Macha must form an independent verdict from the exact bytes/receipts cited below rather than accepting controller conclusions.

Global authority remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

No candidate outcomes, `reader_validation`, or `reader_oracle` may be opened for this review.

---

## 1. Exact objects to review

### A. Task 0 implementation

PR #381

Exact head:
`6059e1d7bb30bd61d3f1f47d46a77e6322c525c0`

Base:
`9328f1c00faee8a0ebf1910d412ea129bab566be`

Focused GREEN:
- workflow run `38632619995`

Inherited GREEN:
- workflow run `38632619965`

Read these Task 0 outputs first:

1. `results/target_discovery/unified_qualification_v1/PREMERGER_ARTIFACT_MIGRATION_MATRIX_V1.json`
2. `results/target_discovery/unified_qualification_v1/PREMERGER_MIXED_ARTIFACT_DECOMPOSITION_V1.json`
3. `results/target_discovery/unified_qualification_v1/PREMERGER_MACHA_DUAL_STREAM_CUSTODY_V1.json`
4. `results/target_discovery/unified_qualification_v1/PREMERGER_UNRESOLVED_WORK_LEDGER_V1.json`
5. `results/target_discovery/unified_qualification_v1/PREMERGER_MERGED_CUSTODY_COMPLETENESS_V1.json`
6. `scripts/v5/td_unified/premerger_migration_task0.py`
7. `scripts/v5/td_unified/premerger_custody_completeness_v1.py`
8. corresponding Task 0 hostile tests.

### B. Old PR #356 Tasks 1–2 exact implementation

Branch:
`implementation/production-synthetic-v3-1-1-20261014`

Exact head:
`ff597faf2182522a320ec5322f8db9b67c9c6094`

Files changed relative to its preimplementation base are only:
- `scripts/production_synthetic/canonical_v1.py`
- `scripts/production_synthetic/custody_v1.py`
- `tests/production_synthetic/custody_fixtures_v1.py`
- `tests/production_synthetic/test_canonical_v1.py`
- `tests/production_synthetic/test_custody_v1.py`
- `tests/production_synthetic/test_custody_v1_hostile.py`

Controller-owned review PR #382 adds only a workflow above those bytes.

Focused controller rerun:
- run `38644641042`
- job `116128364543`
- result: `332 passed in 8.94s`

Inherited integration:
- run `38644640881`
- conclusion: success.

The source branch was rechecked after these runs and remained exactly `ff597faf...`.

---

## 2. Prior blocking findings to re-adjudicate independently

### F1 — mixed historical objects

Original defect: top-level mixed objects could carry only one migration class plus prose decomposition.

Required closure condition:
- machine-readable child decomposition;
- independently classified children;
- at least two migration classes for a mixed parent;
- prose-only note cannot satisfy decomposition;
- superseded/failed children retain their own authority/requalification laws.

### F2 — exact identity self-attestation

Original defect: deleting `exact_identity_available` could bypass identity validation.

Required closure condition:
- field mandatory everywhere relevant;
- boolean only;
- deletion fails closed;
- `true` requires exact source commit + artifact digest;
- no invented exact identity where bytes are genuinely unavailable.

### F5–F9 completeness

Confirm Task 0 now preserves without promotion:
- F5: old PR #356 Tasks 1–4 separately from stopped old Tasks 5–12;
- F6: Foundation `SUBSPACE_ONLY`, technology invariance not qualified, partial matrix coverage/source-acquisition limits;
- F7: multimodal/SCENIC+/ATAC same-vs-separate nucleus and independent-measurement boundaries;
- F8: runtime safety as post-science training prerequisite rather than target authority;
- F9: FULL104 denominator/source channel, evidence-burden, estimability/zero-fill and metric-blindness obligations.

---

## 3. Independent review questions for old Tasks 1–2

### Old Task 1 canonicalization

Independently decide whether the exact `ff597faf...` Task 1 bytes are reusable shared infrastructure.

Check especially:

1. canonical JSON bytes deterministic on the shared JSON-native scientific domain;
2. raw-byte and semantic identities are not conflated;
3. nonfinite/missing/zero/bool/int/float distinctions cannot silently collide;
4. strict JSON load cannot turn a nonzero literal into measured zero by underflow;
5. duplicate normalized keys fail;
6. canonical ordered-registry digest is **order-sensitive**;
7. separate keyed semantic row-set identity is **storage/shard-order invariant**;
8. historical NumPy scalar convenience support does not need to become unified scientific identity authority;
9. historical synthetic digest domains must not be silently adopted as unified receipt domains.

Proposed controller classification to challenge, not accept automatically:

`ADAPT_AND_WRAP__DIRECT_REUSE_CANDIDATE_FOR_CANONICAL_PRIMITIVES`

This does **not** mean unified Task 1 complete. Unified Task 1 additionally requires recursive receipt/parent verification, `QualificationStage`, `ActiveLineageStatus`, authority scope and schemas.

### Old Task 2 custody/RNG

Independently check:

1. >=256-bit nonce/commit-reveal enforcement;
2. identity-keyed/order-invariant RNG rather than row-position seeding;
3. no integer-offset namespaces/seed shopping;
4. append-only exposure/fit-freeze/reveal ordering;
5. linear successor/requalification semantics;
6. no qualification inheritance after post-exposure defect repair;
7. secret-absence and unique withheld-code-path checks;
8. method-local and lineage-wide qualification draw accounting;
9. no production secret/nonce in public fixtures/tests.

Then verify that the module's own explicitly deferred obligations are preserved as unresolved later-task requirements:

- one externally anchored genesis ledger per testbed;
- externally published/verified ledger head after every entry;
- both multiplicity reports;
- reveal-time realization regeneration/content verification;
- full exact committed-tree secret scanning across published commits;
- independent adjudication of generator defect records.

Proposed controller classification to challenge:

`ADAPT_AND_WRAP__SEALED_CUSTODY_RNG_SUBSTRATE`

This does **not** satisfy unified Task 2. Unified Task 2 is `TD_EXECUTION_MANIFEST_V1` + population/access law + producer access receipts.

---

## 4. Consolidation law to review

Audit head containing controller analysis:
`3891ac7376876a7c7f884a0d8a69e92596918656` or later descendant on PR #322.

Relevant controller files:

- `results/target_discovery/unified_qualification_v1/MACHA_OLD_SYNTH_TASK1_2_CONTROLLER_VERIFICATION_V1.json`
- `results/target_discovery/unified_qualification_v1/MACHA_TASK1_2_ABSORPTION_MATRIX_V1.json`
- `docs/agent/UNIFIED_TASK1_4_PR356_CONSOLIDATION_ADAPTER_CONTRACT_V1_20261014.md`
- `docs/agent/UNIFIED_TASKS1_3_HOSTILE_TEST_BLUEPRINT_V1_20261014.md`

Required independent decision:

- accept, amend, or reject the proposed migration of old Task 1 into unified Task 1 primitives;
- accept, amend, or reject the proposed migration of old Task 2 primarily into unified Task 4/later custody obligations;
- confirm old Task 3/4 remain **not authorized to start**;
- confirm old Tasks 5–12 remain stopped as an independent authority program.

---

## 5. What NOT to review/recompute

Do not:

- reopen current candidate outcomes;
- access `reader_validation` or `reader_oracle`;
- redownload/recompute authenticated real support/calibration assets;
- rerun PR #314 corrected replay;
- rerun V79/Q00–Q11;
- regenerate historical references merely for migration;
- review unrelated later unified implementation, because Task 1 has not started.

---

## 6. Required verdict format

Return exactly enough evidence to bind the decision:

1. exact Task 0 head reviewed;
2. exact old Task 1–2 head reviewed;
3. exact controller review run IDs inspected;
4. findings as `CRITICAL | IMPORTANT | MINOR`, each with file/contract locus;
5. explicit F1 verdict;
6. explicit F2 verdict;
7. explicit F5–F9 completeness verdict;
8. old Task 1 migration verdict: `DIRECT_REUSE | ADAPT_AND_WRAP | TEST_ONLY | REJECT`;
9. old Task 2 migration verdict: same enum;
10. explicit decision whether Task 0 can be finally accepted/frozen;
11. explicit statement whether unified Task 1 may start;
12. explicit statement that no human/training authority changed.

If no Critical/Important finding remains and custody is complete, terminal verdict should be equivalent to:

`TASK0_INDEPENDENTLY_ACCEPTED__OLD_TASK1_2_CUSTODY_CONSOLIDATED__FREEZE_EXACT_TASK0_HEAD__UNIFIED_TASK1_MAY_BEGIN_RED_FIRST__NO_HUMAN_OUTCOMES__NO_TRAINING_AUTHORITY`

Otherwise return a fail-closed blocking verdict naming the exact repairs.
