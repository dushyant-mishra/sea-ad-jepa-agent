# T0 V21 prospective design — DRAFT FOR REVIEW, NOT FROZEN

**Status: `DRAFT_FOR_REVIEW_NOT_FROZEN`.** Nothing here is authority. V21 must
not execute until this is reviewed, amended and frozen. V20 is unchanged,
`training_authorized: false`, and steps 1–4 stand as published.

This draft exists because the V20 diagnostic arc established what a successor
has to fix, and because the confirmation donors have now informed method
development and can no longer silently be used to choose V21 machinery.

---

## 0. Blocking questions, and the gate that must precede opening the partition

These must be resolved before freezing, because the design branches on them.

### 0.1 Is a fresh confirmation set available? — **AUDITED, answer below**

Resolved by `scripts/v4/t0_v21_fresh_donor_audit_v1.py`, pathology-blind
(availability flag only; the pathology CSV is never opened). Record:
`outputs/t0_v21_fresh_donor_audit_20260910/`.

Verdict: **`FRESH_DONORS_EXIST_BUT_ONLY_IN_FIREWALL_CLOSED_PARTITIONS__OWNER_GATE_NEW_POPULATION_AUTHORITY_AND_STORE_BUILD_REQUIRED`**

| quantity | value |
| --- | ---: |
| donors with AT8 available | 84 |
| in the frozen V20 membership | 46 (20,804 cells) |
| unused AT8-available donors | 38 |
| …with any cells anywhere in the atlas | 22 |
| …with MTG immune cells at operator 31 | **22** |
| …satisfying the **full** V20 predicate | **0** |

**Fresh donors do exist.** All 22 fail on exactly one predicate — `partition`.
They are not in another region, not a different operator, and not missing immune
cells. Operator-31 immune donors by partition:

| partition | immune donors | op31 cells (all classes) |
| --- | ---: | ---: |
| `reader_fit` (V20's population) | 46 | 638,150 |
| `reader_validation` | **12** | 173,736 |
| `reader_oracle` | **10** | 121,386 |

The remaining 16 of the 38 have no cells anywhere in the atlas — they are in the
pathology table but not this sequencing cohort.

The frozen predicate reproduced all 46 membership donors' cell counts exactly,
so the audit is querying the authority it references.

#### Three things gate using them, none of which is mine to open

1. **Both partitions are firewall-closed.** `docs/agent/CURRENT_WORK_CHECKPOINT.json`
   declares `reader_validation_closed: true` and `reader_oracle_closed: true`,
   in the same gate class as `pathology_closed` and `sealed_expression_closed`.
   Opening either is an owner decision.
2. **A new V21 population authority is required, not a V20 amendment.** V20's
   closure is defined by a predicate that fixes `partition='reader_fit'`.
   Admitting other partitions changes that predicate, which would mutate a
   frozen authority. V20 must stay immutable, so this is a separate authority by
   construction.
3. **A new expression store build is required.** The materialised Phase2 op31
   store holds exactly 638,150 cells — the `reader_fit` count, confirmed by
   query. The other partitions' cells exist in the canonical metadata source but
   their counts are not materialised anywhere the T0 machinery can read. The
   frozen age/sex authority also covers only the 46 donors and would need
   extension from source.

#### Owner decision, recorded

**Approved: open `reader_validation` only. `reader_oracle` stays sealed.** The
12 validation donors are genuinely fresh for V21 and the engineering cost is
accepted, because it restores a clean confirmatory test instead of arguing about
partially spent donors. Conditions attached by the owner:

- a **new V21 population authority**, never an amendment to V20;
- before any AT8 value is opened: build the validation expression store, extend
  the age/sex authority, rerun identity, completeness and provenance closure,
  and freeze the complete V21 contract;
- the 12 donors take **no part** in estimator selection, ridge selection, QC
  thresholding, power calibration, or any other method choice.

`reader_oracle`'s 10 donors are preserved as the eventual truly final check.

#### Why I originally recommended this, retained for the record

**Open `reader_validation` only, and leave `reader_oracle` closed.** That yields
**12 fresh donors** — at the bottom of the 12–15 range this draft set for a
viable independent confirmation set, so it is feasible but not comfortable. And
it preserves `reader_oracle` as a genuinely untouched final oracle, which is
worth more than ten extra confirmation donors: once both are spent there is
nothing left to confirm anything against.

The cost is real and should be weighed openly: a new population authority, a new
op31 store build for the validation partition, an extended age/sex authority,
and a fresh technical-completeness pass. That is a data-engineering project, not
a configuration change.

If that cost is not worth paying now, §1.3's degraded status applies and V21
must describe itself accordingly. Either way the design below is unchanged; only
the confirmatory status of T1 and T2 depends on this choice.

### 0.2 Does the rare-biology estimand have any power at this cohort size?

Step 4 showed the obvious remedy (1:1 matching) is underpowered. Before V21
commits to a rare-biology arm at all, a **power calibration on discovery donors
only** should establish what effect size the proposed continuous statistic can
detect at 18-donor scale. If the answer is "nothing smaller than the effect we
already failed to establish", the arm should be dropped rather than reformulated.

### 0.3 A power gate must precede opening the partition — **new, and I would not skip it**

The owner's structural calls are right and are adopted below. But the
arithmetic says the *sequencing* matters more than the structure, and this is
the one place I would push back on doing it now.

**A 12-donor T1 test has about 27% power at the frozen α = 0.025.** Projecting
V20's observed effect, with `p_full = 5` so residual df = n − 5:

| n | residual df | expected t | one-sided p | power at α = 0.025 |
| ---: | ---: | ---: | ---: | ---: |
| **12** | 7 | 1.558 | 0.082 | **0.271** |
| 18 (V20) | 13 | 1.908 | 0.039 | 0.423 |
| 24 | 19 | 2.203 | 0.020 | 0.552 |
| 30 | 25 | 2.463 | 0.011 | 0.658 |
| 46 | 41 | 3.050 | 0.002 | 0.846 |

For 80% power at n = 12 the test would need t = 3.27, a **2.1× improvement in
standardized effect**. Removing detection noise is unlikely to deliver that.

And it is worse than the table suggests. V20 itself ran at 42% power, so
conditional on having observed p = 0.021 there, the effect estimate is likely
**inflated by winner's curse**. The true effect is probably smaller, which
pushes 12-donor power below 27%.

So the expected outcome of opening `reader_validation` for T1 now is an
**uninformative null** — one that would not disconfirm V20, because the design
could not have detected the effect, but that would permanently consume the only
fresh cohort. Spending an irreplaceable resource on a test that is more likely
than not to answer nothing is the single irreversible move available here.

**Owner decision: HOLD `reader_validation`. The 12 fresh donors are not to be
spent at ~27% power.** The power gate is required first.

**Frozen as a gate:** `reader_validation` is opened only when a frozen V21
design demonstrates **≥ 80% power at α = 0.025 on 12 donors**, computed
discovery-only and pathology-blind, against a pre-declared effect size that is
*not* V20's point estimate but a winner's-curse-adjusted lower bound.

#### The gate's evidence base — corrected, because the target fit is AT8-supervised

An earlier draft said the gate should be evaluated *after* the 46-donor refit
while also being discovery-only. Those are incompatible, and checking the frozen
code shows why. `fit_discovery_target_v2` requires donor metadata whose schema is
exactly `['donor_id','AT8','age','sex']` and sets `y = pd.to_numeric(dm.AT8)`;
the LOODO ridge grid then selects λ by predictive loss on that `y`. **The target
β is fit by supervised regression on AT8.** A 46-donor refit therefore consumes
all 46 donors' AT8, including the 18 whose outcomes V20 already adjudicated.

The consequence runs deeper than the wording. An effect estimate used to project
power must come from donors that were **not** in the fit, or it is in-sample and
optimistic — which is the wrong direction for a gate whose purpose is to prevent
an underpowered test. V20's `t = 1.908` is usable precisely because it was
out-of-fit: β was fit on 28 and evaluated on a disjoint 18. **Once the estimator
is refit on all 46, no donor with known AT8 remains out-of-fit at all**, so no
honest out-of-sample effect estimate exists for that estimator without spending
the fresh 12 — which is the thing the gate exists to protect.

**Redesign, frozen:**

1. **The power gate's effect evidence comes from the 28 discovery donors only,
   by cross-fitting within them.** Outer folds over the 28; in each fold β is fit
   on the training donors with its own inner LOODO ridge selection, and the
   donor-level HC3 statistic is evaluated on the held-out donors. The aggregate
   out-of-fold statistic is the effect estimate.
2. **The 18 spent donors' AT8 outcomes do not enter the power calculation at
   all.** They may be used later to refit the frozen estimator; they may not be
   used to decide whether the fresh 12 are worth spending.
3. **The 46-donor refit is adopted as the final instrument but is credited with
   no additional power in the gate.** More fitting donors should sharpen β, but
   that expectation cannot be verified without spending outcomes, so it is not
   banked. The projection stands on the 28-fit evidence and the actual test
   should, if anything, be better powered than projected.

This also supplies the winner's-curse adjustment the gate requires, rather than
leaving it to a chosen shrinkage constant. A cross-fitted out-of-fold estimate is
not conditioned on having reached significance, so it is not inflated the way a
single realised `t` selected for publication is. **That derivation replaces the
illustrative 0.75 shrinkage entirely.** Note it is conservative twice over: each
fold trains on fewer than 28 donors, so the cross-fitted effect understates what a
28-donor fit achieves, and understates a 46-donor fit by more.

If the gate fails, the correct action is not to open the partition and hope.
Options, in the order I would consider them:

1. **Hold `reader_validation` sealed** and let V21's contribution be the
   methodology — detection-invariant estimator, power-calibrated gates,
   provenance closure — validated on discovery with the spent 18 as internal
   sensitivity. Costs nothing irreversible.
2. **A second brain region — scoped, and it does not solve the power problem.**
   See §11. Other regions have large, well-powered `reader_fit` cohorts, but
   every one of them is a strict subset of the same 46 MTG donors: **zero fresh
   donors.** A second region is a within-donor cross-region generalisation test,
   not an independent confirmation cohort. Worth doing on its own merits;
   useless for this gate.
3. **Reduce the nuisance cost.** At n = 12, `p_full = 5` spends 42% of the data
   on nuisance. A leaner design would recover df — but it must be justified
   prospectively on design grounds, never chosen for power, and the gain is
   small: dropping age² raises 12-donor power only to about 0.30.

**Recommendation, revised after scoping: option 1.** Option 2 was my
suggestion and the scoping refuted it — it adds predictors, not donors. Since
donor count is what drives power for donor-level inference, no combination of
regions raises 12-donor power. The routes that remain are a materially better
estimator (§2) or a different claim type. The owner's hierarchy is the right
structure; its third tier simply must not be spent until there is a test it can
power.

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

**Status: exploratory and non-qualifying in V21, even with the fresh 12.** Owner
decision, and the reasoning is sound on two independent grounds: the estimand is
being reformulated, and its power is unresolved (§0.2). Reserving the fresh
cohort for a target that is still being defined would spend it badly.

### 1.3 The donor hierarchy — four tiers, owner-approved

This replaces the earlier "degraded confirmatory status" fallback entirely. T1
no longer leans on it, because fresh donors are demonstrably available.

| tier | donors | role | may inform method choices? |
| --- | ---: | --- | :---: |
| discovery | 28 | target fit, estimator selection, ridge selection, QC thresholds, power calibration | **yes** |
| spent historical validation | 18 | internal sensitivity and the published steps 1–4 diagnostics | **no** — already spent |
| **fresh V21 confirmation** | **12** | one single-shot confirmatory test of T1 | **no** — must stay untouched |
| final oracle | 10 | reserved, sealed | **no** |

Consequences, stated so they cannot drift:

- **T1's confirmatory evaluation is held** until the 12 are materialised, the
  V21 procedure is completely frozen, and §0.3's power gate passes. It is then
  run **once** on those 12.
- **The previous 18 are no longer V21 confirmation.** They become
  spent/internal-sensitivity donors. Any V21 number computed on them is labelled
  internal sensitivity, never confirmation.
- **`reader_oracle`'s 10 stay sealed** for the eventual final check. Once both
  fresh tiers are spent there is nothing left to confirm anything against, which
  is why the oracle is worth more than ten extra confirmation donors.

#### Owner decision: select on 28, refit the frozen estimator on 46

Better than either option I offered, and it resolves the tension rather than
trading one side against the other:

1. **All method and ridge selection on the 28 discovery donors.** Estimator
   family, selection criteria, ridge bracketing, QC thresholds and power
   calibration — everything that involves a choice.
2. **Then freeze the estimator completely.**
3. **Then refit that frozen estimator on all 46 development donors** — the 28
   plus the 18 spent ones.
4. **Then the single test on the fresh 12.**

Why this is right. Selection on 28 keeps every choice clean. The refit on 46
uses the 18's data as what it now is — development data — without pretending
they are validation. And the fresh 12 stay disjoint from all 46 by construction,
since they are in a different partition entirely, so the test set is untouched
no matter how the instrument was fitted.

Two consequences to record. V21's target is a **different object** from V20's,
which was fit on 28, so V21's T1 is not a replication of V20's exact target and
must not be described as one. And nearly doubling the fitting cohort should
sharpen β, which is the legitimate way to move §0.3's power gate — improve the
instrument, never the threshold.

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

## 3. Ridge search — a frozen deterministic bracketing procedure

**Not a wider fixed grid.** A wider grid is the same mistake at a larger scale:
it can still terminate on an endpoint, and its width would be chosen by
guesswork. V21 freezes a *procedure* that searches until the optimum is interior
or refuses.

Everything below is evaluated by LOODO cross-validation on **discovery donors
only**, exactly as V20 did. Confirmation never sees the search.

### 3.1 The procedure

Let `e` be the multiplier exponent, `λ = 10^e · trace_scale`.

**Stage A — bracket.** Evaluate a frozen coarse anchor set
`e ∈ {−8, −4, 0, +4, +8}`. Chosen for span rather than resolution; the anchor is
frozen so it cannot be retuned.

**Stage B — expand.** While the minimum CV MSE sits at either end of the current
bracket, extend that end by a frozen step of `4` in exponent and re-evaluate. At
most **3** expansions per side, bounding the search at `e ∈ [−20, +20]`.

**Stage C — refine.** Once the minimum is strictly interior, halve the step
around it — `4 → 2 → 1 → 0.5 → 0.25` — for a frozen **4** refinement rounds,
requiring the minimum to remain interior at each round.

**Stage D — accept or STOP.** Accept only if the final minimum is strictly
interior to its refinement interval. The frozen V20 tie rule is reused verbatim
for equal-loss exponents; it is not redefined here.

### 3.2 STOP conditions, frozen in advance

- the minimum is still at a bracket endpoint after the maximum expansions —
  the design is misspecified, not merely under-searched;
- the refined minimum lands on a refinement-interval endpoint;
- the search does not terminate within the frozen expansion and refinement
  budgets;
- **the CV surface is not decisive** (see §3.3).

### 3.3 Interiority is necessary but not sufficient — near-optimal set and functional stability

**The owner's formulation replaces mine, and it is strictly better.** I had
proposed rejecting when the near-optimal plateau spans more than a frozen number
of decades. That measures the wrong thing. A flat CV surface means **λ** is
poorly identified; it does not follow that the **estimator** is poorly
identified. λ can move a hundredfold while β's direction, the per-cell score
geometry and the donor summaries barely change — in which case the fit is fine
and only the λ label is uncertain. Conversely a narrow λ range can produce
materially different β directions, which a width test would pass. A horizontal
width cutoff is also easy to game by rescaling the grid.

So rejection authority moves to functional consequence:

**Step 1 — define the near-optimal set prospectively, by uncertainty not by
equality.** Use a one-standard-error-type rule on **paired donor-level LOODO
differences**: because the same donors are held out at every λ, the standard
error of the *difference* in CV loss between two λ values is the correct scale,
and it is far tighter than an unpaired comparison. The near-optimal set is every
λ whose paired difference from the minimum is within one standard error of zero.

**Step 2 — publish its width in decades.** If it spans more than 2 decades,
flag `RIDGE_CV_SURFACE_FLAT`. **This is a flag, not a rejection.**

**Step 3 — build the reference envelope from donor resampling, not from a
chosen number.** Owner decision, and it removes the last arbitrary constant from
this section. Fix λ at the near-optimal minimum and refit under
leave-one-discovery-donor-out — 28 refits, deterministic, no RNG, and the
machinery already exists because LOODO is what computes the CV surface. For each
refit measure the displacement of

- β **direction** — cosine against the full-discovery-set β;
- **cell-score geometry** — rank correlation of per-cell scores;
- **donor summaries** — correlation and maximum absolute difference of the
  per-donor score used downstream.

The spread of those 28 displacements is the **normal variability of the
estimator under donor resampling** — the uncertainty the analysis already
accepts as unavoidable.

**Step 4 — compare λ-induced displacement against that envelope, and decide.**
On the full discovery set, measure the same three displacements between the
extreme members of the near-optimal λ set.

**Owner decision: leave-one-donor-out with the maximum displacement, applied
per metric, with no averaging.**

- The envelope is the **maximum** displacement observed across the 28
  leave-one-donor-out refits — not a percentile, which would reintroduce an
  arbitrary constant.
- It is computed and applied **separately for each of the three metrics**. β
  direction, cell-score geometry and donor summaries each get their own envelope
  and their own comparison.
- The λ-induced change must stay inside its own metric's maximum LODO change
  **for all three**. They are never averaged or combined into a single score,
  because averaging would let a large failure on one metric be masked by
  agreement on the others.

- If every metric's λ-induced displacement lies **within** that metric's
  envelope, then choosing λ inside the near-optimal set matters less than which
  donors happened to be sampled. λ is functionally irrelevant at this precision:
  choose the **strongest regularisation in the near-optimal set**,
  deterministically, and report that λ is weakly identified while the estimator
  is not.
- If **any** metric's λ-induced displacement exceeds its envelope,
  `STOP_RIDGE_SELECTION_NOT_IDENTIFIED`.

**No constant is chosen anywhere in this rule.** It is a comparison between two
sources of variation, in the same units, per metric. Leave-one-donor-out is
deterministic and needs no seed, and the refits already exist because LOODO is
what computes the CV surface — so the envelope costs nothing extra to obtain.

### 3.4 What must be published

The complete search trace: every exponent visited, in order, its CV MSE, which
stage requested it, and the decision taken at each step — so the search is
replayable and its determinism checkable. Plus the plateau width, the relative
improvement over the anchors, and the selected exponent with its interiority
margin.

### 3.5 What this fix is and is not

It is a **well-posedness** requirement. V20's optimum landed on the `+2.0`
endpoint, which says the grid was misspecified. Note the split §3.3 introduces:
a flat surface is *flagged*, only functional disagreement *rejects*.

It is **not** a repair of an inferential threat, and V21 should not claim
otherwise. The HC3 t-statistic is invariant to positive rescaling of the
predictor, so a boundary λ barely moves the state p-value — V20's inference was
not materially fragile to it. Ridge does change beta's *direction*, so the
choice is not irrelevant, but the honest framing is that V21 makes the fit
well-posed and its regularisation identified, not that it rescues a result that
was in doubt.

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
- for T2 only: failure of donor-level recurrence;
- `STOP_RIDGE_SELECTION_NOT_IDENTIFIED` — any one of the three metrics' λ-induced
  displacement exceeding its own LODO maximum envelope (§3.3);
- the power gate not clearing 80% at α = 0.025 for 12 donors on the within-28
  cross-fitted effect estimate — in which case `reader_validation` stays sealed
  and V21 ships as a methodology contribution (§0.3);
- any AT8 outcome from the 18 spent donors entering the power calculation;
- the cross-region generalisation study altering T1 after T1 is frozen (§11).

---

## 9. What V21 may not claim

- Not an independent confirmation of V20 unless §0.1 yields fresh donors.
- No rare-biology qualification on the spent confirmation donors.
- No successor QC gate promoted to rejection authority without §4.3.
- No retrospective reinterpretation of V20's terminals. `T0 V20` stands as
  adjudicated: broad state supported, rare tail underdetermined.

---

## 10. The V21 validation-population and store authority — requirements

Sequenced **after** §0.3's power gate, because building it is the expensive step
and the gate decides whether it is worth building. The requirements are recorded
now because they are needed either way, and because they are the same
requirements whichever cohort is eventually used.

All of it is pathology-blind. **No AT8 value is opened at any point in this
section**; only the availability flag, exactly as the audit did.

1. **A new authority, not an amendment.** `T0_V21_VALIDATION_POPULATION_AUTHORITY`
   with its own predicate, fixing `partition='reader_validation'` and otherwise
   identical to V20's — same source, matrix, operator 31, native class Immune.
   V20's authority is not read-modify-written; it is referenced as the sibling it
   differs from in exactly one field, and that difference is asserted in the
   authority itself.
2. **Population closure, independently derived.** Row-count authority, block
   manifest digest and membership bytes for the validation partition, with the
   three-root separation V20 used — population closure, logical row authority,
   physical read plan — each digest-bound.
3. **An op31 expression store for the validation partition.** V20's store holds
   exactly the 638,150 `reader_fit` cells, so this is a new build. It must carry
   its own manifest digest, and the completeness pass must be rerun rather than
   inherited.
4. **Age/sex authority extension**, from the same source, covering the 12
   donors, with the frozen loader's expectation checks applied to the extended
   package rather than bypassed.
5. **Eligibility applied unchanged.** The frozen predicate
   `AT8_available & technical_complete & isfinite(age) & sex.notna() & sex != ''`
   is applied verbatim. The count that survives is a result, not a target — if
   fewer than 12 pass, that is the answer.
6. **No role split.** These 12 are confirmation donors in their entirety. There
   is no discovery/confirmation hash split within them, because they exist to be
   the confirmation tier.
7. **Provenance from the start**, per §7: numeric environment recorded, resolved
   input paths recorded beside digests, per-field replay-equivalence policy
   frozen prospectively, and the computation published with the evidence.
8. **A firewall entry.** Opening `reader_validation` must be recorded as an
   explicit owner-authorised gate change with its scope stated —
   `reader_validation` only, `reader_oracle` untouched — so the checkpoint
   reflects reality rather than the pre-approval state.

**Ordering, frozen:** power gate → population authority → store build →
completeness and provenance closure → freeze the complete V21 contract → and
only then, the single AT8-opening confirmatory run.

## 11. Second-region scoping — done, and it refutes my own suggestion

Owner-approved and run, pathology-blind: `scripts/v4/t0_v21_second_region_scoping_v1.py`,
record `outputs/t0_v21_second_region_scoping_20260910/`. No region selected, no
partition opened, no AT8 value read, nothing fitted.

Ranked by **achievable donor-level power**, never by cell count, because T0
inference is donor-level and a region with millions of cells across eight donors
is worse than one with modest cells across thirty. Donors counted are
AT8-available with at least 80 immune cells, that threshold reused from the
frozen tail support minimum rather than chosen here.

| region (`reader_fit`) | AT8-available donors | usable | median cells/donor | projected power |
| --- | ---: | ---: | ---: | ---: |
| MTG — *V20's population* | 46 | 45 | 386 | 0.837 |
| MEC | 44 | 43 | 647 | 0.820 |
| PFC A9 | 42 | 42 | 499 | 0.810 |
| FI | 27 | 27 | 386 | 0.608 |
| STG | 27 | 27 | 310 | 0.608 |
| HIP | 27 | 26 | 382 | 0.590 |
| ANG / ITG / V1C | 27 | 25 | 226–335 | 0.571 |
| LEC | 22 | 21 | 363 | 0.491 |

At first reading MEC and PFC A9 look like well-powered replication cohorts of
42–44 donors. **They are not, and this refutes the suggestion I made in §0.3.**

| region `reader_fit` cohort | donors | already in the MTG 46 | **new donors** |
| --- | ---: | ---: | ---: |
| MEC | 44 | 44 | **0** |
| PFC A9 | 42 | 42 | **0** |
| FI | 27 | 27 | **0** |
| STG | 27 | 27 | **0** |
| HIP | 27 | 27 | **0** |

**Every other region's cohort is a strict subset of the same 46 donors.** These
are the same people, sampled in different tissue. So:

1. **A second region cannot be an independent confirmation cohort.** All 46 have
   had their AT8 used already — 28 in the discovery fit, 18 in the V20
   adjudication. A second region supplies a new *predictor* against an outcome
   we have already seen.
2. **Adding regions cannot fix the power problem.** Power for donor-level
   inference scales with donors, and no combination of regions adds a donor.
3. **The only fresh donors in the entire atlas remain the 12 `reader_validation`
   and the 10 `reader_oracle`** — and they too are the same 12 and 10 people
   across regions.

What a second region *is* worth, on its own merits: a well-powered **within-donor
cross-region generalisation** test at 42–44 donors — does the immune-state
association hold when the expression comes from different tissue? That is real
science and it is properly sized.

**Owner decision: freeze it as a separate generalisation analysis, kept
secondary.** Conditions, recorded so they cannot drift:

- it is **secondary** to T1 and does not gate it;
- it **must not change T1 after T1 is frozen** — not its estimator, its λ, its
  thresholds, or its interpretation;
- it may **never** be described as independent confirmation, because the outcome
  values are reused for every donor in it;
- it needs its own prospective freeze, with its own population authority per
  region and its own power statement.

#### Owner decision on tissue: MTG remains the primary confirmation tissue

MEC's larger per-donor yield — 797 median immune cells against MTG's 342 — buys
precision, and that is not a sufficient reason to move. **Changing tissue changes
the biological question.** "Does broad immune state in MTG track AT8 pathology"
and "does it in MEC" are different claims, and V20's finding, the frozen target
and the entire diagnostic arc are all MTG. Switching to gain precision would
quietly substitute a different estimand for the one under test.

The MEC cell counts are retained as a fact about the cohort, useful for the
cross-region generalisation study above, and explicitly **not** as a reason to
relocate the confirmation.

One non-obvious finding, retained but now settled. The 12 fresh donors have more
immune cells in MEC (median 797) than in MTG (342), with PFC A9 at 414.
Per-donor precision does not change the donor count, so the power gain would
have been second-order in any case — and per the decision above, it is not a
reason to move the confirmation.

## 12. Decision record

| # | item | status |
| --- | --- | --- |
| 1 | §0.1 fresh donors | **decided** — `reader_validation` approved in principle, `reader_oracle` sealed |
| 2 | §0.3 spend the 12 now? | **decided** — hold; power gate first |
| 3 | §0.3 gate evidence base | **decided** — within-28 cross-fit; the 18's AT8 excluded; no power credit for the 46-refit |
| 4 | §1.3 donor hierarchy | **decided** — 28 select → freeze → refit on 46 → single test on 12 |
| 5 | §2.3 estimator selection criteria | **decided** — thinning robustness **and** held-out biology preservation, jointly, discovery-only, single-shot |
| 6 | §3.1–3.2 ridge search | **decided** — frozen deterministic bracketing with endpoint STOP |
| 7 | §3.3 functional stability | **decided** — LODO maximum displacement, per metric, no averaging, all three must pass |
| 8 | §4 QC gate authority | **decided** — association warns, same-cell intervention qualifies, every rejection-capable gate power-calibrated |
| 9 | §11 cross-region study | **decided** — frozen separately, secondary, never called confirmation, must not change T1 after freeze |
| 10 | §11 confirmation tissue | **decided** — MTG; precision is not a reason to change the question |
| 11 | §2.4 continuous rare-biology statistic | **open** — I lean to the shape/interaction form, which needs no threshold |
| 12 | §2.2 dropout-modelling candidate | **open** — left out as too assumption-heavy; owner's call |
| 13 | §3.3 which LODO refits define the envelope | **open, structural only** — recommend all 28 |

## 13. Freeze readiness

**Not ready to freeze.** Three items must close first, in this order.

1. **Resolve §2.4** — the continuous rare-biology statistic. T2 is exploratory
   either way, but the contract cannot be frozen with an undefined estimand in
   it.
2. **Run the estimator selection** on the 28 discovery donors: the `S0`–`S4`
   family under joint thinning-robustness and held-out-biology criteria,
   single-shot, pathology-blind. This produces the frozen estimator.
3. **Run the power gate** on that frozen estimator, by within-28 cross-fitting.
   This is the decision point. If it clears 80% at α = 0.025 for 12 donors, the
   §10 build sequence begins. If it does not, `reader_validation` stays sealed
   and V21 ships as a methodology contribution validated on development donors.

Only after item 3 returns does the question of opening the partition arise at
all, and §10's ordering applies from there: authority → store build → closure →
freeze → single AT8-opening run.

**What is already frozen-ready:** the donor hierarchy, the ridge procedure and
its stability rule, the QC gate hierarchy and its power-calibration requirement,
the data-hygiene rules, the provenance requirements, the STOP conditions, and
the cross-region study's subordinate status.

**What must not happen before freeze:** no AT8 value opened, no partition
opened, no estimator fitted on anything but the 28, no threshold chosen from a
result, and no V21 execution.
