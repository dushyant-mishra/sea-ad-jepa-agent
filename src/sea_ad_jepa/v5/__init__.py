"""Prospective data-first Teacher/Student V5 mechanics.

Nothing in this package is execution authority.

Current authority submodules must remain import-isolated from historical and
prospective helper modules.  The compatibility exports below are therefore
resolved lazily only when an old caller explicitly asks for one of them.
"""
from __future__ import annotations

from importlib import import_module
from typing import Any


_GEOMETRY_PUBLIC_EXPORTS = (
    "PackedValidTokens",
    "anchored_triplet_capacity",
    "partial_fine_derangement",
    "evidence_telemetry",
    "ragged_relational_support",
    "pack_valid_tokens",
    "operator_homogeneous_microbatch_plan",
    "mean_loss_weight",
    "weighted_block_jepa_loss",
    "weighted_loss_partition_weight",
)

# Preserve the historical star-import surface without importing the module on
# package initialization.  These names are compatibility-only and are not
# current production authority.
__all__ = list(_GEOMETRY_PUBLIC_EXPORTS)

_LAZY_COMPATIBILITY_EXPORTS = {
    **{name: (".data_first_geometry", name) for name in _GEOMETRY_PUBLIC_EXPORTS},
    "DonorCapacity": (".proposal_policy_v1", "DonorCapacity"),
    "derive_exposure_constrained_target_mixture": (
        ".proposal_policy_v1",
        "derive_exposure_constrained_target_mixture",
    ),
    "relational_direct_target_group_probabilities": (
        ".proposal_policy_v1",
        "relational_direct_target_group_probabilities",
    ),
}


def __getattr__(name: str) -> Any:
    """Resolve historical/prospective convenience exports only on demand."""

    try:
        module_name, attribute_name = _LAZY_COMPATIBILITY_EXPORTS[name]
    except KeyError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc
    value = getattr(import_module(module_name, __name__), attribute_name)
    globals()[name] = value
    return value
