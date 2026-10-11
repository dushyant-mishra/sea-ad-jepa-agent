# JEPA Synthetic V79 Factorial Hardened Takeover — 2026-10-10

## Canonical entry point

Use this handoff, not the older PR #257 handoff, for the factorial synthetic-world lane.

Current lineage:

1. PR #242 — frozen V78 signed-detection/marginal tournament, no arm promoted.
2. PR #250 — corrected-TRAIN detection-geometry localization.
3. PR #253 — initial V79 factorial implementation + frozen preexecution contract.
4. PR #256 — immutable store for exact preexecution/result authority artifacts.
5. PR #262 — registry-scale hardening + missing distributional endpoint completion.
6. PR #264 — hardened preexecution audit.
7. This handoff — canonical takeover layer.

Canonical implementation for future review:
- branch `fix/v79-factorial-memory-hardening-20261010`
- head `36d51b6c554c21918289bc4f8c9b363cb2ecc0fa`
- PR #262

Canonical hardened audit:
- branch `audit/v79-factorial-preexecution-hardened-20261010`
- head `efa3f4ae8157cd2778a3f802258d36a899c23774`
- PR #264

Exact frozen preexecution artifact store:
- branch `audit/v79-factorial-preexecution-20261010`
- head `f8667ec218c624a40d3e333ba576e7289ae70a26`
- PR #256

## Scientific state

Terminal:
`HARDENED_PREEXECUTION_IMPLEMENTATION_GREEN__SCIENTIFIC_TOURNAMENT_NOT_EXECUTED`

No H0/H1/H2/H3 outcome has been generated or read. No arm has been promoted. JEPA training/checkpoint generation remains unauthorized.

## Why PR #262 exists

Independent review found that the frozen experiment would attempt several registry-scale dense allocations at 4,000 cells × 41,238 addresses. These were engineering defects capable of making the run fail for memory rather than science.

PR #262 prospectively repaired them before any synthetic-arm outcome:
- blockwise latent abundance materialization;
- sparse-streamed observation counts;
- sparse CPM-log1p preselection before dense selected-gene scoring;
- blockwise counterfactual latent distance.

The same review found that the scorer omitted a preregistered distributional surface. Each arm now includes broad-class- and observation-regime-conditioned quantiles for library size, detected features and positive counts.

## Verification

GitHub Actions run `38084642870` is the current independent verification:
- result SUCCESS
- focused V79 suite: 89 passed, 0 failed, in 0.67 s
- Python 3.11.17
- NumPy 2.4.6
- SciPy 1.17.1
- pytest 9.1.1

The workflow compares untouched PR #253 with the hardened head in the same runtime. The fixture produces the same latent/count/capture behavior. Sparse HVG selection is separately compared to the original frozen V77 rule.

Do not use raw floating capture-efficiency bytes as a cross-platform authority hash. Audit showed CPU-dependent floating normal bytes even at identical NumPy versions. Same-runtime semantics and the observed integer-count endpoint are the appropriate equivalence checks.

## Frozen first-tournament configuration

The implementation still carries the original prospective configuration:
- H0/H1/H2/H3 plus C_OBS/C_BIO
- 4,000 cells
- 2 synthetic donors
- biology seed 7901
- observation seed 7902
- counterfactual biology seed 7903
- crossing seed 7904
- balancing `BALANCED_WITHIN_BROAD_CLASS`
- H2/H3 realization family `independent_thinning`
- endpoint `V79_FACTORIAL_ENDPOINTS_V1`
- `training_authorized=false`

No parameter was changed in response to an H0-H3 outcome because none has been observed.

## Corrected-TRAIN evidence that motivated the architecture

On corrected S174, the pooled signed-detection positive/negative strong-edge ratio is approximately 59.0. Conditioning within well-supported broad biological classes collapses it to approximately 1.23; class plus depth moves it to approximately 1.04. Same-cell pooling controls retain ratios above ~50, so the collapse is not explained by cell exclusion. Residual strong negative structure is strongly source-associated, but source remains a mixture of biology and measurement and must not be called purely technical.

This is why V79 separates anonymous biological hierarchy from an explicit observation process and tests them factorially.

## Macha Bayesian geometry lane

Macha's lane is separate:
- source `analysis/v79-bayesian-synthetic-geometry-20261009`
- audited snapshot PR #260
- takeover PR #261

At its audit point it remained `SIMULATION_QUALIFICATION_INCOMPLETE`; no real expression-value Bayesian fit was qualified for consumption.

The intended future interface is stronger than a few scalar summaries: once Macha produces qualified posterior-generative biology and observation authorities, they may prospectively parameterize a successor V79 calibration while keeping synthetic biological identity anonymous.

Do **not** consume provisional Macha sampler estimates into the current frozen H0-H3 arms.

Because the scientific tournament has not executed, there are two lawful choices at future review:

- execute the current frozen authority after independent approval; or
- if Macha's richer authority qualifies first, create and freeze a successor calibration authority *before* any outcome read, rerun preexecution, and then execute that successor once.

Never use Macha after outcome read to rescue a failed arm.

## Target-discovery lane

Target discovery remains separate. PR #259 records the value-blind G4/G5 preflight. G6/G7, value-read replay and training were not authorized by that preflight.

Do not import target ranks, panels, SCENIC+/ATAC target evidence or pathology into synthetic truth.

## Frozen custody

- repaired S174 archive: `88067f2efb5d8a0168eb352f83bd9de88c3b929c95a8f8fa1c40a6e34c568a2f`
- repaired V78 marginal authority: `997280132e981b4c23fab97c479eab782a7d7b162944364062ca21e18c9324c1`
- corrected calibration: `f6ba2c725a5437cc8455fff418027d36efe9ea9430fbd0a5765df62dedca6068`
- paired-meta semantic digest: `b876e13526f51d5a4199ca750ad09065c5ab8a20aeca39dff3d8c385f2241f46`
- class authority: `a4f5e325a54014d87d6380f81ce48922a6558f05ffafdaf7c59c1dc3ae705014`
- registry/address namespace: `7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd`
- historical evaluation-universe NPZ: `e950e967dd593b253837017f8bda5c5a683d975074728f4b8fe20c27272b9763`

## Hard boundaries

Still false / unauthorized:
- JEPA training
- checkpoint generation
- V78 retuning
- synthetic arm promotion
- E4
- TEST/Morabito
- pathology
- target-discovery modification
- Stage4/500K
- production target/representation freeze
- named real biological programs as planted causal truth

## Next technical review items

Before enabling the actual scientific executor, audit output serialization and payload size. Current scoring intentionally retains correlation matrices needed for localization logic; a final executor must write bounded, atomic, identity-scrubbed receipts rather than accidentally serialize unnecessary per-stratum matrices. This is an engineering output-contract task and must be completed prospectively before outcome execution.

Then perform independent preexecution review of whichever calibration authority is selected. Only after that separate review may one frozen scientific tournament be enabled.