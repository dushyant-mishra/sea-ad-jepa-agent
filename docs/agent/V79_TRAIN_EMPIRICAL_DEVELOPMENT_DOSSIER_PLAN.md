# V79 corrected-TRAIN empirical model-development dossier: proposed plan

Date: 2026-10-11

Status: `PROPOSED__NOT_STARTED__AWAITING_CONTROLLER_DECISIONS_D1_TO_D5`

Lane state: `BAYESIAN_MODEL_DEVELOPMENT_HOLD__DETECTION_NOT_QUALIFIED__GAUSSIAN_LOGNORMAL_ZTNB_UNADJUDICATED__EMPIRICAL_TRAIN_CHARACTERIZATION_REQUIRED_BEFORE_NEW_CONFIRMATORY_QUALIFICATION__TRAINING_OFF`

## What this dossier is, and is not

The dossier describes the corrected TRAIN count distribution so the next model generation is built on it. It is not a test of the current models.

- **Exploratory.** We may look at it, iterate against it, compare models and reject families.
- **Not confirmatory.** Nothing here qualifies a family, fixes a frozen parameterization or produces a number for the synthetic generator.
- **No export.** Every output is labelled `DEVELOPMENT_ONLY`. No posterior or point estimate leaves the dossier for H1/H2, PR #253 or any synthetic world.
- **Unchanged until specified.** The current frozen models (`GAUSSIAN_NC_DK_V1`, `LOGNORMAL_NC_ALL_V1`, `ZTNB_NC_DONOR_DK_V1`) stay frozen and unadjudicated. No V2/V3 redesign, no new priors and no new qualification simulations happen until this plan is approved.

## Data, access and firewall

- **Substrate: corrected TRAIN only.** This is the G1b-authorized S174 rebuilt cache: 42 count shards plus metadata, every byte checked against the PR #244 custody hashes (`results/v79/V79_S174_SHARD_AUTHORITY_V1.json`).
- **Size:** 4,726 cells × 41,238 addresses. The gene universe is the 14,417 addresses detected in more than 5% of TRAIN cells.
- **Design:** 149 donors (HVS 62, SEA_AD 68, NPH52 19), 42 operators, 3 sources and 426 donor-class groups. 148 of the 149 donors appear in two or more operators.
- **One authenticated read.** The shards are streamed once into a compact, hash-bound analysis cache using `build_v79_analysis_cache.py`. That builder is tested on synthetic shards only and has never run on real data. It is verified exactly against the current loader before any analysis. No further full-shard reads follow.
- **Columns read:** counts, library size, detected-feature count, donor, broad class, source, operator. Nothing else.
- **Firewalls:**
  - no pathology column, no TEST/Morabito, no DEV/SEALED;
  - no target-discovery gene list, SCENIC+ or ATAC evidence;
  - no V78 outcomes;
  - no JEPA training, no H0/H1/H2/H3 factorial;
  - no export of provisional Bayesian parameters to the generator.
- **Gene panels stay identity-blind.** Full-universe marginal summaries use all 14,417 addresses. Model comparisons use panels drawn by the existing prevalence-stratified, seed-fixed sampler. Genes are never chosen by name.

## The characterization (controller items, in order)

Each analysis says what it measures and which modelling decision it informs. "Expected under NB" means a negative binomial with a per-cell library offset and per-gene, per-class means and dispersion fitted in the development set. Sampling noise for every comparison comes from a parametric bootstrap. Donors are the independent unit; cells sharpen within-donor estimates, but the effective sample size is never the cell count.

| # | Analysis | Method | Informs |
|---|---|---|---|
| 1 | Per-gene mean–variance | Variance against mean on the count scale, within each broad class (so class composition does not pass as overdispersion); Poisson, NB1 (linear) and NB2 (quadratic) reference curves | Count family; NB1 vs NB2 |
| 2 | Zero fraction vs mean count | Observed per-gene zero fraction against the Poisson and NB predictions at the same mean, dispersion and library offsets | Whether zeros need anything beyond NB |
| 3 | Zero fraction vs library depth | Per gene, by library-depth decile, observed against expected NB zeros | Whether a depth-only offset explains detection |
| 4 | Zero fraction within broad class | Analysis 2 stratified by class | Class-specific excess zeros |
| 5 | Zero fraction within donor and operator | Analysis 2 stratified by donor and by operator, only where a stratum has at least 30 cells; the rule is fixed before any data are seen | Donor- or operator-specific detection |
| 6 | Positive counts | Mean and variance of positive counts; upper quantiles and maxima; PIT/QQ against zero-truncated NB and against log-normal fits | ZTNB vs log-normal for the positive part |
| 7 | Empirical overdispersion | Distribution of per-gene dispersion (method of moments and maximum likelihood); its dependence on the mean; how much of it disappears after conditioning on class and donor | Dispersion structure; heterogeneity mistaken for overdispersion |
| 8 | Can NB alone reproduce the zeros? | Simulate NB counts from the fitted means, dispersions and offsets; compare zero fraction per gene, per cell and per depth bin; report the distribution of excess zeros (observed minus expected) against the bootstrap envelope | The key question: is a separate Bernoulli/detection process needed? |
| 9 | Does a hurdle or zero-truncated model help materially? | Per-gene NB, hurdle-NB and zero-inflated NB with class effects and log-library offset, compared by donor-grouped cross-validated predictive log-likelihood per cell. "Material" needs a numerical cut, which the controller sets before item 9 runs (D5) | Whether a detection component earns its place |
| 10 | Donor variance | Per-gene mixed models (random donor) on the count scale (NB-GLMM) and on the log-normalized scale | Donor component size and spread across genes |
| 11 | Class variance | Fixed class effects on orthonormal contrasts, as in the current models, plus their spread across genes | Class component |
| 12 | Donor × class | Random donor-class term (426 groups), with its share relative to donor alone | Whether the donor-class component is supported |
| 13 | Source and operator after class and depth | Source fixed effect (3 levels) and random operator within source, conditional on class and the library offset | Observation-process components |
| 14 | Crossing and aliasing (design only) | Contingency tables donor × operator, donor × class, class × source, operator × source; rank and condition number of the random-effect design matrices; effective levels per component | Which components the design can separate at all |
| 15 | Empirical non-identifiability | Combine 14 with profile-likelihood flatness in the per-gene fits; simulate from fitted components, refit, and check what comes back | Which components must be merged, fixed or dropped |
| 16 | Residual covariance and eigenspectrum | After removing fitted fixed and random effects: gene–gene residual correlation within class; eigenspectrum against a within-stratum permutation null; computed with the existing reference builders' statistics (`v79_geometry`) so later model comparison uses the same definitions | What the generative model must reproduce beyond the marginals |

## Then: a model-development tournament (controller item 8; outlined only)

- **Candidates:**
  - a Gaussian/log-scale model on log-normalized expression;
  - an NB count model;
  - NB plus an explicit detection or hurdle component, only if items 2, 3, 8 and 9 demand it;
  - ZTNB or log-normal for positive counts, where item 6 favours one.
- **Comparison:**
  - developmental PPC of the geometry statistics above (marginals, zero structure, depth relation, class and donor structure, eigenspectrum);
  - donor-grouped cross-validated predictive log-likelihood.
- **Status of results:** they are development evidence only. Choosing a candidate is followed by item 9 of the controller plan: new synthetic qualification worlds not used in development, a freeze, and a fresh confirmatory recovery suite.

## Decisions needed before execution

- **D1: open corrected TRAIN expression counts for development.** The previous contract said not to touch real expression values until the recovery and benchmark gates pass. This plan needs that lifted, for development only, under the firewall above.
- **D2: what stays sealed.** All later confirmation is to use new synthetic worlds. But the earlier plan also had a held-out real-data PPC (Q5) on TRAIN, and a holdout that informs model development stops being a holdout. Two options:
  - **(a) Recommended:** before any expression value is read, freeze a donor-level split stratified by source. Roughly two thirds of donors (about 99) go to development. About one third (about 50: 21 HVS, 23 SEA_AD, 6 NPH52) are sealed for the final held-out PPC of the selected family. Optionally, also seal a gene panel disjoint from the development panels.
  - **(b)** Develop on all TRAIN donors, and accept that any later real-data PPC is development evidence, not confirmation.

  The cost of (a): 19 NPH52 donors leaves only 6 sealed, so NPH52-specific conclusions will be weak.
- **D3: may the next generation include a newly developed detection component?** Detection V2 is `NOT_QUALIFIED`, and the ruling was "no V3". If items 2, 3, 8 and 9 show NB cannot produce the observed zeros, would a detection or hurdle component designed in this development phase be admissible as a new candidate, confirmed later on new worlds? Or does the detection ruling exclude any detection mechanism from this lane? I will not treat a new candidate as a rescue of V2 without your ruling.
- **D4: unit of analysis for the variance components.** Options are cell-level mixed models (donors as the independent unit for inference) or donor × class pseudobulk for the variance decomposition, with cell-level models kept for the zero and depth analyses. I recommend the former for items 10–13 and the latter as a sensitivity check.
- **D5: the numerical cut for "materially improves" in item 9.** For example, a minimum gain in cross-validated log-likelihood per cell, judged against its donor-bootstrap uncertainty. It should be set by you, not by me after seeing the data.

## Compute and order

| order | step | cost |
|---|---|---|
| 1 | Authenticated compact cache, built once | Minutes |
| 2 | Items 14 and 1–7: marginals, zeros, depth, positives, dispersion | Minutes on CPU, vectorized over all 14,417 genes |
| 3 | Items 8–9: per-gene simulations and GLM comparisons | Parallel CPU workers, each gene with its own deterministic seed; roughly one to a few hours |
| 4 | Items 10–13 and 15: mixed models on 200–500 panel genes | The expensive part; at most two concurrent processes until a single-process benchmark exists |
| 5 | Item 16: residual eigenspectrum | Minutes to an hour |

No GPU is needed. All outputs go under `results/v79/development/`, with the input hashes, the code commit and the `DEVELOPMENT_ONLY` label.

## What this plan does not change

- Detection stays `NOT_QUALIFIED` and unavailable downstream.
- Gaussian, log-normal and ZTNB stay `UNADJUDICATED__METHODOLOGICAL_HOLD`.
- No corrected-TRAIN posterior inference runs under the current frozen models.
- Training stays off.
