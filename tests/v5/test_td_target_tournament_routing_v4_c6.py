from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v5"))

import td_target_tournament_routing_v4 as V4  # noqa: E402


def base(**updates):
    out = {cid: "ELIMINATED" for cid in V4.FOUNDATION}
    out.update(updates)
    return out


def test_v4_foundation_adds_c6_without_changing_c5_specialist_role():
    assert V4.FOUNDATION == (
        "C1_SHARED_EMERGENT",
        "C2_RELATIONAL_SHARED",
        "C3_QUERY_MEASURED",
        "C6_SHARED_QUERY_COMPOSITE",
        "C4_STRUCTURED_COMPOSITE",
    )
    assert V4.SPECIALISTS == ("C5_REGULATORY_SPECIALIST",)
    assert "C6_SHARED_QUERY_COMPOSITE" in V4.RELATIONAL_INDEPENDENT
    assert "C6_SHARED_QUERY_COMPOSITE" not in V4.RELATIONAL_DEPENDENT


def test_relational_fail_preserves_c1_c3_c6_and_blocks_c2_c4():
    out = V4.route_relational_replay("FAIL")
    assert out["candidate_routes"]["C1_SHARED_EMERGENT"] == "ACTIVE"
    assert out["candidate_routes"]["C3_QUERY_MEASURED"] == "ACTIVE"
    assert out["candidate_routes"]["C6_SHARED_QUERY_COMPOSITE"] == "ACTIVE_SUBJECT_TO_C1_C3"
    assert out["candidate_routes"]["C2_RELATIONAL_SHARED"] == "ELIMINATED_RELATIONAL_FAIL"
    assert out["candidate_routes"]["C4_STRUCTURED_COMPOSITE"] == "BLOCKED_BY_RELATIONAL_CONSTITUENT"


def test_c6_eligible_requires_c1_and_c3_eligible():
    out = V4.adjudicate_survivors(base(
        C1_SHARED_EMERGENT="ELIGIBLE",
        C3_QUERY_MEASURED="ELIGIBLE",
        C6_SHARED_QUERY_COMPOSITE="ELIGIBLE",
    ))
    assert "C6_SHARED_QUERY_COMPOSITE" in out["eligible_foundation_candidates"]

    blocked = V4.adjudicate_survivors(base(
        C1_SHARED_EMERGENT="ELIMINATED",
        C3_QUERY_MEASURED="ELIGIBLE",
        C6_SHARED_QUERY_COMPOSITE="ELIGIBLE",
    ))
    assert blocked["candidate_statuses"]["C6_SHARED_QUERY_COMPOSITE"] == "BLOCKED_BY_CONSTITUENT"


def test_c6_unresolved_constituent_propagates_unresolved_not_failure():
    out = V4.adjudicate_survivors(base(
        C1_SHARED_EMERGENT="UNRESOLVED",
        C3_QUERY_MEASURED="ELIGIBLE",
        C6_SHARED_QUERY_COMPOSITE="ELIGIBLE",
    ))
    assert out["candidate_statuses"]["C6_SHARED_QUERY_COMPOSITE"] == "UNRESOLVED_BY_CONSTITUENT"
    assert "C6_SHARED_QUERY_COMPOSITE" in out["unresolved_foundation_candidates"]
    assert out["terminal"] == "FOUNDATION_CANDIDATE_UNRESOLVED__CONTINUE_TESTABLE_ROUTES__NO_TARGET_AUTHORITY"


def test_c4_unresolved_parent_propagates_unresolved_and_failed_parent_blocks():
    unresolved = V4.adjudicate_survivors(base(
        C2_RELATIONAL_SHARED="UNRESOLVED",
        C3_QUERY_MEASURED="ELIGIBLE",
        C4_STRUCTURED_COMPOSITE="ELIGIBLE",
    ))
    assert unresolved["candidate_statuses"]["C4_STRUCTURED_COMPOSITE"] == "UNRESOLVED_BY_CONSTITUENT"

    blocked = V4.adjudicate_survivors(base(
        C2_RELATIONAL_SHARED="ELIMINATED",
        C3_QUERY_MEASURED="ELIGIBLE",
        C4_STRUCTURED_COMPOSITE="ELIGIBLE",
    ))
    assert blocked["candidate_statuses"]["C4_STRUCTURED_COMPOSITE"] == "BLOCKED_BY_CONSTITUENT"


def test_relational_not_estimable_does_not_make_c6_unresolved_by_itself():
    out = V4.route_relational_replay("NOT_ESTIMABLE")
    assert out["candidate_routes"]["C6_SHARED_QUERY_COMPOSITE"] == "ACTIVE_SUBJECT_TO_C1_C3"
    assert out["candidate_routes"]["C2_RELATIONAL_SHARED"] == "UNRESOLVED_RELATIONAL_NOT_ESTIMABLE"


def test_zero_one_multiple_survivor_law_includes_c6():
    assert V4.adjudicate_survivors(base())["terminal"] == "NO_TARGET_WINNER__REDESIGN_BEFORE_PROTECTED_CONFIRMATION"
    one = V4.adjudicate_survivors(base(C1_SHARED_EMERGENT="ELIGIBLE"))
    assert one["terminal"] == "SINGLE_CANDIDATE_ELIGIBLE_FOR_PROTECTED_CONFIRMATION__NO_TARGET_AUTHORITY"
    many = V4.adjudicate_survivors(base(C1_SHARED_EMERGENT="ELIGIBLE", C3_QUERY_MEASURED="ELIGIBLE"))
    assert many["terminal"] == "MULTIPLE_QUALIFIED_TARGETS__PROTECTED_HEAD_TO_HEAD_REQUIRED__NO_TARGET_AUTHORITY"


def test_invalid_status_and_downstream_authority_fail_closed():
    with pytest.raises(V4.RoutingV4Error):
        V4.adjudicate_survivors(base(C6_SHARED_QUERY_COMPOSITE="BEST"))
    out = V4.adjudicate_survivors(base(C1_SHARED_EMERGENT="ELIGIBLE"))
    assert all(out[key] is False for key in V4.NO_AUTHORITY)
