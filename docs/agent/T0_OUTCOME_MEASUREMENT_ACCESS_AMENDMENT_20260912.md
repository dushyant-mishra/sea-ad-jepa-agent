# T0 PROSPECTIVE OUTCOME-MEASUREMENT ACCESS AMENDMENT

Date: 2026-09-12
Revision: **R3** (narrow repair after review of R2 at `29d15919`)
Status: `PROSPECTIVE_ACCESS_CONTRACT__DESIGN_APPROVED__NUMERIC_ACCESS_PENDING`
Requested authority: read numeric values of six additional pathology columns,
**28 DISCOVERY donors only**
Terminal if approved: `PASS_T0_OUTCOME_MEASUREMENT_MODEL_ACCESS_GRANTED`
Terminal if refused: `STOP_T0_OUTCOME_MEASUREMENT_ACCESS_NOT_AUTHORIZED`

---

## 0. Why this document exists before any analysis

The current T0 numeric-access authority permits exactly one outcome variable.
`scripts/v4/t0_stage2b_discovery_at8_v1.load_role_numeric_at8` parses donor ID
and the frozen AT8 endpoint and refuses any other endpoint identity; every other
pathology column is left unparsed by construction. Reading Braak, pTau or any
other tau measure is therefore a **new outcome-access action**, even on the 28
donors whose AT8 is already open and even though the file is already
authenticated. Access authority on this project is scoped to the
(donor set × variable) pair, not to the donor set alone.

**What has been read:** the file's byte digest, its header line, its column count
and its row count. Column *names*, not values. No numeric pathology outside the
existing AT8 authorization has been parsed by any process in this lane, at R1,
R2 or R3.

### R3 repairs (narrow; no new candidates, no new thresholds)

| # | R2 defect | R3 repair | § |
| --- | --- | --- | --- |
| 1 | `df = p(p+1)/2 − (2p+1)` counts **one** residual covariance; M2a declares **three** | df computed from the exact surviving model graph; `p ≥ 5 ⇒ df ≥ 4` shortcut deleted | §7.3, §9.3, §11 |
| 2 | rank-based fit produces latent-scale reliability; §13 attenuation is Pearson-scale | successor endpoint and all downstream work declared **on the latent-Gaussian scale**; this study supplies **no** `R_y` to §13 | §5, §6, §13 |
| 3 | mixed Spearman + polyserial matrix repaired by Higham projection could manufacture structure | single coherent latent-Gaussian estimator; non-PD is **fail-closed on an inferential criterion**, not a distance cutoff | §5 |
| 4 | M1a required an informative ω, but equal weighting does not identify ω | measurement model and scoring rule separated; M1a's reliability is identified **by MM-C, stated explicitly**, and M1a is admissible only if MM-C is | §7.4, §11 |
| 5 | MC formula described as controlling endpoint precision | restated accurately as controlling **tail-probability** relative MC error; deterministic two-seed endpoint-stability replay added | §10 |
| 6 | §15 read "(this document, approved)" while access is unauthorized | corrected to design-approved / numeric-access-pending | §15 |

Sections §1–§4 and §13–§15 are otherwise unchanged and were approved as written.

### R3 self-audit — four defects I found in my own R3 draft before committing

Caught by auditing R3 against itself rather than shipping it for review:

| # | defect in my R3 draft | correction | § |
| --- | --- | --- | --- |
| 7 | `ρ = 2·sin(π·ρ_S/6)` and polyserial called "exact" with the Gaussian-copula assumption left implicit | assumption named and carried into every statement the study makes | §5.1 |
| 8 | BCa proposed for the minimum-eigenvalue interval — a **non-smooth** functional whose jackknife acceleration is unreliable | that interval alone uses the percentile bootstrap, `α*` fixed at 0.025 | §5.2 |
| 9 | M3a allowed to become a selection candidate when MM-C is inadmissible — contradicting Braak's declared validity-only role, and letting the coarsest indicator **rescue** a failed model | M3a is validity-only and never selected; MM-C inadmissible ⇒ `COMMON_FACTOR_NOT_ESTABLISHED`; candidate set is always `{M1a, M2a}` | §7.4, §11 |
| 10 | the two-seed rule was circular — declared `UNRESOLVED` *and* said to increase `B` | ordered: recompute `B`, re-run both seeds, `UNRESOLVED` only if they still disagree | §10 |

Defect 9 was the substantive one: it would have admitted exactly the kind of
result-driven rescue this contract exists to prevent.

---

## 1. Provenance and column identity binding  *(unchanged, approved)*

Source: `data/processed/metadata/sea_ad_mtg_donor_pathology_targets.csv`

| property | value |
| --- | --- |
| file SHA-256 (raw bytes) | `ebbe9bc0c623c663331425794bd8fb1b4c4f3657455cf55d806cc383ea6d8e3a` |
| header line SHA-256 | `88114843211d095dbf3ccbc91cc1add4172ca15f7fe6ced07f9ea679ae785385` |
| columns | 27 |
| data rows | 84 |

The file digest reproduces V20's frozen `expected_source_sha256` exactly. The 84
rows exceed the 46-donor T0 cohort; the loader filters by the frozen donor set
and must continue to.

Declared columns, bound by index **and** by digest of the column name, so a
reordered or renamed file cannot silently satisfy this contract:

| idx | SHA-256(name)[:16] | column |
| --- | --- | --- |
| 0 | `b57785e06342c767` | `Donor ID` |
| 5 | `3cdb1a3d64c2b379` | `Braak` |
| 12 | `95870f7dd3210198` | `percent AT8 positive area_Grey matter` |
| 13 | `af74c64ecc9be627` | `number of AT8 positive cells per area_Grey matter` |
| 21 | `cc296b538889eec5` | `guhcl pTau_Grey matter` |
| 22 | `0716f02ae61547dd` | `guhcl tTau_Grey matter` |
| 25 | `065f0168c900a054` | `ripa pTau_Grey matter` |
| 26 | `ea91a5c6edb80445` | `ripa tTau_Grey matter` |

Index 12 is already authorized. The **six new columns** requested are 5, 13, 21,
22, 25, 26. Any column not in this table remains unparsed — in particular the
amyloid (6E10, abeta40/42), glial (GFAP, Iba1), neuronal (NeuN),
`APOE Genotype`, `Cognitive Status`, `Thal`, `CERAD score`,
`Overall AD neuropathological Change` and `Severely Affected Donor` columns.

---

## 2. Scientific rationale, indicator by indicator  *(unchanged, approved)*

**idx 12 — `percent AT8 positive area_Grey matter`** (incumbent endpoint).
AT8 is a monoclonal antibody against phospho-tau at pSer202/pThr205; percent
positive area is the areal fraction of immunoreactive signal in grey matter.
Image morphometry. The frozen V20 endpoint and the incumbent any successor must
beat.

**idx 13 — `number of AT8 positive cells per area_Grey matter`**.
Same antibody, same imaging pipeline, different summary statistic: object count
rather than area fraction, sensitive to the *number* of affected cells where idx
12 is sensitive to *total burden including neuropil threads*. **Shares both
reagent and method with idx 12**, so the two cannot be treated as independent
evidence about the construct — see §7.

**idx 21 — `guhcl pTau_Grey matter`**.
Guanidine-HCl extraction; guanidine solubilizes aggregated protein, so this
indexes the **insoluble / fibrillar** phospho-tau pool. Independent reagent,
method and tissue aliquot from the morphometry.

**idx 25 — `ripa pTau_Grey matter`**.
RIPA-buffer extraction, indexing the comparatively **soluble** phospho-tau pool —
a different biochemical compartment from idx 21, not a replicate of it.

**idx 22, 26 — `guhcl tTau`, `ripa tTau`**.
Total tau in the matching compartments. See §6 for the estimand split: under the
burden estimand these are **indicators in their own right**, not denominators.

**idx 5 — `Braak`**.
Ordinal neurofibrillary staging, 0–VI, defined by the **anatomical distribution**
of neurofibrillary pathology across regions. A different construct emphasis from
every other indicator — topographic spread, not local density in the sampled
middle temporal gyrus — and coarse and ceiling-prone in an aged cohort.
Requested as an **ordinal/topographic validity indicator, never as a continuous
replicate of MTG quantitative burden**.

---

## 3. Allowed population  *(unchanged, approved)*

Numeric values may be read for the **28 DISCOVERY donors only**, identified by
the frozen donor-set digest
`4395fec74bcf7abf192d731db3c827fa25cfde1b5297db4203b041984a780d33`.

Forbidden absolutely, for every column in this amendment:

- the 12 fresh `reader_validation` donors — sealed;
- the 10 `reader_oracle` donors — sealed;
- the 18 spent historical-validation donors — **not authorized here**. They may
  not be used to select the endpoint form, the indicator set, the
  transformations, or the factor structure. "Already spent for AT8" is not
  "available for this purpose"; extending them needs a separate explicit
  authority change, after which they may be proposed for predeclared
  sensitivity/reproduction once the measurement model is frozen.

The reader must enforce this the way the AT8 loader does — refusing any donor
outside the included set *before* values are touched, and requiring the loaded
set to reproduce the frozen digest — not by filtering after loading.

---

## 4. Missingness  *(unchanged)*

- The missingness pattern per indicator and per donor is reported **first**, as a
  standalone artifact, before any model is fitted.
- No imputation in the primary model. Donors with partial indicator sets
  contribute under full-information estimation given the declared model; mean
  substitution, regression imputation, and listwise deletion as a default are
  prohibited.
- **Sparse-indicator rule.** Every primary result is computed **with and without
  each indicator whose observed count falls below 21 of 28**, and if the
  endpoint-selection terminal differs between those fits, the terminal is
  `UNRESOLVED`. The count 21 is a **prespecified operational convention**
  (`CONVENTION`, not a biological or statistical truth) chosen only to bound how
  many refits are performed; the decision rests on whether the conclusion moves.
- Which indicators survive changes both `m` and `r` in §7.3, so df is recomputed
  for every refit rather than assumed.

---

## 5. Measurement scale and the association matrix  *(repairs 2, 3)*

### 5.1 One coherent estimator

R2 combined Spearman for continuous pairs with polyserial for the ordinal pair
and then repaired the result. Those are estimates of *different* parameters, so
the combination was not coherent. R3 estimates a single parameter throughout: the
**latent-Gaussian (nonparanormal) correlation**.

- continuous–continuous: `ρ = 2·sin(π·ρ_S/6)`, which inverts the Gaussian
  identity `ρ_S = (6/π)·arcsin(ρ/2)`;
- continuous–ordinal (Braak): polyserial, which estimates that same
  latent-Gaussian parameter;
- there are no ordinal–ordinal pairs (Braak is the only ordinal indicator).

Every entry is therefore an estimate of one common latent-Gaussian correlation.

**The assumption this rests on, named rather than implied.** Both transforms are
exact only under a **Gaussian copula**: each continuous indicator is assumed to be
some unknown strictly monotone transform of a latent Gaussian variate, and Braak
a thresholded one. This buys the monotone-transform invariance that removes the
R2 constant problem, and it is an assumption, not a free lunch. It is recorded as
a named assumption in `COMMON_FACTOR_SUPPORT` and carried into every statement
the study makes. No threshold or test is attached to it here; it is declared so
that a later reviewer can see exactly what the primary specification assumes.
This retains R2's motivation — invariance to any monotone transform of the
continuous indicators, so no epsilon, no offset and no sample-size-dependent
constant enters the primary specification — while making the matrix internally
coherent.

**Sensitivity only:** Pearson correlations on declared monotone transforms,
`asin(sqrt(x/100))` for idx 12 (finite at 0 and 100, so no boundary correction
and no constant) and `log(x + c)` for count-rate and concentration indicators,
with `c` the assay's smallest reportable nonzero increment recovered from SEA-AD
protocol documentation **before** access. If `c` cannot be recovered from
documentation, that sensitivity is not run and this is reported. `c` is **never**
chosen by inspecting observed minima.

### 5.2 Non-positive-definiteness is fail-closed, on an inferential criterion

Pairwise estimation can yield a non-PD matrix at n = 28. A nearest-PD projection
can manufacture a joint structure that no pairwise estimate supported, so it may
not silently become measurement authority, and the decision may not rest on a
distance cutoff chosen after seeing the matrix.

**Rule, frozen now.** Bootstrap the **minimum eigenvalue** of the unprojected
pairwise matrix under §10's donor-level resampling. The minimum eigenvalue is a
non-smooth functional of the matrix, so its BCa acceleration — a jackknife
quantity — is unreliable for it; this interval alone uses the **percentile**
bootstrap, whose tail level is fixed at `α* = 0.025` and therefore needs only
`B ≥ 3,900` by §10. Then:

- if the bootstrap **upper** confidence bound on the minimum eigenvalue is
  **below zero**, the non-PD-ness is not attributable to estimation noise, the
  indicators do not jointly support a coherent association structure, and the
  terminal is `ASSOCIATION_STRUCTURE_UNRESOLVED`. No projection is performed and
  no model is fitted.
- otherwise the matrix is projected to the nearest PD matrix in the Frobenius
  norm by Higham's alternating-projections algorithm, declared here, and the
  projection distance is reported as evidence in `COMMON_FACTOR_SUPPORT`.

This asks whether the matrix is *significantly* indefinite rather than how far
the repair moved it. No other smoothing is admissible.

### 5.3 What scale the results live on

This study is conducted **entirely on the latent-Gaussian scale**. Loadings,
residual covariances, ω and factor-score determinacy all describe that scale, and
none of them is a statement about raw AT8 percent-area magnitude. Consequences
are frozen in §6 and §13.

---

## 6. Estimands  *(repair 2 extends R2's split)*

**Estimand A — `COMMON_DONOR_TAU_BURDEN__LATENT_GAUSSIAN_SCALE`.** How much
pathological tau the donor carries, as a latent-Gaussian construct. Absolute pTau
legitimately reflects burden, and total tau is itself part of the burden signal,
so `guhcl tTau` and `ripa tTau` enter as **indicators in their own right**, not
denominators. Indicator set: idx 12, 13, 21, 22, 25, 26 continuous, plus Braak as
ordinal in MM-CB. **Eligible for selection.**

**Estimand B — `DONOR_TAU_PHOSPHORYLATION_FRACTION`.** How much of the donor's
tau is phosphorylated, from within-compartment `log(pTau) − log(tTau)`. A
different construct — phosphorylation state rather than load. **Computed and
reported as measurement evidence, ineligible for selection under this
amendment.** If B proves better-measured, that is a finding to report and a new
amendment to request, never an automatic substitution. This is the mechanism that
stops a ratio silently replacing the absolute signal.

`tTau`'s interpretation is frozen per estimand now — **indicator** under A,
**normalizer** under B — and may not be re-roled after seeing results.

**Scale is part of the estimand.** A qualifying successor is a latent-scale
construct. No mapping back to raw AT8 magnitude is claimed, and V20's endpoint on
its own scale is untouched and unreinterpreted.

---

## 7. Measurement models, scoring rules, and identifiability

### 7.1 The two-indicator method factor is underidentified — proof  *(unchanged)*

R1 proposed a latent AT8-method factor loading on idx 12 and idx 13 only,
orthogonal to the common factor. With `Var(F) = Var(M) = 1`, `Cov(F, M) = 0`:

```
x₁ = λ₁F + γ₁M + e₁        x₂ = λ₂F + γ₂M + e₂
```

`λ₁, λ₂` are identified from the covariances of `x₁, x₂` with the other (≥ 2)
indicators, which involve no `γ`. That leaves three moments carrying information
about the method parameters:

```
Var(x₁)     = λ₁² + γ₁² + ψ₁
Var(x₂)     = λ₂² + γ₂² + ψ₂
Cov(x₁, x₂) = λ₁λ₂ + γ₁γ₂
```

Three equations in four unknowns `(γ₁, γ₂, ψ₁, ψ₂)`. **Underidentified by one**,
rescuable only by `γ₁ = γ₂`, untestable with two indicators.

### 7.2 The correlated residual is just-identified and equivalent  *(unchanged)*

```
Var(x₁)     = λ₁² + ψ₁
Var(x₂)     = λ₂² + ψ₂
Cov(x₁, x₂) = λ₁λ₂ + θ₁₂
```

Three equations, three unknowns. **Just identified.** Under the constraint that
rescues the method factor, `θ₁₂ = γ₁γ₂` — the specifications are observationally
equivalent, so the method factor buys no information and costs one parameter of
identification. **Frozen decision: no latent method factor is fitted.** The AT8
method dependence is a prespecified correlated residual.

### 7.3 Structural degrees of freedom — corrected  *(repair 1)*

**R2's `df = p(p+1)/2 − (2p+1)` is wrong and is withdrawn.** It counted a single
residual covariance while the model declares **three** residual-covariance edges:

```
E = { (idx12, idx13) AT8 method,  (idx21, idx22) guHCl,  (idx25, idx26) RIPA }
```

df is computed from the **exact surviving model graph**, never from `p`. On the
correlation scale, for a one-factor model over `m` surviving indicators with
factor variance fixed at 1:

```
observed statistics = m(m−1)/2          (off-diagonals; diagonals are 1 by construction)
free parameters     = m loadings + r residual covariances
                       (residual variances are determined as 1 − λ²)

df = m(m−1)/2 − (m + r) = m(m−3)/2 − r
```

where **`r` = the number of edges in `E` with *both* endpoints surviving**. The
covariance-scale count agrees: `m(m+1)/2 − (2m + r) = m(m−3)/2 − r`. Ordinal
thresholds for Braak are estimated from the univariate margin and do not enter
the correlation-structure df; they must, separately, be estimable (§9.4).

Realizable configurations, computed rather than assumed:

| surviving continuous `p` | `r` | MM-C: `m`, df | MM-CB: `m`, df |
| --- | --- | --- | --- |
| 6 | 3 | 6, **6** | 7, **11** |
| 5 | 2 | 5, **3** | 6, **7** |
| 4 | 2 (one whole pair dropped) | 4, **0** | 5, **3** |
| 4 | 1 | 4, **1** | 5, **4** |
| 3 | 1 | 3, **−1** | 4, **1** |
| 3 | 0 | 3, **0** | 4, **2** |

Two things follow, and both invalidate R2's shortcut. At `p = 6, r = 3` the df is
**6, not 8**. And `p ≥ 5` does **not** imply `df ≥ 4`: `p = 5` gives df 3, `p = 4`
can give df 0, and `p = 3` with a surviving edge is **underidentified at df = −1**.

**Requirement, replacing R2's `df ≥ 4`:** the fitted measurement model must be
**over-identified, `df ≥ 1`**, computed from the surviving graph. This is an
identification fact — df = 0 fits any matrix perfectly and therefore tests
nothing, df < 0 is not estimable — and introduces no chosen number. The computed
df is reported in `COMMON_FACTOR_SUPPORT`, and a low df is reported as a weak
test rather than converted into a cutoff.

### 7.4 Measurement models and scoring rules, separated  *(repair 4)*

R2 required every candidate to have an informative reliability interval while
listing M1a as an equal-weight composite. **Equal weighting does not identify ω.**
A composite is a *scoring rule*; reliability is a property of a *measurement
model*. R3 separates them and states the dependency openly.

**Measurement models** — these are what identify reliability:

- **MM-C** — one-factor congeneric over the surviving continuous indicators, on
  the §5 latent-Gaussian matrix, with the residual-covariance edges of `E` whose
  endpoints survive.
- **MM-CB** — MM-C plus Braak as an ordinal indicator via polyserial loading,
  thresholds from the univariate margin.

**Scoring rules** — these produce the donor endpoint value:

- **SR-0** — idx 12 alone. No measurement model.
- **SR-1** — equal weights over standardized surviving continuous indicators.
- **SR-2** — model-implied **Bartlett** factor-score weights.

**Candidates** are (measurement model, scoring rule) pairs:

| candidate | measurement model | scoring rule | reliability identified by |
| --- | --- | --- | --- |
| M0a (incumbent) | none | SR-0 | **unidentified** — a single indicator |
| M1a | MM-C | SR-1 | **MM-C**, explicitly |
| M2a | MM-C | SR-2 | MM-C |
| M3a | MM-CB | SR-2 | MM-CB — **validity-only, never selected** |

For a composite with weight vector `w` under a congeneric model with loadings `Λ`
and residual covariance `Θ` (including the declared off-diagonals), factor
variance 1:

```
ω_w = (w′Λ)² / [ (w′Λ)² + w′Θw ]
```

with `w` equal for SR-1; factor-score determinacy is additionally reported for
SR-2.

**The dependency, stated rather than borrowed.** M1a's reliability is computed
under MM-C — the same measurement model M2a uses. Therefore **M1a is admissible
only if MM-C is admissible**, and M1a is not an independent simpler competitor at
the measurement-model level. What distinguishes M1a from M2a is only the scoring
rule: equal weights are not estimated from data, so M1a's scoring map has fewer
data-estimated components (standardization alone, fold-internal per §8). That is
the sense in which it is simpler, and §11 step 3 uses exactly that sense.

**M3a is validity-only and is never selected.** R3's first draft let M3a become a
selection candidate if MM-C were inadmissible. That contradicted §2 — Braak is
declared a validity indicator, not a construct driver — and worse, it created a
path in which the coarsest, most ceiling-prone indicator *rescues* a
continuous-only model that had failed on its own. If MM-C is inadmissible, the
terminal is `COMMON_FACTOR_NOT_ESTABLISHED`; MM-CB cannot substitute for it.

MM-CB is fitted and reported purely as corroboration: a Braak loading whose
interval excludes zero is evidence that the common factor indexes tau burden
rather than an imaging-assay artifact. That evidence goes in
`COMMON_FACTOR_SUPPORT` and touches no selection step. The selection candidate
set is therefore always `{M1a, M2a}`.

No model outside this family may be fitted in the primary analysis.

---

## 8. Leakage prohibition on target construction  *(unchanged)*

**R1 said M1 had "no data-derived target map and no leakage pathway." That is
retracted and was wrong.** Equal weights remove *learned weights*; they do not
remove the estimated means and standard deviations that standardization requires.

The rule, applying to every data-derived component — standardizations, the §5.1
rank-to-latent transforms, loadings, factor-score coefficients, polyserial
thresholds, PD projections:

- either the measurement map is **externally fixed**, from an authority
  independent of these 28 donors, and carried in unchanged;
- or **every data-derived component is estimated inside the training fold** and
  the held-out donor is scored with the training-only map, unchanged.

There is no third option, and "equal weights" is not one.

Only after the measurement-model form and the selection rule are frozen may a
final model be refit on the lawful discovery population to define the eventual
frozen successor target.

---

## 9. Refusal criteria — identification facts first, conventions labelled

**Identification and estimability criteria (not conventions):**

1. **Convergence.** Failure to converge on the full discovery fit, or failure in
   more than 5% of bootstrap resamples, gives `COMMON_FACTOR_NOT_ESTABLISHED`.
2. **Indicator support.** An indicator whose standardized loading has a bootstrap
   interval **including zero** is not an indicator of the construct; it is
   removed, the model refitted — with `m` and `r` and therefore df recomputed —
   and both versions reported.
3. **Testability.** The measurement model must be **over-identified, computed
   `df ≥ 1`** from the exact surviving graph (§7.3). Not `p ≥ 5`; not `df ≥ 4`.
4. **Ordinal estimability.** Braak enters MM-CB only if every ordinal threshold
   is estimable — no empty or singleton extreme category.
5. **Association structure.** `ASSOCIATION_STRUCTURE_UNRESOLVED` per §5.2 if the
   bootstrap upper bound on the minimum eigenvalue is below zero.
6. **Method dependence.** Reported as fitted `θ₁₂` with its bootstrap interval
   and the share of idx12/idx13 association it accounts for. No threshold; if the
   interval excludes zero, method dependence is *established* and routes §11
   step 3 rather than triggering a refusal.

**Prespecified conventions (labelled `CONVENTION`, not biological truth):**

- the 21-of-28 sparse-indicator refit trigger (§4);
- the 5% bootstrap non-convergence allowance in criterion 1;
- the reliability-interval informativeness width in §11 step 2.

**Uncertainty gate, overriding all of the above.** Any reliability-like quantity
is reported as a bootstrap interval, never a point. If that interval spans values
that would change the feasibility verdict, the verdict is `UNRESOLVED`. A
`COMMON_FACTOR_NOT_ESTABLISHED` finding must arise because the model is
unsupported, unstable or unidentified — never because a sample correlation landed
at 0.29 rather than 0.30.

---

## 10. Monte Carlo precision budget  *(repair 5)*

`B = 10,000` is a convention, and this project has already told V5 not to inherit
conventional Monte Carlo counts without a precision budget.

**What the budget controls, stated accurately.** For a BCa interval endpoint at
bias- and acceleration-adjusted tail level `α*`, the realized tail count is
binomial, so requiring the relative Monte Carlo standard error of the **tail
probability** to satisfy `sqrt(α*(1−α*)/B) ≤ r·α*` gives

```
B ≥ (1 − α*) / (α* · r²)
```

| adjusted tail `α*` | required `B` at `r = 0.10` |
| --- | --- |
| 0.025 | 3,900 |
| 0.010 | 9,900 |
| 0.005 | 19,900 |

**This controls Monte Carlo error in the tail probability. It does not by itself
guarantee a given numerical precision for the quantile endpoint**, which also
depends on the bootstrap density at that quantile and degrades where the density
is low. R2's language overstated this and is corrected.

**Endpoint-stability replay (added).** Every bootstrap is run at **two disjoint
frozen seeds**. Both replicates' endpoints are reported with their discrepancy.
If the two replicates yield **different §11 terminals**, the response is ordered
and deterministic — R3's first draft stated it circularly and is corrected here:

```
1. recompute B from the formula at the more extreme realized alpha*, and re-run
   both seeds at that larger B;
2. if the two terminals now agree, that terminal stands;
3. if they still disagree, the terminal is UNRESOLVED and no conclusion is drawn.
```

The check is therefore conclusion-based rather than a tolerance on a number, and
it terminates.

**Procedure.** Run `B₀ = 4,000`; read the realized BCa-adjusted tails; if any is
more extreme than 0.025, re-run at the `B` its level requires. Record realized
`B`, realized `α*_lo`/`α*_hi`, attained relative MC SE, both seeds, and the
two-replicate discrepancy in the receipt.

**Determinism.** `numpy.random.Generator(PCG64)`, seeds frozen in the receipt,
resampling **at the donor level** (28 donors, the experimental unit — never
cells, never indicator values within donor), no stratification, resample-index
arrays digested so the run replays exactly.

If a project-wide Monte Carlo precision authority is later established, this
budget defers to it, and the receipt records which authority governed.

---

## 11. Deterministic endpoint-selection rule

Estimand-B models are excluded at every step. All steps run **before any
expression association is computed**.

```
STEP 0 — ASSOCIATION STRUCTURE
  If §5.2 returns ASSOCIATION_STRUCTURE_UNRESOLVED, stop there.
  No model is fitted and M0a stands.

STEP 1 — MEASUREMENT-MODEL ADMISSIBILITY
  Selection uses MM-C only. MM-CB is fitted for validity and can never be
  selected (§7.4), so it cannot rescue an inadmissible MM-C.
  MM-C is admissible only if all hold:
    (a) converges on the full discovery fit;
    (b) converges in >= 95% of bootstrap resamples;
    (c) every retained indicator's loading interval excludes 0      (§9.2);
    (d) computed structural df >= 1 from the exact surviving graph   (§7.3);
  (MM-CB additionally needs estimable Braak thresholds (§9.4), but only to
   be reported as validity evidence.)
  Both M1a and M2a depend on MM-C (§7.4); neither is admissible without it.
  If MM-C is inadmissible:
      -> COMMON_FACTOR_NOT_ESTABLISHED
      -> NO_SUCCESSOR_ENDPOINT_QUALIFIED, M0a stands.

STEP 2 — THE SUCCESSOR MUST DELIVER WHAT M0a CANNOT
  M0a is a single indicator, so its reliability is UNIDENTIFIED. A successor
  earns its place by identifying reliability at all, informatively:
    the bootstrap interval for omega_w (§7.4), and for factor-score
    determinacy where SR-2 is used, must have width <= 0.25 on the [0,1]
    scale.
    [width 0.25 is labelled CONVENTION: an informativeness requirement,
     not a claim about biology]
  All such quantities are on the LATENT-GAUSSIAN SCALE (§5.3).
  If no admissible candidate meets this:
      -> MEASUREMENT_RELIABILITY_UNRESOLVED
      -> NO_SUCCESSOR_ENDPOINT_QUALIFIED, M0a stands.

STEP 3 — PARSIMONY OF THE SCORING MAP, WITH ONE DECLARED EXCEPTION
  Among candidates passing 1 and 2, prefer the scoring rule with FEWER
  data-estimated components:
      SR-1 (standardization only)  <  SR-2 (standardization + estimated weights)
  SR-2 is preferred over SR-1 only if the prespecified measurement defect is
  established:
      theta_12 (AT8 method residual covariance) has an interval excluding 0,
      so equal weighting double-counts shared method variance while
      model-implied weights do not.
  No other defect may be invoked.

STEP 4 — TIES
  The candidate set is always {M1a, M2a} (§7.4). Equal on step 3 resolves in
  the frozen order  M1a < M2a, earliest wins. Declared now. No tolerance, no
  post-hoc tie-break.

STEP 5 — TERMINALS
  PASS_T0_SUCCESSOR_ENDPOINT_QUALIFIED__<candidate>__COMMON_DONOR_TAU_BURDEN__LATENT_GAUSSIAN_SCALE
  NO_SUCCESSOR_ENDPOINT_QUALIFIED            (M0a stands; a real result)
  MEASUREMENT_RELIABILITY_UNRESOLVED
  COMMON_FACTOR_NOT_ESTABLISHED
  ASSOCIATION_STRUCTURE_UNRESOLVED
  UNRESOLVED    (sparse-indicator refits, or the two MC seeds, disagree)
```

`NO_SUCCESSOR_ENDPOINT_QUALIFIED` is a lawful and publishable outcome: it would
say these assays do not identify a better-measured tau-burden construct at this
cohort size. It is not a failure of the study.

A qualifying successor still requires its own freeze, its own receipt and its own
confirmation contract before it carries any authority. V20 and V21 keep their
existing meaning; nothing here reinterprets them.

---

## 12. Output schema — six separate evidence classes

Six artifacts, each independently digested. **No single association matrix or
coefficient may populate more than one field**, and each field names the
computation that produced it.

| field | what it is | what it is NOT |
| --- | --- | --- |
| `CONVERGENT_VALIDITY` | the §5.1 latent-Gaussian association matrix with bootstrap intervals, plus the minimum-eigenvalue bootstrap of §5.2 | not reliability, not factor support |
| `METHOD_VARIANCE` | fitted `θ₁₂` with interval; share of idx12/idx13 association explained | not a construct claim |
| `COMMON_FACTOR_SUPPORT` | convergence rates, loadings with intervals, `m`, `r`, **computed df**, PD-projection distance | not reliability |
| `FACTOR_SCORE_STABILITY` | agreement between donor-held-out scores (training-fold-only maps, §8) and full-fit scores | not reliability |
| `MEASUREMENT_RELIABILITY_OR_SENSITIVITY_ENVELOPE` | `ω_w` / determinacy with intervals, **explicitly labelled latent-Gaussian scale**; otherwise an envelope over hypothesized `R_y` | never an inter-assay correlation relabelled; never a Pearson-scale reliability |
| `ENDPOINT_SELECTION_STATUS` | the §11 terminal and the path through the rule | not a summary of the others |

The reliability field carries two standing notes: **an inter-assay correlation is
not `R_y`**, and **a latent-scale reliability is not a Pearson-scale reliability**.

---

## 13. Step 2 — planning-only feasibility envelope  *(repair 2)*

After and only after the measurement characterization, a sensitivity table over
`n` × plausible reliability × candidate nuisance/test assumptions. Every output
carries

```
PLANNING_ONLY__NOT_DECISION_CAPABLE
```

and any row at `n = 22` carries additionally

```
HYPOTHETICAL__REQUIRES_READER_ORACLE_RELEASE__NOT_AUTHORIZED
```

The current 12 fresh + 10 sealed oracle architecture is unchanged and no oracle
release is recommended. The values around ρ ≈ 0.61–0.76 are planning diagnostics
from an analytic correlation test; they depend on α, on nuisance treatment and on
the final confirmatory statistic, and are **not** qualification thresholds.

**Scale firewall (new in R3).** Under classical measurement-error assumptions
`Y_obs = Y* + ε` with `ε ⊥ (Y*, S)`, `Corr(S, Y_obs) = Corr(S, Y*)·√R_y`, so a
predictor perfect for the latent construct reads out at no more than `√R_y`.
That relation holds only when the reliability and the correlation are on the
**same** scale.

This measurement study produces reliability on the **latent-Gaussian scale**
(§5.3). It therefore **supplies no `R_y` to this envelope.** The envelope remains
over *hypothesized* Pearson-scale `R_y` values and stays `PLANNING_ONLY`. No
quantity produced by the measurement study may be inserted into it.

If a successor endpoint qualifies, it is a latent-scale construct, and **all**
downstream score, transport and power work for it is defined on that scale and
calibrated by simulation of the exact confirmatory test — never by importing a
Pearson-scale attenuation number. No mapping back to raw AT8 magnitude is
claimed here; establishing one would be a separate, separately justified piece of
work.

---

## 14. Standing retractions

- **"A + C + D is probably worth more than B."** Not established. Endpoint
  reliability, cohort size, nuisance treatment and predictor representation act
  on different parts of the problem and are complementary, not substitutes. The
  biological representation remains where real signal has to come from.
- **The oracle release is "free statistically."** Merging the fresh 12 with the
  sealed 10 destroys the independent oracle and changes the confirmation
  architecture.
- **Convergent validity as a reliability estimate.** Three distinct quantities;
  the third needs an explicit measurement model.
- **Freezing the nuisance is a "free lever."** Freezing the covariate *set* is
  straightforward; freezing nuisance *coefficients* from development and carrying
  them into confirmation changes the test and introduces its own transport
  assumption. The measured 0.269 → 0.554 figure is a planning diagnostic for an
  unqualified procedure.
- **R2: "M1 has no leakage pathway."** Wrong. Equal weights do not remove the
  estimated means and SDs that standardization requires. See §8.
- **R2: pTau/tTau as a "sensitivity alternative."** Wrong. A different estimand.
  See §6.
- **R3: `df = p(p+1)/2 − (2p+1)`, and `p ≥ 5 ⇒ df ≥ 4`.** Wrong. The formula
  counted one residual covariance where three are declared; at `p = 6, r = 3` the
  df is 6, not 8, and `p = 5` gives df 3 while `p = 3, r = 1` is underidentified.
  df is computed from the exact surviving graph. See §7.3.
- **R3: M1a treated as an independent simpler competitor with its own ω.** Equal
  weighting does not identify ω. M1a's reliability is identified by MM-C, the
  same model M2a uses; the dependency is now explicit and M1a is inadmissible
  without MM-C. See §7.4.
- **R3: the `B` formula described as guaranteeing endpoint precision.** It
  controls relative MC error of the tail probability only. See §10.
- **F1 stays open.** Naming `ρ = Corr(ỹ, s̃)` does not demonstrate transport.
  `STOP_T0_V21_EFFECT_TRANSPORT_NOT_AUTHORITY_BOUND` is not lifted until the
  exact `y`, the exact frozen score `s`, residualization, weighting,
  cross-fitting, influence/stability, the population whose ρ is claimed, the
  assumptions under which discovery ρ transports, sensitivity to distribution
  shift, and the exact confirmatory test and power procedure all qualify.

---

## 15. Execution order and authority state  *(repair 6)*

```
measurement-access contract (this document — DESIGN APPROVED, NUMERIC ACCESS PENDING)
  → discovery-only measurement characterization
  → measurement-model qualification
  → planning-only feasibility / power envelope
  → decision whether a successor endpoint is scientifically justified
  → only then: transport qualification and biological-representation work
```

Nothing here grants access; it requests it. Until approval:

- fresh-12 sealed; reader-oracle sealed; V20 immutable at `d5d67e21`;
- `S0_S4_SELECTION_AUTHORIZED = FALSE`;
- `FRESH_READER_VALIDATION_OPEN_AUTHORIZED = FALSE`;
- `READER_ORACLE_OPEN_AUTHORIZED = FALSE`;
- `V5_PRODUCTION_TRAINING_AUTHORIZED = FALSE`;
- estimand B ineligible for selection;
- expression association forbidden during measurement-model selection;
- training OFF;
- no numeric pathology outside the frozen AT8 endpoint has been read.
