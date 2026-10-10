# JEPA Synthetic Lane V79 Factorial Preexecution Takeover — 2026-10-10

## Canonical entry point

Start from **audit PR #256**, branch `audit/v79-factorial-preexecution-20261010`, audited head `f8667ec218c624a40d3e333ba576e7289ae70a26`.

This is the current synthetic-world takeover state. Do not restart from V78 or rerun corrected-TRAIN localization unless a later commit invalidates their frozen heads.

## Lineage

1. **PR #242** — frozen V78 terminal state at `e959d9a732698ae9a41e8cb1f6c10052d7390326`; F0–F3 complete, no arm promoted, training unauthorized.
2. **PR #250** — corrected-TRAIN signed-detection localization at `62a1ff8cd93bd4250cd6ca11c93c7f3e9e6d6123`; real pooled ratio ~59 collapses to ~1.23 within broad class and ~1.04 after class+depth; residual signed topology is strongly source-associated but causality remains unresolved.
3. **PR #253** — V79 factorial biology × observation design + implementation at `1a0ab6e1108af924ca13e81caa3c70f3101d251c`.
4. **PR #256** — audit packaging and frozen preexecution evidence at `f8667ec218c624a40d3e333ba576e7289ae70a26`.

## What is implemented

- anonymous hierarchical biology (`H1` layer);
- explicit observation process (`H2` layer);
- factorial H0/H1/H2/H3 world builder;
- mandatory C_OBS observation twins and C_BIO biological controls;
- legacy V77/V78 + localization-aware scoring;
- fail-closed custody/falsification runner;
- frozen arm config, custody contract, biological authority, observation authority, arm manifest, and preexecution gate.

## Fresh terminal verification

At audit packaging:

- focused V79 suite: **84 passed, 0 failed**;
- preexecution-only replay: **READY**;
- blockers: none;
- `training_authorized=false`;
- no scientific H0/H1/H2/H3 arm outputs were generated.

## Frozen tournament contract

- arms: `H0,H1,H2,H3,C_OBS,C_BIO`;
- cells: 4,000;
- synthetic donors: 2;
- biology seed: 7901;
- observation seed: 7902;
- counterfactual biology seed: 7903;
- crossing seed: 7904;
- H2/H3 realization: independent thinning;
- biology authority SHA-256: `a5a9094930672ecdfb38aca6caca76e5654a58e00c2746f24c035468fe554d0a`;
- observation authority SHA-256: `8036c4b007235c6a6858e4e282259b571d7d1e583899157f0e4dac1778453fc1`;
- arm manifest SHA-256: `3ac220dab3db96fe34e799e5ac19352d93cd9cdcec367c72528ffe7175040dec`;
- preexecution gate SHA-256: `7cd8105882dcebc0e895a68ccaca904db32cc5ed0cdbe8b5295b625871f21143`.

Exact compressed copies of those four JSON artifacts are committed under `results/v79_factorial/audit/` in PR #256. The audit doc records decompressed SHA-256 values.

## External custody, hash-bound not duplicated

- repaired S174 archive: `88067f2efb5d8a0168eb352f83bd9de88c3b929c95a8f8fa1c40a6e34c568a2f`;
- repaired V78 marginal authority: `997280132e981b4c23fab97c479eab782a7d7b162944364062ca21e18c9324c1`;
- canonical 41,238-address namespace: `7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd`.

Do not duplicate the 25 MB namespace into the audit lane; authenticate the canonical bytes by hash.

## Scientific interpretation that motivated V79

Corrected TRAIN showed that the pooled ~59:1 positive/negative strong detection-edge ratio is mostly a broad-cell-class mixture effect. Matching broad class collapses it to ~1.23; adding depth collapses it to ~1.04. Source conditioning then removes most residual strong negative edges, but real source is confounded with biology. Therefore V79 explicitly separates upstream anonymous biological hierarchy from downstream observation process and crosses them factorially rather than adding another random signed field.

## Parallel-lane firewall

**Macha Bayesian geometry lane:** separate. Do not modify its branch or consume intermediate sampler/recovery outputs. Only a final qualified, identity-scrubbed Bayesian geometry artifact may be considered, and only prospectively before scientific V79 execution. If it arrives after execution or conflicts with deterministic localization, preserve the conflict and design a resolving experiment; never retune an executed arm.

**Target discovery:** separate and untouched. No TD panel, target rank/posterior, ATAC/SCENIC+/NIH-CARD evidence, 353-ID repair, pathology information, TEST, or Morabito may enter this synthetic lane.

## Hard authorization boundaries

Still false / prohibited:

- JEPA training/checkpoint generation;
- synthetic scientific tournament execution without a separate explicit decision after review;
- V78 retuning;
- TEST/Morabito access;
- pathology access;
- target-discovery modification;
- E4/Stage4/500K promotion;
- post-outcome parameter changes.

## Next action for the new agent

1. Open PR #256 and verify its head is exactly `f8667ec218c624a40d3e333ba576e7289ae70a26`.
2. Confirm PR #253 remains at `1a0ab6e1108af924ca13e81caa3c70f3101d251c` and V78 PR #242 remains at `e959d9a732698ae9a41e8cb1f6c10052d7390326`.
3. Review the code/tests plus `V79_FACTORIAL_NATIVE_EXECUTION_AUDIT_20261010.md`, the machine-readable audit state, and the implementation ledger.
4. Verify the four compressed audit result files decompress to the recorded SHA-256 values.
5. **Stop and adjudicate preexecution review.** If clean, the next user decision may authorize one frozen scientific H0/H1/H2/H3 + C_OBS/C_BIO tournament execution. Do not alter arm parameters first.
6. After execution, score against the frozen corrected-real endpoints and localization pattern. A failed family is falsification evidence; do not launch an unregistered retuning sweep.
7. Only if the synthetic world qualifies should a separate decision reopen a tiny JEPA engineering/training run and checkpoint generation.

## Do not redo

Do not redo S174 extraction/custody, V78 F0–F3, the corrected-TRAIN localization, or V79 architecture design unless their exact heads moved or a specific audit defect is identified.
