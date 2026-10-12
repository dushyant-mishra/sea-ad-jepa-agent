from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v5"))

import td_protected_head_to_head_v2 as H  # noqa: E402


def dims(default="NONINFERIOR", **updates):
    out = {name: default for name in H.DIMENSIONS}
    out.update(updates)
    return out


def pair(a, b, values=None):
    return {"candidate_a": a, "candidate_b": b, "dimensions": values or dims()}


def test_c6_component_lattice_is_frozen():
    assert H.COMPONENTS["C6_SHARED_QUERY_COMPOSITE"] == frozenset({"SHARED", "QUERY"})
    assert H.COMPONENTS["C1_SHARED_EMERGENT"] < H.COMPONENTS["C6_SHARED_QUERY_COMPOSITE"]
    assert H.COMPONENTS["C3_QUERY_MEASURED"] < H.COMPONENTS["C6_SHARED_QUERY_COMPOSITE"]
    assert H.COMPONENTS["C6_SHARED_QUERY_COMPOSITE"] < H.COMPONENTS["C4_STRUCTURED_COMPOSITE"]
    assert not (H.COMPONENTS["C2_RELATIONAL_SHARED"] < H.COMPONENTS["C6_SHARED_QUERY_COMPOSITE"])
    assert not (H.COMPONENTS["C6_SHARED_QUERY_COMPOSITE"] < H.COMPONENTS["C2_RELATIONAL_SHARED"])


def test_noninferior_ties_use_only_component_subset_simplicity():
    assert H.compare_pair(pair("C1_SHARED_EMERGENT", "C6_SHARED_QUERY_COMPOSITE")) == "A_DOMINATES_SIMPLER"
    assert H.compare_pair(pair("C3_QUERY_MEASURED", "C6_SHARED_QUERY_COMPOSITE")) == "A_DOMINATES_SIMPLER"
    assert H.compare_pair(pair("C6_SHARED_QUERY_COMPOSITE", "C4_STRUCTURED_COMPOSITE")) == "A_DOMINATES_SIMPLER"
    assert H.compare_pair(pair("C2_RELATIONAL_SHARED", "C6_SHARED_QUERY_COMPOSITE")) == "INCOMPARABLE"


def test_c6_can_be_unique_leader_only_by_same_protected_dimension_law():
    survivors = ["C1_SHARED_EMERGENT", "C3_QUERY_MEASURED", "C6_SHARED_QUERY_COMPOSITE"]
    comparisons = [
        pair("C1_SHARED_EMERGENT", "C3_QUERY_MEASURED"),
        pair("C1_SHARED_EMERGENT", "C6_SHARED_QUERY_COMPOSITE", dims(BIOLOGICAL_INFORMATION="WORSE")),
        pair("C3_QUERY_MEASURED", "C6_SHARED_QUERY_COMPOSITE", dims(DONOR_TRANSFER="WORSE")),
    ]
    out = H.adjudicate(survivors, comparisons)
    assert out["leader"] == "C6_SHARED_QUERY_COMPOSITE"
    assert out["terminal"] == "UNIQUE_HEAD_TO_HEAD_LEADER__PROTECTED_CONFIRMATION_REQUIRED__NO_TARGET_AUTHORITY"
    assert out["target_selected"] is False


def test_c6_does_not_enter_if_not_in_survivor_set_and_c5_stays_forbidden():
    with pytest.raises(H.HeadToHeadError):
        H.adjudicate(["C1_SHARED_EMERGENT", "C5_REGULATORY_SPECIALIST"], [])
    with pytest.raises(H.HeadToHeadError):
        H.adjudicate(
            ["C1_SHARED_EMERGENT", "C3_QUERY_MEASURED"],
            [pair("C1_SHARED_EMERGENT", "C6_SHARED_QUERY_COMPOSITE")],
        )
