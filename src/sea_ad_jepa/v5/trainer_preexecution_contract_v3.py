"""Trainer pre-execution V3: bind the exact closed V5 qualification bundle.

V2 bound only a generic anti-cheat authority digest. V3 retains every V2
mechanics constraint and additionally embeds and revalidates the exact
pretraining qualification bundle, closing that substitution path.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .pretraining_qualification_bundle_v1 import (
    validate_pretraining_qualification_bundle,
)
from .trainer_preexecution_contract_v2 import (
    TrainerPreexecutionAuthorityV2,
    canonical_json_sha256,
)


def _validate_bound_bundle(bundle: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(bundle, Mapping):
        raise ValueError("pretraining qualification bundle must be a mapping")
    if bundle.get("schema") != "JEPA_V5_PRETRAINING_QUALIFICATION_BUNDLE_V1":
        raise ValueError("unexpected pretraining qualification bundle schema")
    if bundle.get("qualification_bundle_closed") is not True:
        raise RuntimeError("STOP_V5_PRETRAINING_BUNDLE_NOT_CLOSED")
    if bundle.get("training_authorized") is not False:
        raise RuntimeError("STOP_V5_PRETRAINING_BUNDLE_CLAIMS_TRAINING_AUTHORITY")

    regenerated = validate_pretraining_qualification_bundle(
        bundle.get("required_evidence"),
        qualification_rules_frozen_before_candidate_model_outcome=bundle.get(
            "qualification_rules_frozen_before_candidate_model_outcome"
        ),
        optimizer_started=bundle.get("optimizer_started"),
    )
    if regenerated.get("bundle_sha256") != bundle.get("bundle_sha256"):
        raise RuntimeError("STOP_V5_PRETRAINING_BUNDLE_DIGEST_MISMATCH")
    if regenerated.get("required_evidence") != bundle.get("required_evidence"):
        raise RuntimeError("STOP_V5_PRETRAINING_BUNDLE_EVIDENCE_MISMATCH")
    return regenerated


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
    pretraining_qualification_bundle: Mapping[str, Any]
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
        _validate_bound_bundle(self.pretraining_qualification_bundle)

    def canonical_digest(self) -> str:
        self.validate()
        return canonical_json_sha256({
            "schema": "TRAINER_PREEXECUTION_AUTHORITY_V3",
            "v2_authority_sha256": self._v2().canonical_digest(),
            "pretraining_qualification_bundle_sha256":
                self.pretraining_qualification_bundle["bundle_sha256"],
            "training_authorized": False,
        })
