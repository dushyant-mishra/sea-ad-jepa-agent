# T0 PROSPECTIVE OUTCOME-MEASUREMENT ACCESS AMENDMENT

Date: 2026-09-12
Status: `PROSPECTIVE_ACCESS_CONTRACT__NOT_YET_AUTHORIZED__NO_NUMERIC_VALUES_READ`
Requested authority: read numeric values of seven declared pathology columns,
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

This amendment is written *before* any of those values is read, so that the
measurement question is decided on its design rather than on its results.

**What has been read so far:** the file's byte digest, its header line, its
column count and its row count. Column *names*, not values. No numeric pathology
outside the existing AT8 authorization has been parsed by any process in this
lane.

---

## 1. Provenance and column identity binding

Source: `data/processed/metadata/sea_ad_mtg_donor_pathology_targets.csv`

| property | value |
| --- | --- |
| file SHA-256 (raw bytes) | `ebbe9bc0c623c663331425794bd8fb1b4c4f3657455cf55d806cc383ea6d8e3a` |
| header line SHA-256 | `88114843211d095dbf3ccbc91cc1add4172ca15f7fe6ced07f9ea679ae785385` |
| columns | 27 |
| data rows | 84 |

The file digest reproduces V20's frozen `expected_source_sha256` exactly, so this
is the same authority V20 read. The 84 rows exceed the 46-donor T0 cohort; the
loader filters by the frozen donor set and must continue to.

Declared columns, bound by index **and** by digest of the column name, so that a
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

Index 12 is already authorized (the frozen V20 endpoint) and is listed for
completeness. The **six new columns** requested are indices 5, 13, 21, 22, 25, 26.

Any column not in this table remains unparsed. In particular the amyloid (6E10,
abeta40/42), glial (GFAP, Iba1), neuronal (NeuN), `APOE Genotype`,
`Cognitive Status`, `Thal`, `CERAD score`,
`Overall AD neuropathological Change` and `Severely Affected Donor` columns are
**not** requested and must remain refused.

---

## 2. Scientific rationale, indicator by indicator

Each column is declared with what it measures and — equally important — how it
differs from the others, because indicators that differ only by method do not
provide independent evidence about the construct.

**idx 12 — `percent AT8 positive area_Grey matter`** (incumbent endpoint).
AT8 is a monoclonal antibody against phospho-tau at pSer202/pThr205. Percent
positive area is the areal fraction of immunoreactive signal in grey matter.
Image morphometry. This is the frozen V20 endpoint and the incumbent against
which any successor must be judged.

**idx 13 — `number of AT8 positive cells per area_Grey matter`**.
Same antibody, same imaging pipeline, different summary statistic: object count
rather than area fraction. It is sensitive to the *number* of affected cells
where idx 12 is sensitive to *total burden including neuropil threads*.
**It shares both reagent and method with idx 12.** It must therefore enter any
measurement model with an explicit AT8-method factor; treating it as an
independent indicator would let method variance masquerade as construct variance
and inflate any reliability-like quantity.

**idx 21 — `guhcl pTau_Grey matter`**.
Guanidine-HCl extraction followed by biochemical quantification. Guanidine
solubilizes aggregated protein, so this indexes the **insoluble / fibrillar**
phospho-tau pool. Independent reagent, independent method, independent tissue
aliquot from the morphometry — genuinely different measurement error.

**idx 25 — `ripa pTau_Grey matter`**.
RIPA-buffer extraction, indexing the comparatively **soluble** phospho-tau pool.
Different biochemical compartment from idx 21, so the two are not replicates of
each other either; they are complementary indicators whose ratio carries
biological meaning about aggregation state.

**idx 22, 26 — `guhcl tTau`, `ripa tTau`**.
Total tau in the matching compartments. Requested because **unnormalized pTau
confounds phosphorylation state with total tau abundance**: a donor with more tau
overall will show more phospho-tau without being more pathological in the sense
the endpoint intends. The standard normalization is pTau relative to tTau within
compartment. Declaring these now, prospectively, is deliberate — discovering
mid-analysis that the biochemical indicators need normalization and then
requesting more columns would be exactly the retrospective broadening this
contract exists to prevent.

**idx 5 — `Braak`**.
Ordinal neurofibrillary staging, 0–VI, defined by the **anatomical distribution**
of neurofibrillary pathology across regions. This is a different construct
emphasis from every other indicator: it measures topographic spread, not local
density in the sampled middle temporal gyrus, and it is coarse and liable to
ceiling effects in an aged, heavily-affected cohort. It is requested as a
**validity check on the common factor, not as a continuous replicate**, and if it
enters a model at all it enters with an ordinal link.

---

## 3. Allowed population

Numeric values may be read for the **28 DISCOVERY donors only**, identified by
the frozen donor-set digest
`4395fec74bcf7abf192d731db3c827fa25cfde1b5297db4203b041984a780d33`.

Forbidden, absolutely, for every column in this amendment:

- the 12 fresh `reader_validation` donors — remain sealed;
- the 10 `reader_oracle` donors — remain sealed;
- the 18 spent historical-validation donors — **not authorized by this
  amendment**. They may not be used to select the endpoint form, the indicator
  set, the transformations, or the factor structure. They are already spent for
  AT8, but "already spent" is not the same as "available for this purpose," and
  extending them requires a separate explicit authority change. After the
  measurement model is frozen they may be proposed for predeclared
  sensitivity/reproduction under that separate decision.

The reader must enforce this the way the AT8 loader already does — by refusing
any donor outside the included set, before values are touched, and by requiring
the loaded set to reproduce the frozen digest — not by filtering after loading.

---

## 4. Missingness

Frozen before the data are seen:

- The missingness pattern per indicator and per donor is reported **first**, as a
  standalone artifact, before any model is fitted.
- No imputation in the primary model. Donors with partial indicator sets
  contribute under full-information estimation given the declared model; mean
  substitution, regression imputation and listwise deletion as a default are all
  prohibited.
- **Any indicator missing for more than 7 of the 28 donors (25%) is dropped from
  the primary model** and reported as insufficiently observed. This threshold is
  frozen here, before the pattern is known, and may not be relaxed after seeing
  it.
- If dropping indicators under that rule leaves fewer than three continuous
  indicators, the common-factor models `M2`/`M3` are not estimable and the study
  terminates at `M0`/`M1` with that stated.

---

## 5. Admissible transformations

One primary transform per indicator, declared now, with one prespecified
alternative for sensitivity. **No post-hoc transform selection**; the primary
result is the primary transform, and the alternative is reported alongside it
rather than replacing it.

| indicator | measurement semantics | primary | sensitivity alternative |
| --- | --- | --- | --- |
| idx 12 percent area | bounded proportion [0,100], right-skewed | `logit(x/100)` with a frozen boundary offset | `log1p(x)` |
| idx 13 count per area | non-negative rate, right-skewed | `log1p(x)` | untransformed |
| idx 21, 25 pTau | non-negative concentration, typically lognormal | `log(x)` | `log(pTau/tTau)` within compartment |
| idx 22, 26 tTau | non-negative concentration | `log(x)` | — used as normalizer only |
| idx 5 Braak | ordinal 0–VI | none; ordinal | none |

The logit boundary offset is frozen at `(x·(n−1) + 0.5)/n` on the proportion
scale, the standard smoothing, chosen now rather than after observing whether any
donor sits at 0 or 100.

---

## 6. Candidate measurement-model family

Deliberately small, and fixed here. No model outside this family may be fitted in
the primary analysis.

- **M0 — incumbent.** AT8 percent-area alone. Estimand
  `PERCENT_AT8_POSITIVE_AREA`. This is the status quo and the thing to beat.
- **M1 — prespecified composite.** Equal-weight mean of z-scored, transformed
  continuous indicators. **No estimated weights**, therefore no data-derived
  target map and no leakage pathway. The conservative successor.
- **M2 — one-factor congeneric model** over the continuous indicators, with an
  explicit **AT8-method factor** loading on idx 12 and idx 13, and correlated
  residuals permitted within biochemical compartment.
- **M3 — M2 plus Braak** as an ordinal indicator with a threshold link.

Selection among `M0`–`M3` is on **measurement validity, stability and scientific
interpretation only**, and is completed and frozen **before any expression
association is computed**. A model may not be preferred because it correlates
better with expression. That ordering is the whole point of doing this
prospectively.

---

## 7. What would reject a common latent-tau interpretation

Frozen refusal criteria, stated before the data are seen. At n = 28, global SEM
fit indices are not trustworthy, so the primary criteria are deliberately simple
and interpretable:

1. **Insufficient convergence.** If the mean pairwise correlation among the
   transformed continuous indicators, excluding the within-AT8-method pair, is
   below 0.30, the common-construct interpretation is rejected outright.
2. **Method dominance.** If `corr(idx 12, idx 13)` exceeds every
   morphometry-to-biochemistry correlation by a margin greater than 0.30, method
   variance is declared dominant and a single common factor is refused.
3. **Weak indicator.** Any indicator with a standardized loading below 0.40 on
   the common factor is declared not an indicator of that construct and is
   removed, with the model refitted and both versions reported.
4. **Uncertainty swamps the conclusion.** Any reliability-like quantity is
   reported as a bootstrap interval (BCa, B = 10,000, donor-level resampling),
   never as a point. If that interval spans values that would change the
   feasibility verdict, the verdict is `UNRESOLVED` and no endpoint change is
   proposed on that basis.
5. **Ordinal ceiling.** If Braak is at its maximum for more than half the 28
   discovery donors, it is reported as ceiling-limited and excluded from `M3`.

A rejection here is a real and publishable result: it would say the available
assays do not identify a shared tau-burden construct at this cohort size, which
settles the endpoint question in the other direction.

---

## 8. Leakage prohibition on target construction

This is the subtle failure mode and it is prohibited explicitly.

If scales, transformations, factor loadings or composite weights are estimated
from the pathology observations themselves, then a held-out donor's own outcome
has helped define the target used to evaluate that donor. For any donor-held-out
predictive evaluation:

- either the measurement map is **externally frozen** — fixed weights, fixed
  scaling, no estimation from this cohort (which is why `M1` uses equal weights);
- or **every data-derived component is fitted inside the training fold**, and the
  held-out donor is scored with the training-only map.

Only after the measurement-model family and the selection rule are frozen may a
final measurement model be refit on the lawful discovery population to define the
eventual frozen successor target.

---

## 9. Successor endpoint semantics

If a latent endpoint qualifies, it is a **successor target, not a repair of
AT8**. Its estimand is

```
COMMON_DONOR_TAU_BURDEN
```

which is a different scientific question from

```
PERCENT_AT8_POSITIVE_AREA
```

V20 and V21 keep their existing meaning; nothing here reinterprets them. A
successor endpoint requires its own freeze, its own receipt and its own
confirmation contract before it can carry any authority.

---

## 10. Step 2 — planning-only feasibility envelope

After and only after the measurement characterization, a sensitivity table over
`n` × plausible reliability × candidate nuisance/test assumptions. Every output
carries:

```
PLANNING_ONLY__NOT_DECISION_CAPABLE
```

and any row at `n = 22` carries additionally:

```
HYPOTHETICAL__REQUIRES_READER_ORACLE_RELEASE__NOT_AUTHORIZED
```

The current 12 fresh + 10 sealed oracle architecture is unchanged and no oracle
release is recommended. The values around ρ ≈ 0.61–0.76 are planning diagnostics
from an analytic correlation test; they depend on α, on nuisance treatment and on
the final confirmatory statistic, and they are **not** qualification thresholds.
Once a successor endpoint, score, nuisance model and confirmatory test are
frozen, power must be recalibrated to that exact procedure by simulation rather
than promoted from the analytic approximation.

The attenuation relation is retained as a **model-based diagnostic**: under
explicit classical measurement-error assumptions `Y_obs = Y* + ε` with
`ε ⊥ (Y*, S)`, `Corr(S, Y_obs) = Corr(S, Y*)·√R_y`, so a predictor that is
perfect for the latent construct still reads out at no more than `√R_y`. An
inter-assay correlation is **not** `R_y`, and the envelope is reported over
plausible `R_y` unless the measurement model identifies a defensible reliability
parameter.

---

## 11. Corrections to the proposal that produced this amendment

Recorded so the reasoning is auditable rather than quietly dropped:

- **Retracted: "A + C + D is probably worth more than B."** Not established.
  Endpoint reliability, cohort size, nuisance treatment and predictor
  representation act on different parts of the problem and are complementary, not
  substitutes. The biological representation remains where real signal has to
  come from; the endpoint work bounds what would be observable and does not
  replace it.
- **Retracted: the oracle release is "free statistically."** Merging the fresh 12
  with the sealed 10 destroys the independent oracle and changes the confirmation
  architecture. That may eventually be rational, but only after we know what
  target and what test are being confirmed.
- **Withdrawn: convergent validity as a reliability estimate.** Convergent
  association, shared latent variance and measurement reliability are three
  distinct quantities; the third requires an explicit measurement model with
  assumptions about assay-specific error.
- **Corrected: freezing the nuisance is not a free lever.** Freezing the covariate
  *set* is straightforward. Freezing nuisance *coefficients* from development and
  carrying them into confirmation changes the test and introduces its own
  transport assumption, which needs separate qualification and simulation. The
  measured 0.269 → 0.554 power figure is a planning diagnostic for a procedure
  that is not yet qualified.
- **F1 stays open.** Naming `ρ = Corr(ỹ, s̃)` does not demonstrate transport.
  `STOP_T0_V21_EFFECT_TRANSPORT_NOT_AUTHORITY_BOUND` is not lifted until the
  exact `y`, the exact frozen score `s`, residualization, weighting,
  cross-fitting, influence/stability, the population whose ρ is claimed, the
  assumptions under which discovery ρ transports, sensitivity to distribution
  shift, and the exact confirmatory test and power procedure all qualify.

---

## 12. Execution order, once authorized

```
measurement-access contract (this document, approved)
  → discovery-only measurement characterization
  → measurement-model qualification
  → planning-only feasibility / power envelope
  → decision whether a successor endpoint is scientifically justified
  → only then: transport qualification and biological-representation work
```

## 13. Authority state — unchanged by this document

Nothing here grants access; it requests it. Until approval:

- fresh-12 sealed; reader-oracle sealed; V20 immutable at `d5d67e21`;
- `S0_S4_SELECTION_AUTHORIZED = FALSE`;
- `FRESH_READER_VALIDATION_OPEN_AUTHORIZED = FALSE`;
- `READER_ORACLE_OPEN_AUTHORIZED = FALSE`;
- `V5_PRODUCTION_TRAINING_AUTHORIZED = FALSE`;
- training OFF;
- no numeric pathology outside the frozen AT8 endpoint has been read.
