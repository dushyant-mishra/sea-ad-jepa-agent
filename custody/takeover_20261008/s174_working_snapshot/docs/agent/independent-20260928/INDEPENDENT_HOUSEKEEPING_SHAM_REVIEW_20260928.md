# Independent review: housekeeping genes and real-gene shams

**28 September 2026 | JEPA | Source review + independent synthetic counterexample | No protected RNA readouts opened | TRAINING=OFF**

## Material reviewed

The user-supplied `Pasted markdown.md` contains Claude's inspection of `FULL104_MYELOID_R8_PANEL_COUNTS_V1.npz`, with a code excerpt and measured marginal summaries for the 15 program query/partner genes and eight disjoint housekeeping-reference genes. This environment has the transcript and prior V46 files, but **not** a mounted copy of that corrected 187,909-cell NPZ. Its claimed measurements are transcript-derived and have **not** been recomputed here against the physical corrected NPZ.

## What the observed results support

- The eight housekeeping genes are not uniformly high-abundance in these nuclei. Transcript-reported medians: 0.37 raw counts/nucleus and 27.1% detection for the housekeeping set, versus 1.05 and 44.5% for the 15 program genes. These are across heterogeneous sources; PGK1 has only 17,381 available nuclei whereas the other 22 genes have 187,909, so source-specific comparisons are essential.
- A single gene may resemble a candidate program gene in *marginal* statistics: RPL13A 1.13 mean counts / 49.4% detection vs C1QA 1.05 / 48.7% (from the uploaded transcript). **RPL13A is already among the eight frozen housekeeping-reference addresses and is therefore forbidden as an actual sham** under the v7 29+19 exclusion set. It is only an illustrative marginal match.
- The transcript's average normalized-expression correlation with the excluded-29 depth reference, +0.154 vs +0.131, is a measured observable association, **not** an estimate of latent capture sensitivity. Normalizing by a depth term while correlating with that same depth also creates mathematical coupling.

## Interpretations not justified by the reported regressions

The OLS model in the transcript regressed `log1p(count*10000 / total_excluding_29)` on `log(total_excluding_29)` plus operator dummies. Its reported remaining variance (95.5% program; 98.9% housekeeping) is **unexplained by those included predictors**, not biologically explained variance and not a Poisson-noise decomposition. It may contain genuine within-stratum biological variability, latent capture, ambient RNA, zero inflation, count sampling noise and unmodelled donor-by-region structure. Also, `operator_index` in SEA-AD corresponds to a brain-region matrix and cannot be called purely technical. This analysis does not determine whether latent capture is a minor or a dominant confounder after the frozen model's controls.

The claim that a sham's noise floor depends on mean and detection 'and nothing else' is not established: overdispersion, gene-specific capture, residual hidden technical factors, within-quadruple dependence and overlap among the sham draws all matter. Matching 199 sets marginally or observing comparable depth Spearman cannot alone establish the **joint real-versus-sham exchangeability** required for a calibrated sham-rank p-value.

## Executed independent synthetic counterexample

`conditional_capture_counterexample.py` constructs four real genes and four sham genes as geometric/negative-binomial raw counts with a matched Gaussian-copula data-generating process. Both have the *same population* joint distribution with observed log library depth and the *same within-panel dependence*. However, the real gene panel shares a latent **technical** capture fluctuation `H` with an independent biological readout `Q`, while the sham's equally strong within-panel coordination comes from an unrelated shared factor `G`. There is no true program-specific biological association. The synthetic outcome is inspected solely to diagnose null failure, not to choose real shams.

With 120,000 simulated nuclei (seed 20260928):

| Metric | Real panel | Sham panel | Absolute difference |
|---|---:|---:|---:|
| Average per-gene raw count | 1.05350 | 1.05083 | 0.00267 |
| Average per-gene detected fraction | 0.51426 | 0.51154 | 0.00272 |
| Average variance / mean | 2.04347 | 2.06598 | 0.02251 |
| Mean Spearman(normalized expression, observed log depth) | 0.06167 | 0.05847 | 0.00320 |
| Mean within-quadruple Spearman | 0.40285 | 0.40237 | 0.00048 |

Yet after adjusting for observed log depth:

| Conditional synthetic diagnostic | Real | Sham |
|---|---:|---:|
| Correlation with residual **hidden technical capture** | +0.80933 | +0.00217 |
| Correlation with Q, whose only common driver is hidden technical capture | +0.55839 | +0.00388 |

Thus even matching mean, detection, dispersion, measured-depth coupling **and within-quadruple coordination** does not guarantee a valid sham: the real panel appears biologically predictive entirely because of residual technical nuisance the sham does not inherit. This is a *constructive impossibility counterexample* to the sufficiency claim, not an estimate of type-I error for real microglia. It does not run the frozen negative-binomial GLM or full six-directed BH/donor-consistency protocol.

`python -m pytest -q -p no:cacheprovider test_conditional_capture_counterexample.py` passes 13/13 tests: observables matched, hidden nuisance imbalanced, false apparent Q coherence, positive zero count test, residualization algebra, deterministic seeds and second independent seed. See the raw JSON for all four per-gene measurements, not just averages.

## Consequences for the biological design

1. **Do use candidate housekeeping-like genes as nuisance sensors** when their source-specific measurement, lineage constancy and genuine technical sensitivity are demonstrated without using any protected readout. For example, cell-generic stable genes may improve nuisance estimation, but their readout relevance and regional expression still require checking.
2. **Do not use the original eight housekeeping-reference genes as shams**: all eight are excluded by the frozen target and denominator authority. Their observed marginals can inform target ranges but must not be converted into adaptive selection thresholds based on held-out outcomes. For fresh shams, authenticate the distinct candidate pool outside the frozen 29+19 addresses and known program/pathway dependencies.
3. On Claude's machine, build a fit-donor-only, per-source table with raw count mean, detected fraction, dispersion, per-gene depth relationship, residual variance after prespecified measured controls, dropout/mapping/source availability, ambient sensitivity, *within-quadruple* coherence and overlap between proposed sham sets. These are **necessary screening diagnostics**, not proof of the same latent capture mechanism.
4. Require an independent, prespecified nuisance stress test: realistic joint negative and positive synthetic controls with gene-specific capture effects and conditional hidden factors; a nonprotected outcome-blind placebo, if scientifically defensible; and a full-pipeline null calibration retaining the actual 199-sham selection and reuse algorithm. Null shams containing generic programs or MHC co-regulation answer an additional specificity question but are not automatically statistically exchangeable with a true program.
5. Keep the v7 six readout identities and denominator exclusions frozen; maintain the CSF1R exposure firewall; do not open any of those six outcomes to pick candidates or tune matching thresholds. PGK1 is unavailable in SEA-AD; do not treat missing expression as zero. Splits and matching must respect donor and region structure, not pool 187,909 nuclei as independent replicates.
6. If latent-nuisance balance remains undefended, record the planned count-based biological qualification as **insufficiently identifiable under tested nuisance**, not a failure of cellular biology. The alternative composition readout requires an independent prospective reliability and leakage audit.

**Status:** synthetic counterexample physically executed and tests pass; user-supplied 187,909-cell gene summaries source-reviewed only; real shams not chosen; no independent biological qualification; neural training remains OFF.
