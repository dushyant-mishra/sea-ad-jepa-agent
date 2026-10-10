# V79 Factorial Hardened Preexecution Audit — 2026-10-10

## Scope

This audit supersedes the execution-readiness interpretation of the earlier pre-hardening audit PR #256 while preserving #256 as the immutable store for the exact frozen preexecution/result authority artifacts. No H0/H1/H2/H3 scientific arm outcome has been generated or read in this hardening lane.

Current hardened implementation:
- PR #262
- branch `fix/v79-factorial-memory-hardening-20261010`
- head `36d51b6c554c21918289bc4f8c9b363cb2ecc0fa`
- parent implementation PR #253 head `1a0ab6e1108af924ca13e81caa3c70f3101d251c`
- frozen V78 base `e959d9a732698ae9a41e8cb1f6c10052d7390326`

## Independent review findings and repairs

The pre-hardening implementation contained three registry-scale memory defects:

1. Hierarchical biology accumulated full float64 cell×gene intermediates before casting to float32.
2. The explicit observer accumulated full dense base/rate/int64 count matrices.
3. The scorer densified the full registry/evaluation universe before the frozen 3K selection.

PR #262 removes these full-registry dense intermediates while preserving the frozen experiment semantics. Latent biology is materialized in cell blocks; observation samples blockwise or rowwise directly to CSR; the CPM-log1p HVG variance is computed sparsely and only selected genes are materialized densely.

A separate frozen-design gap was also found: the scorer lacked the preregistered class-conditioned and observation-regime-conditioned abundance/depth distribution views. PR #262 now reports, per broad class and per observation regime, cell count plus library-size, detected-feature, and positive-count quantiles.

## Verification evidence

GitHub Actions workflow: `V79 factorial memory hardening`

Final audited run:
- run `38084642870`
- job `114308511231`
- conclusion `SUCCESS`
- Python `3.11.17`
- NumPy `2.4.6`
- SciPy `1.17.1`
- pytest `9.1.1`
- focused result: **89 passed in 0.67 s**

The workflow checks out untouched PR #253 at `1a0ab6e1108af924ca13e81caa3c70f3101d251c` in a second worktree and executes the same observer fixture on base and hardened code under the same runtime. The base/head outputs agree exactly on that runner, including the integer count hash. The hardening tests also verify the frozen CPM-log1p HVG selection against the original V77 dense implementation.

### Reproducibility qualification

A transient audit failure exposed that raw floating capture-efficiency bytes are not a valid cross-CPU reproducibility identity: two GitHub hosted CPU families produced different raw float hashes at the same NumPy version, while untouched #253 and hardened #262 agreed exactly within each shared runtime and the sampled integer count hash stayed stable. The final regression therefore binds the exact in-process pre-hardening RNG rule plus same-runtime base/head equivalence rather than treating CPU-specific floating bytes as a scientific identifier.

This finding does not change the frozen causal design or observed-count endpoint.

## Frozen authority artifacts

The exact preexecution artifacts remain preserved in audit PR #256 under `results/v79_factorial/audit/`:
- `V79_BIOLOGY_AUTHORITY_V1.json.gz`
- `V79_OBSERVATION_AUTHORITY_V1.json.gz`
- `V79_FACTORIAL_ARM_MANIFEST_V1.json.gz`
- `V79_FACTORIAL_PREEXECUTION_GATE_V1.json.gz`

The earlier preexecution replay returned `READY`, blockers `[]`, `training_authorized=false`. PR #262 does not modify the gate algorithm, frozen arm config, custody contract, authority files, seeds, or protected-data flags. It changes only registry-scale materialization/scoring implementation and completes an already-preregistered distributional output surface.

Canonical large-data bindings remain:
- repaired S174 archive SHA-256 `88067f2efb5d8a0168eb352f83bd9de88c3b929c95a8f8fa1c40a6e34c568a2f`
- repaired V78 marginal authority SHA-256 `997280132e981b4c23fab97c479eab782a7d7b162944364062ca21e18c9324c1`
- registry/address namespace SHA-256 `7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd`
- historical frozen evaluation-universe NPZ SHA-256 `e950e967dd593b253837017f8bda5c5a683d975074728f4b8fe20c27272b9763`

## Frozen tournament configuration

- H0/H1/H2/H3 + C_OBS/C_BIO
- 4,000 cells
- 2 synthetic donors
- biology seed 7901
- observation seed 7902
- counterfactual biology seed 7903
- crossing seed 7904
- H2/H3 first-family `independent_thinning`
- endpoint `V79_FACTORIAL_ENDPOINTS_V1`
- `training_authorized=false`

## Parallel-lane firewall

This audit does not consume or modify:
- Macha's Bayesian geometry lane (`analysis/v79-bayesian-synthetic-geometry-20261009`, PR #260/#261 audit/handoff);
- target-discovery work, including PR #259;
- TEST/Morabito;
- pathology;
- frozen V78 outcomes.

Macha's eventual *qualified* posterior-generative authorities may prospectively parameterize a successor frozen synthetic calibration before outcome execution. No provisional Macha estimate has been used in PR #262.

## Terminal audit state

`HARDENED_PREEXECUTION_IMPLEMENTATION_GREEN__SCIENTIFIC_TOURNAMENT_NOT_EXECUTED`

Specifically:
- registry-scale hardening: PASS
- base-vs-head fixture equivalence: PASS
- focused CI: 89/89 PASS
- preregistered distributional scoring surface: completed
- scientific H0/H1/H2/H3 outcome read: NO
- arm promotion: NONE
- V78 retuning: NOT AUTHORIZED
- TEST/Morabito/pathology: NOT ACCESSED
- JEPA training/checkpoint generation: NOT AUTHORIZED

## Next lawful action

Use this hardened state, not PR #256/#257 alone, for any future execution review. Before any scientific tournament is enabled, either:

1. independently approve the existing frozen calibration authority as-is; or
2. if Macha completes and qualifies a richer posterior-generative authority first, freeze a prospective successor calibration authority and rerun the preexecution gate before any H0/H1/H2/H3 outcome is generated.

No post-outcome parameter rescue is permitted.