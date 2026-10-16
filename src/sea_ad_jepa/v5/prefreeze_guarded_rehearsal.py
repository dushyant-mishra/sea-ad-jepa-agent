"""Non-authorizing full-cycle rehearsal for the prefreeze runtime guard.

This is deliberately not a trainer. It composes callbacks supplied by tests or
an inactive mechanics harness so ordering can be proved without selecting
biology, loading protected data, or granting execution authority.
"""
from __future__ import annotations

from typing import Any, Callable

try:
    from .prefreeze_runtime_authority import (
        PrefreezeMechanicalAuthorityV1,
        PrefreezeOptimizerGuardV1,
        PrefreezeGovernanceError,
        StepCompletionError,
    )
except ImportError:  # direct-file loading used by focused pure-Python tests
    from prefreeze_runtime_authority import (
        PrefreezeMechanicalAuthorityV1,
        PrefreezeOptimizerGuardV1,
        PrefreezeGovernanceError,
        StepCompletionError,
    )


REHEARSAL_SCHEMA = "V5_PREFREEZE_GUARDED_REHEARSAL_V2"


def _callable(value: object, name: str) -> Callable[[], Any]:
    if not callable(value):
        raise PrefreezeGovernanceError(f"{name} callback is required")
    return value


def run_test_only_guarded_rehearsal(
    *,
    authority: PrefreezeMechanicalAuthorityV1,
    guard: PrefreezeOptimizerGuardV1,
    optimizer_identity: str,
    backward: Callable[[], Any],
    unscale: Callable[[], Any],
    validate_gradients: Callable[[], bool],
    ema_update: Callable[[], Any],
    checkpoint: Callable[[], str],
) -> dict[str, Any]:
    """Exercise one optimizer-bound step, EMA, checkpoint, and reload proof."""
    if not isinstance(authority, PrefreezeMechanicalAuthorityV1):
        raise PrefreezeGovernanceError("rehearsal requires prefreeze mechanical authority")
    authority._validate_digest()
    if not isinstance(guard, PrefreezeOptimizerGuardV1) or guard.authority is not authority:
        raise PrefreezeGovernanceError("guard must be bound to the supplied prefreeze authority")

    backward = _callable(backward, "backward")
    unscale = _callable(unscale, "unscale")
    validate_gradients = _callable(validate_gradients, "validate_gradients")
    ema_update = _callable(ema_update, "ema_update")
    checkpoint = _callable(checkpoint, "checkpoint")

    starting_checkpoint_digest = authority.checkpoint_digest
    token = guard.begin_step(optimizer_identity, starting_checkpoint_digest)

    backward()
    unscale()
    guard.mark_unscaled(token)

    valid = validate_gradients()
    if valid is not True:
        guard.reject_step(token, "gradient validation failed")
        raise StepCompletionError("gradient validation failed; optimizer and EMA forbidden")
    guard.mark_gradients_valid(token)

    guard.run_optimizer_step(token)
    guard.assert_step_complete(token)
    guard.run_ema(token, ema_update)

    checkpoint_digest = checkpoint()
    receipt = guard.completed_checkpoint_receipt(token, checkpoint_digest)
    PrefreezeMechanicalAuthorityV1.verify_completed_checkpoint_receipt(
        receipt, checkpoint_digest, governance_state=authority.governance_state
    )

    return {
        "schema": REHEARSAL_SCHEMA,
        "rehearsal_only": True,
        "training_authorized": False,
        "execution_authorized": False,
        "guarded_step_token": token,
        "starting_checkpoint_digest": starting_checkpoint_digest,
        "checkpoint_digest": checkpoint_digest,
        "checkpoint_receipt": receipt,
    }
