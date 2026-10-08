# Teacher/Student V5 anti-cheat + historical T1 mechanics findings

Date: 2026-09-09
Status: `CONSOLIDATED_FINDINGS__NO_TRAINING_AUTHORITY`
Canonical branch target: `main`

This file consolidates the teacher/student anti-cheat findings developed in the current review lane so future agents do not repeat the historical mistakes. It is not execution authority and it does not authorize training, TD60, successor-u0, D1, DEV/SEALED, protected-population access, or biological sweeps.

## Decision

```text
SAFE_TO_TRAIN = false
TEACHER_STUDENT_TRAINING_AUTHORIZED = false
SUCCESSOR_U0_AUTHORIZED = false
TD60_AUTHORIZED = false
D1_REAL_AUTHORIZED = false
HISTORICAL_U10_TO_U205_RESUME_AUTHORITY = false
HISTORICAL_U10_TO_U205_BIOLOGICAL_TEACHER_AUTHORITY = false
HISTORICAL_U10_TO_U205_TD60_INPUT_AUTHORITY = false
CLEAN_U0_UNAFFECTED_BY_FP16_BACKWARD_DEFECT = true
```

Current practical state:

```text
REAL_DATA_CONFIRMS_SHORTCUT_RISK
V5_PARTIALLY_HARDENED__NOT_YET_CHEAT_QUALIFIED
READY_TO_BUILD_ANTI_CHEAT_QUALIFICATION_LAYER
```

## Corrected historical diagnosis

The historical T1 failure should not be described merely as "the run crashed" or as proof that the architecture itself cannot learn biology. The scoped causal diagnosis is a specific training-mechanics defect in the historical 128 effective batch / 8 microbatch mixed-precision path:

```text
C2_CAUSAL_CONDITION_ESTABLISHED_FOR_HISTORICAL_128x8_PATH__BACKWARD_EXECUTED_UNDER_FP16_AUTOCAST
```

Under the historical condition:

- backward was executed while fp16 autocast was still enabled;
- 48/48 protected attention-routing gradients were dead;
- Adam `exp_avg` and `exp_avg_sq` remained exactly zero for those 48 tensors;
- 0/48 protected tensors moved beyond decay;
- attention output and other parts of the model could remain live;
- the objective could improve mechanically while the protected route that should learn biological signal was not actually trained.

Under the paired correction:

- the same setup used backward with autocast disabled;
- 0/48 protected gradients were dead;
- Adam moments became live;
- 48/48 protected tensors moved beyond decay;
- attention output remained live.

Therefore historical u10--u205 checkpoints are classified as:

```text
TRAINING_MECHANICS_DEFECT_INHERITED
```

They are not lawful resume points, not biological teacher authority, and not TD60 input. The clean u0 checkpoint predates optimizer updates and is unaffected by this fp16-backward defect, but u0 alone does not authorize training.

## Production update chain required by this diagnosis

Future healthy teacher/student training must bind this update chain exactly:

```text
fp16 forward
  -> backward with autocast disabled
  -> unscale
  -> 48-tensor mandatory protected-gradient gate
  -> optimizer step proved
  -> both Adam moments checked
  -> EMA update
```

Required protected identities:

```text
6 blocks
x 4 protected roles: attention_norm, attention.query, attention.key, attention.value
x weight+bias
= 48 tensors
```

Dynamic discovery may not define completeness. It must be checked against the frozen 48-tensor registry.

## T1 trajectory JSON evidence bound

Uploaded trajectory file bound in the 2026-09-09 review lane:

```text
file: 04265c6d-285c-45b6-8e17-184d6e8bdd7b.json
schema: prod41k-t1-trajectory-v2
sha256: 64c996b053d35722c7c18eeadf5e9b2dbab97b063c59101881f8a4b578125a49
updates: 205
loss_u1: 2.34403012693
loss_u205: 0.0061423068837
minimum_loss: 0.00605465978151 at update 203
loss_reduction_u1_to_u205: 99.737960%
strict_loss_decrease_steps: 141
strict_loss_increase_steps: 63
aggregate_missing_parameter_tensors_total: 0
aggregate_nonfinite_parameter_tensors_total: 0
ema_updates_match_update_count: True
```

This strengthens, rather than weakens, the guard: the loss trajectory shows a large mechanical loss decrease, but its gradient telemetry is only aggregate over coarse components. It does not expose the frozen 48 protected attention-routing tensors elementwise, nor their Adam moments. Therefore it cannot rehabilitate historical u10--u205 as resume authority or biological teacher authority.

Controlling interpretation:

```text
LOSS_DECREASE_CONFIRMED = true
LOSS_DECREASE_IS_BIOLOGICAL_QUALIFICATION = false
AGGREGATE_COMPONENT_GRADIENT_TELEMETRY_IS_INSUFFICIENT_FOR_48_TENSOR_GATE = true
HISTORICAL_U10_TO_U205_RESUME_AUTHORITY = false
HISTORICAL_U10_TO_U205_BIOLOGICAL_TEACHER_AUTHORITY = false
```

## Real-data anti-cheat findings

The actual mounted discovery expression/sample/support assets were inspected in this review lane. Synthetic fixtures are not sufficient for this layer.

Verified real expression sample facts:

```text
shape: 50,000 cells x 41,238 molecular addresses
nnz: 246,702,069
density: 0.119647931
row nnz mean: 4,934.041
row nnz min / median / max: 30 / 4,761 / 17,258
```

Real sample composition:

```text
A_NATURAL_MIXTURE:    25,000 rows
B_COVERAGE_DISCOVERY: 25,000 rows
SEA_AD: 33,821 rows
HVS:    10,958 rows
NPH52:   5,221 rows
operators: 42
donors: 104
support fingerprints: 9
```

The real support geometry is a direct shortcut channel:

```text
support_fingerprint -> source purity: 1.000
```

Depth/QC-only features were weaker than support fingerprints but still source/operator-informative in the sample. This confirms the need to route measurement information through an observation channel rather than allowing it to serve as biology.

## Anti-collapse mechanism review

Already present historically:

- stop-gradient / detached target tensors;
- evaluation-only gradient-frozen EMA target encoder;
- asymmetric online/predictor versus teacher path;
- prospective per-group collapse telemetry for relational geometry;
- synthetic/mechanics variance-floor helper with caller-supplied parameters.

Not present as V5 production policy:

- SIGReg;
- VICReg;
- calibrated covariance regularizer;
- real-data constant-vector negative-control checkpoint;
- complete V5 z_bio/z_obs collapse telemetry authority;
- externally frozen variance/effective-rank floors.

Decision:

```text
KEEP stop-gradient as hard trainer requirement.
KEEP EMA, but bind it to successful base-cell presentations rather than raw optimizer steps.
ADD latent variance/effective-rank/spread telemetry by donor/source/operator/support strata.
ADD constant-vector and low-rank negative controls before any real checkpoint can pass.
EVALUATE SIGReg-like regularization only after donor/source/operator-balanced calibration.
DO NOT add global SIGReg/VICReg as a blind default.
```

## Observation-operator rule

The model may use lawful observation facts to interpret evidence, but those facts must not become biological state.

Allowed in the observation/measurement channel (`z_obs` or equivalent):

```text
source family where physically meaningful
operator support
measured vocabulary
sequencing depth / detection statistics
measurement uncertainty
count-split noise
chemistry / technology descriptors where available
```

Forbidden as free direct inputs to the biological state path (`z_bio`):

```text
donor ID
arbitrary matrix ID embedding
arbitrary dataset ID embedding
pathology labels
protected labels
sealed labels
post-T0 confirmation labels
```

Do not blindly erase all operator information. The right question is:

```text
After controlling for comparable molecular biology, how much unnecessary acquisition signal remains in z_bio?
```

## Biology-destructive low-loss checkpoint STOP rule

Loss decrease is never sufficient. A future checkpoint must be rejected if any of these occur while loss improves:

```text
STOP_LOSS_IMPROVED_BUT_BIOLOGY_DEGRADED
STOP_LOSS_IMPROVED_BUT_SHORTCUT_ASCENDED
STOP_LOSS_IMPROVED_BUT_TRANSFER_DEGRADED
STOP_Z_BIO_VARIANCE_COLLAPSE
STOP_Z_BIO_EFFECTIVE_RANK_COLLAPSE
STOP_CHECKPOINT_TELEMETRY_MISSING
```

Required atomic checkpoint telemetry:

```text
jepa_loss
biology_endpoint_score
shortcut_probe_score
z_bio_variance_ratio_to_teacher_or_u0
z_bio_effective_rank_ratio_to_teacher_or_u0
transfer_score
target_branch_stop_gradient_verified
ema_exposure_clock_verified
hardware_science_firewall_verified
no_forbidden_gate_opened
```

## Required anti-cheat qualification gates before training

```text
HISTORICAL_T1_MECHANICS_DEFECT_QUARANTINE
BACKWARD_AUTOCAST_DISABLED_GATE
MANDATORY_48_GRADIENT_AND_MOMENT_GATE
ATTENTION_OUTPUT_CANNOT_RESCUE_PROTECTED_ROUTING_DEATH
STOP_GRADIENT_TARGET_BRANCH_AUDIT
EMA_EXPOSURE_CLOCK_BINDING
LATENT_COLLAPSE_VARIANCE_EFFECTIVE_RANK
CONSTANT_VECTOR_NEGATIVE_CONTROL
SUPPORT_ONLY_SOURCE_ATTACK
DEPTH_QC_ONLY_ATTACK
MASK_ONLY_ATTACK
SUPPORT_COUNTERFACTUAL
OPERATOR_SOURCE_CONDITIONAL_PROBE
DONOR_MEMORIZATION_PROBE
HELD_OUT_DONOR_TRANSFER
HELD_OUT_OPERATOR_OR_MATRIX_TRANSFER
HELD_OUT_STUDY_OR_SOURCE_TRANSFER
HELD_OUT_TECHNOLOGY_TRANSFER_WHERE_POSSIBLE
EVIDENCE_RESPONSE_CURVE
DEPTH_RESPONSE_CURVE
PROPOSAL_WEIGHTING_P_OVER_Q_AUDIT
HARDWARE_INVARIANCE_REPLAY
HISTORICAL_CHECKPOINT_QUARANTINE
```

## Local review artifacts pushed or summarized

Detailed chat-local review artifacts are mirrored under `docs/agent/v5_anticheat/`, `scripts/v5_anticheat/`, and `tests/v5_anticheat/` as available. Large binary inputs such as `.pt`, `.npz`, and full checkpoint archives are intentionally not copied into GitHub by this note; they remain external artifacts and are referenced by SHA/provenance.

## Verification run in local review lane

```text
python scripts/analyze_t1_trajectory_json_v1.py
# PASS_T1_TRAJECTORY_JSON_REVIEW_V1

python scripts/review_t1_trajectory_json_outputs_v1.py
# PASS_T1_TRAJECTORY_JSON_OUTPUT_REVIEW_V1

PYTHONPATH=. python -m pytest tests -q
# 23 passed

python scripts/review_mechanics_defect_integration_v1.py
# PASS_HISTORICAL_T1_MECHANICS_DEFECT_INTEGRATION_REVIEW_V1

python scripts/review_biology_destruction_sentinel_v1.py
# PASS_BIOLOGY_DESTRUCTION_SENTINEL_REVIEW_V1

python scripts/review_anti_collapse_outputs_v1.py
# PASS_ANTI_COLLAPSE_OUTPUT_REVIEW_V1

python scripts/review_real_data_anticheat_outputs_v1.py
# PASS_REAL_DATA_ANTI_CHEAT_OUTPUT_REVIEW_V1

python scripts/review_anticheat_docs_v1.py
# PASS_ANTI_CHEAT_DOC_REVIEW_V1
```

These are chat-local checks; they are not CI and must be reproduced before promotion.

## Permanent frozen phrase

```text
A teacher/student checkpoint is not biologically qualified because loss decreases.
It is biologically qualified only if mechanics health is proven and the checkpoint survives mask-only, support-only, depth-only, donor-holdout, matrix-holdout, study-holdout, technology-holdout, proposal-weighting, collapse, and hardware-invariance attacks.
```
