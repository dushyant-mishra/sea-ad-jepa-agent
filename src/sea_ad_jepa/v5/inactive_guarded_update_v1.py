"""Canonical guarded wrapper for the inactive V5 one-update mechanics harness.

The V5 consumer computes forward/backward and verifies postconditions. This
wrapper owns the only lawful mutation route for the rehearsal: the actual
optimizer is bound to PrefreezeOptimizerGuardV1, optimizer completion is proven,
and EMA is executed only through guard.run_ema(). No training or Stage-A
authority is granted.
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
    **kwargs: Any,
) -> dict[str, object]:
    """Run exactly one test-only guarded V5 update with guard-owned EMA."""
    if not isinstance(authority, PrefreezeMechanicalAuthorityV1):
        raise ValueError("PrefreezeMechanicalAuthorityV1 is required")
    if "update_index" not in kwargs:
        raise ValueError("update_index is required")

    optimizer = modules.optimizer
    guard = PrefreezeOptimizerGuardV1(authority, optimizer)
    token = guard.begin_step(authority.optimizer_identity, authority.checkpoint_digest)

    def before_gradient_validation() -> None:
        # This reference path is non-AMP, so the unscale boundary is an explicit
        # no-op. AMP integration uses scaler.unscale_ before marking this state.
        guard.mark_unscaled(token)

    def guarded_optimizer_step(_: dict[str, object]) -> None:
        guard.mark_gradients_valid(token)
        guard.run_optimizer_step(token)
        guard.assert_step_complete(token)

    def guarded_ema_step(momentum: float) -> None:
        m = float(momentum)

        def apply_ema() -> None:
            with torch.no_grad():
                for teacher, online in zip(modules.teacher.parameters(), modules.online.parameters()):
                    teacher.mul_(m).add_(online, alpha=1.0 - m)

        guard.run_ema(token, apply_ema)

    try:
        report = run_inactive_reference_update(
            modules,
            before_gradient_validation=before_gradient_validation,
            guarded_optimizer_step=guarded_optimizer_step,
            guarded_ema_step=guarded_ema_step,
            **kwargs,
        )
    finally:
        guard.close()

    report = dict(report)
    report["guarded_optimizer_step"] = True
    report["guarded_ema"] = True
    report["guard_kind"] = "V5_PREFREEZE_OPTIMIZER_GUARD_V1"
    report["authority_digest"] = authority.authority_digest
    report["training_authorized"] = False
    report["execution_authorized"] = False
    return report
