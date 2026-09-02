# JEPA PROJECT MEMORY OS
Date: 2026-08-23
Status: controlling project-governance layer

## Purpose
Prevent repeated experiments, loss of prior conclusions, silent resurrection of rejected ideas, and drift from the protected scientific objective.

## Canonical state
Do not rely on conversational memory alone. Controlling state is externalized into:
- DECISION_REGISTRY.csv
- EXPERIMENT_LEDGER.csv
- ACTIVE_STATE.md
- ARCHITECTURE_CONTRACT.md
- NEXT_ALLOWED_ACTION.json

## Mandatory novelty preflight
Before proposing or running any experiment, record:
1. Exact scientific question.
2. Closest prior experiment IDs.
3. Closed decisions that constrain it.
4. Genuine novel delta.
5. Why prior evidence does not already answer it.
6. Duplication verdict:
   - NOVEL_AND_AUTHORIZED
   - REVISIT_JUSTIFIED
   - DUPLICATE_DO_NOT_RUN
   - CONTRADICTS_CLOSED_DECISION
   - INSUFFICIENT_NEW_INFORMATION

No experiment proceeds without this check.

## Evidence-consistency critic comes first
The first critic for every major design is PROJECT HISTORIAN / EVIDENCE CONSISTENCY:
- Have we already tested this?
- Did we reject or qualify this mechanism?
- Does this recreate an old failure under a new name?
- Is a recent result merely rediscovering an older one?
- Is a mechanics fixture being mistaken for production biology?

Only after it passes do Target/Predictor, Biology/Rare-State, Statistics/Leakage, and Compute critics run.

## Experiment IDs
Every experiment gets an ID: EXP-YYYYMMDD-NNN.
Every experiment records question, data, intervention, controls, teacher/student state, view count, mask/exposure policy, key results, limitations, affected decisions, and supersession links.

## Decision IDs
Every durable conclusion gets DEC-NNN with status OPEN / PROVISIONAL / CLOSED / SUPERSEDED.
A CLOSED decision can only be reopened by specifically documented new evidence.

## Experiment classes
- MECHANICS_DIAGNOSTIC
- BIOLOGY_DIAGNOSTIC
- CAUSAL_INTERVENTION
- TEACHER_QUALIFICATION
- STUDENT_QUALIFICATION
- PRODUCTION_QUALIFICATION

Claims may not silently jump classes.

## Protected objective
Infer latent biological programs/states from incomplete RNA evidence.
Not exact hidden-transcript reconstruction, dataset/source prediction, or loss minimization for its own sake.

## Permanent operating rules
- Negative results are first-class evidence.
- Loss improvement never substitutes for biological qualification.
- Broad molecular address coverage and biology-aware exposure are orthogonal.
- Do not call tier-hiding a production cascade.
- Random/frozen u0 is a mechanics fixture, not a biological teacher.
- Teacher target fidelity and downstream biology are separate endpoints.
- Every completed experiment must update the ledger, registry, active state, and next action.

## Bootstrap rule
Every new JEPA chat/Codex session must first read the canonical state files completely, then perform the novelty preflight before proposing experiments.
