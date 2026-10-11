# V79 Bayesian geometry controller handoff — model-development correction

Date: 2026-10-11

This handoff controls only the synthetic/V79 Bayesian dataset-geometry lane. Target discovery is separate.

## Current ruling

The previous plan to immediately complete Gaussian/log-normal/ZTNB S0-S5 confirmation under the old frozen model family is superseded by an empirical model-development hold.

Bernoulli/detection V2 remains terminally `NOT_QUALIFIED` under its frozen confirmatory contract. That failure is preserved and is not being reinterpreted as a pass.

Gaussian/log-normal/ZTNB under the old monolithic hierarchy are **UNADJUDICATED** rather than failed; their queued confirmatory campaign remains on hold.

## New empirical development evidence

Controller-side development used the authenticated auxiliary 50K fit-population expression substrate, donor-balanced to 10,379 cells across 104 fit donors, 42 operators and 3 sources. Twenty identity-blind addresses span prevalence ~0.05-0.87. Three held-out-donor folds were used. Count replay from log1p10k + source_library reproduced the used normalized entries to max absolute error 8.88e-16.

Canonical development records:
- `docs/agent/V79_BAYESIAN_MODEL_DEVELOPMENT_V2_CANDIDATE_20261011.md`
- `results/v79/development/V79_BAYESIAN_MODEL_DEVELOPMENT_V2_EVIDENCE_COMPACT.json`

### Detection hierarchy
Held-out-donor binary log loss:
- depth linear 0.466368
- depth quadratic 0.463706
- + broad class 0.416760
- + source 0.330816
- + operator 0.322037
- source×class + operator 0.322219

Broad class and source are essential; operator adds a smaller reproducible gain; source×class is not earned.

### Positive-magnitude hierarchy
Count-scale lognormal held-out-donor LPD:
- depth -2.233011
- + class -2.187061
- + source -2.080901
- + operator -2.039129

Operator improves mean LPD by +0.041772 and wins 17/20 genes. Quadratic depth improves +0.005326 and wins 16/20 genes.

### Random-effect evidence
After fixed depth/class/source/operator structure:
- donor residual structure exceeds within-source permutation q95 in 12/12 detection genes and 10/12 positive genes;
- operator residual structure exceeds q95 in 9/12 detection genes and 8/12 positive genes;
- donor×class increment beyond donor main effect clears q95 in only 3/12 detection and 5/12 positive genes; mean detection excess is below null.

Therefore donor and operator remain; donor×class is removed from the default next candidate.

### Positive family
Lognormal is the development default because it is stable and predictive. ZTNB is not declared scientifically inferior: a direct truncated-NB stress test was numerically unstable and produced zero genes with 3/3 converged folds, while earlier bounded evidence showed near-tied positive-family predictive scores. ZTNB remains a challenger for exact S174 replay only if implemented stably.

## Candidate V2

Per gene, modularly:

Detection:
`detected ~ Bernoulli(logit^-1(intercept + quadratic(log_library) + broad_class + source + operator_re + donor_re))`

Positive magnitude:
`log(count) | count>0 ~ Normal(intercept + quadratic(log_library) + broad_class + source + operator_re + donor_re, sigma)`

Constraints:
- broad class and source are fixed constrained contrasts;
- operator random intercept is constrained within source;
- donor random intercept is constrained within source;
- no donor×class default layer;
- no free matrix/dataset identity effect;
- genes are fit modularly, not in the previous monolithic hyper-sd hierarchy;
- across-gene geometry is estimated second-stage from the per-gene posterior summaries.

A small development recovery probe on the actual donor/operator crossing recovered the main planted directions but showed leakage between unrestricted donor/operator dummies. Therefore the next Bayesian implementation must use the constrained source-nested random effects, not unrestricted fixed identities.

## Exact S174 boundary

GitHub contains an authenticated custody receipt for the repaired corrected-TRAIN cache at `D:\\Jepa project\\data\\cache\\s174_rebuilt_real_train_v1`, with 42 count shards + 42 metadata shards and exact per-file SHA-256 identities. The raw shard bytes themselves are not mounted in this controller environment and are not committed to GitHub. Therefore exact 4,726-cell S174 model-development replay cannot honestly be executed here.

This is the only remaining model-development gate before a new confirmatory freeze. Replay the same nested comparisons on corrected S174 TRAIN counts (4,726 cells / 149 donors / 42 operators) without changing comparison metrics after viewing results.

If exact S174 preserves these structural conclusions, freeze Candidate V2 and only then generate fresh untouched synthetic qualification worlds. Do not reuse the old confirmatory worlds as the sole confirmation set.

Current terminal:
`DEVELOPMENT_CANDIDATE_V2__TWO_PART_MODEL__CLASS_SOURCE_OPERATOR_DONOR_DEPTH_EARNED__DONOR_CLASS_NOT_EARNED__MODULAR_GENE_FITS_REQUIRED__EXACT_S174_REPLAY_PENDING__OLD_CONFIRMATORY_CAMPAIGN_ON_HOLD__TRAINING_OFF`

Hard firewalls remain: no corrected-TRAIN posterior authority, no H0-H3 factorial execution, no TEST/Morabito/pathology, no target-discovery work in this lane, no V78 outcome-driven retuning, no Stage4 and no JEPA training.
