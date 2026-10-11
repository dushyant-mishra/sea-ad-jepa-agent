# JEPA Synthetic V79 Factorial Takeover Addendum — 2026-10-10

## Read this first

This is the controlling addendum for the factorial synthetic-world lane after the original PR #257 takeover was written.

The original scientific state remains unchanged: no H0/H1/H2/H3 scientific tournament has been executed, no arm has been promoted, and JEPA training/checkpoint generation is unauthorized.

A later pre-outcome engineering review found registry-scale memory defects and created PR #262. Those fixes are **not yet covered by the old 84-test/READY receipt**. The next agent must close that verification gap before any scientific run.

## Canonical lineage

1. PR #242 — frozen V78 signed-detection/marginal tournament, no arm promoted.
2. PR #250 — corrected-TRAIN deterministic localization; major result: pooled signed-detection excess is driven primarily by broad-class mixture, with residual source-associated structure after class+depth conditioning.
3. PR #253 — factorial biology × observation implementation and frozen preexecution design.
4. PR #256 — native preexecution audit; 84 focused tests passed and preexecution-only gate returned READY on the pre-hardening implementation.
5. PR #257 — original takeover handoff.
6. PR #262 — prospective registry-scale memory hardening, head `3419dfc9bbc0410298b21b55e2caddd07ed82a27`; pending equivalence/focused-test verification.
7. PR #260/#261 — Macha Bayesian dataset-geometry audit/handoff, separate lane, terminal `SIMULATION_QUALIFICATION_INCOMPLETE` at snapshot.

## Scientific model to preserve

The V79 causal architecture is:

`latent biology -> observation operator -> observed counts`

Factorial worlds:

- H0: frozen baseline biology + frozen baseline observer
- H1: hierarchical anonymous biology + baseline observer
- H2: baseline biology + explicit observation operator
- H3: hierarchical anonymous biology + explicit observation operator
- C_OBS: identical latent biological truth replayed through different observers
- C_BIO: different latent biological truths replayed through the same observer

The purpose is to distinguish biological hierarchy from measurement/observation effects rather than fitting a single flexible covariance object.

## Corrected-TRAIN evidence motivating the architecture

The real corrected-S174 diagnostic reproduced the frozen pooled statistics exactly. The key localization result was:

- pooled strong positive/negative ratio: ~59
- same well-supported cells without class conditioning: still ~54–56
- within broad biological class: ~1.2–1.3
- within class + depth: ~1.0–1.1
- residual strong negative edges become nearly absent after source conditioning on the supported subset

Interpretation boundary: broad-class composition explains most of the enormous pooled positive excess. Residual negative structure is strongly source-associated but is not automatically technical because source remains confounded with biology. This is why V79 needs both biological and observation layers.

## Macha integration — updated project direction

Do not treat Macha as a competing generator. His lane is intended to estimate the corrected-TRAIN generative geometry with uncertainty.

Once qualified, his final posterior-generative outputs should be incorporated **prospectively** into the factorial simulator as richly as scientifically defensible:

Biology-safe inputs may include posterior distributions for class effects, donor effects, donor×class effects, residual within-class variability, anonymous gene-effect distributions, covariance/eigenspectrum structure, and related uncertainty.

Observation-safe inputs may include posterior distributions for source/operator effects, detection/capture variability, depth/count dispersion, count-family behavior, and dependencies among detection/depth/counts.

Do not intentionally cripple realism. The governing rule is now:

> use all corrected-TRAIN information that describes the data-generating distribution, while withholding only information whose inclusion destroys causal identifiability or leaks a downstream evaluation target.

For the causal qualification world, preserve anonymous/randomized biological identities rather than exact real gene-to-program assignments. A separate maximum-realism fitted world may be built, but it cannot serve as planted biological truth by itself.

No Macha numerical posterior has yet been consumed because his lane was not terminally qualified at snapshot. Do not import provisional sampler estimates.

## PR #262 engineering delta

Independent review found three scale defects:

1. latent biology created full float64 cell×gene intermediates;
2. observation created full dense support/base/rate/int64 count matrices;
3. scoring densified the 41,238-address matrix/full evaluation universe before selecting 3K genes.

PR #262 rewrites those paths to block/stream and stay sparse longer while intending to preserve frozen semantics.

Changed files only:

- `scripts/v79/v79_hierarchical_biology.py`
- `scripts/v79/v79_observation_operator.py`
- `scripts/v79/score_v79_factorial_worlds.py`

Do not assume it is qualified merely because it is an engineering-only change.

## Exact next-agent order

### Gate A — verify PR #262

1. checkout exact head `3419dfc9bbc0410298b21b55e2caddd07ed82a27` or the newest explicitly audited successor;
2. run the five focused V79 test files;
3. add/run equivalence tests proving old vs hardened outputs agree on small deterministic fixtures for:
   - latent biology arrays/truth hashes for same seeds;
   - observer counts/count hashes for same seeds and both realization families where applicable;
   - CPM-log1p HVG selection;
   - legacy V77 endpoint summaries;
   - V79 localization summaries;
4. inspect for remaining full registry-scale `.todense()`, `.toarray()`, or full dense cell×gene temporaries in the execution path;
5. rerun preexecution-only gate and record fresh hashes/receipt;
6. create a successor audit receipt; do not overwrite the old audit.

If equivalence fails, determine whether the mismatch is numerical-only, RNG-order-changing, or scientific. Do not execute scientific arms until resolved.

### Gate B — reconcile Macha

Check PR #261 / live Macha branch for newer terminal outputs.

If still incomplete: continue engineering/audit work but do not use provisional estimates as frozen calibration authority.

If qualified:

1. audit recovery-suite and PPC success;
2. audit model-family selection and convergence;
3. inspect final biology and observation posterior-generative authorities;
4. verify target/pathology/TEST identity firewall;
5. freeze exact authority SHAs and permitted field mapping into H1/H2;
6. regenerate/freeze any affected synthetic calibration authority **before** reading factorial outcomes.

If incorporating Macha changes H1/H2 materially, this becomes a prospectively frozen successor execution package, not a silent mutation of the already audited manifest.

### Gate C — scientific tournament

Only after A and the Macha decision are closed:

1. authenticate frozen authorities and manifest;
2. generate H0/H1/H2/H3 + C_OBS/C_BIO exactly once under frozen seeds;
3. preserve all raw world receipts;
4. score legacy V77/V78 endpoints plus localization-aware endpoints;
5. enforce falsification rules before interpreting mechanism-family results;
6. record failures as failures; do not retune after outcome read.

### Gate D — only after synthetic qualification

JEPA training/checkpoint work remains closed until a synthetic world is scientifically qualified under the planted-truth and observation-invariance criteria.

## Frozen custody anchors

- frozen V78 head: `e959d9a732698ae9a41e8cb1f6c10052d7390326`
- corrected S174 RAR SHA-256: `88067f2efb5d8a0168eb352f83bd9de88c3b929c95a8f8fa1c40a6e34c568a2f`
- repaired V78 marginal authority SHA-256: `997280132e981b4c23fab97c479eab782a7d7b162944364062ca21e18c9324c1`
- canonical address namespace SHA-256: `7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd`
- frozen evaluation-universe historical expected SHA-256: `e950e967dd593b253837017f8bda5c5a683d975074728f4b8fe20c27272b9763`
- evaluation-universe semantics: `TRAIN_PREVALENCE05_19569`, 14,417 addresses

The historical NPZ container bytes were not recovered in the local environment during the diagnostic pass; the 14,417 membership was exactly rederived from authenticated corrected TRAIN and reproduced the frozen corrected-real L0 statistics. Do not silently substitute a newly serialized NPZ for the historical byte authority in any canonical receipt.

## Hard prohibitions

Until a new explicit authority says otherwise:

- no TEST/Morabito;
- no pathology;
- no target-discovery ranks/panels/SCENIC+/ATAC target evidence in synthetic truth;
- no 353 historical-ID repair as synthetic evidence;
- no V78 retuning;
- no E4/Stage4/500K;
- no production target/representation freeze;
- no JEPA training/checkpoint generation;
- no post-outcome parameter rescue.

## Current terminal

`PREEXECUTION_SCIENCE_FROZEN__MEMORY_HARDENING_PENDING_VERIFICATION__MACHA_QUALIFICATION_PENDING__SCIENTIFIC_TOURNAMENT_NOT_RUN__TRAINING_OFF`
