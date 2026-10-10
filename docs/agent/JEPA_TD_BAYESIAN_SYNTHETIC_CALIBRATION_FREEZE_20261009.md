# JEPA TD Bayesian spike — synthetic calibration freeze

Date: 2026-10-09

Status: `SYNTHETIC_CALIBRATION_DESIGN_FROZEN__NO_HISTORICAL_FIT`

Parent contracts:
- `docs/agent/JEPA_TARGET_DISCOVERY_BAYESIAN_SPIKE_PREREG_20261009.md`
- `docs/agent/JEPA_TARGET_DISCOVERY_BAYESIAN_LEDGER_DESIGN_20261009.md`

This freeze is written before opening any synthetic calibration posterior result. It creates no target, stage, representation, G6/G7, TD60, Stage-4, training, or historical-adjudication authority.

Hard terminal remains:
`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

## 1. Synthetic geometry

Synthetic calibration uses the same sparse stage×source observation geometry planned for the historical spike:

- stage `A`: HVS, NPH52, SEA_AD;
- stage `B`: HVS only;
- stage `C`: HVS, NPH52, SEA_AD.

This mirrors the information geometry of TD57B / TD57C / TD59 without using their values or verdict labels.

The seven synthetic observations are already dependency-collapsed stage×source blocks. No panel/split/half pseudo-replicates enter this calibration likelihood.

## 2. Model family

For block margin `y_ts`:

`y_ts ~ StudentT(nu=4, loc=mu_t + beta_s, scale=sigma)`

Priors:

- `mu_t ~ Normal(0, k_mu)`;
- `beta_s ~ Normal(0, k_source)` with a zero-sum centering transform across the three sources;
- `sigma ~ HalfNormal(k_sigma)`.

The source centering constraint prevents the global location from being duplicated between stage and source effects.

Synthetic calibration is dimensionless. Base scale = 1.0.

Three prospectively frozen prior regimes are:

- skeptical: `k_mu=0.5`, `k_source=0.5`, `k_sigma=0.5`;
- reference: `k_mu=1.0`, `k_source=1.0`, `k_sigma=1.0`;
- diffuse: `k_mu=2.0`, `k_source=2.0`, `k_sigma=2.0`.

The historical fit, if later allowed, must derive its dimensional base scale by the preregistered label-blind robust historical margin scale. It may not borrow a synthetic outcome magnitude.

## 3. Deterministic posterior engine

Calibration will use a dependency-free seeded random-walk Metropolis sampler implemented only with NumPy/math.

Frozen sampler settings:

- chains: 4;
- seeds: `2026100901`, `2026100902`, `2026100903`, `2026100904`;
- draws/chain: 12,000;
- burn-in/chain: 4,000;
- thinning: 4;
- retained posterior draws total: 8,000;
- proposal adaptation occurs during burn-in only, targeting acceptance 0.20–0.50;
- no adaptation after burn-in;
- initialization at zero stage/source effects and log-sigma 0;
- numerical failure/non-finite density is a calibration failure.

The sampler is a method-spike implementation, not production Bayesian infrastructure.

## 4. Primary posterior summaries

For each stage `t`:

- `P(mu_t > 0)`;
- median and central 90% interval of `mu_t`;
- posterior predictive `P(y_new_source,t > 0)` where a new source effect is drawn from the fitted source-effect empirical posterior geometry and Student-t residual noise is added.

For the observed-source set:

- posterior source-effect spread;
- posterior predictive sign-consistency across three synthetic new source draws.

No target-level quantity exists.

## 5. Frozen synthetic scenarios

All scenarios use fixed, exact seven block values. No random data generation is used for primary pass/fail calibration, so reruns are byte-stable.

### S0 — null

All seven block margins = `0.0`.

Purpose: a null must not generate strong positive replication confidence.

### S1 — one-source-only signal

HVS blocks for A/B/C = `+2.0`; NPH52 and SEA_AD blocks for A/C = `0.0`.

Purpose: a source-specific positive effect must not be mistaken for stage-general replication.

### S2 — duplicate attack

Start from S0, then present 20 exact duplicate copies of every HVS case identity to the *ledger layer*.

Purpose: the dependency ledger must reject duplicate identities before posterior fitting. There is no Bayesian tolerance for this scenario; accepting the duplicated ledger is failure.

### S3 — sign-flipping sources

For stages A and C:
- HVS `+2.0`;
- NPH52 `-2.0`;
- SEA_AD `+2.0`.

Stage B HVS = `+2.0` because B has no other source by design.

Purpose: source heterogeneity must prevent a confident source-general interpretation for A/C despite two positive sources.

### S4 — genuinely shared positive signal

All seven block margins = `+2.0`.

Purpose: the model must recover a clearly shared positive effect for stages with multi-source evidence.

Stage B remains one-source-only and is **not** required to satisfy the same source-general criterion as A/C.

## 6. Frozen acceptance criteria

All criteria are evaluated in the **reference prior** unless a criterion explicitly concerns prior sensitivity.

### C0 — null calibration

For each stage A/B/C:

- `P(mu_t > 0)` must lie in `[0.35, 0.65]`.

No stage may have posterior predictive positive probability > `0.75`.

### C1 — one-source-only resistance

For multi-source stages A and C under S1:

- `P(mu_t > 0) < 0.90`; and
- posterior predictive positive probability for a new source `< 0.80`.

Stage B is excluded from this source-general criterion because its design contains only HVS.

### C2 — duplicate resistance

The ledger must reject S2 before the sampler is invoked with terminal/error containing `duplicate case identity`.

### C3 — sign-flip heterogeneity

For stages A and C under S3:

- posterior predictive positive probability for a new source `< 0.85`; and
- the 90% posterior interval for `mu_t` must include `0` **or** `P(mu_t > 0) < 0.95`.

This intentionally does not require the latent stage mean to be negative; it requires uncertainty/heterogeneity to block near-certain replication.

### C4 — shared-positive recovery

For stages A and C under S4:

- `P(mu_t > 0) > 0.95`; and
- posterior predictive positive probability for a new source `> 0.85`.

No equivalent source-general PASS is required for stage B because only one source is observed in the frozen geometry.

### C5 — prior sensitivity

Run S0–S4 under all three prior regimes.

For the decision-bearing qualitative classifications above (null not strongly positive; one-source-only not source-general; sign-flip not near-certain; shared positive recovered), skeptical/reference/diffuse priors must agree.

If any qualitative calibration classification changes across the three prior regimes, calibration terminal is:

`PRIOR_SENSITIVE`

rather than PASS.

## 7. MCMC quality floor

Because this is a small exploratory Metropolis implementation, the calibration receipt must report per-chain acceptance and split-chain consistency diagnostics.

Frozen minimums:

- each retained chain acceptance fraction in `[0.10, 0.70]`;
- no parameter may have split-Rhat > `1.10` using the four retained chains;
- effective sample size is reported but not used as a post-hoc tuning lever; if bulk ESS < 200 for any stage effect, calibration is `SAMPLER_NOT_ESTIMABLE`.

No chain length, proposal scale, burn-in or threshold may be changed after seeing a failed scientific scenario without a new prospective calibration freeze.

## 8. Calibration terminal

PASS requires all S0–S4 criteria, all three prior regimes, and sampler quality floors.

PASS terminal:
`PASS_TD_BAYESIAN_SYNTHETIC_CALIBRATION__HISTORICAL_FIT_STILL_NOT_AUTHORIZED`

Other allowed terminals:
- `PRIOR_SENSITIVE`;
- `SAMPLER_NOT_ESTIMABLE`;
- `FAIL_TD_BAYESIAN_SYNTHETIC_CALIBRATION`.

Even a calibration PASS does **not** authorize the historical fit until exact TD57C case values are authenticated and the ledger receipt is complete.

## 9. Anti-tuning rule

Historical TD57B/TD57C/TD59 values and PASS/FAIL labels may not be inspected to alter:

- scenario values;
- prior multipliers;
- MCMC settings;
- posterior thresholds;
- predictive thresholds;
- source-general reporting rules.

If the frozen calibration fails, report the failure. A revised method requires a new prospective freeze and must not be tuned until it recreates desired historical conclusions.
