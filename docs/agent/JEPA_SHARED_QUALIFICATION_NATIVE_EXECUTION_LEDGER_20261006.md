# Shared qualification native-execution ledger — 2026-10-06

Plan: `docs/superpowers/plans/2026-10-06-shared-qualification-interface-implementation-plan.md`
Spec: `docs/agent/JEPA_SHARED_QUALIFICATION_PIPELINE_DESIGN_20261006.md` + final safeguards/lifecycle correction
Execution: Native / RED-first
Implementation PR: #223 (`shared-qualification-interface-v1-20261006`)

## Environment ruling

Ruling: this chat has GitHub repository mutation and GitHub Actions inspection, but no repository worktree/shell execution surface. Therefore the plan's local `pytest` RED/GREEN commands are witnessed through a draft PR and GitHub Actions instead. Tests still land before production code, and production code must not be written until the relevant workflow has produced the expected RED. This preserves the TDD requirement while changing only the execution transport.

## Binding review amendments

See `docs/agent/JEPA_SHARED_QUALIFICATION_PLAN_AMENDMENTS_20261006.md` at commit `12d27476056de1ff0b69b8476803ec5a4270128d`.

- V1 mutation authority is OFF-only; no usable future authorized state in this slice.
- Feature identity must be mechanically proven, never boolean-attested.
- Experiment-specific representation/estimand/threshold requests must not become winner/selected/deciding authority.

## Pre-flight shared interfaces

- Task 1 `QualificationProtocolV1` is consumed by Tasks 4, 5, 6, 8 and downstream runtime/adapter plans. Exact governance binding and execution mode are therefore foundational.
- Task 2 visibility declarations are consumed by batch/adapters and q-safety descendants; no declassification is permitted in V1.
- Task 3 feature/batch identities are consumed by receipts and lifecycle provenance; packing metadata must stay outside scientific identity.
- Task 4 authorities consume Task 1 protocol and constrain Task 5 mutation lifecycle.
- Task 5 lifecycle supplies run identity/state to Tasks 7/8.
- Task 6 q-safety/control roster is protocol-bound but does not implement normalization.
- Task 7 oracle consumes frozen ordinary outputs only and must not feed upstream.
- Task 8 receipts compose prior task digests without granting authority.

No conflict found with the frozen spec. Runtime convergence and adapters remain out of scope for this plan.

## Task 1 — protocol/governance binding

RED 1: commit `891b0372cbc5144f29bbd66af307db43fbf71896`; workflow `37536914465` failed with `ModuleNotFoundError: sea_ad_jepa.qualification`, proving the strengthened protocol tests preceded production code.

GREEN 1: implementation through `c5fe0d273ca47a40bdd66f01f9707c3e1f91b6e6`; workflow `37537061400` passed, including untouched PR #220 governance tests.

Self-audit finding: `QualificationProtocolV1.validate()` did not reject a non-finite exploratory threshold; only later digesting would have failed. Added RED at `5fab889f59598a3fd4e76bb569bd324ee12caf45`; workflow `37537186060` failed exactly on `test_protocol_validation_rejects_nonfinite_exploratory_thresholds` with 55 other tests passing.

Repair: `d53394d836f645b4a6810e606163406ef768c69a`; workflow `37537287392` SUCCESS.

Task 1: complete. Exact governance digest is bound; representation/estimand requests remain experiment-specific rather than winner authority; exploratory thresholds cannot populate deciding state; malformed threshold values fail closed.

## Task 2 — transitive visibility firewall

RED: commit `18905c10f5f66bb251b1b7a495caee07227acd0a`; workflow `37537419024` failed with `ModuleNotFoundError: sea_ad_jepa.qualification.visibility`.

GREEN: implementation `fa59c6b157220324e2d33996bf3450b849b58d8b`; workflow `37537503989` SUCCESS.

Self-audit: V1 intentionally rejects mixed-parent visibility derivations rather than trying to infer a least-restrictive class. There is no declassification API. `SPLIT_ONLY`, `ORACLE_ONLY`, and `LAWFUL_OPERATOR_CONTEXT` cannot become free model/preprocessing inputs through derivation.

Task 2: complete.

## Task 3 ruling — mechanical feature identity proof

Ruling: the original plan's digest-only `FeatureIdentityReceiptV1` is insufficient under the binding review amendment because a boolean or self-attested digest relationship could repeat the historical 41K semantic mapping failure. V1 will construct the receipt from independently inspectable ordered ID sequences and recompute every chain digest mechanically. A well-formed permutation must fail even when dimensions and per-component hash syntax are valid. Persisted downstream receipts may bind the resulting proof digest, but construction/validation requires inspectable ordered identifiers.

## Status

Task 3: starting RED phase for feature-chain permutation and packing/scientific-identity separation.
