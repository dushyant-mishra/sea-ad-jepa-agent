from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v5"))

import td_corrected_replay_routing_v1 as R  # noqa: E402


def call(td56="PASS", td57b="PASS", td57c="FAIL", td59="PASS", source="PASS"):
    return R.interpret_corrected_replay(
        td56=td56,
        td57b=td57b,
        td57c=td57c,
        td59=td59,
        universal_source=source,
    )


def test_broad_meso_viable_maps_to_relational_pass_but_not_target_winner():
    out = call()
    assert out["biological_state"] == "BROAD_MESO_RELATIONAL_VIABLE__NOT_TARGET_WINNER"
    assert out["v3_relational_status"] == "PASS"
    assert out["candidate_routes"]["C2_RELATIONAL_SHARED"] == "ACTIVE"
    assert out["target_selected"] is False


def test_td56_fail_stops_relational_promotion_and_preserves_c1_c3():
    out = call(td56="FAIL", td57b="PASS", td57c="FAIL", td59="PASS")
    assert out["biological_state"] == "RELATIONAL_PROMOTION_STOP__TD56_FAIL"
    assert out["v3_relational_status"] == "FAIL"
    assert out["candidate_routes"]["C1_SHARED_EMERGENT"] == "ACTIVE"
    assert out["candidate_routes"]["C3_QUERY_MEASURED"] == "ACTIVE"
    assert out["candidate_routes"]["C2_RELATIONAL_SHARED"] == "ELIMINATED_RELATIONAL_FAIL"


def test_td57b_fail_cannot_be_rescued_by_td59():
    a = call(td57b="FAIL", td59="PASS")
    b = call(td57b="FAIL", td59="FAIL")
    assert a["biological_state"] == b["biological_state"] == "NO_STRONGER_RECURRENT_SCALE_FREE_ORDER__TD57B_FAIL"
    assert a["v3_relational_status"] == b["v3_relational_status"] == "FAIL"


def test_td57c_pass_is_divergence_not_relational_pass_regardless_of_td59():
    a = call(td57c="PASS", td59="PASS")
    b = call(td57c="PASS", td59="FAIL")
    for out in (a, b):
        assert out["biological_state"] == "DIVERGENCE__PROSPECTIVE_LOCALITY_EXPERIMENT_REQUIRED"
        assert out["v3_relational_status"] == "NOT_ESTIMABLE"
        assert out["candidate_routes"]["C2_RELATIONAL_SHARED"] == "UNRESOLVED_RELATIONAL_NOT_ESTIMABLE"
        assert out["locality_experiment_required"] is True


def test_td59_fail_after_56_57b_pass_and_57c_fail_is_broad_global_only():
    out = call(td59="FAIL")
    assert out["biological_state"] == "BROAD_GLOBAL_ONLY__CURRENT_C2_NOT_QUALIFIED"
    assert out["v3_relational_status"] == "FAIL"


@pytest.mark.parametrize(
    "kwargs,state",
    [
        ({"td56": "NOT_ESTIMABLE"}, "NOT_ESTIMABLE__TD56__NO_BIOLOGICAL_PASS"),
        ({"td57b": "NOT_ESTIMABLE"}, "NOT_ESTIMABLE__TD57B__NO_BIOLOGICAL_PASS"),
        ({"td57c": "NOT_ESTIMABLE"}, "NOT_ESTIMABLE__TD57C__NO_BIOLOGICAL_PASS"),
        ({"td59": "NOT_ESTIMABLE"}, "NOT_ESTIMABLE__TD59__NO_BIOLOGICAL_PASS"),
    ],
)
def test_each_not_estimable_path_remains_unresolved(kwargs, state):
    out = call(**kwargs)
    assert out["biological_state"] == state
    assert out["v3_relational_status"] == "NOT_ESTIMABLE"
    assert out["candidate_routes"]["C1_SHARED_EMERGENT"] == "ACTIVE"
    assert out["candidate_routes"]["C3_QUERY_MEASURED"] == "ACTIVE"


def test_source_failure_overrides_favorable_within_source_result_for_universal_c2():
    out = call(source="FAIL")
    assert out["biological_state"] == "SOURCE_DISAGREEMENT__UNIVERSAL_RELATIONAL_TARGET_NOT_QUALIFIED"
    assert out["v3_relational_status"] == "FAIL"
    assert out["source_averaging_rescue_allowed"] is False


def test_source_not_estimable_leaves_relational_foundation_unresolved():
    out = call(source="NOT_ESTIMABLE")
    assert out["biological_state"] == "NOT_ESTIMABLE__UNIVERSAL_SOURCE_REPLICATION__NO_BIOLOGICAL_PASS"
    assert out["v3_relational_status"] == "NOT_ESTIMABLE"


def test_invalid_status_fails_closed():
    with pytest.raises(R.CorrectedReplayRoutingError):
        call(td57c="MAYBE")
    with pytest.raises(R.CorrectedReplayRoutingError):
        call(source="MIXED")


def test_all_downstream_authority_stays_false():
    out = call()
    for key in (
        "corrected_replay_authorized",
        "target_selected",
        "representation_selected",
        "td60_authorized",
        "stage4_authorized",
        "training_authorized",
    ):
        assert out[key] is False
