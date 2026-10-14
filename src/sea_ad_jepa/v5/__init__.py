"""Prospective data-first Teacher/Student V5 mechanics.

Nothing in this package is execution authority.
"""
from __future__ import annotations

import importlib.abc
import sys

_PRIVATE_RUNTIME_IMPLEMENTATIONS = frozenset({
    __name__ + "._inactive_checkpoint_binding_impl_v1",
    __name__ + "._ema_bound_runtime_proof_impl_v1",
})
_PRIVATE_RUNTIME_IMPORT_PERMITS: set[str] = set()


class _PrivateRuntimeImplementationGuard(importlib.abc.MetaPathFinder):
    """Fail closed if a private implementation is imported outside its public wrapper."""

    _jepa_v5_private_runtime_guard = True

    def find_spec(self, fullname, path=None, target=None):
        if fullname in _PRIVATE_RUNTIME_IMPLEMENTATIONS and fullname not in _PRIVATE_RUNTIME_IMPORT_PERMITS:
            raise ImportError(
                f"{fullname} is a private implementation; import its canonical public wrapper"
            )
        return None


if not any(getattr(finder, "_jepa_v5_private_runtime_guard", False) for finder in sys.meta_path):
    sys.meta_path.insert(0, _PrivateRuntimeImplementationGuard())


def _permit_private_runtime_import(fullname: str) -> None:
    if fullname not in _PRIVATE_RUNTIME_IMPLEMENTATIONS:
        raise RuntimeError("unknown private runtime implementation")
    _PRIVATE_RUNTIME_IMPORT_PERMITS.add(fullname)


def _revoke_private_runtime_import(fullname: str) -> None:
    _PRIVATE_RUNTIME_IMPORT_PERMITS.discard(fullname)


from .data_first_geometry import (
    PackedValidTokens, anchored_triplet_capacity, partial_fine_derangement,
    evidence_telemetry, ragged_relational_support, pack_valid_tokens,
    operator_homogeneous_microbatch_plan, mean_loss_weight,
    weighted_block_jepa_loss, weighted_loss_partition_weight,
)
__all__=[
    'PackedValidTokens','anchored_triplet_capacity','partial_fine_derangement','evidence_telemetry','ragged_relational_support',
    'pack_valid_tokens','operator_homogeneous_microbatch_plan','mean_loss_weight','weighted_block_jepa_loss','weighted_loss_partition_weight'
]

# Proposal algebra is prospective/design-only; importing this package does not activate it.
from .proposal_policy_v1 import DonorCapacity, derive_exposure_constrained_target_mixture, relational_direct_target_group_probabilities
