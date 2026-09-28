# Real-gene sham feasibility and exchangeability — outcome-blind report

**Date 2026-09-28. Branch `review/v27-authority-root-inventory-20260925`, on top of
`82e3fe1f`. `TRAINING=OFF`. Real teacher-fidelity evaluation CLOSED. No reserved
readout value was read, computed on, or used to select anything in this report.**

**Bottom line: the count-based route is not yet qualifiable, and the obstruction
is now identified precisely rather than suspected.** It is not "matching is
hard". It is a vise with two jaws, plus a proof that neither jaw can be opened
by better marginal matching. Detail in §4. No candidate sham list is proposed,
and none should be until §6 is answered.

---

## 1. Historical-work dependency register

Classification of every prior result bearing on this estimand. `REUSABLE` means
the implementation pattern and its conclusion transfer. `INAPPLICABLE` means
sound but answering a different question. `SUPERSEDED` means replaced by a later
authority. `DEFECTIVE_INPUT` means computed on scrambled gene coordinates.

| # | Prior work | Class | What transfers, and what must not |
|---|---|---|---|
| H1 | Frozen protocol **v7** (`b2ce4216`) | **AUTHORITY** | Sole execution authority. Sham must be real-gene quadruples from the same nuclei; stopping rule pre-committed; six-gene denominator exclusion frozen. |
| H2 | v6 sham failure: partial corr(amp, log cap \| log D) real **+0.4437**, abundance-matched sham **+0.0031**, reliability-matched **+0.0092** | **REUSABLE** | The measured reason synthesised shams fail: a sham built from the observed denominator `D` has no route to latent capture once `log D` is controlled. Do not re-derive. |
| H3 | Same-mechanism sham diagnostic: real .441 / sham .452, readout .197 / .194 | **REUSABLE, WEAK** | V46 records this as **a single seeded diagnostic**. Two matched numbers at one seed are not exchangeability. Do not cite as if replicated. |
| H4 | R7/R8 named-gene outcomes (150 scored R² over the reserved readouts) | **DEFECTIVE_INPUT** | 361-cell subset = 128 HVS op19 + 233 SEA-AD op25, **zero NPH52**; both those axes scrambled. No biological conclusion may select or reject a program. *Design* lesson survives (§1a). |
| H5 | V44 tiny-teacher tournament | **DEFECTIVE_INPUT** | Same 50k discovery NPZ (SHA-256 prefix `4c50f1de`). Gene-label interpretation needs decoded replay. |
| H6 | Corrected 29-address extraction, 187,909 nuclei / 13 matrices / 92 source-specific donors | **REUSABLE** | The substrate for this report. Availability masks authenticated, 10/10 audit checks pass. **Not** proof the general 41,238-address reader is correct. |
| H7 | Gate v4 synthetic receipt (FP 26/960, power 240/240) | **REUSABLE** | Numerically validated by receipt validator v2; not an independent Monte Carlo rerun. |
| H8 | Gate v1 receipt validator | **SUPERSEDED** | Admitted 16 of 21 corrupted receipts. v2 admits none. v1 preserved as evidence. |
| H9 | Same-cell binomial thinning, p={1,.9,.75,.5,.25}, 201,149 cells | **REUSABLE, REPURPOSED** | Concluded `MEASUREMENT_SHORTCUT_NOT_DEMONSTRATED` for its own question. Its *machinery* is the most promising instrument for latent capture (§6). |
| H10 | Reserved-readout exposure ledger | **AUTHORITY** | All six retained behind the firewall; CSF1R value-exposed; all six stay in the v7 denominator. |
| H11 | Discovery-atlas housekeeping / degree-matched controls | **INAPPLICABLE** | Abundance-matched controls for a different estimand. The v6 failure (H2) already shows abundance matching is insufficient here. |
| H12 | F1 matched-null contracts (Sept 1) | **REUSABLE (pattern only)** | Matched-null *engineering* — row-binding, replay parity, donor separation. Its null preserved query identity, so it is not a model for this null. |
| H13 | NPH52 real-gene pilot, 304 nuclei / 16 donors | **REUSABLE AS FEASIBILITY ONLY** | §2. Explicitly not a test of exchangeability. |
| H14 | Independent sham-overlap stress (ρ → type-I table) | **REUSABLE** | §4.2. |
| H15 | Independent housekeeping counterexample | **REUSABLE, DECISIVE** | §3. |

### 1a. What survives H4's defect and matters

R7's arms were negative **including technical-covariates-only**, at 59–145
training units. That is estimator variance, and it is gene-label independent, so
it survives the scramble. The independent note adds the correct caveat: small
samples, mislabelled response, between-donor shift and low count support are
competing explanations and the cause is **not uniquely identified**. The
corrected cohort has a different donor census, so this does not predict that the
six prospective tests will fail — it is a prospective feasibility warning that
the unit count must be checked before, not after.

---

## 2. NPH52 pilot — reconciled, not treated as confirmation

**Scope accepted as stated:** 304 MG nuclei, operator 39, 16 donors, four
balanced held-out-donor folds, from the SHA-256-authenticated August 24 historical
50k × 41,238 normalized NPZ. Reserved readout values filtered **at the CSR index
stage**, before counts reached analysis arrays — this is the right place to do it.
The 304 nuclei are reused across all four folds and were coverage-selected, so
they are not population-representative.

**Audited, as instructed:**

- **HLA-DPA1 address discrepancy resolved as NOT a defect in the corrected
  extractor.** The historical NPH52 archive has frozen address 23673 structurally
  unmeasured, with a `legacy_exact` same-symbol entry at 40452; the pilot correctly
  refused to substitute. In the corrected FULL104 29-address artifact, address
  **23673 is available on all 187,909 nuclei**, verified directly. Different
  substrate, not a contradiction. No change to the extractor is warranted.
- **RPL13A**: I had noted it as a good marginal match for C1QA (1.13 vs 1.05 mean).
  The pilot and the independent review are right that it is **ineligible** — it is
  one of the eight frozen housekeeping-reference addresses. Marginal similarity is
  not eligibility.
- **ITM2B/BRI2 disqualified** on functional TREM2 interaction (PMC10933458). This
  is the decisive demonstration that numerical screening cannot stand alone.
  **KCNQ5** (neuronal cortical staining, ambient risk) and **NEXMIF** (neurite
  extension) likewise require ambient/cell-type review. A symbol-prefix blacklist
  is demonstrably insufficient.

**Not used to select a method.** The pilot's mean+variance results (APOE 0.053,
P2RY12 0.123 median held-out coherence mismatch) are descriptive over four reused
folds of one coverage-enriched source. The five-observable method looked better on
P2RY12 depth correlation (0.044 vs 0.208) and worse on coherence (0.194). That is
not a consistent ordering and is not treated as one.

---

## 3. The decisive result: observable matching is provably insufficient

The independent counterexample settles the central question, and it settles it
against us. With 120,000 nuclei, two panels matched to within:

| matched observable | absolute difference |
|---|---|
| per-gene raw count | 0.00267 |
| detected fraction | 0.00272 |
| variance / mean | 0.02251 |
| Spearman(normalised expression, observed log depth) | 0.00320 |
| **within-quadruple Spearman** | **0.00048** |

yet, after adjusting for observed log depth:

| | real | sham |
|---|---:|---:|
| correlation with residual hidden capture | **+0.80933** | +0.00217 |
| correlation with Q, whose only common driver is that capture | **+0.55839** | +0.00388 |

**Matching all five observables — including whole-panel covariance — does not
bound the residual capture gap at all.** Any selection procedure whose acceptance
criteria are functions of those five observables is therefore unqualifiable in
principle, not merely underpowered. This retires the entire "match more moments"
family of fixes.

### 3a. Scope of that counterexample, stated precisely

Its `H` is *named* hidden capture but is *implemented* as a generic shared latent
entering expression through a Gaussian copula — not as a capture mechanism acting
on molecule detection. The proof is therefore: **those five observables are
insufficient.** It is *not* a proof that no instrument exists. The distinction
matters, because if `H` is genuinely technical then a measurement that perturbs
capture while holding biology fixed can see it (§6), whereas if `H` is biological
then the real panel predicting Q through it is a true positive, not a false one.
The counterexample collapses those two cases; a qualification design must not.

---

## 4. The vise

### 4.1 Jaw one — strict matching is infeasible

From the pilot's per-fold candidate pools, under mean-within-1.25 plus detection,
Fano, observed-depth and housekeeping-sensor criteria:

| program | slot pools across folds | verdict |
|---|---|---|
| APOE / APOC1 (sparse) | `[0,22,4,142]`, `[0,89,4,199]`, `[52,9,5,57]`, `[0,41,8,367]` | **ZERO_POOL_REFUSAL in 3 of 4 folds** |
| P2RY12 / CX3CR1 (abundant) | 57–60 mean-only, 13–22 all-five | severe |
| P2RY12 / C1QA | 4–10 all-five | severe |

199 non-overlapping quadruples cannot be assembled under strict matching in this
subset. This is a *historical-subset* result and the corrected FULL104 population
may be kinder — that is the open measurement (§7).

### 4.2 Jaw two — dependence, quantified at the measured reuse

The independent stress test gives type-I error as a function of sham–sham
correlation ρ. I combined it with the pilot's **measured** overlap, taking
ρ ≈ mean_shared_genes / 4 (the note's own linear equal-weight rule), and
simulated the frozen rank p-value at B=199, 40,000 batches per cell:

| program | tier | pairs sharing a gene | implied ρ | **P(p ≤ .05)** | max gene reuse |
|---|---|---:|---:|---:|---:|
| APOE | mean 1.25 | 0.6% | 0.0015 | **4.88%** | 4 |
| APOE | mean+detect | 0.7% | 0.0019 | **4.87%** | 4 |
| APOE | all-five strict | 35.5% | 0.0982 | **6.49%** | 55 |
| P2RY12 | mean 1.25 | 2.5% | 0.0063 | **4.88%** | 8 |
| P2RY12 | mean+detect | 2.7% | 0.0069 | **4.89%** | 9 |
| P2RY12 | all-five strict | 24.3% | 0.0646 | **5.91%** | 44 |

Nominal α = 5%.

**This is materially better news than the adversarial fixture suggests.** The
stress test's pathological roster (three of four genes shared in every panel,
ρ = 0.75) gives 26.6% per test and 64% BH-rejection across six. Nothing in the
*measured* pool structure approaches that: the worst observed tier costs about
1.5 percentage points. Dependence is a real effect that must be reported and
calibrated, but at the reuse levels actually seen it is **not** the binding
constraint.

### 4.3 Why it is a vise

The tiers that are feasible and well-calibrated (mean-only, mean+detect: 4.87–4.89%)
are exactly the tiers §3 proves insufficient for latent capture. The tier that
matches more observables collapses to empty pools for sparse partners and, where
non-empty, adds reuse. **Neither jaw is opened by choosing a better matching
band, and §3 shows tightening the band cannot close the real gap anyway.**

---

## 5. The denominator self-inclusion asymmetry — now measured

The independent note identified a structural asymmetry: `D(P,Q)` excludes the true
`P` and `Q` panels, but a *sham* panel's own counts stay inside `D`. It gave an
illustrative figure at a made-up `D = 5,000` of `log(5010/5000) = 0.001998`.

**Measured on the real 187,909 nuclei**, using each third program's four partners
as an abundance-matched stand-in for a sham quadruple:

| directed test | median D | median sham sum | median Δlog offset | p90 | max |
|---|---:|---:|---:|---:|---:|
| APOE → P2RY12 | 5,129 | 4.0 | 0.000623 | 0.002096 | 0.019820 |
| APOE → HLA-DRA | 5,130 | 3.0 | 0.000466 | 0.001627 | 0.021506 |
| P2RY12 → APOE | 5,129 | 4.0 | 0.000623 | 0.002096 | 0.019820 |
| P2RY12 → HLA-DRA | 5,128 | 1.0 | 0.000266 | 0.001040 | 0.015831 |
| HLA-DRA → APOE | 5,130 | 3.0 | 0.000466 | 0.001627 | 0.021506 |
| HLA-DRA → P2RY12 | 5,128 | 1.0 | 0.000266 | 0.001040 | 0.015831 |

Median across the six: **0.000466 log units — a 1.00047× offset inflation**, about
four times smaller than the illustrative figure. The 19 nuisance addresses are not
in the 29-address artifact, so `D` here is slightly larger than the frozen
`D(P,Q)`; these are therefore slight **under**-estimates.

**But it is not a constant.** Spearman(offset inflation, the sham panel's own
summed counts) = **+0.8296**. A constant offset would be absorbed by the
intercept; one that tracks the sham's own expression is a confounded offset.

**Assessment: real, structural, and small.** At ~0.05% of the denominator it is
very unlikely to drive a verdict, but it is in a fixed direction and must be
carried into the full-pipeline null simulation rather than dismissed here.
Redefining `D` per sham is **not** an acceptable repair: it would change the
estimand and requires a prospectively dated amendment (v7 governance, and the
ledger rule that a governance fix must never move the estimand).

---

## 6. One diagnostic worth developing — a robustness check, NOT an identification strategy

> **Terminology correction, 2026-09-28 (owner).** An earlier version of this
> section called thinning an "instrument" for latent capture and said qualifying
> it would make the exchangeability question answerable. That overstates it.
> Same-nucleus thinning tests **post-capture measurement robustness** and can
> expose differential sensitivity to *additional* sampling loss. **It cannot
> establish exchangeability with respect to the original hidden biochemical
> capture process** — that process ran before the counts existed, and nothing
> done to the counts afterwards reaches back to it. The section is kept, with
> its claim reduced to what the operation can actually support.

Every observable in §3 is a *static* property. The quantity that matters is a
*causal* one: how does this gene's measured value respond when the measurement
is degraded further and biology does not change? Static observables cannot
answer that; a perturbation can — but only about the sampling stage it actually
perturbs.

**Same-nucleus binomial thinning** is that perturbation, and this project already
has it qualified as machinery (H9: p={1,.9,.75,.5,.25}, 201,149 cells). Thin a
nucleus's counts, recompute normalised expression against the thinned denominator,
and measure the drift. Biology is held **exactly** fixed — it is the same nucleus —
so any drift is measurement. A gene whose capture sensitivity differs from the
library's average will drift; one that the denominator absorbs will not.

**Status of my own test of this idea: INCONCLUSIVE, and I am not claiming it
works.** I built a fixture where capture acts as a genuine mechanism (per-nucleus
efficiency `c`, gene-specific exponent, binomial detection) rather than as a
copula latent:

- residual capture coupling, real **+0.0603** vs sham **+0.0004** — the gap exists
- thinning-drift correlation with latent capture: real **−0.0678** vs sham **+0.0040**,
  discrimination **0.0718** — the instrument responds

**However my fixture is not adequately matched** on two of the five observables
(depth-rho +0.171 vs +0.059; within-panel +0.083 vs +0.183), so part of the
thinning gap may come from those mismatches rather than from capture sensitivity.
**This does not yet demonstrate anything** and must be redone against a properly
matched fixture before the idea is used. A first attempt of mine was worse still —
means 3.3 vs 6.6 — and was discarded.

Known limits even if it does qualify: thinning emulates multinomial **sampling**
loss, not biochemical capture heterogeneity (nuclear retention, RT efficiency,
intron content). Those act at the bench, before any count exists. So a clean
thinning result would say a panel is robust to further sampling loss; it would
say nothing about whether two panels experienced the same original capture. The
quantity v7 named — partial correlation with latent capture given `log D` — is
not recovered by this and remains unobserved.

---

## 7. The three families — current verdicts

| family | role | verdict |
|---|---|---|
| **A. Housekeeping-like stable genes** | technical **sensor**, never a sham | **CONDITIONALLY SUPPORTABLE, unproven.** The eight frozen reference genes are forbidden as shams and already excluded from `D`. As sensors their weakness is measured: median 0.37 counts/nucleus, 27.1% detection, so an 8-gene sensor sums to ≈5 counts — a very noisy per-nucleus capture estimate whose reliability must be established by split-half before use. RUV's own assumption — that control genes do not respond to the biological contrast — is **unverified here**. |
| **B. Mean+variance matched quadruples** | transparent baseline | **FEASIBLE AND WELL-CALIBRATED ON THE RANK STATISTIC (4.87–4.89%), BUT INSUFFICIENT** by §3. Usable as a reported baseline; not defensible as the primary null on its own. |
| **C. Co-regulated generic modules** (proteasome, spliceosome, basal transcription) | challenging biological comparator | **NOT A NULL.** Their coherence is the point of the comparison and disqualifies an automatic no-biology assumption. Keep in a separate reported family. For HLA-DRA specifically, the MHC class II locus is co-regulated by CIITA and physically linked, so a random-gene null lacks structure the real panel has; module comparators are the fair contrast there, and that asymmetry must be stated wherever the HLA result is reported. |

---

## 8. Corrections to claims I made earlier in this session

The independent housekeeping review is right on all three, and I withdraw them:

1. **"The dominant competitor is Poisson sampling noise."** Not measured. My OLS
   left 95.5% (program) and 98.9% (housekeeping) of variance *unexplained by the
   included predictors*. That residual contains genuine within-stratum biology,
   latent capture, ambient RNA, zero inflation and unmodelled donor-by-region
   structure as well as sampling noise. I inferred a decomposition I did not
   perform.
2. **"The noise floor is set by mean and detection and nothing else."**
   Overstated. Overdispersion, gene-specific capture, within-quadruple dependence
   and sham overlap all matter — §3 proves the point directly.
3. **The +0.154 vs +0.131 depth correlation** was reported without noting that
   correlating `log1p(count·10⁴/D)` against `log D` is mathematically coupled
   through `D` itself. It is a measured association, not an estimate of latent
   capture sensitivity.

Also: `operator_index` in SEA-AD is a brain-region matrix; I described removing it
as removing a technical term. It absorbs real regional biology too.

---

## 9. Decision

**Supportable now:** the corrected 187,909-nucleus substrate; family B as a
reported baseline with its exact reuse and overlap matrix; family C as a separate
challenger; the measured denominator asymmetry as a small, carried, non-blocking
bias.

**Not supportable now:** any claim of nuisance exchangeability for any candidate
sham family, by any combination of the five observables. No candidate gene list is
proposed, and the pilot's shortlists must not be promoted to one.

**Not yet answered, and blocking:**

1. Per-slot candidate pool sizes on the **corrected FULL104 fitting donors**,
   source-decoded and availability-masked, stratified by source and region. The
   pilot's zero pools are from 304 coverage-enriched nuclei of one source and may
   not transport. This is the single highest-value next measurement and it is
   outcome-blind. It needs per-gene marginals over the 41,238 addresses on myeloid
   nuclei — obtainable from a bounded pass, not a full substrate regeneration.
2. Whether same-nucleus thinning qualifies as a latent-capture instrument (§6),
   tested on a properly matched fixture.
3. Split-half reliability of any proposed technical sensor.

**If 1–3 do not produce a defensible design, the recorded outcome is
`COUNT_READOUT_INSUFFICIENTLY_IDENTIFIABLE_UNDER_TESTED_NUISANCE`** per the v7
stopping rule — a statement about the validation strategy, not about whether the
per-nucleus biological state exists. Matching bands, thresholds and candidate
pools are not to be retuned to induce a pass. The preregistered
conditional-composition alternative would then need its own reliability and
leakage audit; at one to four molecules a centred log-ratio with a pseudocount is
not automatically nuisance-free.

**Stopped at the biological decision boundary.** No reserved readout opened, no
directed outcome run, no training.
