# Claude — Unified Teacher/Student V4 Self-Contained External Review

Date: 2026-09-08

Review the exact self-contained package generated from the governance-only successor branch:

`production/teacher-student-unified-v4-governance-repair-20260908`

## Controlling V4 source identity

- integrated source commit:
  `739b6495f9c102a6d6d68f64beb37c68c42e676d`
- source manifest:
  `docs/agent/TEACHER_STUDENT_INTEGRATED_SOURCE_MANIFEST_V4.csv`
- source root:
  `2637fe1a4954cb26edde4f6cf79993dff4dbeb1662885bac70b150b9eb654870`
- predictor registry:
  `43922a62a885cbedee22c06363a8355c6561dad43c95f0a43147fc2f4cbe3592`
- healthy-teacher base:
  `9e1ee362773a8329f783015a04af4f7699135cc0710b1ee1ea66abc0aafd8534`
- population registry:
  `e9903bbb9d56663790f5f5b298c5633d87a71548466089e7cc6aae7c45728ee7`
- F1-B attack authority:
  `daa79afe19ab17f1f7cfa064754d671afd4ac4b284250605979f1d288862544b`

Read first:

`docs/agent/TEACHER_STUDENT_V4_GOVERNANCE_REPAIR_20260908.md`

V4 supersedes V3 for future execution binding. V3 independently replayed green but adversarial review found governance fail-open boundaries. V4 changes only governance validation; the production model/loss/masking/optimizer/EMA mechanics are unchanged. Separately, prospective relational V1 was superseded by prospective V2 after adversarial review found an 8×16 batch-contract override and pooled collapse-health rescue.

## Required package verification

From a clean extraction, verify every `PACKAGE_MANIFEST.csv` row by exact bytes/SHA-256 and verify:

`sha256(PACKAGE_MANIFEST.csv) == PACKAGE_ROOT_SHA256.txt`

Reject any packaged path containing `__pycache__`, `.pytest_cache`, or `.pyc`.

## Reproduce active V4 review

Install:

```bash
python -m pip install pytest numpy pandas scipy
python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
```

Then:

```bash
export PYTHONPATH=src:.
python scripts/agent/audit_teacher_student_integration_freeze_v4.py --root .
python -m pytest -q \
  tests/test_c2_mandatory_gradient_gate_v1.py \
  tests/test_f1b_successor_attack_suite_v1.py \
  tests/test_population_access_registry_v1.py \
  tests/test_healthy_teacher_training_contract_v1.py \
  tests/test_teacher_student_unified_runtime_v1.py \
  tests/test_teacher_student_integration_freeze_v4.py
```

The C2 test must actually replay K0 and K1 from packaged JSON evidence; no evidence-missing skip is acceptable.

Reproduce the healthy-teacher base manifest and population-registry manifest from packaged members.

## Mandatory V4 governance attacks

Independently verify all of the following, not only via the packaged tests:

1. The integrated-successor independent-review terminal is accepted only by exact equality with:
   `PASS_TEACHER_STUDENT_UNIFIED_V4_INDEPENDENT_REVIEW__TRAINING_STILL_UNAUTHORIZED`.
2. A spoof such as
   `PASS_TEACHER_STUDENT_UNIFIED_V4_INDEPENDENT_REVIEW__TRAINING_STILL_UNAUTHORIZED__STOP_FORGED`
   is rejected.
3. The u40 independent-review terminal is accepted only by exact equality with:
   `PASS_HEALTHY_TEACHER_U40_INDEPENDENT_REVIEW`.
4. A u40 PASS-prefix spoof is rejected.
5. Checkpoint header/restore rejects any phase outside exactly:
   `U0`, `QUALIFICATION`, `CONTINUATION`.
6. Qualification restore requires `expected_phase="U0"`.
7. Continuation restore requires `expected_phase="QUALIFICATION"` at cursor 40.
8. A checkpoint with correct counters/hashes but phase `FORGED` cannot be restored.
9. Qualification/continuation consume the overlay validator's internally generated PASS terminal by exact equality, not generic `PASS_` prefix matching.
10. No V4 governance repair changes the frozen model, masking, optimizer, EMA, movement, schedule/population, or biology-firewall semantics.

## Production mechanics regression review

Reconfirm that V4 still preserves:

1. exact 41,238-address / 160-D / 6-block / 4-head geometry;
2. EMA teacher no-grad/eval semantics;
3. exact predictor 15-tensor mandatory registry;
4. four exact 40%-hidden MEASURED_SCALAR target-mask views;
5. CUDA fp16 forward autocast;
6. scaled backward with autocast disabled;
7. unscale before gradient gates;
8. exact missing/nonfinite/all-zero rejection for 48 backbone + 15 predictor tensors;
9. no arbitrary small-gradient floor;
10. optimizer step proved before EMA;
11. both Adam moments finite/nonzero;
12. EMA parameters/buffers follow canonical equation;
13. exact movement adjudication against repeated AdamW decay-only counterfactual;
14. checkpoint/RNG/config/source bindings;
15. no biology-dependent early stopping;
16. u0→u40 only; no automatic u40→u205 continuation;
17. no legal resume from historical defect-inherited u10–u205.

## Prospective relational extension

Review separately and do not conflate with active V4 training:

- `docs/agent/TEACHER_STUDENT_RELATIONAL_EXTENSION_V2_20260908.md`
- `src/sea_ad_jepa/v4/prospective_relational_teacher_student_v2.py`
- `tests/test_teacher_student_relational_v2.py`

Run:

```bash
python -m pytest -q tests/test_teacher_student_relational_v2.py
```

The relational V2 adjunct remains prospective, inactive, and training-unauthorized. V1 is superseded and must not be treated as candidate mechanics. Independently attack the exact 8×16 batch contract, per-group no-pooled-rescue collapse gate, zero-norm angle rejection, exact evidence levels, fine-matched null, and V4 runtime non-import/non-call firewall. A relational defect should be reported separately unless it reveals a shared-source contradiction.

## Execution firewall

The package must not contain either:

- `docs/agent/HEALTHY_TEACHER_U0_U40_EXECUTION_AUTHORITY_V1.json`
- `docs/agent/HEALTHY_TEACHER_CONTINUATION_EXECUTION_AUTHORITY_V1.json`

No real training is authorized by this review.

## Requested terminals

If V4 active source/replay packaging is clean:

`PASS_TEACHER_STUDENT_UNIFIED_V4_INDEPENDENT_REVIEW__TRAINING_STILL_UNAUTHORIZED`

If V4 active source or package has a defect:

`STOP_TEACHER_STUDENT_UNIFIED_V4_INDEPENDENT_REVIEW__<PRECISE_REASON>`

For the relational adjunct, report separately:

- `PASS_RELATIONAL_EXTENSION_V2_PROSPECTIVE_REVIEW`, or
- `STOP_RELATIONAL_EXTENSION_V2_PROSPECTIVE_REVIEW__<PRECISE_REASON>`

Do not authorize u1, real F1/T0/D1, pathology, reader-validation/oracle, DEV, or SEALED as part of this review.
