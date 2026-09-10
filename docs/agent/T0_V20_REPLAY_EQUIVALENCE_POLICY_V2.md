# T0 V20 replay-equivalence policy V2 — frozen review policy

Status: **FROZEN REVIEW POLICY. NOT T0 SCIENCE AUTHORITY. NOT TRAINING AUTHORITY.**

Parent policy: `T0_V20_REPLAY_EQUIVALENCE_CANDIDATE_V1.md` and the V1 implementation on `review/t0-v20-replay-equivalence-20260910`.

V1 result retained unchanged: `STOP_T0_V20_REPLAY_NOT_EQUIVALENT_UNDER_FROZEN_POLICY`.

## Owner decision

Freeze a V2 replay-equivalence policy with exactly one change from V1:

- `final_trace_scale`: move from exact-scalar equality to `max_ulp: 1` in float64.

Every other V1 target-fit tolerance, exact field, dtype rule, provenance rule, decision-replay rule, terminal rule, routing rule and reporting-only restriction remains unchanged.

No V1 artifact, V1 STOP result, frozen V20 file, or historical `verify_target_v2_against_raw` may be edited or superseded in place.

## Basis for the V2 correction

This is frozen as a correction to an internally inconsistent classification of two algebraically linked outputs, not as a permission to tune tolerances until replay passes.

Frozen `t0_target_learner_v1.py` computes:

```python
s = float(np.trace(gram)/n)
lam = float((10.0**float(multiplier_exp))*s)
```

where `s` is serialized as `final_trace_scale` and `lam` as `final_lambda`. Under the frozen selected multiplier exponent `2.0`, the latter is derived directly from the former by multiplication by `100.0`. The V1 policy already classifies `final_lambda` as a float64 reduction-derived quantity permitted to differ by at most one ULP while classifying its parent `final_trace_scale` as exact. That asymmetry is not a scientifically meaningful distinction.

The frozen scoring path subsequently consumes `beta`, `mu`, and `sigma`; `final_trace_scale` is not an independent scoring or adjudication input after the target fit. Its influence on the fitted target is mediated through `final_lambda` and therefore through `beta`, all of which remain independently checked under their frozen V1 rules.

The V1 run observed one ULP on `final_trace_scale`, but that observation is not used to set a wider numerical envelope than the already-adopted one-ULP class. V2 permits exactly the same one-ULP class already assigned to its algebraically derived companion `final_lambda`; it does not introduce a caller-configurable or result-dependent tolerance.

## Immutable V2 rules

V2 inherits V1 unchanged except for the single field move above. In particular:

- canonical raw-input provenance must match exactly;
- dtype guards remain active, with float64 required for budgeted and ULP fields;
- `beta`, `sigma`, and `cv_mse_by_multiplier` retain their frozen field-specific V1 budgets;
- `final_lambda` and `response_residual_sd` remain `max_ulp: 1`;
- `final_trace_scale` is now also `max_ulp: 1`;
- all remaining V1 exact arrays and exact scalars remain exact;
- both terminal strings remain exact;
- `state_primary` keeps the V1 split between tightly budgeted continuous fields and exact discrete/p-value fields;
- no V20 science conclusion, estimator, target, threshold, nuisance model, feature role, membership, or adjudication rule changes;
- sensitivity recovery remains reporting-only and cannot authorize training.

The committed `null_t` field is a truncated serialized representation rather than the full 9,999-value null array. V2 therefore makes no claim of full-null-array equality. It requires the committed representation check available to V1 plus exact permutation count and exact decision-relevant p-values; this limitation must be stated in any recovered report.

## Rerun rule

Run the recovery unchanged under a separately versioned V2 implementation/policy identity.

If any field other than the V1 `final_trace_scale` mismatch fails its inherited rule, or if `final_trace_scale` exceeds one float64 ULP, or if either decision-equivalence/terminal check fails, the result is STOP.

**Do not create a V3 tolerance expansion in response to another observed mismatch.** Any future policy change requires independent evidence and a new owner governance decision; it is not implied by this authorization.

The original numeric-stack reconstruction remains a parallel reproducibility task and should continue. It is not waived by V2.

## Required publication

The V2 run must publish:

1. the V1 STOP artifact unchanged;
2. the exact V2 policy/implementation identity;
3. complete target-fit equivalence results, including observed absolute/relative/ULP differences;
4. exact provenance result;
5. decision-equivalence results and terminal strings;
6. numeric environment including Python, NumPy, SciPy, BLAS implementation/thread count, and SIMD where available;
7. recovered sensitivity statistics only if every V2 gate passes;
8. explicit `training_authorized: false`.

Independent review remains required before this review policy can be promoted into project governance authority.