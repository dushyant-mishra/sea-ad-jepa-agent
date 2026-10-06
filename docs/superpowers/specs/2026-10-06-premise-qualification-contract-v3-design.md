# JEPA Premise Qualification and Real-RNA Target Contract — Audited Design V3

Date: 2026-10-06
Role: `PROSPECTIVE_SCIENTIFIC_GOVERNANCE_SPEC__PREFREEZE_ONLY`
Base: `main@102aa26730e4c2eda8b52a7532adee5332971e8b`
Status: `V3_DRAFT_FOR_PREFREEZE__TRAINING_OFF`

## 0. Purpose and authority boundary

This V3 extends the October-5 V2 premise contract without authorizing execution. It preserves P1-P6, representation neutrality, the claim ladder, Stage-A TRAIN-only target discrimination, external-asset role separation, and foundation-population estimand choice. It adds four controls that were not explicit enough in V2:

1. technology/assay as an **observation operator**, not a free biological covariate;
2. explicit **basis/subspace stability** requirements before coordinate-level biological interpretation;
3. separate **biological-evidence** and **measurement-depth** convergence curves;
4. separate **biological-support OOD** from **measurement-regime OOD**.

This document does **not** authorize encoder training, predictor training, EMA updates, Stage-A execution, TEST opening, Morabito opening, Stage 4, 500K promotion, target selection, representation selection, dimensionality selection, or estimand selection.

Hard state remains:

`TRAINING=OFF`
`MULTIMODAL_TRAINING=OFF`
`500K=NOT_AUTHORIZED`
`STAGE4=NOT_AUTHORIZED`
`TEST=SEALED`
`MORABITO=PROTECTED`
`TARGET_WINNER=NONE_QUALIFIED`
`REPRESENTATION_WINNER=NONE_QUALIFIED`

## 1. Governing scientific distinction

The claim ladder remains:

`OBSERVED_RNA`
→ `RECOVERABLE_RNA_STRUCTURE`
→ `RNA_REPRESENTATION`
→ `TRANSFERABLE_BIOLOGICAL_STATE`
→ `REGULATORY_SUPPORT`
→ `CAUSAL_PERTURBATIONAL_PREDICTION`

No transition is automatic.

`TARGET_OBJECT_RECOVERABILITY` is not `BIOLOGICAL_TRUTH_RECOVERABILITY`.

Real-RNA self-supervision can show that an observation-defined object is recoverable from lawful evidence. It cannot by itself prove that the recovered object is biological truth.

## 2. Premise gates P1-P6

### P1 — Target meaning

For every candidate define, before deciding results are opened:

- object scope: global transcriptomic, query-local, program/subspace, structured combined, or other;
- lawful measured quantities allowed to define it;
- forbidden quantities;
- whether the object is observation-derived or independently biologically grounded;
- why matching it means more than address identity, generic cell summaries, technical state, or hidden-scalar reconstruction.

Failure: `TARGET_MEANING_UNDEFINED`.

### P2 — Recoverability

Report separately:

- `TARGET_OBJECT_RECOVERABILITY` on real RNA;
- `BIOLOGICAL_TRUTH_RECOVERABILITY` only where genuine independent truth exists;
- candidate recovery relative to the recoverable portion of the target object.

Allowed component statuses:

- `RECOVERABLE_FROM_VIEW`
- `PARTIALLY_RECOVERABLE_FROM_VIEW`
- `NONRECOVERABLE_FROM_VIEW`
- `RECOVERABILITY_NOT_IDENTIFIED`

A biologically important but nonrecoverable component is not automatically a model failure.

### P3 — Representation-family tournament

No single-vector representation is privileged.

Exactly these four families remain mandatory for prospective comparison:

1. `GLOBAL_CELL_STATE`
2. `QUERY_LOCAL_STATE`
3. `PROGRAM_STATE`
4. `STRUCTURED_COMBINED_STATE`

For every family freeze:

- extraction object;
- intended biological scope;
- what information it may legitimately discard;
- shortcut controls;
- transfer axes;
- basis/subspace stability requirements;
- biological-evidence convergence requirements;
- measurement-depth convergence requirements;
- maximum allowed claim before external evidence.

`cell_state` is an implemented object, not a default winner.

`width=160` is architecture capacity, not biological dimensionality authority.

### P4 — Technical identifiability

Mandatory controls include:

- gene/address identity;
- matched wrong-query/query exchangeability;
- capacity-matched global summary;
- source identity;
- operator identity;
- sequencing depth/library size;
- visibility/support/missingness;
- normalization-mediated q leakage;
- donor/source imbalance;
- technical-only baselines;
- biology × operator interaction where identifiable.

The objective is not to erase all technology information. Measurement effects may legitimately alter observed evidence. The requirement is to prevent technical information from masquerading as biological state.

### P5 — Transport and target population

Track separately:

- `DONOR_TRANSFER`
- `OPERATOR_TRANSFER`
- `STUDY_TRANSFER`
- `TECHNOLOGY_TRANSFER`

No missing axis is promoted to PASS.

Foundation-population estimand remains `UNSET_REQUIRES_APPROVAL` until deliberately selected. Candidate estimands must include at least:

- cell-weighted;
- donor-weighted;
- source-balanced donor-weighted;
- a prospectively justified hierarchical alternative.

### P6 — Claim boundary

Primary claim levels:

1. `RNA_REPRESENTATION`
2. `TRANSFERABLE_BIOLOGICAL_STATE`
3. `REGULATORY_SUPPORT`
4. `CAUSAL_PERTURBATIONAL_PREDICTION`

Stage A can qualify at most a lawful, nonshortcut `RNA_REPRESENTATION` candidate.

## 3. Observation-operator contract

### 3.1 Model

Use the conceptual separation:

`z_biology -> O_t -> X_observed`

`O_t` describes how an experiment measures a biological state. Inference may condition on lawful observation metadata, conceptually `q(z | X, O_t)`, without treating technology as biology.

### 3.2 Lawful observation descriptors

Potentially lawful inputs to the observation channel include, when prospectively declared and source-authenticated:

- scRNA versus snRNA;
- platform/chemistry;
- measured vocabulary/support;
- library depth;
- detected-gene characteristics;
- count-split/downsampling characteristics;
- documented acquisition properties.

### 3.3 Forbidden shortcut descriptors

Do not use as unrestricted model covariates:

- donor ID;
- arbitrary dataset ID;
- arbitrary matrix/file ID;
- labels that encode study identity without a measurement rationale;
- pathology/outcome labels during target selection.

If a dataset/study identifier is required for an audit or stratified metric, that does not make it a lawful model input.

### 3.4 Invariance target

Approximate invariance is desirable to irrelevant measurement realization and technical replicate noise, while preserving sensitivity/equivariance to legitimate biology such as cell state, region, donor biology and age-associated biology.

Do not use `technology cannot be predicted from representation` as a universal success rule. Prefer conditional residual measurement-imprint tests after comparable biological structure is accounted for.

## 4. Basis and subspace stability contract

A representation subspace can be stable while individual coordinates rotate. Coordinate-level biological interpretation is therefore forbidden unless axis stability is separately demonstrated.

Before interpreting individual coordinates, require donor-balanced resampling or leave-donor-group-out analyses reporting, as applicable:

- principal angles between fitted subspaces;
- canonical correlations;
- Procrustes-aligned coordinate stability;
- eigenvalue/singular-value gaps;
- coordinate sign/order stability after lawful alignment.

Allowed outcomes:

- `AXES_STABLE`
- `SUBSPACE_STABLE_AXES_ROTATE`
- `SUBSPACE_UNSTABLE`
- `NOT_IDENTIFIED`

If the outcome is `SUBSPACE_STABLE_AXES_ROTATE`, report stable subspaces/blocks rather than assigning biological meaning to individual coordinates.

## 5. Evidence-response and measurement-depth curves

Two different curves are required and must not be conflated.

### 5.1 Biological-evidence convergence

For the same biological cell/state, evaluate representation as progressively more lawful biological evidence is revealed, e.g. 20%, 40%, 60%, 80%, 100% of the prospectively defined evidence universe.

Record representation displacement to the full-evidence reference and incremental change as evidence increases.

Purpose: estimate how much inferred state changes when **additional relevant molecular information** becomes available.

This is a biological-information uncertainty diagnostic, not a truth metric.

### 5.2 Measurement-depth convergence

Holding the biological information universe fixed, downsample measurement depth, e.g. 25%, 50%, 75%, 100% counts.

Purpose: estimate how much inferred state changes when the same biology is measured more or less deeply.

Do not call molecule-subsampling stability independent biological remeasurement.

### 5.3 Required distinction

Report separately:

- `U_bio`: state sensitivity to additional lawful biological evidence;
- `U_measurement`: state sensitivity to depth/noise under the same information universe.

A representation that is stable to depth but insensitive to additional biology may be technically robust but biologically uninformative.

## 6. Domain-support contract

Track two support axes separately:

- `D_measurement`: familiarity of assay/technology/observation regime;
- `D_biological_support`: familiarity of the biological state/population.

Do not automatically correct an unusual but well-measured donor/cell toward the training mean merely because it is biologically rare.

Do not classify biological novelty as technical OOD solely because it is uncommon.

## 7. Stage-A real-RNA prefreeze contract

Status remains:

`PREFREEZE_EXECUTION_CONTRACT__NOT_EXECUTION_AUTHORITY`

Hard boundaries:

- encoder optimizer updates = 0;
- predictor/encoder training updates = 0 except prospectively approved diagnostic readouts;
- EMA updates = 0;
- TEST sealed;
- Morabito protected;
- no pathology outcome opened for target selection;
- no external-validation outcome used to tune target definition;
- no legacy checkpoint promoted as biological authority.

Immediate fail conditions:

- direct or descendant q leakage;
- identity-only or technical-only control satisfies the biological rule;
- target/readout/threshold changed after deciding outcome is visible;
- held-out units used to fit diagnostic readout;
- lower claim level promoted automatically.

Any fitted diagnostic readout must fit on inner TRAIN only, freeze before held-donor evaluation, and carry fit/evaluation provenance.

Top-level verdicts remain:

- `QUALIFIED_FOR_RNA_REPRESENTATION`
- `INFORMATIVE_BUT_NOT_QUALIFIED`
- `FAIL_LEAKAGE`
- `FAIL_SHORTCUT`
- `FAIL_TRANSPORT`
- `NONRECOVERABLE_FROM_VIEW`
- `INDETERMINATE`

No verdict authorizes production training.

## 8. External-validation asset roles

Do not redo completed audits from PRs #188-#199 unless a required field is genuinely missing.

For every external asset record:

- modality;
- biological unit count;
- same-cell/same-nucleus pairing status;
- prior exposure;
- protected/sealed status;
- independence class;
- source/data-access class;
- claim transitions it can test;
- claim transitions it cannot test;
- provenance grade;
- known confounding or identity defects.

Previously exposed assets must not be called pristine independent validation.

Morabito remains `PROTECTED_NOT_AVAILABLE_FOR_SELECTION`.

Observational multimodal association cannot by itself receive causal authority.

## 9. Foundation-population estimand candidates

No estimand is selected in this document.

At minimum compare prospectively:

### Cell-weighted

Represents the empirical cell distribution. Risk: large donors/sources dominate.

### Donor-weighted

Gives donors equal total weight. Better aligned to donor-level inference; may underrepresent legitimate source prevalence.

### Source-balanced donor-weighted

Balances source/study first, then donors within source. Protects against a dominant source controlling the representation objective; changes the target population away from empirical cell prevalence.

### Hierarchical tempered sampling

Possible future form: sample dataset/source, donor, then cell with a prospectively fixed tempering exponent rather than tuning the exponent on biological outcomes.

Selection remains `UNSET_REQUIRES_APPROVAL`.

## 10. Synthetic evidence firewall

Synthetic success proves recovery/rejection of known planted structure under simulated conditions only.

Any synthetic result used to justify canonical production-pipeline behavior must use the 41,238-address identity universe or a prospectively justified equivalent that preserves relevant shortcut and dimensional opportunities.

The current V77 generator search is separate from this real-RNA premise contract. A simulator family being qualified or falsified does not select a real-RNA target or representation.

## 11. Required prefreeze artifacts before Stage-A execution can even be considered

1. target-meaning declaration for each candidate;
2. representation-family contract with no winner;
3. observation-operator declaration and forbidden shortcut list;
4. leakage seam audit;
5. negative-control roster;
6. recoverability definition and denominators;
7. donor/operator/study/technology transfer plan;
8. basis/subspace stability metrics and verdict logic;
9. biological-evidence convergence protocol;
10. measurement-depth convergence protocol;
11. measurement-support vs biological-support OOD rules;
12. external-validation asset matrix;
13. foundation-population estimand choice set with `selected=UNSET_REQUIRES_APPROVAL`;
14. metric directions, resampling unit, multiplicity policy and stop conditions;
15. explicit list of untested claims.

Only a separate later authority may convert this prefreeze package into narrow Stage-A execution permission.

## 12. Do-not-repeat / anti-overclaim rules

Do not:

- equate target-object recoverability with biological truth;
- privilege `cell_state` because it already exists;
- interpret `width=160` as biological dimensionality;
- demand universal technology invariance;
- use dataset ID as an unrestricted shortcut covariate;
- interpret unstable coordinates when only the subspace is stable;
- merge biological-evidence uncertainty with sequencing-depth uncertainty;
- call unusual biology technical OOD by default;
- call rare RNA structure biological novelty without independent support;
- reuse external assets for both target selection and independent confirmation without explicit exposure accounting;
- treat cell count as biological-unit count;
- let a successful synthetic benchmark authorize real training;
- open TEST or Morabito during prefreeze.

## 13. Non-authority statement

This V3 design selects no target, representation, dimension, estimand, threshold, architecture winner or validation outcome.

It changes scientific governance only.

`TRAINING=OFF`; `MULTIMODAL_TRAINING=OFF`; `500K=NOT_AUTHORIZED`; `STAGE4=NOT_AUTHORIZED`; `TEST=SEALED`; `MORABITO=PROTECTED`; `STAGE_A_EXECUTION=NOT_AUTHORIZED__PREFREEZE_ONLY`.
