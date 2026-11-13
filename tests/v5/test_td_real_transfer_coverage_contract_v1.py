from __future__ import annotations

import pytest

import scripts.v5.td_real_transfer_coverage_contract_v1 as T


FOUNDATION = {
    "C1_SHARED_EMERGENT",
    "C2_RELATIONAL_SHARED",
    "C3_QUERY_MEASURED",
    "C6_SHARED_QUERY_COMPOSITE",
    "C4_STRUCTURED_COMPOSITE",
}


def _registry():
    candidates = sorted(FOUNDATION | {"C5_REGULATORY_SPECIALIST"})
    rows = [
        {
            "stratum_id": "HVS_OP1_RNA",
            "donor_id": "D01",
            "source": "HVS",
            "operator_matrix": "OP1",
            "study_family": "F_HVS",
            "technology": "RNA",
            "candidate_support": {c: True for c in candidates},
        },
        {
            "stratum_id": "SEA_OP2_RNA",
            "donor_id": "D02",
            "source": "SEA_AD",
            "operator_matrix": "OP2",
            "study_family": "F_SEA",
            "technology": "RNA",
            "candidate_support": {**{c: True for c in candidates}, "C5_REGULATORY_SPECIALIST": False},
        },
        {
            "stratum_id": "SEA_OP3_MULTIOME",
            "donor_id": "D03",
            "source": "SEA_AD",
            "operator_matrix": "OP3",
            "study_family": "F_SEA",
            "technology": "MULTIOME",
            "candidate_support": {**{c: True for c in candidates}, "C5_REGULATORY_SPECIALIST": True},
        },
    ]
    claims = {
        c: ["DONOR", "SOURCE", "OPERATOR_MATRIX", "STUDY_FAMILY", "TECHNOLOGY"]
        for c in FOUNDATION
    }
    claims["C5_REGULATORY_SPECIALIST"] = ["DONOR", "SOURCE", "OPERATOR_MATRIX", "TECHNOLOGY"]
    return {
        "schema": "JEPA_TD_REAL_STATIC_POPULATION_SUPPORT_REGISTRY_V1",
        "frozen": True,
        "candidate_transfer_claims": claims,
        "strata": rows,
    }


def test_unfrozen_registry_is_rejected():
    registry = _registry()
    registry["frozen"] = False
    with pytest.raises(T.StaticContractError, match="frozen"):
        T.derive_static_contract(registry)


def test_foundation_claim_envelope_is_all_physically_supported_strata():
    out = T.derive_static_contract(_registry())
    expected = {"HVS_OP1_RNA", "SEA_OP2_RNA", "SEA_OP3_MULTIOME"}
    for candidate in FOUNDATION:
        assert set(out["mandatory_claim_envelopes"][candidate]) == expected
        assert out["claim_envelope_status"][candidate] == "SUPPORTED_ENVELOPE_FROZEN"


def test_specialist_claim_envelope_is_support_limited_and_cannot_rescue_foundation():
    out = T.derive_static_contract(_registry())
    assert set(out["mandatory_claim_envelopes"]["C5_REGULATORY_SPECIALIST"]) == {
        "HVS_OP1_RNA",
        "SEA_OP3_MULTIOME",
    }
    assert out["claim_envelope_status"]["C5_REGULATORY_SPECIALIST"] == "SUPPORTED_ENVELOPE_FROZEN"
    assert out["specialist_foundation_rescue_authorized"] is False


def test_required_transfer_dimensions_are_static_and_noncompensating():
    out = T.derive_static_contract(_registry())
    c1 = out["transfer_applicability"]["C1_SHARED_EMERGENT"]
    assert c1 == {
        "DONOR": "REQUIRED",
        "SOURCE": "REQUIRED",
        "OPERATOR_MATRIX": "REQUIRED",
        "STUDY_FAMILY": "REQUIRED",
        "TECHNOLOGY": "REQUIRED",
    }


def test_claimed_dimension_with_insufficient_levels_is_blocked_dependency():
    registry = _registry()
    for row in registry["strata"]:
        row["technology"] = "RNA"
    out = T.derive_static_contract(registry)
    assert out["transfer_applicability"]["C1_SHARED_EMERGENT"]["TECHNOLOGY"] == "BLOCKED_DEPENDENCY"


def test_unclaimed_dimension_is_structurally_not_applicable():
    out = T.derive_static_contract(_registry())
    assert out["transfer_applicability"]["C5_REGULATORY_SPECIALIST"]["STUDY_FAMILY"] == "NOT_APPLICABLE_STRUCTURAL"


def test_transfer_claim_dimension_must_be_literal_known_string():
    registry = _registry()
    registry["candidate_transfer_claims"]["C1_SHARED_EMERGENT"] = ["DONOR", 1]
    with pytest.raises(T.StaticContractError, match="nonempty strings"):
        T.derive_static_contract(registry)


def test_foundation_with_zero_supported_strata_is_explicitly_unresolved():
    registry = _registry()
    for row in registry["strata"]:
        row["candidate_support"]["C1_SHARED_EMERGENT"] = False
    out = T.derive_static_contract(registry)
    assert out["mandatory_claim_envelopes"]["C1_SHARED_EMERGENT"] == []
    assert out["claim_envelope_status"]["C1_SHARED_EMERGENT"] == "NO_SUPPORTED_STRATA__NOT_ESTIMABLE"
    assert set(out["transfer_applicability"]["C1_SHARED_EMERGENT"].values()) == {"BLOCKED_DEPENDENCY"}


def test_outcome_fields_are_forbidden_from_static_registry():
    registry = _registry()
    registry["strata"][0]["candidate_score"] = 0.99
    with pytest.raises(T.StaticContractError, match="unexpected stratum fields"):
        T.derive_static_contract(registry)


def test_authority_remains_exactly_false():
    out = T.derive_static_contract(_registry())
    assert out["authority"] == {
        "value_read_authorized": False,
        "real_tournament_authorized": False,
        "target_selection_authorized": False,
        "representation_selection_authorized": False,
        "td60_authorized": False,
        "stage4_authorized": False,
        "training_authorized": False,
    }
