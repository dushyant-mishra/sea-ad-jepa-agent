# JEPA: independent sham-null exchangeability stress test

**28 September 2026 · separate local CPU study · synthetic only · no real readout opened**

## Why this test was run

The remaining scientific decision is to nominate real four-gene sham programs whose measured behavior under technical nuisance is comparable to a real teacher program. The frozen v7 statistical test uses the empirical rank of the real program among `B=199` sham statistics. A previous structural preflight (`sham_preflight_v0.py`) verifies exactly 199 **distinct** gene quadruples per directed comparison and reports reuse, but deliberately does not claim biological exchangeability or enforce an unsupported overlap threshold.

**New stress question:** Can a roster with 199 distinct quadruples pass the existing structural preflight even when the sham statistics cannot serve as an exchangeable null for a distinct real program? **Yes**, on an intentionally pathological but structurally valid fixture.

## Physical results and limits

1. Build 199 unique synthetic quadruples for one of the six directed comparisons. Three anchor genes recur in *every* quadruple; the fourth gene changes. All entries remain outside the frozen 29-address program/readout/reference set and the 19 nuisance addresses, contain fit-only metadata, have source-axis flags, and are individually distinct. The existing v0 structural preflight **correctly reports** maximum gene reuse = 199 but still returns `STRUCTURAL_PREFLIGHT_PASS_ONLY_NOT_BIOLOGICALLY_QUALIFIED`. This is not a defect against v0's stated scope: v0 explicitly leaves the scientific null design unresolved.
2. Isolate the statistical consequence with a Gaussian toy. The real statistic R is N(0,1); each of 199 sham statistics is *marginally* N(0,1), but all shams share a nuisance/error component U. Their pairwise correlation is ρ. The real test statistic uses a distinct gene panel and is independent of U. We compute the frozen-style sham-rank p-value `(1 + count(sham >= real))/200`, and, in a separate illustrative extension, apply BH at q=.05 to six independent all-null test directions. The experiment has **no biological signal in any direction**.

| Sham pairwise correlation | Per-direction P(sham-rank p ≤ .05) | P(BH rejects ≥1 of 6 all-null tests) |
|---:|---:|---:|
| 0.00 | 0.0502 | 0.0316 |
| 0.50 | 0.1684 | 0.3308 |
| 0.75 | 0.2656 | 0.6417 |
| 0.95 | 0.3952 | 0.9106 |
| 1.00 | 0.4999 | 0.9843 |

25,000 independent simulated six-test batches per row, explicit deterministic seeds, no outcome tuning. For three of four shared genes, a **linear equal-weight** gene statistic has illustrative sham-sham correlation 3/4; this correspondence is not an estimate for the frozen negative-binomial estimator. At ρ=1, the single-test result follows exactly without simulation: all shams equal U, independently drawn R and U have P(R > U)=1/2, and the rank p-value equals its minimum 1/200 in half the null experiments.

**Interpretation:** marginal abundance/sparsity/reliability matching, a count of 199 distinct quadruples, and even a nominal p-value formula do not guarantee the requisite **joint real-versus-sham exchangeability**. Dependence alone is not automatically invalid: some randomization designs remain exactly calibrated with dependent sham draws if the real program and sham collection are jointly exchangeable. This specific adversary violates that joint condition. The six-test BH column intentionally omits v7's additional two-thirds donor-consistency qualification and uses independent directed test statistics, so it is **not** a forecast of the full human study's type-I error.

3. A second purely arithmetic asymmetry exists in the frozen denominator: `D_i(P,Q)` excludes the **true P and Q** partners, but ordinary candidate sham genes are still included in D. In an exact counterfactual with baseline D=5,000, adding 10 molecules to true P increases `total_all` by 10 and increases excluded counts by 10, leaving D unchanged. Adding 10 to a sham quadruple increases `total_all` but not excluded counts, yielding D=5,010; the illustrative log-offset shift is `log(5010/5000)=0.001998`. Its real-world size and direction are **not measured here**, but the asymmetry must be checked in full-pipeline nuisance simulations before treating the real/sham test as exchangeable. Redefining D per sham without freezing the resulting estimand would introduce a different comparability problem.

## Executed scope

- `python sham_overlap_stress_v1.py`: accepted the adversarial metadata fixture by the old **structural-only** preflight and executed 125,000 six-direction null batches across the five correlation settings.
- `python -m pytest -q --junitxml=pytest_sham_overlap_v1.xml test_sham_overlap_stress_v1.py`: **16/16 passed**, no skipped tests. The tests confirm fixture non-vacuity, overlapping but distinct quadruples, fit-only metadata, forbidden-address refusal, duplicate detection, exact BH arithmetic, null calibration under independent shams, miscalibration under dependence, analytic perfect-overlap behavior, repeatable seeds and denominator asymmetry.
- This code does **not** run the real NB GLM, test disease biology, prove a particular real-gene sham is invalid, or license protected-data access. The real-vs-sham joint distribution is a deliberate toy counterexample.

## Concrete decision for Claude

Retain the working v0 preflight as a **necessary structure check**; do not promote its PASS to statistical qualification. Before choosing the 199 shams and opening any reserved outcome, freeze a scientific qualification that:

1. Requires a fully enumerated, authenticated candidate pool, source-specific measurable support and fitting-donor-only statistics. Report cross-sham feature reuse, overlap matrix and across-sham covariance; do not assert independence solely because quadruples are distinct. Predeclare any restriction on overlap, or calibrate the actual dependent selection algorithm, without looking at reserved outcomes.
2. Assesses **joint** real-versus-sham nuisance behavior, including latent capture variability after conditioning on measured depth, gene-specific capture/dropout, source effects, coexpression/biological annotation and possible real biological relationships to Q. Fitting-only proxies cannot certify unobserved latent nuisance by themselves.
3. Explicitly tests the true-P-versus-sham **denominator self-inclusion asymmetry** on realistic count-only synthetic fixtures and an outcome-blind, independently prespecified *nonprotected* placebo. If alternative offsets or a common excluded pool are considered, document that they alter the estimand and qualify them prospectively.
4. Evaluates the entire six-directed null with the frozen donor-consistency and multiplicity conditions after the sham-selection algorithm is sealed. A toy rank calibration alone is necessary but not sufficient.
5. Preserves original v7, all six historically reserved identities and the CSF1R exposure firewall. Do not access protected readouts to select shams, retune cutoffs or choose which comparisons to report. If nuisance exchangeability remains undefended, record **COUNT_READOUT_INSUFFICIENTLY_IDENTIFIABLE_UNDER_TESTED_NUISANCE**, not absence of biology.

**Separate R7 qualification:** negative historical out-of-sample R² for its technical baseline signals poor generalization on the scrambled-input small-sample fixture. The cause is not identified uniquely: small samples/overfitting, mislabelled response, between-donor shift and low count support are competing explanations. The corrected cohort has a different source-specific donor census, so do not assert the six prospective tests *will* reproduce the R7 outcome without a prospective donor/rank/stratum feasibility check.

**Separate gatekeeping observation (source inspection, not executed):** at `PR178@82e3fe1f`, `teacher_fidelity_gate_executor_v5.py` makes its full-run `arm_pass` by checking `r['qualifies'] == cfg['want']`, i.e. the *full channel*. Its `assert_complete` requires channels to be present but not to have the required composition/amplitude pattern, and the number of calibration datasets is command-line overridable. The historical v4 receipt validator v2 cannot validate the different v5 receipt schema automatically. Close that acceptance-binding gap with adversarial tests; none of these prospective issues retrospectively change v4's recorded numbers.
