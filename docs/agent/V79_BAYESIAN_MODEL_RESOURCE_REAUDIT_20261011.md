# V79 Bayesian model/resource re-audit — 2026-10-11

## Scope

Independent audit addendum for the synthetic/V79 Bayesian dataset-geometry lane. This does not alter the historical snapshot preserved by PR #260. It records the later controller correction and the qualified engineering path to the next empirical-development gate.

Live Macha source inspected after the snapshot: `analysis/v79-bayesian-synthetic-geometry-20261009` at `b06bd819abd7da1be0426767c6909f4cdc7cc7bf`.

## Scientific correction

The project had been attempting confirmatory synthetic recovery before sufficiently characterizing the real TRAIN-like distribution. The old Gaussian/log-normal/ZTNB campaign is therefore on a methodological hold rather than being treated as pass/fail evidence.

Detection/Bernoulli V2 remains a genuine frozen-contract failure:
- S4 worst R-hat: 1.0050606797;
- S4 worst ESS: 361.8761303;
- frozen ESS minimum: 400;
- final divergences: 0.

The later empirical tournament does not convert that result into a pass. It instead shows that **a separate detection process remains useful**, so the failure should be attributed to the specific old hierarchical Bernoulli parameterization/posterior geometry rather than to the concept of detection modelling.

## Development candidate

Auxiliary fit-population development supports a two-part per-gene candidate:
- quadratic depth;
- broad class;
- source;
- operator-within-source candidate;
- donor-within-source candidate;
- no donor×class default layer;
- modular per-gene fits;
- second-stage across-gene geometry;
- lognormal positive magnitude as the stable development default;
- ZTNB retained as an unresolved challenger.

This is **development evidence only**.

### Self-audit correction

The auxiliary operator residual-support count used a weaker source-stratified permutation that could retain donor-composition effects. Therefore those particular operator-support counts are provisional.

The exact S174 replay prospectively corrects this before S174 results are viewed:
- predictive operator proxy is reference-coded within source so the source+operator design is full rank;
- operator residual support is tested after donor-centering;
- the null permutes within donor;
- donor×class increment is also donor-centered and tested within donor.

Held-out-donor predictive improvement from adding operator in the auxiliary tournament remains development evidence, but final structural support for the operator random layer must be decided by exact S174.

## Resource re-audit

Historical real-data code repeatedly loaded all 42 corrected-TRAIN shards, globally assembled a 4,726 × 41,238 CSR matrix and selected a small panel only afterward. Phase/fold processes repeated this work.

The prior 'compact cache' implementation was not truly streaming: it accumulated all CSR blocks, called `sparse.vstack`, and its verification path rebuilt the full matrix again.

PR #279 (`fix/v79-streaming-analysis-cache-20261011`) repairs this.

### Verified engineering state

Independently tested code head: `2d5de281a171f0510d22a7408780fb069625ea02`.

GitHub Actions:
- workflow run `38166126568`;
- job `114548954034`;
- **15 passed in 1.27 s**.

The focused tests cover:
- no global `sparse.vstack` cache construction;
- no historical global loader in cache verification;
- two count-shard passes exactly;
- maximum one count shard resident;
- selected-count/library/detected-feature/gene-sample equivalence;
- metadata design derived from exact authenticated bytes and equivalent to historical firewall semantics;
- tampered-shard rejection;
- hash-bound replay cache;
- donor-held-out fold integrity;
- prevalence-balanced subpanel selection;
- full-rank operator-within-source fixed proxy;
- residual group permutation;
- donor-controlled operator null;
- machine-wide scheduler default of one heavy fit.

### Actual machine bottleneck

A measured historical Gaussian recovery fit recorded:
- peak RSS 1.32 GB;
- mean process CPU ~10.28 logical CPUs;
- mean whole-machine CPU ~93.1%;
- wall time 1561.5 s;
- disk read only ~21.9 MB during the measured fit.

Audit interpretation: heavy Bayesian execution is primarily **sampler CPU-bound**, not expression-data RAM-bound. Streaming prevents unnecessary I/O/RAM churn but does not solve NUTS compute by itself. Future heavy work should therefore remain one fit at a time and modular per gene where scientifically valid.

## Exact S174 provenance boundary

Do not reconstruct the 4,726-cell S174 set from the larger 50K corpus. The repaired S174 cache deliberately preserves the exact historical cells by cell ID and order while replacing their expression values from corrected physical sources.

The lawful next input is the authenticated local cache:
`D:\Jepa project\data\cache\s174_rebuilt_real_train_v1`

with:
- `results/v78/V78_S174_SHARD_OPERATOR_BRIDGE_V1.json`;
- `results/v79/V79_S174_SHARD_AUTHORITY_V1.json`.

## Audit verdict

`PASS_ENGINEERING_TO_PHYSICAL_S174_DEVELOPMENT_REPLAY__MODEL_NOT_YET_CONFIRMATORILY_QUALIFIED`

Authorized next action:
1. build one 500-gene hash-bound compact cache by the PR #279 two-pass stream;
2. run the exact-S174 cache-only structure replay (200 replay genes, 3 held-out-donor folds, 50 support genes, 99 permutations);
3. return the receipt/result for controller adjudication.

Not authorized:
- restart of the old 18-fit campaign;
- corrected-TRAIN Bayesian posterior inference;
- posterior parameter export to the factorial generator;
- H0-H3 scientific execution;
- TEST/Morabito/pathology;
- target discovery in this lane;
- JEPA training.
