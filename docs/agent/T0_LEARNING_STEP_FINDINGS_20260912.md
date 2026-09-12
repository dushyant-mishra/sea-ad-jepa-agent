# T0 — the learning step, and what it means for future designs

Date: 2026-09-12
Status: `V20_DID_NOT_DEMONSTRATE_INCREMENTAL_EXPRESSION_PREDICTION__SUCCESSOR_QUESTION_OPEN`

Revised 2026-09-12 after external review corrected two overreaches in the first
version. See §4 and §9.
Supersedes the framing in `T0_CLOSEOUT_HANDOFF_20260911.md`, which named effect
transport as the blocker. It is not the first blocker. This document says why.

Nothing here changes an authority. Training remains off, the protected partitions
remain closed, V20 remains immutable.

---

## 0. The interpretation to carry forward

> **V20 is not evidence that the biological target is absent.** It is evidence
> that the frozen V20 high-dimensional donor-level ridge formulation failed to
> demonstrate incremental expression-based prediction over its nuisance-only
> limit. Its extreme shrinkage, monotone boundary-seeking CV trajectory, and near
> identity with the λ→∞ comparator show that the fitted expression contribution
> effectively collapsed. Therefore transport and confirmation of the V20 effect
> should not proceed as though a qualified expression target had been
> established.

The successor question is open and worth pursuing:

> Can the existing cellular dataset support a better-qualified,
> low-effective-dimensional biological representation of AT8 while preserving
> donor-level independence and confirmation discipline?

## 1. Bottom line

The V21 work — estimator family, ridge procedure, selection rule, power gate,
effect transport — all asked **how to carry a discovered effect forward**. The
prior question, *whether anything was discovered*, was never checked. It has now
been measured, and the answer is that it cannot be established at n = 28 with
this loss.

Three measurements, independent of each other, point the same way.

**The fitted expression component has under a third of one effective degree of
freedom.** From published numbers only, no data access:

```
edf = Σ dᵢ/(dᵢ+λ) ≤ Σ dᵢ/λ = trace/λ = n/10^e = 28/100 = 0.28
```

This holds for any eigenvalue spectrum, since `d/(d+λ) ≤ d/λ`. Checked
numerically across flat, power-law and one-dominant spectra: 0.24–0.28. The
covariance structure barely matters at λ = 100× the mean eigenvalue, which is why
characterizing the 24,482-dimensional spectrum turned out to be much less urgent
than it looked.

**V20's CV curve descends monotonically across all 17 grid points and is still
falling at the edge** — 2.4220 at exponent −6.0 to 1.8830 at +2.0, with 0.575%
still being gained on the last step.

**That endpoint is statistically indistinguishable from using no expression at
all.** The nuisance-only comparator is `L_∞ = 1.877862` against V20's best grid
point of `1.882992`.

Read together: the CV curve is not selecting a regularization strength, it is
shrinking the expression contribution away, and it converges on the no-expression
limit. The grid-boundary selection at +2.0 was previously diagnosed as a
well-posedness defect that V21's bracket expansion would fix. That reading now
looks like a symptom treated as the disease — expanding the grid lets the model
shrink further toward the same limit.

---

## 2. The comparison is unresolved, and that is itself the finding

```
L_∞                              = 1.877862   (three implementations, identical)
V20 best grid point (exp +2.0)   = 1.882992
difference                       = −0.005130  (0.272%)
```

Pre-specified rule: near-equality is unresolved, inspect the folds. The folds say
why it cannot be resolved.

```
|difference| / se of the mean       = 0.0076
top donor share of the total        = 33.5%
top three donors                    = 58.6%
median / mean fold loss             = 0.47
leave-one-donor-out L_∞             = 1.2954 … 1.9474   (contains 1.882992)
dropping the most influential donor moves L_∞ by −0.5824 — 114× the difference
```

The quantity being compared is **1/130th of a standard error**, and one donor
moves the estimate 114 times more than the difference itself. This is a statement
about the resolving power of the measurement, not a finding that the model does
or does not beat nuisance-only prediction.

Per the pre-agreed framing: were the difference decisive and negative, the correct
claim would be that *the frozen V20 learner, objective and grid did not beat their
nuisance-only limit* — not that AT8 is unpredictable from expression.

---

## 3. The target distribution, measured rather than assumed

The per-fold losses are strongly right-skewed at the donor level: median/mean =
0.47, one donor contributing 33.5% of the total, top three 58.6%.

So squared-error CV on this target genuinely is driven by a handful of high-AT8
donors. This was previously an assumption on both sides of the argument; it is now
a measurement, and it matters for any future objective choice. A model can improve
MSE by fitting the bulk while failing entirely on the rare high-pathology biology
of interest, and the reverse is equally possible.

---

## 4. What is and is not a structural limit

**Corrected after review.** The first version of this section said donor-level
pseudobulk regression on this cohort was structurally dead because p ≫ n. That
does not follow and is withdrawn.

**p ≫ n does not preclude learning.** If the biology lives on a low-dimensional
manifold, a sparse programme, a small number of pathways, or a pretrained
representation, a 24,482-dimensional starting matrix can still contain a learnable
low-dimensional signal. What V20 showed is that *its particular representation,
ridge objective and endpoint formulation* did not establish that signal. Likewise
`edf ≤ 0.28` describes the fitted V20 solution at its selected λ; it says nothing
about the intrinsic dimensionality of the true biological signal.

**The cells do not change the sample size of the outcome, and the first version of
this document was dangerously wrong about that.** It claimed the design "throws
away four orders of magnitude of sample size" and recommended moving the
statistics to where the dataset is large. AT8 is measured **once per donor**, so
every cell of a donor inherits the same outcome value. Those cells are not
independent pathology observations, and treating them as such is pseudoreplication.

For any relationship of the form `cell biology → donor-level pathology`:

```
n_independent_pathology_units = 46,   not 638,150
```

**What the cells are genuinely for** is measuring the predictor well, and that is
worth a great deal: cell-state proportions, rare-state abundance, neighbourhood
structure, expression programmes, conditional cell-state distributions,
within-donor heterogeneity, cell-state-specific pathway scores, learned
representations. The correct shape is

```
638,150 cells → a well-measured, low-dimensional representation of 46 donors
              → donor-level pathology inference at n = 46
```

There is a quantitative reason this helps. Attenuation bounds an observed
correlation by the reliability of its measurements, roughly
`ρ_observed ≈ ρ_true √reliability`. Reducing noise in the donor representation
raises the achievable ρ toward its ceiling without touching the outcome. The cells
buy real power — through the predictor, which is exactly where they legitimately
can.

**The one constraint no representation can relax.** Confirmation power depends
only on ρ and the confirmation cohort size:

| | available | needed at ρ ≈ 0.48 |
| --- | --- | --- |
| confirmation donors | 12 | 22 (α = 0.05, frozen nuisance) to 33 (current design) |

A better representation helps only by raising ρ past the bar. At n = 12 with the
nuisance frozen and α = 0.05 that bar is **ρ ≥ 0.61**. Any successor should be
checked against it at the design stage rather than after the work.

---

## 5. What to fold into future designs

**Establish the learning step before building anything downstream.** The cheapest
possible check — one number, comparing the fitted model against its own
nuisance-only limit — should be a gate at the point of discovery, not something
computed months later. Everything V21 built sits on top of a premise that took an
afternoon to test.

**Publish the null comparator alongside any CV curve.** A CV minimum is
meaningless without the value the curve is descending toward. Had `L_∞` been
recorded next to the 17 grid losses in V20's output, the whole question would have
been visible immediately.

**Treat a boundary selection as a diagnostic before treating it as a bug.** The
+2.0 hit was read as a misspecified grid. Ask first what the model is doing at
that boundary; at λ → ∞ ridge degenerates toward a similarity-weighted average of
training outcomes, which is a different object from a learned gene programme.

**Report effective degrees of freedom with any regularized fit.** `edf ≤ n/10^e`
is free to compute and would have flagged this immediately. A fit with edf < 1 is
not a 24,482-feature model in any meaningful sense.

**Match simulation geometry to the dataset before trusting any conclusion from
it.** A study calibrated at 12 genes said nothing about a 24,482-feature problem,
and it produced confident, wrong answers. Anchor to the project's own measured
results — V20's `t = 1.9002, df = 12` implies ρ ≈ 0.48 and was available the whole
time.

**Separate the sample size of the outcome from the quality of the predictor.**
If a question needs donor-level inference, the donor count is the sample size no
matter how many cells were collected. Use the cells to measure the donor
representation better and to keep its effective dimensionality low — never as
replicate observations of a donor-level outcome.

**Keep the confirmation-design levers explicit.** Freezing the nuisance
coefficients from development donors rather than re-estimating four columns on
twelve is worth 0.269 → 0.411 power at unchanged α, and it preserves type I error
(measured 0.0455 against a nominal 0.050). Also: a 1/11 sex split at n = 12 gives
that donor HC3 leverage exactly 1.0 and is inestimable outright — with the real
31F/15M cohort ratio, a fresh 12 has a **6.0%** chance of landing there.

---

## 5b. The successor shape, and what a permutation test would and would not settle

Not a rerun of V20, and not an abandonment of donor-level target discovery. The
dataset-first shape is:

```
raw cells → qualified biological representation (no protected AT8)
          → small, structured donor representation
          → AT8 association at n = 46, with confirmation discipline intact
```

The point is to stop asking ridge to discover biology from 24,482 essentially raw
molecular features and 28 donors, and instead to arrive at the donor-level step
with a deliberately low-dimensional, independently qualified representation.

**On the whole-procedure permutation test.** Permuting AT8 and re-running the
complete V20 discovery machinery, including tuning and selection, would answer:
*does the V20 pipeline extract more donor-level predictive structure than
exchangeability would produce?* That is a legitimate closure test for V20 as
history. It would **not** answer whether AT8 is biologically predictable from this
dataset, and it would say nothing about whether another representation works.
Given the exact `L_∞` result, it is worth running only if a rigorous postmortem of
V20 is wanted. **The successor architecture should not be made to depend on it.**

## 6. What is preserved and remains correct

- the V20 broad immune-state result as reported, with its recovered sensitivities;
- the rare-tail refusal, `RARE_TAIL_UNDERDETERMINED_MEASUREMENT`;
- the same-cell counterfactual QC principle — association warns, intervention
  qualifies — which is portable to any future design;
- the donor-level discovery/confirmation firewall;
- power-before-spending-a-holdout, which worked exactly as intended by refusing;
- the provenance and fail-closed machinery, which caught two errors today: a
  wrong pathology source, and an estimand that the design declared unvalidated
  while the code used it anyway.

---

## 7. Corrections to earlier claims in this line of work

| earlier claim | status |
| --- | --- |
| "prospective confirmation should be abandoned" | **retracted** — concluded from a toy geometry; never committed |
| achievable ρ is 0.07–0.40 | **void** — an artifact of a 12-gene simulation |
| "the learner selects +2.0 even on pure noise" | **wrong as stated** — 40% of seeds select +2.0, the rest select −6.0; that instability is a property of the toy, not the real data |
| "every grid point is worse than predicting nothing" | **not established** — the null asymptote spans 1.51–2.51 across outcome distributions |
| effect transport is the first blocker | **superseded** — incremental expression prediction was never established |
| "donor-level regression on this cohort is structurally dead" | **withdrawn** — p ≫ n does not preclude learning; V20's representation and objective failed, which is narrower |
| "the design throws away four orders of magnitude of sample size" | **withdrawn, and it was the most damaging claim** — AT8 is one value per donor, so cells are not independent outcome observations; the recommendation would have invited pseudoreplication |

---

## 8. Evidence and provenance

| artifact | content |
| --- | --- |
| `scripts/v4/t0_v21_null_comparator_probe_v1.py` | the `L_∞` computation |
| `docs/agent/evidence/t0_v21_null_comparator_20260912.json` | all 28 fold losses |
| `scripts/v4/t0_v21_locate_frozen_pathology_source_v1.py` | source-identity resolution |
| `scripts/v4/t0_v21_transport_estimand_v1.py` | the partial-correlation estimand and its derivation |
| `scripts/v4/t0_v21_crossfit_null_calibration_v1.py` | cross-fit null calibration |
| `docs/agent/evidence/t0_v21_crossfit_null_calibration_20260911.json` | its results |

AT8 was read only through the frozen discovery-only loader, which skipped the 18
confirmation rows before their values were touched. The load reproduced V20's
frozen donor-set digest `4395fec7…` and endpoint-values digest `4cfb5727…`,
proving it is the same read V20 performed and nothing more. The frozen source
guard refused an incorrect candidate file (`20c444d0…` against the required
`ebbe9bc0…`) before any value was parsed.

No expression store was opened. No confirmation AT8 was read. No partition was
opened. No training occurred.

```
EFFECT_TRANSPORT_STATUS                  = OPEN (superseded as the first blocker)
POWER_GATE_PRODUCTION_VERDICT_CAPABILITY = DISABLED
S0_S4_EXECUTION_AUTHORITY                = FALSE
FRESH_CONFIRMATION_AUTHORITY             = FALSE
TRAINING_AUTHORITY                       = FALSE
```
