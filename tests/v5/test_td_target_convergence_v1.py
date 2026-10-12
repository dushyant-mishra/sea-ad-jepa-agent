from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v5"))

import td_target_convergence_v1 as C  # noqa: E402


def statuses(**overrides):
    base = {cid: "ELIMINATED" for cid in C.FOUNDATION}
    base.update(overrides)
    return base


def dims(value="NONINFERIOR", **overrides):
    out = {name: value for name in C.H2H.DIMENSIONS}
    out.update(overrides)
    return out


def pair(a, b, **overrides):
    return {"candidate_a": a, "candidate_b": b, "dimensions": dims(**overrides)}


def test_zero_survivors_returns_redesign_and_no_authority():
    out = C.converge(statuses())
    assert out["terminal"] == "NO_TARGET_WINNER__REDESIGN_BEFORE_PROTECTED_CONFIRMATION"
    assert out["finalist"] is None
    assert out["target_selected"] is False
    assert out["training_authorized"] is False


def test_single_survivor_requires_protected_confirmation():
    out = C.converge(statuses(C1_SHARED_EMERGENT="ELIGIBLE"))
    assert out["finalist"] == "C1_SHARED_EMERGENT"
    assert out["terminal"] == "PROTECTED_CONFIRMATION_REQUIRED__NO_TARGET_AUTHORITY"


def test_multiple_survivors_require_complete_h2h_and_can_yield_unique_finalist():
    s = statuses(C1_SHARED_EMERGENT="ELIGIBLE", C2_RELATIONAL_SHARED="ELIGIBLE")
    out = C.converge(s, comparisons=[pair("C1_SHARED_EMERGENT", "C2_RELATIONAL_SHARED")])
    # all NONINFERIOR => strict component-subset simplicity chooses C1
    assert out["finalist"] == "C1_SHARED_EMERGENT"
    assert out["terminal"] == "PROTECTED_CONFIRMATION_REQUIRED__NO_TARGET_AUTHORITY"


def test_multiple_incomparable_stays_multiple():
    s = statuses(C1_SHARED_EMERGENT="ELIGIBLE", C3_QUERY_MEASURED="ELIGIBLE")
    out = C.converge(s, comparisons=[pair(
        "C1_SHARED_EMERGENT", "C3_QUERY_MEASURED",
        BIOLOGICAL_INFORMATION="BETTER", DONOR_TRANSFER="WORSE",
    )])
    assert out["finalist"] is None
    assert out["terminal"] == "MULTIPLE_QUALIFIED_TARGETS__INCOMPARABLE__NO_TARGET_AUTHORITY"


def test_missing_h2h_is_unresolved_not_arbitrary_winner():
    s = statuses(C1_SHARED_EMERGENT="ELIGIBLE", C2_RELATIONAL_SHARED="ELIGIBLE", C3_QUERY_MEASURED="ELIGIBLE")
    out = C.converge(s, comparisons=[pair("C1_SHARED_EMERGENT", "C3_QUERY_MEASURED")])
    assert out["finalist"] is None
    assert out["terminal"] == "HEAD_TO_HEAD_UNRESOLVED__NO_TARGET_AUTHORITY"


def test_unresolved_candidate_preempts_selection():
    s = statuses(C1_SHARED_EMERGENT="ELIGIBLE", C3_QUERY_MEASURED="UNRESOLVED")
    out = C.converge(s)
    assert out["terminal"] == "FOUNDATION_CANDIDATE_UNRESOLVED__CONTINUE_TESTABLE_ROUTES__NO_TARGET_AUTHORITY"
    assert out["finalist"] is None


def test_composite_dependency_resolution_is_preserved():
    s = statuses(C1_SHARED_EMERGENT="ELIMINATED", C3_QUERY_MEASURED="ELIGIBLE", C6_SHARED_QUERY_COMPOSITE="ELIGIBLE")
    out = C.converge(s)
    assert out["candidate_statuses"]["C6_SHARED_QUERY_COMPOSITE"] == "BLOCKED_BY_CONSTITUENT"
    assert out["finalist"] == "C3_QUERY_MEASURED"


@pytest.mark.parametrize(
    "confirmation,terminal",
    [
        ("PASS", "TARGET_CANDIDATE_CONFIRMED__OWNER_SELECTION_DECISION_REQUIRED__NO_TARGET_AUTHORITY"),
        ("FAIL", "PROTECTED_CONFIRMATION_FAILED__NO_TARGET_WINNER__REDESIGN"),
        ("NOT_ESTIMABLE", "PROTECTED_CONFIRMATION_NOT_ESTIMABLE__NO_TARGET_AUTHORITY"),
    ],
)
def test_protected_confirmation_never_self_selects(confirmation, terminal):
    out = C.converge(statuses(C1_SHARED_EMERGENT="ELIGIBLE"), protected_confirmation=confirmation)
    assert out["terminal"] == terminal
    assert out["finalist"] == "C1_SHARED_EMERGENT"
    assert out["target_selected"] is False
    assert out["representation_selected"] is False
    assert out["td60_authorized"] is False
    assert out["stage4_authorized"] is False
    assert out["training_authorized"] is False


def test_confirmation_is_forbidden_without_unique_finalist():
    with pytest.raises(C.TargetConvergenceError):
        C.converge(statuses(), protected_confirmation="PASS")
