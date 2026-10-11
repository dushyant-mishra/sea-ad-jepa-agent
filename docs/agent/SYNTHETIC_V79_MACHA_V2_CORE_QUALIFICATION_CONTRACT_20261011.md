# Macha execution contract — V79 V2_CORE synthetic qualification — 2026-10-11

This is the only authorized next Macha task for the **synthetic/V79 Bayesian geometry lane**. Target discovery remains separate.

## Start state

Controller terminal:
`CANDIDATE_V2_CORE_FROZEN_FOR_NEW_SYNTHETIC_QUALIFICATION__OPERATOR_EXTENSION_RETURNED_TO_DEVELOPMENT__EXACT_S174_REPLAY_COMPLETE__BAYESIAN_REAL_TRAIN_INFERENCE_OFF__FACTORIAL_SCIENCE_OFF__TRAINING_OFF`

Read first:
- PR #261 canonical handoff
- PR #260 audit
- PR #283 operator repair implementation
- PR #285 completed exact-S174 replay
- PR #285 controller freeze comment `6113335756`
- `docs/agent/V79_BAYESIAN_GEOMETRY_CONTROLLER_STATE_20261011.json`
- `docs/agent/SYNTHETIC_V79_NEW_AGENT_TAKEOVER_HANDOFF_20261011.md`

## Frozen V2_CORE structure

### Detection, per gene

`detected ~ quadratic(log_library) + broad_class + source + donor_within_source`

### Positive magnitude, per gene

`log(count) | count>0 ~ Normal(quadratic(log_library) + broad_class + source + donor_within_source, sigma)`

Frozen structural decisions:
- quadratic depth IN
- broad class IN
- source IN
- donor-within-source IN, hierarchical / partially pooled
- operator OUT of core
- donor×class OUT
- source×class OUT
- free matrix/dataset identity OUT
- modular per-gene fitting
- across-gene geometry second-stage
- lognormal = current positive-family qualification family
- ZTNB = separate unresolved challenger

Do not add operator to V2_CORE during this qualification cycle.

## Immediate deliverable — before expensive fitting

Commit:
`V79_V2_CORE_FROZEN_MODEL_AND_PROSPECTIVE_SYNTHETIC_QUALIFICATION_CONTRACT`

The commit must freeze, before any qualification result is read:
1. exact Bayesian model code/config
2. exact priors
3. exact centered/non-centered parameterization choices
4. exact synthetic-world generator/config
5. scenario truth table
6. scenario IDs and fresh seeds
7. metrics
8. pass/fail thresholds
9. absent-effect false-positive rules
10. sampler retry / extension policy
11. chains / warmup / draws / target_accept path
12. environment/package lock
13. CPU/resource limits
14. result schema
15. combined terminal receipt logic

Report that contract commit and stop if any of those pieces remain unspecified.

## Priors and parameterization

Priors may be informed by already-permitted empirical TRAIN development summaries, but must be fixed before qualification outcomes.

At minimum freeze priors for:
- detection intercept
- positive intercept
- linear depth
- quadratic depth
- broad-class contrasts
- source contrasts
- donor SD and donor latent effects
- positive sigma
- second-stage across-gene geometry parameters

Use constrained contrasts where needed to remove redundant location degrees of freedom.

Default expectation:
- standardized depth
- non-centered donor hierarchy where appropriate
- no deep monolithic cross-gene NUTS hierarchy
- modular gene fits
- second-stage across-gene geometry

Any centered choice must be justified prospectively.

## Required fresh qualification worlds

The world manifest must be committed before results and must use new seeds/scenario IDs not used in old Bernoulli/Gaussian/lognormal/ZTNB recovery, the auxiliary tournament, or exact S174 replay.

Required worlds:

### Q0 BASELINE
Ordinary supported depth + class + source + donor effects.

### Q1 WEAK_DONOR
Low but nonzero donor variance.

### Q2 STRONG_DONOR
High supported donor variance.

### Q3 WEAK_SOURCE
Small nonzero source effect.

### Q4 SOURCE_ABSENT
True source effect exactly zero. Must test false-positive control.

### Q5 CLASS_ABSENT
True broad-class effect exactly zero.

### Q6 QUADRATIC_DEPTH_ABSENT
Linear depth present, quadratic term exactly zero.

### Q7 DONOR_ABSENT
True donor variance exactly zero.

### Q8 SPARSE_DETECTION_STRESS
Low-prevalence genes / strong zeros generated from V2_CORE itself.

### Q9 POSITIVE_MAGNITUDE_TAIL_STRESS
High sigma / broader positive log-count variation within the frozen lognormal family.

### Q10 REALISTIC_WEAK_CROSSING_STRESS
Imbalanced donor/source/class design resembling corrected S174 crossing/group-size difficulty.

### Q11 OMITTED_OPERATOR_MISSPECIFICATION_STRESS
Generate a small prospectively fixed operator-like perturbation but do **not** fit operator. Purpose: test whether V2_CORE falsely reallocates omitted measurement structure into donor/source/class.

Q11 is a robustness world only. It does not authorize an operator term.

## Qualification metrics

Freeze exact metrics before outcomes.

### Fixed / continuous effects
For depth, class and source as applicable:
- bias
- RMSE / absolute error
- interval coverage
- sign recovery
- true-vs-posterior effect correlation where meaningful

### Donor hierarchy
- donor SD recovery
- donor-effect correlation/rank where meaningful
- interval coverage
- shrinkage behavior
- absent-donor false-positive control in Q7

### Detection predictive behavior
- held-out Bernoulli log loss
- calibration
- prevalence reproduction
- zero fraction vs depth
- prevalence by broad class/source
- low-prevalence stress behavior

### Positive magnitude
- held-out positive-count log predictive density
- positive log-count mean / variance reproduction
- upper-tail reproduction
- sigma recovery

### Posterior predictive checks
At minimum:
- zero fraction
- zero fraction vs depth
- broad-class prevalence
- source prevalence
- positive mean vs depth
- positive variance
- donor heterogeneity

## Qualification thresholds

Do not inherit thresholds automatically from the old model. Freeze a V2_CORE-specific contract before results.

The contract must state:
- maximum R-hat
- minimum ESS
- divergence tolerance
- interval-coverage requirement
- effect-recovery tolerance
- absent-effect false-positive tolerance
- required PPC adequacy
- required scenario-level and combined-family pass logic

Thresholds cannot be relaxed after a failure.

## Sampler recovery path

Freeze allowed recovery behavior before results. Example acceptable shape:
1. primary target_accept
2. one predefined target_accept escalation only for divergence-triggered failure
3. one predefined same-model extension for ESS/R-hat miss if allowed
4. otherwise terminal FAIL for that scenario/family

Record every attempt:
- scenario/seed
- code/config hash
- chains
- warmup
- draws
- target_accept
- divergences
- worst R-hat
- minimum ESS
- retry/extension status
- elapsed time
- resource use when available

No post-outcome parameterization redesign inside the same confirmatory cycle.

## Resource rules

Heavy fit defaults:
- maximum concurrent heavy fits = 1
- settle interval = 120 s
- no Windows + WSL heavy Bayesian fits in parallel
- compact synthetic arrays only; no 41K matrix reconstruction
- checkpoint each scenario/result immediately
- free state before next heavy job

The historical bottleneck is CPU saturation, not S174 disk size.

## Positive-family boundary

For this qualification generation, the positive part is **lognormal**.

Do not run ZTNB head-to-head during the qualification and then select the winner. ZTNB requires a separate prospective comparison if pursued later.

A V2_CORE lognormal qualification pass means the frozen V2_CORE lognormal model recovers its declared structure; it does not establish global optimality versus every count family.

## Operator boundary

Operator is not part of V2_CORE.

Exact S174 showed:
- detection fixed proxy `PRIOR_SENSITIVE__UNRESOLVED`
- positive fixed proxy `NOT_SUPPORTED`
- donor-controlled residual operator organization present

Therefore operator is a separate development extension. Do not use Q11 as a reason to fit operator in the core.

## Required outputs

Commit before execution:
- frozen model/config
- frozen priors
- frozen world manifest/truth table/seeds
- thresholds
- sampler recovery policy
- environment/resource policy
- result/receipt schemas

For every world commit machine-readable:
- truth
- posterior summaries
- diagnostics
- recovery metrics
- absent-effect control results
- PPCs
- pass/fail ruling
- exact code/config/environment hashes
- resource record

At the end produce one combined terminal V2_CORE qualification receipt.

No selective scenario promotion.

## Stop rules

If a frozen qualification criterion fails after the allowed recovery path:
- mark the generation FAILED / NOT_QUALIFIED;
- do not tune within that cycle;
- stop for controller review.

A later model redesign is allowed only as a new development generation with a new untouched qualification suite.

If all worlds PASS:
- stop;
- do not run corrected-TRAIN posterior inference automatically;
- do not export posterior geometry;
- do not alter H1/H2/H3;
- do not run factorial science;
- do not train JEPA.

Expected PASS terminal:
`V2_CORE_SYNTHETIC_QUALIFICATION_PASS__CONTROLLER_AUDIT_REQUIRED__REAL_TRAIN_POSTERIOR_INFERENCE_STILL_OFF__FACTORIAL_SCIENCE_OFF__TRAINING_OFF`

## Hard firewalls

Forbidden:
- TEST/Morabito
- pathology
- target discovery in this lane
- SCENIC+/ATAC target evidence in planted truth
- V78 outcome retuning
- detection V2/V3 rescue
- old 18-fit campaign restart
- corrected-TRAIN posterior fit before qualification + audit
- H0/H1/H2/H3/C_OBS/C_BIO science
- Stage4/500K
- JEPA training/checkpoints

`training_authorized=false`
