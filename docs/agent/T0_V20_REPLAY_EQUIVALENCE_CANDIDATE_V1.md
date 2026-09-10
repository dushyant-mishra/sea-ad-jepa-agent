# T0 V20 replay-equivalence candidate V1 — review only

Status: **CANDIDATE FOR INDEPENDENT REVIEW. NOT T0 AUTHORITY. NOT TRAINING AUTHORITY.**

Base T0 authority commit: `d5d67e21398da92e39095afd864b4fb9ebe3da02`.
The frozen V20 files and the historical bit-exact verifier are not edited.

## Problem this candidate addresses

The committed V20 target verifies raw-input provenance exactly and then requires
bit-exact equality of floating arrays. On a different numerical stack the exact
same input provenance recomputes with last-bit differences: beta max relative
`2.8e-12` / max absolute `5.9e-21`, sigma max relative `8.2e-16` / max absolute
`2.2e-16`, CV MSE max relative `2.6e-15`, and one-ULP differences in final
lambda and residual SD. Mu, decision mask, selected multiplier/exponent,
discovery age center and donor order are exact. The published reproducibility
finding states that recovering the omitted reporting-only sensitivities requires
an explicit governance decision rather than silently weakening the historical
verifier.

This candidate implements that decision as a **separate opt-in verifier**.
It does not redefine the frozen verifier.

## Frozen equivalence policy

The candidate has no caller-configurable tolerance.

| field | candidate rule | documented cross-stack discrepancy |
| --- | --- | --- |
| `beta` | symmetric `rtol=1e-11`, `atol=1e-20` | max rel `2.8e-12`, max abs `5.9e-21` |
| `sigma` | symmetric `rtol=1e-14`, `atol=1e-15` | max rel `8.2e-16`, max abs `2.2e-16` |
| `cv_mse_by_multiplier` | symmetric `rtol=1e-14`, `atol=0` | max rel `2.6e-15` |
| `final_lambda` | at most 1 float64 ULP | 1 ULP |
| `response_residual_sd` | at most 1 float64 ULP | 1 ULP |
| `mu` | exact | exact historically |
| `decision_gene_mask` | exact | exact historically |
| `multiplier_exponents` | exact | selected grid unchanged |
| `canonical_donor_order` | exact | exact historically |
| selected multiplier index/exponent | exact | `16 / 2.0` exact |
| `final_trace_scale` | exact | no documented cross-stack discrepancy |
| `discovery_age_center` | exact | exact historically |

Before any float comparison, the complete canonical raw discovery provenance
object must match exactly. NaN/Inf is rejected. Shape or key drift is rejected.

The target tolerances are field-specific envelopes above the already documented
cross-stack discrepancies, not a global `allclose`. For arrays the implemented
criterion is symmetric:

`abs(a-b) <= atol + rtol * max(abs(a), abs(b))`

## Decision replay policy

Both terminal strings must match **exactly**. The full `state_primary` key set
must match exactly.

Only `beta`, `hc3_se`, and `t_observed` may differ numerically, each at relative
`1e-12` with zero absolute tolerance, matching the published statement that the
recomputed state primary must agree to roughly `1e-12` relative. Everything
else in `state_primary` is exact: estimability, donor count, permutation count,
model dimensions, residual df, lower/upper p-values, and the serialized null-t
representation. Thus a change in a permutation decision, p-value, estimability,
or terminal cannot be hidden by the float policy.

## Reporting-only sensitivity recovery V2

`t0_sensitivity_recovery_v2.py` reuses the V1 repair that surfaces the two state
sensitivity objects already computed by the frozen adjudicator and omitted from
five return paths. It derives Stage 3's R8 router source and adds exactly two
scoped namespace bindings:

1. repaired reporting surface for `adjudicate_donor_table_non_authoritative`;
2. `verify_target_v2_against_raw` routed to the separately versioned replay
   equivalence verifier.

The wrapper refuses to run unless the original `_adjudicate_from_raw_v2` source
marker, namespace anchor, R8 pretarget authority binding, and R8 preadjudication
authority binding are each present exactly once and in the expected order. It
also requires exactly one target replay verification during the Stage-3 run.
The R8 execution-authority assignments themselves are not replaced.

The V2 output explicitly records:

- `training_authorized: false`;
- `historical_bit_exact_verifier_modified: false`;
- `model_changed: false`;
- `decision_procedure_changed: false`;
- `reporting_surface_changed: true`;
- `discovery_fit_recomputed_for_replay: true`;
- `discovery_target_changed: false`;
- target and decision equivalence reports.

## Test status in the producing lane

Local candidate tests: **19 passed, 0 failed**.
They include failure cases for tolerance overflow, two-ULP drift, NaN, exact-mask
and exact-mu drift, key-set drift, near-zero absolute budget, p-value drift,
terminal drift, missing R8 source markers, duplicate namespace anchors, exact
provenance mismatch, and missing recovered sensitivity objects.

A real sensitivity replay was **not** executed in the producing chat runtime
because the required Stage-3 input packages were not physically present there.
Therefore this candidate makes no claim about recovered sensitivity values.

## Independent-review decision required

Before this can become governance authority, an independent reviewer should:

1. confirm that the tolerance envelopes are sufficiently tight and are not a
   conclusion-dependent escape hatch;
2. confirm that exact fields cover every discrete/terminal decision channel;
3. inspect the namespace derivation and verify the R8 authority routing remains
   intact;
4. run the tests in a clean repository environment;
5. if the exact original numeric stack remains unavailable, run V2 on the exact
   frozen Stage-3 inputs and require both equivalence reports to pass before
   accepting any reporting-only sensitivity output.

No T0 science conclusion is reopened by this candidate.
