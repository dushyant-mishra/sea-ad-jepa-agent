# V79 Factorial Native Execution Audit — 2026-10-10

## Terminal state of this phase

This audit records the native implementation and preexecution freeze for the V79 factorial synthetic-world lane. It does **not** record a scientific H0/H1/H2/H3 tournament execution and does **not** authorize JEPA training.

- implementation PR: **#253**
- implementation branch: `design/v79-factorial-biology-observer-20261010`
- implementation head before audit packaging: `1a0ab6e1108af924ca13e81caa3c70f3101d251c`
- frozen V78 base: `e959d9a732698ae9a41e8cb1f6c10052d7390326`
- corrected-TRAIN localization parent: PR #250 @ `62a1ff8cd93bd4250cd6ca11c93c7f3e9e6d6123`
- local native implementation tip used for audit: `f278e1699e2e05b87df929f62597dfeba6ea53aa`

## What is implemented

The branch contains the complete preexecution implementation surface for:

1. anonymous hierarchical biology;
2. explicit observation process;
3. frozen H0/H1/H2/H3 factorial composition;
4. mandatory C_OBS and C_BIO counterfactual controls;
5. legacy + localization-aware scoring;
6. fail-closed custody and falsification gate;
7. frozen arm/custody/preexecution contracts.

No V78 source was modified.

## Fresh executable verification

Fresh focused suite:

```text
84 passed in 0.67s
```

Command:

```bash
pytest tests/test_v79_hierarchical_biology_v1.py tests/test_v79_observation_operator_v1.py tests/test_v79_factorial_worlds_v1.py tests/test_v79_factorial_scoring_v1.py tests/test_v79_factorial_gate_v1.py -q
```

Fresh preexecution-only replay:

- status: **READY**
- blockers: `[]`
- `training_authorized`: `false`
- scientific arm outputs generated: **false**

Only authority/manifest/gate artifacts exist under `results/v79_factorial/`; no H0/H1/H2/H3 counts, scientific scores, or terminal tournament ruling were generated.

## Frozen artifacts and hashes

| Artifact | SHA-256 |
|---|---|
| `scripts/v79/v79_hierarchical_biology.py` | `8281ae455f8765d1df39a3250152e6bcf55e01d4a2d58c6ce95e774694eaadd7` |
| `scripts/v79/v79_observation_operator.py` | `cc6f25011c89acea2a5bc8e5ae9825299ea473d4de893932825d38e37756904d` |
| `scripts/v79/build_v79_factorial_worlds.py` | `1a100066f96c3e3a05498eda609b17d9e5fcc82a7c3cf192dbaebd5b7c45bc11` |
| `scripts/v79/score_v79_factorial_worlds.py` | `e0100e29e21a49efba59f8c0cd720be2f9836fb558d62c9878c661aefcf3dc26` |
| `scripts/v79/run_v79_factorial_tournament.py` | `48503668fc9c8c27cc2e06856e8ffa28e8b479895d8593da6fa7b05df30e5cda` |
| `tests/test_v79_hierarchical_biology_v1.py` | `2a8fd00a18a6e5201a322584757696287de87b0c9f93c6236630b2822539a1d7` |
| `tests/test_v79_observation_operator_v1.py` | `0c16fedd7bcee52e57ba5c7f2a3174c5eafe85ad58d47a4d13a782ddf7d33694` |
| `tests/test_v79_factorial_worlds_v1.py` | `0fe61311e4c7e256ce0104521e0d119e748aba0b07108e37bde41f08b39f0715` |
| `tests/test_v79_factorial_scoring_v1.py` | `bba5b44994eeaf82865dce3acd4b636d41bc4a64582e6e5fdae6fe27fe1a6384` |
| `tests/test_v79_factorial_gate_v1.py` | `4a4c9a1614afee7c62c54c1133eabda2265065cb132672196c01913778dce0aa` |
| `docs/agent/V79_FACTORIAL_ARM_CONFIG_20261010.json` | `d6976905cccef68b2c637d14eeb8f23ab7a782bb2e79294e69de7532e049690a` |
| `docs/agent/V79_FACTORIAL_CUSTODY_20261010.json` | `7693fd01f277bdc58312f8f70f75ebc09109a19acd33d02143eb44eefdb59769` |
| `docs/agent/V79_FACTORIAL_TOURNAMENT_PREEXECUTION_20261010.md` | `7cd721b2c4c817bb7f34bb3e740a09449fe4b963a7ac859d466d675c3ca2daac` |
| `results/v79_factorial/V79_BIOLOGY_AUTHORITY_V1.json` | `a5a9094930672ecdfb38aca6caca76e5654a58e00c2746f24c035468fe554d0a` |
| `results/v79_factorial/V79_OBSERVATION_AUTHORITY_V1.json` | `8036c4b007235c6a6858e4e282259b571d7d1e583899157f0e4dac1778453fc1` |
| `results/v79_factorial/V79_FACTORIAL_ARM_MANIFEST_V1.json` | `3ac220dab3db96fe34e799e5ac19352d93cd9cdcec367c72528ffe7175040dec` |
| `results/v79_factorial/V79_FACTORIAL_PREEXECUTION_GATE_V1.json` | `7cd8105882dcebc0e895a68ccaca904db32cc5ed0cdbe8b5295b625871f21143` |

## External canonical custody (hash-bound, not duplicated)

- canonical 41,238-address namespace: `7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd`
- repaired V78 marginal authority: `997280132e981b4c23fab97c479eab782a7d7b162944364062ca21e18c9324c1`
- repaired S174 archive: `88067f2efb5d8a0168eb352f83bd9de88c3b929c95a8f8fa1c40a6e34c568a2f`

The large canonical address namespace is not duplicated into this audit branch; the execution gate authenticates its bytes by SHA-256.

## Native implementation decision ledger

Key rulings preserved from the native execution ledger:

- H1 receives no source/operator input and uses only anonymous geometry.
- H2 cannot mutate latent truth and cannot externally force detected-gene counts.
- repaired positive-abundance quantiles may seed anonymous baseline heterogeneity, with gene membership randomly permuted.
- synthetic donor localization pools across deliberately crossed observation regimes after class+depth matching; it is explicitly a causal synthetic view, not a claim about real nested L4.
- 4,000 cells and 2 synthetic donors are frozen to make the preregistered 100-cell conditional support floor estimable; this is not population realism.
- first explicit observer uses exact registry source support, source-invariant capture log mean 0/log-SD 0.35, neutral gene propensity, independent thinning, molecule scale 0.20. Failure is falsification evidence, not permission for post-outcome retuning.
- the CLI recomputes byte hashes for all supplied authorities; quoted `actual` values cannot authenticate execution bytes.
- latent arrays use float32 and serialization deduplicates identical latent truth by hash to reduce memory while preserving the frozen semantics.

## Parallel-lane firewall

Macha's Bayesian dataset-geometry lane is separate. This audit does not modify that branch and does not consume its intermediate sampler/recovery outputs. A future **qualified, identity-scrubbed** Bayesian geometry artifact may be audited prospectively before scientific V79 execution; it may not silently retune an already executed arm.

Target discovery is also separate and untouched: no target panel, target rank, SCENIC+/ATAC/NIH-CARD evidence, 353-ID repair, pathology evidence, or target posterior is changed or consumed here.

## Authorization state

- synthetic scientific tournament execution: **not yet performed**
- JEPA training/checkpoint generation: **unauthorized**
- V78 retuning: **unauthorized**
- TEST/Morabito: **not accessed**
- pathology: **not accessed**
- target discovery: **not modified**

The next scientifically lawful step is independent audit/review of this preexecution package, followed by a separate explicit decision about whether to execute the frozen H0/H1/H2/H3 + controls tournament.
