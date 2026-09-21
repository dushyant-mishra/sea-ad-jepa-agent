# G5 — null-equivalence margin: basis options

Date: 2026-09-20
Status at end of document: **`STOP_G5_NULL_EQUIVALENCE_MARGIN_BASIS_OPEN`**

This document identifies candidate scientific bases for the FULL104
null-equivalence margin. **It selects no value and freezes nothing.** No terminal
masking outcome, D_shared, pathology, DEV or SEALED outcome was consulted.

---

## 0. The question, stated precisely

The masking decision declares a policy acceptable when residual shortcut
predictability is *equivalent to null* within a margin δ. Every threshold in the
decision reads that one constant: the primary null bar, each per-source
guardrail, the nonlinear bar, the target-heterogeneity floor (as −δ), and the
admissibility window for the negative control.

So δ must answer:

> **How much residual shortcut information is small enough that a model exploiting
> it would still be learning biological/cellular state rather than recovering
> hidden expression by local interpolation?**

That is a question about **scientific consequence**, not about sampling error.

### The statistic δ applies to

`excess_over_shuffled_null` — the paired difference

```
residual = actual_policy_score − shuffled_same_mask_score
```

on the primary score: source-balanced mean of per-donor, donor-centred
prediction correlation **squared**, bounded [0, 1]. Both arms use the identical
already-selected mask; the shuffle is a deterministic within-donor permutation of
the target. δ is therefore on a **shared-variance scale**, not a correlation
scale and not a raw-count scale. Any candidate basis must produce a number on
that same scale or state its conversion explicitly.

### Why an equivalence margin cannot be inherited

An equivalence margin is the largest effect considered scientifically negligible.
It is a claim about the science, not a property of the estimator, so it cannot be
read off a previous run, a different universe size, or a different attacker.

---

## 1. Biological-consequence / practical-effect basis

**Interpretation.** δ is the largest residual shortcut that could not materially
change the biological-state content the representation is meant to carry.

**Applies to.** `excess_over_shuffled_null`, directly.

**Form.** Define a state-fidelity functional `S(·)` on the authorised
representation, pathology-blind. Find the residual shortcut magnitude r at which
the induced change in `S` falls below a preregistered negligible change:

```
δ = max { r : |S(model | residual = r) − S(model | residual = 0)| < ε_bio }
```

**Evidence required.** A frozen, pathology-blind state-fidelity functional; a
characterised monotone relation between residual shortcut and that functional;
a preregistered ε_bio.

**Currently available?** **No.** No such functional is frozen (this is G4), and
the residual→fidelity relation has never been characterised.

**Independent of terminal outcomes?** Yes, if `S` is defined and calibrated
without opening any masking rung.

**Strengths.** The only class that answers the question actually asked. It ties δ
to consequence rather than to estimator behaviour.

**Failure modes.** ε_bio becomes the same unjustified constant one level up —
displacing the arbitrariness rather than removing it. Requires a defensible
state-fidelity measure the project does not yet have.

**Circular if.** `S` is calibrated on the same masking outcomes δ will later
judge, or if ε_bio is tuned so a preferred policy passes.

---

## 2. Measurement / reproducibility-resolution basis

**Interpretation.** δ is tied to the resolution floor of the authorised
representation or attacker statistic: differences the measurement cannot
reliably resolve cannot carry scientific meaning.

**Applies to.** The same paired residual, via the reproducibility of the score
under technical re-measurement.

**Form.** Using same-cell technical intervention (the existing thinning
machinery), estimate the score's reproducibility floor `σ_repro`, then set
δ = k·σ_repro for a preregistered k.

**Evidence required.** Same-cell counterfactual intervention on the authorised
representation; a frozen k with its own justification.

**Currently available?** **Partially.** The same-cell thinning machinery exists
and has been audited, but it was applied at a different model class and to a
different statistic. It would need re-running against the current primary score.

**Independent of terminal outcomes?** Yes.

**Strengths.** Grounded in the measurement process rather than in a preference;
reuses machinery already qualified as an intervention rather than an association.

**Failure modes.** **This is the dangerous one.** A measurement noise floor is
*not* practical insignificance. A shortcut can be perfectly reproducible and
still scientifically fatal — reproducibility bounds what we can *detect*, not
what *matters*. Used alone this conflates "too small to measure" with "too small
to care about", and those come apart precisely when the measurement is good.

**Circular if.** k is chosen to make the observed residual pass.

---

## 3. Negative-control calibration — supporting evidence only

**Interpretation.** Shuffled/null controls characterise the numerical and
statistical background of the paired estimand.

**Applies to.** `negative_control_delta`, already computed per policy.

**Form.** Characterise the null distribution's spread; use it to bound
numerical/statistical background.

**Currently available?** **Yes** — the control-calibration cache supports exactly
this, and the decision layer already requires the negative control to lie inside
the frozen margin.

**Independent of terminal outcomes?** Yes.

**Strengths.** Cheap, lawful, available now. Genuinely useful as a precision and
sanity check, and as a *lower bound*: δ below the null background would be
unmeasurable and therefore useless.

**Failure modes — decisive.**

> **`null variability != scientific equivalence margin`**

The null distribution describes how the statistic behaves when there is nothing
to find. It says nothing about how much of something would be acceptable. Setting
δ from null spread means a noisier pipeline earns a looser scientific bar, which
is the F12 defect in a new place: precision buying permissiveness.

**Verdict.** Use as a **floor and a sanity check**, never as the basis.

---

## 4. Downstream-sensitivity basis

**Interpretation.** δ is the residual shortcut magnitude with negligible effect
on the downstream state quantity the JEPA exists to preserve.

**Applies to.** A downstream functional of the learned representation, mapped
back onto the residual scale.

**Form.** For downstream quantity Q, characterise sensitivity ∂Q/∂(residual) and
set δ where the induced change in Q is below a preregistered tolerance.

**Evidence required.** A frozen, pathology-blind downstream quantity; a
characterised sensitivity relation; a tolerance on Q justified in Q's own units.

**Currently available?** **No.** Requires a trained representation, and training
is off. Could in principle be approximated with a frozen non-trained
state-fidelity proxy.

**Independent of terminal outcomes?** Yes, if Q is pathology-blind and calibrated
before any rung opens.

**Strengths.** Provides the principled bridge from an abstract shortcut score to
a consequence expressed in units someone can reason about — the thing basis 1
wants and basis 2 lacks.

**Failure modes.** Tolerance on Q needs its own justification; sensitivity may be
non-monotone or policy-dependent. Cannot be completed pre-training without an
explicitly declared proxy.

**Circular if.** Q is evaluated on protected outcomes, or the tolerance is set
after seeing which policies pass.

---

## 5. Externally justified tolerance

**Interpretation.** Adopt a margin from an independent scientific or measurement
standard that legitimately applies to this quantity.

**Currently available?** **No candidate identified.** The primary score —
source-balanced mean of per-donor donor-centred squared prediction correlation,
after burden-preserving co-masking on a 17,186-address strict common core — is
specific to this design. No external literature threshold is known to measure the
same quantity.

**Strengths.** If one existed, it would be the least circular option available.

**Failure modes.** Retrofitting a threshold that measures a *different* quantity
is worse than having none: it imports false authority. A shared *name* (an R²
cutoff, say) is not a shared *estimand*.

---

## 6. Explicitly rejected

| rejected basis | why |
|---|---|
| historical `0.001` | prior use is not justification; different universe, attacker and estimand |
| the observed terminal result | δ must be frozen before outcomes; this inverts the test |
| any value chosen so a preferred policy passes | defines the answer as the premise |
| δ estimated from the same data then called prospective | prospective means *before*, not *derived and relabelled* |
| sampling error / detectability alone | statistical significance ≠ practical significance; a detectable shortcut may be negligible and an undetectable one may not be |
| the calibration envelope (1024 targets / 1024 rows-per-donor / 31 distractors / 32 features) | an acceleration envelope, not a biological definition of negligible |

---

## 7. Assessment

Only bases **1** and **4** can actually answer the question, because only they
express δ in terms of consequence. Both are currently **unavailable**: each needs
a frozen pathology-blind state-fidelity or downstream quantity that does not yet
exist. That requirement is **G4**, which means:

> **G5 is blocked on G4, not merely unresolved.**

Basis **2** is available in principle but must not stand alone — it answers
"what can we resolve?", not "what matters?". Basis **3** is available now and is
genuinely useful as a floor and sanity check, but using it as the basis would
reintroduce the defect where imprecision buys permissiveness. Basis **5** has no
candidate.

### Recommended sequence

1. Define and freeze the G4 pathology-blind state-fidelity functional `S`.
2. Characterise the residual-shortcut → `S` relation on lawful calibration data.
3. Preregister ε_bio in `S`'s own units, with its justification.
4. Derive δ from basis 1 (or basis 4 once a downstream quantity exists).
5. Use basis 3 only to check δ exceeds the null background — a floor, never the value.
6. Only then size H3 for equivalence precision against that δ.

### Non-negotiable ordering

H3 asks whether the design can establish *residual < δ*. That is unanswerable
until δ exists. The current target-panel ladder sizes for detecting a
deliberately easy **planted** shortcut — a superiority question on a large
effect, not an equivalence question on a small one. It must not be reused as H3
evidence.

---

## Status

**`STOP_G5_NULL_EQUIVALENCE_MARGIN_BASIS_OPEN`**

No margin selected. No basis frozen. The blocking dependency is identified and
specific: **G5 requires G4's state-fidelity functional first.** That is a real
result — it converts an open question into an ordered one — but it is not
closure, and it is not manufactured as such.
