# H4 and G2 — preterminal design work

Date: 2026-09-20
Status: **design only; nothing frozen, no value selected, no rung opened**

Both items below are independent of the G5 margin value and were developed
without consulting any terminal masking outcome, D_shared, pathology, DEV or
SEALED data.

---

# H4 — interpretation tree for "all burden rungs fail"

## The problem

The ladder evaluates 5%, 10%, 15%, 20%, 30%, 50% and stops at the first fully
qualifying rung. If none qualifies it returns
`FAIL_CLOSED_NO_MASKING_AUTHORITY`. That single terminal is currently
**scientifically ambiguous**: at least four materially different states produce
it, and they imply opposite next actions.

Without a preregistered interpretation rule, a multi-hour run can end in a
verdict nobody can act on — and the temptation afterwards is to loosen δ, which
would convert a failed experiment into a tuned one.

## The four states, and how to separate them

Each branch must be decidable from evidence gathered **during** the same run, and
each discriminator must be preregistered before any rung opens.

### State A — targeted masking genuinely does not help

*Meaning.* No policy suppresses the shortcut beyond what uniform masking already
achieves.

*Discriminator.* `delta_vs_uniform` confidence intervals cover zero (or are
negative) for every non-uniform arm at every rung, **while** controls pass and
the planted positive control is detected. The machinery worked; the effect is
absent.

*Implication.* A real negative result about dependency-aware masking. Do not
retune. Record and redesign the intervention, not the threshold.

### State B — the margin δ was too strict

*Meaning.* Residual shortcut is small but not below δ.

*Discriminator.* Residual upper bounds cluster just above δ — within, say, a
preregistered multiple of the residual interval half-width — while controls pass
and per-source guardrails are individually satisfied.

*Implication.* **Do not widen δ.** δ is a prospective scientific claim about what
is negligible. Widening it after seeing residuals is exactly the prohibited move.
The lawful response is to record that the design could not achieve the declared
standard.

### State C — residual predictability is irreducible

*Meaning.* Some shortcut survives any masking because it does not live in the
masked addresses — depth, detection rate, or global library structure that
survives log1p-10k normalisation.

*Discriminator.* Residual is approximately **flat across burden rungs**: a
fivefold increase in masked evidence (5% → 50%, 859 → 8,592 co-masked addresses)
barely moves it. A shortcut that lives in the masked addresses must decay with
burden; one that does not is not being masked at all.

*Implication.* The threat model is misspecified. Suppressing it requires an
intervention on the *representation or normalisation*, not on masking. This is
the most scientifically informative of the four outcomes and the easiest to miss.

### State D — insufficient equivalence power

*Meaning.* The design cannot resolve residual below δ regardless of truth.

*Discriminator.* The residual interval **half-width is itself comparable to or
larger than δ**. Then "residual < δ" is unestablishable a priori and the run
carried no information about the hypothesis.

*Implication.* This is H3, and it should have been caught before execution.
Detecting it only at the end means the run was not worth doing.

## Required preregistration

Before any rung opens, freeze:

1. the four discriminators above with their exact statistics;
2. the flatness criterion for State C (what counts as "does not decay with burden");
3. the proximity multiple for State B;
4. the power criterion for State D — which is H3, and must be settled **first**;
5. an explicit statement that State B **never** authorises widening δ.

## Observation

State D is checkable **before** execution — the residual interval half-width is a
property of the design, not of the outcome. Running the ladder without having
excluded State D is running an experiment already known to be uninformative. That
is the strongest practical argument for settling H3 before any terminal run.

---

# G2 — complexity-equivalence band scaling

## The defect

`TARGETING_COMPLEXITY_EQUIVALENCE_EVENTS = 1` is a fixed constant, while the
target × outer-fold grid varies across the frozen panel ladder:

| targets | grid | band | band as fraction of grid | relative stringency |
|---|---|---|---|---|
| 128 | 512 | 1 event | 0.001953 | 1.0× |
| 256 | 1024 | 1 event | 0.000977 | 2.0× |
| 512 | 2048 | 1 event | 0.000488 | 4.0× |
| 1024 | 4096 | 1 event | 0.000244 | **8.0×** |

The band is **8× stricter at the largest panel than at the smallest**, entirely
because the grid is larger. Whether two policies count as "equivalently complex"
therefore depends on a panel-size decision made for statistical-power reasons,
not on any judgement about targeting complexity.

## Why it matters

Within a rung, selection is: among qualifying policies prefer minimum targeting,
then maximum effect. Effect size only breaks ties **inside** the band. So the
band's width determines how often effect size is consulted at all. At 1024
targets a 2-event difference — 0.049% of the grid — overrides an arbitrarily
large effect difference; at 128 targets the same *relative* difference would be
8 events and would fall outside the band.

This also violates the project's own standing rule that dataset geometry
determines scale-sensitive parameters. Grid size **is** dataset geometry, and the
band ignores it.

## Candidate scale-free formulations (none selected)

| formulation | 128 | 256 | 512 | 1024 |
|---|---|---|---|---|
| fixed 1 event *(current)* | 1 | 1 | 1 | 1 |
| 0.1% of grid | 0.5 | 1.0 | 2.0 | 4.1 |
| 0.5% of grid | 2.6 | 5.1 | 10.2 | 20.5 |

A proportional band keeps relative stringency constant. Alternatives worth
considering: a band expressed per target-fold cell (e.g. ≤ 1 event per cell on
average); a band derived from the targeted-partner cap, since that bounds
per-query complexity; or a band tied to the measurement resolution of
`mean_effective_targeted_n` itself.

**None is selected here.** Any replacement must be frozen prospectively with its
own justification, and — like δ — must not be chosen by observing which policy it
would favour.

## Interaction with H4 State B

If the band is widened, more policies become complexity-equivalent and effect
size decides more often. That changes which policy is selected, not whether any
qualifies, so it does not affect the all-rungs-fail analysis. The two are
independent and can be settled in either order.

---

## Status

Both items are **design work only**. Nothing is frozen, no constant is selected,
no rung is opened, and no terminal outcome was consulted. H4 remains open pending
its preregistration and pending H3; G2 remains open pending a prospectively
justified scale-free band.


---

## 2026-09-21 implementation update — G2 mechanics separated from parameter choice

A successor implementation now exists at:

`src/sea_ad_jepa/v5/targeting_complexity_materiality_v1.py`

with focused tests at:

`tests/test_v5_targeting_complexity_materiality_v1.py`.

It represents the complexity-equivalence band as an **exact fraction of the
bound target x outer-fold grid**, using integer cross-multiplication rather than
floating-point rounding. Therefore one declared relative materiality has the
same stringency at 128, 256, 512, or 1024 targets.

The successor authority requires:

- an exact numerator/denominator for the relative band;
- a nonempty scientific rationale ID;
- a SHA-256 binding the rationale;
- an explicit declaration that terminal outcomes were not inspected.

It rejects post-outcome freezing.

This closes the **implementation-form** problem only. It does not justify or
select the production fraction, and the canonical selector remains unchanged.

```
G2_SCALE_FREE_SELECTOR_IMPLEMENTATION = READY_AND_TESTED
G2_PRODUCTION_MATERIALITY_FRACTION   = OPEN
CANONICAL_POLICY_SELECTOR_CHANGED    = false
TERMINAL_MASKING_OUTCOMES            = UNOPENED
TRAINING_OFF
```
