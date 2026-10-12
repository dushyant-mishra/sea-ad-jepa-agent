from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v5"))

import td_protected_head_to_head_v1 as H  # noqa: E402


def dims(default="NONINFERIOR", **updates):
    out = {name: default for name in H.DIMENSIONS}
    out.update(updates)
    return out


def pair(a, b, values=None):
    return {"candidate_a": a, "candidate_b": b, "dimensions": values or dims()}


def test_frozen_components_dimensions_and_authority_boundary():
    assert H.COMPONENTS["C1_SHARED_EMERGENT"] == frozenset({"SHARED"})
    assert H.COMPONENTS["C4_STRUCTURED_COMPOSITE"] == frozenset({"SHARED", "RELATIONAL", "QUERY"})
    assert len(H.DIMENSIONS) == 7
    assert all(value is False for value in H.NO_AUTHORITY.values())


def test_all_noninferior_uses_subset_simplicity_only():
    assert H.compare_pair(pair("C1_SHARED_EMERGENT", "C2_RELATIONAL_SHARED")) == "A_DOMINATES_SIMPLER"
    assert H.compare_pair(pair("C1_SHARED_EMERGENT", "C3_QUERY_MEASURED")) == "INCOMPARABLE"


def test_better_without_worse_dominates_but_mixed_tradeoff_does_not():
    a = pair("C1_SHARED_EMERGENT", "C3_QUERY_MEASURED", dims(BIOLOGICAL_INFORMATION="BETTER"))
    assert H.compare_pair(a) == "A_DOMINATES"
    mixed = pair(
        "C1_SHARED_EMERGENT",
        "C3_QUERY_MEASURED",
        dims(BIOLOGICAL_INFORMATION="BETTER", DONOR_TRANSFER="WORSE"),
    )
    assert H.compare_pair(mixed) == "INCOMPARABLE"


def test_worse_without_better_means_b_dominates():
    rec = pair("C1_SHARED_EMERGENT", "C3_QUERY_MEASURED", dims(BIOLOGICAL_INFORMATION="WORSE"))
    assert H.compare_pair(rec) == "B_DOMINATES"


def test_not_estimable_prevents_pairwise_dominance():
    rec = pair("C1_SHARED_EMERGENT", "C2_RELATIONAL_SHARED", dims(SOURCE_TRANSFER="NOT_ESTIMABLE"))
    assert H.compare_pair(rec) == "UNRESOLVED"


def test_unique_candidate_dominating_every_other_survivor_is_only_a_leader():
    survivors = ["C1_SHARED_EMERGENT", "C2_RELATIONAL_SHARED", "C3_QUERY_MEASURED"]
    comparisons = [
        pair("C1_SHARED_EMERGENT", "C2_RELATIONAL_SHARED"),
        pair("C1_SHARED_EMERGENT", "C3_QUERY_MEASURED", dims(BIOLOGICAL_INFORMATION="BETTER")),
        pair("C2_RELATIONAL_SHARED", "C3_QUERY_MEASURED", dims(BIOLOGICAL_INFORMATION="WORSE")),
    ]
    out = H.adjudicate(survivors, comparisons)
    assert out["leader"] == "C1_SHARED_EMERGENT"
    assert out["terminal"] == "UNIQUE_HEAD_TO_HEAD_LEADER__PROTECTED_CONFIRMATION_REQUIRED__NO_TARGET_AUTHORITY"
    assert out["target_selected"] is False


def test_incomparable_survivors_do_not_force_winner():
    survivors = ["C1_SHARED_EMERGENT", "C3_QUERY_MEASURED"]
    out = H.adjudicate(survivors, [pair(*survivors)])
    assert out["leader"] is None
    assert out["terminal"] == "MULTIPLE_QUALIFIED_TARGETS__INCOMPARABLE__NO_TARGET_AUTHORITY"


def test_not_estimable_or_missing_pair_returns_unresolved_terminal():
    survivors = ["C1_SHARED_EMERGENT", "C2_RELATIONAL_SHARED", "C3_QUERY_MEASURED"]
    incomplete = H.adjudicate(survivors, [pair("C1_SHARED_EMERGENT", "C2_RELATIONAL_SHARED")])
    assert incomplete["terminal"] == "HEAD_TO_HEAD_UNRESOLVED__NO_TARGET_AUTHORITY"
    assert incomplete["missing_pairs"]

    unresolved = H.adjudicate(
        ["C1_SHARED_EMERGENT", "C2_RELATIONAL_SHARED"],
        [pair("C1_SHARED_EMERGENT", "C2_RELATIONAL_SHARED", dims(SOURCE_TRANSFER="NOT_ESTIMABLE"))],
    )
    assert unresolved["terminal"] == "HEAD_TO_HEAD_UNRESOLVED__NO_TARGET_AUTHORITY"


def test_c5_cannot_enter_foundation_head_to_head():
    with pytest.raises(H.HeadToHeadError):
        H.adjudicate(["C1_SHARED_EMERGENT", "C5_REGULATORY_SPECIALIST"], [])


def test_invalid_dimension_or_duplicate_pair_fails_closed():
    bad = pair("C1_SHARED_EMERGENT", "C2_RELATIONAL_SHARED")
    bad["dimensions"]["DONOR_TRANSFER"] = "MAYBE"
    with pytest.raises(H.HeadToHeadError):
        H.compare_pair(bad)

    rec = pair("C1_SHARED_EMERGENT", "C2_RELATIONAL_SHARED")
    with pytest.raises(H.HeadToHeadError):
        H.adjudicate(["C1_SHARED_EMERGENT", "C2_RELATIONAL_SHARED"], [rec, rec])


def test_adjudication_never_grants_downstream_authority():
    out = H.adjudicate(
        ["C1_SHARED_EMERGENT", "C2_RELATIONAL_SHARED"],
        [pair("C1_SHARED_EMERGENT", "C2_RELATIONAL_SHARED")],
    )
    for key, value in H.NO_AUTHORITY.items():
        assert out[key] is value is False
