# V79 Factorial Tournament Preexecution Contract

Date: 2026-10-10
Status: FROZEN PREEXECUTION / NON-TRAINING / NO SCIENTIFIC ARM EXECUTION

## Lineage
- Frozen V78 base: `e959d9a732698ae9a41e8cb1f6c10052d7390326`
- Parent corrected-TRAIN localization: PR #250 @ `62a1ff8cd93bd4250cd6ca11c93c7f3e9e6d6123`
- V79 design/implementation branch: `design/v79-factorial-biology-observer-20261010`

## Frozen arm manifest
Input config: `docs/agent/V79_FACTORIAL_ARM_CONFIG_20261010.json`
Semantic manifest SHA-256: `f2285bb82f6552e98dee1472d4dd2b0a3e6fa3fab923abffd8e94da7713ab892`

Exact arms: `H0,H1,H2,H3,C_OBS,C_BIO`
- cells: 4000
- synthetic donors: 2
- biology seed: 7901
- observation seed: 7902
- counterfactual biology seed: 7903
- crossing seed: 7904
- class balancing: `BALANCED_WITHIN_BROAD_CLASS`
- H2/H3 realization: `independent_thinning`
- endpoint version: `V79_FACTORIAL_ENDPOINTS_V1`
- training authorized: false

Two donors are intentionally used in this first causal tournament so the preregistered 100-cell conditional support floor remains estimable after class+depth stratification at 4,000 cells. This is a causal-support design, not a claim that two donors reproduce human population heterogeneity.

## H1 biological authority
`results/v79_factorial/V79_BIOLOGY_AUTHORITY_V1.json`
SHA-256: `a5a9094930672ecdfb38aca6caca76e5654a58e00c2746f24c035468fe554d0a`

Frozen choices:
- 3 balanced anonymous broad classes;
- 3 anonymous substates/class;
- substate prevalence concentration 1.5;
- anonymous module sizes 150, 300, 400 addresses, inherited as scale choices from the already-preregistered V77 synthetic module geometry, never as real gene memberships;
- 3 modules/substate;
- 4 low-amplitude continuous factors;
- substate effect scale 0.55, anchored to the frozen E2 class-program magnitude;
- continuous scale 0.10;
- donor-like scale 0.08;
- identity-scrubbed positive abundance quantiles from the repaired V78 marginal authority, anonymously permuted under the biology seed.

No real gene identity, edge list, pathway, donor-by-gene effect, source, or operator is present in H1 authority.

## H2 observation authority
`results/v79_factorial/V79_OBSERVATION_AUTHORITY_V1.json`
SHA-256: `8036c4b007235c6a6858e4e282259b571d7d1e583899157f0e4dac1778453fc1`

Observation regimes: `HVS`, `NPH52`, `SEA_AD`.

Structural support is taken exactly from the canonical address namespace, SHA-256 `7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd`:
- HVS: 18,736 / 41,238 addresses;
- NPH52: 35,533 / 41,238;
- SEA-AD: 35,786 / 41,238;
- 17,569 supported by all three;
- 9,990 supported by exactly one.

The first observer family is deliberately minimal:
- source-specific structural support only;
- source-invariant technical capture log mean 0;
- source-invariant capture log SD 0.35;
- anonymous gene propensity fixed to 1.0;
- independent thinning/count realization;
- molecule scale 0.20.

The observer deliberately does **not** infer source-specific capture efficiency from real library size. Real library total mixes biology and measurement. The 0.20 scale was frozen prospectively from the anonymous positive-abundance mass and real global depth scale, not selected by synthetic topology outcomes. If depth adequacy fails, that is a falsification/next-family result rather than permission to retune this arm after inspection.

## Custody
`docs/agent/V79_FACTORIAL_CUSTODY_20261010.json`

Required byte hashes:
- biology authority: `a5a9094930672ecdfb38aca6caca76e5654a58e00c2746f24c035468fe554d0a`
- observation authority: `8036c4b007235c6a6858e4e282259b571d7d1e583899157f0e4dac1778453fc1`
- canonical address namespace: `7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd`
- repaired V78 marginal authority: `997280132e981b4c23fab97c479eab782a7d7b162944364062ca21e18c9324c1`

The CLI recomputes `actual` hashes from the supplied bytes. Quoted `actual` values in the custody JSON are not trusted.

## Preexecution-only command

```bash
python -m scripts.v79.run_v79_factorial_tournament \
  --manifest docs/agent/V79_FACTORIAL_ARM_CONFIG_20261010.json \
  --custody docs/agent/V79_FACTORIAL_CUSTODY_20261010.json \
  --biology-authority results/v79_factorial/V79_BIOLOGY_AUTHORITY_V1.json \
  --observation-authority results/v79_factorial/V79_OBSERVATION_AUTHORITY_V1.json \
  --authority-file registry=/mnt/data/v79_native_runtime/address_namespace.csv \
  --authority-file repaired_marginal=/mnt/data/v79_inputs/V78_MARGINAL_AUTHORITY_REPAIRED_V1.json \
  --out results/v79_factorial \
  --preexecution-only
```

Expected outputs at this gate only:
- `results/v79_factorial/V79_FACTORIAL_PREEXECUTION_GATE_V1.json`
- `results/v79_factorial/V79_FACTORIAL_ARM_MANIFEST_V1.json`

No H0/H1/H2/H3 counts, scores, or terminal ruling are permitted in this commit.

## Hard stop
After the preexecution package is committed, stop for independent implementation/preexecution review. Scientific tournament execution requires a later explicit decision. JEPA training and checkpoint generation remain unauthorized.
