# F1 HC3 reusable nuisance admissibility contract

This freezes a cohort-agnostic procedure, not the current cohort's ranks and not a model-selection rule.

For every later lawful donor cohort: (A) rebuild the mandatory nuisance base from that cohort's frozen primitives; (B) recompute source/operator residual spaces; (C) recompute `LOCAL_NUMERICAL_RANK`, `FULL_DESIGN_INCREMENTAL_RANK`, `DONOR_REPLICATED_RANK`, and `HC3_ADMISSIBLE_RANK`; (D) admit a prefix/direction only through the unchanged full-design rank, leave-one-donor-out replication, and HC3 geometry checks. The procedure must not carry forward HVS rank 6, NPH52 rank 1 or 0, SEA-AD rank 4, donor NPH_906, or any current leverage value.

The authoritative numerical rank is computed from the float64 singular values of each actual design matrix X: `tau(X) = max(X.shape) * float64_eps * s_max(X)` and `rank(X) = count(s > tau(X))`. Production leverage is the SVD column-space projection `h_i = sum_j U[i,j]^2` over the retained numerical rank. It must be finite, lie in `[-TOL, 1+TOL]`, and sum to the numerical rank within `TOL`, where `TOL = 100 * n * float64_eps` is recalculated from the current cohort size.

The independent cross-check uses pivoted QR `Q0,R,piv = scipy.linalg.qr(X, mode='economic', pivoting=True)`. QR rank is `count(abs(diag(R)) > max(X.shape) * float64_eps * abs(diag(R))[0])`; an orthonormal basis is rebuilt from `X[:,piv[:rank]]`, and its projection leverage must agree with SVD leverage within `TOL`. Any SVD/QR rank or leverage disagreement is a STOP, not a tuning opportunity.

HC3 is admissible only when constructed columns equal SVD numerical rank, `df=n-rank>0`, all projection invariants hold, every donor deletion preserves rank, and `min(1-h) > sqrt(float64_eps)`. Leverage is never clamped. Normal-equation leverage, pseudoinverse substitution, ridge regularization, donor deletion as repair, and HC0/HC1/HC2 substitution are forbidden.

A `NONREPLICATED_NUISANCE_DIRECTION` in this cohort may become estimable when a larger cohort supplies independent donor replication. A direction estimable here may fail in a larger cohort if new rare operator/source geometry creates a `HC3_DONOR_INDISPENSABLE_DIRECTION`. Measured cohort geometry determines ranks; the algorithm remains frozen. This contract does not authorize automatic model selection.
