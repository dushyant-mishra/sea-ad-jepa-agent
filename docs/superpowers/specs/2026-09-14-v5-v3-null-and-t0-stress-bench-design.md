# V5 V3 null and T0 stress-bench design

Date: 2026-09-14
Status: `DESIGN_FOR_REVIEW__NO_D_SHARED_OUTCOME_ACCESS__NO_T0_REOPEN`

## Purpose

Design a successor measurement/null framework for V5 after FULL104 reconnaissance established that the V2 exact matching key `(donor, operator, Q_DEPTH_COUNT, Q_DETECT_COUNT)` is technically lossless but scientifically unusable: 99.911% of cells are singleton strata and the frozen permutation is therefore almost always the identity.

The successor must preserve the project rule:

`UNDERSTAND_FULL104_DEEPLY__KEEP_FINAL_D_SHARED_HYPOTHESIS_TEST_SEALED`

and must not turn retrospective T0 information into V5 confirmatory authority.

## Immutable boundaries

1. Do not execute or inspect current-V5 D_shared decision-bearing outcomes.
2. Do not execute D_private, D_obs, TD60, relational activation, training, or protected/pathology confirmation.
3. T0 V20 and its frozen closeout remain immutable. The terminal `RARE_TAIL_UNDERDETERMINED_MEASUREMENT` stands.
4. A T0-V3 sandbox may reject a candidate mechanism but may not certify it for FULL104/V5.
5. Fresh/sealed T0 confirmation data (`reader_validation`, fresh AT8, oracle/protected data) remain closed.
6. Any V3 numeric thresholds used for V5 decision authority must be frozen from FULL104 outcome-blind structural information and measurement-control qualification, not optimized against historical T0 outcomes.
7. No arbitrary post-hoc depth/detection bins are allowed.

## Governing scientific problem

FULL104 reconnaissance established four interacting facts:

- operator/source structure is a dominant nuisance axis;
- depth and detection correlate substantially with the derived features;
- exact depth/detection matching degenerates into near-unique cell identifiers;
- A/B are independent hash projections of the same molecular address space, not independent molecular measurements.

The design therefore separates four jobs that V2 tried to make one matching key perform:

1. **measurement robustness** — does the representation move when only measurement quality changes?
2. **nuisance neutralization** — can operator/source/depth/detection explain the putative shared structure?
3. **exchangeability/null construction** — can the shared relationship be broken without destroying the real technical geometry?
4. **independent-view corroboration** — does the result recur across genuinely partially disjoint molecular visibility patterns?

## Architecture

### Component A — same-cell counterfactual measurement intervention

Primary candidate.

For a fixed observed cell, create deterministic measurement-counterfactual variants by modifying only measurement availability/intensity under a prospectively frozen intervention family. Candidate operations are controlled thinning and/or visibility masking that preserve cell identity, donor, operator, source, and the original molecular state as the parent.

The mechanism must emit paired `(original, counterfactual)` observations and a displacement metric. It must never replace a cell with another cell and therefore cannot create singleton matching strata.

The qualification question is not whether biological features are uncorrelated with QC. It is:

> Holding biological identity fixed, does changing only the measurement process materially alter the biological conclusion?

This carries forward the frozen T0 lesson that biological state may legitimately correlate with RNA complexity.

### Component B — explicit nuisance comparator / residualized comparator

Fit a nuisance-only model using only outcome-blind technical variables permitted by authority (operator/source/study/technology/depth/detection/support geometry as applicable). The comparator must be evaluated on exactly the same population/folds as the candidate shared measurement.

Two outputs are required:

- nuisance-only predictive/explanatory performance;
- incremental candidate performance beyond nuisance.

Residualization is a comparator, not automatically the production representation. The project must not silently remove biology that is correlated with QC.

### Component C — blocked relationship-breaking null

Construct a null that preserves the important technical geometry but breaks the cross-view/shared relationship.

The first admissible blocking axes are frozen structural variables rather than learned outcome-informed clusters. Candidate blocks may use donor, operator, source/study/technology, operator support pattern, and mask-view identity only when the resulting exchangeability argument is explicit and occupancy is adequate.

The null must:

- move a substantial fraction of eligible observations;
- report exact movable/non-movable fractions;
- preserve block marginals by construction;
- use deterministic RNG binding;
- full-refit the measurement procedure per replicate where the estimator requires it;
- count estimator failures unconditionally.

A null with identity-map behavior comparable to V2 is nonqualifying even if mathematically well defined.

### Component D — common-core / operator-native dual analysis

Use the 17,186-address common measured core as a clean operator-comparable baseline while preserving an operator-native analysis that retains all lawful measured information.

This is a two-sided anti-shortcut design:

- if a signal exists only in operator-native space and disappears in the common core, operator-specific measurement structure is a plausible explanation;
- if a signal survives both, confidence increases that it is not an artifact of operator-specific support.

The common-core result is a comparator/qualification channel unless a later authority explicitly promotes it to production geometry.

### Component E — independent-view correction

Do not use A↔B as the primary independent-measurement corroboration because both hash the same molecular address space.

Use the four 60%-visible mask views as the partially disjoint visibility axis. Qualification must quantify actual pairwise address overlap and bind view construction. A/B may remain useful as independent sketch/hash mechanics but must be labelled as such.

### Component F — outcome-blind rank-support restriction

Do not inherit ranks `1..512` as automatically scientifically supported when pooled covariance is singular and effective dimension is far smaller.

A successor authority may restrict the candidate rank envelope prospectively using outcome-blind structural criteria such as:

- nonzero/supportable covariance rank;
- spectral-entropy/participation-ratio summaries;
- variance-capture thresholds;
- numerical stability of the metric under frozen ridge perturbations.

The exact rule must be frozen before any D_shared rank curve is opened. Ridge must not create dimensions unsupported by the data.

### Component G — real-geometry positive/negative qualification

Before real D_shared, the complete successor procedure must pass:

1. real-geometry strict negative controls;
2. real-geometry controlled positive shared-signal injections;
3. a prospectively frozen difficulty/detection curve;
4. unconditional estimator-failure accounting;
5. donor influence / leave-one-donor diagnostics;
6. matched nuisance/simple comparator;
7. identity-null/mobility diagnostics;
8. common-core/operator-native concordance diagnostics;
9. mask-view reproducibility diagnostics.

The FULL104 reconnaissance already supplies outcome-blind variance/SE/runtime scales sufficient to choose a prospective control grid without D_shared access.

## T0-V3 methodological stress bench

### Role

T0 is a retrospective falsification and calibration bench only.

A candidate V3 mechanism may be discarded if it fails T0 stress tests. Passing T0 does not authorize it for V5; it only permits progression to FULL104 real-geometry qualification.

### Allowed T0 inputs

- frozen V20/V21 development artifacts already opened historically;
- immutable code paths and frozen historical measurement artifacts;
- synthetic fixtures generated from declared T0 geometry;
- previously published/recorded T0 outcomes only for retrospective falsification labels, never for tuning V5 thresholds.

### Forbidden T0 inputs

- fresh `reader_validation` outcomes;
- sealed/oracle/protected pathology values not already opened under historical authority;
- any modification of the frozen V20 result or terminal;
- using T0 pass/fail to set V5 numerical thresholds.

### Stress tests

#### T0-A strict null calibration

Run the complete candidate null/mechanism under synthetic no-signal geometries with whole-procedure reruns. Check empirical false-positive behavior, null spread, failure rate, and mobility.

#### T0-B controlled positive signal

Inject a known signal across a frozen ladder and quantify recovery. The ladder is a sandbox property and must not be copied into V5 without independent FULL104 justification.

#### T0-C same-cell measurement intervention

Apply the candidate thinning/masking intervention to the same underlying cell/state and verify that nuisance perturbation behaves as intended. Measure whether the biological summary is stable over a frozen intervention ladder.

#### T0-D known rare-tail falsification challenge

Use the historically known depth-fragile rare-tail failure as a negative/falsification challenge. A mechanism that confidently certifies the already-refused rare-tail without explaining the historical measurement failure is nonqualifying.

#### T0-E broad-state non-destruction check

The historically broad immune-state association may be used only as a non-destruction diagnostic: a candidate mechanism should not be selected because it reproduces the old positive, but catastrophic loss of a robust broad-state signal under mild measurement intervention is evidence of an overly destructive nuisance control.

#### T0-F cross-fit variance-inflation challenge

Replay the known whole-pipeline null calibration problem. The candidate framework must distinguish association evidence from effect-transport authority and must not treat HC3 studentization or permutation significance as a transportable effect magnitude.

## Candidate-family comparison

The sandbox compares three null/control families under the same diagnostic contract:

1. `SAME_CELL_COUNTERFACTUAL_MEASUREMENT_V1` — primary candidate;
2. `NUISANCE_CONDITIONED_BLOCKED_PERMUTATION_V1` — secondary candidate;
3. `COARSE_STRUCTURAL_BLOCK_PERMUTATION_V1` — secondary/negative-control candidate using only frozen discrete structural axes.

Prospective coarsened depth/detection bins and continuous nearest-neighbor matching remain research alternatives, not initial production candidates. They may be evaluated only if the three primary families fail, with their metric/radius/bin rules frozen before execution.

## Common diagnostics for every candidate

Every candidate must emit:

- population and eligible-population counts;
- changed-vs-identity fraction;
- per-donor/operator/source mobility;
- nuisance-balance deltas;
- null mean/spread/tails under synthetic controls;
- positive-control recovery curve;
- unconditional failure counts;
- donor influence / top-k concentration;
- simple/nuisance comparator;
- deterministic seed/input/script hashes;
- explicit authority classification.

No survivor-only summaries are allowed.

## Promotion rule

A candidate progresses from T0 sandbox to FULL104 qualification only if it:

1. has adequate null mobility;
2. controls strict-null false positives under the complete procedure;
3. recovers controlled signal over a prespecified range;
4. does not turn known T0 measurement pathology into confident biology;
5. does not erase robust signal merely because biology correlates with QC;
6. keeps association evidence separate from effect-transport claims;
7. has deterministic, auditable implementation and complete failure accounting.

A FULL104 successor authority is still required after this promotion. T0 passage alone never sets `d_shared_real_outcome_access_authorized=true`.

## Implementation decomposition

This architecture will be implemented as separate reviewable units:

1. T0-V3 sandbox authority + receipts + firewall tests.
2. Same-cell counterfactual intervention producer + synthetic qualification tests.
3. Nuisance-conditioned comparator/null producer + synthetic qualification tests.
4. Structural blocked-permutation producer + mobility/occupancy tests.
5. Common-core/operator-native comparator contract.
6. Mask-view independence contract and overlap evidence binding.
7. Outcome-blind rank-support authority contract.
8. Unified real-geometry measurement-qualification contract.
9. Red-team/mutation tests proving T0 cannot confer V5 authority and no D_shared outcome path opens.

## Success state

The work is complete only when there is a prospectively frozen, independently reviewable successor measurement-qualification design that can be exercised first on T0 as a falsification bench and then on FULL104 controls, while all real D_shared decision-bearing outputs remain sealed.
