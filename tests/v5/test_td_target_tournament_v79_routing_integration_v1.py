from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v5"))

import td_target_tournament_routing_v3 as V3  # noqa: E402
import td_v79_synthetic_crosswalk_v1 as X  # noqa: E402


def test_exact_crosswalk_status_projection_is_frozen():
    assert V3.CROSSWALK_STATUS_TO_V3 == {
        X.ELIGIBLE: "ELIGIBLE",
        "ELIMINATED_REAL_FAIL": "ELIMINATED",
        "ELIMINATED_SYNTHETIC_FALSIFIER": "ELIMINATED",
        "UNRESOLVED_REAL_NOT_ESTIMABLE": "UNRESOLVED",
        "BLOCKED_BY_CONSTITUENT": "BLOCKED_BY_CONSTITUENT",
    }


def test_crosswalk_unresolved_candidate_blocks_final_selection_but_preserves_live_routes():
    statuses = {
        "C1_SHARED_EMERGENT": X.ELIGIBLE,
        "C2_RELATIONAL_SHARED": "UNRESOLVED_REAL_NOT_ESTIMABLE",
        "C3_QUERY_MEASURED": X.ELIGIBLE,
        "C4_STRUCTURED_COMPOSITE": "BLOCKED_BY_CONSTITUENT",
    }
    out = V3.adjudicate_crosswalk_statuses(statuses)
    assert out["terminal"] == "FOUNDATION_CANDIDATE_UNRESOLVED__CONTINUE_TESTABLE_ROUTES__NO_TARGET_AUTHORITY"
    assert out["eligible_foundation_candidates"] == ["C1_SHARED_EMERGENT", "C3_QUERY_MEASURED"]
    assert out["unresolved_foundation_candidates"] == ["C2_RELATIONAL_SHARED"]


def test_crosswalk_relational_failure_still_allows_independent_multiple_survivors():
    statuses = {
        "C1_SHARED_EMERGENT": X.ELIGIBLE,
        "C2_RELATIONAL_SHARED": "ELIMINATED_REAL_FAIL",
        "C3_QUERY_MEASURED": X.ELIGIBLE,
        "C4_STRUCTURED_COMPOSITE": "BLOCKED_BY_CONSTITUENT",
    }
    out = V3.adjudicate_crosswalk_statuses(statuses)
    assert out["terminal"] == "MULTIPLE_QUALIFIED_TARGETS__PROTECTED_HEAD_TO_HEAD_REQUIRED__NO_TARGET_AUTHORITY"
    assert out["eligible_foundation_candidates"] == ["C1_SHARED_EMERGENT", "C3_QUERY_MEASURED"]


def test_crosswalk_status_adapter_rejects_unknown_or_missing_candidate():
    statuses = {
        "C1_SHARED_EMERGENT": X.ELIGIBLE,
        "C2_RELATIONAL_SHARED": "ELIMINATED_REAL_FAIL",
        "C3_QUERY_MEASURED": X.ELIGIBLE,
        "C4_STRUCTURED_COMPOSITE": "BEST_SCORE",
    }
    with pytest.raises(V3.RoutingV3Error):
        V3.adjudicate_crosswalk_statuses(statuses)
    del statuses["C4_STRUCTURED_COMPOSITE"]
    with pytest.raises(V3.RoutingV3Error):
        V3.adjudicate_crosswalk_statuses(statuses)


def test_specialist_projection_never_changes_foundation_terminal():
    statuses = {
        "C1_SHARED_EMERGENT": X.ELIGIBLE,
        "C2_RELATIONAL_SHARED": "ELIMINATED_REAL_FAIL",
        "C3_QUERY_MEASURED": "ELIMINATED_SYNTHETIC_FALSIFIER",
        "C4_STRUCTURED_COMPOSITE": "BLOCKED_BY_CONSTITUENT",
    }
    a = V3.adjudicate_crosswalk_statuses(statuses, specialist_status="ELIMINATED_REAL_FAIL")
    b = V3.adjudicate_crosswalk_statuses(statuses, specialist_status=X.ELIGIBLE)
    assert a["terminal"] == b["terminal"] == "SINGLE_CANDIDATE_ELIGIBLE_FOR_PROTECTED_CONFIRMATION__NO_TARGET_AUTHORITY"
    assert b["optional_specialists_eligible"] == ["C5_REGULATORY_SPECIALIST"]
