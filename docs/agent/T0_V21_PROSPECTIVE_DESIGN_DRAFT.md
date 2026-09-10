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

**Therefore, frozen as a gate:** `reader_validation` is opened only when a
frozen V21 design demonstrates **≥ 80% power at α = 0.025 on 12 donors**,
computed discovery-only and pathology-blind, against a pre-declared effect size
that is *not* V20's point estimate but a winner's-curse-adjusted lower bound.

If the gate fails, the correct action is not to open the partition and hope.
Options, in the order I would consider them:

1. **Hold `reader_validation` sealed** and let V21's contribution be the
   methodology — detection-invariant estimator, power-calibrated gates,
   provenance closure — validated on discovery with the spent 18 as internal
   sensitivity. Costs nothing irreversible.
2. **A second brain region as the replication cohort.** The audit incidentally
   showed the unused donors carry substantial cells outside MTG — PFC A9
   367,252, MEC 256,071, caudate 194,624, V1C 145,172, STG 127,294. A second
   region would be a *generalization* test rather than a replication, since the
   biology differs, but it could be adequately sized, which 12 MTG donors are
   not. This is likely the higher-value engineering investment.
3. **Reduce the nuisance cost.** At n = 12, `p_full = 5` spends 42% of the data
   on nuisance. A leaner design would recover df — but it must be justified
   prospectively on design grounds, never chosen for power, and the gain is
   small: dropping age² raises 12-donor power only to about 0.30.

My recommendation is 1, with 2 scoped in parallel. The owner's hierarchy is the
right structure; I would simply not spend its third tier until there is a test
it can power.

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

One design question the hierarchy raises, flagged rather than decided: **should
V21's discovery target fit use 28 donors or 28 + 18 = 46?** Using 46 nearly
doubles the fitting cohort and is legitimate, since the fresh 12 remain
untouched and a better-fit target is a better instrument rather than a biased
one. Against it: V20's frozen target was fit on 28, so refitting on 46 makes
V21 a different object and muddies the comparison, and it blurs the 18's
internal-sensitivity role. I lean to **fit on 28** and keep the three-way
separation clean, but the power cost is real and it is the owner's call.

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

**Step 3 — test functional stability across the near-optimal set**, all
pathology-blind on discovery:

- β **direction** agreement — cosine between the β vectors of the extreme
  members of the near-optimal set;
- **cell-score geometry** — rank correlation of per-cell scores;
- **donor summaries** — correlation and maximum absolute difference of the
  per-donor score used downstream.

**Step 4 — decide.**

- If the near-optimal solutions are **functionally equivalent**, choose a
  deterministic conservative λ — the **strongest regularisation in the
  near-optimal set** — and report explicitly that λ itself is weakly identified
  while the estimator is not.
- If they **materially disagree**, `STOP_RIDGE_SELECTION_NOT_IDENTIFIED`.

The agreement bounds for step 3 are numbers, and they must be frozen in review
rather than chosen by me here. They should be expressed as consequences where
possible — for instance, whether the donor summaries agree closely enough that
any downstream terminal would be unchanged across the near-optimal set — because
a consequence-based bound is much harder to game than a bare correlation
threshold.

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
- for T2 only: failure of donor-level recurrence.

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

## 11. Open items for review

1. §0.1 — **answered and decided.** `reader_validation` approved,
   `reader_oracle` sealed.
2. **§0.3 — the one I would most like a decision on.** 12-donor T1 power is
   about 0.27 at α = 0.025, and lower after winner's curse. I recommend holding
   `reader_validation` sealed until a design can power it, and scoping a second
   brain region in parallel as the adequately-sized replication cohort.
2. §0.2 — whether T2 has any power at 18-donor scale before it is designed.
3. §2.4 — which continuous formulation. I lean to the shape/interaction form
   because it needs no threshold.
4. Whether T1's confirmatory status under §1.3 is acceptable to you, or whether
   you would rather hold T1 until fresh donors exist.
5. Whether the estimator family should include a candidate that models dropout
   explicitly, which I left out as too assumption-heavy for a frozen design.
6. §3.3 — the functional-agreement bounds for β direction, cell-score geometry
   and donor summaries. Expressed as consequences where possible. The 2-decade
   figure survives only as a *flag*, per the owner's correction.
7. §1.3 — whether V21's discovery target fit uses 28 donors or 28 + 18 = 46. I
   lean to 28 for a clean separation; 46 is defensible and more powerful.
