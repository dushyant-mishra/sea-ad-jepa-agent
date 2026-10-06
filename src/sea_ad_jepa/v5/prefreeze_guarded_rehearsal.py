"""Test-only full-cycle rehearsal for the prefreeze runtime guard.

This is deliberately not a trainer.  It composes callbacks supplied by a test
or inactive mechanics harness so the ordering can be proved without selecting
biology, loading protected data, or granting execution authority.
"""
from __future__ import annotations

from typing import Any, Callable

from prefreeze_runtime_authority import (
    CurrentTrainingAuthorityV2,
    OptimizerGuardV4,
    PrefreezeGovernanceError,
    StepCompletionError,
)


REHEARSAL_SCHEMA = "V5_PREFREEZE_GUARDED_REHEARSAL_V1"


def _callable(value: object, name: str) -> Callable[[], Any]:
    if not callable(value):
        raise PrefreezeGovernanceError(f"{name} callback is required")
    return value


def run_test_only_guarded_rehearsal(
    *,
    authority: CurrentTrainingAuthorityV2,
    guard: OptimizerGuardV4,
    optimizer_identity: str,
    backward: Callable[[], Any],
    unscale: Callable[[], Any],
    validate_gradients: Callable[[], bool],
    optimizer_step: Callable[[], Any],
    ema_update: Callable[[], Any],
    checkpoint: Callable[[], str],
) -> dict[str, Any]:
    """Exercise one guarded update and checkpoint round-trip in test mode only."""
    if not isinstance(authority, CurrentTrainingAuthorityV2) or authority.test_only is not True:
        raise PrefreezeGovernanceError("guarded rehearsal requires test-only authority")
    authority._validate_digest()
    if not isinstance(guard, OptimizerGuardV4) or guard.authority is not authority:
        raise PrefreezeGovernanceError("guard must be bound to the supplied test-only authority")

    backward = _callable(backward, "backward")
    unscale = _callable(unscale, "unscale")
    validate_gradients = _callable(validate_gradients, "validate_gradients")
    optimizer_step = _callable(optimizer_step, "optimizer_step")
    ema_update = _callable(ema_update, "ema_update")
    checkpoint = _callable(checkpoint, "checkpoint")

    token = guard.begin_step(optimizer_identity, authority.checkpoint_digest)

    backward()
    unscale()
    guard.mark_unscaled(token)

    valid = validate_gradients()
    if valid is not True:
        guard.reject_step(token, "gradient validation failed")
        raise StepCompletionError("gradient validation failed; optimizer and EMA forbidden")
    guard.mark_gradients_valid(token)

    guard.run_optimizer_step(token, optimizer_step)
    guard.assert_step_complete(token)

    # Authorization must be consumed before the EMA mutation itself.
    guard.authorize_ema(token)
    ema_update()

    checkpoint_digest = checkpoint()
    receipt = authority.checkpoint_receipt()
    # The reload call is the fail-closed digest check; a different physical
    # checkpoint cannot inherit this authority receipt.
    CurrentTrainingAuthorityV2.reload(receipt, checkpoint_digest)

    return {
        "schema": REHEARSAL_SCHEMA,
        "test_only": True,
        "training_authorized": False,
        "execution_authorized": False,
        "checkpoint_digest": checkpoint_digest,
        "authority_receipt": receipt,
    }
