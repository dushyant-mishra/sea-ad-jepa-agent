# F1 prospective decision logic

This is executable arithmetic parameterized by the externally frozen query prefix; it has not been applied.

Use alpha 0.05. Donors are the independent units. For any donor vector x with n>=2 and nonzero variance, use the deterministic Student-t interval `mean(x) ± t_(1-alpha/2,n-1)*sd(x)/sqrt(n)`; directional tests use the corresponding one-sided t statistic. No Monte Carlo bootstrap count is introduced.

Primary 60% gate: the two-sided 95% donor interval for overall A must have lower bound >0. Protected family: report all eight program A values, local_core explicit; one-sided positive tests are Holm-corrected across eight. Direct fairness: test `Delta_ctx_minus_direct<0` one-sided and Holm-correct across eight; veto a program only when adjusted evidence rejects zero in the negative direction. A CI spanning zero means no demonstrated degradation, not superiority.

Evidence convergence: the donor OLS slopes defined in the estimand contract require a one-sided t lower bound >0; individual evidence points need not be monotone. Query-identity margins/cross-query correlations require donor lower bounds >0 as veto diagnostics.

An endpoint is inferentially estimable only with at least two independent donors, finite values, nonzero donor variance and full-rank required contrast. Otherwise it is explicitly descriptive/unpowered; no substitute threshold is used.

Nuisance veto: at 60%, fit equal-donor OLS of donor A on an intercept plus deterministically rank-selected centered nuisance columns: source indicators; operator-mixture fractions; recipient physical-support/depth; and correct-minus-null visible-value depth and measured-zero-rate. Columns are considered in lexicographic name order and retained only when they increase numerical rank under `tol=max(X.shape)*float64_eps*largest_singular_value`. Use HC3 covariance and t df=`n-rank(X)`. The centered intercept's lower 95% bound must exceed zero. Rank/df failure, nonpositive adjusted bound, or sign reversal is `STOP_NUISANCE_SHORTCUT`. A column name beginning `protected_` is defined as protected-source leakage and is rejected before fitting. Same-source/operator/support matching remains a design control, not a replacement for this audit.

Qualification also requires legal hashes/firewalls/null bijection, no query leakage, positive primary and evidence-trend gates, both query-identity vetoes, no multiplicity-confirmed protected degradation, and no nuisance veto. Dense programs remain panel-conditioned unless external coverage authority upgrades the claim. Same-source/operator/donor negatives are always reported and can falsify interpretation but do not acquire an outcome-chosen cutoff.

The complete executable path is `scripts/v4/contextual_target_f1_decision_v1.py::qualify`. It fails closed on unestimable overall, protected-family, trend, query-identity, or nuisance quantities. The protected-program positive Holm results are reported but are not converted into an invented all-program success hurdle; the direct negative-tail Holm family is the degradation veto.
