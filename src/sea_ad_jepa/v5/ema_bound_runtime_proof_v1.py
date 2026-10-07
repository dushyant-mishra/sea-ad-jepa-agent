"""Non-authorizing EMA-configuration binding for the canonical V5 rehearsal.

The current V5 EMA mechanics are presentation-normalized. No production
half-life is selected here. A legacy constant-momentum identity remains only as
a compatibility/test adapter while the successor proof is migrated to the
presentation-unit + half-life contract.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from .inactive_checkpoint_binding_v1 import (
    V5PrefreezeBoundCheckpointV1,
    issue_prefreeze_authority_from_bound_checkpoint,
)
from .inactive_guarded_update_v1 import run_guarded_inactive_reference_update
from .inactive_update_reference import V5ReferenceModules
from .prefreeze_runtime_authority import PrefreezeMechanicalAuthorityV1

EMA_BINDING_SCHEMA = "V5_PREFREEZE_EMA_BOUND_AUTHORITY_V1"
EMA_CONFIGURATION_SCHEMA = "V5_CONSTANT_EMA_CONFIGURATION_V1"
PRESENTATION_EMA_CONFIGURATION_SCHEMA = "V5_PRESENTATION_EMA_CONFIGURATION_V1"


def _digest(value: object) -> str:
    raw = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def constant_ema_configuration_identity(momentum: float) -> str:
    """Legacy constant-momentum identity for compatibility tests only."""
    if isinstance(momentum, bool):
        raise ValueError("EMA momentum must be a finite float in [0,1)")
    try:
        value = float(momentum)
    except (TypeError, ValueError) as exc:
        raise ValueError("EMA momentum must be a finite float in [0,1)") from exc
    if not math.isfinite(value) or value < 0.0 or value >= 1.0:
        raise ValueError("EMA momentum must be a finite float in [0,1)")
    core = {"schema": EMA_CONFIGURATION_SCHEMA, "constant_momentum": value}
    return f"V5_CONSTANT_EMA:{_digest(core)}"


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
class EmaBoundPrefreezeAuthorityV1:
    """Exact parent mechanical authority plus an explicit EMA configuration identity."""

    base_authority: PrefreezeMechanicalAuthorityV1
    parent_runtime_source_sha256: str
    ema_configuration_identity: str
    binding_digest: str
    training_authorized: bool = False
    execution_authorized: bool = False
    production_promotable: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.base_authority, PrefreezeMechanicalAuthorityV1):
            raise RuntimeError("EMA-bound authority requires PrefreezeMechanicalAuthorityV1")
        self.base_authority._validate_digest()
        if not isinstance(self.parent_runtime_source_sha256, str) or len(self.parent_runtime_source_sha256) != 64:
            raise RuntimeError("EMA-bound authority requires parent runtime SHA-256")
        try:
            int(self.parent_runtime_source_sha256, 16)
        except ValueError as exc:
            raise RuntimeError("EMA-bound authority requires parent runtime SHA-256") from exc
        if not isinstance(self.ema_configuration_identity, str) or not self.ema_configuration_identity.startswith("V5_CONSTANT_EMA:"):
            raise RuntimeError("EMA configuration identity is invalid")
        if self.training_authorized or self.execution_authorized or self.production_promotable:
            raise RuntimeError("EMA-bound rehearsal authority cannot authorize execution or training")
        if self.binding_digest != _digest(self._core()):
            raise RuntimeError("EMA-bound authority digest mismatch")

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

    def verify_ema_momentum(self, momentum: float) -> bool:
        observed = constant_ema_configuration_identity(momentum)
        if observed != self.ema_configuration_identity:
            raise RuntimeError("EMA configuration identity mismatch")
        self.base_authority._validate_digest()
        if self.binding_digest != _digest(self._core()):
            raise RuntimeError("EMA-bound authority digest mismatch")
        return True


def issue_ema_bound_authority_from_checkpoint(
    modules: V5ReferenceModules,
    parent: V5PrefreezeBoundCheckpointV1,
    *,
    premise_state_path: Path,
    ema_momentum: float,
    scaler: object | None = None,
) -> EmaBoundPrefreezeAuthorityV1:
    if not isinstance(parent, V5PrefreezeBoundCheckpointV1):
        raise RuntimeError("EMA binding requires the canonical bound parent checkpoint")
    base = issue_prefreeze_authority_from_bound_checkpoint(
        modules,
        parent,
        premise_state_path=premise_state_path,
        scaler=scaler,
    )
    identity = constant_ema_configuration_identity(ema_momentum)
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
    return EmaBoundPrefreezeAuthorityV1(
        base_authority=base,
        parent_runtime_source_sha256=parent.runtime_source_sha256,
        ema_configuration_identity=identity,
        binding_digest=_digest(core),
    )


def run_ema_bound_guarded_reference_update(
    modules: V5ReferenceModules,
    *,
    authority: EmaBoundPrefreezeAuthorityV1,
    ema_momentum: float,
    scaler: Any | None = None,
    completion_checkpoint_digest: Any | None = None,
    **kwargs: Any,
) -> dict[str, object]:
    """Legacy constant-momentum wrapper retained only until successor migration is complete."""
    if not isinstance(authority, EmaBoundPrefreezeAuthorityV1):
        raise ValueError("EmaBoundPrefreezeAuthorityV1 is required")
    authority.verify_ema_momentum(ema_momentum)
    report = run_guarded_inactive_reference_update(
        modules,
        authority=authority.base_authority,
        scaler=scaler,
        completion_checkpoint_digest=completion_checkpoint_digest,
        ema_momentum=ema_momentum,
        **kwargs,
    )
    report = dict(report)
    report["ema_configuration_identity"] = authority.ema_configuration_identity
    report["ema_bound_authority_digest"] = authority.binding_digest
    report["training_authorized"] = False
    report["execution_authorized"] = False
    return report
