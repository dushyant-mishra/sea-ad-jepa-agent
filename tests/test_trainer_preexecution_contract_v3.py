import copy
import pytest

from sea_ad_jepa.v5.qualification_phase_contract_v1 import (
    PRE_EXECUTION_EVIDENCE,
    build_preexecution_bundle,
)
from sea_ad_jepa.v5.trainer_preexecution_contract_v2 import REQUIRED_AUTHORITY_SHAS
from sea_ad_jepa.v5.trainer_preexecution_contract_v3 import TrainerPreexecutionAuthorityV3


def bundle():
    evidence = {
        name: {
            "status": "EXECUTED_PASS",
            "artifact_sha256": format(i + 1, "064x"),
            "authority_id": f"{name}-authority-v1",
            "training_authorized": False,
        }
        for i, name in enumerate(PRE_EXECUTION_EVIDENCE)
    }
    return build_preexecution_bundle(
        evidence,
        design_context_sha256="c" * 64,
        optimizer_started=False,
    )


def authority(b=None, mode="BOUNDED_QUALIFICATION_ONLY", horizon=100, frozen_horizon=100):
    return TrainerPreexecutionAuthorityV3(
        authorities={name: "a" * 64 for name in REQUIRED_AUTHORITY_SHAS},
        protected_registry_sha256="b" * 64,
        presentation_horizon=horizon,
        ema_half_life_presentations=50,
        singleton_queries_per_base_cell=1,
        effective_base_cells_per_update=8,
        relational_training_active=False,
        optimizer_started=False,
        preexecution_qualification_bundle=b or bundle(),
        qualification_horizon_authority_id="qualification-horizon-v1",
        qualification_horizon_presentations=frozen_horizon,
        execution_mode=mode,
        training_authorized=False,
    )


def test_v3_binds_preexecution_bundle_for_qualification_only():
    a = authority()
    a.validate()
    assert len(a.canonical_digest()) == 64


def test_v3_rejects_production_mode_before_postqualification():
    with pytest.raises(RuntimeError, match="PRODUCTION_MODE_FORBIDDEN"):
        authority(mode="PRODUCTION").validate()


def test_qualification_horizon_must_equal_frozen_authority():
    with pytest.raises(RuntimeError, match="HORIZON_NOT_EXACTLY_FROZEN"):
        authority(horizon=101, frozen_horizon=100).validate()


def test_tampered_preexecution_bundle_stops():
    b = copy.deepcopy(bundle())
    b["required_evidence"]["representation_firewall"]["artifact_sha256"] = "f" * 64
    with pytest.raises(RuntimeError, match="DIGEST_MISMATCH"):
        authority(b).validate()


def test_missing_preexecution_gate_stops():
    b = copy.deepcopy(bundle())
    del b["required_evidence"]["qc_policy_freeze"]
    with pytest.raises(RuntimeError, match="EVIDENCE_SET_MISMATCH"):
        authority(b).validate()


def test_preexecution_bundle_cannot_claim_production_authority():
    b = copy.deepcopy(bundle())
    b["production_training_authorized"] = True
    with pytest.raises(RuntimeError, match="CLAIMS_PRODUCTION_AUTHORITY"):
        authority(b).validate()
