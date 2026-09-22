# Audit-B B2 prospective scientific decision memo

Date: 2026-09-22

Status:

`PROSPECTIVE_ONLY__NO_N1_OUTCOME_OPENED__NO_B2_SELECTION_RECORDED__TRAINING_OFF`

This memo exists to make the remaining Audit-B scientific choices explicit
*before* the first N1 burden outcome is opened.

It does not choose a weighting, precision scope or near-zero precision rule.

## 1. Fixed background

The current Audit-B burden quantity is already defined prospectively.

For a sampled target, donor, policy and burden rung:

[
Delta_{B2}^{norm}
=
rac{
B2(	ext{addresses added by policy})
-
B2(	ext{addresses dropped from the common random mask})
}{
B2(	ext{uniform-random full mask at the same target/fold/rung})
}
]

The primary B2 quantity is held-out detected-token burden.

The raw-UMI B3 quantity is descriptive only and cannot control escalation.

The frozen sample ladder remains:

- N1 = 256 targets;
- N2 = 1,024 targets;
- N3 = 4,096 targets.

No N1 burden outcome has been inspected.

The current V1 execution contract is permanently non-executable and retains
historical source-balanced / relative-RSE semantics only as a preexecution
parent record.

A reviewed successor contract must encode the actual B2 resolution.

## 2. Weighting decision

Two weighting estimands are now implemented and tested.

### W1 — donor-uniform primary estimand

`DONOR_UNIFORM_ACROSS_ALL_DONORS__TARGET_UNIFORM_V1`

For each target/policy/rung:

1. every one of the 104 donors contributes one held-out donor value;
2. donors are weighted equally;
3. targets are then weighted equally.

Under the current FULL104 donor counts this implies source mass:

- HVS: 41 / 104 = 39.42%;
- NPH52: 17 / 104 = 16.35%;
- SEA_AD: 46 / 104 = 44.23%.

This is very different from cell-uniform weighting, where SEA_AD would contribute
about 90.44% of cells.

Scientific interpretation:

> "What is the average burden change for a donor drawn uniformly from the
> authenticated FULL104 donor population?"

Advantages:
- matches the current donor-primary population definition;
- prevents large donors and SEA_AD cell count from dominating;
- keeps every donor at equal scientific mass;
- does not artificially inflate small-source donor mass.

Limitation:
- source representation follows the actual 41/17/46 donor composition;
- NPH52 receives only 16.35% of primary mass.

### W2 — source-balanced primary estimand

`SOURCE_BALANCED__DONOR_UNIFORM_WITHIN_SOURCE__TARGET_UNIFORM_V1`

For each target/policy/rung:

1. average donors equally within HVS;
2. average donors equally within NPH52;
3. average donors equally within SEA_AD;
4. assign each source exactly one-third mass;
5. weight targets equally.

Scientific interpretation:

> "What is the average burden change across the three source environments when
> every source receives equal scientific mass?"

Approximate per-donor weights become:

- HVS donor: 0.813%;
- NPH52 donor: 1.961%;
- SEA_AD donor: 0.725%.

Thus one NPH52 donor receives about 2.71x the weight of one SEA_AD donor.

Advantages:
- forces all three source environments to matter equally;
- protects HVS/NPH52 from being diluted by the larger SEA_AD donor count;
- is attractive if cross-source robustness itself is the primary scientific
  estimand.

Limitation:
- no longer represents the donor-uniform FULL104 population;
- deliberately reweights individual donors according to source membership.

### W3 — primary + robustness separation

A successor could designate one of W1/W2 as the primary escalation estimand and
require the other as a mandatory non-decision-driving robustness report.

This avoids pretending the two questions are interchangeable.

A particularly clean structure would be:

- one explicitly frozen primary population estimand;
- mandatory HVS/NPH52/SEA_AD estimates shown separately;
- the alternate aggregate reported as sensitivity evidence;
- no escalation decision allowed to switch weighting after N1.

This memo does not decide which aggregate is primary.

## 3. Precision-scope decision

The current code can represent two reviewed scopes.

### S1 — one predeclared primary policy x rung cell

`ONE_PREDECLARED_PRIMARY_BURDEN_STATISTIC_V1`

One policy/rung is selected prospectively.

Only its precision determines N1 -> N2 -> N3 escalation.

All other policy/rung cells remain reportable but do not control sample size.

Advantages:
- sample size is driven by the predeclared primary scientific question;
- a nearly-null secondary cell cannot force unnecessary escalation;
- standard primary/secondary analysis structure.

Risk:
- the primary policy/rung must itself be justified before N1;
- choosing it after seeing burden is forbidden.

### S2 — all 18 non-uniform policy x rung cells

`ALL_3_NONUNIFORM_X_6_RUNG_CELLS_V1`

All 3 non-uniform policies x 6 burden rungs must satisfy the precision rule.

Advantages:
- every reported cell receives the same formal precision guarantee;
- no privileged policy/rung.

Risk:
- the noisiest or near-zero cell controls the entire sample ladder;
- a biologically null effect can force N2/N3 without improving a decision-relevant
  estimate;
- multiplicity of precision requirements makes escalation increasingly likely
  even when most cells are already well estimated.

The current all-18 rule is therefore conservative but not automatically
scientifically preferable.

## 4. Near-zero precision problem

Current V1 precision is:

[
RSE = rac{SE}{|arDelta|}
]

with threshold:

[
RSE le 0.05
]

Exact zero is already handled fail-closed.

But the problem is broader than exact zero.

For any fixed small standard error:

[
|arDelta| ightarrow 0
quadLongrightarrowquad
RSE ightarrow infty
]

So an estimate can be tightly concentrated around a biologically negligible
effect and still appear arbitrarily "imprecise" under relative-only RSE.

Example conceptually:

- mean burden effect = 0.001;
- SE = 0.0002;
- absolute uncertainty is only 0.02 percentage points of the normalized burden;
- RSE = 20%, so a 5% relative criterion fails.

Whether that should trigger four times or sixteen times more targets is a
scientific decision, not a numerical inevitability.

## 5. Candidate near-zero rules

These are prospective design choices, not recommendations encoded by this memo.

### P1 — retain relative-only RSE

Use:

[
SE / |arDelta| le 0.05
]

with an explicit rule for zero.

Strength:
- simple and scale-relative.

Weakness:
- pathological near zero;
- sample size can be driven by null effects.

### P2 — absolute-or-relative precision envelope

Predeclare an absolute tolerance (epsilon_{abs}) and pass when:

[
SE le max(epsilon_{abs}, 0.05|arDelta|)
]

Equivalent interpretation:

- for meaningful nonzero effects, require <=5% relative SE;
- near zero, require an absolute SE no larger than a scientifically meaningful
  burden-resolution floor.

Strength:
- continuous near zero;
- prevents division-by-nearly-zero from governing computation;
- still preserves relative precision for larger effects.

Critical requirement:
- (epsilon_{abs}) must be fixed before N1 from scientific meaning or external
  calibration, not estimated from N1.

### P3 — absolute precision only

Require:

[
SE le epsilon_{abs}
]

for the primary burden statistic.

Strength:
- directly answers how tightly the dimensionless normalized burden is estimated.

Weakness:
- one absolute tolerance may be too strict for large effects or too permissive
  for small but scientifically important ones.

### P4 — practical-null / confidence-bound rule

Predeclare a practical materiality threshold (delta).

Near zero, precision is sufficient when uncertainty is narrow enough to rule out
a burden effect larger than (delta).

For larger observed effects, a relative-precision criterion may apply.

This is scientifically interpretable but requires more machinery and an
independently justified materiality threshold.

## 6. Constraints on any B2 resolution

Whatever is selected must be frozen before N1 and must include:

- resolver identity;
- UTC time;
- exact non-executable V1 parent contract SHA-256;
- statement that no Audit-B burden outcome was viewed;
- weighting ID;
- precision-scope ID;
- primary policy/rung if S1 is selected;
- exact near-zero precision rule;
- all numerical tolerances;
- exact escalation semantics N1 -> N2 -> N3;
- source-stratified reporting remains mandatory;
- no policy adaptation from observed burden;
- no target-sample changes;
- no RNG changes;
- no terminal masking or training authority.

## 7. Decision sheet

The eventual reviewed resolution should explicitly fill:

```
PRIMARY_WEIGHTING =
    DONOR_UNIFORM
    OR SOURCE_BALANCED

MANDATORY_ROBUSTNESS_WEIGHTING =
    SOURCE_BALANCED
    OR DONOR_UNIFORM
    OR NONE

PRECISION_SCOPE =
    SINGLE_PRIMARY
    OR ALL_18

IF SINGLE_PRIMARY:
    PRIMARY_POLICY =
    PRIMARY_RUNG =

PRECISION_RULE =
    RELATIVE_ONLY
    OR ABSOLUTE_OR_RELATIVE
    OR ABSOLUTE_ONLY
    OR PRACTICAL_NULL_BOUND

IF RULE USES ABSOLUTE TOLERANCE:
    ABSOLUTE_SE_TOLERANCE =

IF RULE USES MATERIALITY:
    PRACTICAL_BURDEN_DELTA =

ZERO_MEAN_BEHAVIOR =

ESCALATION:
    N1=256 -> N2=1024 -> N3=4096
    driven only by the frozen primary precision rule
```

## 8. Current terminal

`B2_DECISION_MEMO_FROZEN_PREOUTCOME__NO_SELECTION_MADE__N1_UNOPENED__TRAINING_OFF`
