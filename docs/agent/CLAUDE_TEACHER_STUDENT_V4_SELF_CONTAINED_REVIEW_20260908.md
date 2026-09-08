# Claude — Unified Teacher/Student V4 Self-Contained External Review

Date: 2026-09-08

Review only the exact self-contained V4 package supplied with this instruction.

## Controlling source identity

Branch:

`development/teacher-student-relational-v4-20260908`

Integrated source commit:

`931520bdbe6ac58b93298b38890bbcb054011648`

Source manifest:

`docs/agent/TEACHER_STUDENT_INTEGRATED_SOURCE_MANIFEST_V4.csv`

Source root:

`743347ab176adb8c3b7bd4ec74897d8e223d3ca4de9d78b9e4d398aa90bdedb2`

Upstream frozen authorities remain:

- predictor registry: `43922a62a885cbedee22c06363a8355c6561dad43c95f0a43147fc2f4cbe3592`
- healthy-teacher base: `9e1ee362773a8329f783015a04af4f7699135cc0710b1ee1ea66abc0aafd8534`
- population registry: `e9903bbb9d56663790f5f5b298c5633d87a71548466089e7cc6aae7c45728ee7`
- F1-B authority: `daa79afe19ab17f1f7cfa064754d671afd4ac4b284250605979f1d288862544b`
- historical clean u0 state-source: `19fb0c25d9f7549c37de39285807d5b6a6e828ced94af63927e83fa3c5c6b7c4`

## Why V4 supersedes the pre-review V3 candidate

### Review binding

V3's requested review terminal and execution-overlay validator used different terminal namespaces. V4 requires one exact review PASS string and additionally binds the reviewed package SHA/root and reviewed source root. Do not accept prefix substitution.

### Relational target

The previous prospective V1 relational adjunct matched normalized distance magnitudes and angle/cosine values. That is stronger than the Target Discovery evidence.

V4 replaces it with:

`src/sea_ad_jepa/v4/teacher_student_relational_target_v2.py`

The V2 target is still **inactive**. It is included in the reviewed source identity so that a future promotion cannot silently swap in unreviewed mechanics.

## Required package verification

From a clean extraction, rehash every member against `PACKAGE_MANIFEST.csv` and verify:

`sha256(PACKAGE_MANIFEST.csv) == PACKAGE_ROOT_SHA256.txt`.

Confirm no packaged path contains `__pycache__`, `.pytest_cache`, or `.pyc`.

## Required replay

Install pytest, numpy, pandas, scipy, and CPU PyTorch.

Then run:

```bash
export PYTHONPATH=src:.
python scripts/agent/audit_teacher_student_integration_freeze_v4.py --root .
python -m pytest -q \
  tests/test_c2_mandatory_gradient_gate_v1.py \
  tests/test_f1b_successor_attack_suite_v1.py \
  tests/test_population_access_registry_v1.py \
  tests/test_healthy_teacher_training_contract_v1.py \
  tests/test_teacher_student_unified_runtime_v1.py \
  tests/test_teacher_student_relational_v2.py \
  tests/test_teacher_student_integration_freeze_v4.py
```

The C2 test must replay its packaged K0/K1 evidence rather than skip.

## Production mechanics review

Independently inspect that the inherited active runtime still preserves:

1. exact 41,238-address / 160-D / 6-block / 4-head geometry;
2. EMA teacher no-grad/eval semantics;
3. exact 15-tensor predictor mandatory registry;
4. four exact 40%-hidden MEASURED_SCALAR views;
5. CUDA fp16 forward;
6. scaled backward with autocast disabled;
7. unscale before mandatory gradient gates;
8. fail-closed missing/nonfinite/all-zero mandatory gradients;
9. no arbitrary small-gradient floor;
10. optimizer step proof before EMA;
11. live finite/nonzero Adam moments;
12. canonical EMA parameter/buffer equation;
13. per-tensor exact deviation from repeated AdamW decay-only counterfactual;
14. checkpoint/RNG/config/source bindings;
15. no biology-dependent continuation;
16. u0→u40 only after separate execution authority;
17. historical u10-u205 never legal resume sources.

## Review the V2 relational target

Confirm the implementation matches this exact prospective target:

For direct 160-D teacher/student cell states,

`d(a,b)=1-cosine(z_a,z_b)`.

For teacher-resolved triplets,

`y=sign(d_T(i,k)-d_T(i,j))`.

Student margin:

`m_S=d_S(i,k)-d_S(i,j)`.

Loss:

`softplus(-y*m_S)/log(2)`.

Verify:

- only teacher order sign supervises the student;
- teacher distance magnitude and angle are not matched;
- zero-norm/nonfinite states fail closed;
- student ties are penalized, not treated as success;
- relations never cross donor×operator groups;
- exact externally frozen triplets can be accepted;
- the module itself selects no locality fraction or k;
- grouped production geometry has no silent default;
- collapse calibration has no numerical default;
- `production_update` does not import/call the relational target.

A defect here is a V4 source defect even though the target is inactive, because V4 intentionally includes it in the reviewed source identity.

## Historical-u0 preflight

Review:

`docs/agent/HEALTHY_TEACHER_U0_CPU_COMPATIBILITY_PREFLIGHT_20260908.json`.

Treat it only as a schema/key/shape preflight. It is not CUDA materialization and does not authorize execution.

## Execution firewall

The package must not contain either execution authority file. No u1 or neural training is authorized by this review.

## Requested terminal

If and only if the exact V4 source, replay closure, package closure, and prospective relational target are clean, return exactly:

`PASS_TEACHER_STUDENT_UNIFIED_V4_INDEPENDENT_REVIEW__TRAINING_STILL_UNAUTHORIZED`

Otherwise return:

`STOP_TEACHER_STUDENT_UNIFIED_V4_INDEPENDENT_REVIEW__<PRECISE_REASON>`

Do not emit the PASS terminal as an example if stopping.
