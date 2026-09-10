"""Executable scientific-update packing/restart invariance gate for V5.

Microbatch packing is a hardware decision. It may split a frozen scientific
update, but it may not change presentation membership or order within that
update. Restart must resume at the exact frozen scientific-update cursor.
Randomness is bound to the keyed RNG contract whose scientific address excludes
packing/tensor/device coordinates.

This gate checks mechanics only and never grants training authority.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

FORBIDDEN_RNG_COORDINATES = (
    "device_ordinal",
    "microbatch_ordinal",
    "packing_shape",
    "tensor_position",
)


def _id(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be nonempty")
    return value


def _sha(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"{name} must be a SHA-256 hex digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be hexadecimal") from exc
    return value.lower()


def _reference(updates: Sequence[Sequence[object]]) -> tuple[tuple[str, ...], ...]:
    out = []
    seen = set()
    if not updates:
        raise ValueError("reference_updates cannot be empty")
    for i, update in enumerate(updates):
        ids = tuple(str(v) for v in update)
        if not ids or any(not v for v in ids):
            raise ValueError(f"reference update {i} must be nonempty")
        for value in ids:
            if value in seen:
                raise ValueError("presentation identities must be globally unique")
            seen.add(value)
        out.append(ids)
    return tuple(out)


def _packed(updates: Sequence[Sequence[Sequence[object]]], name: str) -> tuple[tuple[str, ...], ...]:
    out = []
    if not updates:
        raise ValueError(f"{name} cannot be empty")
    for i, microbatches in enumerate(updates):
        if not microbatches:
            raise ValueError(f"{name} update {i} has no microbatches")
        flat = []
        for j, microbatch in enumerate(microbatches):
            ids = tuple(str(v) for v in microbatch)
            if not ids or any(not v for v in ids):
                raise ValueError(f"{name} update {i} microbatch {j} must be nonempty")
            flat.extend(ids)
        out.append(tuple(flat))
    return tuple(out)


@dataclass(frozen=True)
class PackingRestartInvarianceAuthorityV1:
    authority_id: str
    scientific_schedule_authority_id: str
    scientific_schedule_artifact_sha256: str
    keyed_rng_contract_sha256: str
    proposal_weight_artifact_sha256: str
    dimension_authority_artifact_sha256: str
    forbidden_rng_coordinates: tuple[str, ...]
    rules_frozen_before_optimizer_start: bool

    def validate(self) -> None:
        _id(self.authority_id, "authority_id")
        _id(self.scientific_schedule_authority_id, "scientific_schedule_authority_id")
        _sha(self.scientific_schedule_artifact_sha256, "scientific_schedule_artifact_sha256")
        _sha(self.keyed_rng_contract_sha256, "keyed_rng_contract_sha256")
        _sha(self.proposal_weight_artifact_sha256, "proposal_weight_artifact_sha256")
        _sha(self.dimension_authority_artifact_sha256, "dimension_authority_artifact_sha256")
        if self.forbidden_rng_coordinates != FORBIDDEN_RNG_COORDINATES:
            raise ValueError("forbidden_rng_coordinates must equal the canonical packing/device exclusion set")
        if self.rules_frozen_before_optimizer_start is not True:
            raise ValueError("packing/restart rules must be frozen before optimizer start")


def qualify_packing_restart_invariance(
    *,
    reference_updates: Sequence[Sequence[object]],
    packed_updates: Sequence[Sequence[Sequence[object]]],
    restart_update_cursor: int,
    resumed_packed_updates: Sequence[Sequence[Sequence[object]]],
    authority: PackingRestartInvarianceAuthorityV1,
) -> dict[str, object]:
    authority.validate()
    ref = _reference(reference_updates)
    packed = _packed(packed_updates, "packed_updates")
    if packed != ref:
        raise RuntimeError("STOP_V5_PACKING_CHANGED_SCIENTIFIC_UPDATE_MEMBERSHIP_OR_ORDER")
    if isinstance(restart_update_cursor, bool) or not isinstance(restart_update_cursor, int):
        raise ValueError("restart_update_cursor must be an exact integer")
    if restart_update_cursor < 0 or restart_update_cursor >= len(ref):
        raise ValueError("restart_update_cursor outside frozen scientific update range")
    resumed = _packed(resumed_packed_updates, "resumed_packed_updates")
    if resumed != ref[restart_update_cursor:]:
        raise RuntimeError("STOP_V5_RESTART_CURSOR_OR_SUFFIX_MISMATCH")

    return {
        "schema": "JEPA_V5_PACKING_ORDER_RESTART_INVARIANCE_V1",
        "authority_id": authority.authority_id,
        "scientific_schedule_authority_id": authority.scientific_schedule_authority_id,
        "scientific_schedule_artifact_sha256": authority.scientific_schedule_artifact_sha256,
        "keyed_rng_contract_sha256": authority.keyed_rng_contract_sha256,
        "proposal_weight_artifact_sha256": authority.proposal_weight_artifact_sha256,
        "dimension_authority_artifact_sha256": authority.dimension_authority_artifact_sha256,
        "scientific_updates": len(ref),
        "restart_update_cursor": restart_update_cursor,
        "packing_changes_scientific_membership": False,
        "packing_changes_scientific_order": False,
        "restart_replays_or_skips_updates": False,
        "forbidden_rng_coordinates": FORBIDDEN_RNG_COORDINATES,
        "passed": True,
        "training_authorized": False,
    }
