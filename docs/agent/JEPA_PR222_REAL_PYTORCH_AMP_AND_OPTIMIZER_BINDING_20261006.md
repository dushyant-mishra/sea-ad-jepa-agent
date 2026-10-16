# PR #222 real PyTorch / AMP / optimizer-provenance checkpoint — 2026-10-06

## Scope

This checkpoint records runtime-reconciliation work on draft PR #222 (`reconcile/v64-runtime-core-onto-prefreeze-main-20261006`). It is rehearsal-only and non-authorizing.

Hard state remains:
- TRAINING = OFF
- STAGE_A_EXECUTION = OFF
- MULTIMODAL_TRAINING = OFF
- 500K = NOT_AUTHORIZED
- STAGE4 = NOT_AUTHORIZED
- TEST = SEALED
- MORABITO = PROTECTED

## Real PyTorch / GradScaler RED

Commit:
`5bc85b78e405173d9c5adb1d92ab690e3cd95b2f`

The dedicated runtime workflow now installs CPU PyTorch and executes `tests/test_v5_prefreeze_runtime_torch_integration.py`.

The RED required:
1. a real `torch.optim.SGD` update to be observed through the bound optimizer hooks;
2. a finite CPU `torch.amp.GradScaler` step to complete through the guard;
3. a nonfinite-gradient GradScaler skip to leave the guarded step incomplete and prevent EMA.

Workflow `37547452413` used PyTorch `2.14.1+cpu` and produced `2 failed / 53 passed`: the direct real-SGD test already passed; only the two missing scaler-path tests failed because `PrefreezeOptimizerGuardV1` had no `run_scaler_step` method.

## GradScaler GREEN

Commit:
`9e71d67d3de58fc622b8773cfeb914ff5c7e14dc`

`PrefreezeOptimizerGuardV1.run_scaler_step()` now routes the actual optimizer through the scaler while preserving the same pre/post-hook token proof.

If GradScaler skips `optimizer.step()`, the optimizer hooks do not consume/complete the token. The guard rejects the step and EMA remains unavailable.

Workflow `37547731781`: SUCCESS.

This physically demonstrates the CPU AMP skipped-step invariant; it is not a mock-only claim.

## Optimizer-configuration provenance RED

Commit:
`7e7f30bcf9235fb23bdc7e139e0d783ab927a46b`

A real SGD optimizer was attached to an authority whose caller-supplied label claimed AdamW.

Workflow `37547893704`: `1 failed / 55 passed`.

The sole failure proved the mismatch was accepted. This confirmed that object-bound hooks alone did not bind the authority to the optimizer's configured type/hyperparameters.

## Optimizer-configuration provenance GREEN

Implementation commit:
`69175e6e2a2b2cc6ea72438ce53b7b53c8f3de16`

Test/adoption commit:
`a8911a56b98b34f27f11860ac15b99f546784cac`

For optimizers exposing a real configuration surface (`defaults` + `param_groups`), the runtime now derives a deterministic optimizer identity from:
- fully qualified optimizer class;
- normalized optimizer defaults;
- normalized parameter-group hyperparameters;
- parameter-group parameter counts;
- parameter shapes;
- parameter dtypes.

`PrefreezeMechanicalAuthorityV1.issue_for_optimizer()` derives the identity from the actual optimizer object. `PrefreezeOptimizerGuardV1` recomputes it at attachment and fails closed on mismatch.

The real-PyTorch tests now prove:
- forged AdamW authority on SGD is rejected;
- changing SGD hyperparameters changes the bound optimizer identity;
- real SGD hook completion still works;
- finite GradScaler works;
- nonfinite GradScaler skip cannot authorize EMA.

Workflow `37548159745`: SUCCESS.

## Convergence decision

Do not build a second checkpoint/restart implementation in PR #222.

PR #221 already contains the inactive canonical guarded-update/checkpoint surface:
- `src/sea_ad_jepa/v5/inactive_guarded_update_v1.py`
- `src/sea_ad_jepa/v5/inactive_checkpoint_binding_v1.py`
- `src/sea_ad_jepa/v5/inactive_update_reference.py`

The next work should converge PR #222's stronger actual-optimizer/AMP guard into PR #221's consumer, then extend #221's checkpoint evidence from roundtrip restore to deterministic interrupt/resume equivalence.

## Remaining blockers

1. No competing parallel guard/consumer should survive final convergence.
2. Prove no reachable unguarded optimizer/EMA mutation handle around the canonical consumer.
3. Extend checkpoint/restart proof to interrupt/resume equivalence.
4. Account for GradScaler state where AMP is in scope.
5. Bind the final runtime successor into PR #223 physical proof statuses.
6. Keep real-RNA execution authority absent unless separately approved.
