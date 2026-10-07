"""Canonical guarded wrapper for the inactive V5 one-update mechanics harness.

The V5 consumer computes the scientific losses and verifies postconditions.
This wrapper owns backward scaling and the only lawful mutation route for the
rehearsal: the actual optimizer is bound to PrefreezeOptimizerGuardV1,
optimizer completion is proven, and EMA is executed only through guard.run_ema().
After all update postconditions pass, an optional checkpoint-digest callback may
request the guard's completed optimizer->EMA receipt while the guard is still
open. No training or Stage-A authority is granted.
"""
from __future__ import annotations

from typing import Any

import torch

from .inactive_update_reference import V5ReferenceModules, run_inactive_reference_update
from .prefreeze_runtime_authority import (
    PrefreezeMechanicalAuthorityV1,
    PrefreezeOptimizerGuardV1,
)


def run_guarded_inactive_reference_update(
    modules: V5ReferenceModules,
    *,
    authority: PrefreezeMechanicalAuthorityV1,
    scaler: Any | None = None,
    completion_checkpoint_digest: Any | None = None,
    **kwargs: Any,
) -> dict[str, object]:
    """Run exactly one test-only guarded V5 update with optional AMP scaling."""
    if not isinstance(authority, PrefreezeMechanicalAuthorityV1):
        raise ValueError("PrefreezeMechanicalAuthorityV1 is required")
    if "update_index" not in kwargs:
        raise ValueError("update_index is required")
    if completion_checkpoint_digest is not None and not callable(completion_checkpoint_digest):
        raise ValueError("completion_checkpoint_digest must be callable")
    if scaler is not None:
        for name in ("scale", "unscale_", "step", "update"):
            if not callable(getattr(scaler, name, None)):
                raise ValueError(f"scaler missing callable {name}")

    optimizer = modules.optimizer
    guard = PrefreezeOptimizerGuardV1(authority, optimizer)
    token = guard.begin_step(authority.optimizer_identity, authority.checkpoint_digest)

    def backward_loss(loss: torch.Tensor) -> None:
        if scaler is None:
            loss.backward()
        else:
            scaler.scale(loss).backward()

    def before_gradient_validation() -> None:
        if scaler is not None:
            scaler.unscale_(optimizer)
        guard.mark_unscaled(token)

    def guarded_optimizer_step(_: dict[str, object]) -> None:
        guard.mark_gradients_valid(token)
        if scaler is None:
            guard.run_optimizer_step(token)
        else:
            try:
                guard.run_scaler_step(token, scaler)
            finally:
                scaler.update()
        guard.assert_step_complete(token)

    def guarded_ema_step(momentum: float) -> None:
        m = float(momentum)

        def apply_ema() -> None:
            with torch.no_grad():
                for teacher, online in zip(modules.teacher.parameters(), modules.online.parameters()):
                    teacher.mul_(m).add_(online, alpha=1.0 - m)

        guard.run_ema(token, apply_ema)

    completed_guard_receipt = None
    try:
        report = run_inactive_reference_update(
            modules,
            backward_loss=backward_loss,
            before_gradient_validation=before_gradient_validation,
            guarded_optimizer_step=guarded_optimizer_step,
            guarded_ema_step=guarded_ema_step,
            **kwargs,
        )
        if completion_checkpoint_digest is not None:
            checkpoint_digest = completion_checkpoint_digest()
            completed_guard_receipt = guard.completed_checkpoint_receipt(token, checkpoint_digest)
    finally:
        guard.close()

    report = dict(report)
    report["guarded_optimizer_step"] = True
    report["guarded_ema"] = True
    report["amp_scaler_used"] = scaler is not None
    report["guard_kind"] = "V5_PREFREEZE_OPTIMIZER_GUARD_V1"
    report["authority_digest"] = authority.authority_digest
    report["completed_guard_receipt"] = completed_guard_receipt
    report["training_authorized"] = False
    report["execution_authorized"] = False
    return report
