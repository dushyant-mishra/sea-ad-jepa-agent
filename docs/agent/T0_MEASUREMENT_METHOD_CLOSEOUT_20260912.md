# T0 MEASUREMENT-METHOD CLOSEOUT

Date: 2026-09-12
Terminal: `T0_MEASUREMENT_PROCEDURE_NOT_QUALIFIED_AT_N28__BIOLOGY_UNRESOLVED`
Status: **closed — this measurement contract is not to be modified further**

No pathology value was ever read. All evidence below is synthetic, at the real
T0 geometry. Fresh-12 sealed, reader-oracle sealed, spent-18 excluded, the six
declared pathology columns unread, expression association closed, V20 immutable
at `d5d67e21`, F1 transport open, training OFF, and `NONCONVERGENCE_ALLOWANCE`
unchanged at 0.05 in every file.

This document underwent an adversarial review against its own evidence; the
workflow's independent verification stage did not execute, and the recovered
findings were subsequently adjudicated by the draft's author. §8 records this
limitation.

---

## 1. The frozen interpretation

| statement | verdict |
| --- | --- |
| estimator/model **conditional** behaviour | potentially informative when a proper solution exists |
| end-to-end **n = 28 measurement procedure** | **not qualified** |
| biological common factor | **unresolved, not rejected** |
| T0 endpoint successor | **not lawfully established** |
| reason | insufficient operating characteristics at the actual T0 geometry, dominated by estimator/resampling instability |
| inference that tau biology is absent | **none — not drawn, not supported** |

---

## 2. What was run

Two prospectively frozen synthetic studies, each committed before it produced a
result. Both are entirely at n = 28; **neither varies sample size.**

- **Estimator qualification** — design `a6e88941`, results `c22031f9`.
  24 declared DGP configurations x 3 estimators x 300 replicates, with the
  declared six-indicator / three-residual-edge structure and
  measurement-semantic marginals.
- **Selection operating characteristics** — design `9bb17bda`.
  5 cells x 3 estimators x 40 replicates, each running the actual section 11
  rule including BCa bootstrap intervals with jackknife acceleration
  (B = 150 plus 28 jackknife fits per replicate).

Estimators: ULS on off-diagonals, normal-theory ML, ULS with a declared 0.05
residual-variance floor. `NULL` cells retain all three residual-covariance edges
while removing the common factor — pairwise dependence without a shared
construct.

**Design redundancy, recorded:** the extra arm varies `braak_ceiling`, but MM-C
is fitted on the continuous indicators only, so Braak never enters the fit. Two
of the 24 declared configurations are therefore exact numeric duplicates of two
others. Only 22 distinct DGPs were actually simulated.

---

## 3. Results

### 3.1 End-to-end rates, all three estimators, 40 replicates each

Columns marked **(u)** are unconditional over all 40 replicates. The bootstrap
non-convergence column is marked **(c)** because it is a mean over non-improper
replicates only — a conditional quantity, printed here beside unconditional ones
and labelled rather than blended.

| cell | est | improper (u) | boot non-conv (c) | width gate (u) | M1a (u) | M2a (u) | **PASS (u)** |
| --- | --- | --- | --- | --- | --- | --- | --- |
| STRONG/0.75/0.55 | uls | 0.175 | 0.358 | 0.600 | 0.100 | 0.500 | **0.025** |
| STRONG/0.75/0.55 | ml | 0.300 | 0.547 | 0.625 | 0.000 | 0.575 | **0.000** |
| STRONG/0.75/0.55 | uls_floor | 0.175 | 0.431 | 0.600 | 0.100 | 0.500 | **0.000** |
| STRONG/0.25/0.15 | uls | 0.175 | 0.300 | 0.725 | 0.275 | 0.450 | **0.025** |
| STRONG/0.25/0.15 | ml | 0.300 | 0.467 | 0.575 | 0.075 | 0.475 | **0.000** |
| STRONG/0.25/0.15 | uls_floor | 0.225 | 0.364 | 0.700 | 0.250 | 0.450 | **0.000** |
| MODERATE/0.75/0.55 | uls | 0.325 | 0.458 | 0.450 | 0.025 | 0.425 | **0.000** |
| MODERATE/0.75/0.55 | ml | 0.575 | 0.579 | 0.425 | 0.050 | 0.300 | **0.000** |
| MODERATE/0.75/0.55 | uls_floor | 0.350 | 0.491 | 0.475 | 0.025 | 0.450 | **0.000** |
| WEAK/0.75/0.55 | uls | 0.525 | 0.501 | 0.275 | 0.025 | 0.250 | **0.000** |
| WEAK/0.75/0.55 | ml | 0.675 | 0.637 | 0.150 | 0.000 | 0.075 | **0.000** |
| WEAK/0.75/0.55 | uls_floor | 0.500 | 0.535 | 0.300 | 0.025 | 0.250 | **0.000** |
| NULL/0.75/0.55 | uls | 0.425 | 0.522 | 0.375 | 0.175 | 0.200 | **0.000** |
| NULL/0.75/0.55 | ml | 0.625 | 0.670 | 0.250 | 0.125 | 0.100 | **0.000** |
| NULL/0.75/0.55 | uls_floor | 0.425 | 0.548 | 0.375 | 0.175 | 0.200 | **0.000** |

**False qualification under NULL: 0/40 for all three estimators.
True qualification: 1/40 at best, and only for ULS in the two STRONG cells.**

`ULS+floor` does **not** track ULS on the decision-bearing metric: it qualifies
0/40 everywhere, including both STRONG cells where ULS reaches 0.025. It tracks
ULS on improper rate and width gate, and diverges exactly where it matters.

ML is worse than ULS on improper rate and on bootstrap non-convergence in all
five cells; it is **not** uniformly worse — on the PASS terminal it ties ULS at
0.000 in three of five, and it is marginally better on the width gate in one
(0.625 vs 0.600).

Bootstrap non-convergence runs **0.300 to 0.670 across every cell and estimator**
— six to thirteen times the 0.05 allowance, including under a strong true
construct. This, together with 0 of 72 grid combinations reaching a ≤5% improper
rate, is the basis on which the 5% criterion is called empirically invalid; the
phrase is not carried in from elsewhere.

The terminal distribution is degenerate: 97.5–100% of every cell lands on a
single terminal — `COMMON_FACTOR_NOT_ESTABLISHED` as frozen, or
`MEASUREMENT_ESTIMATOR_NOT_QUALIFIED` once reclassified. `UNRESOLVED`,
`MEASUREMENT_RELIABILITY_UNRESOLVED`, `NO_SUCCESSOR_ENDPOINT_QUALIFIED` and
`MEASUREMENT_MODEL_NOT_ESTIMABLE_AT_N` occur at rate 0.000 in all 15 rows. The
non-convergence criterion preempts every other branch.

A procedure that answers negative to essentially everything has perfect
specificity and no scientific usefulness. It cannot support a biological
negative.

### 3.2 The core rule reduces to the width gate, and the two broken components mask each other

This is the finding that most needs to survive into V5.

Steps 1–5 run independently of the non-convergence gate, so the M1a/M2a columns
of §3.1 show what the **core rule** does before the gate suppresses it. For ULS,
the candidate rate equals the width-gate rate **exactly, in all five cells**
(0.600, 0.725, 0.450, 0.275, 0.375), and for ULS+floor in four of five. Step 1's
admissibility conditions — convergence, loading support, `df ≥ 1` — never reject
anything the width criterion accepts. **The core selection rule is the width
gate.** §3.3's numbers are therefore not independent corroboration; they are the
same measured quantity viewed from the other side.

Reading the core rule against truth:

| cell | truth | core rule qualifies (ULS) |
| --- | --- | --- |
| STRONG/0.75/0.55 | true construct | 0.600 |
| STRONG/0.25/0.15 | true construct | 0.725 |
| MODERATE/0.75/0.55 | true construct | 0.450 |
| WEAK/0.75/0.55 | true construct | 0.275 |
| **NULL/0.75/0.55** | **no construct** | **0.375** |

The core rule qualifies structured-but-factorless data **more often than it
qualifies a genuinely weak construct** (0.375 vs 0.275) and nearly as often as a
moderate one. Its discrimination between NULL and non-strong truth is close to
absent.

**On the M1a/M2a split under NULL.** Under NULL there is no common construct, so
reaching *any* candidate is a false qualification — all 0.375, not just the M1a
half. Which candidate is chosen is a separate question, and choosing M2a is
*correct conditional on qualifying at all*, because the NULL cells do contain
genuine method dependence for step 3's exception to detect. Correct candidate
selection inside a qualification that should never have happened is not
mitigation.

**Consequence, and the reason this contract is closed rather than repaired:**
the 0% false qualification in §3.1 is not a property of the selection rule. It
is produced entirely by the non-convergence criterion suppressing a core rule
that would otherwise false-qualify at roughly 37%. Relaxing or retiring that
criterion without simultaneously adding a level-sensitive qualification
component would convert an inert procedure into an actively misleading one.
Neither change may be made alone.

### 3.3 Why a width criterion cannot do this job

Section 11 step 2 gates interval **width** and never gates **level**. Under NULL,
ULS satisfies it in 0.375 of all cohorts and 0.65 of those with a proper fit —
barely below MODERATE's 0.45 / 0.67. A width criterion asks whether the study
learned something *precisely*; it cannot ask whether what was learned is
*non-zero*. That is the structural reason §3.2's core rule fails to discriminate.

### 3.4 Reliability is manufactured from residual structure alone

`ω` on NULL data, where the true value is exactly 0. All figures are conditional
on a proper fit and are labelled as such; the unconditional statement is given
below the table.

| cell (ULS) | true ω | mean ω̂ (c) | q05 / q50 / q95 (c) |
| --- | --- | --- | --- |
| STRONG/0.75/0.55 | 0.757 | 0.743 | 0.623 / 0.747 / 0.889 |
| STRONG/0.25/0.15 | 0.809 | 0.786 | 0.666 / 0.791 / 0.894 |
| MODERATE/0.75/0.55 | 0.564 | 0.577 | 0.294 / 0.572 / 0.792 |
| WEAK/0.75/0.55 | 0.321 | 0.379 | 0.013 / 0.355 / 0.707 |
| **NULL/0.75/0.55** | **0.000** | **0.213** | **0.001 / 0.111 / 0.602** |

**Unconditionally**, ω does not exist for 17 of 40 NULL cohorts and 7 of 40
STRONG/0.75/0.55 cohorts — those fits are improper and yield no estimate at all.
The conditional means above therefore describe 23 and 33 cohorts respectively,
not 40. No unconditional mean is quoted because the quantity is undefined where
the fit fails; the honest unconditional summary is the non-existence rate itself.

Three declared residual-covariance edges with no common factor produce a mean
apparent reliability of 0.213, with an upper tail reaching 0.602 — above
MODERATE's median. The estimator grid finds the same across **all eight NULL
rows for ULS, with `omega_bias` from +0.166 to +0.211** (four core
configurations plus four in the extra arm).

### 3.5 Discrimination collapses once failures are counted

All nine comparisons the grid provides:

| comparison | conditional AUC | **unconditional AUC** |
| --- | --- | --- |
| ULS, STRONG vs NULL | 0.992 | **0.636** |
| ULS, MODERATE vs NULL | 0.935 | **0.601** |
| ULS, WEAK vs NULL | 0.735 | **0.532** |
| ULS+floor, STRONG | 0.992 | **0.626** |
| ULS+floor, MODERATE | 0.936 | **0.594** |
| ULS+floor, WEAK | 0.734 | **0.531** |
| ML, STRONG | 0.995 | **0.592** |
| ML, MODERATE | 0.899 | **0.546** |
| ML, WEAK | 0.700 | **0.516** |

Arithmetic, not a defect. For ULS STRONG vs NULL the proper rates are 0.763 and
0.363, so only 0.277 of comparisons have both fits proper and the remainder
contribute 0.5 under the declared tie convention:
`0.277 × 0.992 + 0.723 × 0.5 = 0.636`, matching the measured value.

---

## 4. Retractions

Recorded so the git history is not left carrying them.

- **"The problem is not impossible at n = 28; ω discriminates at AUC 0.992."**
  Reported at `79297e58`. Conditional on proper fits — a diagnostic about the
  estimator, not an operating characteristic. Unconditional it is 0.636.
- **"The latent tau measurement model is not estimable at n = 28 and plausibly
  is at roughly n ≥ 100."** Asserted in the message of `c22031f9`. It applied
  the declared tie convention, `cond × both + 0.5 × (1 − both)`, to improper
  rates measured at other sample sizes — which assumes the surviving fits at a
  new geometry behave like the surviving fits at this one. Same
  conditional-performance error one level up. **Withdrawn entirely.** The
  supporting improper rates at n = 60 and n = 120 came from an ad-hoc inline
  probe that was never committed as evidence and appear in **neither** frozen
  study; both studies are at n = 28 only. Those numbers carry no standing and
  are not repeated here. V5 must run the whole procedure at its own geometry.
- **"The bootstrap non-convergence rule is the thing doing the blocking, and the
  surviving interval looks sensible."** The surviving interval is computed only
  over resamples that converged, so it is conditional on a plausibly informative
  selection event. When 30–67% of resamples fail, a reassuring survivor interval
  is not evidence the failures were ignorable.
- **The retraction of "convergence behaviour carries construct signal" is itself
  withdrawn.** I withdrew that claim on the basis of the nested study's
  NULL (0.425) falling below WEAK (0.525) — a reversal at 40 replicates, where
  the standard error on a rate near 0.5 is about 0.08, so the gap is inside
  noise. The estimator grid at **300** replicates is monotone across all four
  ULS core cells including NULL: improper rate 0.237 → 0.363 → 0.620 → 0.637 for
  STRONG → MODERATE → WEAK → NULL. **The correct statement is that the
  relationship is neither established nor refuted at these replicate counts, and
  nothing should be built on it either way.** Withdrawing a 300-replicate
  finding on a 40-replicate reversal was the wrong move.

---

## 5. What transfers to V5

Two rules, worth more than the T0 endpoint would have been.

```
DECISION-BEARING METRIC = UNCONDITIONAL OVER THE DECLARED EVALUATION POPULATION
```

Conditional-on-success statistics are diagnostics and may never carry a
decision. Every qualification in V5 — estimator, representation gate, dimension
selector, same-cell technical-intervention test, teacher/student criterion —
must report **all attempted units in the denominator**: failed fits,
zero-gradient updates, undefined cosine cases, missing support, non-estimable
donors, failed perturbations. Where a quantity is undefined for failed units,
report the non-existence rate rather than silently averaging the survivors.

```
FAILURE TO MEASURE != ABSENCE OF BIOLOGY
```

with four terminals kept permanently distinct:

- `MEASUREMENT_ESTIMATOR_NOT_QUALIFIED` — the numerical procedure cannot support
  trustworthy inference at the frozen geometry;
- `MEASUREMENT_MODEL_NOT_ESTIMABLE_AT_N` — no qualified estimator identifies the
  frozen model at this sample size;
- `COMMON_FACTOR_NOT_ESTABLISHED` — estimator and geometry qualified, data do not
  support the construct;
- `NO_SUCCESSOR_ENDPOINT_QUALIFIED` — a lawful structure may exist, no candidate
  satisfies the prospective rule.

Three further lessons earned here:

- **An inert gate can hide a broken one.** When two components fail in opposite
  directions, fixing one alone makes the system worse. Any V5 qualification
  stack must be tested with each component disabled in turn, so masking is
  visible.
- **Check whether two "independent" criteria are the same measurement.** For ULS
  the step-1 admissibility rate and the width-gate rate were identical in every
  cell. A stack of gates is only as deep as the number of genuinely distinct
  questions it asks.
- **A precision criterion is not an effect criterion.** Gating interval width
  without gating level admits confident nothing.

Also permanent, from the executor repairs:

- declared residual-covariance edges must actually participate in estimation —
  a free edge is solved as `θ_ab = R_ab − λ_aλ_b`, never left unconstrained with
  no gradient;
- Heywood/boundary solutions may not be counted as converged;
- `BOOTSTRAP SURVIVOR INTERVAL != UNCONDITIONAL SAMPLING UNCERTAINTY` when
  bootstrap failure is common.

---

## 6. What is explicitly not concluded

- Not that tau biology is absent.
- Not that a common donor tau construct does not exist.
- Not that the latent-endpoint direction is wrong.
- Not that any particular n makes the problem tractable. Neither frozen study
  varied n; every n-scaling figure has been withdrawn (§4).
- Not that ULS is the final measurement authority. It is the leading candidate
  of three, and the end-to-end procedure it sits inside is unqualified at this
  geometry, so promoting it would be meaningless.

The 5% allowance was not replaced with 20%, 40% or any other value. Tuning it to
this simulation after seeing the answer is precisely the failure this contract
existed to prevent, and
`test_improper_rate_at_n28_exceeds_the_contract_allowance` pins the constant so
the suite fails loudly if anyone edits it.

---

## 7. Disposition

T0 is a qualification rig. It did its job: it exposed, cheaply and on synthetic
data, failure modes that would otherwise have appeared for the first time in
production on a real target after the compute was spent — pseudoreplication,
effect transport, structural df over the true residual graph, leakage through
global standardization, an underidentified two-indicator method factor, improper
solutions counted as converged, reliability manufactured from residual
structure, conditional statistics masquerading as operating characteristics, two
broken gates masking one another, and two nominally independent gates that were
the same measurement.

No further effort is to be spent optimizing this rig. The failure modes carry
forward and are to be tested at the real V5 geometry.

---

## 8. Audit of this document

A five-lens adversarial review was run over the first draft against the two
evidence files. **Its verification stage did not execute** — 30 of 36 agents
died on a session limit, including every verifier — so the workflow's
`0 confirmed defects` result was vacuous, exactly the "green because it did not
run" failure this project has hit before. The 31 raw review findings were
recovered from the run journal and adjudicated by hand against the JSON.

Changes made as a result: all three estimators reported where the first draft
gave only ULS (§3.1, §3.2, §3.4, §3.5); conditional and unconditional columns
labelled rather than blended; the arithmetic corrected from 0.637 to 0.636;
improper rates given at full precision instead of inconsistent two-decimal
rounding; the §3.2/§3.3 identity discovered and reported rather than presented
as two independent findings; the M1a/M2a-under-NULL contradiction resolved; the
claim that ML is "worse in every cell" and that ULS+floor "tracks ULS closely"
both corrected; the NULL ω-bias range extended from four cells to all eight
rows; the missing zero-rate terminal added; the unsourced n-scaling numbers
removed; the design redundancy in the extra arm recorded; and the
monotonicity retraction itself withdrawn (§4).

The findings were adjudicated by the same author who wrote the draft, which is
weaker evidence than independent verification would have been. That limitation
is stated rather than hidden.
