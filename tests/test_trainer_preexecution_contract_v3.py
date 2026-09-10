import copy
import pytest

from sea_ad_jepa.v5.pretraining_qualification_bundle_v1 import (
    REQUIRED_EVIDENCE,
    validate_pretraining_qualification_bundle,
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
        for i, name in enumerate(REQUIRED_EVIDENCE)
    }
    return validate_pretraining_qualification_bundle(
        evidence,
        qualification_rules_frozen_before_candidate_model_outcome=True,
        optimizer_started=False,
    )


def authority(b=None):
    return TrainerPreexecutionAuthorityV3(
        authorities={name: "a" * 64 for name in REQUIRED_AUTHORITY_SHAS},
        protected_registry_sha256="b" * 64,
        presentation_horizon=100,
        ema_half_life_presentations=50,
        singleton_queries_per_base_cell=1,
        effective_base_cells_per_update=8,
        relational_training_active=False,
        optimizer_started=False,
        pretraining_qualification_bundle=b or bundle(),
        training_authorized=False,
    )


def test_v3_binds_closed_exact_bundle_and_still_does_not_authorize_training():
    a = authority()
    a.validate()
    assert len(a.canonical_digest()) == 64
    assert a.training_authorized is False


def test_generic_anticheat_digest_cannot_replace_missing_gate():
    b = bundle()
    del b["required_evidence"]["shortcut_superiority"]
    with pytest.raises(RuntimeError, match="EVIDENCE_SET_MISMATCH"):
        authority(b).validate()


def test_tampered_evidence_with_stale_bundle_digest_stops():
    b = copy.deepcopy(bundle())
    b["required_evidence"]["heldout_biology_validation"]["artifact_sha256"] = "f" * 64
    with pytest.raises(RuntimeError, match="DIGEST_MISMATCH"):
        authority(b).validate()


def test_bundle_cannot_claim_training_authority():
    b = copy.deepcopy(bundle())
    b["training_authorized"] = True
    with pytest.raises(RuntimeError, match="CLAIMS_TRAINING_AUTHORITY"):
        authority(b).validate()


def test_bundle_must_be_marked_closed():
    b = copy.deepcopy(bundle())
    b["qualification_bundle_closed"] = False
    with pytest.raises(RuntimeError, match="NOT_CLOSED"):
        authority(b).validate()


def test_bundle_digest_is_part_of_v3_authority_identity():
    a = authority()
    b = bundle()
    b["required_evidence"]["shortcut_superiority"]["artifact_sha256"] = "e" * 64
    b = validate_pretraining_qualification_bundle(
        b["required_evidence"],
        qualification_rules_frozen_before_candidate_model_outcome=True,
        optimizer_started=False,
    )
    c = authority(b)
    assert a.canonical_digest() != c.canonical_digest()
