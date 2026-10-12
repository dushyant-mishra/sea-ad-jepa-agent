from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v5"))

import td_real_tournament_contract_v1 as RTC  # noqa: E402


def test_real_contract_candidate_registry_and_dependencies_are_exact():
    contract = RTC.load_real_tournament_contract()
    validated = RTC.validate_candidate_registry(contract)
    assert list(validated) == [
        "C1_SHARED_EMERGENT",
        "C2_RELATIONAL_SHARED",
        "C3_QUERY_MEASURED",
        "C6_SHARED_QUERY_COMPOSITE",
        "C4_STRUCTURED_COMPOSITE",
        "C5_REGULATORY_SPECIALIST",
    ]
    assert validated["C1_SHARED_EMERGENT"]["parents"] == []
    assert validated["C2_RELATIONAL_SHARED"]["parents"] == ["C1_SHARED_EMERGENT"]
    assert validated["C3_QUERY_MEASURED"]["parents"] == []
    assert validated["C6_SHARED_QUERY_COMPOSITE"]["parents"] == ["C1_SHARED_EMERGENT", "C3_QUERY_MEASURED"]
    assert validated["C4_STRUCTURED_COMPOSITE"]["parents"] == ["C2_RELATIONAL_SHARED", "C3_QUERY_MEASURED"]
    assert validated["C5_REGULATORY_SPECIALIST"]["foundation_rescue"] is False


def test_real_contract_gate_sets_and_falsifiers_are_complete():
    contract = RTC.load_real_tournament_contract()
    registry = RTC.validate_candidate_registry(contract)
    mandatory = set(RTC.MANDATORY_FALSIFIERS)
    for candidate_id, record in registry.items():
        assert record["required_gates"]
        assert set(record["mandatory_falsifiers"]) <= mandatory
        if candidate_id == "C3_QUERY_MEASURED":
            assert {
                "q_count_only",
                "q_address_only",
                "query_agnostic",
                "wrong_q",
                "technical_plus_q",
                "q_excluded_teacher",
            } <= set(record["mandatory_falsifiers"])
        if candidate_id in {"C2_RELATIONAL_SHARED", "C4_STRUCTURED_COMPOSITE"}:
            assert "fine_neighborhood_wrong_cell" in record["mandatory_falsifiers"]


def test_real_contract_preserves_donor_primary_operator_and_support_law():
    contract = RTC.load_real_tournament_contract()
    assert contract["replication_unit"] == "donor"
    assert contract["source_semantics"] == "observation_operator_not_biological_replicate"
    assert contract["support_semantics"] == {
        "measured_zero": "VALID_MEASUREMENT",
        "structurally_unsupported": "ABSTAIN",
        "imputation": "FORBIDDEN",
    }
    assert contract["synthetic_evidence_consumed"] is False


def test_real_contract_carries_no_downstream_authority():
    contract = RTC.load_real_tournament_contract()
    assert set(contract["authority"]) == set(RTC.AUTHORITY_KEYS)
    assert all(value is False for value in contract["authority"].values())


def test_real_contract_refuses_candidate_or_authority_drift():
    contract = RTC.load_real_tournament_contract()
    drift = copy.deepcopy(contract)
    drift["candidates"].pop("C3_QUERY_MEASURED")
    with pytest.raises(RTC.RealTournamentContractError):
        RTC.validate_candidate_registry(drift)

    drift = copy.deepcopy(contract)
    drift["authority"]["training_authorized"] = True
    with pytest.raises(RTC.RealTournamentContractError):
        RTC.validate_candidate_registry(drift)
