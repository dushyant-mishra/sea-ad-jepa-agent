# V79 Bayesian model-development V2 candidate — 2026-10-11

## Scope

Exploratory/model-development evidence only. This does not supersede the frozen Bernoulli V2 failure, does not authorize corrected-S174 posterior inference, and does not authorize H0-H3 execution or training.

Evidence substrate: authenticated auxiliary 50K discovery fit population, deterministically donor-balanced to 10,379 cells across 104 fit donors, 42 operators and 3 sources. The selected 20 identity-blind addresses deliberately span prevalence ~0.05 to ~0.87. Three held-out-donor folds were used for predictive comparisons. Integer counts were replayed from the mounted log1p10k values and source_library; reconstructed log1p values agree to max absolute error 8.88e-16 on the used matrix.

## What the data earn

### Detection fixed structure
Held-out-donor mean binary log loss:

- depth linear: 0.466368
- depth quadratic: 0.463706
- + broad class: 0.416760
- + source: 0.330816
- + operator: 0.322037 (class + source + operator)
- replacing class+source with source×class gives 0.322219 and does not improve the mean.

Interpretation: broad class and source are essential; operator adds a smaller but reproducible gain; source×class interaction is not earned.

### Positive-magnitude fixed structure
Held-out-donor mean count-scale lognormal LPD:

- depth: -2.233011
- + broad class: -2.187061
- + source: -2.080901
- + operator: -2.039129

Operator improves mean LPD by +0.041772 over depth+class+source and wins 17/20 genes. Adding quadratic depth to the full positive model improves mean LPD by +0.005326 and wins 16/20 genes.

### Random-effect structure
After removing depth/class/source/operator fixed structure, donor residual organization exceeds a within-source permutation q95 for:

- detection: 12/12 sampled genes;
- positive magnitude: 10/12 sampled genes.

Operator residual organization beyond depth/class/source exceeds q95 for:

- detection: 9/12 genes;
- positive magnitude: 8/12 genes.

Donor×class **increment beyond donor main effect** is not broadly supported:

- detection: 3/12 genes exceed q95; mean excess over q95 = -0.002149;
- positive magnitude: 5/12 genes exceed q95; mean excess = +0.000215.

Therefore donor main effect and operator effect are earned; donor×class is not earned as a default layer.

## Failed/limited development probe

A direct statsmodels zero-truncated-NB regression stress test was numerically unstable across the prevalence-spanning panel (no gene achieved three converged folds). This is an implementation/development stability failure, not evidence that ZTNB is scientifically inferior. Earlier bounded development evidence found lognormal and ZTNB positive-count predictive scores nearly tied. Positive-family selection therefore remains provisional.

## Adversarial design recovery check

A small development simulation used the actual 10,379-cell donor/operator/source/class crossing and the simplified class/source/operator/donor structure. Main planted components were recovered directionally, but a naive penalized fixed-effect fit leaked some donor-only signal into operator and some operator-only signal into donor. This confirms that donor and operator should not be represented as unrestricted fixed dummies. They require the constrained source-nested random-effect parameterization and shrinkage.

## Candidate V2 architecture

For each gene independently:

### Part 1 — detection

`detected ~ Bernoulli(logit^-1(eta_det))`

`eta_det = intercept_g + f_g(log_library) + class_g + source_g + operator_g + donor_g`

where:
- `f_g` is quadratic in centered log library initially;
- class and source are constrained fixed contrasts;
- operator is a random intercept constrained within source;
- donor is a random intercept constrained within source;
- **no donor×class random effect in the default candidate**;
- no free dataset/matrix identity effect.

### Part 2 — positive magnitude

Development default:

`log(count) | count > 0 ~ Normal(eta_pos, sigma_g)`

`eta_pos = intercept_g + f_g(log_library) + class_g + source_g + operator_g + donor_g`

with the same structural decomposition and quadratic depth. Lognormal is the development default because it is stable, strong on held-out donors, and does not require claiming that ZTNB is disproven. ZTNB remains an explicit challenger for the exact corrected-S174 replay if a stable implementation is available.

### Across-gene geometry

Do **not** begin with the previous monolithic cross-gene hierarchy of per-gene standard deviations. Fit genes modularly, with fixed/weakly regularizing priors chosen from the empirical development dossier, then estimate the across-gene distribution of recovered class/source/operator/donor/depth/residual summaries as a second-stage meta-distribution. This preserves the synthetic geometry objective while removing the funnel-producing hierarchy that caused much of the previous NUTS pathology.

## Why this is the current best candidate

It is the minimum architecture that retains every component supported by held-out-donor or permutation evidence:
- biological broad class;
- source/acquisition shift;
- operator variation;
- donor variation;
- nonlinear depth dependence;
- separate zero/detection and positive-magnitude processes.

It removes the largest unsupported complexity: donor×class. It also decouples genes computationally instead of forcing a joint hyper-sd hierarchy before that pooling has earned itself.

## Remaining gate before confirmatory freeze

This candidate is `DEVELOPMENT_QUALIFIED_ON_AUXILIARY_FIT_POPULATION`, not final S174 authority. Before a new untouched simulation qualification is created, replay the same nested model-development comparisons on exact corrected S174 TRAIN counts (4,726 cells / 149 donors / 42 operators) without changing the comparison metrics after viewing results. If the exact S174 replay preserves the structural conclusions, freeze Candidate V2 and only then generate new untouched synthetic recovery worlds.

Terminal:

`DEVELOPMENT_CANDIDATE_V2__TWO_PART_MODEL__CLASS_SOURCE_OPERATOR_DONOR_DEPTH_EARNED__DONOR_CLASS_NOT_EARNED__MODULAR_GENE_FITS_REQUIRED__EXACT_S174_REPLAY_PENDING__NO_CONFIRMATORY_AUTHORITY__TRAINING_OFF`
