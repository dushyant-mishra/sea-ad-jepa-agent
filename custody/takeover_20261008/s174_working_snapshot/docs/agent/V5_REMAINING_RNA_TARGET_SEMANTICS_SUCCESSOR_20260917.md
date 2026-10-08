# V5 remaining-RNA necessity and teacher-target semantics successor — 2026-09-17

Status: `STRUCTURAL_SEMANTIC_SUCCESSOR_PASS__SCIENTIFIC_REMAINING_RNA_QUALIFICATION_OPEN__TRAINING_OFF`

Working branch: `impl/v5-remaining-rna-target-semantics-20260917`

Parent lineage: `analysis/v5-ridge8-expanded-validation-20260917 @ cee67631eadd808850a3659f08b154baaa82fb3b`

## What this closes

The prior `TeacherTargetSemanticsAuthorityV1` accepted nonempty semantic strings without constraining their meaning. That left a real semantic-spillover path: a future implementation could supply a plausible label while silently binding a scalar hidden-gene reconstruction target.

The successor now makes the following current-V5 semantics explicit and enumerated:

- state target: `BIOLOGICAL_CELLULAR_LATENT_STATE_V1`;
- query-local target: `QUERY_LOCAL_STATE_CONDITIONED_ON_CANONICAL_ADDRESS_V1`;
- scalar hidden-gene reconstruction: `HIDDEN_GENE_SCALAR_RECONSTRUCTION_FORBIDDEN_V1`;
- route sufficiency: `REMAINING_RNA_REQUIRED__IDENTITY_ONLY_AND_GLOBAL_ONLY_INSUFFICIENT_V1`.

Current authority closure now rejects the historical teacher-target semantics schema, the historical target-address schema, and the historical masking schema even if a caller makes their hashes internally self-consistent.

The Stage-A spillover firewall now treats the current target-address, current masking, remaining-RNA necessity, and teacher-target-semantics successor modules as the current path and quarantines the three superseded schemas.

## Remaining-RNA necessity rule

`RemainingRnaNecessityAuthorityV1` prospectively defines a paired query-local state necessity test.

The intervention keeps query identity and lawful global biological context available while removing the remaining RNA evidence. The full-evidence condition must beat both:

1. query identity only; and
2. query identity plus lawful global biological context with no remaining RNA.

The approved primary state metrics are query-local latent-state cosine similarity or cosine error. Hidden-gene expression prediction is not an approved metric.

The evaluator orients paired differences so positive always means remaining RNA improves query-local state recovery and uses a paired median advantage plus win fraction. Numerical scientific thresholds are required explicit authority inputs; this implementation does not silently choose production thresholds.

## What this does NOT close

This is a structural/semantic successor and decision-rule implementation. It is **not** evidence that a healthy production teacher has passed remaining-RNA necessity.

Still open before any production scientific claim:

- prospective precision authority and numerical acceptance thresholds;
- canonical target-construction authority/root;
- healthy-teacher execution of the identity-only and lawful-global-context/no-RNA interventions;
- execution evidence carried through the current critical-test/anti-cheat path;
- prospective FULL104 masking qualification and evidence-budget authority;
- production geometry, geometry-dependent capacity rerun, EMA timescale, measurement robustness, runtime qualification, and explicit training authority.

Historical T1 checkpoints remain adversarial fixtures only and are not accepted as healthy-teacher evidence.

## Verification

The dedicated GitHub Actions current-V5 regression run executed the following current and spillover suites together:

- remaining-RNA necessity;
- teacher-target semantic successor spillover;
- target/masking successor schema spillover;
- current authority closure;
- Stage-A spillover firewall v1 and v2;
- current address-registry/policy authority;
- current masking-policy authority;
- shared-address query-provider structural tests.

Result: `220 passed` on the primary run and `220 passed` again under the explicit no-skip check. No skipped tests were accepted.

## Boundaries

- `TRAINING_OFF`.
- Protected/pathology/DEV/SEALED/D_shared outcomes remain sealed.
- This change does not freeze production mask burden, RIDGE8, geometry, EMA timescale, optimizer, or training schedule.
- This change does not inspect protected outcomes.
- The JEPA objective remains biological/cellular state, including query-local state, never hidden-gene scalar expression.
