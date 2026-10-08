# F1 Evidence-Trend Numerical Repair Contract

Date: 2026-09-02
Status: prospective, synthetic-only, frozen before implementation and before repair comparison outputs.

## Scope

This contract addresses only `STOP_F1_EVIDENCE_TREND_NUMERICAL_DEFECT_UNRESOLVED`.

It does not authorize real F1, reader/forward execution, biological outcome adjudication, training, checkpoint writes, optimizer steps, EMA updates, DEV/SEALED/pathology access, nuisance reselection or reopening any closed branch.

## Defect being repaired

Historical `scripts/v4/contextual_target_f1_decision_v1.py::evidence_slopes()` computes the slope for evidence fractions `(0.2,0.4,0.6,0.8,1.0)` by float64 centering of the evidence vector and a dot product. Current frozen-base `contextual_target_f1_decision_v4.py` delegates the decision-bearing evidence-trend endpoint to that historical helper.

Because the float64 centered evidence vector does not sum to exact zero, a mathematically flat donor evidence curve can acquire a tiny nonzero slope. This is decision-bearing because qualification requires the one-sided lower confidence bound for donor slopes to be strictly greater than zero.

## Frozen scientific/statistical semantics

The following must remain unchanged:

- evidence levels exactly `(0.2,0.4,0.6,0.8,1.0)` in that order;
- 104 donor decision population;
- Student-t donor inference and `ALPHA=0.05`;
- the evidence-trend gate remains one-sided and strict: `lower_one_sided > 0`;
- all protected programs, Holm families, QID endpoints, draw-sign rule, cross-source rule, legal-provenance rule, claim scope and program estimand;
- frozen F1 query/population design, matched-null semantics and aggregation;
- accepted HC3 selected nuisance triple `(5,0,4)`, effective design and externally accepted QR/SVD numerical repair;
- all historical decision-v1, decision-v4, integration-v4, 15A4, 15B, historical 15C and HC3-repair bytes.

No epsilon qualification gate, threshold relaxation, alpha/tail change, donor deletion, evidence-level change, clipping, ridge, hidden fallback or reinterpretation of zero variance is permitted.

## Conclusion-bearing repaired slope

For a donor evidence row `A=[A20,A40,A60,A80,A100]`, the only authorized production slope is the algebraically identical five-point OLS identity:

`beta = (A100 - A20) + 0.5 * (A80 - A40)`

`A60` has zero coefficient under the frozen symmetric evidence grid and must not be given a nonzero coefficient.

The implementation must operate in float64, require exactly five finite values, and fail closed on malformed/nonfinite input.

## Independent numerical reference

The independent validator must not import the repaired production slope helper.

For each float64 donor row it must reconstruct the same linear functional independently using a different accumulation route, preferably `math.fsum` over the coefficient terms `[-A20, -0.5*A40, 0.5*A80, A100]` or an exact/high-precision Decimal reconstruction from the input floats.

The independent path must verify the exact coefficient vector `[-1,-0.5,0,0.5,1]` and must not call historical `v1.evidence_slopes()` as its reference.

## Prospective numerical comparison discipline

- Exact-flat rows with all five stored float64 values identical must produce production slope exactly `0.0` and independent-reference slope exactly `0.0`.
- For finite non-flat rows, production/reference scalar agreement is checked under the separately frozen tolerance authority.
- No tolerance can excuse a sign disagreement for a nonzero reference slope.
- No tolerance can excuse an evidence-trend gate disagreement.
- Zero donor variance remains non-estimable under the existing frozen `t_interval` semantics; it must not be converted into a PASS.

## Superseding decision layer

Do not edit historical decision-v1 or decision-v4 in place.

Add a new superseding current decision version/layer that:

1. obtains the frozen-base decision-v4 result;
2. recomputes donor evidence slopes with the repaired production function;
3. recomputes only `reports["evidence_slope"]` and `gates["evidence_trend_one_sided_positive"]`;
4. recomputes `qualified = all(gates.values())`;
5. proves every non-evidence-trend gate is exactly unchanged;
6. proves every non-evidence-trend report is exactly unchanged;
7. records that legacy v1 evidence-slope arithmetic is nonauthoritative for the superseding layer.

The accepted additive HC3 repair remains conclusion-bearing for HC3; this repair must not revert to the historical normal-equations HC3 route.

## Required synthetic/adversarial tests

At minimum:

1. exact-flat rows at several levels including `1.0`, `0.28`, `0.0`, and a negative finite level: repaired slope exactly zero;
2. positive linear evidence curves with known donor slopes;
3. negative linear evidence curves with known donor slopes;
4. donor-varying positive-trend case that passes the frozen one-sided gate;
5. donor-varying negative-trend case that vetoes;
6. prospective near-boundary positive and negative trend-gate fixtures with exact gate agreement between production and independent adjudication;
7. NaN/+inf/-inf/malformed evidence rows fail closed;
8. zero donor variance in slopes is non-estimable and vetoes;
9. exact 104-donor population and evidence shape enforcement;
10. all frozen 14-case decision truth-table regressions;
11. all accepted 15C/HC3 synthetic/adversarial regressions relevant to decision semantics;
12. a deliberately flat-but-donor-level-varying fixture demonstrating that historical v1 can emit tiny donor-dependent nonzero slopes while the repaired function returns exact zeros and the current gate fails closed rather than spuriously passing.

## Complete independent adjudication

A separate validator must reconstruct the complete current gate vector using the repaired evidence slope and the accepted HC3 repair authority. It must show:

- every non-evidence-trend gate exactly matches the superseding production decision;
- the evidence-trend gate exactly matches;
- final `qualified` exactly matches;
- all non-evidence-trend report semantics remain unchanged;
- no caller-supplied evidence-trend PASS/authority field can override recomputation.

## Required repair package

The synthetic-safe repair package must contain at minimum:

1. repair contract binding;
2. numerical tolerance authority binding;
3. historical-authority hash binding;
4. production repaired-slope source snapshot;
5. superseding decision-layer source snapshot;
6. independent validator source snapshot;
7. exact-flat/linear/near-boundary fixture bindings;
8. production-versus-independent numerical comparison;
9. complete gate-vector reconstruction comparison;
10. frozen decision/15C/HC3 regression results;
11. firewall audit;
12. source manifest and package manifest/root;
13. external-review handoff.

## Terminal state

Local success may terminate only as:

`PASS_F1_EVIDENCE_TREND_NUMERICAL_REPAIR_AWAITING_EXTERNAL_REVIEW`

That terminal does not authorize reader/forward/executor preflight or real F1 until fresh external review explicitly promotes the repair.
