# T0 PROSPECTIVE OUTCOME-MEASUREMENT ACCESS AMENDMENT

Date: 2026-09-12
Revision: **R2** (repair pass after review of R1 at `3ac60201`)
Status: `PROSPECTIVE_ACCESS_CONTRACT__NOT_YET_AUTHORIZED__NO_NUMERIC_VALUES_READ`
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
existing AT8 authorization has been parsed by any process in this lane, at R1 or
at R2.

### What changed in R2

R1 froze a specification prospectively, which was necessary but not sufficient —
the frozen measurement model also has to be well-posed. Eight repairs:

| # | R1 defect | R2 repair | §
| --- | --- | --- | --- |
| 1 | M1 called "no leakage pathway"; z-scoring needs sample means/SDs | statement retracted; all scaling is fold-internal or externally fixed | §8 |
| 2 | two-indicator AT8 method factor asserted, not proved | **proved underidentified**; replaced by a correlated residual, which is observationally equivalent and just-identified | §7 |
| 3 | pTau/tTau offered as a "sensitivity alternative" to absolute pTau | they are different estimands; split into estimand A and estimand B, B ineligible for selection | §6 |
| 4 | five bare numerical cutoffs | three converted to identification/estimability facts; the rest labelled conventions | §9 |
| 5 | logit boundary offset `(x(n−1)+0.5)/n` is n-dependent | primary analysis moved to a rank-based correlation input, removing the transform constant entirely | §5 |
| 6 | `B = 10,000` by convention | derived from a stated Monte Carlo precision budget | §10 |
| 7 | selection left to "scientific interpretation" — recreating F7 | deterministic executable rule with a `NO_SUCCESSOR_ENDPOINT_QUALIFIED` terminal | §11 |
| 8 | evidence classes could be satisfied by one matrix | six separate artifacts, each with its own digest, no double-counting | §12 |

Sections §1–§4 and §13–§15 are unchanged from R1 and were approved as written.

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

## 4. Missingness

- The missingness pattern per indicator and per donor is reported **first**, as a
  standalone artifact, before any model is fitted.
- No imputation in the primary model. Donors with partial indicator sets
  contribute under full-information estimation given the declared model; mean
  substitution, regression imputation, and listwise deletion as a default are
  prohibited.
- **Sparse-indicator rule (revised).** R1 declared a bare 25% cutoff. That number
  has no external justification, so the decision is made uncertainty-driven
  instead: every primary result is computed **with and without each indicator
  whose observed count falls below 21 of 28**, and if the endpoint-selection
  terminal differs between those fits, the terminal is `UNRESOLVED`. The count 21
  is a **prespecified operational convention** (`CONVENTION`, not a biological or
  statistical truth) chosen only to bound how many refits are performed; the
  decision rests on whether the conclusion moves, not on the cutoff.
- If fewer than three continuous indicators survive, the common-factor models are
  not estimable and the study terminates at M0/M1 with that stated.

---

## 5. Correlation input and transformations  *(repair 5)*

R1 specified a logit with boundary offset `(x·(n−1)+0.5)/n`. That is **n-dependent**:
the same raw AT8 value maps to a different target value in a 28-donor fit than in
a 27-donor training fold, so the target's meaning would shift with the fold. That
defect is not patched — it is removed, by making the primary analysis not depend
on a transform constant at all.

**Primary.** The measurement models are fitted to a **rank-based association
matrix**: Spearman for continuous–continuous pairs, polyserial for
continuous–ordinal pairs (Braak). This is invariant to *any* monotone transform
of the continuous indicators, so no epsilon, no offset and no sample-size-
dependent constant enters the primary specification, and Braak's ordinality is
handled natively rather than by pretending it is continuous.

If the resulting matrix is not positive definite — a real possibility at n = 28 —
it is projected to the nearest positive-definite matrix in the Frobenius norm by
Higham's alternating-projections algorithm, declared here, with the projection
distance reported as evidence. No other smoothing is admissible.

**Sensitivity.** Pearson correlations on declared monotone transforms:
`asin(sqrt(x/100))` for idx 12 (the variance-stabilizing transform for a
proportion — **finite at both 0 and 100, so it needs no boundary correction and
no constant**), and `log(x + c)` for the count-rate and concentration indicators,
where `c` is the assay's smallest reportable nonzero increment, to be recovered
from SEA-AD protocol documentation **before** access. If `c` cannot be recovered
from documentation, the log sensitivity is not run and that is reported —
`c` is **not** to be chosen by inspecting the observed minima.

The endpoint score's own scale is a separate matter and is governed by §8.

---

## 6. Estimand split: burden is not phosphorylation fraction  *(repair 3)*

R1 offered `log(pTau/tTau)` as a "sensitivity alternative" to absolute `log(pTau)`.
That was wrong: they answer different biological questions, and a ratio must
never become the endpoint because it happens to look statistically cleaner.

**Estimand A — `COMMON_DONOR_TAU_BURDEN`.** How much pathological tau the donor
carries. Absolute pTau legitimately reflects burden, and total tau is itself part
of the burden signal. Under A, `guhcl tTau` and `ripa tTau` enter as
**indicators in their own right**, not as denominators. Indicator set:
idx 12, 13, 21, 22, 25, 26 (six continuous), plus Braak as ordinal in M3a.

**Estimand B — `DONOR_TAU_PHOSPHORYLATION_FRACTION`.** How much of the donor's
tau is phosphorylated. Built on `log(pTau) − log(tTau)` within compartment.
A different construct, approaching phosphorylation state rather than load.

**Eligibility.** Estimand B models are computed and reported as measurement
evidence, and are **ineligible to be selected as the successor endpoint under
this amendment**. If B turns out to be the better-measured construct, that is a
finding to report and a *new* amendment to request — not an automatic
substitution. This is the mechanism that prevents the ratio silently replacing
the absolute signal.

`tTau`'s interpretation is therefore frozen per estimand now: **indicator** under
A, **normalizer** under B, and it may not be re-roled after seeing results.

---

## 7. Model family and identifiability  *(repair 2)*

### 7.1 The two-indicator method factor is underidentified — proof

R1 proposed a latent AT8-method factor loading on idx 12 and idx 13 only,
orthogonal to the common factor. Write, with `Var(F) = Var(M) = 1`,
`Cov(F, M) = 0`:

```
x₁ = λ₁F + γ₁M + e₁        x₂ = λ₂F + γ₂M + e₂
```

The loadings `λ₁, λ₂` are identified from the covariances of `x₁, x₂` with the
other (≥ 2) indicators, which involve no `γ`. That leaves exactly three moments
carrying information about the method parameters:

```
Var(x₁)     = λ₁² + γ₁² + ψ₁
Var(x₂)     = λ₂² + γ₂² + ψ₂
Cov(x₁, x₂) = λ₁λ₂ + γ₁γ₂
```

Three equations in four unknowns `(γ₁, γ₂, ψ₁, ψ₂)`. **Underidentified by one.**
It can be rescued only by imposing `γ₁ = γ₂`, an equality constraint that is
untestable with two indicators.

### 7.2 The correlated residual is just-identified and equivalent

Replace the method factor with a residual covariance `θ₁₂ = Cov(e₁, e₂)`:

```
Var(x₁)     = λ₁² + ψ₁
Var(x₂)     = λ₂² + ψ₂
Cov(x₁, x₂) = λ₁λ₂ + θ₁₂
```

Three equations, three unknowns. **Just identified.** And under the constraint
that rescues the method factor, `θ₁₂ = γ₁γ₂` — the two specifications are
observationally equivalent. The method factor therefore buys no information and
costs one parameter of identification, which at n = 28 is not a trade worth
making.

**Decision, frozen now, before any covariance matrix is seen:** the AT8 method
dependence is modelled as a **prespecified correlated residual** between idx 12
and idx 13. No latent method factor is fitted.

### 7.3 Degrees of freedom, and why tTau must be an indicator

For `p` continuous indicators, one common factor with variance fixed at 1, `p`
loadings, `p` residual variances and 1 correlated residual:

```
df = p(p+1)/2 − (2p + 1)
```

| p | df |
| --- | --- |
| 4 | 1 |
| 5 | 4 |
| 6 | **8** |

At `p = 4` (AT8 pair + two pTau, tTau excluded) the model has **1 df** and is not
credibly testable at n = 28. Including the two tTau columns as estimand-A
indicators gives `p = 6` and `df = 8`. So §6's scientific decision — total tau is
part of tau burden — is also what makes the model structurally testable. If
missingness reduces the indicator set below `p = 5`, the common-factor model is
reported as `NOT_CREDIBLY_TESTED` and cannot support a successor endpoint.

### 7.4 The frozen family

**Estimand A (eligible for selection):**

- **M0a — incumbent.** `percent AT8 positive area` alone. Estimand
  `PERCENT_AT8_POSITIVE_AREA`. Reliability is **unidentified** for a single
  indicator, which is precisely the gap a successor would close.
- **M1a — prespecified composite.** Equal-weight mean of standardized indicators.
  No estimated weights. Scaling governed by §8.
- **M2a — one-factor congeneric** over the continuous indicators, with the
  prespecified idx 12 ↔ idx 13 correlated residual and correlated residuals
  permitted within biochemical compartment (guhcl pair, ripa pair), all declared
  here.
- **M3a — M2a plus Braak** as an ordinal indicator via a polyserial link.

**Estimand B (computed, reported, ineligible):** M1b, M2b, defined identically on
the within-compartment log-ratio indicators.

No model outside this family may be fitted in the primary analysis.

---

## 8. Leakage prohibition on target construction  *(repair 1)*

**R1 said M1 had "no data-derived target map and no leakage pathway." That is
retracted and was wrong.** Equal weights remove *learned weights*; they do not
remove the estimated means and standard deviations that standardization requires.
If those are computed on all 28 donors, a held-out donor has contributed to the
target map used to evaluate itself.

The rule, applying to every data-derived component — standardizations, rank
mappings, loadings, factor-score coefficients, polyserial thresholds, PD
projections:

- either the measurement map is **externally fixed**, from an authority
  independent of these 28 donors, and carried in unchanged;
- or **every data-derived component is estimated inside the training fold** and
  the held-out donor is scored with the training-only map, unchanged.

There is no third option, and "equal weights" is not one.

Only after the measurement-model form and the selection rule are frozen may a
final model be refit on the lawful discovery population to define the eventual
frozen successor target.

---

## 9. Refusal criteria — identification facts first, conventions labelled  *(repair 4)*

R1 stated five bare numerical cutoffs. Three are replaced by facts about whether
the question is answerable at all; the remainder are labelled.

**Identification and estimability criteria (not conventions):**

1. **Convergence.** If the model fails to converge on the full discovery fit, or
   fails to converge in more than 5% of bootstrap resamples, the common construct
   is `NOT_ESTABLISHED`. Non-convergence is an identification fact.
2. **Indicator support.** An indicator whose standardized loading has a bootstrap
   interval **including zero** is declared not an indicator of the construct and
   is removed, with the model refitted and both versions reported. This is
   inferential, and replaces R1's bare 0.40 loading cutoff.
3. **Testability.** `df ≥ 4` (i.e. `p ≥ 5` surviving indicators) is required
   before a common-factor model may support a successor endpoint; otherwise
   `NOT_CREDIBLY_TESTED`. Derived in §7.3, not chosen.
4. **Ordinal estimability.** Braak enters M3a only if every ordinal threshold is
   estimable — no empty or singleton extreme category. This replaces R1's ">50%
   at ceiling" rule with the condition that actually determines whether the
   parameter exists.
5. **Method dominance.** Reported as the fitted `θ₁₂` with its bootstrap
   interval, and as the share of idx 12 / idx 13 covariance it accounts for. No
   threshold. If `θ₁₂`'s interval excludes zero, method dependence is
   *established* and M2a/M3a are preferred over M1a under §11 step 3 — the
   finding routes the selection rather than triggering a refusal.

**Prespecified conventions (labelled `CONVENTION`, not biological truth):**

- the 21-of-28 sparse-indicator refit trigger (§4) — bounds the number of refits;
- the 5% bootstrap non-convergence allowance in criterion 1;
- the reliability-interval informativeness width in §11 step 2.

**Uncertainty gate, overriding all of the above.** Any reliability-like quantity
is reported as a bootstrap interval, never a point. If that interval spans values
that would change the feasibility verdict, the verdict is `UNRESOLVED` and no
endpoint change is proposed. A `COMMON_FACTOR_NOT_ESTABLISHED` finding must arise
because the model is unsupported, unstable or unidentified — never because a
sample correlation landed at 0.29 rather than 0.30.

---

## 10. Monte Carlo precision budget  *(repair 6)*

`B = 10,000` is a convention, and this project has already told V5 not to inherit
conventional Monte Carlo counts without a precision budget. T0 will not
reintroduce that through a bootstrap.

**Quantity estimated.** The endpoints of a BCa bootstrap interval for each
reported measurement quantity, i.e. quantiles of the bootstrap distribution at
the bias- and acceleration-adjusted tail levels `α*_lo, α*_hi`.

**Precision requirement.** The Monte Carlo standard error of the realized tail
proportion at an adjusted level `α*` must not exceed **10% of `α*`** (relative MC
SE `r = 0.10`). Since the realized tail count is binomial,
`SE = sqrt(α*(1−α*)/B) ≤ r·α*`, giving

```
B ≥ (1 − α*) / (α* · r²)
```

| adjusted tail `α*` | required `B` |
| --- | --- |
| 0.025 | 3,900 |
| 0.010 | 9,900 |
| 0.005 | 19,900 |

**Rule.** Run an initial `B₀ = 4,000`, read the realized BCa-adjusted tail levels,
and if any is more extreme than 0.025, re-run at the `B` its level requires by
the formula above. The realized `B`, the realized `α*_lo`/`α*_hi`, and the
attained relative MC SE are recorded in the receipt. `B` is thus **derived from
the requirement**, not asserted.

**Determinism.** `numpy.random.Generator(PCG64)`, seed frozen in the receipt,
resampling **at the donor level** (28 donors, the experimental unit — never
cells, never indicator values within donor), stratification none, and the full
resample-index array digested so the run replays exactly.

If a project-wide Monte Carlo precision authority is later established, this
budget defers to it, and the receipt records which authority governed.

---

## 11. Deterministic endpoint-selection rule  *(repair 7)*

R1 left selection to "measurement validity, stability and scientific
interpretation," which is an unconstrained post-result choice — exactly the F7
defect this project already found in V20's undeclared tie rule. The rule below is
executable, ordered, and frozen now.

Estimand-B models are excluded at every step. All steps run **before any
expression association is computed**.

```
STEP 1 — CONSTRUCT SUPPORT
  A model is admissible only if all hold:
    (a) converges on the full discovery fit;
    (b) converges in >= 95% of bootstrap resamples;
    (c) every retained indicator's loading interval excludes 0   (§9.2);
    (d) df >= 4                                                   (§9.3);
    (e) Braak thresholds estimable, for M3a only                  (§9.4).
  If no multi-indicator model is admissible:
      -> COMMON_FACTOR_NOT_ESTABLISHED
      -> NO_SUCCESSOR_ENDPOINT_QUALIFIED, M0a stands.

STEP 2 — THE SUCCESSOR MUST DELIVER WHAT M0a CANNOT
  M0a is a single indicator, so its reliability is UNIDENTIFIED. A successor
  earns its place by identifying reliability at all, informatively:
    the bootstrap interval for the score's reliability (omega, and factor-score
    determinacy for M2a/M3a) must have width <= 0.25 on the [0,1] scale.
    [width 0.25 is labelled CONVENTION: an informativeness requirement,
     not a claim about biology]
  If no admissible model meets this:
      -> MEASUREMENT_RELIABILITY_UNRESOLVED
      -> NO_SUCCESSOR_ENDPOINT_QUALIFIED, M0a stands.

STEP 3 — PARSIMONY, WITH ONE DECLARED EXCEPTION
  Among models passing 1 and 2, select the FEWEST estimated parameters.
  A more complex model is preferred only if it resolves a prespecified
  measurement defect the simpler model demonstrably exhibits. Exactly one
  such defect is declared in advance:
    the idx12<->idx13 residual correlation theta_12 has an interval
    excluding 0 (method dependence established), which admits M2a/M3a
    over M1a.
  No other defect may be invoked.

STEP 4 — TIES
  Equal parameter counts resolve in the frozen order  M1a < M2a < M3a,
  earliest wins. Declared now. No tolerance, no post-hoc tie-break.

STEP 5 — TERMINALS
  PASS_T0_SUCCESSOR_ENDPOINT_QUALIFIED__<model>__COMMON_DONOR_TAU_BURDEN
  NO_SUCCESSOR_ENDPOINT_QUALIFIED            (M0a stands; a real result)
  MEASUREMENT_RELIABILITY_UNRESOLVED
  COMMON_FACTOR_NOT_ESTABLISHED
  UNRESOLVED                                  (sparse-indicator refits disagree)
```

`NO_SUCCESSOR_ENDPOINT_QUALIFIED` is a lawful and publishable outcome: it would
say these assays do not identify a better-measured tau-burden construct at this
cohort size. It is not a failure of the study.

A qualifying successor still requires its own freeze, its own receipt and its own
confirmation contract before it carries any authority. V20 and V21 keep their
existing meaning; nothing here reinterprets them.

---

## 12. Output schema — six separate evidence classes  *(repair 8)*

Six artifacts, each independently digested. **No single correlation matrix or
coefficient may populate more than one field**, and each field names the
computation that produced it.

| field | what it is | what it is NOT |
| --- | --- | --- |
| `CONVERGENT_VALIDITY` | the rank-based association matrix with bootstrap intervals | not reliability, not factor support |
| `METHOD_VARIANCE` | fitted `θ₁₂` with interval; share of idx12/idx13 covariance explained | not a construct claim |
| `COMMON_FACTOR_SUPPORT` | convergence rates, loadings with intervals, df, PD-projection distance | not reliability |
| `FACTOR_SCORE_STABILITY` | agreement between donor-held-out scores (training-fold-only maps, §8) and full-fit scores | not reliability |
| `MEASUREMENT_RELIABILITY_OR_SENSITIVITY_ENVELOPE` | ω / determinacy with intervals where identified; otherwise an envelope over plausible `R_y` | never an inter-assay correlation relabelled |
| `ENDPOINT_SELECTION_STATUS` | the §11 terminal and the path through the rule | not a summary of the others |

The reliability field carries an explicit standing note: **an inter-assay
correlation is not `R_y`**. Convergent association, shared latent variance and
measurement reliability are three distinct quantities, and the third is
identified only under a stated measurement model with assumptions about
assay-specific error.

---

## 13. Step 2 — planning-only feasibility envelope  *(unchanged, approved)*

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
the final confirmatory statistic, and are **not** qualification thresholds. Once a
successor endpoint, score, nuisance model and confirmatory test are frozen, power
must be recalibrated to that exact procedure by simulation rather than promoted
from the analytic approximation.

The attenuation relation is retained as a **model-based diagnostic**: under
explicit classical measurement-error assumptions `Y_obs = Y* + ε` with
`ε ⊥ (Y*, S)`, `Corr(S, Y_obs) = Corr(S, Y*)·√R_y`, so a predictor perfect for
the latent construct still reads out at no more than `√R_y`. The envelope is
reported over plausible `R_y` unless the measurement model identifies a
defensible reliability parameter.

---

## 14. Standing retractions  *(unchanged, plus R2 additions)*

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
  assumption, needing separate qualification and simulation. The measured
  0.269 → 0.554 figure is a planning diagnostic for an unqualified procedure.
- **R2: "M1 has no leakage pathway."** Wrong. Equal weights do not remove the
  estimated means and SDs that standardization requires. See §8.
- **R2: pTau/tTau as a "sensitivity alternative."** Wrong. It is a different
  estimand. See §6.
- **F1 stays open.** Naming `ρ = Corr(ỹ, s̃)` does not demonstrate transport.
  `STOP_T0_V21_EFFECT_TRANSPORT_NOT_AUTHORITY_BOUND` is not lifted until the
  exact `y`, the exact frozen score `s`, residualization, weighting,
  cross-fitting, influence/stability, the population whose ρ is claimed, the
  assumptions under which discovery ρ transports, sensitivity to distribution
  shift, and the exact confirmatory test and power procedure all qualify.

---

## 15. Execution order and authority state  *(unchanged, approved)*

```
measurement-access contract (this document, approved)
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
- expression association forbidden during measurement-model selection;
- training OFF;
- no numeric pathology outside the frozen AT8 endpoint has been read.
