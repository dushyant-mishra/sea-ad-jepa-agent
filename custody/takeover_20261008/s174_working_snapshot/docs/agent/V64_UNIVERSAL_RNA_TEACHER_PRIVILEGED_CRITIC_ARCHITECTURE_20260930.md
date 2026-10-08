# V64 architecture decision — universal RNA teacher + privileged auxiliary critics

**Date:** 2026-09-30  
**Status:** PROSPECTIVE ARCHITECTURE DECISION — no training authority

## Decision

Do **not** replace the universal RNA JEPA teacher with one giant multimodal teacher.

Keep the universal teacher/target path RNA-native unless and until a successor is explicitly qualified.

Rich regulatory measurements begin as **privileged auxiliary critics/encoders** on paired subsets.

A privileged factor may enter compulsory universal RNA-student supervision only after its recoverable subspace passes the V64 privileged-state recoverability contract.

## Why

The full foundation corpus is predominantly RNA-only, whereas paired regulatory cohorts are smaller and non-random.

A multimodal teacher can encode:
- regulatory state preceding transcription;
- assay-private information;
- promoter/enhancer state not identifiable from RNA;
- availability patterns specific to the multimodal cohort.

Forcing all of that into the universal target creates an impossible or biased student objective.

The universal target must remain identifiable from lawful student inputs.

## Proposed topology

### Universal path

`FULL104 RNA -> online RNA encoder -> predictor -> RNA EMA teacher targets`

This remains the broad state-learning path.

### Privileged calibration path

On paired/regulatory subsets only:

`regulatory measurements -> privileged encoder/critic -> Z_priv`

`lawful RNA -> RNA representation -> candidate prediction of Z_priv`

The privileged object is then partitioned conceptually into:

- `Z_priv_shared`: qualified RNA-recoverable subspace;
- `Z_priv_private`: retained privileged-private residual.

Only `Z_priv_shared` can become a compulsory auxiliary RNA target after qualification.

## Privileged critics are not automatically teachers

Before recoverability authority, privileged encoders may provide:

- biological validation;
- relational constraints;
- neighborhood/ranking consistency;
- uncertainty estimates;
- target-candidate adjudication;
- held-out evidence-family evaluation.

They must not silently redefine the universal EMA teacher state.

## Promotion gate

A privileged factor can be promoted into universal auxiliary supervision only if:

1. construction is leakage-safe;
2. basis/subspace stability is established;
3. donor-disjoint RNA recoverability passes prospectively frozen criteria;
4. simple activity/technical/availability baselines do not explain the result;
5. shared/private rank is selected without TEST;
6. private residual remains explicit;
7. strongest feasible held-out evidence-family check is reported separately.

Promotion is factor-specific. One passing factor does not authorize all privileged modalities.

## Loss semantics

No numeric loss weights are frozen here.

Future allowed categories:

- universal RNA JEPA loss on RNA-eligible cells;
- recoverable privileged auxiliary loss on cells with the qualified target or lawful target estimate;
- optional relational/geometry constraint where prospectively defined.

Forbidden:

- zero target for missing privileged modality;
- loss on RNA-only cells against privileged-private state;
- availability indicator as a shortcut target;
- direct full-rich-teacher MSE without recoverability authority.

## Coordinate versus geometry supervision

Coordinate-wise distillation is allowed only if teacher coordinates themselves are stable and meaningful.

If the teacher state is identifiable only up to rotation, prefer a frozen TRAIN-derived alignment or rotation-invariant geometry/subspace objective.

TEST data may not choose the rotation.

## Missing modalities

Missing privileged evidence is a mask/state, not a zero-valued modality.

A cell lacking privileged measurements:
- remains eligible for universal RNA JEPA when otherwise lawful;
- receives no privileged-private loss;
- does not receive a fabricated regulatory state.

## Paired subset selection bias

The paired subset cannot automatically set universal scientific mass.

Future auxiliary weighting must separately consider:
- donor balance;
- dataset balance;
- evidence availability;
- gene/promoter coverage;
- common support.

The multimodal cohort's raw cell count must not determine the universal ontology.

## Training sequencing

No joint multimodal training is authorized yet.

Preferred scientific sequence:

1. qualify universal RNA state candidate;
2. construct privileged factors on development paired data;
3. qualify recoverability;
4. lock recoverable projection/subspace;
5. only then test an auxiliary-supervision successor;
6. compare against RNA-only baseline on donor/dataset holdouts.

This sequence avoids jointly training a teacher/student system that can reshape its teacher to become easier for the student.

## Relation to existing runtime

The current V5 inactive runtime already has an RNA EMA teacher and RNA-masked student.

That path should remain semantically intact during current V64 Phase-A work.

A future privileged auxiliary module is a successor extension, not a reinterpretation of existing target tensors.

## Literature context

Cross-modal and privileged-information distillation show that richer training-time modalities can improve a unimodal model. Relevant examples include:
- privileged multimodal teacher -> unimodal student frameworks;
- modality-disentangling teacher designs for missing-modality inference;
- cross-modal distillation to improve transcriptomic representations using morphological features.

These establish feasibility of the general paradigm, not validity of full-teacher imitation in this project. The project's stricter requirement is to qualify which privileged information is actually recoverable and biologically transferable before compulsory distillation.

## Governance

TRAINING OFF.
Phase B STOPPED.
Stage 4 NOT AUTHORIZED.
Morabito PROTECTED.
No loss weight, privileged encoder, or joint-training schedule is authorized.
