from __future__ import annotations

import hashlib
import json

import pytest

import scripts.v5.td_real_g12_claim_envelope_guard_v1 as G


def _sha(payload: dict) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _contract(*, status="SUPPORTED_ENVELOPE_FROZEN", envelope=("S1", "S2", "S3")):
    return {
        "schema": "JEPA_TD_REAL_TRANSFER_COVERAGE_STATIC_CONTRACT_V2",
        "status": "STATIC_CONTRACT_DERIVED__SPLIT_BOUND__NO_BIOLOGICAL_OUTCOME_AUTHORITY",
        "mandatory_claim_envelopes": {"C1_SHARED_EMERGENT": list(envelope)},
        "claim_envelope_status": {"C1_SHARED_EMERGENT": status},
        "claim_scope_rule": "FOUNDATION_ENVELOPE_EQUALS_ALL_PHYSICALLY_SUPPORTED_FROZEN_STRATA__SPECIALIST_ENVELOPE_SUPPORT_LIMITED__NO_POSTHOC_SCOPE_SHRINKAGE",
        "authority": {
            "value_read_authorized": False,
            "real_tournament_authorized": False,
            "target_selection_authorized": False,
            "representation_selection_authorized": False,
            "td60_authorized": False,
            "stage4_authorized": False,
            "training_authorized": False,
        },
    }


def test_exact_frozen_envelope_is_ready_for_later_execution_only():
    contract = _contract()
    out = G.guard_claim_envelope(
        static_contract=contract,
        expected_contract_sha256=_sha(contract),
        candidate_id="C1_SHARED_EMERGENT",
        proposed_strata=["S3", "S1", "S2"],
    )
    assert out["status"] == "FROZEN_CLAIM_ENVELOPE_READY_FOR_LATER_G12_EXECUTION"
    assert out["mandatory_claim_envelope"] == ["S1", "S2", "S3"]
    assert out["g12_biological_adjudication_authorized"] is False


def test_missing_supported_stratum_is_posthoc_scope_shrinkage_and_fails_closed():
    contract = _contract()
    with pytest.raises(G.G12EnvelopeError, match="scope shrinkage"):
        G.guard_claim_envelope(
            static_contract=contract,
            expected_contract_sha256=_sha(contract),
            candidate_id="C1_SHARED_EMERGENT",
            proposed_strata=["S1", "S2"],
        )


def test_extra_stratum_not_in_frozen_support_universe_is_rejected():
    contract = _contract()
    with pytest.raises(G.G12EnvelopeError, match="outside frozen envelope"):
        G.guard_claim_envelope(
            static_contract=contract,
            expected_contract_sha256=_sha(contract),
            candidate_id="C1_SHARED_EMERGENT",
            proposed_strata=["S1", "S2", "S3", "S4"],
        )


def test_duplicate_proposed_stratum_is_rejected():
    contract = _contract()
    with pytest.raises(G.G12EnvelopeError, match="duplicate"):
        G.guard_claim_envelope(
            static_contract=contract,
            expected_contract_sha256=_sha(contract),
            candidate_id="C1_SHARED_EMERGENT",
            proposed_strata=["S1", "S2", "S2", "S3"],
        )


def test_incomplete_evidence_support_blocks_before_any_g12_outcome_execution():
    contract = _contract(status="SUPPORT_REGISTRY_INCOMPLETE__NOT_ESTIMABLE", envelope=())
    out = G.guard_claim_envelope(
        static_contract=contract,
        expected_contract_sha256=_sha(contract),
        candidate_id="C1_SHARED_EMERGENT",
        proposed_strata=[],
    )
    assert out["status"] == "BLOCKED_G12_SUPPORT_REGISTRY_INCOMPLETE"
    assert out["g12_biological_adjudication_authorized"] is False


def test_no_supported_strata_is_not_estimable_not_biological_fail():
    contract = _contract(status="NO_SUPPORTED_STRATA__NOT_ESTIMABLE", envelope=())
    out = G.guard_claim_envelope(
        static_contract=contract,
        expected_contract_sha256=_sha(contract),
        candidate_id="C1_SHARED_EMERGENT",
        proposed_strata=[],
    )
    assert out["status"] == "NOT_ESTIMABLE_G12_NO_SUPPORTED_STRATA"
    assert out["biological_fail"] is False


def test_wrong_static_contract_identity_is_rejected():
    contract = _contract()
    with pytest.raises(G.G12EnvelopeError, match="contract binding"):
        G.guard_claim_envelope(
            static_contract=contract,
            expected_contract_sha256="d" * 64,
            candidate_id="C1_SHARED_EMERGENT",
            proposed_strata=["S1", "S2", "S3"],
        )


def test_claim_scope_rule_must_be_exact_no_shrinkage_law():
    contract = _contract()
    contract["claim_scope_rule"] = "ALLOW_POSTHOC_SUBSET"
    with pytest.raises(G.G12EnvelopeError, match="claim scope rule"):
        G.guard_claim_envelope(
            static_contract=contract,
            expected_contract_sha256=_sha(contract),
            candidate_id="C1_SHARED_EMERGENT",
            proposed_strata=["S1", "S2", "S3"],
        )


def test_all_authority_remains_false():
    contract = _contract()
    out = G.guard_claim_envelope(
        static_contract=contract,
        expected_contract_sha256=_sha(contract),
        candidate_id="C1_SHARED_EMERGENT",
        proposed_strata=["S1", "S2", "S3"],
    )
    assert all(value is False for value in out["authority"].values())
