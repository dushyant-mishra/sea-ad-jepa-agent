from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v5"))

import td_target_tournament_routing_v3 as V3  # noqa: E402


def test_frozen_candidate_dependency_graph_and_no_authority():
    assert V3.FOUNDATION == (
        "C1_SHARED_EMERGENT",
        "C2_RELATIONAL_SHARED",
        "C3_QUERY_MEASURED",
        "C4_STRUCTURED_COMPOSITE",
    )
    assert V3.SPECIALISTS == ("C5_REGULATORY_SPECIALIST",)
    assert V3.RELATIONAL_DEPENDENT == frozenset({"C2_RELATIONAL_SHARED", "C4_STRUCTURED_COMPOSITE"})
    assert V3.RELATIONAL_INDEPENDENT == frozenset({"C1_SHARED_EMERGENT", "C3_QUERY_MEASURED"})
    assert all(value is False for value in V3.NO_AUTHORITY.values())


def test_relational_pass_keeps_all_foundation_routes_active():
    out = V3.route_relational_replay("PASS")
    assert out["candidate_routes"] == {
        "C1_SHARED_EMERGENT": "ACTIVE",
        "C2_RELATIONAL_SHARED": "ACTIVE",
        "C3_QUERY_MEASURED": "ACTIVE",
        "C4_STRUCTURED_COMPOSITE": "ACTIVE_SUBJECT_TO_C2_C3",
    }
    assert out["target_selected"] is False


def test_relational_fail_eliminates_only_relational_route_and_composite():
    out = V3.route_relational_replay("FAIL")
    assert out["candidate_routes"]["C1_SHARED_EMERGENT"] == "ACTIVE"
    assert out["candidate_routes"]["C3_QUERY_MEASURED"] == "ACTIVE"
    assert out["candidate_routes"]["C2_RELATIONAL_SHARED"] == "ELIMINATED_RELATIONAL_FAIL"
    assert out["candidate_routes"]["C4_STRUCTURED_COMPOSITE"] == "BLOCKED_BY_RELATIONAL_CONSTITUENT"
    assert out["independently_testable"] == ["C1_SHARED_EMERGENT", "C3_QUERY_MEASURED"]


def test_relational_not_estimable_does_not_kill_c1_or_c3():
    out = V3.route_relational_replay("NOT_ESTIMABLE")
    assert out["candidate_routes"]["C1_SHARED_EMERGENT"] == "ACTIVE"
    assert out["candidate_routes"]["C3_QUERY_MEASURED"] == "ACTIVE"
    assert out["candidate_routes"]["C2_RELATIONAL_SHARED"] == "UNRESOLVED_RELATIONAL_NOT_ESTIMABLE"
    assert out["candidate_routes"]["C4_STRUCTURED_COMPOSITE"] == "UNRESOLVED_RELATIONAL_CONSTITUENT"
    assert out["independently_testable"] == ["C1_SHARED_EMERGENT", "C3_QUERY_MEASURED"]


def test_unknown_relational_status_fails_closed():
    with pytest.raises(V3.RoutingV3Error):
        V3.route_relational_replay("MAYBE")


def _base(**updates):
    statuses = {
        "C1_SHARED_EMERGENT": "ELIMINATED",
        "C2_RELATIONAL_SHARED": "ELIMINATED",
        "C3_QUERY_MEASURED": "ELIMINATED",
        "C4_STRUCTURED_COMPOSITE": "ELIMINATED",
    }
    statuses.update(updates)
    return statuses


def test_zero_survivors_means_redesign_not_best_loser_rescue():
    out = V3.adjudicate_survivors(_base(), specialist_status="ELIGIBLE")
    assert out["terminal"] == "NO_TARGET_WINNER__REDESIGN_BEFORE_PROTECTED_CONFIRMATION"
    assert out["eligible_foundation_candidates"] == []
    assert out["optional_specialists_eligible"] == ["C5_REGULATORY_SPECIALIST"]
    assert out["target_selected"] is False


def test_exactly_one_survivor_advances_only_to_protected_confirmation():
    out = V3.adjudicate_survivors(_base(C1_SHARED_EMERGENT="ELIGIBLE"))
    assert out["terminal"] == "SINGLE_CANDIDATE_ELIGIBLE_FOR_PROTECTED_CONFIRMATION__NO_TARGET_AUTHORITY"
    assert out["eligible_foundation_candidates"] == ["C1_SHARED_EMERGENT"]
    assert out["target_selected"] is False


def test_multiple_survivors_require_head_to_head_without_forcing_winner():
    out = V3.adjudicate_survivors(_base(C1_SHARED_EMERGENT="ELIGIBLE", C3_QUERY_MEASURED="ELIGIBLE"))
    assert out["terminal"] == "MULTIPLE_QUALIFIED_TARGETS__PROTECTED_HEAD_TO_HEAD_REQUIRED__NO_TARGET_AUTHORITY"
    assert out["eligible_foundation_candidates"] == ["C1_SHARED_EMERGENT", "C3_QUERY_MEASURED"]
    assert out["target_selected"] is False


def test_unresolved_candidate_blocks_final_selection_but_not_independent_testing():
    out = V3.adjudicate_survivors(
        _base(
            C1_SHARED_EMERGENT="ELIGIBLE",
            C2_RELATIONAL_SHARED="UNRESOLVED",
            C3_QUERY_MEASURED="ELIGIBLE",
            C4_STRUCTURED_COMPOSITE="UNRESOLVED",
        )
    )
    assert out["terminal"] == "FOUNDATION_CANDIDATE_UNRESOLVED__CONTINUE_TESTABLE_ROUTES__NO_TARGET_AUTHORITY"
    assert out["eligible_foundation_candidates"] == ["C1_SHARED_EMERGENT", "C3_QUERY_MEASURED"]
    assert out["unresolved_foundation_candidates"] == ["C2_RELATIONAL_SHARED", "C4_STRUCTURED_COMPOSITE"]
    assert out["target_selected"] is False


def test_c4_cannot_survive_without_both_c2_and_c3():
    out = V3.adjudicate_survivors(
        _base(
            C2_RELATIONAL_SHARED="ELIMINATED",
            C3_QUERY_MEASURED="ELIGIBLE",
            C4_STRUCTURED_COMPOSITE="ELIGIBLE",
        )
    )
    assert out["candidate_statuses"]["C4_STRUCTURED_COMPOSITE"] == "BLOCKED_BY_CONSTITUENT"
    assert "C4_STRUCTURED_COMPOSITE" not in out["eligible_foundation_candidates"]


def test_c5_never_changes_foundation_terminal():
    statuses = _base(C1_SHARED_EMERGENT="ELIGIBLE")
    no_specialist = V3.adjudicate_survivors(statuses, specialist_status="ELIMINATED")
    specialist = V3.adjudicate_survivors(statuses, specialist_status="ELIGIBLE")
    assert no_specialist["terminal"] == specialist["terminal"]
    assert no_specialist["optional_specialists_eligible"] == []
    assert specialist["optional_specialists_eligible"] == ["C5_REGULATORY_SPECIALIST"]


def test_invalid_candidate_statuses_fail_closed_and_authority_stays_off():
    with pytest.raises(V3.RoutingV3Error):
        V3.adjudicate_survivors(_base(C1_SHARED_EMERGENT="BEST_SCORE"))
    out = V3.adjudicate_survivors(_base(C1_SHARED_EMERGENT="ELIGIBLE"))
    for key in (
        "target_selected",
        "representation_selected",
        "corrected_replay_authorized",
        "td60_authorized",
        "stage4_authorized",
        "training_authorized",
    ):
        assert out[key] is False
