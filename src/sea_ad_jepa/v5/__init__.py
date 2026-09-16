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

# `from sea_ad_jepa.v5 import *` must not be a hole in the spillover firewall.
# A star-import resolves every name in __all__, and resolving a compatibility name
# triggers __getattr__ below, which imports the quarantined helper -- so listing them
# here would reintroduce exactly the eager load the firewall exists to prevent.
#
# Repository evidence (2026-09-16): no module in src/ or tests/ performs a wildcard
# import of this package, and no caller reaches these symbols through the package at
# all -- every existing use imports the submodule directly. Nothing therefore depends
# on the star-import surface, so it is withdrawn.
#
# Explicit named access (`from sea_ad_jepa.v5 import PackedValidTokens`) still works and
# still loads lazily, via __getattr__. Historical source files are untouched.
__all__: list[str] = []

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
