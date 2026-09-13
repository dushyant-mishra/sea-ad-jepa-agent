"""Active V5 trainer pre-execution authority for bounded qualification runs.

V4 supersedes the generic pre-execution bundle consumed by V3. It requires the
dependency-closed V2 bundle, including true production-geometry GPU evidence.
It remains qualification-run-only and cannot authorize production training.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .preexecution_qualification_bundle_v2 import validate_preexecution_bundle_v2
from .trainer_preexecution_contract_v2 import TrainerPreexecutionAuthorityV2, canonical_json_sha256

QUALIFICATION_EXECUTION_MODE = "BOUNDED_QUALIFICATION_ONLY"


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


def _positive_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{name} must be a positive integer")
    return value


@dataclass(frozen=True)
class TrainerPreexecutionAuthorityV4:
    authorities: Mapping[str, str]
    protected_registry_sha256: str
    presentation_horizon: int
    ema_half_life_presentations: int
    singleton_queries_per_base_cell: int
    effective_base_cells_per_update: int
    relational_training_active: bool
    optimizer_started: bool
    preexecution_qualification_bundle_v2: Mapping[str, Any]
    preexecution_dependency_closure_report: Mapping[str, Any]
    preexecution_dependency_closure_artifact_sha256: str
    qualification_horizon_authority_id: str
    qualification_horizon_presentations: int
    execution_mode: str = QUALIFICATION_EXECUTION_MODE
    training_authorized: bool = False

    def _mechanics(self) -> TrainerPreexecutionAuthorityV2:
        return TrainerPreexecutionAuthorityV2(
            authorities=self.authorities,
            protected_registry_sha256=self.protected_registry_sha256,
            presentation_horizon=self.presentation_horizon,
            ema_half_life_presentations=self.ema_half_life_presentations,
            singleton_queries_per_base_cell=self.singleton_queries_per_base_cell,
            effective_base_cells_per_update=self.effective_base_cells_per_update,
            relational_training_active=self.relational_training_active,
            optimizer_started=self.optimizer_started,
            training_authorized=self.training_authorized,
        )

    def validate(self) -> None:
        self._mechanics().validate()
        if self.execution_mode != QUALIFICATION_EXECUTION_MODE:
            raise RuntimeError("STOP_V5_PREEXECUTION_V4_PRODUCTION_MODE_FORBIDDEN")
        _id(self.qualification_horizon_authority_id, "qualification_horizon_authority_id")
        qh = _positive_int(self.qualification_horizon_presentations, "qualification_horizon_presentations")
        if self.presentation_horizon != qh:
            raise RuntimeError("STOP_V5_PREEXECUTION_V4_QUALIFICATION_HORIZON_NOT_EXACTLY_FROZEN")
        artifact = _sha(
            self.preexecution_dependency_closure_artifact_sha256,
            "preexecution_dependency_closure_artifact_sha256",
        )
        pre = validate_preexecution_bundle_v2(
            self.preexecution_qualification_bundle_v2,
            dependency_closure_report=self.preexecution_dependency_closure_report,
            dependency_closure_artifact_sha256=artifact,
        )
        if pre.get("qualification_run_eligible") is not True:
            raise RuntimeError("STOP_V5_PREEXECUTION_V4_QUALIFICATION_RUN_NOT_ELIGIBLE")
        if pre.get("production_geometry_gpu_required") is not True:
            raise RuntimeError("STOP_V5_PREEXECUTION_V4_PRODUCTION_GPU_NOT_REQUIRED")
        if pre.get("historical_gpu_regression_is_supporting_only") is not True:
            raise RuntimeError("STOP_V5_PREEXECUTION_V4_HISTORICAL_GPU_ROLE_INVALID")
        if pre.get("production_training_authorized") is not False:
            raise RuntimeError("STOP_V5_PREEXECUTION_V4_CLAIMS_PRODUCTION_AUTHORITY")

        # End-to-end anti-splice checks.  The dependency closure may be valid on
        # its own and the trainer mechanics authority may be valid on its own,
        # but a bounded run is lawful only when both name the exact same
        # production geometry and protected-parameter registry authorities.
        closure = self.preexecution_dependency_closure_report
        if not isinstance(closure, Mapping):
            raise ValueError("preexecution_dependency_closure_report must be a mapping")
        trainer_geometry = _sha(
            self.authorities.get("update_geometry_authority_sha256"),
            "authorities[update_geometry_authority_sha256]",
        )
        closure_geometry = _sha(
            closure.get("update_geometry_authority_sha256"),
            "preexecution_dependency_closure_report.update_geometry_authority_sha256",
        )
        if trainer_geometry != closure_geometry:
            raise RuntimeError("STOP_V5_PREEXECUTION_V4_UPDATE_GEOMETRY_AUTHORITY_MISMATCH")

        trainer_registry = _sha(self.protected_registry_sha256, "protected_registry_sha256")
        closure_registry = _sha(
            closure.get("protected_registry_sha256"),
            "preexecution_dependency_closure_report.protected_registry_sha256",
        )
        if trainer_registry != closure_registry:
            raise RuntimeError("STOP_V5_PREEXECUTION_V4_PROTECTED_REGISTRY_AUTHORITY_MISMATCH")

    def canonical_digest(self) -> str:
        self.validate()
        pre = validate_preexecution_bundle_v2(
            self.preexecution_qualification_bundle_v2,
            dependency_closure_report=self.preexecution_dependency_closure_report,
            dependency_closure_artifact_sha256=self.preexecution_dependency_closure_artifact_sha256,
        )
        return canonical_json_sha256({
            "schema": "TRAINER_PREEXECUTION_AUTHORITY_V4",
            "execution_mode": QUALIFICATION_EXECUTION_MODE,
            "qualification_horizon_authority_id": self.qualification_horizon_authority_id,
            "qualification_horizon_presentations": self.qualification_horizon_presentations,
            "v2_mechanics_authority_sha256": self._mechanics().canonical_digest(),
            "preexecution_qualification_bundle_v2_sha256": pre["bundle_sha256"],
            "preexecution_dependency_closure_artifact_sha256": _sha(
                self.preexecution_dependency_closure_artifact_sha256,
                "preexecution_dependency_closure_artifact_sha256",
            ),
            "production_training_authorized": False,
        })
