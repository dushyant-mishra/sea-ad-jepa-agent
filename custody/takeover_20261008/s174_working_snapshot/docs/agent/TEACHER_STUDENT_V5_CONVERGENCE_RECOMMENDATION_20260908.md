# Teacher/Student V5 Convergence Recommendation V1 — 2026-09-08

Status: **EXTERNAL REVIEW RECOMMENDATION — NOT A SCIENTIFIC FREEZE / NOT TRAINING AUTHORITY**

This recommendation resolves architecture ambiguity using only outcome-blind
reader-fit geometry already present in the V5 branch.

## 1. Separate the two clocks permanently

### Q40_MECHANICS

Purpose:
- AMP/backward correctness;
- mandatory gradients;
- optimizer-step proof;
- Adam moments;
- EMA equation/counter;
- checkpoint/resume/RNG mechanics.

A bounded historical-style 40-update qualification remains useful for this
purpose.

It is **not** a biological-learning checkpoint.

### Full-reader scientific exposure clock

Production learning begins only after Q40 mechanics passes and a distinct V5
full-reader execution authority is issued.

The production schedule must expose the complete 4,553,407-cell reader-fit
population through a prospectively compiled sampling policy.

Scientific checkpoints must be named by frozen exposure/coverage milestones,
not by inherited u40/u205 labels.

The exact milestone values remain to be compiled before training. The milestone
schema should record at least:

- total scientific presentations;
- presentations by donor;
- unique cells by donor;
- presentations and unique cells by donor x operator/support stratum;
- source totals;
- target/masking support totals;
- relational sampled-group/triplet totals.

No biological score may decide when a milestone occurs.

## 2. Amend TD60 before any learned checkpoint exists

TD60 currently treats successor u40 as the decision-bearing learned teacher.

That conflicts with the later data-first audit, which states fixed u40 cannot
serve as the learned-biology clock on 4.55M cells.

Prospectively supersede that checkpoint clause:

```text
OLD: decision-bearing checkpoint = successor u40 EMA teacher
NEW: decision-bearing checkpoint =
     first frozen V5 full-reader scientific-exposure checkpoint
     after mechanics qualification
```

Reuse the already-frozen TD57B/TD59 molecular panels, triplets, nulls and 48-case
criterion. Only the checkpoint eligibility clause changes.

No TD60 outcome has been opened, so this correction remains prospective.

## 3. Recommended primary cell estimand

The scientific unit is donor recurrence.

The descriptive V5 analysis reports:

- cell-uniform target mass:
  - HVS 4.36%
  - NPH52 5.19%
  - SEA_AD 90.44%
- donor-uniform target mass:
  - HVS 39.42%
  - NPH52 16.35%
  - SEA_AD 44.23%
- source-donor-uniform:
  - 33.33% each source.

A cell-uniform target therefore makes source cell yield, especially SEA_AD
yield, the dominant scientific weighting.

### Recommended candidate

`DONOR_UNIFORM_CELL_WITHIN_DONOR`

Target probability:

`p(cell c in donor d) = 1 / (104 * n_d)`

Proposal:

sample donor uniformly, then sample a lawful cell uniformly within that donor.

Thus:

`q(cell) = p(cell)`

and the base JEPA importance weight is exactly 1.

Why this is preferable to cell-uniform proposal + reweighting:

The V5 analysis shows donor-uniform p under cell-uniform q has:
- max/min importance weight ratio ~2,149.5;
- effective sample-size fraction ~0.0968.

Sampling p directly avoids that avoidable variance.

### Why not source-donor-uniform by default

Source-donor-uniform would deliberately give every source equal scientific mass,
which is a stronger scientific claim: a donor in the 17-donor NPH52 source
would receive more source-level mass than a donor in HVS/SEA_AD.

That may be a legitimate sensitivity analysis, but the project's stated
scientific unit is donor recurrence. Equal-donor mass is therefore the cleaner
primary default.

This remains a recommendation until explicitly frozen by project authority.

## 4. Recommended relational scientific weighting

Relational triplet count is compute, not scientific mass.

For donor d with G_d estimable relational groups in the frozen update/population,
a natural donor-primary group weight is:

`w(d,g) = 1 / (104 * G_d)`

for each estimable group g of donor d.

Within each group:
- sample a finite fixed number of eligible anchored triplets using the reviewed
  finite sampler;
- average triplet loss within the group;
- combine group means using the scientific group weights above.

Therefore increasing a group's sampled triplet budget improves Monte Carlo
precision but does not increase its scientific mass.

If the group definition later moves from raw operator to a validated support
stratum, that mapping must be prospectively frozen before the schedule is
compiled.

## 5. Evidence/target policy remains a separate unresolved authority

Do not inherit historical 40%-within-measured masking as production biology.

The reader-fit supports range from:
- HVS: 18,736 measured scalar addresses;
- SEA_AD: 35,076.

The production evidence authority should separately freeze:

1. teacher native-support policy;
2. student comparable-evidence policy;
3. target-block construction;
4. optional support-perturbation/calibration arm.

A useful primary direction is to make the student's evidence dose comparable in
**absolute lawful measured information**, while keeping native-support teacher
context and preserving measured zero.

No numeric visible-gene dose or hidden-target reserve is frozen by this
recommendation.

## 6. Optimizer/EMA timescales

Do not copy per-update u205 meanings into a ~35,574-updates-per-full-pass regime.

Freeze desired timescales in scientific presentations/coverage units first,
then derive per-update optimizer/EMA parameters from the final effective update
size.

In particular, the production EMA half-life must be stored in presentations in
the V5 schedule authority and converted to a per-step momentum only after
effective cells/update is frozen.

## 7. One canonical RNG

Production V5 must name exactly one keyed RNG/dropout authority.

The current branch contains:
- Philox4x32-10 reference;
- a separate modular-hash keyed dropout proof primitive.

Do not permit both as interchangeable production RNGs.

Recommended direction:
- retain Philox as the canonical specification because it is an established
  counter-based construction and already has explicit counter-word semantics;
- implement a vectorized CPU/GPU version;
- prove it byte/mask-equivalent to the reference;
- retire the modular-hash function to historical/proof-only status.

## 8. Required next freeze artifacts

Before production training review:

1. `V5_SCIENTIFIC_ESTIMAND_AUTHORITY`
2. `V5_PROPOSAL_SAMPLER_AUTHORITY`
3. `V5_RELATIONAL_GROUP_WEIGHT_AUTHORITY`
4. `V5_EVIDENCE_TARGET_POLICY_AUTHORITY`
5. `V5_FULL_READER_SCHEDULE_AUTHORITY`
6. `V5_EXPOSURE_CHECKPOINT_AUTHORITY`
7. `V5_KEYED_RNG_AUTHORITY`
8. `V5_HARDWARE_COST_CALIBRATION_AUTHORITY`
9. one integrated production-update source/root
10. independent review package + PASS terminal

None of these grants protected-population or pathology access.
