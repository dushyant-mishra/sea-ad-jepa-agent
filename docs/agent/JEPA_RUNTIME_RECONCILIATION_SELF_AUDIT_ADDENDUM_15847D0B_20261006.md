# JEPA runtime reconciliation — exact-head self-audit addendum — 15847d0b — 2026-10-06

This addendum supersedes earlier current-head/CI status in the full self-audit and c8edfde7 addendum where they conflict.

## Exact audited head

Branch:

`reconcile/v64-runtime-core-onto-prefreeze-main-20261006`

Head:

`15847d0b38bbe20c4cb80b0be33cfd1dec0fe676`

Commit:

`Update governance mutation expectation to fail closed`

## Canonical-governance spillover closure

The prior stale reconciliation test that expected a modified `claim_ladder` to issue a second valid authority was removed/replaced.

The replacement test requires a scientifically altered V3 governance object to fail with the canonical-governance-digest mismatch.

This aligns the older reconciliation suite with the newer red-team contract and the implementation introduced at `c8edfde7...`, which binds rehearsal authority to the exact merged V3 governance digest.

Therefore, for the focused prefreeze authority adapter, the previously identified same-shape semantic-governance spillover defect is now CLOSED at this exact head.

## Fresh verification evidence

GitHub Actions run:

`37532495121`

Workflow:

`v64-runtime-core-reconciliation`

Result:

`SUCCESS`

The focused runtime reconciliation test step completed successfully at exact head `15847d0b...`.

Do not propagate this GREEN to later SHAs without re-running exact-head verification.

## What focused GREEN now supports

At this exact head the focused pure-Python suite supports:

- exact merged V3 governance digest binding for this prefreeze adapter;
- rejection of structurally valid scientific-governance mutation;
- schema-closed governance/receipt structures covered by the focused tests;
- optimizer-object pre/post hook binding in the fake-optimizer surrogate;
- direct/wrong-token optimizer rejection while hooks own the optimizer;
- unscale-before-gradient-validation ordering;
- optimizer exception and ambiguous completion fail-closed behavior;
- one-shot EMA;
- exactly-one-update prefreeze boundary;
- one-shot completed checkpoint receipt and parent digest lineage;
- non-authorizing OFF/SEALED/PROTECTED hard boundaries.

## What this GREEN does NOT prove

The CI workflow installs only `pytest`. Therefore this GREEN does not prove:

1. real `torch.optim.AdamW` hook behavior;
2. `GradScaler.step()` skip/overflow behavior;
3. scaler state continuity;
4. optimizer provenance truth (`optimizer_identity` remains a free label);
5. process-wide optimizer/EMA exclusivity;
6. callback-exception fail-closed behavior for `backward`, `unscale`, or gradient-validation exceptions in the rehearsal wrapper;
7. canonical inactive V5 one-update consumer integration;
8. checkpoint digest provenance from physically persisted bytes;
9. complete deterministic restart state;
10. interrupt/resume equivalence;
11. synthetic/V77 integration through the canonical consumer;
12. any Stage-A or training execution authority.

## Newly retained RED requirement from full self-audit

Before treating the callback rehearsal as a safe canonical spine, add RED tests for exceptions thrown by:

- `backward()`;
- `unscale()`;
- `validate_gradients()`.

Any exception after the step token is armed must leave that authorization unusable; it must not be salvageable by later calls on the reachable guard object.

Also specify/check checkpoint-writer failure semantics. A caller-returned digest is not proof of successful persisted bytes.

## Merge decision

Focused mechanics are now GREEN at `15847d0b...`, but PR #222 is still **not yet qualified as the canonical mutation boundary**.

Do not merge as final runtime closure until at least:

- real local PyTorch optimizer integration is physically tested;
- GradScaler skipped update cannot authorize EMA/cursor advancement;
- optimizer provenance is derived/verified rather than free-labeled;
- callback exceptions fail closed;
- guard is integrated into the canonical inactive/test-only V5 one-update consumer with no alternate reachable optimizer/EMA mutation route;
- deterministic checkpoint/restart completeness and interrupt/resume equivalence are physically demonstrated.

Training remains OFF. Stage A remains OFF. TEST remains SEALED. Morabito remains PROTECTED.
