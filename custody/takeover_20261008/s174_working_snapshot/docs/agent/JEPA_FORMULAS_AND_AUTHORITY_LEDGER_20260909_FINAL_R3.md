# JEPA formulas and authority ledger — FINAL R3 — 2026-09-09

`p_i = 1/(D*n_d)`; exact proposal correction `w_i=p_i/q_i`.

Relational comparator pairs for anchor in group n: `C(n-1,2)=(n-1)(n-2)/2`; total anchor-triplet capacity `n(n-1)(n-2)/2`. Capacity is availability, not scientific mass.

Schedule: `A=Σ_i 1/(D^2*n_d^2*m_i)`, `H=Σ_i m_i`, `ESS_fraction=1/(H*A)`.

Full-coverage conditioning lower bound: `ratio>=n_max/(n_min*C)`. Conditional minimum cap for supplied ceiling R: `C_min=ceil(n_max/(R*n_min))`.

Deterministic scientific order: `slot=(a*presentation_index+b) mod H`, with gcd(a,H)=1.

EMA per successful update: `momentum=2^(-m/h)=exp(log(0.5)*m/h)`; candidate rule `h=ceil(coverage_lower_bound*smoothing_multiple)`; numeric h unfrozen.

Singleton-query finite-population bound: `B(N,q,w)=w^2*(N-q)/(q*(N-1))`; choose positive `q_common+q_native=Q` minimizing two-family sum per operator, then smallest Q meeting supplied risk bound. Current 5% candidate Q=21; Q=20 fails.

Support-family mass is derived under donor-equal target: `family_mass_f=E_p[addresses in family f]/E_p[total measured addresses]`. Current candidate COMMON_CORE=0.607055395953596; OPERATOR_NATIVE=0.392944604046404.

`D_total=D_shared+D_private`; D_obs is separate measurement-state rank; d_gene is neural capacity, not biological D. Historical 5/96/160/224/320/512 are not production D authority.

T0 primary: p_upper=0.021 vs alpha=0.025; beta=124.94507515835764; HC3_SE=65.48932245523241; t=1.9078694125102356.

T0 QC diagnostic: corr(Q_DEPTH,Q_DETECT)=0.9232; condition number 310.6 -> 37,671 with both QC; residual unique variance fractions ~0.087 and ~0.096.

C2 successful chain: `FP16_FORWARD → BACKWARD_AUTOCAST_DISABLED → UNSCALE → PROTECTED_48_GRADIENT_GATE → OPTIMIZER_STEP_PROVED_BEYOND_DECAY → ADAM_EXP_AVG_PROVED → ADAM_EXP_AVG_SQ_PROVED → EMA_UPDATE → SUCCESSFUL_PRESENTATION_CURSOR_ADVANCE → ATOMIC_CHECKPOINT_TELEMETRY_COMMIT`.

All formulas are candidate/authority-dependent as described in the handoff; none independently authorizes training.
