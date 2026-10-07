# JEPA contextual-target identifiability downgrade — 2026-10-07

## Scope

This checkpoint restores a previously explicit project constraint: a rich teacher may use biological evidence unavailable to the partial-RNA student, but the student cannot be required to point-predict the realized teacher-only component of that state.

For teacher evidence T, student evidence C, and query q, a deterministic squared-error student can at best recover E[z_T(T,q) | C,q]. Any component of z_T driven by information unique to T is irreducible conditional uncertainty, not student error.

This checkpoint does not authorize Stage A, training, protected data, TEST, Morabito, pathology, 500K, or Stage 4.

## Historical findings

Project history explicitly separated three requirements that had previously been conflated:

1. rich teacher fidelity: preserve enough evidence to construct a biologically meaningful cellular state;
2. student withholding: give the student incomplete evidence so it must infer rather than copy;
3. shortcut prevention: block q leakage and other unlawful paths without impoverishing the teacher.

The same history states that no architecture can recover information genuinely absent from the student observations. A rich-teacher design is therefore coherent only if the training/evaluation contract distinguishes student-predictable shared structure from teacher-private evidence and represents the latter as uncertainty, a distribution, or an abstention/support boundary rather than unavoidable pointwise mismatch.

## Re-audit of historical candidates

### R5

R5 remains scientifically useful because it restored a genuinely richer same-cell teacher and explicitly separated teacher fidelity, query specificity, and student predictability. However, its measured eight-gene q-context is only a developmental target probe, not a complete production state.

### TD56–TD58

TD56–TD58 remain strong evidence that some relational RNA structure is shared across disjoint views, donors, and sources, and TD58 shows that this shared structure remains detectable from partial RNA. This is evidence for a student-predictable shared component. It is not evidence that arbitrary rich-teacher state is point-identifiable from partial RNA.

Classification:

`TD56_TD58__SHARED_PREDICTABLE_RELATIONAL_STRUCTURE_EVIDENCE__NOT_FULL_RICH_STATE_IDENTIFIABILITY`

### LOCAL_CONTEXTUAL_CANDIDATE_V4

The historical local contextual candidate directly compares a query-safe rich teacher residual with a partial-student residual using cosine alignment, correct-cell retrieval, and evidence-convergence curves. These diagnostics are useful representation probes, but no recovered candidate contract couples them to an explicit conditional distribution, calibrated conditional variance, or irreducible-uncertainty term for teacher-private evidence.

Therefore its former local-front-runner status is too strong for the current target decision.

Reclassification:

`LOCAL_CONTEXTUAL_CANDIDATE_V4__REPRESENTATION_PROBE_ONLY__PRODUCTION_TARGET_IDENTIFIABILITY_NOT_ESTABLISHED`

High cosine does not prove point identifiability. A large shared component can dominate cosine while a biologically important teacher-private residual remains unpredictable.

## Important semantic distinction

Historical V5 D_shared / D_private machinery must not be silently reinterpreted as student-predictable versus teacher-private multimodal information. D_shared had donor-held-out cross-view and independent-view/sketch gates; D_private had its own donor/operator/technical-stability qualification. Those terms have historical data-derived semantics and require re-derivation before use in the teacher/student identifiability problem.

## Required prospective target contract

Before any Stage-A target can be promoted, it must make the decomposition explicit. Conceptually:

z_T = z_predictable(C,q) + z_teacher_private(T,C,q)

with the student objective applying point prediction only to a component demonstrated to be recoverable from lawful student evidence. Teacher-private evidence must be represented by one of the following prospectively qualified mechanisms:

- conditional uncertainty / calibrated predictive distribution;
- abstention/support when the student evidence is insufficient;
- or exclusion from the deterministic matching loss while remaining available to define/validate the richer teacher state.

Candidate qualification must separately test:

1. teacher biological fidelity improves with richer evidence;
2. the proposed shared component is donor-held-out and source-held-out predictable from partial RNA;
3. prediction exceeds generic-cell-state, query-only, and technical shortcuts;
4. residual teacher-only information is nonzero when expected and is not mis-scored as deterministic student error;
5. evidence-response uncertainty increases when biologically relevant evidence is withheld and remains separate from sequencing-depth uncertainty;
6. multimodal evidence, when introduced, is not assumed RNA-identifiable without direct cross-view evidence.

## Consequence for current target work

The correct next Stage-A scientific question is not:

`Can partial RNA match the full rich teacher vector?`

It is:

`Does richer teacher evidence construct a more faithful biological state, and which components of that state are demonstrably predictable from lawful partial-RNA evidence?`

No target winner is selected.

## Permanent boundaries

- TARGET_WINNER: none
- REPRESENTATION_WINNER: none
- selected population estimand: unset
- Phase-A eligible population authority: 13,510 cells
- Stage A execution: OFF
- training: OFF
- 500K: not authorized
- Stage 4: not authorized
- TEST: sealed
- Morabito: protected
- pathology: unopened
