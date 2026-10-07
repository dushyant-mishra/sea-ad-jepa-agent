# JEPA rich-teacher / partial-student component recoverability gap — 2026-10-07

Status: `AUDIT_CHECKPOINT__NO_EXECUTION_AUTHORITY`

## What current V3 already gets right

Current `main` premise-qualification V3 correctly separates target meaning from recoverability. It explicitly allows candidate components to be:

- `RECOVERABLE_FROM_VIEW`
- `PARTIALLY_RECOVERABLE_FROM_VIEW`
- `NONRECOVERABLE_FROM_VIEW`
- `RECOVERABILITY_NOT_IDENTIFIED`

and states that a biologically important but nonrecoverable component is not automatically a model failure.

The Stage-A gate likewise says a nonrecoverable component should be reported as `NONRECOVERABLE_FROM_VIEW` rather than treated as a model defect.

This is consistent with the historical teacher/student identifiability principle: a rich teacher may construct a biologically faithful state using evidence not available to the partial-RNA student; student failure to point-recover genuinely absent information is not, by itself, evidence that the teacher target is invalid.

## Historical evidence that reinforces the distinction

The V77/Macha historical audit found that earlier attempts to tune "partial recoverability" numerically were artificial. It preferred structural partial recoverability arising from real measurement support: a biological program may partly occupy addresses unavailable to a source/view.

The same audit distinguishes biological ATAC-private signal from ATAC technical signal and records that prior ATAC recovery remained unqualified when the ATAC observer SNR was inadequate. SCENIC+ is explicitly not ground truth.

A later forward-only Phase-3 preflight also separates:

- `PRESERVATION FAILURE`: complete/rich representation loses biology present in raw evidence;
- `INFERENCE LIMITATION`: complete/rich representation preserves biology but partial evidence cannot recover it;
- `UNCERTAINTY FAILURE`: inference exists but uncertainty is miscalibrated.

These are scientifically distinct and must not collapse into a single prediction score.

## Machine-enforcement gap found on current main

The V3 prose contract is stronger than the machine-readable state and tests.

`docs/agent/JEPA_PREMISE_QUALIFICATION_V3_STATE_20261006.json` records recoverability semantics and a top-level Stage-A verdict roster, but it does not encode a required per-component recoverability ledger/status roster.

`tests/governance/test_stage_a_v3_machine_contract.py` freezes the seven top-level Stage-A verdicts and diagnostic-readout firewall, but does not require per-component classifications.

`scripts/governance/verify_premise_qualification_v3_surface.py` validates the meaning of target-object recoverability and forbids equating it with biological-truth recoverability, but does not require any `component_recoverability` object or enforce the four component statuses above.

Classification:

`V3_PROSE_COMPONENT_RECOVERABILITY_CORRECT__MACHINE_ENFORCEMENT_INCOMPLETE`

## Why this matters for target discovery

For a rich teacher with partial-RNA student, one whole target object may contain a mixture of:

1. components reliably predictable from lawful student RNA;
2. components only partially predictable from RNA;
3. biologically meaningful teacher-private components not point-identifiable from RNA;
4. components whose recoverability has not yet been identified.

A single aggregate cosine, retrieval score, NLL, or family-level PASS/FAIL can hide these distinctions. In particular, a dominant shared component can yield excellent whole-vector similarity while smaller biologically important teacher-private components remain irreducibly uncertain.

The historical `LOCAL_CONTEXTUAL_CANDIDATE_V4` therefore remains useful only as representation/evidence-convergence evidence unless and until its target is decomposed under component-level recoverability semantics.

TD56-TD58 likewise remain evidence for shared predictable relational RNA structure, not authorization to deterministically match the entire state of a richer teacher.

## Required prospective repair before Stage-A execution authority

Do not change `main` under this audit branch. A future reviewed governance patch should require, for every structured target candidate, a machine-readable component ledger containing at minimum:

- component ID / scope;
- evidence available to teacher;
- evidence available to student;
- whether component is measured, latent, program/subspace, query-local, or other;
- recoverability status from the frozen roster;
- recoverability metric and denominator;
- held-donor evidence;
- shortcut-control result;
- whether deterministic point loss is permitted;
- whether uncertainty/distributional output is required;
- abstention/support rule where applicable;
- maximum claim level.

A structured target must not receive a single deterministic student-matching objective over components classified `NONRECOVERABLE_FROM_VIEW` or `RECOVERABILITY_NOT_IDENTIFIED`.

No numeric threshold, component definition, target winner, representation winner, or estimand is selected here.

## Current boundaries

- `TARGET_WINNER = none`
- `REPRESENTATION_WINNER = none`
- `TRAINING = OFF`
- `MULTIMODAL_TRAINING = OFF`
- `STAGE_A_EXECUTION = OFF`
- `500K = NOT_AUTHORIZED`
- `STAGE4 = NOT_AUTHORIZED`
- `TEST = SEALED`
- `MORABITO = PROTECTED`
- foundation-population estimand remains `UNSET_REQUIRES_APPROVAL`
