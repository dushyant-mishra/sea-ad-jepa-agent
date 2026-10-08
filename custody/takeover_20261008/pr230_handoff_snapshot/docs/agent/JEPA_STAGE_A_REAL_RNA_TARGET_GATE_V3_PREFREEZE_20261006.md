# JEPA Stage-A real-RNA target/representation gate — V3 prefreeze

Date: 2026-10-06
Status: `PREFREEZE_EXECUTION_CONTRACT__NOT_EXECUTION_AUTHORITY`

## Purpose

Prospectively define how lawful TRAIN-only real RNA may discriminate candidate target/representation families without training the JEPA encoder or opening protected evaluation assets.

## Hard execution boundaries

- encoder optimizer updates = 0;
- JEPA predictor/encoder training updates = 0;
- EMA updates = 0;
- TRAIN-only evidence;
- TEST remains sealed;
- Morabito remains protected;
- no pathology/outcome label is used for target selection;
- no external validation outcome is used to tune the target, representation, readout, threshold or negative-control roster;
- historical checkpoints may be inspected for mechanics but do not carry biological authority.

This document does not authorize Stage-A execution.

## Candidate families

The deciding comparison must remain open across:

- `GLOBAL_CELL_STATE`
- `QUERY_LOCAL_STATE`
- `PROGRAM_STATE`
- `STRUCTURED_COMBINED_STATE`

No family has incumbent priority.

## Absolute leakage failure

Verdict `FAIL_LEAKAGE` if q/the hidden answer, or a deterministic descendant of it, enters lawful student evidence through any path including:

- direct value access;
- target/teacher pre-context access;
- normalization denominator;
- QC summary;
- support/missingness pattern;
- derived feature;
- mask construction;
- any equivalent descendant channel.

## Absolute shortcut failure

Verdict `FAIL_SHORTCUT` if the candidate's deciding rule can be satisfied by a frozen control based only on easier information such as:

- gene/address identity;
- matched wrong-query/query exchangeability;
- capacity-matched global summary;
- source/operator identity;
- depth/library size;
- visibility/support/missingness;
- technical-only features;
- biology-absent/covariance-only structure where applicable.

## Recoverability reporting

Report `TARGET_OBJECT_RECOVERABILITY` where estimable from lawful partial RNA.

Do not call it `BIOLOGICAL_TRUTH_RECOVERABILITY` unless an independently defined truth exists.

A nonrecoverable component is reported as `NONRECOVERABLE_FROM_VIEW`; it is not automatically a model defect.

## Fitted diagnostic firewall

If a diagnostic readout is required:

- fit only on a prospectively defined inner-TRAIN partition;
- freeze target, features, hyperparameters and readout before held-donor evaluation;
- never fit on deciding held-out units;
- record all fit/evaluation unit identities and tuning decisions;
- diagnostic fitting does not authorize JEPA training.

## Required transport reporting

Report independently where identifiable:

- `DONOR_TRANSFER`
- `OPERATOR_TRANSFER`
- `STUDY_TRANSFER`
- `TECHNOLOGY_TRANSFER`

Allowed statuses include `PASS`, `FAIL`, `NOT_TESTED`, `NOT_IDENTIFIABLE_UNDER_CURRENT_CONFOUNDING`.

Only actually tested evidence may receive PASS.

## Stability and uncertainty requirements

For representation candidates report, where applicable:

- donor-resampled subspace stability;
- coordinate stability only after lawful alignment;
- biological-evidence convergence;
- measurement-depth convergence;
- `D_biological_support` separately from `D_measurement`.

Stable depth behavior is not biological validation. Stable subspace does not authorize coordinate semantics.

## Prospective statistics

Before any deciding candidate result is opened, freeze:

- target construction for each candidate;
- representation extraction definition;
- negative-control roster;
- comparison directions;
- biological resampling unit;
- diagnostic fit/evaluation partition;
- metric definitions;
- multiplicity policy;
- stop/fail logic;
- estimand used for deciding summaries;
- any numeric decision margins.

Numeric decision margins remain `UNSET_REQUIRES_APPROVAL` unless inherited from independent prior authority or a prospectively approved calibration that cannot inspect deciding candidate outcomes.

## Top-level verdicts

Exactly these top-level scientific statuses are available:

- `QUALIFIED_FOR_RNA_REPRESENTATION`
- `INFORMATIVE_BUT_NOT_QUALIFIED`
- `FAIL_LEAKAGE`
- `FAIL_SHORTCUT`
- `FAIL_TRANSPORT`
- `NONRECOVERABLE_FROM_VIEW`
- `INDETERMINATE`

`QUALIFIED_FOR_RNA_REPRESENTATION` is not production-training authority and does not establish transferable biological, regulatory or causal validity.

## Stop rather than tune

STOP if:

- target meaning is undefined;
- deciding thresholds would have to be chosen after outcome inspection;
- identity/technical controls satisfy the biological rule;
- q leakage cannot be excluded;
- held-out units influenced fitted readouts;
- target-object recoverability is being promoted to biological truth;
- a representation winner would depend on an untested transport axis;
- protected/external outcomes are needed to rescue target selection.

## Non-authority statement

`TRAINING=OFF`; `STAGE_A_EXECUTION=NOT_AUTHORIZED`; TEST sealed; Morabito protected; target winner none; representation winner none; estimand unset.
