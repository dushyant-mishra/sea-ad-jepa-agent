# The 32-feature confirmation, and why G3 stays open

Date: 2026-09-20
Status: **design and scoping only. No rung opened, no attacker frozen, no
capacity constant selected.**

Two statements must be held apart. Both are true; conflating them would convert
a narrow, real result into a broad, unearned one.

| | |
|---|---|
| **PRESERVED** | The 32-feature confirmation evidence stands as produced. |
| **OPEN** | `G3 production-capacity shortcut resistance` is not established. |

---

## 1. What the 32-feature attacker actually is

From `full104_control_calibration_cache_evaluator_v1.py:293-294`:

```python
if len(set(feature_cols)) != 32:
    raise ValueError("capacity control must expose exactly 32 distinct features")
```

So the confirmation attacker is, precisely:

* **32 distinct feature columns** — one proxy address plus 31 distractors
  (`distractor_count = 31` in the calibration envelope);
* a **linear ridge**, `A = XᵀX + α n I`, `b = Xᵀy / scale`;
* fitted on a cached design of 105,553 retained rows across 104 donors, capped
  at 1,024 rows per donor and 1,024 targets.

## 2. What that evidence does establish

It is a genuine and useful result, and nothing here withdraws it:

* the shortcut-detection machinery **has power** — when a shortcut is planted,
  this attacker finds it;
* the paired actual-vs-shuffled contrast behaves as designed on a known positive;
* the estimator, the caching, and the donor-balanced scoring reproduce.

That is a working **positive control**. It is what lets a null result later be
read as "no shortcut detected" rather than "the detector was broken."

## 3. What it does not establish

The masking decision needs the opposite direction — evidence that a residual
shortcut is *not exploitable*. A negative from this attacker does not supply it,
for three independent reasons.

**Capacity.** A 32-feature linear ridge has on the order of 32 free parameters.
The production encoder has many orders of magnitude more. "Not recoverable by 32
linear coefficients" is a very weak upper bound on "not recoverable by the model
we are actually going to train."

**Functional form.** A ridge fits a single linear map. Any shortcut expressed
through interactions, thresholds, ratios, or rank structure is invisible to it
by construction — not because the shortcut is small, but because the estimator
cannot represent it. Absence of linear predictability is not absence of
predictability.

**Address count.** The attacker sees 32 columns. The production model sees the
whole 17,186-address strict common core. A shortcut distributed weakly across
thousands of addresses can be individually negligible in every one of them and
jointly decisive, and this attacker cannot see that at all.

Together:

> **residual undetectable by a 32-feature linear ridge**
> **≠ residual unexploitable by the production model**

The existing planted-shortcut ladder is therefore **not** G3 evidence. It is a
superiority test on a deliberately easy planted effect. G3 asks the opposite
question about a small, adversarially chosen one.

## 4. The envelope constants are not a capacity claim

`max_target_count = 1024`, `max_rows_per_donor = 1024`, `distractor_count = 31`
and the 32-feature cap are a **calibration and acceleration envelope**. They were
chosen so the calibration cache could be built in feasible time. Freezing them in
code does not confer production authority, and they are not evidence that H3
equivalence power, G3 capacity resistance, or any production capacity has been
scientifically established. The cache evidence record already says this; it is
repeated here because this is exactly the point where the two get conflated.

## 5. What a G3-sufficient attacker would have to satisfy

Design requirements only. None of these is selected, sized, or frozen here.

**R1 — capacity at least matched to production.** The attacker's effective
capacity must be no smaller than the representation route the production model
uses. If the model can fit it, the attacker must be able to fit it. An attacker
weaker than the model cannot bound what the model will find.

**R2 — functional form at least as expressive.** At minimum a nonlinear learner;
ideally the same architecture family as the production encoder, so "the attacker
could not find it" is a statement about the information rather than about the
hypothesis class.

**R3 — full address access.** The attacker must see the same address space the
model sees, not a 32-column excerpt, so that distributed shortcuts are reachable.

**R4 — honest generalisation.** Donor-held-out evaluation, because a
high-capacity attacker will otherwise memorise. The measured quantity must be
out-of-donor predictability, never in-sample fit.

**R5 — its own positive control, at its own capacity.** A high-capacity attacker
needs its own planted-shortcut check. Capacity does not imply power: a
high-capacity learner can fail from optimisation or sample size, and that failure
would masquerade as "no shortcut."

**R6 — declared before the outcome.** Architecture, capacity, training budget,
and stopping rule frozen in advance. An attacker tuned until it stops finding
something is not an attacker.

## 6. The ordering problem, stated plainly

R1 and R2 make G3 partly dependent on the production model's architecture and
capacity — which is F14/F15 territory, and is itself not yet established. And
R4's measured quantity is the same residual predictability that G5's margin must
be expressed on. So:

```
G3 needs:  a frozen production representation route (F13/F14/F15)
           + a margin to compare residual against (G5)
G5 needs:  a frozen pathology-blind state-fidelity functional (G4)
```

G3 is therefore not independently closable right now, and no amount of
strengthening the current linear attacker closes it. Recording the dependency is
the honest result; declaring G3 closed on the strength of the 32-feature
confirmation would not be.

## 7. Standing statements

```
32_FEATURE_CONFIRMATION_EVIDENCE = PRESERVED_AS_PRODUCED
G3_PRODUCTION_CAPACITY_SHORTCUT_RESISTANCE = OPEN
```

Do not conflate them. A working positive control at one capacity is evidence
that the detector functions. It is not evidence that a different, much larger
model cannot exploit what that detector missed.
