from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v5"))

import td_corrected_replay_routing_v2 as R  # noqa: E402


def call(td56="PASS", td57b="PASS", td57c="FAIL", td59="PASS", source="PASS"):
    return R.interpret_corrected_replay(
        td56=td56,
        td57b=td57b,
        td57c=td57c,
        td59=td59,
        universal_source=source,
    )


def test_v1_biological_state_is_preserved_but_projection_is_v4():
    out = call()
    assert out["biological_state"] == "BROAD_MESO_RELATIONAL_VIABLE__NOT_TARGET_WINNER"
    assert out["v4_relational_status"] == "PASS"
    assert out["candidate_routes"]["C6_SHARED_QUERY_COMPOSITE"] == "ACTIVE_SUBJECT_TO_C1_C3"
    assert out["target_selected"] is False


def test_relational_fail_keeps_c6_independent_and_blocks_only_c2_c4():
    out = call(td56="FAIL")
    assert out["v4_relational_status"] == "FAIL"
    assert out["candidate_routes"]["C1_SHARED_EMERGENT"] == "ACTIVE"
    assert out["candidate_routes"]["C3_QUERY_MEASURED"] == "ACTIVE"
    assert out["candidate_routes"]["C6_SHARED_QUERY_COMPOSITE"] == "ACTIVE_SUBJECT_TO_C1_C3"
    assert out["candidate_routes"]["C2_RELATIONAL_SHARED"] == "ELIMINATED_RELATIONAL_FAIL"
    assert out["candidate_routes"]["C4_STRUCTURED_COMPOSITE"] == "BLOCKED_BY_RELATIONAL_CONSTITUENT"


def test_divergence_and_not_estimable_leave_c6_active_but_c2_c4_unresolved():
    for out in (call(td57c="PASS"), call(td57b="NOT_ESTIMABLE")):
        assert out["v4_relational_status"] == "NOT_ESTIMABLE"
        assert out["candidate_routes"]["C6_SHARED_QUERY_COMPOSITE"] == "ACTIVE_SUBJECT_TO_C1_C3"
        assert out["candidate_routes"]["C2_RELATIONAL_SHARED"] == "UNRESOLVED_RELATIONAL_NOT_ESTIMABLE"
        assert out["candidate_routes"]["C4_STRUCTURED_COMPOSITE"] == "UNRESOLVED_RELATIONAL_CONSTITUENT"


def test_source_failure_does_not_eliminate_c6():
    out = call(source="FAIL")
    assert out["biological_state"] == "SOURCE_DISAGREEMENT__UNIVERSAL_RELATIONAL_TARGET_NOT_QUALIFIED"
    assert out["v4_relational_status"] == "FAIL"
    assert out["candidate_routes"]["C6_SHARED_QUERY_COMPOSITE"] == "ACTIVE_SUBJECT_TO_C1_C3"
    assert out["source_averaging_rescue_allowed"] is False


def test_v2_preserves_td57b_no_rescue_and_td57c_divergence():
    assert call(td57b="FAIL", td59="PASS")["biological_state"] == "NO_STRONGER_RECURRENT_SCALE_FREE_ORDER__TD57B_FAIL"
    assert call(td57b="FAIL", td59="FAIL")["biological_state"] == "NO_STRONGER_RECURRENT_SCALE_FREE_ORDER__TD57B_FAIL"
    assert call(td57c="PASS", td59="PASS")["biological_state"] == "DIVERGENCE__PROSPECTIVE_LOCALITY_EXPERIMENT_REQUIRED"
    assert call(td57c="PASS", td59="FAIL")["biological_state"] == "DIVERGENCE__PROSPECTIVE_LOCALITY_EXPERIMENT_REQUIRED"


def test_invalid_status_and_all_authority_fail_closed():
    with pytest.raises(R.CorrectedReplayRoutingError):
        call(td56="MAYBE")
    out = call()
    for key in R.NO_AUTHORITY:
        assert out[key] is False
