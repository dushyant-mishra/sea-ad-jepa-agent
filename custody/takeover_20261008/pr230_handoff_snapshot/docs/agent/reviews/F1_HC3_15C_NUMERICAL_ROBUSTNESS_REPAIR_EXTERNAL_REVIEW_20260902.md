# F1 HC3 15C Numerical Robustness Repair — External Review — 2026-09-02

## Verdict

`PASS_F1_HC3_15C_NUMERICAL_ROBUSTNESS_REPAIR_EXTERNAL_REVIEW`

Reviewed final commit: `5e8127d360d1effd0867a73c2bb007ddffb2c901`.

The prior blocker `STOP_F1_HC3_15C_NUMERICAL_INDEPENDENCE_UNRESOLVED` is resolved at its synthetic-only scope. This PASS does not authorize real F1 because a separate pre-result evidence-trend arithmetic defect remains open.

## Accepted repair

- Repair package manifest SHA-256: `f7cc3be9340c817f57953d3ef009c568a57dca7ea4fffbc2ccefbe6266e123a5`.
- Prospective repair contract SHA-256: `4ece6ea2fb85dad49e91d2087f6ce8d16941deb0e9c3226209add66057c2a3c7`.
- Prospective tolerance authority SHA-256: `3c504c94ed08c45a1b4ac634ddbe54b3a7fc0cddd9948ce781fa7f49da01c49a`.
- Frozen selected nuisance design remains `(5,0,4)`, 104 x 16, rank 16, df 88.
- Frozen effective centered design remains SHA-256 `37653ed4a21f513a7389630bffa7447f9022323e8240bb80f53394138f1917eb`.
- Production HC3 uses reduced QR plus triangular solves and orthonormal-basis leverage; it does not form or invert `X.T @ X` and has no ridge/pseudoinverse fallback.
- Independent validation uses thin SVD plus an explicit pseudoinverse and SVD-basis leverage; it does not import the production QR helper.
- Baseline QR-versus-SVD maximum differences are leverage `6.661338147750939e-16`, beta0 `5.551115123125783e-17`, SE `4.5146178462296405e-14`, and lower CI `8.970602038971265e-14`, all within the prospectively frozen tolerances.
- Prospective near-boundary fixture outcomes agree exactly: positive `+1e-5` lower-bound target passes in QR and SVD; negative `-1e-5` target vetoes in QR and SVD.
- The frozen 14-case decision truth table and the 15C adversarial suite pass, including design mutation, donor population/order/API, legal-domain, zero-variance and source-confined checks.
- The repair is additive: frozen decision-v1, decision-v4 and integration-v4 Git blobs remain unchanged.
- Real reader/forward authority remains unset. No expression, real F1 outcome, model/checkpoint tensor, training, optimizer, EMA, DEV, SEALED or pathology access is authorized by this PASS.

## Separate remaining blocker

Current decision-v4 still delegates evidence-trend arithmetic to historical decision-v1 `evidence_slopes()`:

`x = evidence - mean(evidence)` followed by `(y @ x) / (x @ x)` for evidence `(0.2,0.4,0.6,0.8,1.0)`.

In float64 the centered evidence vector does not sum to exact zero, so a mathematically flat donor evidence curve can acquire a tiny nonzero slope. Because the evidence-trend lower one-sided confidence bound is decision-bearing, this must be repaired prospectively before real F1.

The algebraically identical stable slope for the frozen five-point evidence grid is:

`(A100 - A20) + 0.5 * (A80 - A40)`.

## Next allowed scientific work

One narrow synthetic-only evidence-trend numerical repair:

1. Preserve historical decision-v1, decision-v4, integration-v4, accepted 15C and HC3-repair bytes unchanged.
2. Freeze the evidence-slope repair contract and any comparison tolerance before implementation/result comparison.
3. Add a superseding current decision layer/version; do not edit historical v1/v4 in place.
4. Replace only evidence-slope arithmetic with the paired-difference identity above.
5. Keep evidence levels, alpha, tails, one-sided gate, donor population, protected programs, HC3, query design, matched null, QID logic, multiplicity, legal gate and claim scope unchanged.
6. Add exact-flat, positive-linear, negative-linear, near-zero positive/negative, nonfinite and zero-donor-variance tests.
7. Re-run the frozen decision truth table, HC3 15C regressions and all currently accepted synthetic/adversarial regressions.
8. Independently reconstruct the complete gate vector and prove all non-evidence-trend gates/reports are unchanged.
9. Require fresh external review before reader/forward/executor preflight.

## Still forbidden

- real F1 model-forward sweep or real outcome adjudication;
- setting real reader/forward authority;
- training/finetuning/optimizer/checkpoint/EMA work;
- DEV/SEALED/pathology access;
- nuisance-design reselection or HC3 frontier reopening;
- D_shared rescue/re-entry.
