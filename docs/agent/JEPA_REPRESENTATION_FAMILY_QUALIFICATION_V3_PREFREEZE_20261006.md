# JEPA representation-family qualification — V3 prefreeze

Date: 2026-10-06
Status: `DRAFT_PREFREEZE__NO_WINNER__NO_EXECUTION_AUTHORITY`

This document defines the comparison that must be frozen before any deciding TRAIN-only real-RNA representation result is opened.

It selects no representation, dimension, threshold or target.

## Families under comparison

### 1. `GLOBAL_CELL_STATE`

Object: one cell-level representation summarizing broad transcriptomic state.

Legitimate strengths:
- compact global state;
- donor/cell-state transport testing;
- natural evidence/depth convergence curves.

Legitimate losses:
- fine query-specific structure may be compressed away.

Primary shortcut risks:
- depth/library size;
- source/operator identity;
- broad cell-class identity;
- donor imbalance;
- global expression summaries that look predictive without query-specific evidence.

Maximum claim before independent external evidence:
`RNA_REPRESENTATION`.

### 2. `QUERY_LOCAL_STATE`

Object: representation conditional on the queried gene/address or local target context.

Legitimate strengths:
- preserves local/query-specific state;
- can test incremental evidence beyond gene identity.

Legitimate losses:
- may not provide a coherent global cell summary.

Primary shortcut risks:
- address identity;
- query leakage through normalization/QC/support descendants;
- memorized gene-specific priors;
- support/missingness revealing q.

Maximum claim before independent external evidence:
`RNA_REPRESENTATION`.

### 3. `PROGRAM_STATE`

Object: representation of reproducible multigene programs/subspaces rather than individual coordinates.

Legitimate strengths:
- better suited when biological structure is subspace-stable but coordinate axes rotate;
- may preserve modular biology while avoiding arbitrary coordinate interpretation.

Legitimate losses:
- gene-local detail may be compressed;
- program construction itself can introduce identity/covariance shortcuts.

Primary shortcut risks:
- program definitions derived from deciding outcomes;
- static gene covariance mistaken for cell-specific state;
- source/operator-specific modules;
- unstable program basis across donors.

Maximum claim before independent external evidence:
`RNA_REPRESENTATION`.

### 4. `STRUCTURED_COMBINED_STATE`

Object: explicit combination of a global state with query-local and/or program-level components.

Legitimate strengths:
- can preserve both broad and local structure;
- avoids forcing one vector to carry all molecular detail.

Legitimate losses:
- higher complexity;
- more surfaces for technical shortcuts and leakage.

Primary shortcut risks:
- one component silently carrying forbidden q information;
- global component dominating local evidence;
- duplicated information creating artificial apparent robustness;
- difficult attribution of transport failure.

Maximum claim before independent external evidence:
`RNA_REPRESENTATION`.

## Required comparison dimensions

Every family must be evaluated on the same declared dimensions where applicable.

### A. Incremental information beyond shortcuts

Candidate must add information beyond prospectively frozen controls including:

- gene/address identity;
- wrong-query/query exchangeability;
- capacity-matched global summaries;
- source/operator/depth/support baselines;
- donor/source imbalance;
- technical-only baselines.

Passing a raw prediction metric is insufficient.

### B. Target-object recoverability

Report candidate recovery relative to `TARGET_OBJECT_RECOVERABILITY` where estimable.

Do not label this biological-truth recoverability on real RNA.

### C. Donor-level transport

Held-donor evaluation is mandatory for deciding evidence unless a later authority explicitly justifies a different biological unit.

Cell count cannot replace donor count.

### D. Separate transport axes

Report independently:

- donor transfer;
- operator transfer;
- study transfer;
- technology transfer.

Missing axes remain `NOT_TESTED` or `NOT_IDENTIFIABLE`, never PASS.

### E. Basis/subspace stability

For representations with coordinates/subspaces, use donor-balanced resampling or leave-donor-group-out and report:

- principal angles;
- canonical correlations;
- Procrustes-aligned coordinate stability;
- spectral/eigenvalue gaps where applicable.

Any coordinate alignment used for held-donor evaluation must be fit on lawful inner TRAIN data and frozen before the held donors are evaluated.

Interpretation:

- `STABLE_COORDINATES`: coordinate-level interpretation may become eligible for later biological testing;
- `STABLE_SUBSPACE_ONLY`: only subspace/block claims are allowed;
- `UNSTABLE_REPRESENTATION`: representation family is not qualified as stable state;
- `INDETERMINATE__INSUFFICIENT_BIOLOGICAL_UNITS`: insufficient biological units for a stability conclusion.

No coordinate receives biological semantics from stability alone.

### F. Biological-evidence convergence

For the same biological state, reveal progressively more lawful molecular evidence using a prospectively frozen schedule such as 20/40/60/80/100%.

Measure representation displacement relative to the full-evidence state and incremental movement with added evidence.

A good state representation should respond when meaningful biological evidence is added, rather than merely remaining invariant.

### G. Measurement-depth convergence

Holding the information universe fixed, downsample counts using a prospectively frozen schedule such as 25/50/75/100%.

This evaluates sensitivity to measurement depth/noise, not sensitivity to added biological variables.

Report separately from biological-evidence convergence.

### H. Domain support

Report separately:

- `D_measurement`: support of the observation regime;
- `D_biological_support`: support of the biological state/population.

Do not force unusual but well-measured biology toward the training mean merely because it is rare.

### I. Observation-operator dependence

Technology/assay descriptors may be used only through a prospectively declared observation-process interface.

Do not grant unrestricted dataset-ID or donor-ID embeddings.

Assess residual technical imprint conditional on comparable biology rather than demanding universal technology unpredictability.

## Common fail conditions

Any family fails the current qualification layer if:

- q or a deterministic descendant leaks into the permitted student evidence;
- address identity alone satisfies the deciding rule;
- a technical-only control satisfies the deciding rule;
- held-out units influence fitted diagnostic readouts;
- deciding thresholds are chosen after deciding outcomes are visible;
- a representation is called biological because it reconstructs RNA;
- unstable coordinates are interpreted biologically when only the subspace is stable;
- biological-evidence and measurement-depth uncertainty are collapsed into one number;
- missing transport evidence is promoted to PASS.

## Required output structure

For each family produce a row with:

- target object;
- extraction definition;
- dimensionality/structure declaration;
- shortcut-control results;
- target-object recoverability;
- held-donor result;
- operator/study/technology transfer statuses;
- basis/subspace stability status;
- biological-evidence convergence summary;
- measurement-depth convergence summary;
- `D_measurement` and `D_biological_support` behavior;
- rare/local RNA behavior;
- maximum claim level;
- unresolved items.

## Selection rule

No winner is selected in this prefreeze.

A later execution authority must prospectively define how evidence across the comparison dimensions is adjudicated. A representation cannot win solely by one aggregate score if it fails an absolute leakage/shortcut/transport requirement.

`cell_state` has no incumbent advantage.

`STRUCTURED_COMBINED_STATE` is not preselected merely because it is more expressive.

## Non-authority statement

`TRAINING=OFF`.

Encoder/predictor optimization and EMA updates remain zero during target/representation discrimination unless a later narrow authority explicitly permits a prospectively frozen diagnostic readout that is not JEPA training.
