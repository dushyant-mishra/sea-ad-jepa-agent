import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
EXPOSURE=json.loads((ROOT/"docs"/"agent"/"v5_anticheat"/"results"/"V5_ACTUAL_PRESENTATION_EXPOSURE_GEOMETRY_SUMMARY_V2.json").read_text())
EMA=json.loads((ROOT/"docs"/"agent"/"V5_EMA_EXPOSURE_DERIVATION_CANDIDATE_V1.json").read_text())
QUERY=json.loads((ROOT/"docs"/"agent"/"V5_SINGLETON_QUERY_PRECISION_AUTHORITY_CANDIDATE_V1.json").read_text())

def test_exposure_is_real_and_does_not_select_ema():
    assert EXPOSURE["synthetic_data_used"] is False
    assert EXPOSURE["worst_exposure_gaps"]["donor"]["max_gap"]==11384
    assert EXPOSURE["worst_exposure_gaps"]["operator"]["max_gap"]==37117
    assert EXPOSURE["interpretation"]["selected_ema_half_life"] is None

def test_ema_rule_uses_presentations_and_has_no_smoothing_default():
    assert EMA["time_unit"]=="successful_scientific_base_presentations"
    assert EMA["smoothing_rule"]["smoothing_multiple"] is None
    assert EMA["training_authorized"] is False

def test_query_floor_is_derived_at_the_20_to_21_boundary():
    assert QUERY["geometry"]["operator_family_geometry_sha256"]=="ccb94270405034f17e26e0c260aeacc8331d87a55a12083930343f774488671b"
    assert QUERY["derived_result"]["minimum_total_queries_per_base_cell"]==21
    assert QUERY["derived_result"]["worst_ratio_at_minimum"] < 0.05
    assert QUERY["derived_result"]["worst_ratio_at_previous"] > 0.05
    assert QUERY["synthetic_data_used_for_numeric_authority"] is False
