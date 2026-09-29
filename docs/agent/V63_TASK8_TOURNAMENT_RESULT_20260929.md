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
