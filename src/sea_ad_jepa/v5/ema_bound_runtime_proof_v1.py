"""Non-authorizing presentation-normalized EMA binding for the canonical V5 rehearsal.

This successor restores the authenticated V5 EMA mechanics: teacher age is
measured in successful base-cell presentations and the scalar momentum used for
one completed update is derived from an explicitly supplied presentation
half-life. This module selects no production half-life and grants no execution
or training authority.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from .ema_presentation_v1 import ema_momentum_for_presentations
from .inactive_checkpoint_binding_v1 import (
    V5PrefreezeBoundCheckpointV1,
    issue_prefreeze_authority_from_bound_checkpoint,
)
from .inactive_guarded_update_v1 import run_guarded_inactive_reference_update
from .inactive_update_reference import V5ReferenceModules
from .prefreeze_runtime_authority import PrefreezeMechanicalAuthorityV1

EMA_BINDING_SCHEMA = "V5_PREFREEZE_PRESENTATION_EMA_BOUND_AUTHORITY_V1"
PRESENTATION_EMA_CONFIGURATION_SCHEMA = "V5_PRESENTATION_EMA_CONFIGURATION_V1"
PRESENTATION_EMA_COMPLETED_UPDATE_PROOF_SCHEMA = "V5_PRESENTATION_EMA_COMPLETED_UPDATE_PROOF_V1"
PRESENTATION_UNIT_SUCCESSFUL_BASE_CELLS = "SUCCESSFUL_BASE_CELL_PRESENTATIONS"


def _digest(value: object) -> str:
    raw = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _require_sha256(value: object, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or value.lower() != value:
        raise RuntimeError(f"{label} must be lowercase SHA-256")
    try:
        int(value, 16)
    except ValueError as exc:
        raise RuntimeError(f"{label} must be lowercase SHA-256") from exc
    return value


def presentation_ema_configuration_identity(*, half_life_presentations: int, presentation_unit_id: str) -> str:
    """Bind explicit rehearsal EMA timescale mechanics without selecting production authority."""
    if isinstance(half_life_presentations, bool) or not isinstance(half_life_presentations, int) or half_life_presentations < 1:
        raise ValueError("half_life_presentations must be a positive integer")
    if not isinstance(presentation_unit_id, str) or not presentation_unit_id.strip():
        raise ValueError("presentation_unit_id must be non-empty")
    core = {
        "schema": PRESENTATION_EMA_CONFIGURATION_SCHEMA,
        "half_life_presentations": half_life_presentations,
        "presentation_unit_id": presentation_unit_id.strip(),
    }
    return f"V5_PRESENTATION_EMA:{_digest(core)}"


@dataclass(frozen=True)
class PresentationEmaBoundPrefreezeAuthorityV1:
    """Exact parent mechanical authority plus explicit presentation-EMA mechanics."""

    base_authority: PrefreezeMechanicalAuthorityV1
    parent_runtime_source_sha256: str
    half_life_presentations: int
    presentation_unit_id: str
    ema_configuration_identity: str
    binding_digest: str
    training_authorized: bool = False
    execution_authorized: bool = False
    production_promotable: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.base_authority, PrefreezeMechanicalAuthorityV1):
            raise RuntimeError("presentation-EMA authority requires PrefreezeMechanicalAuthorityV1")
        self.base_authority._validate_digest()
        _require_sha256(self.parent_runtime_source_sha256, "presentation-EMA parent runtime digest")
        expected = presentation_ema_configuration_identity(
            half_life_presentations=self.half_life_presentations,
            presentation_unit_id=self.presentation_unit_id,
        )
        if self.ema_configuration_identity != expected:
            raise RuntimeError("presentation EMA configuration identity mismatch")
        if self.training_authorized or self.execution_authorized or self.production_promotable:
            raise RuntimeError("presentation-EMA rehearsal authority cannot authorize execution or training")
        if self.binding_digest != _digest(self._core()):
            raise RuntimeError("presentation-EMA authority digest mismatch")

    @property
    def optimizer_identity(self) -> str:
        return self.base_authority.optimizer_identity

    @property
    def checkpoint_digest(self) -> str:
        return self.base_authority.checkpoint_digest

    @property
    def authority_digest(self) -> str:
        return self.base_authority.authority_digest

    def _core(self) -> dict[str, object]:
        return {
            "schema": EMA_BINDING_SCHEMA,
            "base_authority_digest": self.base_authority.authority_digest,
            "parent_checkpoint_digest": self.base_authority.checkpoint_digest,
            "parent_runtime_source_sha256": self.parent_runtime_source_sha256,
            "ema_configuration_identity": self.ema_configuration_identity,
            "training_authorized": False,
            "execution_authorized": False,
            "production_promotable": False,
        }

    def verify_ema_configuration(self, *, half_life_presentations: int, presentation_unit_id: str) -> bool:
        observed = presentation_ema_configuration_identity(
            half_life_presentations=half_life_presentations,
            presentation_unit_id=presentation_unit_id,
        )
        if observed != self.ema_configuration_identity:
            raise RuntimeError("presentation EMA configuration identity mismatch")
        self.base_authority._validate_digest()
        if self.binding_digest != _digest(self._core()):
            raise RuntimeError("presentation-EMA authority digest mismatch")
        return True


def issue_presentation_ema_bound_authority_from_checkpoint(
    modules: V5ReferenceModules,
    parent: V5PrefreezeBoundCheckpointV1,
    *,
    premise_state_path: Path,
    half_life_presentations: int,
    presentation_unit_id: str = PRESENTATION_UNIT_SUCCESSFUL_BASE_CELLS,
    scaler: object | None = None,
) -> PresentationEmaBoundPrefreezeAuthorityV1:
    """Bind an explicit rehearsal half-life/unit to an exact parent runtime state."""
    if not isinstance(parent, V5PrefreezeBoundCheckpointV1):
        raise RuntimeError("presentation EMA binding requires the canonical bound parent checkpoint")
    base = issue_prefreeze_authority_from_bound_checkpoint(
        modules,
        parent,
        premise_state_path=premise_state_path,
        scaler=scaler,
    )
    identity = presentation_ema_configuration_identity(
        half_life_presentations=half_life_presentations,
        presentation_unit_id=presentation_unit_id,
    )
    core = {
        "schema": EMA_BINDING_SCHEMA,
        "base_authority_digest": base.authority_digest,
        "parent_checkpoint_digest": base.checkpoint_digest,
        "parent_runtime_source_sha256": parent.runtime_source_sha256,
        "ema_configuration_identity": identity,
        "training_authorized": False,
        "execution_authorized": False,
        "production_promotable": False,
    }
    return PresentationEmaBoundPrefreezeAuthorityV1(
        base_authority=base,
        parent_runtime_source_sha256=parent.runtime_source_sha256,
        half_life_presentations=half_life_presentations,
        presentation_unit_id=presentation_unit_id,
        ema_configuration_identity=identity,
        binding_digest=_digest(core),
    )


def _completed_update_proof_core(
    *,
    authority: PresentationEmaBoundPrefreezeAuthorityV1,
    completed_guard_receipt: Mapping[str, object],
    presentations_this_update: int,
) -> dict[str, object]:
    if isinstance(presentations_this_update, bool) or not isinstance(presentations_this_update, int) or presentations_this_update < 1:
        raise RuntimeError("presentations_this_update must be a positive integer")
    receipt_digest = _require_sha256(
        completed_guard_receipt.get("receipt_digest"),
        "completed guard receipt digest",
    )
    checkpoint_digest = _require_sha256(
        completed_guard_receipt.get("checkpoint_digest"),
        "completed checkpoint digest",
    )
    return {
        "schema": PRESENTATION_EMA_COMPLETED_UPDATE_PROOF_SCHEMA,
        "ema_configuration_identity": authority.ema_configuration_identity,
        "ema_bound_authority_digest": authority.binding_digest,
        "parent_checkpoint_digest": authority.checkpoint_digest,
        "parent_runtime_source_sha256": authority.parent_runtime_source_sha256,
        "completed_guard_receipt_digest": receipt_digest,
        "completion_checkpoint_digest": checkpoint_digest,
        "presentations_this_update": presentations_this_update,
        "execution_authorized": False,
        "training_authorized": False,
        "production_promotable": False,
    }


def _issue_presentation_ema_completed_update_proof(
    *,
    authority: PresentationEmaBoundPrefreezeAuthorityV1,
    completed_guard_receipt: Mapping[str, object],
    presentations_this_update: int,
) -> dict[str, object]:
    core = _completed_update_proof_core(
        authority=authority,
        completed_guard_receipt=completed_guard_receipt,
        presentations_this_update=presentations_this_update,
    )
    return {**core, "proof_digest": _digest(core)}


def verify_presentation_ema_completed_update_proof(
    proof: object,
    *,
    authority: PresentationEmaBoundPrefreezeAuthorityV1,
    completed_guard_receipt: Mapping[str, object],
    half_life_presentations: int,
    presentation_unit_id: str,
) -> bool:
    """Reject any completed-update proof detached from its EMA configuration or guard receipt."""
    if not isinstance(proof, Mapping):
        raise RuntimeError("presentation EMA completed-update proof is required")
    authority.verify_ema_configuration(
        half_life_presentations=half_life_presentations,
        presentation_unit_id=presentation_unit_id,
    )
    presentations_this_update = proof.get("presentations_this_update")
    core = _completed_update_proof_core(
        authority=authority,
        completed_guard_receipt=completed_guard_receipt,
        presentations_this_update=presentations_this_update,  # type: ignore[arg-type]
    )
    for key, expected in core.items():
        if proof.get(key) != expected:
            raise RuntimeError(f"presentation EMA completed-update proof mismatch: {key}")
    observed_digest = proof.get("proof_digest")
    if observed_digest != _digest(core):
        raise RuntimeError("presentation EMA completed-update proof digest mismatch")
    return True


def run_presentation_ema_bound_guarded_reference_update(
    modules: V5ReferenceModules,
    *,
    authority: PresentationEmaBoundPrefreezeAuthorityV1,
    half_life_presentations: int,
    presentation_unit_id: str = PRESENTATION_UNIT_SUCCESSFUL_BASE_CELLS,
    scaler: Any | None = None,
    completion_checkpoint_digest: Any | None = None,
    **kwargs: Any,
) -> dict[str, object]:
    """Run one bounded update with momentum derived from successful base-cell presentations."""
    if not isinstance(authority, PresentationEmaBoundPrefreezeAuthorityV1):
        raise ValueError("PresentationEmaBoundPrefreezeAuthorityV1 is required")
    authority.verify_ema_configuration(
        half_life_presentations=half_life_presentations,
        presentation_unit_id=presentation_unit_id,
    )
    if presentation_unit_id != PRESENTATION_UNIT_SUCCESSFUL_BASE_CELLS:
        raise ValueError("canonical V5 rehearsal requires successful base-cell presentation units")
    if "ema_momentum" in kwargs:
        raise ValueError("caller may not supply scalar EMA momentum on the presentation-normalized route")
    expression = kwargs.get("expression")
    if expression is None or not hasattr(expression, "shape") or len(expression.shape) < 1:
        raise ValueError("expression batch is required to count base-cell presentations")
    presentations_this_update = int(expression.shape[0])
    momentum = ema_momentum_for_presentations(
        presentations_this_update=presentations_this_update,
        half_life_presentations=half_life_presentations,
    )
    report = run_guarded_inactive_reference_update(
        modules,
        authority=authority.base_authority,
        scaler=scaler,
        completion_checkpoint_digest=completion_checkpoint_digest,
        ema_momentum=momentum,
        **kwargs,
    )
    report = dict(report)
    completed_guard_receipt = report.get("completed_guard_receipt")
    if completed_guard_receipt is None:
        presentation_completion_proof = None
    elif isinstance(completed_guard_receipt, Mapping):
        presentation_completion_proof = _issue_presentation_ema_completed_update_proof(
            authority=authority,
            completed_guard_receipt=completed_guard_receipt,
            presentations_this_update=presentations_this_update,
        )
    else:
        raise RuntimeError("completed guard receipt has unexpected type")
    report["ema_configuration_identity"] = authority.ema_configuration_identity
    report["ema_bound_authority_digest"] = authority.binding_digest
    report["ema_presentation_unit_id"] = presentation_unit_id
    report["ema_half_life_presentations"] = half_life_presentations
    report["ema_presentations_this_update"] = presentations_this_update
    report["ema_momentum_used"] = momentum
    report["presentation_ema_completion_proof"] = presentation_completion_proof
    report["training_authorized"] = False
    report["execution_authorized"] = False
    return report
