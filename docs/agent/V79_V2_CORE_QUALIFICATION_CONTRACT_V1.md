# V79 V2_CORE: frozen model and prospective synthetic-qualification contract (V1)

> **SUPERSEDED (2026-10-11, PR #286 controller ruling 6113874774).** This V1 contract (SHA-256 `70edabb8…`) is historical pre-controller draft evidence only, never launch authority. Its JSON is kept unchanged. The amended candidate is `V79_V2_CORE_QUALIFICATION_CONTRACT_V2_DRAFT.md`, which is pending controller acceptance.

Date: 2026-10-11

Status: `FROZEN_BEFORE_ANY_QUALIFICATION_FIT`. No qualification fit and no world generation has run.

Authority: this document is a readable summary. The authority is the machine-readable contract:

| item | value |
|---|---|
| contract JSON | `results/v79/v2_core_qualification/V79_V2_CORE_QUALIFICATION_CONTRACT_V1.json` |
| SHA-256 | `70edabb86c93a9f4ddb4dfb27bded60bab355c90b99d49f49cb851b4c1e58540` (also in the `.sha256` file beside it) |
| builder | `scripts/v79/build_v79_v2_core_contract.py`; `--check` rebuilds the JSON and compares byte for byte |

The JSON holds every number exactly once. Derived numbers (the multiplicity level, the gene count, the binomial thresholds and the planting magnitudes) are computed by the builder from declared constants and committed inputs. Fitting and scoring code must refuse any contract whose hash differs.

Boundaries:
- `training_authorized=false`.
- No real-TRAIN posterior inference, no factorial science (H0–H3, C_OBS, C_BIO), no TEST, no Morabito, no pathology, no target discovery, no SCENIC+/ATAC in truth, no operator in the model, no 18-fit campaign, no Bernoulli V2/V3 rescue, no Stage4/500K.

## 0. Development finding that shaped this contract (for controller audit)

While setting priors, I found that the S174 compact cache, the V3 replay and the first planting calibration all treated **structurally unmeasured** entries as **measured zeros**.

| what | value |
|---|---|
| unmeasured cell-gene entries treated as zeros | 5.76% |
| genes affected | 59 of 500 |
| genes fully unmeasured in at least one source | 56 |
| genes partially unmeasured inside NPH52 (matrix level) | 3 |
| nonzero counts on an unmeasured entry | 0 (the authority and the cache agree) |

How it was established:
- Authority: `results/v4/stage81a2r_foundation_molecular_address_measurement_support_candidate.csv.gz`, frozen at `95d2cafe`.
- Join: cache operator index → S174 bridge `matrix_id` → matrix-level measurement support.
- Record: `results/v79/development/v2_core_planting_calibration/V79_G500_STRUCTURAL_SUPPORT_DEV.json` and `struct_mask.py`.

This violates the hard invariant `MEASURED_SCALAR != STRUCTURALLY_UNMEASURED`.

Effect on the ratified V3 answers (a descriptive split made after the fact, not a predeclared rule):

| question | 28 affected replay genes | 172 clean genes | reading |
|---|---|---|---|
| C, source (detection) | median gain +0.088 | median +0.00094, 74% improved | the large skewed mean came from structural zeros; source in detection is still supported on clean genes |
| D, operator at λ=1 (detection) | — | median +0.00055, 56% improved | unchanged |
| positive part | — | — | unaffected (no zeros enter it) |
| support panel (det / pos) | — | donor 28/45 and 18/45; operator-beyond-donor 34/45 and 21/45 | still far above chance |

**The V2_CORE term set is unchanged.** What this contract does about it:
1. The V2_CORE likelihood runs only over structurally measured entries. This enforces the invariant; it is not a new term.
2. Every world plants structural absence at the development rate.
3. Planting magnitudes come from a **masked** recalibration (V2). The masked calibration shrinks the detection |source| p95 from 8.75 to 1.25 logit, and moves the intercept p05 from −6.6 to −3.4.

## 1. Model (V2_CORE)

The model is fitted per gene, as two independent parts. Genes are fitted separately, so the model is modular.

| part | specification |
|---|---|
| detection | `y ~ Bernoulli(p)`, `logit p = α + β1·z + β2·(z²−1) + class + source + u[donor]`, over measured cells (a measured zero is y=0) |
| positive | `log y ~ Normal(μ, σ)` for measured y>0, `μ = α⁺ + γ1·z + γ2·(z²−1) + class⁺ + source⁺ + u⁺[donor]` |

Covariates and parameterization:
- **z** is the standardized log library over all cells of the design (ddof 0).
- **Class and source** use normalized Helmert sum-to-zero contrasts (two each).
- **Donor** uses a within-source normalized Helmert block basis W, **non-centred**: `u = W·(σ_d·ε)`, ε ~ N(0, I). It is non-centred in every world, with no switching.

Excluded: operator/matrix, donor×class, source×class, dataset/matrix ID. The positive family is lognormal; ZTNB is a separate challenger and is not compared here.

Numerics: float64 and CPU. These are small per-gene fits, so precision cannot be the cause of a failure.

## 2. Priors (frozen; z units)

| part | parameter | prior |
|---|---|---|
| detection | α | N(−1.2, 2.5) |
| detection | β1 | N(0, 2) |
| detection | β2 | N(0, 0.5) |
| detection | class contrasts | N(0, 1.5) |
| detection | source contrasts | N(0, 1.5) |
| detection | σ_d | HalfNormal(1) |
| positive | α⁺ | N(0.5, 1) |
| positive | γ1 | N(0, 1) |
| positive | γ2 | N(0, 0.5) |
| positive | class contrasts | N(0, 0.75) |
| positive | source contrasts | N(0, 0.5) |
| positive | τ | HalfNormal(0.5) |
| positive | σ | HalfNormal(1) |

Rule for setting them:
- Slopes and contrasts are centred at 0; intercepts at the masked development median.
- Each scale puts the development p99 magnitude within about 1.5 prior SD. SD priors have scales above the development p99.
- The one documented exception is the detection |source| p99 (about 7.9). That is near-separation in about 1% of genes; it is not planted.

The second stage is descriptive in this qualification:
- an across-gene normal–normal model per quantity type, with priors taken from that type's per-gene prior, solved on an exact grid;
- a disattenuated cross-gene donor correlation, compared against a planted shared donor factor (λ = 0.6 in half of the genes).

## 3. Sampler and frozen recovery path

Settings: NUTS, 4 chains run in parallel, 1,000 warmup and 1,000 draws each, tree depth 10.

| step | what happens |
|---|---|
| primary | target_accept 0.90 |
| one escalation | on any divergence: refit fresh at 0.99, the terminal value of the existing A5_V2 ladder |
| one extension | on an R-hat/ESS miss with no divergence: continue the same chains for +1,000 draws, no new warm-up |
| otherwise | NOT_DIAGNOSED, and the world fails `CONVERGENCE_ALL_FITS_DIAGNOSED` |

"Diagnosed" means, on every site: R-hat ≤ 1.01, bulk and tail ESS ≥ 400, and 0 divergences.

Each attempt records: seed, chains, warmup, draws, target_accept, extension flag, divergences per chain, worst R-hat, worst bulk and tail ESS, wall time, CPU time, peak working set and mean tree steps.

## 4. Worlds (G = 45 genes each; seed root 31000000, verified unused)

Two designs:
- **BASE** is a crossed design with S174 sizes: 62/19/68 donors, cells per donor resampled per source, class and log library iid, and matrices crossed with donors. It is generated once and shared by Q00–Q09.
- **S174** is the exact S174 design arrays (value-blind extract `V79_S174_DESIGN_ONLY_V1.npz`, SHA-256 `10e3c472…`). They come from the authenticated G500 cache; no expression is read.

Planting:
- Q00 rules form a Latin hypercube over the masked development per-gene values, spanning p05–p95.
- The detection intercept is solved so that the planted prevalence holds over the measured cells.
- Contrast signs are seeded.

| world | design | change from the Q00 rules |
|---|---|---|
| Q00 baseline | BASE | none |
| Q01 weak donor | BASE | σ_d = 0.191, τ = 0.044 (0.5 × dev p05) |
| Q02 strong donor | BASE | σ_d = 1.087, τ = 0.515 (2 × dev p95) |
| Q03 weak source | BASE | both \|source contrasts\| = dev p25 (0.121 / 0.025) |
| Q04 source absent | BASE | source = 0 |
| Q05 class absent | BASE | class = 0 |
| Q06 quadratic absent | BASE | β2 = γ2 = 0 |
| Q07 donor absent | BASE | σ_d = τ = 0 |
| Q08 sparse detection | BASE | prevalence log-uniform on [0.005, 0.05] |
| Q09 positive tail | BASE | σ = 1.458 (2 × dev p95) |
| Q10 S174 imbalance | S174 | Q00 rules on the real weak-crossing design (single-class matrices in HVS/NPH52; class–depth confounding about 1.45 SD) |
| Q11 omitted operator | S174 | Q00 rules plus per-matrix offsets, SD 0.5 × the gene's donor SD, centred within source, **not fitted** |

Structural absence, in every world:
- 5 of 45 genes have it: 1 measured in a single source, 3 with one source fully unmeasured (sources drawn in proportion 38:20:10), and 1 with 3 of 7 NPH52 matrices unmeasured.
- Unmeasured entries are written as −1 (a poison value), so any read of them is detectable.

Held-out replicates are generated per world: same donors with new noise, and new donors.

The realized truth tables, world manifests and file hashes are generated from these seeds and **committed before any fit**.

## 5. Gates and thresholds

Multiplicity:
- There are 264 statistical gates across all worlds and parts (292 gates in total).
- The family-wise false-fail rate is 0.05 (convention), Bonferroni-corrected to **α = 1.89×10⁻⁴ per gate**.

Gene count from the precision budget:
- G is the smallest gene count at which the bias t-test detects a 0.75-SD standardized bias with power 0.80 at that α.
- Result: **G = 45**, with t_crit 4.07, power 0.816, and a minimum significant mean bias of 0.61 SD.
- Genes are the independent unit: they have independent truths, donor effects and noise.

| gate | rule |
|---|---|
| convergence | every fit diagnosed after the recovery path (RULE) |
| coverage, fixed effects pooled | per-gene 90%-interval coverage, one-sided t across genes at α |
| bias, per fixed type, donor SD and σ | FAIL iff \|t\| > t_crit **and** \|mean z\| > 0.5 (materiality, convention) |
| coverage of donor SD and σ (one per gene) | exact binomial (max passing misses: 13 of 45) |
| coverage of donor effects | per-gene coverage, t across genes |
| absent effect (Q04–Q06) | the 90% interval excludes 0, tested at the coverage rule (nominal 10%); rates at 95% and 99% also reported |
| donor absent (Q07) | false positive if posterior q05(SD) > 0.1 × dev p05 donor SD (0.038 / 0.0088); binomial against 5% (max passing 9 of 45) |
| type-S (Q03) | wrong sign among intervals that exclude 0; binomial against 5% |
| PPC | count of (gene, statistic) with ppp < 0.01 over 1,000 replicates; binomial against 1% |
| population donor-SD ratio | ratio in [0.80, 1.25] (convention); gated for detection in Q00/Q02/Q10 and for positive in Q02 only |

The PPC statistics are:
- zero fraction overall, by depth decile, by class and by source;
- positive mean overall and by depth decile;
- positive variance;
- positive q01 and q99;
- donor heterogeneity in both parts.

**LIMIT-class gates (predeclared).** These report what a real result can and cannot mean; they do not fail the model.
- **Q11:** the donor gates and PPC. An omitted operator is expected to be partly absorbed into donor effects. Every fixed-effect gate in Q11 stays FAIL-class, because class and source must remain stable.
- **Donor-SD bias in Q01 (both parts), Q08 positive and Q09 positive.** These place the SD near zero or under weak information, where a proper prior pulls the posterior mean above a small truth. Coverage stays FAIL-class there.

**Descriptive** (prospectively declared, with the rationale in the JSON):
- correlation, RMSE and sign;
- donor rank, calibration slope and shrinkage;
- held-out log loss and LPD against the oracle, 10-bin calibration, and prevalence, including the low-prevalence subset;
- the second stage;
- Q11 minus Q10 contrasts.

## 6. Terminal logic and run policy

- **World verdict:** FAIL if any FAIL-class gate fails; PASS_WITH_LIMITS if only LIMIT-class gates fail; PASS otherwise.
- **Combined:** PASS iff all 12 worlds are PASS or PASS_WITH_LIMITS. The terminals are:
  - PASS: `V2_CORE_SYNTHETIC_QUALIFICATION_PASS__CONTROLLER_AUDIT_REQUIRED__REAL_TRAIN_POSTERIOR_INFERENCE_STILL_OFF__FACTORIAL_SCIENCE_OFF__TRAINING_OFF`
  - FAIL: `V2_CORE_SYNTHETIC_QUALIFICATION_NOT_QUALIFIED__NO_TUNING__CONTROLLER_REVIEW_REQUIRED__REAL_TRAIN_POSTERIOR_INFERENCE_OFF__TRAINING_OFF`
  - INFRASTRUCTURE: `..._INCOMPLETE__INFRASTRUCTURE_STOP__CONTROLLER_REVIEW_REQUIRED`
- **Run policy (a choice the controller may override before launch):**
  - All 12 worlds run to completion in the fixed order, even after a world FAILs. Nothing about later worlds can change, and the full verdict map is more useful for review.
  - An infrastructure failure (crash, hash mismatch, poison read) stops the run immediately.
  - No tuning and no reruns with changed settings. STOP for controller audit in every outcome.

## 7. Resources

- **Environment:** Windows conda env `v79-bayes` only: Python 3.11.17, numpy 2.0.2, scipy 1.17.1, jax/jaxlib 0.4.35, numpyro 0.15.3, arviz 0.20.0. The lock is `inputs/V79_BAYES_ENV_PIP_FREEZE.txt`. No WSL fits.
- **Concurrency:** one heavy job at a time. A heavy job is one world process fitting its genes serially, detection then positive per gene.
- **Settle and checkpoints:** 120 s settle between worlds. Each fit record is written atomically, so a world resumes at its first missing fit.
- **Outputs:** compact JSON summaries plus 200 thinned donor draws (float32). No full chains are stored.
- **Estimate (to be replaced by the engineering benchmark):**
  - 1,080 fits;
  - about 1.1 h per world;
  - about 14 h without retries, about 17 h with a ×1.2 allowance;
  - under 2 GB of memory and 4 of 16 cores.
- **Engineering benchmark before launch:** 2 genes on an unscored engineering world, seed root 31999999. If the projection exceeds 72 h: STOP and report, with no setting changes.

## 8. Declared limitations

1. Positive values are continuous lognormal. Discretization of real integer counts is not tested; that is the ZTNB question.
2. Planting magnitudes come from ridge proxies; the development donor SDs are biased low.
3. The truths are fixed values, not prior draws, so coverage for weakly identified quantities is not guaranteed nominal.
4. Detection operator remains `PRIOR_SENSITIVE__UNRESOLVED`. Q11 tests one mild omitted-operator rule only.
5. The second stage is descriptive.
6. S174 is smaller than corrected TRAIN.
7. The roughly 1% near-separation tail is not planted.

## 9. Next steps (not started)

1. Implement test-first (`v79_v2_core.py`, the world builder, the runner and the scorer) and get green CI.
2. Generate the 12 worlds and commit the realized truth tables, manifests and hashes.
3. Run the engineering benchmark, then the qualification worlds Q00–Q11.
4. Write the per-world results and the combined receipt, then STOP for the controller audit.
