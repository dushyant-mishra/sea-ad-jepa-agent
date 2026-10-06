# JEPA observation-operator contract — V1 prefreeze

Date: 2026-10-06
Status: `PREFREEZE_ONLY__NO_EXECUTION_AUTHORITY`

Purpose: separate biological state from how an experiment observes it, and prevent measurement metadata from becoming an unrestricted biological shortcut.

## Core model

Conceptual separation:

`z_biology -> O_t -> X_observed`

where `O_t` is the observation process associated with assay/technology/acquisition conditions.

Inference may condition on lawful observation descriptors, conceptually `q(z | X, O_t)`, but `O_t` is not itself biological state.

## Lawful descriptor classes

The following may be eligible for a prospectively declared observation channel if authenticated and scientifically justified:

- assay type, e.g. scRNA versus snRNA;
- platform/chemistry;
- measured feature vocabulary/support;
- library depth or count budget;
- detected-feature characteristics;
- count splitting/downsampling state;
- documented acquisition properties that affect measurement.

Eligibility does not mean all descriptors must be used.

## Forbidden unrestricted covariates

The following are forbidden as free model covariates unless a later explicit authority provides a narrow scientific reason and shortcut test:

- donor identifier;
- arbitrary dataset identifier;
- arbitrary matrix/file identifier;
- pathology/outcome label;
- study label used solely as a memorization key;
- any label derived from protected outcomes.

Dataset/study labels may still be used for audit stratification and held-out transport evaluation without becoming model inputs.

## Required invariance/sensitivity distinction

Desired approximate invariance:

- repeated measurement realization;
- irrelevant technical noise;
- technical replicate variation not carrying new biological evidence.

Desired sensitivity/equivariance:

- genuine cell state;
- cell type/subtype where biologically relevant;
- brain region/tissue biology;
- donor biology;
- age-related or disease-associated molecular biology when lawfully present in RNA;
- additional lawful molecular evidence.

Therefore `technology prediction accuracy = chance` is not a universal qualification rule.

## Residual measurement-imprint test

Technology/observation imprint should be assessed conditionally, not naively.

The question is:

> after accounting for comparable lawful biological structure, how much unnecessary observation-process information remains in the representation?

A future execution contract must prospectively define the conditioning strategy and held-out unit before using this as a deciding metric.

## Biology × observation interaction

State-dependent observation effects may exist.

Do not force a model in which `O_t` has only a global additive effect if the substrate supports evidence that measurement distortion depends on biological state.

Where identifiable, report biology × operator/technology interaction separately rather than calling all interaction biology or all interaction nuisance.

## Evidence/depth separation

Observation-process robustness must be tested with two distinct perturbations:

1. **same information universe, lower depth** — measurement uncertainty;
2. **more lawful biological variables/evidence revealed** — biological-information uncertainty.

A model stable under count downsampling but unchanged when meaningful biological evidence is added is not biologically informative merely because it is technically robust.

## Domain-support split

Keep:

- `D_measurement`: support/familiarity of the observation regime;
- `D_biological_support`: support/familiarity of the biological state.

Do not automatically treat unusual biology as measurement OOD.

## Audit requirements

Any future implementation using observation metadata must record:

- exact descriptor names;
- source/provenance of each descriptor;
- whether each descriptor is model input, audit-only, or stratification-only;
- transformation/encoding;
- missing-value handling;
- whether the descriptor can reveal dataset/donor identity;
- negative controls showing that descriptor access does not satisfy the biological rule by itself;
- transport behavior when the descriptor takes unseen values.

## Fail conditions

Fail the observation-channel qualification if:

- donor/dataset identity is accepted as an unrestricted embedding;
- protected outcomes enter the observation channel;
- the model can satisfy the biological qualification rule from observation descriptors alone;
- a descriptor's provenance is unknown;
- unseen technologies silently map to an arbitrary learned ID without an explicit OOD rule;
- biological evidence is discarded solely to make technology harder to predict;
- measurement-depth stability is presented as biological validation.

## Non-authority statement

This contract selects no observation embedding architecture and authorizes no model update.

`TRAINING=OFF`; Stage A remains prefreeze only; TEST remains sealed; Morabito remains protected.
