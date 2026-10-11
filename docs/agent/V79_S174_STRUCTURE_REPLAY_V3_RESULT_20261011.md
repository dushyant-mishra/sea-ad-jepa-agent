# V79 exact-S174 structure replay (operator-penalty repair): result and interpretation

Date: 2026-10-11

Terminal: `EXACT_S174_STRUCTURE_REPLAY_COMPLETE__PRIMARY_OPERATOR_LAMBDA_1__FROZEN_SENSITIVITY_0p25_1_4__DEVELOPMENT_ONLY__CONTROLLER_MODEL_FREEZE_REQUIRED__BAYESIAN_CONFIRMATION_OFF__TRAINING_OFF`

This is development evidence only. It is not confirmatory and not synthetic-consumable. No NUTS was run, no parameters were exported, `training_authorized=false`.

## Provenance

| item | value |
|---|---|
| code | `02fb78c36473d9863ae9482619133c052ba4a480` (PR #283), implementing the PR #280 ruling of 2026-10-11T19:40:47Z |
| CI | run `38170751947`, job `114562666364`, **22 passed** |
| executed from | `git archive` snapshot `/d/v79_runs/02fb78c3`; Python 3.9.7, NumPy 1.24.2, SciPy 1.10.1 |
| input | the **same** authenticated G500 cache (not rebuilt): SHA-256 `2f922c08e38c104ed7149a2ee74a5e3adc8c287ef5b5c07ea1b5b862f92a6a62`, receipt `3a5ed9ef…`, built from 84/84 verified S174 shards at `615b55eb` (PR #280) |
| command | `run_v79_s174_structure_replay.py <cache> <receipt> <out> --genes 200 --support-genes 50 --permutations 99 --folds 3 --seed 20261011` |
| output | `V79_S174_STRUCTURE_REPLAY_DEVELOPMENT_V3.json`, SHA-256 `78db6d310797533f4af80652b45dc0b5b8b005fd7d990d7f1b760735c8c6f8bc` |
| population | 4,726 cells; 149 donors; 200 replay genes (prevalence 0.050–0.927); 50 support genes; 3 held-out-donor folds |

**Numerical failures:**
- Primary λ = 1: none (every fit converged).
- Sensitivity λ = 0.25: one detection fit failed (gene position 362, prevalence 0.10, 1 fold). It is recorded, not rescued. This makes λ = 0.25 non-material under the convention.
- Positive lognormal: no failures.

## Held-out-donor metric table (all 200 genes)

| nested model | detection log loss, mean / median (lower is better) | positive lognormal LPD, mean / median (higher is better) |
|---|---|---|
| depth linear | 0.43241 / 0.45383 | −0.67188 / −0.74600 |
| + quadratic depth | 0.43114 / 0.45390 | −0.66344 / −0.72554 |
| + broad class | 0.42289 / 0.44659 | −0.65277 / −0.72164 |
| + source | 0.40031 / 0.42774 | −0.64926 / −0.72633 |
| + operator-within-source (λ = 1) | 0.39281 / 0.42181 | −0.65580 / −0.72671 |

## Per-gene nested deltas

A positive delta means the richer model predicts held-out donors better. These are descriptive summaries computed after the run (`V79_S174_REPLAY_PER_GENE_NESTED_DELTAS.json`). Only the operator rule was predeclared. Intervals come from a gene bootstrap, which is optimistic because genes share donors.

| step | detection: median [95%] · share of genes improved | positive: median [95%] · share of genes improved |
|---|---|---|
| A: quadratic depth | +0.00047 [+0.00025, +0.00067] · 73% | +0.0054 [+0.0037, +0.0087] · 73% |
| B: broad class | +0.0025 [+0.0019, +0.0033] · 84% | +0.0025 [+0.0019, +0.0035] · 76% |
| C: source | +0.0015 [+0.0009, +0.0024] · 78% (mean +0.0226, skewed) | +0.0008 [+0.0002, +0.0016] · 59% |
| D: operator (λ = 1) | +0.00035 [−0.00014, +0.0019] · 55% | −0.0094 [−0.0120, −0.0070] · 30% |

## Operator robustness under the predeclared rule (λ = {0.25, 1, 4})

| part | λ = 0.25 | λ = 1 (primary) | λ = 4 | ruling |
|---|---|---|---|---|
| detection | median −0.00037, CI [−0.0013, +0.0009], 1 failed gene: not material | +0.00035, CI [−0.0001, +0.0019]: not material | +0.0014, CI [+0.0009, +0.0026], 69% improved: material | **PRIOR_SENSITIVE__UNRESOLVED** |
| positive lognormal | −0.0122, CI [−0.0157, −0.0084] | −0.0094, CI [−0.0118, −0.0071] | −0.0054, CI [−0.0067, −0.0025] | **NOT_SUPPORTED** |

## Random-effect support

Panel: 50 genes, 99 permutations, a per-gene 5% test. By chance alone about 2.5 of 50 genes would be supported; the binomial 99th percentile is 7. Genes share donors, so the counts are not independent.

| component | detection | positive |
|---|---|---|
| donor, after the full fixed structure (λ = 1) | **32/50** | **19/50** |
| operator beyond donor (donor-centred, within-donor null; identical at every λ by construction) | **37/50** | **23/50** |
| donor×class increment after donor | 8/50 | 3/50 |

## Scientific answers A–H (development evidence)

- **A. Depth.** Quadratic depth reproducibly improves on linear depth in both parts: about 73% of genes improve, and the median gain is small but its interval excludes zero. **Supported.**
- **B. Broad class.** This is the most consistent gain after depth (84% of genes for detection, 76% for positive magnitude). **Supported in both parts.**
- **C. Source.** For detection, source adds a clear further gain after depth and class (78% of genes, with a large mean driven by some genes): **supported.** For positive magnitude the gain is small (59% of genes, median +0.0008, interval excluding zero): **weakly supported.**
- **D. Operator-within-source**, under the predeclared rule.
  - Detection is **`PRIOR_SENSITIVE__UNRESOLVED`**: the gain is material only at the strongest penalty, λ = 4, and not at the primary λ = 1.
  - Positive magnitude is **`NOT_SUPPORTED`**: the operator fixed proxy makes held-out-donor prediction *worse* at every penalty.
- **E. Donor.** Residual donor organization is far above chance in both parts (32/50 and 19/50). **Supported.** For positive magnitude the excess is concentrated in a subset of genes.
- **F. Operator beyond donor.** Under the stronger donor-controlled null, residual operator organization survives well above chance (37/50 detection, 23/50 positive).
  - **The tension with D:** operator structure exists within the data, but an unshrunk operator fixed effect does not carry over to unseen donors, and it hurts positive magnitude.
  - **My reading (a judgment, not a finding):** operator effects are real but small and heterogeneous. A strongly shrunk hierarchical operator term might capture them, but this replay does not show that it would.
  - **Status:** operator stays **unresolved** and must not be assumed into the next model.
- **G. Donor×class.** The increment after removing donor is not broadly earned. Positive magnitude is 3/50, which is chance level. Detection is 8/50, just above the chance 99th percentile, but its average excess is negative. **Stays OUT**, with a weak detection-only signal recorded.
- **H. Positive lognormal.** It is a stable development representation on exact S174: all 200 genes were fit for every model with no numerical failures, and the depth and class gains are consistent. ZTNB was not tested here and **remains an unadjudicated challenger.**

## Was the prospective candidate preserved?

**Partially preserved; the operator component is weakened.**

| component | status |
|---|---|
| quadratic depth, broad class, donor | preserved in both parts |
| source | preserved for detection; weakly for positive magnitude |
| donor×class OUT, source×class OUT | consistent with the data |
| operator in detection | unresolved (sensitive to the prior) |
| operator in positive magnitude | not supported as a fixed effect |

Under the controller's decision rule, the operator conclusion is therefore not "broadly preserved". Options for the controller (not my decision):

1. Freeze Candidate V2 **without** the operator term in the positive part. Carry operator in detection only as an explicitly unresolved, strongly shrunk hierarchical component, adjudicated by new untouched synthetic worlds and held-out checks.
2. Return the operator component alone to model development, for example a hierarchical operator effect estimated with shrinkage across operators. No post-outcome covariates, thresholds or selective genes.

Under either option, nothing here authorizes NUTS, the old 18-fit campaign, H0–H3 or training. Detection V2 stays `NOT_QUALIFIED`. Gaussian, log-normal and ZTNB under the old hierarchy stay `UNADJUDICATED__METHODOLOGICAL_HOLD`.

## Committed artifacts

In `results/v79/development/s174_structure_replay_v3/`:
- `V79_S174_STRUCTURE_REPLAY_DEVELOPMENT_V3.json`: the full replay output, with per-gene results by cache position only (no identities);
- `V79_S174_REPLAY_PER_GENE_NESTED_DELTAS.json`: the descriptive deltas and the chance reference for the support counts;
- `replay.stdout.txt` and `replay.stderr.txt` (empty).
