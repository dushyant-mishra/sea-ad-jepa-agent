from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v5"))

import td_v79_synthetic_crosswalk_v1 as X  # noqa: E402

REGISTRY = ROOT / "results" / "target_discovery" / "synthetic_crosswalk" / "TD_V79_SYNTHETIC_CROSSWALK_V1.json"


def crosswalk():
    return X.load_crosswalk(REGISTRY)


def test_exact_world_candidate_and_class_registries_and_authority_off():
    cw = crosswalk()
    X.validate_crosswalk(cw)
    assert tuple(cw["worlds"]) == X.EXACT_WORLDS
    assert tuple(cw["candidates"]) == X.EXACT_CANDIDATES
    assert tuple(cw["evidence_classes"]) == X.EVIDENCE_CLASSES
    assert all(value is False for value in cw["authority"].values())


def test_decisive_entries_require_truth_bindings_and_known_worlds():
    cw = crosswalk()
    bad = copy.deepcopy(cw)
    entry = next(e for e in bad["claims"] if e["evidence_class"].startswith("DECISIVE"))
    entry["required_truth_fields"] = []
    with pytest.raises(X.CrosswalkError):
        X.validate_crosswalk(bad)

    bad = copy.deepcopy(cw)
    bad["claims"][0]["worlds"] = ["Q99_UNKNOWN"]
    with pytest.raises(X.CrosswalkError):
        X.validate_crosswalk(bad)


def test_missing_or_extra_world_or_candidate_is_rejected():
    cw = crosswalk()
    bad = copy.deepcopy(cw)
    bad["worlds"].pop("Q11_OMITTED_OPERATOR")
    with pytest.raises(X.CrosswalkError):
        X.validate_crosswalk(bad)

    bad = copy.deepcopy(cw)
    bad["candidates"]["C6_FAKE"] = {"foundation": True}
    with pytest.raises(X.CrosswalkError):
        X.validate_crosswalk(bad)


def test_mandatory_not_estimable_claims_are_frozen():
    cw = crosswalk()
    required = {
        ("C1_SHARED_EMERGENT", "SHARED_MULTIGENE_LATENT_RECOVERY"),
        ("C2_RELATIONAL_SHARED", "RELATIONAL_GEOMETRY_RECOVERY"),
        ("C3_QUERY_MEASURED", "QUERY_CONDITIONED_BIOLOGICAL_RECOVERY"),
        ("C4_STRUCTURED_COMPOSITE", "INCREMENT_OVER_CONSTITUENTS_BIOLOGICAL_TRUTH"),
        ("C5_REGULATORY_SPECIALIST", "REGULATORY_CHROMATIN_RECOVERY"),
    }
    seen = {(e["candidate"], e["claim"]): e["evidence_class"] for e in cw["claims"]}
    assert required <= set(seen)
    assert all(seen[key] == "NOT_ESTIMABLE" for key in required)


def test_q10_q11_operator_claim_requires_canonical_pair():
    cw = crosswalk()
    pair = cw["paired_counterfactual"]
    assert pair["worlds"] == ["Q10_S174_DESIGN_IMBALANCE", "Q11_OMITTED_OPERATOR"]
    assert pair["non_operator_truth_identical_required"] is True
    assert pair["single_world_operator_invariance_allowed"] is False

    bad = copy.deepcopy(cw)
    bad["paired_counterfactual"]["worlds"] = ["Q11_OMITTED_OPERATOR"]
    with pytest.raises(X.CrosswalkError):
        X.validate_crosswalk(bad)


def _syn(evidence_class, status):
    return [{"evidence_class": evidence_class, "status": status}]


def test_real_fail_and_not_estimable_cannot_be_rescued_by_synthetic_pass():
    cw = crosswalk()
    assert X.combine_candidate_evidence("C1_SHARED_EMERGENT", "FAIL", _syn("DECISIVE_POSITIVE", "PASS"), cw) == "ELIMINATED_REAL_FAIL"
    assert X.combine_candidate_evidence("C1_SHARED_EMERGENT", "NOT_ESTIMABLE", _syn("DECISIVE_POSITIVE", "PASS"), cw) == "UNRESOLVED_REAL_NOT_ESTIMABLE"


def test_real_pass_with_decisive_synthetic_fail_is_eliminated_but_diagnostic_fail_is_not():
    cw = crosswalk()
    assert X.combine_candidate_evidence("C1_SHARED_EMERGENT", "PASS", _syn("DECISIVE_NEGATIVE", "FAIL"), cw) == "ELIMINATED_SYNTHETIC_FALSIFIER"
    assert X.combine_candidate_evidence("C1_SHARED_EMERGENT", "PASS", _syn("DIAGNOSTIC", "FAIL"), cw) == "ELIGIBLE_PENDING_TARGET_SELECTION"
    assert X.combine_candidate_evidence("C1_SHARED_EMERGENT", "PASS", _syn("NOT_ESTIMABLE", "PASS"), cw) == "ELIGIBLE_PENDING_TARGET_SELECTION"


def test_foundation_contingency_zero_one_multiple_and_c5_separation():
    zero = {
        "C1_SHARED_EMERGENT": "ELIMINATED_REAL_FAIL",
        "C2_RELATIONAL_SHARED": "ELIMINATED_REAL_FAIL",
        "C3_QUERY_MEASURED": "ELIMINATED_SYNTHETIC_FALSIFIER",
        "C4_STRUCTURED_COMPOSITE": "ELIMINATED_REAL_FAIL",
    }
    out = X.adjudicate_foundation(zero, specialist_status="ELIGIBLE_PENDING_TARGET_SELECTION")
    assert out["terminal"] == "NO_TARGET_WINNER__REDESIGN_BEFORE_PROTECTED_CONFIRMATION"
    assert out["optional_specialists_eligible"] == ["C5_REGULATORY_SPECIALIST"]

    one = dict(zero, C1_SHARED_EMERGENT="ELIGIBLE_PENDING_TARGET_SELECTION")
    assert X.adjudicate_foundation(one)["terminal"] == "SINGLE_CANDIDATE_ELIGIBLE_FOR_PROTECTED_CONFIRMATION__NO_TARGET_AUTHORITY"

    many = dict(one, C3_QUERY_MEASURED="ELIGIBLE_PENDING_TARGET_SELECTION")
    assert X.adjudicate_foundation(many)["terminal"] == "MULTIPLE_QUALIFIED_TARGETS__PROTECTED_HEAD_TO_HEAD_REQUIRED__NO_TARGET_AUTHORITY"


def test_c4_cannot_be_eligible_without_c2_and_c3():
    statuses = {
        "C1_SHARED_EMERGENT": "ELIGIBLE_PENDING_TARGET_SELECTION",
        "C2_RELATIONAL_SHARED": "ELIMINATED_REAL_FAIL",
        "C3_QUERY_MEASURED": "ELIGIBLE_PENDING_TARGET_SELECTION",
        "C4_STRUCTURED_COMPOSITE": "ELIGIBLE_PENDING_TARGET_SELECTION",
    }
    out = X.adjudicate_foundation(statuses)
    assert "C4_STRUCTURED_COMPOSITE" not in out["eligible_foundation_candidates"]
    assert out["candidate_statuses"]["C4_STRUCTURED_COMPOSITE"] == "BLOCKED_BY_CONSTITUENT"


def test_unknown_statuses_fail_closed():
    cw = crosswalk()
    with pytest.raises(X.CrosswalkError):
        X.combine_candidate_evidence("C1_SHARED_EMERGENT", "MAYBE", [], cw)
    with pytest.raises(X.CrosswalkError):
        X.combine_candidate_evidence("C1_SHARED_EMERGENT", "PASS", [{"evidence_class": "DECISIVE_NEGATIVE", "status": "MAYBE"}], cw)
