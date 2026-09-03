# F1 HC3 15C Numerical Robustness Repair Contract

Date: 2026-09-02

Status: prospective, synthetic-only, frozen before implementation and before numerical comparison results.

## Scope and immutable scientific semantics

This repair addresses only `STOP_F1_HC3_15C_NUMERICAL_INDEPENDENCE_UNRESOLVED`. It does not address the separate evidence-slope issue and cannot authorize real F1.

The following are unchanged:

- donor outcome: the 104-donor `overall_A` endpoint at 60% evidence;
- selected nuisance triple: `(5,0,4)`;
- donor order from the frozen selected-design schema;
- effective design: intercept unchanged, every retained non-intercept selected column mean-centered exactly as in frozen 15C;
- HC3 estimator and two-sided 95% Student-t interval;
- rank `16`, residual degrees of freedom `88`, and the strict gate `lower > 0`;
- fail-closed behavior for nonfinite inputs, rank deficiency, nonpositive df, leverage singularity, and zero or nonfinite standard error;
- all non-HC3 v4 gates, endpoints, estimands, multiplicity rules, and claim scope.

Forbidden changes include ridge or other regularization, leverage clamping, epsilon qualification gates, altered alpha or tail, donor deletion, nuisance reselection, or any change to frozen v1/v4/15A4/15B/15C historical bytes.

## Frozen authorities

- Raw selected design SHA-256: `5d2fda2e81a6edd63241ccf996fe0e5086275233e765daae19509be24cd518e3`
- Selected-design schema SHA-256: `d7d0be302b455f7be0982d3e7906778c4fac59aee9b9f5c43e6017090d25e778`
- Effective centered design SHA-256: `37653ed4a21f513a7389630bffa7447f9022323e8240bb80f53394138f1917eb`
- Shape: `104 x 16`; rank: `16`; df: `88`; leave-one-donor rank stable: `104/104`
- Frozen decision-v1 Git-blob SHA-256: `204859f48b96d1bb268d9249596b801537f2c911183dc4a20bc30fe5683e2d34`
- Frozen decision-v4 Git-blob SHA-256: `5215faffe1e90b6567054fd7fb4d62d501787dbacd704e09ff28af9c65d45913`
- Frozen integration-v4 Git-blob SHA-256: `5dfd5858f1e8865f871b633a033e400f2d7fb5e2fb52bebbc613f7efed1bce2a`
- Frozen truth-table SHA-256: `76d420a0aa71f9b062b7394453f1f33282f7c78a956fc950fceb7ead682dcf5e`

## Conclusion-bearing production method: QR

For the frozen effective design `X = QR` in reduced QR form:

1. `beta = solve_triangular(R, Q.T @ y)`.
2. `h_i = sum(Q[i,:]^2)`.
3. `r = y - X @ beta` and `u = r / (1-h)`.
4. `Xplus = solve_triangular(R, Q.T)`.
5. `cov = (Xplus * u[None,:]) @ (Xplus * u[None,:]).T`.
6. The intercept standard error, two-sided 95% Student-t interval with df 88, and strict `lower > 0` gate follow from that covariance.

The production route must not form or invert `X.T @ X`, use a normal-equations solve or leverage calculation, or use ridge/pseudoinverse fallback.

## Independent method: SVD/pseudoinverse

The independent validator must not import the production QR helper. It computes `X = U diag(s) V.T`, reconstructs `Xplus = V diag(1/s) U.T`, obtains leverage from `sum(U^2, axis=1)`, and independently computes beta, residuals, HC3 covariance, intercept standard error, interval, and gate. It may not copy the production QR arithmetic.

## Prospective comparison authority

- Rank, df, donor order, raw design SHA, and effective design SHA must agree exactly.
- Estimability and gate booleans must agree exactly; no numerical tolerance can excuse a gate disagreement.
- Maximum absolute leverage difference must not exceed `2.3092638912203256e-12`.
- For beta0, standard error, lower CI, and upper CI, the absolute tolerance is `100 * eps_float64 * kappa2(X) * max(1, max(abs(y)))`.
- `kappa2(X)` is computed once from the frozen effective design and recorded in the separately hashed tolerance authority before any QR/SVD comparison is run.

## Frozen synthetic and adversarial scope

The repair reruns the existing all-pass baseline, isolated HC3 veto, zero-variance/non-estimable case, wrong design bytes, wrong triple, donor permutation/omission/duplicate/relabel, forbidden NPH C1, forbidden HVS C6, old rank-18 design, NaN/nonfinite, source-confined case, strict legal-domain attacks, forged caller HC3 PASS, and all prior complete decision regressions.

Two prospective near-boundary donor vectors are constructed from the already-frozen synthetic baseline `overall_A`. Using the independent SVD reference lower bound `L0`, the positive vector is `y + (1e-5 - L0)` and the negative vector is `y + (-1e-5 - L0)`. Both vectors must be materialized and hash-bound before the production QR comparison. Because the design has an intercept, residuals and HC3 standard error must remain invariant while beta0 and interval bounds shift by the constant. The positive fixture must pass and the negative fixture must veto in both implementations.

## Firewall and terminal state

No expression, model/checkpoint tensor, real F1 outcome, DEV, SEALED, pathology, training, optimizer, checkpoint write, or EMA access is permitted. Real reader/forward authority remains unset. Historical decision and integration sources remain byte-identical.

Local PASS can terminate only as `PASS_F1_HC3_15C_NUMERICAL_ROBUSTNESS_REPAIR_AWAITING_EXTERNAL_REVIEW`. It does not authorize real F1 or any later scientific gate.
