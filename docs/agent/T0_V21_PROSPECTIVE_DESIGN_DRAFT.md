# T0 V21 prospective design — DRAFT FOR REVIEW, NOT FROZEN

**Status: `DRAFT_FOR_REVIEW_NOT_FROZEN`.** Nothing here is authority. V21 must
not execute until this is reviewed, amended and frozen. V20 is unchanged,
`training_authorized: false`, and steps 1–4 stand as published.

This draft exists because the V20 diagnostic arc established what a successor
has to fix, and because the confirmation donors have now informed method
development and can no longer silently be used to choose V21 machinery.

---

## 0. Two blocking questions the contract cannot answer by itself

These must be resolved before freezing, because the design branches on them.

### 0.1 Is a fresh confirmation set available? — the decisive one

Read from the frozen authorities:

| quantity | value | source |
| --- | ---: | --- |
| donors with AT8 available | **84** | `T0_AT8_AVAILABILITY_METADATA.available_donor_count` |
| donors in the primary MTG immune membership | **46** | `…membership_donor_count` |
| membership donors with AT8 available | 46 of 46 | `…membership_donors_available` |
| eligible donors after the frozen predicate | 46 of 46 candidates | `T0_ELIGIBLE_DONOR_METADATA` |
| already allocated | 28 discovery + 18 confirmation | frozen donor-role authority |

**Every eligible donor in the T0 population is spent.** But the binding
constraint is the *membership*, not pathology availability: up to **38
AT8-available donors sit outside the current MTG immune membership.**

What must be established, pathology-blind (availability only, never values):

- how many of those 38 have MTG immune cells in the authenticated population at
  all, versus being absent from this region or cohort;
- how many would pass the frozen eligibility predicate unchanged;
- whether the membership can be extended without altering the frozen population
  closure, or whether extension constitutes a new population requiring its own
  freeze.

**If ≥ 12–15 fresh eligible donors are materialisable**, V21 should be designed
around a genuinely fresh confirmation set and the contamination question
disappears. **If not**, V21 must adopt §1.3's degraded status honestly rather
than describing a re-test of spent donors as confirmation.

### 0.2 Does the rare-biology estimand have any power at this cohort size?

Step 4 showed the obvious remedy (1:1 matching) is underpowered. Before V21
commits to a rare-biology arm at all, a **power calibration on discovery donors
only** should establish what effect size the proposed continuous statistic can
detect at 18-donor scale. If the answer is "nothing smaller than the effect we
already failed to establish", the arm should be dropped rather than reformulated.

---

## 1. Targets and their status

### 1.1 T1 — broad immune state, primary confirmatory

Unchanged in intent from V20: expression-only broad-IMMUNE score against
donor-disjoint AT8 pathology, donor-level HC3 inference with the frozen
`[1, age_c, age_c², sex]` nuisance design.

Retained as the **primary confirmatory target**. V20 adjudicated it
`BROAD_IMMUNE_EXPRESSION_TARGET_SUPPORTED_INTERNAL` at p = 0.021, and the
recovered sensitivities (composition 0.019, measurement 0.030) are now on
record.

### 1.2 T2 — rare biology as a continuous / neighbourhood direction, exploratory

**Not a hard binary tail.** The V20 tail estimand thresholded a
detection-sensitive score at a frozen quantile, which coupled the estimand to
the confound and put all inference on an extreme region of a noisy
distribution. V21 replaces it with a continuous formulation, of which the
specific form is an open design choice (§2.4).

**Status: exploratory and non-qualifying**, for a reason independent of its
formulation: the held-out coherence statistic on the confirmation donors is part
of the tail adjudication chain and its value is now known to us. Any V21 rare
result on those same donors is a second look. If §0.1 yields fresh donors, T2's
status can be revisited *in the frozen contract*, not afterwards.

### 1.3 Confirmatory status if no fresh donors are available

Stated in advance so it cannot be softened later:

- **T1 remains confirmatory**, conditional on §3 estimator selection being
  strictly discovery-only and single-shot. Confirmation AT8 has never been read,
  and the HC3 t-statistic depends on the score–AT8 relationship, so a
  discovery-selected estimator cannot have been tuned toward it. The residual
  exposure is optimism about generalisation, not a false-positive route, and it
  must be stated in the result.
- **T2 is exploratory** regardless.
- V21 may **not** describe itself as an independent confirmation of V20. It is a
  revised-method analysis on a partially spent cohort, and the report must say so
  in those words.

---

## 2. The estimator problem, and what V21 changes

### 2.1 The defect V21 must fix

`score_raw_counts` computes

```
score = Σ over DETECTED genes of log1p(10000·count/library)·w  −  Σ over ALL genes of mu·w
```

The summation set is the detected genes; the offset set is all genes. A gene
dropping to zero loses its term while the offset is unchanged, so the estimator
is **not detection-invariant by construction**. Step 2 measured the consequence:
the upper tail is the most depth-sensitive region of the distribution
(`corr(score, displacement)` = −0.557 at quarter depth), and a 10% depth
reduction churns 9–11% of the tail label.

### 2.2 A pre-registered estimator family

| id | definition | rationale |
| --- | --- | --- |
| `S0` | the frozen V20 score | mandatory baseline |
| `S1` | `Σ_detected (log1p(CP10K) − mu)·w` | summation and offset sets agree; a dropout contributes nothing to either |
| `S2` | `S0` restricted to a **common measured gene core** | where detection ≈ 1 the set mismatch is negligible |
| `S3` | `S1` ∩ `S2` | both fixes |
| `S4` | weighted within-cell ranks over the core | invariant to monotone count transforms |

The core threshold for `S2`/`S3`/`S4` is **derived from the discovery detection
profile, not typed** — consistent with the standing rule that dataset geometry
sets scale-sensitive parameters. It is also the "common measured gene core"
already on the V5 derivation list, so this work is shared.

### 2.3 Selection rule — joint, and discovery-only

Selection is on **discovery donors only**, pathology-blind, and never sees
confirmation cells or any AT8 value. Two criteria, applied jointly:

1. **Same-cell measurement robustness** — under the existing frozen thinning
   ladder, the displacement of the continuous score and its within-donor rank
   stability. Reuses the machinery already built and tested.
2. **Preservation of independent held-out biology** — the held-out program's
   donor-consistency must survive the estimator change, measured on discovery
   donors with the discovery-fit scale.

**Both are required.** Robustness alone is gameable: a candidate can be perfectly
stable by flattening the score into noise. Criterion 2 is what rules that out,
and it is the reason not to select on binary-label stability, which would merely
optimise an arbitrary threshold.

Selection must be **single-shot**: one pass, frozen result, no iteration after
seeing any confirmation quantity. A leave-one-discovery-donor-out variant of the
selection is recommended, because the discovery donors also fit `beta`/`mu`/
`sigma` and the criterion could otherwise overfit discovery's particular depth
profile.

### 2.4 The continuous rare-biology statistic — open design choice

Candidates to be narrowed before freezing:

- **Upper-region mass**: donor summary = mean score over the top-q fraction,
  with q derived from the discovery score distribution, tested for association
  beyond the donor mean.
- **Neighbourhood coherence**: for each cell, agreement of its held-out profile
  with its k nearest neighbours in score space; donor summary = coherence in the
  upper score region relative to the rest.
- **Continuous interaction**: whether the score's association with pathology
  strengthens in its upper region — a shape question rather than a
  membership question.

The third is the most conservative: it needs no threshold at all. I lean toward
it, with the first as a pre-registered secondary.

---

## 3. Ridge search

**Widen the grid prospectively and require an interior optimum.** V20's
`ridge_multiplier_exponents` ran −6.0 to +2.0 and the LOODO optimum landed on the
`+2.0` endpoint. V21 widens the range and **STOPs if the optimum lands on either
boundary**, since a boundary optimum means the grid is misspecified and the fit is
not well-posed.

One thing this fix should not be oversold as. The HC3 t-statistic is invariant to
positive rescaling of the predictor, so a boundary λ barely moves the state
p-value — V20's inference was not materially fragile to it. Ridge does change
beta's *direction*, so it is not irrelevant, but the requirement is about
well-posedness, not about repairing an inferential threat.

The widened range and the STOP rule must be frozen before the grid is run.

---

## 4. QC methodology — the arc's conclusions, as design

### 4.1 What carries rejection authority

| tier | instrument | authority |
| --- | --- | --- |
| 1 | cross-cell association with technical variables | **warning only, never rejects** |
| 2 | **same-cell measurement intervention** — thin molecules, hold cell identity fixed, ask whether the conclusion moves | **qualification authority** |
| 3 | independent held-out biology on prospectively separated genes | corroboration |

The V20 QC veto belongs to tier 1 and was used as a rejection rule. Steps 1–4
established why that is too coarse: association is weaker than artefact, the two
gate metrics are 0.92 collinear and substitute for each other in the statistic
(null argmax 476/523), and the frozen statistic is **not monotone under support
restriction** — restricting to common support *raised* it from 0.2947 to 0.3228
because the standardiser shrank faster than the numerator. A gate with that
property cannot certify that a confound has been addressed.

### 4.2 QC balancing is a sensitivity analysis, not a gate

Weighting and matching are demoted. Step 4 showed 1:1 matching removes the
imbalance (SMD reduction 92–94% on a fixed denominator) and simultaneously
destroys the power to see the signal — the matched coherence landed **inside** the
confound-retaining control range. Balancing may be reported as a sensitivity
analysis with its ESS stated; it may not adjudicate.

If a balancing method is used at all, weighting is preferred over matching
because it reselects cells rather than subtracting a fitted QC effect from
expression, and residualising a score on QC can subtract biology whenever
biological state genuinely alters transcript complexity.

### 4.3 Power calibration is an admission requirement

**No gate may reject anything until it has demonstrated, on a confound-retaining
or signal-injected control at the sample size the gate itself creates, that it
can detect an effect of the magnitude it is being asked to adjudicate.**

This is step 4's lesson generalised: a gate that removes a confound can
simultaneously go blind, and that failure presents as a clean pass. Without
calibration, "no longer correlates with the technical variable" and "can no
longer see anything" are the same number.

### 4.4 Balance measures must use a fixed denominator

Any pre/post balance table must standardise both sides by the **pre-intervention
denominator**. The frozen `_donor_delta` restandardises on whatever subset it is
handed, which makes a pre/post pair incomparable and produced exactly the
artefact in §4.1.

---

## 5. Donor-level inference and recurrence

- Inference remains **donor-level**. Cells are not independent units.
- **Donor-level recurrence** is required for any rare-biology claim: the
  direction must be present in a pre-declared majority of donors, evaluated by
  the frozen exact sign-flip test or its stated successor, not by a cohort
  average that a few donors could carry.
- Per-donor contributions must be published, and any statistic whose value could
  be dominated by the donors with the least data must report the relationship
  between per-donor contribution and per-donor cell count. (Step 1 did this and
  the concern did not materialise there — correlation +0.101 — but the check
  should be standing rather than ad hoc.)

---

## 6. Data hygiene

1. **All method and estimator choices use discovery or calibration data only.**
   No V21 machinery may be selected using confirmation cells, confirmation
   labels, confirmation QC structure or any AT8 value.
2. **A fresh confirmation set is used if §0.1 permits it.** Otherwise §1.3's
   degraded status applies and is stated in the result.
3. **Single-shot.** One frozen pass. No re-selection after seeing any
   confirmation quantity, and no V22 tolerance or threshold expansion in
   response to a V21 result without a separate owner decision on independent
   evidence.
4. **Steps 1–4 are not retracted.** They remain published diagnostics of V20 and
   the source of §4. What changes is that they may not serve as a selection
   criterion for machinery tested on the same donors.

---

## 7. Provenance requirements, from the V20 failures

Each of these fixes something that actually cost time in V20:

1. **Record the numeric environment** in every run record — Python, NumPy,
   SciPy, BLAS implementation and thread count, SIMD. V20 recorded none, and its
   bit-exact verifier then could not be satisfied on any available stack.
2. **Record resolved input paths alongside digests.** Digest-only binding meant
   the store had to be guessed; the wrong guess (`expression_level0` instead of
   `expression_level4`) survived four replay steps undetected because nothing
   reads the store until step 5.
3. **Freeze the replay-equivalence policy prospectively**, per field, rather
   than retrofitting one. Bit-exact float equality across stacks is
   unsatisfiable; the V2 policy's structure — exact for discrete and structural
   quantities, field-specific budgets for characterised drift, dtype equality as
   a precondition — is the working template.
4. **Publish the computation with the evidence.** V20's frozen modules and input
   authorities lived only in a session scratchpad and were one cleanup from
   unrecoverable.
5. **Every emitted return path carries the statistics that determined its
   terminal.** Five of eight returns in the frozen adjudicator dropped the state
   sensitivities that had decided the terminal above them.

---

## 8. STOP conditions to be frozen

- ridge optimum on either grid boundary;
- estimator selection not reproducible from discovery data alone;
- any rejection-capable gate without a passing power calibration;
- balance reported without a fixed denominator, or without ESS where weighting
  is used;
- confirmation quantities consulted before the design is frozen;
- a replay that fails the frozen per-field equivalence policy;
- for T2 only: failure of donor-level recurrence.

---

## 9. What V21 may not claim

- Not an independent confirmation of V20 unless §0.1 yields fresh donors.
- No rare-biology qualification on the spent confirmation donors.
- No successor QC gate promoted to rejection authority without §4.3.
- No retrospective reinterpretation of V20's terminals. `T0 V20` stands as
  adjudicated: broad state supported, rare tail underdetermined.

---

## 10. Open items for review

1. §0.1 — the fresh-donor question. Highest value, resolvable pathology-blind,
   and it changes the design. I can scope it on request.
2. §0.2 — whether T2 has any power at 18-donor scale before it is designed.
3. §2.4 — which continuous formulation. I lean to the shape/interaction form
   because it needs no threshold.
4. Whether T1's confirmatory status under §1.3 is acceptable to you, or whether
   you would rather hold T1 until fresh donors exist.
5. Whether the estimator family should include a candidate that models dropout
   explicitly, which I left out as too assumption-heavy for a frozen design.
