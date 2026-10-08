# JEPA Population Access & Sealed-Holdout Registry V1

Status: **PROSPECTIVE GOVERNANCE — NO NEW DATA ACCESS AUTHORIZED**

Date: 2026-09-07

This registry resolves a governance ambiguity that matters before the healthy-teacher training contract is frozen: the project has **two independent population-partition axes** and they must never be collapsed into one another.

1. The **foundation split** controls broad train / development / sealed / external-holdout status.
2. The **reader partition** is a second split nested entirely inside the original 149-donor foundation-train population.

Opening one axis never implicitly opens another, and opening expression never opens pathology.

## Exact authorities

| Authority | SHA-256 | Geometry |
|---|---|---:|
| `foundation_split_registry.csv` | `35afb7f53fa36d580a4552dd5ad7e59841e454ea85d4adcb761666cb20d05433` | 215 rows |
| `reader_donor_split.csv` | `efe43e63bfd580085f115f74dd00fdf3051f2c2a77674c99cee5c9ce43322511` | 149 donors |
| `T1_BIOLOGY_EVALUATION_FREEZE.json` | `33cd9758db351e8f2a0e72d5a55341e9ff24f6f50cba620b91f0987be3b95a06` | historical T1 evaluation semantics |
| recovered calibration-bundle transport | `07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444` | transport copy only |

The machine validator is `scripts/agent/validate_population_access_registry_v1.py`.

## Verified split geometry

Foundation registry:

| split | count |
|---|---:|
| train | 166 |
| development | 24 |
| sealed_holdout | 24 |
| whole_study_external_holdout | 1 study |

By split domain:

| domain | train | development | sealed |
|---|---:|---:|---:|
| foundation | 149 | 19 | 19 |
| continuation | 17 | 5 | 5 |

The whole-study external holdout is `siletti_human_brain_cell_atlas_v1`.

The 149-donor reader split is:

| reader partition | count |
|---|---:|
| reader_fit | 104 |
| reader_validation | 22 |
| reader_oracle | 23 |

Every one of those 149 reader donors is in **foundation/train**. None of the 17 continuation/train donors is in the frozen reader split.

This means:

`foundation/train` is **not equivalent** to `reader_fit`.

`reader_validation` is **not equivalent** to foundation `development`.

`reader_oracle` is **not equivalent** to foundation `sealed_holdout`.

## Current access states

### reader_fit — 104 donors

State: `ELIGIBLE_POOL__NOT_EXECUTION_AUTHORITY`

This is the only already-frozen reader training/discovery partition. It was the historical T1 encoder-fit population and is the population used by the bounded F1 reader preflight.

Current permissions remain narrow:

- metadata-only planning;
- already-authorized bounded technical preflight;
- D1-A synthetic/u0-safe development when no real reader-fit expression is consumed.

Potential future uses require their own authority:

- healthy-teacher training after the separate training contract freezes the exact corpus;
- real D1 discovery after a mechanically healthy trained teacher and prospective D1 algorithm freeze;
- real F1-A producer after producer/replay source freeze plus explicit execution authority.

The 17 continuation/train donors must **not** be silently added. A corpus-extension authority is required first.

### reader_validation — 22 donors

State: `CLOSED_READER_SELECTION`

Intended role: reader/model selection and descriptive validation after prospective release.

Never valid for:

- encoder/teacher training;
- D1 hypothesis generation;
- post-outcome tuning fed back into the training population.

Opening requires at minimum:

- exact candidate checkpoint root frozen;
- evaluation code/source frozen;
- metrics and use of the results frozen;
- explicit named reader-validation release authority.

### reader_oracle — 23 donors

State: `SEALED_INTERNAL_ORACLE`

Intended role: primary untouched internal evaluation.

Never valid for:

- training;
- hyperparameter/model selection;
- D1 discovery;
- iterative tuning after oracle outcomes.

Opening requires at minimum:

- model/training candidate frozen;
- analysis source frozen;
- reader-validation phase concluded;
- explicit one-way oracle release authority.

Once opened for a candidate, those outcomes become historical evaluation evidence. They cannot remain an untouched oracle for a modified candidate.

### foundation development — 24 donors

State: `CLOSED_DEVELOPMENT`

Composition: 19 foundation + 5 continuation donors.

This is a separate development population, not a synonym for reader-validation.

Current default: closed.

Any future opening must prospectively state:

- exact purpose;
- exact donor/source scope;
- exact analysis code and allowed output schema;
- whether the result is allowed to influence model selection.

It is currently unauthorized for teacher training, D1 real discovery, F1/T0 execution, and pathology.

### foundation sealed_holdout — 24 donors

State: `SEALED_FOUNDATION_HOLDOUT`

Composition: 19 foundation + 5 continuation donors.

Intended role: late confirmatory/internal generalization.

Never valid for:

- training;
- model selection;
- D1 discovery;
- tuning ranking formulas, thresholds, or multiplicity rules.

Opening requires:

- trained checkpoint frozen;
- hypothesis/estimand prospectively frozen;
- confirmatory analysis source and multiplicity handling frozen;
- explicit sealed-holdout release authority.

### whole-study external holdout

State: `SEALED_EXTERNAL_REPLICATION`

Study: `siletti_human_brain_cell_atlas_v1`

This is a whole-study external replication resource, not an internal model-selection set.

Opening requires a frozen internal candidate, frozen mapping/normalization authority, frozen external analysis code, and explicit external-release authority.

## Pathology is a separate firewall

The foundation split registry records `pathology_used_for_foundation_split=False` for every row.

That does **not** mean pathology is generally available. It means pathology was not used to define the foundation split.

Pathology remains a separate protected information channel. Access to a donor's RNA, metadata, latent state, or reader assignment never grants permission to inspect pathology labels or pathology-derived endpoints.

## Historical T1 exposure does not create new authority

The frozen T1 biology-evaluation contract historically used:

- `reader_fit` for readout fitting;
- `reader_validation` for reader selection/descriptive evaluation;
- `reader_oracle` as the primary untouched evaluation.

Those historical runs are evidence about the historical T1 line. They are **not** a standing permission to reopen those populations.

Because u10-u205 are defect-inherited, the historical reader-validation/oracle uses do not create a valid trained-teacher authority either.

Current state therefore remains:

- reader-validation: **closed**;
- reader-oracle: **sealed**.

## Lane-specific rules

### F1-A

Current permitted production population: reader-fit only, and even there real F1 remains unauthorized until the primary producer and independent replay sources are frozen and independently reviewed.

No reader-validation/oracle/development/sealed population may be substituted into F1 by convenience.

### F1-B / C3

Mechanical readiness does not grant population access.

A green attack suite or successor CI does **not** authorize training.

### Healthy-teacher training

This registry does not choose the final training corpus.

The later training contract must bind the exact corpus. The only pre-existing frozen reader-fit pool is the 104-donor reader-fit set. Any continuation/train expansion is a separate prospective decision.

### D1

D1-A is synthetic/u0-safe now.

When real D1 becomes legal, discovery defaults to reader-fit. Reader-validation requires a separate release for frozen robustness/validation analyses. Reader-oracle and sealed populations cannot be used to discover or rank hypotheses.

### T0

T0 V20 independent review is accepted as execution-binding review only. Real T0 and pathology remain unauthorized.

## Forbidden shortcuts

The following are explicit governance errors:

1. treating foundation development as reader-validation;
2. treating reader-oracle as foundation sealed-holdout;
3. treating RNA/latent access as pathology permission;
4. using oracle/sealed outcomes to tune training, D1 rankings, hypotheses, thresholds, or multiplicity;
5. silently adding continuation/train donors to the historical reader-fit training pool;
6. opening a protected population because mechanics code is ready;
7. allowing a later implementation to redefine these population labels without a new prospective registry version.

## Release ordering for a healthy teacher

A conservative future sequence is:

`reader_fit training/discovery -> reader_validation frozen validation/selection -> freeze selected candidate -> reader_oracle one-way internal evaluation -> separately frozen confirmatory question -> foundation sealed_holdout -> external whole-study replication`

Not every project question must traverse every stage, but no later protected population may be pulled earlier merely because an earlier result is inconvenient.

## Terminal meaning

This document supports only:

`PASS_POPULATION_ACCESS_REGISTRY__NO_NEW_DATA_ACCESS`

It grants no training run, no real F1, no real D1, no DEV/SEALED access, no reader-oracle access, and no pathology access.
