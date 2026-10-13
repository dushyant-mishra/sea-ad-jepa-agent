from __future__ import annotations

import td_relational_successor_gate_v1 as G


class CapabilityReductionError(ValueError):
    pass


_FINE_LABELS = ("1/8", "1/6", "1/4", "1/3")
_RARE_CAPABILITIES = frozenset({
    "REL_RARE_LOCAL_ISLAND_POSITIVE",
    "REL_MULTI_ISLAND_POSITIVE",
    "REL_DONOR_RESTRICTED_POSITIVE",
    "REL_TECHNICAL_TWIN_NEGATIVE",
})
_ALLOWED_CAPABILITIES = frozenset({
    "REL_BROAD_MESO_POSITIVE",
    "REL_FINE_RECURRENT_POSITIVE",
    "REL_RARE_LOCAL_ISLAND_POSITIVE",
    "REL_MULTI_ISLAND_POSITIVE",
    "REL_DONOR_RESTRICTED_POSITIVE",
    "REL_SOURCE_VISIBILITY_STRESS",
    "REL_TECHNICAL_TWIN_NEGATIVE",
    "REL_NULL_NEGATIVE",
    "REL_UNDERPOWERED_POSITIVE",
})


def _collapse(statuses: list[str]) -> str:
    if any(status == "PASS" for status in statuses):
        return "PASS"
    if statuses and all(status == "NOT_ESTIMABLE" for status in statuses):
        return "NOT_ESTIMABLE"
    return "FAIL"


def reduce_capability_status(
    capability_id: str,
    profile: G.RelationalProfileReceipt,
    *,
    rare_increment: G.RareIncrementReceipt | None = None,
) -> str:
    if capability_id not in _ALLOWED_CAPABILITIES:
        raise CapabilityReductionError(f"unknown relational capability: {capability_id}")
    if not isinstance(profile, G.RelationalProfileReceipt):
        raise CapabilityReductionError("profile must be a RelationalProfileReceipt")
    if tuple(profile.scale_results) != G.SCALE_LABELS:
        raise CapabilityReductionError("profile scale grid differs from frozen successor grid")

    if capability_id == "REL_BROAD_MESO_POSITIVE":
        return profile.scale_results["1/2"].status

    if capability_id == "REL_FINE_RECURRENT_POSITIVE":
        return _collapse([profile.scale_results[label].status for label in _FINE_LABELS])

    if capability_id in _RARE_CAPABILITIES:
        if not isinstance(rare_increment, G.RareIncrementReceipt):
            raise CapabilityReductionError(f"rare_increment is required for {capability_id}")
        if rare_increment.source != profile.source or rare_increment.panel_id != profile.panel_id:
            raise CapabilityReductionError("rare increment source/panel mismatch")
        if tuple(rare_increment.scale_results) != G.SCALE_LABELS:
            raise CapabilityReductionError("rare increment scale grid differs from frozen successor grid")
        return _collapse([rare_increment.scale_results[label].status for label in _FINE_LABELS])

    if capability_id in {"REL_NULL_NEGATIVE", "REL_UNDERPOWERED_POSITIVE", "REL_SOURCE_VISIBILITY_STRESS"}:
        return _collapse([profile.scale_results[label].status for label in G.SCALE_LABELS])

    raise CapabilityReductionError(f"no frozen reduction rule for {capability_id}")
