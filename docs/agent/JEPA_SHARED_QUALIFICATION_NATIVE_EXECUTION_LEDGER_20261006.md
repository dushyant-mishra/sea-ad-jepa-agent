# Shared qualification native-execution ledger — 2026-10-06

Plan: `docs/superpowers/plans/2026-10-06-shared-qualification-interface-implementation-plan.md`
Spec: `docs/agent/JEPA_SHARED_QUALIFICATION_PIPELINE_DESIGN_20261006.md` + final safeguards/lifecycle correction
Execution: Native / RED-first

## Environment ruling

Ruling: this chat has GitHub repository mutation and GitHub Actions inspection, but no repository worktree/shell execution surface. Therefore the plan's local `pytest` RED/GREEN commands are witnessed through a draft PR and GitHub Actions instead. Tests still land before production code, and production code must not be written until the relevant workflow has produced the expected RED. This preserves the TDD requirement while changing only the execution transport.

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

## Status

Task 1: starting RED phase.
