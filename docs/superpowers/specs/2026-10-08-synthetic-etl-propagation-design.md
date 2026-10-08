# Synthetic ETL → generator propagation design

Status: **PROSPECTIVE DESIGN / NON-AUTHORIZING / NO GENERATOR CODE CHANGES**  
Date: 2026-10-08  
Base branch: `claude/s174-train-cache-rebuild-20261007`  
Base merge checkpoint: `f88338713b173edb3acbc90662e607ce45b5878b`  
Design branch: `design/synthetic-etl-propagation-contract-20261008`

## 1. Purpose

Repair one specific synthetic-dataset defect: corrected TRAIN calibration measures broad cell-class composition and class-conditioned structure, but the V73/V77 synthetic truth path does not physically carry `broad_cell_class` or condition biological programs on class.

This design does **not** authorize training, optimizer mutation, runtime changes, target-discovery changes, 353-ID remapping, TEST/Morabito access, 500K, Stage 4, production EMA selection, or production estimand selection.

The first experiment asks only:

> If broad cell class is propagated into synthetic truth and given an outcome-blind random-content biological program, does the synthetic world move toward the corrected real class-separation geometry without breaking population/measurement structure that is already working?

## 2. Evidence motivating the change

`build_v77_real_calibration.py` reads pathology-blind TRAIN metadata containing `broad_cell_class`, records class counts, and explicitly says cell-class composition is intended to make synthetic cell identity carry realistic dominance. It preserves the rule **real geometry, random content**: real program membership is not planted.

`build_v73_sharded_master_truth.py` currently writes cell identity, donor, source, operator, World-A biological latents, and technical latents, but no broad-cell-class truth variable.

`build_v77_extended_truth.py` adds state, donor, rare-state, pseudotime, marker, partial-recoverability, interaction, regulatory, spatial and perturbation components. Those cell-level biological components are keyed to cell identity (or donor for B2), not to an annotated broad class.

The corrected S174 replay reports:

- real T5 within-class / pooled correlation ratio: about `0.7435`;
- replayed synthetic arms: about `1.02–1.21`;
- no replayed arm spans the corrected real T5 point;
- current substate mechanisms are independent of annotated broad class by construction.

The same replay also shows that abundance and depth remain badly mismatched in several historical dynamic-range arms, so T5 must not be optimized in isolation.

## 3. Design principles

1. **Minimal propagation, not simulator replacement.** Keep the authenticated FULL104 source/donor/operator geometry and frozen observer/counting mechanics unchanged for the first class-propagation experiment.
2. **Real geometry, random content.** Real class prevalence may determine synthetic class counts. Real gene identities, real class marker lists, real regulatory programs and pathology labels may not be planted.
3. **Separate biology from measurement.** Broad class is biological truth. Operator remains an observation/support variable. The first causal ablation must not implement `operator -> class` or treat matrix/operator ID as a biological axis.
4. **Outcome-blind effect scale.** New class-program scales are inherited from already-declared V77 mechanism scales, not tuned against corrected T5.
5. **Preserve within-class variation.** A lower T5 obtained by making each class a deterministic block is not an acceptable repair.
6. **No hard S159 gate.** Corrected real point estimates are descriptive references; current S159 p05–p95 intervals remain uncertainty diagnostics, not binary qualification thresholds.
7. **No JEPA training in this phase.** First validate the synthetic worlds themselves.

## 4. Approaches considered

### Approach A — minimal class propagation with frozen observer (**selected**)

Carry an explicit broad-class truth variable, reproduce corrected TRAIN global class composition, and add class-conditioned random-content expression programs using existing V77 effect-scale conventions. Keep donor/operator assignment and the observer fixed.

Advantages:

- isolates the suspected missing biological mechanism;
- preserves existing population and measurement machinery;
- does not require importing real gene programs;
- gives a clean E0→E1→E2→E3 causal sequence.

Limitation: initial class assignment is intentionally independent of donor/operator. It is a causal ablation, not a claim that the final synthetic population reproduces the real joint class×operator sampling distribution.

### Approach B — immediately reproduce empirical class×source/operator joint sampling

Derive a richer joint class-support authority and condition synthetic class assignment on measurement groups.

Deferred because operator semantics are not a common cross-source biological axis: HVS/NPH52 operators can be class-pure while SEA-AD operators are multi-class. Introducing this in the first experiment would mix biological class propagation with measurement/sampling coupling and make the causal result harder to interpret.

A later contract may test joint sampling geometry if Approach A demonstrates that class propagation matters.

### Approach C — continue dynamic-range/counting tuning

Rejected for this experiment. The corrected replay already shows that the historical arm family can move many covariance/topology statistics while still failing class separation, abundance and depth. More counting-scale tuning does not supply the missing broad-class generative mechanism.

## 5. Frozen E0–E4 experiment family

### E0 — current generator

Unmodified current V77 generator and current frozen observer. This is the reference control.

### E1 — class composition only

Add `broad_class_index` to hidden truth with the corrected TRAIN class proportions, but **do not allow class to alter expression**.

Purpose: prove that merely attaching labels/composition does not manufacture the desired covariance structure.

Expected mechanistic result: observed expression/count realizations remain byte-/digest-equivalent to E0 when all other seeds and settings are identical; only hidden class truth and class-dependent scoring metadata differ.

### E2 — class-shared random-content program

E1 plus one random-content class-shared expression program per broad class.

Mechanism:

- use a new disjoint truth/observer stream block reserved for class propagation;
- create one class-specific dense random loading vector over the synthetic panel using the existing V77 `_dense` construction;
- inherit the existing B1 state scale `SC["state"] = 0.55` exactly;
- class contribution is selected by `broad_class_index`;
- no real gene symbols, Ensembl IDs, marker lists or regulatory edges are used to choose loading content.

Purpose: test whether broad class can contribute to pooled covariance while leaving existing within-class generic biology intact.

### E3 — E2 plus explicit within-class continuous biology

E2 plus a two-dimensional continuous latent state within each broad class.

Mechanism:

- two standard-normal per-cell coordinates from a new disjoint stream block;
- each broad class receives its own two random dense loading vectors;
- aggregate scale is normalized outcome-blind so the two-dimensional continuous term has the same nominal RMS effect budget as one B1 state term: each dimension uses `SC["state"] / sqrt(2)`;
- the coordinates vary within class and are independent of donor, source and operator.

Purpose: ensure class separation is not achieved by collapsing biologically meaningful within-class covariance.

### E4 — E3 plus donor×class interaction

Frozen as a **later ablation**, not executable in the first implementation/replay PR.

Proposed mechanism:

- one deterministic standard-normal latent value per `(donor, broad_class)` pair from a disjoint stream;
- random dense loading content;
- inherit existing donor effect scale `SC["donor"] = 0.45`;
- no operator/source keying.

E4 may be authorized only after E0–E3 are scored and reviewed, because bundling donor×class structure into the first repair would make attribution ambiguous.

## 6. Broad-class assignment contract

### Authority

The only biological authority for class prevalence in E1–E4 is corrected, pathology-blind TRAIN `broad_cell_class` metadata already consumed by the corrected V77 real calibration.

The implementation must create a small hash-bound class-composition authority artifact that records:

- corrected calibration source identifier and SHA;
- ordered broad-class labels;
- exact TRAIN counts and proportions;
- total TRAIN cells represented;
- explicit statement that no pathology-like fields were read;
- implementation version/schema.

### Synthetic allocation

For a synthetic world of `N` cells:

1. convert frozen TRAIN class proportions to integer class quotas using deterministic largest-remainder allocation;
2. deterministically permute class assignments over global cell IDs using a new class-assignment stream;
3. class assignment must be shard-invariant;
4. assignment must not read donor, source, operator, expression values, query values, pathology fields, target-discovery artifacts or real gene identities.

This deliberate independence makes E1–E3 a clean biological-mechanism ablation. It is not a final claim about real class×measurement sampling geometry.

## 7. Observer/counting freeze

For E0–E3 the following remain unchanged:

- FULL104 source quotas;
- 104-donor population geometry;
- 42 observation operators;
- 1,400 donor×operator groups and ragged support;
- zero-quota rescue / 2K 42-of-42 operator support;
- operator-specific structural availability;
- World-A empirical depth/support targets;
- exact-count realization machinery;
- existing measurement seed rules;
- existing runtime/q-safety/provenance machinery.

The only observer change allowed for E2/E3 is addition of the preregistered class biological contribution to pre-count expression rate (`eta`). No counting parameter, availability rule, library-depth distribution, dynamic-range multiplier or operator support rule may be retuned.

## 8. Seed and stream rules

- Preserve existing generator seed behavior; the first exact-comparison run uses the historical seed already attached to the current world so E0 reproduction remains checkable.
- New class assignment, class-shared program, within-class continuous state and later donor×class interaction each receive disjoint stream blocks not used by existing V77 components.
- Stream identifiers are part of the implementation contract and must be recorded in output manifests.
- Historical seed reuse is **not independent confirmation**. Any later confirmation-seed study requires a separate frozen record before outcomes are read.

## 9. RED requirements before implementation

The implementation phase must begin with tests that fail against the current generator for the intended reasons.

Required RED assertions:

1. current V73/V77 hidden truth has no `broad_class_index` field;
2. no current V77 biological component is selected/conditioned by broad class;
3. a proposed class authority with pathology-like fields is rejected;
4. class quotas must reconcile exactly to `N` and be deterministic/shard-invariant;
5. class assignment must not change when shard size changes;
6. E1 must leave observable counts identical to E0 under identical seeds/settings;
7. E2 must create a class-dependent `eta` contribution while observer/counting configuration hashes remain unchanged;
8. E2 class-program content must be generated only from synthetic random streams, never from real gene-program identities;
9. E3 must show non-zero within-class continuous latent variance for every class with sufficient cells;
10. E3 must not key continuous state to donor/source/operator;
11. the 2K smoke must retain all 42 observation operators with minimum support >= 1;
12. output manifests must bind class authority SHA, generator source SHA, arm definition, seeds/streams and observer configuration;
13. E4 execution must fail closed unless separately authorized after E0–E3 review.

## 10. Frozen scoring panel

Score all arms on the same corrected evaluation universe and scoring implementation used by the corrected S174 replay.

Primary descriptive panel:

- expression median `|r|`;
- expression fraction `|r| > 0.3`;
- expression top-10-PC variance;
- detection median `|r|`;
- detection fraction `|r| > 0.3`;
- detection mean degree;
- detection transitivity;
- detection largest-community fraction;
- T5 within-class / pooled correlation ratio;
- abundance max / median nonzero;
- top-1% count share;
- median detected genes per cell.

Corrected real reference points currently recorded:

- expression median `|r|`: ~0.0562;
- expression fraction `|r| > 0.3`: ~0.0242;
- expression top-10-PC variance: ~0.262;
- detection median `|r|`: ~0.1946;
- detection fraction `|r| > 0.3`: ~0.1348;
- detection mean degree: ~404.36;
- detection transitivity: ~0.6672;
- T5: ~0.7435;
- abundance max/median: ~2273.21;
- top-1% count share: ~0.2741;
- median detected genes/cell: ~4495.5.

These are descriptive references, not independently valid binary thresholds.

## 11. Prospective interpretation and falsification rules

No arm is selected merely because its T5 is numerically closest to `0.7435`.

### E1 falsification check

If E1 materially changes expression/count outputs relative to E0, the class-label-only isolation contract is broken and implementation must stop.

### E2 mechanistic expectation

Relative to E1, E2 should introduce a real class contribution to pooled covariance, visible as a directional reduction in T5 and a change in class-conditioned geometry. If T5 does not move in the expected direction, the simple class-shared-program hypothesis is not supported.

E2 is also rejected as an adequate explanation if apparent T5 improvement is accompanied by gross deterioration across the predeclared expression, detection, abundance or depth panel, or is traceable to source/operator leakage.

### E3 mechanistic expectation

E3 must preserve measurable within-class heterogeneity while retaining a broad-class contribution to pooled structure. A lower T5 caused by near-deterministic class blocks or collapsed within-class variance is a failure, even if T5 is numerically close to the real point.

### Cross-arm ruling

The useful outcome is whether E1→E2→E3 establishes that the missing ETL-derived class mechanism moves the full corrected panel in a coherent direction without damaging already-correct population/measurement geometry.

If no arm does so, do **not** tune class-program magnitude against T5. Record the hypothesis as insufficient and design the next mechanism prospectively.

## 12. Shortcut and spillover diagnostics

Before any scientific interpretation:

- verify source/operator/donor are not inputs to class-program generation in E1–E3;
- report association of synthetic class with source/operator created accidentally by allocation; expected design target for E1–E3 is no intentional dependence beyond finite-sample chance;
- preserve existing nuisance/source/operator shortcut controls;
- preserve exact-twin / negative-control semantics where applicable;
- rerun the existing 2K operator-support regression;
- compare E0 against previously committed current-generator output to detect unintended spillover.

## 13. Implementation boundaries

The first implementation successor may add only what is necessary for E1–E3:

- a class-composition authority artifact/builder;
- class assignment in hidden truth;
- E1/E2/E3 arm switches/configuration;
- class biological contribution in the V77 observer;
- RED→GREEN unit/integration tests;
- synthetic scoring/replay records.

It must not modify:

- canonical runtime / optimizer / EMA / checkpoint code;
- q-safety or physical provenance contracts;
- target-discovery artifacts;
- corrected real cache contents;
- 353 historical identity mappings;
- existing World-A frozen files in place if the established pattern requires a successor file;
- production training authority.

## 14. Execution order after design approval

1. write RED tests for missing broad-class truth and isolation invariants;
2. implement class-composition authority and E1 only;
3. prove E1 observable equivalence to E0 and 2K operator preservation;
4. implement E2 using inherited `SC["state"] = 0.55` and disjoint streams;
5. run E0–E2 synthetic replay on the frozen scoring panel;
6. self-audit before E3;
7. implement E3 with fixed two-dimensional within-class continuous mechanism;
8. rerun the same scoring panel without parameter tuning;
9. record SHAs, config hashes, outputs and CI receipts;
10. review whether E4 merits separate authorization.

## 15. Completion criterion for this scientific step

This step is complete when E0–E3 have been implemented under the frozen contract, their structural tests and spillover checks are green, and the same corrected multi-statistic panel has been reported without post-outcome retuning.

Completion does **not** imply:

- a synthetic arm is selected for production;
- S159 is resolved;
- another optimizer update is authorized;
- real-data training is authorized;
- representation/target/EMA choices are frozen.
