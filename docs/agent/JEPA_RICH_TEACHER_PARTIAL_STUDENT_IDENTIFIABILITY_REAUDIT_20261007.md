# JEPA rich-teacher / partial-student identifiability re-audit — 2026-10-07

## Scope

This checkpoint re-opens the target-design question after re-reading the historical teacher/student discussions. It supersedes any shorthand that says the student should simply "match the rich teacher target" when that target contains information unavailable from the student's lawful observations.

No target winner is selected. Stage A execution remains OFF. Training remains OFF.

## Recovered project principle

The project's objective is a cellular molecular-state world model, not hidden-gene regression. The teacher is allowed, and in many cases required, to use richer biological evidence to construct a faithful target. The student receives partial lawful evidence and a query and must predict the biologically meaningful components of that target that are inferable from its observations.

These are distinct requirements:

1. teacher fidelity: richer evidence should improve construction of the biological state;
2. student predictability: the recoverable part of that state must be inferable from partial RNA;
3. shortcut control: q leakage, copied teacher embeddings, technical shortcuts, and generic cell-state-only solutions must be rejected.

Teacher richness must not be reduced merely to make deterministic student matching easier.

## Identifiability limit

Let `T` denote teacher-only rich evidence, `C` the student's lawful partial RNA/context, `q` the query, and `z_T(T,q)` the teacher state.

If the student is trained under squared error, the Bayes-optimal deterministic prediction is:

`z_hat(C,q) = E[z_T(T,q) | C,q]`.

Therefore any component of `z_T` that is unique to `T` and not statistically determined by `(C,q)` is irreducible uncertainty. No architecture can reconstruct the realized teacher-only information for an individual cell from evidence that does not contain it.

Accordingly, a valid rich-teacher target must not be qualified merely because teacher and student vectors can be numerically compared. Qualification must separate:

- shared/predictable biological state;
- teacher-private biological information;
- measurement-specific information;
- predictive uncertainty induced by missing biological evidence.

## Consequence for multimodal teacher evidence

If the teacher eventually uses ATAC, SCENIC+, or another modality that the RNA-only student does not observe, the student must not be required to reproduce modality-private realization-level details exactly.

Those rich measurements may be used to construct or validate a biological latent state, but the student objective must be one of the following, prospectively specified:

1. predict a cross-view/shared latent component whose held-out predictability from RNA has been demonstrated;
2. predict the conditional mean / distribution of the rich teacher state given partial RNA and query;
3. predict both a central state and calibrated biological uncertainty, with uncertainty increasing when teacher-private evidence materially changes the state;
4. abstain for target components that are not sufficiently predictable from the lawful student evidence.

A direct deterministic loss against the full rich teacher vector is scientifically invalid unless held-out evidence demonstrates that the relevant teacher components are sufficiently identifiable from the student view.

## Reinterpretation of historical target work

### R5 measured contextual target

R5 was scientifically useful because it restored a genuinely richer teacher: the teacher had same-cell measured target/context information while the student used a complementary RNA panel. However, predictability had to be demonstrated empirically; teacher fidelity alone could not qualify the target.

### TD56–TD58

TD56–TD58 provide evidence that some relational geometry is shared and predictable across independent RNA views and survives partial (~60%) RNA evidence. This is evidence for a potentially student-predictable shared relational component.

They do **not** justify asking the student to reproduce arbitrary rich-teacher state components or future modality-private teacher evidence.

TD58 should therefore be interpreted as:

`EVIDENCE_FOR_SHARED_PREDICTABLE_RELATIONAL_STRUCTURE__NOT_LICENSE_FOR_FULL_RICH_TEACHER_MATCHING`.

### Contextual residual candidate

Any historical candidate in which rich and partial representations appear nearly identical must be re-audited for whether the target was dominated by information common to both views, generic cell state, normalization geometry, or representation collapse. High cosine similarity by itself is not proof that the student recovered genuinely teacher-only biological information.

## Required prospective Stage-A contract

Before any target arm can execute, the contract must state explicitly:

1. what evidence the teacher sees;
2. what evidence the student sees;
3. which target components are intended to be shared/predictable;
4. which teacher-private components are not required to be point-predicted;
5. the uncertainty or abstention semantics for irreducible information;
6. held-donor and held-source tests showing student predictability above query-only, generic-cell-state, source/operator, depth/support, and wrong-cell controls;
7. an evidence ladder showing how prediction and uncertainty change as lawful student evidence increases;
8. no promotion of a target whose score rewards the student for impossible realization-level recovery of teacher-private information.

## Current target-design classification

- rich teacher: scientifically desirable, not a problem by itself;
- partial RNA student: intended design;
- deterministic exact matching to full rich state: **NOT GENERALLY IDENTIFIABLE**;
- shared predictable relational component: promising, still unqualified;
- probabilistic/uncertainty-aware prediction: required consideration wherever teacher-private evidence remains;
- TARGET_WINNER: none;
- Stage A execution: OFF;
- training: OFF.
