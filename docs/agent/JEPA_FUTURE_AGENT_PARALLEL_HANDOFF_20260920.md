# JEPA future-agent parallel handoff — 2026-09-20

Purpose: durable takeover note for the FULL104 information-channel red-team while Claude/GPU and GPT/chat lanes work in parallel.

## Live lineage at last refresh

- cleaned implementation/review branch: `impl/v5-full104-pass1-review-repairs-20260920`
- PR #32 cleaned head after stale support-geometry test retirement: `a215bb77c4dbaa4bb60ad5b7ed54c2d574c8bf2a`
- active information-channel audit branch: `audit/v5-full104-information-channel-redteam-20260920`
- Draft PR #33 live head at last refresh: `505dc78ae88303d3b61928eedf4b572942f203b4`
- GPT supporting/handoff branch: `handoff/jepa-v5-gpt-parallel-audit-20260920`
- Draft PR #34 contains supporting/historical evidence only.

Always re-fetch live PR #33 before acting; it is advancing during this handoff.

## Closed foundations that should not be redone

- corrected selection-row keyed pass1 is reproducible byte-for-byte: `37f79e49f11364daa487ad9e5a5680f72378daf338852765d2f52e1e98d90ba1`
- physical binding root: `4c44b89e91e85b762224a6c2cf7e5cd88956a1726f57a52c03ddcab4ad0c3602`
- Census Authority V2 canonical root: `7a090d4078239e9bc161ae60c289b7f1a5bbb02e7cf3e6bcc0ae9c284b89ee21`
- 4,553,407 cells / 104 donors / 42 operators / 41,238 ledger addresses / 17,186 strict core / 17,053 globally eligible targets
- corrected strict-core measured-zero frequency: `0.8329826626244999`
- calibration cache exists and remains `CONTROL_CALIBRATION_ONLY__FORBIDDEN_FOR_TERMINAL_MASKING_QUALIFICATION_V1`
- dense linear algebra environment issue was invocation/PATH conditioned, not a broken environment; qualified preterminal invocation exists.

## Hard boundaries

- terminal masking outcomes: UNOPENED
- D_shared: SEALED
- pathology / DEV / SEALED outcomes: SEALED
- terminal masking policy: NOT SELECTED
- training: OFF

## Active PR #33 audits

A — normalization denominator outside-ledger information
B — actual/effective mask burden vs nominal address burden
C — source-specific target estimability and zero target variance
D — held-out-donor standardization / primary estimand
E — co-detection vs quantitative partner association
F — target identity × target-zero decomposition
G — calibration-cache coverage

## Independent GPT review findings that must be carried forward

### Audit D wording/estimand

The current within-donor centred correlation is blind to pure between-donor/source location or scale channels. Do not broaden this to 'all donor/source-level channels': source-specific within-donor predictive relationships and cell-varying denominator channels can still be expressed. The real G3 issue is that production JEPA may exploit absolute cross-donor/source geometry that this primary score intentionally removes.

### Audit G causal decomposition

The calibration cache row selector is deterministic hash-priority bottom-k independently within each donor. Therefore the observed marginal high-complexity shift must be decomposed into:

1. deliberate donor/source composition reweighting from the 1,024-per-donor cap;
2. residual within-donor selection imbalance.

Do not causally call the row selector high-complexity-biased before this decomposition. Marginal non-population-representativeness is real either way.

### Audit F instrument is not yet frozen for the real teacher

The committed fixture implementation is scalar-only and uses a dense address one-hot design. The real teacher target is a multivariate latent state. Before a future real-teacher measurement:

- define multivariate explained variance (e.g. Frobenius SSE/SST and/or per-latent-dimension R² distribution);
- use scalable grouped/sparse/fixed-effect residualization rather than dense n×17,186 one-hot;
- freeze context representation dimensionality/meaning;
- state whether the decomposition is descriptive in-sample ANOVA or predictive/exploitable information; cross-fit if the latter.

Until then use status similar to `SCALAR_FIXTURE_DECOMPOSITION = QUALIFIED__REAL_MULTIVARIATE_ESTIMAND_OPEN`, not `DECOMPOSITION_DESIGN = FROZEN`.

### Audit B current implementation is not the actual production mask burden

The current `audit_b_effective_burden_20260920.py` reduced-pool calculation:

- selects partners within the deterministic co-detection pool, not the full 17,186-address universe;
- uses all donors in screening rather than outer-training donors per fold;
- compares selected addresses with the pool mean, not actual deterministic addresses dropped by each common-random base mask;
- computes B5 entropy from full-population detection probability although the contract says training-side only.

It can establish a reduced-pool mechanism, not actual TOP8/RIDGE8/PREFIX3 burden. Either relabel it and keep actual burden OPEN, or run exact fold-specific production planner burden on a prospectively deterministic diagnostic target sample.

### Audit C C2 is not implemented in the reviewed version

The reviewed script parses `--fold-by-donor` but does not use it. It defines train>=20 and validation>=5 but its headline source estimability only checks >=5 supported donors per source overall.

Required condition is per source × outer fold:

- supported training donors >=20
- supported held-out donors >=5

for every source/fold if that is the intended source guardrail population.

Also `donor_nnz == 0` is an exact all-zero condition and therefore guarantees zero variance, but is not an exhaustive exact zero-variance test. Rename accordingly or add a stable scorer-relevant variance calculation.

## Supporting historical evidence on PR #34

These values are prior/mechanism evidence only and MUST NOT set current thresholds:

- historical 50K measured-zero fraction among measurable slots: HVS ~0.7643, SEA_AD ~0.8501, NPH52 ~0.8821;
- historical u0 `partial_H -> support_measured_count` R² ~0.991 and source balanced accuracy 1.0;
- historical 84-cell truth table measured-zero fraction ~0.8215; ~82.1% of uniformly hidden measured targets were zero-valued;
- historical T1 gene-identity residual drift after decay removal is strongly support-patterned.

Current-authority inputs independently verified locally:

- address registry SHA `7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd`
- observation-state SHA `852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537`

## Key scientific interpretation to preserve

The 83.3% measured-zero rate is not itself a defect. The deeper issue is that information and intervention burden live in a highly uneven detection/count space while several current contracts are defined in address space.

Masking value-independence is deliberate: do NOT repair burden asymmetry by using each held-out cell's realized nonzero pattern to choose masks. Any successor weighting must be prospectively frozen and training-only/value-independent.

The normalization denominator is computed from full raw source counts before mapping/filtering to the 41K ledger. Therefore excluded/unmapped RNA can influence every visible normalized feature through `source_library`; direct query-column withholding does not close this denominator route.

## Dependency order

1. finish and independently validate A/B/C/E/G;
2. settle whether masking burden, source estimability, and primary shortcut estimand are scientifically well posed;
3. freeze a pathology-blind G4 state-fidelity functional;
4. derive a scientifically justified G5 equivalence margin from consequence, not null noise;
5. H3 equivalence precision/power;
6. H4/G2;
7. execute G4 preservation qualification;
8. G3 capacity/functional-form/estimand-matched attacker;
9. remaining F13/F14/F15;
10. terminal masking only after all blockers close;
11. training authority last.

## Start commands for a future agent

1. Fetch PR #33 live head and read `analysis/v5_full104_information_channel_redteam_20260920/README.md`.
2. Read `CROSS_AUDIT_INTERACTIONS.md` but verify it against the latest audit scripts/results because review comments may have forced revisions.
3. Read PR #34 supporting files under `analysis/v5_full104_information_channel_redteam_20260920/supporting_gpt_parallel/`.
4. Re-read review comments on PR #33 before accepting Audit B/C/D/F/G statuses.
5. Never promote historical/supporting numbers to current authority.

`TRAINING_OFF` remains the controlling state.
