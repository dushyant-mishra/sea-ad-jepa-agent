# Shared qualification implementation plan amendments — 2026-10-06

Status: `BINDING_EXECUTION_AMENDMENT__TRAINING_OFF__NO_MUTATION_AUTHORITY`

These amendments apply to `docs/superpowers/plans/2026-10-06-shared-qualification-interface-implementation-plan.md` before any production implementation code is added.

## Amendment 1 — Mutation authority is structurally OFF-only in V1

`MutationAuthorityV1` in this implementation slice may represent only `MUTATION_NOT_AUTHORIZED`.

It must not contain a future authorized mutation state, dormant switch, convenience constructor, or permissive enum member. A mutation-authorized schema belongs to the later #221/#222 runtime-convergence successor and requires a separate RED-first plan and authority review.

Consequence: any `BOUNDED_MUTATION_REHEARSAL` protocol request in this slice may be representable as an experiment request only if validation explicitly records that no compatible mutation authority exists; it cannot create a runnable mutation path.

## Amendment 2 — Feature identity must be mechanically proven

`FeatureIdentityReceiptV1` must not accept a boolean/attestation such as `mapping_verified=True` as evidence that registry/order/reader/tokenizer/tensor-axis identities agree.

The implementation must recompute a canonical ordered-ID digest relationship from independently inspectable inputs, or verify a cryptographically bound producer receipt whose ordered identifiers/inputs are themselves independently checkable.

The RED suite must include a well-formed but semantically permuted feature mapping that fails even when dimensions, byte counts, and individual component digests look valid.

This amendment directly guards against recurrence of the historical 41K registry-rank/source-index versus matrix-column identity failure.

## Amendment 3 — Experiment requests never become scientific winners

`QualificationProtocolV1` may request one candidate representation family for one experiment, may evaluate one candidate estimand/weighting rule, and may carry exploratory thresholds. None of those fields create or imply:

- `representation_winner`;
- `selected_estimand`;
- deciding numeric thresholds;
- stronger claim authority.

RED tests must prove:

- requesting `PROGRAM_STATE` or any other approved family does not create winner authority;
- evaluating `DONOR_WEIGHTED` or another candidate estimand does not create selected-estimand authority;
- `EXPLORATORY_ONLY` thresholds cannot populate deciding-threshold state.

## Execution consequence

Production code remains blocked until the strengthened Task-1 tests have produced the expected RED. Tasks 3 and 4 must implement Amendments 2 and 1 respectively before being eligible for GREEN completion.

All global boundaries remain unchanged: `TRAINING=OFF`, `STAGE_A_EXECUTION=OFF`, `MULTIMODAL_TRAINING=OFF`, `500K=NOT_AUTHORIZED`, `STAGE4=NOT_AUTHORIZED`, `TEST=SEALED`, `MORABITO=PROTECTED`.
