# F1 HC3 15C — External Review — 2026-09-02

## Verdict

`STOP_F1_HC3_15C_NUMERICAL_INDEPENDENCE_UNRESOLVED`

15C completed its local synthetic-only integration packet and is durably anchored with terminal `PASS_F1_HC3_15C_DECISION_INTEGRATION_AWAITING_EXTERNAL_REVIEW`, manifest SHA-256 `6b50bc768346c9dcaff6b26ec986f3af21c68b7a5b54eefebbd5ae407fbbe436`, and handoff SHA-256 `bda3a56a7da5cbdbac022190c0de7744867b27cc5908bcb90e16275ae17f67ac`.

The external review does **not** promote 15C. The blocker is narrow: the conclusion-bearing HC3 numerical route and its claimed independent validation are not sufficiently independent or numerically robust for the selected ill-conditioned nuisance design.

## What passes this review

- Frozen 15B selection `(5,0,4)` remains accepted and unchanged.
- Selected 104 x 16 design remains rank 16 with df 88, 104/104 donor-deletion rank stability, and HC3 geometry admissible under the already accepted SVD/QR 15A4/15B geometry checks.
- Exact selected design SHA-256 remains `5d2fda2e81a6edd63241ccf996fe0e5086275233e765daae19509be24cd518e3`.
- 15C is additive: the frozen decision-v4 and integration-v4 authorities remain hash-bound rather than silently edited.
- The 15C adapter is donor-keyed, requires the exact 104-donor set, rejects caller-supplied authority fields, and leaves real reader/forward authority unset.
- No expression, real outcome, model/checkpoint tensor, training, optimizer, or EMA access is authorized by this review.

## Blocking numerical finding

The frozen selected design reports condition number `5,871,549.063684238`. Squaring the design through normal equations gives an approximate condition number for `X^T X` of `3.4475088407251254e13`; multiplying by float64 machine epsilon gives approximately `7.66e-3` as a worst-case numerical-error amplification scale. This is too large to treat a normal-equations implementation as automatically interchangeable with a QR/SVD implementation at a conclusion-bearing gate.

The production arithmetic currently inherited by 15C (`scripts/v4/contextual_target_f1_decision_v1.py::hc3_intercept`) forms `inv(X.T @ X)` and derives both coefficients/covariance and leverage from that inverse.

The purported independent 15C validator (`scripts/v4/validate_contextual_target_f1_hc3_15c_v1.py::hc3`) independently rewrites the function, but it repeats the same numerical route: `inv(x.T @ x)` followed by the same normal-equations leverage/covariance construction. Therefore implementation independence is insufficient for the numerical issue that matters here.

This is inconsistent with the stronger numerical discipline already established in 15A4, where conclusion-bearing leverage was computed from the SVD column-space projection and independently cross-checked with pivoted QR.

The issue is not that the selected design has failed HC3 geometry. Its accepted geometry remains well away from the leverage singularity (`max h ~= 0.86937`, `min(1-h) ~= 0.13063`). The issue is that 15C has not yet demonstrated that the actual HC3 intercept estimate, HC3 standard error, confidence bound, and resulting gate are invariant to a stable numerical implementation.

## Required narrow repair before promotion

1. Preserve the existing historical 15C packet and all frozen v1/v4/15B bytes. Do not overwrite or relabel them.
2. Freeze a prospective **15C numerical-robustness repair contract** before examining any new comparison result.
3. Add a new conclusion-bearing stable HC3 route rather than modifying the frozen historical decision-v1/v4 bytes in place. The production route must avoid forming/inverting `X^T X` for the solve/leverage calculation; QR or SVD column-space methods are acceptable.
4. Compute leverage from an orthonormal basis (`sum(Q^2, axis=1)` or the equivalent SVD projection). Compute the coefficient and HC3 sandwich through a stable QR/SVD factorization rather than a normal-equations inverse.
5. The independent validator must use a genuinely different stable route (for example, production QR and independent SVD/pseudoinverse or pivoted-QR reconstruction) and must not import the production HC3 helper.
6. Prospectively freeze numerical comparison tolerances from float64 scale/design conditioning before reading the repair outputs. Reuse the existing 15A4 SVD-vs-QR leverage discipline where applicable.
7. Re-run the synthetic all-pass case, isolated HC3 veto, zero-variance/non-estimable case, selected-design authority mutations, donor-order/API attacks, source-confined case, strict legal-domain suite, and all prior decision regressions.
8. Add a targeted synthetic near-boundary HC3 stress test demonstrating that the stable production and independent routes produce the same gate and closely matching beta0, standard error, confidence bound, leverage, and effective-design identity.
9. Keep real F1 reader/forward authority unset. No real F1 sweep, training, checkpoint write, optimizer step, EMA update, DEV/SEALED/pathology access, or biological outcome adjudication is authorized by this repair.
10. Require a fresh external review of the repair packet before any real F1 execution authority can be considered.

## Scope of this STOP

This STOP does **not** reopen 15A4 or 15B selection, does not authorize a new nuisance-design search, and does not reopen the closed `D_shared` branch. It only blocks promotion of 15C until the HC3 numerical implementation and independent validation are made consistent with the already established fail-closed SVD/QR geometry discipline.

## Reviewed GitHub state

- Repository: `dushyant-mishra/sea-ad-jepa-agent`
- Reviewed preservation commit: `2c000eccb0ff8f0c23e19e0e0c27c0c6cbdffafd`
- 15C root: `docs/agent/provenance-anchors/F1_HC3_15C_DECISION_INTEGRATION_ROOT_20260902.json`
- 15C preserved handoff/manifest/source manifest: `docs/history/exact_bytes/outputs/contextual_teacher_target_v1_f1_hc3_15c_decision_integration_20260902/`
- Selected-design geometry: `docs/history/exact_bytes/outputs/contextual_teacher_target_v1_f1_hc3_nuisance_design_freeze_20260902/F1_HC3_SELECTED_GEOMETRY.json`
- Production HC3 arithmetic: `scripts/v4/contextual_target_f1_decision_v1.py`
- 15C adapter/runner/validator/finalizer: `scripts/v4/contextual_target_f1_hc3_15c_adapter_v1.py`, `run_contextual_target_f1_hc3_15c_v1.py`, `validate_contextual_target_f1_hc3_15c_v1.py`, `finalize_contextual_target_f1_hc3_15c_v1.py`

Chronology note: the 2026-09-02 Git preservation commits are backfill/preservation events. They do not retroactively establish historical Git chronology for recovered artifacts.