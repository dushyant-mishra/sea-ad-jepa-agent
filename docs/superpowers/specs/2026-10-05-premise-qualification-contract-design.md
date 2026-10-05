# JEPA Premise Qualification and Real-RNA Target Contract — Audited Design V2

Date: 2026-10-05
Role: `PROSPECTIVE_SCIENTIFIC_GOVERNANCE_SPEC__PREFREEZE_ONLY`
Base: `main@874939b5e9dd34a4f195dcc163db90e9dd3eee11`
Status: `AUDITED_AFTER_TARGET_LINEAGE_CLOSURE__TRAINING_OFF`

## 0. Governing purpose

Freeze the scientific questions, comparison structure, claim boundaries, scale requirements and fail-closed decision logic that govern future target/representation work **before any deciding TRAIN-only real-RNA result is opened** and before synthetic results are allowed to tune verdict rules.

This specification does not authorize encoder training, EMA updates, Stage-A execution, 500K promotion, Stage 4, TEST opening, Morabito opening, target selection, representation selection or estimand selection.

The controlling premise is:

> Observable RNA != recoverable RNA structure != biologically supported state != transferable biological state != regulatory support != causal/interventional state.

Every transition must be separately tested.

## 1. Authority freshness is part of scientific governance

Canonical startup authority must move with the work frontier.

Binding rule:

`UPDATE_CANONICAL_SURFACE_WHEN_CURRENT_TASK_CLOSES_OR_NEXT_AUTHORIZED_TASK_CHANGES`

When a controlling task closes, blocks or is superseded, the canonical startup surface must be updated in the same change set or an immediate successor governance PR. A completed task must never remain advertised as current.

The terminal target-lineage reconstruction is complete and merged. It is historical authority, not the current task.

## 2. Premise gates P1-P6

### P1 — Target meaning

For every candidate, define the target independently of the architecture that predicts it.

Required declaration:
- object scope: transcriptomic/global/program/query-local/novelty-candidate/other;
- lawful measured quantities allowed to define it;
- forbidden quantities;
- whether it is observation-derived or independently biologically grounded;
- why matching it means more than hidden-scalar reconstruction, address identity or generic covariance.

Failure: `TARGET_MEANING_UNDEFINED`.

### P2 — Recoverability

Two recoverability concepts are mandatory and must never be conflated.

#### P2A — `TARGET_OBJECT_RECOVERABILITY`

For real RNA, estimate how much information about an **observation-defined target object** is available from the lawful partial-RNA view. This may be estimated without claiming the target is biological truth.

#### P2B — `BIOLOGICAL_TRUTH_RECOVERABILITY`

Use this term only where an independently defined biological truth exists, such as planted synthetic truth or genuinely independent validated ground truth. Real-RNA self-supervision alone cannot create this quantity.

Components may be classified as:
- `RECOVERABLE_FROM_VIEW`;
- `PARTIALLY_RECOVERABLE_FROM_VIEW`;
- `NONRECOVERABLE_FROM_VIEW`;
- `RECOVERABILITY_NOT_IDENTIFIED`.

A biologically important but nonrecoverable component is not a model failure. On real RNA, target-object recoverability is not evidence by itself that the object is biological.

### P3 — Structured-state test

No single-vector representation is privileged prospectively. Compare at minimum:

1. `GLOBAL_CELL_STATE`
2. `QUERY_LOCAL_STATE`
3. `PROGRAM_STATE`
4. `STRUCTURED_COMBINED_STATE`

For each family define extraction object, intended scope, what it may legitimately discard, shortcut controls, transport evidence and allowed claim level. Dimensionality remains unspecified and evidence-derived.

`cell_state` is an implemented object, not a qualified default winner.

### P4 — Technical identifiability

A candidate must demonstrate that apparent recoverable structure is not explained by easier technical/measurement structure.

Mandatory control families:
- address/gene identity;
- matched wrong-query/query exchangeability;
- capacity-matched global summary;
- source identity;
- operator identity;
- sequencing depth/library size;
- visibility/support/missingness pattern;
- normalization-mediated query leakage;
- donor/source imbalance;
- technical-only baselines;
- biology × operator interaction where the substrate supports identification.

Naive technology invariance is not a requirement. State-dependent observation effects may exist and must be measured rather than erased by definition.

### P5 — Transport and target population

Transport is **not one nested pass ladder**. Track separate evidence axes:

- `DONOR_TRANSFER`
- `OPERATOR_TRANSFER`
- `STUDY_TRANSFER`
- `TECHNOLOGY_TRANSFER`

Claims must state which axes were tested, which passed, which failed and which were not identifiable because of confounding or missing support. Missing higher-level evidence is never converted into a pass.

Separately, the foundation-population estimand must be declared before production training: cell-weighted, donor-weighted, source-balanced donor-weighted, or another prospectively justified estimand. Until deliberately selected it remains `UNSET_REQUIRES_APPROVAL`.

### P6 — Claim boundary

Four primary claim levels are kept separate:

1. `RNA_REPRESENTATION`
2. `TRANSFERABLE_BIOLOGICAL_STATE`
3. `REGULATORY_SUPPORT`
4. `CAUSAL_PERTURBATIONAL_PREDICTION`

No lower level automatically promotes a higher one.

Stage A can qualify at most a lawful, nonshortcut, recoverable **RNA representation candidate**. Biological semantics require independent evidence after target selection.

## 3. Stage-A real-RNA prefreeze contract

Canonical status:

`PREFREEZE_EXECUTION_CONTRACT__NOT_EXECUTION_AUTHORITY`

Stage A is target/representation discrimination, not encoder training.

### 3.1 Hard execution boundaries

- encoder optimizer updates = 0;
- predictor/encoder training updates = 0 except prospectively approved diagnostic readouts under §3.5;
- EMA teacher updates = 0;
- no legacy checkpoint warm start as biological authority;
- TEST remains sealed;
- Morabito remains protected;
- external-validation assets are not used to choose the target;
- no pathology outcome is opened for target selection;
- no execution until all required open governance fields are prospectively closed by a separate authority decision.

### 3.2 Legality gate — absolute fail

Immediate `FAIL_LEAKAGE` if the hidden answer reaches the target or permitted evidence through direct value access, teacher pre-context access, normalization-mediated dependence, support/missingness, deterministic transforms or any equivalent leakage seam.

### 3.3 Shortcut gate — absolute fail

A biological qualification rule is invalid if an address-only, wrong-query, global-summary, source/operator/depth/support-only, technical-only or biology-absent/covariance-only control can satisfy it.

### 3.4 Recoverability-aware RNA gate

Report, without semantic overclaim:
- `TARGET_OBJECT_RECOVERABILITY` where estimable;
- candidate recovery;
- recovery relative to recoverable target-object information;
- biological-unit uncertainty;
- global RNA structure recovery;
- query/local RNA structure recovery;
- program RNA structure recovery;
- rare/novel RNA structure behavior where defensibly measurable.

Do not rename rare/novel RNA structure as biological novelty until independent evidence supports that interpretation.

### 3.5 Fitted diagnostic firewall

Any fitted diagnostic/readout used during target discrimination must:
- fit only on a prospectively defined inner-TRAIN partition;
- freeze hyperparameters, features and target definition before held-donor evaluation;
- never fit on the units used for its deciding evaluation;
- never permit target-definition changes based on deciding readout outcomes;
- carry provenance for fit units, evaluation units and all tuning decisions.

A fitted readout is diagnostic evidence, not encoder training authorization.

### 3.6 Transport gate

At minimum report held-donor performance with donor-level uncertainty where the chosen estimand requires donor inference. Operator/study/technology transfer are reported as separate axes where identifiable.

Allowed statuses include `PASS`, `FAIL`, `NOT_TESTED`, `NOT_IDENTIFIABLE_UNDER_CURRENT_CONFOUNDING`; `NOT_TESTED` and `NOT_IDENTIFIABLE` are never coerced into pass.

### 3.7 Stage-A verdicts

Allowed top-level verdicts:
- `QUALIFIED_FOR_RNA_REPRESENTATION`
- `INFORMATIVE_BUT_NOT_QUALIFIED`
- `FAIL_LEAKAGE`
- `FAIL_SHORTCUT`
- `FAIL_TRANSPORT`
- `NONRECOVERABLE_FROM_VIEW`
- `INDETERMINATE`

`QUALIFIED_FOR_RNA_REPRESENTATION` does not authorize production training or confer transferable biological/regulatory/causal validity.

## 4. Prospective statistics and threshold discipline

Freeze before deciding outcomes are opened:
- comparison directions;
- paired comparison structure;
- biological resampling unit;
- estimand weights;
- multiplicity policy;
- negative-control roster;
- stop/fail conditions;
- metric definitions;
- representation extraction definitions;
- readout fit/evaluation partitions.

Numeric margins may be fixed only from pre-existing independent authority or a prospectively approved calibration procedure that does not inspect deciding candidate outcomes. Otherwise they remain `UNSET_REQUIRES_APPROVAL`.

Cell count never substitutes for biological-unit count.

## 5. Synthetic evidence classes and dimensional-scale firewall

### 5.1 World A / 96-feature class

The locked 96-feature World A is classified:

`REDUCED_MEASUREMENT_AND_METRIC_CONTROL_WORLD`

Legitimate uses:
- generator/custody reproducibility;
- measurement/operator geometry;
- leakage and nuisance controls;
- simple recoverability methodology;
- negative-control sensitivity;
- oracle-normalized metric development where planted truth is explicit.

It is **not** a production-scale biological-state surrogate.

### 5.2 96-feature B/C/D prototypes

If B/C/D are instantiated in the 96-feature universe, their results may qualify only the behavior of the planted mechanism, metric or control in that reduced universe. They cannot qualify production architecture behavior over the canonical Molecular Ledger.

### 5.3 Production-pipeline synthetic qualification requirement

Any synthetic result used to justify behavior of the actual canonical JEPA pipeline must use:

`CANONICAL_41238_ADDRESS_SYNTHETIC_UNIVERSE`

or a prospectively justified equivalent identity universe with an explicit lawful mapping and proof that it preserves the shortcut/dimensional opportunities relevant to the 41,238-address runtime.

The preferred production-premise worlds are therefore `B41K`, `C41K`, and `D41K`.

Minimum scale/structure requirements:
- all 41,238 canonical addresses physically present with the same identity vocabulary used by the tokenizer;
- heterogeneous abundance and long-tail expression/support;
- gene-specific detectability and operator-specific support;
- dense and sparse biological programs;
- partially overlapping/redundant modules;
- rare/local programs;
- distributed covariance;
- nonlinear interactions where relevant;
- realistic opportunities for identity, support and covariance shortcuts.

Simply padding a 96-feature simulator with 41,142 independent noise genes **does not** satisfy this requirement.

No arbitrary `ENSG_SYN_* -> canonical address` assignment is permitted. If synthetic biology is planted on canonical identities, the assignment and biological meaning must be prospective and documented before evaluation.

### 5.4 Synthetic claim boundary

Synthetic success proves only that the method can recover or reject **known planted structure under the simulated conditions**. It does not prove real biological validity.

Oracle ceilings may be measured before JEPA evaluation because they define recoverability denominators. If measured ceilings contradict the prospectively designed class, the simulator is repaired or withdrawn; the class is not reinterpreted after model results.

## 6. External semantic validation boundary

RNA self-supervision can establish lawful recoverable RNA structure but cannot confer biological semantics by itself.

External assets are used only after target selection for the claim transition they can legitimately test. Task 5 must consolidate existing audited evidence from PRs #188–#199 rather than repeating completed audits; unsupported fields remain `UNKNOWN_REQUIRES_AUDIT`.

Previously exposed assets are not called pristine independent validation. Morabito remains `PROTECTED_NOT_AVAILABLE_FOR_SELECTION`.

Support is not qualification unless a prospectively defined integrated rule says exactly what evidence closes a claim transition.

## 7. Vocabulary boundaries

Use:
- `recoverable transcriptomic state` / `recoverable RNA structure` for Stage-A RNA-only objects;
- `candidate biological novelty` only after independent evidence begins to support rare/novel RNA structure;
- `transferable biological state` only after independent semantic/transport qualification;
- `regulatory support` only after independent regulatory/chromatin evidence;
- `causal/counterfactual prediction` only after intervention evidence.

`pathology-label blind` means pathology labels are absent from optimization; it does not mean pathology-associated biology is absent from RNA.

`molecule-subsampling stability` is not independent remeasurement stability.

The 41,238-address Molecular Ledger is the lawful RNA observation universe, not complete cellular molecular state.

## 8. Stop conditions

STOP rather than tune thresholds if:
- target meaning is undefined;
- nonrecoverable information is treated as model failure;
- target-object recoverability is promoted to biological-truth recoverability without independent truth;
- technical-only, identity-only or biology-absent/covariance-only controls pass the biological rule;
- rare RNA novelty is called biological novelty without independent support;
- cross-modal validation reuses information given to the model;
- a result depends materially on arbitrary synthetic-to-41K identity mapping;
- a 96-feature result is promoted into production-scale pipeline qualification;
- 41K scale is satisfied only by padding with independent nuisance genes without reproducing relevant structural opportunities;
- training loss or masked-RNA success is used as biological-state proof;
- a lower claim level is promoted automatically;
- a deciding threshold is chosen after deciding outcomes are visible;
- a completed task remains advertised as current authority.

## 9. Required artifacts before any production-training decision

1. target-meaning declaration for every candidate;
2. target-object recoverability assessment where estimable;
3. independent biological-truth recoverability only where genuine truth exists;
4. frozen representation comparison;
5. leakage seam audit;
6. shortcut/negative-control specification;
7. transport axes and biological resampling unit;
8. foundation-population estimand declaration;
9. frozen metric/verdict/readout-partition contract;
10. requested claim level;
11. production-scale synthetic qualification evidence if synthetic evidence is used to justify canonical pipeline behavior;
12. explicit list of what remains untested.

Only a separate later authority may convert this prefreeze governance into narrow execution permission.

## 10. Non-authority statement

This document selects no target, representation, network width, biological dimension, estimand, threshold or production architecture winner. `TRAINING=OFF`; `MULTIMODAL_TRAINING=OFF`; `500K=NOT_AUTHORIZED`; `STAGE4=NOT_AUTHORIZED`; `TEST=SEALED`; `MORABITO=PROTECTED`; `STAGE_A_EXECUTION=NOT_AUTHORIZED__PREFREEZE_ONLY`.
