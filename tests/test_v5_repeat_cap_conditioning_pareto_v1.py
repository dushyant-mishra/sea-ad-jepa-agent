import json
from pathlib import Path

OBJ=json.loads((Path(__file__).resolve().parents[1]/"docs"/"agent"/"v5_anticheat"/"results"/"V5_REPEAT_CAP_CONDITIONING_PARETO_SUMMARY_V1.json").read_text())

def test_cap_32_is_not_claimed_as_data_required():
    assert OBJ["data_derived_findings"]["minimum_cap_that_can_achieve_ess_0_5_at_all"]==11
    assert OBJ["data_derived_findings"]["cap_10_can_achieve_ess_0_5"] is False
    rows={r["cap"]:r for r in OBJ["data_derived_findings"]["selected_frontier_points"]}
    assert rows[32]["weight_ratio_lower_bound"] > 64
    assert rows[34]["weight_ratio_lower_bound"] < 64
    assert OBJ["training_authorized"] is False
    assert OBJ["synthetic_data_used"] is False

def test_more_repeat_capacity_moves_the_real_conditioning_frontier():
    rows={r["cap"]:r for r in OBJ["data_derived_findings"]["selected_frontier_points"]}
    assert rows[11]["total_presentations"] > rows[32]["total_presentations"] > rows[64]["total_presentations"]
    assert rows[11]["weight_ratio_lower_bound"] > rows[32]["weight_ratio_lower_bound"] > rows[64]["weight_ratio_lower_bound"]
