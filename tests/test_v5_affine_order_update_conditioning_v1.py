import json
from pathlib import Path

OBJ=json.loads((Path(__file__).resolve().parents[1]/"docs"/"agent"/"v5_anticheat"/"results"/"V5_AFFINE_ORDER_UPDATE_CONDITIONING_DIAGNOSTIC_V1.json").read_text())

def test_global_ess_does_not_imply_local_ess():
    assert OBJ["global_importance_geometry"]["ess_fraction"] > 0.5
    rows={r["base_cells_per_scientific_update"]:r for r in OBJ["update_diagnostics"]}
    assert rows[128]["local_ess_fraction_min"] < 0.17
    assert rows[512]["local_ess_fraction_min"] < 0.28
    assert OBJ["scientific_order_authorized"] is False
    assert OBJ["training_authorized"] is False
    assert OBJ["inputs"]["synthetic_data_used"] is False

def test_small_updates_can_be_dominated_by_one_weighted_presentation():
    rows={r["base_cells_per_scientific_update"]:r for r in OBJ["update_diagnostics"]}
    assert rows[32]["maximum_single_presentation_weight_share"] > 0.55
    assert rows[128]["maximum_single_presentation_weight_share"] > 0.17
