# JEPA formulas and authority ledger — FINAL R4 — 2026-09-09

## Population target and proposal correction
For cell i belonging to eligible donor d with n_d eligible cells and D eligible donors:
`p_i = 1/(D*n_d)`.
D and n_d are derived from the authenticated reader-fit ledger, not typed as constants.
If the presentation proposal is q_i, use exact correction `w_i=p_i/q_i`.

## Full-coverage schedule
Let m_i be the integer presentation multiplicity for cell i.
`H = Σ_i m_i`.
`A = Σ_i 1/(D^2*n_d^2*m_i)`.
`ESS_fraction = 1/(H*A)`.

Under full unique-cell coverage and a maximum multiplicity C:
`conditioning_ratio >= n_max/(n_min*C)`.
For a prospectively supplied conditioning ceiling R:
`C_min = ceil(n_max/(R*n_min))`.

Current cap32 V3 candidate: H=5,267,086, ESS=0.5000000953357726, H-1 fails, conditioning ratio=58037/864=67.17245370370371.
Conditional 64× diagnostic: cap34 is the smallest compatible integer cap; cap33 fails.

## Deterministic presentation order
`slot=(a*presentation_index+b) mod H`, requiring `gcd(a,H)=1`.
Current V3: H=5,267,086, a=2,340,573, b=5,029,443.

## Relational capacity
For an anchor in a same-group population of size n, comparator-pair capacity:
`C(n-1,2)=(n-1)(n-2)/2`.
Total ordered-anchor triplet capacity:
`n(n-1)(n-2)/2`.
Capacity is availability, not scientific mass.

## EMA
Time unit = successful scientific base presentations.
For m successful presentations in an update and half-life h:
`momentum = 2^(-m/h) = exp(log(0.5)*m/h)`.
Candidate scaling form:
`h = ceil(coverage_lower_bound*smoothing_multiple)`.
Numeric h remains unfrozen.

## Singleton-query Monte-Carlo precision
Finite-population family bound:
`B(N,q,w)=w^2*(N-q)/(q*(N-1))`.
For each total Q, choose positive q_common+q_native=Q minimizing the two-family sum per operator; choose the smallest Q whose worst operator meets a prospectively supplied risk fraction.
Current 5% candidate: Q=21 passes at 0.0476703666914567; Q=20 fails at 0.05006881843151968.

## Support-family mass
Under target p:
`family_mass_f = E_p[addresses in family f] / E_p[total measured addresses]`.
Current candidate: COMMON_CORE=0.607055395953596; OPERATOR_NATIVE=0.392944604046404.

## Dimension hierarchy
`D_total = D_shared + D_private`.
D_obs is separate measurement-state rank.
d_gene is neural/token capacity, not biological rank.
Historical 5/96/160/224/320/512 are not production D authority.

D_shared qualification must combine full-refit matched-null separation, donor-resampled subspace stability, held-donor predictability, independent-view/sketch agreement, contiguous-prefix selection, and increment beyond frozen measurement-shortcut baselines.
D_private must add held-donor/held-operator prediction of common-core biology beyond D_shared while surviving measurement-shortcut and same-cell intervention tests.

## T0 primary
`p_upper=0.021 < alpha=0.025`.
`beta=124.94507515835764`.
`HC3_SE=65.48932245523241`.
`t=1.9078694125102356`.

## T0 QC diagnostic
`corr(Q_DEPTH,Q_DETECT)=0.9232`.
Condition number: 310.6 → 37,671 after adding both.
Residual unique variance fractions: Q_DEPTH≈0.087, Q_DETECT≈0.096.

## C2 successful update chain
`FP16_FORWARD → BACKWARD_AUTOCAST_DISABLED → UNSCALE → PROTECTED_48_GRADIENT_GATE → OPTIMIZER_STEP_PROVED_BEYOND_DECAY → ADAM_EXP_AVG_PROVED → ADAM_EXP_AVG_SQ_PROVED → EMA_UPDATE → SUCCESSFUL_PRESENTATION_CURSOR_ADVANCE → ATOMIC_CHECKPOINT_TELEMETRY_COMMIT`.

All formulas are authority-dependent and do not independently authorize training.
