# V63 Task 8 — the tournament does **not** qualify the criterion

**Branch** `claude/v63-external-regulatory-qualification-20260929`, from `97dab7fa`.
`TRAINING=OFF`. `TD60=BLOCKED`. Synthetic only; no real measurement read.
Sealed: no parameter came from GSE173316, Morabito, the NIH-CARD object or any
real target overlap, and `assert_sealed()` runs at start-up.

**Verdict: `gate_may_proceed = false`, on `FAIL__TECH`.** Under the stop rule —
*if Task 8 cannot reject the identifiable synthetic nuisances, we stop there* —
this is a stop, not a near miss to be argued past.

---

## A. REPRESENTED_NUISANCE_SPECIFICITY

donors=18, seeds=24, one-sided LCB95 bootstrapped over seeds (the independent
unit; leave-one-donor-out folds are averaged within seed first).

| family | arms | margin | **LCB95** | M_MIN 0.010 | 0.005 | 0.020 |
|---|---|---|---|---|---|---|
| NULL | NEG_NULL_0 | +0.03230 | **+0.03184** | PASS | PASS | PASS |
| **TECH** | NEG_TECH_1, **NEG_TECH_2** | +0.00932 | **+0.00768** | **FAIL** | PASS | FAIL |
| GEO | NEG_GEO_1 | +0.01482 | +0.01349 | PASS | PASS | FAIL |
| ACC | NEG_ACC_1 | +0.02638 | +0.02418 | PASS | PASS | PASS |
| ANCHOR | NEG_ANCHOR_1 | +0.01960 | +0.01852 | PASS | PASS | FAIL |
| DONOR | NEG_DONOR_1 | +0.03176 | +0.03098 | PASS | PASS | PASS |
| *held-out* | NEG_HELDOUT_1 (ambient) | +0.03145 | +0.02987 | *generalises* | | |

**The binding arm is NEG_TECH_2** — the latent capture factor correlated with
the target, median +0.02314 against a positive floor set by POS_BIO_2. Every
other represented family clears the predeclared margin comfortably.

**This is exactly what v1 hid.** v1 compared the positive floor against a single
pooled negative ceiling; the pooled number looked healthy while TECH sat
unrejected underneath it. Requiring the margin per family is what surfaced it.

Note the 0.020 column: at a stricter threshold **three** families fail. The
criterion is not comfortably clear of its nuisance class anywhere above 0.010.

## B. IDENTIFIABILITY_BOUNDARY

`NEG_SEMANTIC_TWIN` median **+0.22976**, `POS_BIO_1` median **+0.22976**,
identical to zero tolerance across all seeds.

Classification **`NON_IDENTIFIABLE_BY_DESIGN`. Not a gate failure.** The twin's
permitted observables *are* the positive's; equality is the correct result and a
difference would indicate leakage, not success. This is the empirical
identifiability ceiling: worlds inside it need an **external measurement**, not a
cleverer statistic. V48 established this for the RNA-only case, and V58/V59
repeated the lesson when an anchor-keyed twin passed an external-anchor
benchmark perfectly.

---

## The common-support finding, and it is not good news

The question was whether the attrition is *statistical cost* or a *changed
estimand*. It is a changed estimand.

**146 of 960 linked pairs retained — 15.2%. 145 of 4,704 strata usable.**

| variable | SMD (retained − discarded) | |
|---|---|---|
| **log10 distance** | **+0.346** | **MATERIAL** |
| distal accessibility | −0.229 | modest |
| promoter degree | +0.142 | modest |
| RE density | +0.119 | modest |
| anchor frequency | −0.119 | modest |
| promoter activity | −0.017 | negligible |

Retained linked pairs are systematically **longer-range and less accessible**
than the ones trimmed away. At |SMD| 0.346 on distance this is past the
conventional 0.25 "material" line, so matching has not merely cost power — it
has selected a different slice of the linked population.

**Consequence for claim scope:** any qualification obtained under this matching
speaks for the *retained* population — longer-range, lower-accessibility linked
pairs — and not for externally linked pairs in general. That sentence has to
travel with the result.

Attrition got worse than v1's 41% because anchor frequency was added as a
matching variable. That addition was necessary: without it, NEG_ANCHOR_1 would
have been rejected by the matching rather than by the statistic, which is a free
win and not a test. The cost is real and is reported rather than tuned away.

---

## Anti-false-green controls — including where they were weak

**1. Common random numbers** — verified, not assumed. The arm-independent donor
QC draw is identical across arms for the same seed and donor, so family
comparisons are paired.

**2. Mutation controls** — one strong, two weak, reported honestly:

| mutation | effect |
|---|---|
| `no_control_matching` | **strongly red** — TECH −0.201, GEO −0.149, ACC −0.086, DONOR −0.328, ANCHOR fail, detectability FAIL, ordering broken. Negatives score *above* positives. |
| `no_qc_residualization` | **weak** — only TECH degrades (+0.00768 → +0.00490), and TECH already failed. Everything else still passes. |
| `pooled_scoring` | **weak** — only TECH fails; DONOR still passes at +0.02920. |

**3. Positive-control detectability** — LCB95 +0.03184 above the clean null, and
the ordering POS_BIO_1 > POS_BIO_2 > all negatives holds. A scorer that rejected
everything could not have passed this.

**4. Held-out nuisance family** — ambient cross-talk, a mechanism not used while
designing the score, **generalises** (LCB95 +0.02987). Reported, not used to
retune: retuning against a held-out family would convert a generalisation test
into a memorisation test.

---

## Self-audit

**S-V63-4 — a mutation control that barely mutates.** `no_qc_residualization`
moves only the TECH family, which had already failed. As a control it therefore
demonstrates very little: it cannot show the suite going red because the only
thing it touches was red already. A useful mutation must be able to flip a
family that currently passes.

**S-V63-5 — I did not demonstrate what I claimed the donor axis does.** I built
`NEG_DONOR_1` as a shared factor whose loading *sign* alternates by donor, and
asserted that pooled scoring would be fooled while donor-held-out scoring would
not. It isn't: under `pooled_scoring` the DONOR family still passes at +0.02920,
because sign-alternating loadings cancel when metacells are concatenated too.
So the rejection of `NEG_DONOR_1` is being done by the **matched-control
subtraction**, not demonstrably by donor-held-out scoring, and the donor axis of
this tournament is **untested**. A construction that would actually test it is a
donor-structured latent with a *consistent sign and varying magnitude*, which
pooling would amplify rather than cancel. I am recording this rather than
quietly rebuilding the arm, because changing a negative's construction after
seeing that it passes too easily is how a benchmark gets tuned into agreement.

**What this means for the authority statement.** The proposed
`QUALIFIED_WITHIN_REPRESENTED_AND_BOUNDED_HIDDEN_QUALITY_REGIME` is **not
reachable at the predeclared M_MIN = 0.010**. It would be reachable only at the
0.005 sensitivity arm, and lowering the threshold after seeing that 0.010 failed
is precisely the move the project's own rule forbids. The honest status is:

> **`NOT_QUALIFIED__TECH_FAMILY_UNREJECTED_AT_PREDECLARED_MARGIN`**

with two riders: the donor axis is untested (S-V63-5), and any future
qualification will speak for the retained 15.2% of linked pairs, which differ
materially in distance from those trimmed.

---

# v2.1 — strengthened arm and control (step 1 of the repair plan)

Two changes, both strictly hardening, made before any estimator was touched.
M_MIN, the scoring rule, the confidence construction and every other arm are
unchanged. v2 is preserved so its committed results stay reproducible.

## The primary result did not move: still `FAIL__TECH`

| family | v2 LCB95 | **v2.1 LCB95** | |
|---|---|---|---|
| NULL | +0.03184 | +0.03184 | identical |
| **TECH** | +0.00768 | **+0.00768** | **identical — still FAIL** |
| GEO | +0.01349 | +0.01349 | identical |
| ACC | +0.02418 | +0.02418 | identical |
| ANCHOR | +0.01852 | +0.01852 | identical |
| DONOR | +0.03098 | +0.03159 | changed, as intended |

Every family except DONOR is **bit-identical** across the two versions. That is
the common-random-numbers design proving itself: revising one arm perturbed only
that arm. It also means the TECH failure is not a sampling artifact.

## S-V63-4 — CLOSED. The new mutation is strong.

`no_anchor_matching` drops anchor frequency from the matching key:

| | v2.1 primary | `no_anchor_matching` |
|---|---|---|
| ANCHOR | +0.01960 (PASS) | **−0.08186 (FAIL)**, LCB −0.08620 |
| detectability | PASS | **FAIL** |
| ordering POS1>POS2>negatives | holds | **broken** |
| common support | 15.2% | 46.8% |

A passing family flipped hard to failing, and the positive ordering broke. This
is the demonstration v2's mutations could not give.

## …and it exposed a trap worth naming

Under `no_anchor_matching`, **TECH PASSES** at +0.01147 / LCB +0.01056 — above
M_MIN. Dropping a matching variable retains 46.8% of linked pairs instead of
15.2%, which shifts the positive floor enough to clear the threshold.

So there exists a change that "fixes" the TECH failure, and it fixes it by
**destroying the ANCHOR family** — which a single pooled negative ceiling might
well have absorbed without complaint. This is the clearest possible argument for
per-family margins: the pooled criterion is fixable in a way that is
scientifically worthless, and the per-family criterion refuses it.

**Recorded as a prohibited move.** Relaxing the matching to recover TECH is not
available.

## S-V63-5 — refined, not closed, and I am stopping here

The rebuilt `NEG_DONOR_1` (consistent sign, donor-varying magnitude) still does
not expose pooled scoring: under `--mutate pooled_scoring` the DONOR family
passes at +0.02939. Two constructions have now failed to make the donor axis
bite, and the reason is structural rather than a defect in either:

> A donor-level latent that acts **uniformly across pairs** is removed by the
> MATCHED-CONTROL SUBTRACTION, because it shifts linked and control pairs
> equally and cancels in the difference — whether or not donors are pooled.

To make donor-held-out scoring load-bearing, the latent would need pair-specific
structure correlated with linked status — at which point it is a geometry or
anchor confound wearing a donor label, and those families are already
represented and already rejected.

**Honest status: donor-held-out scoring is NOT demonstrated to be load-bearing
for this nuisance class.** It may still matter for donor-specific *pair-level*
effects, which this tournament does not represent. I am stopping after two
attempts rather than continuing to reshape a negative until it behaves the way
I predicted — that is the path by which a benchmark gets tuned into agreement,
and I said so before running.

## Where this leaves the plan

Step 1 is done. TECH remains unrejected at the predeclared margin, by a margin
whose *point estimate* (+0.00932) is itself below M_MIN, so no amount of extra
seeding closes it. Step 2 — the estimator repair — remains the only legitimate
route, and remains unauthorised.


---

# The bias-support frontier (step 3) -- `NO_FEASIBLE_REGION`

Question fixed before the sweep: *is there any prospective operating region where
TECH is rejected without selecting a materially different subset of regulatory
links?* Feasible region declared before any curve existed: **TECH LCB95 > 0.010
AND worst |SMD| <= 0.25**, retention reported not optimised. Worlds held fixed
across granularities (separate world and matching rngs), so movement along the
curve is caused by matching resolution, not Monte Carlo variability.

donors=18, seeds=24.

| bins | TECH margin / LCB95 | TECH | ANCHOR LCB95 | retention | worst SMD *declared* | *diagnostic* vs-ALL |
|---|---|---|---|---|---|---|
| 2 | -0.07031 / -0.07205 | fail | -0.00480 fail | 93.4% | 0.623 | **0.034** |
| 3 | -0.02335 / -0.02490 | fail | +0.00744 fail | 65.3% | 0.430 | **0.143** |
| 4 | -0.00083 / -0.00185 | fail | +0.01431 CLEAR | 36.9% | 0.371 | **0.221** |
| 5 | +0.00943 / +0.00785 | fail | +0.01839 CLEAR | 15.2% | 0.346 | **0.288** |
| 6 | +0.01686 / **+0.01384** | **CLEAR** | +0.02116 CLEAR | 4.7% | 0.391 | 0.370 |
| 8 | +0.02109 / **+0.01541** | **CLEAR** | +0.02749 CLEAR | 0.9% | 0.769 | 0.761 |

**Declared criterion: `NO_FEASIBLE_REGION_ON_THIS_FRONTIER`.**

## The mechanism, and a prediction that held

TECH rises **monotonically** with matching resolution -- harder matching does
shrink the residual geometry leak, exactly as first framed. I had pre-registered
that `no_anchor_matching` might mean the opposite, and it does not: **removing a
matching variable and changing granularity are different axes**, and both results
stand. The prediction is recorded as held rather than quietly dropped.

## The measurement defect I flagged was real -- and immaterial

The declared statistic is retained-vs-discarded, which is degenerate at extreme
retention: at 93.4% retention the discarded 6.6% is a small extreme tail, so
SMD 0.623 says nothing about whether the estimand moved. The estimand-relevant
contrast is retained-vs-**all linked**, added as a labelled diagnostic and never
used in the feasibility flag.

**It does not rescue the conclusion.** Under the diagnostic contrast the two
conditions still never overlap:

- representative under vs-ALL (bins 2, 3, 4 -> 0.034, 0.143, 0.221) -> **TECH
  fails, and at bins 4 its margin is NEGATIVE (-0.00185), not merely short**
- TECH clears (bins 6, 8 -> +0.01384, +0.01541) -> vs-ALL 0.370 and 0.761,
  materially selected
- bins 5 sits between and fails both

The conditions cross in opposite directions across bins 4->6 with **no point of
overlap under either contrast**. So the flagged defect changed how one column
should be read; it changed nothing about the answer. Reported that way rather
than as a crisis averted.

## What this licenses, stated no more strongly than earned

> **`NEG_TECH_2 = EMPIRICALLY_UNRESOLVED_WITHIN_CURRENT_OBSERVABLE_AND_ESTIMATOR_CLASS`**

Deliberately **weaker** than the semantic twin's status. The twin is
*mathematically* non-identifiable: its observables are identical to the
positive's, which is a theorem about the observables. This is an *empirical*
statement about one observable set and one class of support adjustment
(coarsened exact matching at six granularities). It does **not** license
demanding another assay, because the same-observable degeneracy has not been
demonstrated -- only that this estimator class fails to resolve it.

## The fork, and which branch this selects

1. feasible region exists -> narrow estimator work -- **ruled out by this sweep**
2. no feasible region, identifiability not proven impossible -> **ONE
   prospectively specified orthogonalised/continuous-adjustment estimator, not a
   tournament** -- **this is the indicated branch**
3. no feasible region AND same-observable degeneracy demonstrated -> elevate
   hidden capture into the identifiability boundary and require an independent
   measurement -- **not yet earned**

Branch 2 is indicated because the failure has an obvious candidate mechanism:
coarsened *binning* balances geometry only to within a bin, and the latent is
keyed to geometry continuously. A continuous adjustment does not have to trade
balance against retention the way binning does, so it is the one change that
could move both conditions in the same direction rather than along the frontier.

That is a single, prospectively specified estimator -- not a search -- and it
remains unauthorised.
