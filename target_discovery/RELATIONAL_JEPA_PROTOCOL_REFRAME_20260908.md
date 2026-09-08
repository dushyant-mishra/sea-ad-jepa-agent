# Relational JEPA protocol reframe after TD56

Status: `CONCEPTUAL_REFRAME__NO_TARGET_OR_TRAINING_AUTHORITY`
Date: 2026-09-08

## Trigger

TD56 established label-free, donor-wise, three-source survival of disjoint-gene within-donor relational geometry, while TD37 and TD48-TD55 repeatedly failed or became donor/source-fragile when the program attempted to define universal latent/query coordinates.

This changes the object that should be qualified.

## Core reframe

The Foundation program does **not** need to identify a fixed biological target tensor before JEPA training.

The learned target encoder may produce an emergent representation. What must be frozen and qualified is the **training protocol that constrains the geometry of that representation**:

- context/target evidence authority;
- masking/evidence schedule;
- learned target-encoder update rule;
- predictor architecture;
- relational loss;
- within-donor/block batch construction;
- collapse-prevention regularization;
- null/attack construction;
- donor-primary acceptance gates;
- checkpoint/selection rules.

The auditable object is the protocol and its invariants, not a named coordinate system.

## Teacher type

The project should retain a **learned online target encoder / EMA teacher**, not introduce an external frozen biological teacher.

Teacher:
- sees the richest lawful evidence allowed by the frozen query-safe/self-masked contract;
- produces latent cell embeddings;
- is stop-gradient for the student loss;
- parameters update only through the prospectively frozen EMA rule.

Student/context encoder:
- sees lawful partial evidence under the frozen evidence ladder;
- predictor maps partial-evidence embeddings toward teacher-defined relational structure.

No pathology, DEV, SEALED, reader-validation, reader-oracle, or query scalar leakage is introduced.

## Relational objective family

TD57 should prospectively qualify a relational latent objective rather than search for another fixed target coordinate.

Candidate components to freeze before execution:

### Distance geometry
For cells i,j inside an admissible donor-local training block:

`D_T(i,j) = ||t_i - t_j||_2`
`D_S(i,j) = ||s_i - s_j||_2`

Normalize each block by a prospectively specified robust/mean teacher/student distance so the loss does not require absolute cross-source distance scale.

A distance-wise loss penalizes disagreement between normalized teacher and student pair distances.

### Angle geometry
For prospectively sampled triples i,j,k inside the same admissible block, match the cosine angle between teacher difference vectors and student difference vectors.

This is invariant to translation and global positive scale and does not require latent-axis identity.

### Neighborhood/rank geometry
Optionally freeze a teacher-neighborhood ranking objective so the student must reproduce local teacher ordering rather than absolute distances.

No component search is allowed after outcomes. A TD57 freeze must choose the exact mixture before training.

## Anti-collapse

A purely relational objective admits degenerate solutions if teacher and student collapse together.

TD57 must therefore prospectively freeze explicit spread/collapse controls, preferably variance/covariance regularization on student/context embeddings plus deterministic monitoring of teacher variance, effective rank, pair-distance spread, and neighborhood entropy.

Collapse prevention is part of the scientific protocol, not an optimizer convenience.

## Coarse-structure failure gate

A relational objective that learns only broad cell type does **not** count as success.

Qualification must make fine same-cell/local-structure discrimination binding.

At minimum:
- standard matched wrong-cell null preserving donor/operator/depth/detection;
- a **fine-neighborhood wrong-cell null** in which the wrong cell is drawn from the correct cell's teacher-local neighborhood under a frozen outcome-blind rule;
- donor-primary recurrence;
- leave-one-donor/block robustness.

A TD57/TD58 pass requires student geometry from the correct partial-evidence cell to outperform these fine-matched wrong-cell alternatives.

No annotation-defined cell type is used during discovery/training. Annotated TD34-style structure may be opened only after label-free gates for validation.

## Anchor-relative profiles

Anchor-relative or prototype-relative distance/rank profiles are a lawful secondary bridge for:
- evaluation;
- export;
- per-cell diagnostics;
- possibly downstream interfaces.

They should **not** be the primary training target at this stage because universal anchors can silently recreate the TD37 transfer problem.

If anchors are later used, anchor identities/selection must be source-local or otherwise prospectively proven transportable; only the relational protocol may be shared across sources unless a separate transportability gate passes.

## Governance implication

The qualification regime can remain fail-closed without requiring a named biological target tensor.

The authority object becomes a deterministic relational-training contract whose:
- input rights;
- masks;
- block construction;
- loss equations;
- normalization;
- EMA update;
- collapse controls;
- nulls;
- donor gates;
- and acceptance terminal

are all byte-level frozen and reviewable.

Representation coordinates may remain emergent and are explicitly **not** scientific authority.

## Next phase

TD56 closes the search for a fixed coordinate target strongly enough to justify a phase transition:

`TARGET_DISCOVERY -> RELATIONAL_OBJECTIVE_QUALIFICATION`

The first prospective experiment should test whether a learned EMA teacher on rich lawful evidence can teach a partial-evidence student to reproduce fine donor-local relational geometry at the frozen evidence ladder, while beating both matched wrong-cell and fine-neighborhood wrong-cell attacks.

No neural training is authorized by this note. A separate prospective TD57/F-relational contract is required before any optimizer/EMA/checkpoint writes.
