"""Trainer pre-execution V3: qualification-run authority only.

V3 binds the exact pre-execution qualification bundle. It cannot authorize a
production training run; it only proves that a bounded qualification run is
eligible to be launched under separately explicit owner/run authority.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .qualification_phase_contract_v1 import validate_preexecution_bundle
from .trainer_preexecution_contract_v2 import (
    TrainerPreexecutionAuthorityV2,
    canonical_json_sha256,
)

QUALIFICATION_EXECUTION_MODE = "BOUNDED_QUALIFICATION_ONLY"


@dataclass(frozen=True)
class TrainerPreexecutionAuthorityV3:
    authorities: Mapping[str, str]
    protected_registry_sha256: str
    presentation_horizon: int
    ema_half_life_presentations: int
    singleton_queries_per_base_cell: int
    effective_base_cells_per_update: int
    relational_training_active: bool
    optimizer_started: bool
    preexecution_qualification_bundle: Mapping[str, Any]
    execution_mode: str = QUALIFICATION_EXECUTION_MODE
    training_authorized: bool = False

    def _v2(self) -> TrainerPreexecutionAuthorityV2:
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
        self._v2().validate()
        if self.execution_mode != QUALIFICATION_EXECUTION_MODE:
            raise RuntimeError("STOP_V5_PREEXECUTION_PRODUCTION_MODE_FORBIDDEN")
        pre = validate_preexecution_bundle(self.preexecution_qualification_bundle)
        if pre.get("qualification_run_eligible") is not True:
            raise RuntimeError("STOP_V5_QUALIFICATION_RUN_NOT_ELIGIBLE")
        if pre.get("production_training_authorized") is not False:
            raise RuntimeError("STOP_V5_PREEXECUTION_CLAIMS_PRODUCTION_AUTHORITY")

    def canonical_digest(self) -> str:
        self.validate()
        pre = validate_preexecution_bundle(self.preexecution_qualification_bundle)
        return canonical_json_sha256({
            "schema": "TRAINER_PREEXECUTION_AUTHORITY_V3",
            "execution_mode": QUALIFICATION_EXECUTION_MODE,
            "v2_mechanics_authority_sha256": self._v2().canonical_digest(),
            "preexecution_qualification_bundle_sha256": pre["bundle_sha256"],
            "production_training_authorized": False,
        })
