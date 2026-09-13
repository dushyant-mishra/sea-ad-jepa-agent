from __future__ import annotations

import pytest

from sea_ad_jepa.v5.preexecution_dependency_guard_v1 import PRE_EXECUTION_BASE_EVIDENCE_V2
from sea_ad_jepa.v5.preexecution_qualification_bundle_v2 import (
    DEPENDENCY_EVIDENCE_ID,
    build_preexecution_bundle_v2,
)
from sea_ad_jepa.v5.trainer_preexecution_contract_v2 import REQUIRED_AUTHORITY_SHAS
from sea_ad_jepa.v5.trainer_preexecution_contract_v4 import TrainerPreexecutionAuthorityV4


def _h(char: str) -> str:
    return char * 64


def _base_rows():
    rows = {}
    alphabet = "12345678"
    for i, name in enumerate(PRE_EXECUTION_BASE_EVIDENCE_V2):
        rows[name] = {
            "status": "EXECUTED_PASS",
            "artifact_sha256": _h(alphabet[i]),
            "authority_id": f"authority:{name}",
            "training_authorized": False,
        }
    return rows


def _closure(*, update_geometry_sha: str = _h("a"), protected_registry_sha: str = _h("b")):
    rows = _base_rows()
    return {
        "schema": "JEPA_V5_PREEXECUTION_DEPENDENCY_CLOSURE_V1",
        "authority_id": "dependency-authority-v1",
        "design_context_sha256": _h("c"),
        "evidence_artifact_sha256": {
            name: rows[name]["artifact_sha256"] for name in PRE_EXECUTION_BASE_EVIDENCE_V2
        },
        "evidence_authority_ids": {
            name: rows[name]["authority_id"] for name in PRE_EXECUTION_BASE_EVIDENCE_V2
        },
        "protected_registry_sha256": protected_registry_sha,
        "update_geometry_authority_sha256": update_geometry_sha,
        "production_gpu_geometry": {
            "effective_batch": 64,
            "microbatch": 8,
            "model_width": 192,
            "model_depth": 8,
            "source": "DATA_DERIVED_PRODUCTION_AUTHORITY",
        },
        "data_to_dimension_bound": True,
        "data_to_proposal_bound": True,
        "proposal_and_dimension_to_packing_bound": True,
        "all_preexecution_artifacts_to_production_gpu_bound": True,
        "passed": True,
        "training_authorized": False,
    }


def _bundle(closure, dep_artifact_sha: str):
    evidence = _base_rows()
    evidence[DEPENDENCY_EVIDENCE_ID] = {
        "status": "EXECUTED_PASS",
        "artifact_sha256": dep_artifact_sha,
        "authority_id": closure["authority_id"],
        "training_authorized": False,
    }
    return build_preexecution_bundle_v2(
        evidence,
        design_context_sha256=closure["design_context_sha256"],
        dependency_closure_report=closure,
        dependency_closure_artifact_sha256=dep_artifact_sha,
        optimizer_started=False,
    )


def _authorities(update_geometry_sha: str = _h("a")):
    out = {name: f"{i + 20:064x}" for i, name in enumerate(REQUIRED_AUTHORITY_SHAS)}
    out["update_geometry_authority_sha256"] = update_geometry_sha
    return out


def _v4(*, closure, authorities=None, protected_registry_sha: str = _h("b")):
    dep_sha = _h("d")
    return TrainerPreexecutionAuthorityV4(
        authorities=_authorities() if authorities is None else authorities,
        protected_registry_sha256=protected_registry_sha,
        presentation_horizon=1024,
        ema_half_life_presentations=256,
        singleton_queries_per_base_cell=3,
        effective_base_cells_per_update=64,
        relational_training_active=False,
        optimizer_started=False,
        preexecution_qualification_bundle_v2=_bundle(closure, dep_sha),
        preexecution_dependency_closure_report=closure,
        preexecution_dependency_closure_artifact_sha256=dep_sha,
        qualification_horizon_authority_id="qualification-horizon-v1",
        qualification_horizon_presentations=1024,
        training_authorized=False,
    )


def test_v4_accepts_same_gpu_and_trainer_geometry_authority():
    closure = _closure()
    _v4(closure=closure).validate()


def test_v4_rejects_individually_valid_but_different_geometry_authority():
    closure = _closure(update_geometry_sha=_h("e"))
    trainer_authorities = _authorities(update_geometry_sha=_h("a"))
    with pytest.raises(RuntimeError, match="UPDATE_GEOMETRY_AUTHORITY_MISMATCH"):
        _v4(closure=closure, authorities=trainer_authorities).validate()


def test_v4_rejects_dependency_registry_different_from_trainer_registry():
    closure = _closure(protected_registry_sha=_h("e"))
    with pytest.raises(RuntimeError, match="PROTECTED_REGISTRY_AUTHORITY_MISMATCH"):
        _v4(closure=closure, protected_registry_sha=_h("b")).validate()
