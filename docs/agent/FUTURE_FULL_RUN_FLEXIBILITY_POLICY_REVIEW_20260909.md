# Future full-run flexibility policy review — Target Discovery + Teacher/Student V5

Date: 2026-09-09
Status: `DESIGN_REVIEW__NO_EXECUTION_AUTHORITY`

## Decision

Future full-reader runs should be more flexible than T0 V20 in their **pre-freeze design phase**, but not flexible after decision-bearing evidence is opened or after a production teacher/student optimizer run begins.

```text
FLEXIBLE_BEFORE_FREEZE = true
FLEXIBLE_AFTER_OUTCOME_OR_DECISION_EVIDENCE = false
FLEXIBLE_AFTER_PRODUCTION_TRAINING_START = false
TRAINING_AUTHORIZED = false
CONFIRMATION_AT8_AUTHORIZED_BY_THIS_REVIEW = false
TD60_AUTHORIZED_BY_THIS_REVIEW = false
```

The rule is not “never adapt.” The rule is:

```text
Adapt broadly while the evidence source is design/calibration-only and outcome-blind.
Freeze exactly before the evidence becomes decision-bearing.
If adaptation uses outcome-bearing discovery data, demote that run to design evidence and start a new frozen run.
```

## Why this review exists

T0 Stage 2 selected the maximum pre-registered ridge multiplier exponent `2.0`. That was lawful because the grid was frozen, but it exposed a design lesson: for future full runs, we should not make narrow grids, budgets, horizons, or schedule constants the reason a scientifically promising run becomes underpowered or ambiguous.

The better future pattern is a two-layer authority:

1. **Exploration/calibration layer** — flexible, explicitly non-decision-bearing, preferably outcome-blind or using only released discovery outcomes with the run demoted to design evidence.
2. **Confirmatory freeze layer** — no adaptive redesign, no hidden fallback, no grid expansion, no changing endpoints/thresholds after decision evidence is opened.

## Target Discovery review

The established Target Discovery result is not a fixed coordinate target. The qualified object is relational geometry:

```text
relation = anchored triplet ordering sign(d(i,j) - d(i,k))
distance = direct 160-D cell_state cosine distance
absolute_distance_equality_required = false
scale_free = true
```

What survived:

- TD57B: foundational/global donor-recurrent scale-free relational order, 24/24 cases passed.
- TD59: nearest-half mesoscale recurrence, 24/24 cases passed under its frozen pilot criterion.

What failed or remains constrained:

- TD57C nearest-third fine-locality was not stable enough to become the primary target.
- TD59 nearest-half is pilot mesoscale evidence, not a production locality fraction.
- TD60 is prospective only and must wait for a lawful full-reader exposure-defined learned teacher checkpoint.

### Target Discovery flexibility recommendation

For future full runs, Target Discovery should support flexible **pre-freeze** design around:

- candidate locality scales and neighborhood fractions;
- null definitions and fine-stratum matching;
- triplet budget and Monte Carlo precision;
- recurrence statistics and confidence criteria;
- donor/source/operator stratification for robustness;
- common-core versus native-support basis comparisons.

But once a Target Discovery run is marked decision-bearing, freeze:

- relation family;
- distance metric;
- locality fraction or scale grid;
- triplet/null construction;
- donor/source/operator panels;
- pass/fail criterion;
- all thresholds and multiplicity rules.

Future target discovery should include a formal `DESIGN_GRID_WIDE_ENOUGH_AUDIT` before any outcome-bearing or confirmation-like test. The audit should ask whether a boundary selection would be scientifically uninterpretable. If yes, widen the grid **before** opening decision evidence, not afterward.

## Teacher/Student V5 review

V5 correctly moved away from mechanics-sample constants and toward data-first authority. Current V5 principles that should remain:

- the dataset defines support and estimability;
- donor-uniform target mass, not raw-cell mass;
- donor×operator groups are admissibility/robustness structure, not equal scientific mass;
- common-core and operator-native support are separate evidence families;
- support/operator/depth are observation-state facts, not free biological identity shortcuts;
- proposal `q` is separate from target `p` and requires exact `p/q` correction when different;
- compute packing may not change target mass, proposal mass, selected cells, masks, singleton identity, or EMA exposure unit;
- EMA is expressed in successful base-cell presentations, not optimizer-update count;
- historical u10--u205 checkpoints are quarantined and cannot be resumed or used as biological teacher authority.

### Student/Teacher flexibility recommendation

V5 should be flexible before training authority around:

- proposal-family mixture/grid over donor-uniform, source/operator coverage, and variance-conditioned proposals;
- total presentation horizon and repeat-exposure limits;
- finite relational triplet budgets;
- common-core/native-support view counts and loss weights;
- singleton query budget and variance target;
- block sizes and visible/target dose;
- EMA half-life in presentation units;
- optimizer/update-size/token/microbatch geometry;
- hardware packing and GPU kernel choices;
- anti-collapse regularizer candidates such as SIGReg/VICReg-like variants, only after donor/source/operator-balanced calibration;
- checkpoint qualification thresholds for biology, shortcut, collapse, transfer, and residual preservation.

But V5 must freeze before production training:

- scientific target `p`;
- proposal `q` and exact `p/q` estimator;
- support-family definitions and weights;
- mask/keyed-RNG identity;
- singleton target/query identity;
- triplet sampling policy and budget;
- presentation horizon;
- EMA half-life and update chronology;
- mandatory 48-tensor protected-gradient/moment registry;
- atomic checkpoint telemetry schema;
- stopping and checkpoint qualification criteria;
- protected population gates.

## Proposed future full-run pattern

### Phase A — outcome-blind design calibration

Use only reader-fit metadata, support contracts, expression statistics, synthetic negative controls, and already-lawful public/calibration evidence. Optimize grids and candidate families here.

Required outputs:

```text
DESIGN_SPACE_MANIFEST
GRID_WIDTH_AND_BOUNDARY_AUDIT
SUPPORT_OPERATOR_SHORTCUT_ATLAS
PROPOSAL_P_Q_CONDITIONING_AUDIT
VIEW_MASK_DOSE_AUDIT
EMA_PRESENTATION_SCALE_AUDIT
GPU_PACKING_PARITY_AUDIT
ANTI_CHEAT_PROBE_PLAN
```

### Phase B — discovery sandbox, if needed

If a discovery outcome is used to decide that a grid is too narrow or a design should change, stop and mark the run:

```text
DISCOVERY_USED_FOR_DESIGN__NOT_CONFIRMATORY
```

Then freeze a new version before opening any confirmation or protected holdout. Do not call it the same decision-bearing run.

### Phase C — confirmatory freeze

Before confirmation/protected evidence or production training, freeze the full design. No grid expansion, hidden fallback, threshold movement, endpoint change, donor change, or mask change after this point.

### Phase D — atomic checkpoint qualification

Every future checkpoint must emit loss, mechanics, biology, shortcut, collapse, transfer, proposal, and hardware telemetry atomically. Loss decrease alone is not qualification.

## Concrete design-rule additions recommended

1. `DESIGN_GRID_WIDE_ENOUGH_AUDIT` — no decision-bearing run may open outcome evidence if critical selected values can land on an uninterpretable edge without a pre-declared fallback.
2. `BOUNDARY_SELECTION_POLICY` — if a boundary is selected during discovery, allowed actions must be predeclared: continue with caveat, stop as discovery-only, or trigger a separately frozen V-next; never silently expand and continue.
3. `EXPLORATION_CONFIRMATION_SEPARATION` — any outcome-adaptive redesign demotes the current run to design evidence.
4. `FLEXIBLE_PRETRAINING_AUTHORITY` — V5 can tune proposal/horizon/masks/EMA/hardware before optimizer execution using outcome-blind data and anti-cheat probes.
5. `NO_FLEX_AFTER_OPTIMIZER_START` — once production training starts, no scientific target, mask, proposal, EMA unit, checkpoint criterion, or anti-cheat threshold may change without starting a new run.
6. `MECHANICS_HEALTH_BEFORE_BIOLOGY` — fp16 forward is permitted only with backward outside autocast, unscale, 48-tensor gradient gate, optimizer-step proof, Adam-moment proof, then EMA.
7. `REAL_DATA_ANTI_CHEAT_BEFORE_TRAINING` — support-only, depth/QC-only, mask-only, donor/matrix/source/technology holdout, collapse, constant-vector/low-rank, proposal, and hardware-invariance probes must exist before training.
8. `NO_TEST_SKIP_GREEN` — torch-dependent or hardware-dependent tests must report executed/skipped separately; skipped critical tests are not a pass.

## Current execution decision

This review does not change active T0 Stage 2/3 handling. The current T0 V20 should proceed as frozen through R8 and confirmation if authorized by its own lane, with the ridge-boundary caveat recorded.

This review is for future full-reader Teacher/Student and post-T0 successor design.

```text
CURRENT_T0_V20_REDO_RECOMMENDED_NOW = false
FUTURE_FULL_RUN_SHOULD_HAVE_WIDER_PREFREEZE_DESIGN_GRIDS = true
```
