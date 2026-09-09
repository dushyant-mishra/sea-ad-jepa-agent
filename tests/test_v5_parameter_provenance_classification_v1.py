import json
from pathlib import Path

OBJ=json.loads((Path(__file__).resolve().parents[1]/"docs"/"agent"/"V5_PARAMETER_PROVENANCE_AND_DERIVATION_CLASSIFICATION_V1.json").read_text())

def test_old_pilot_numbers_are_not_promoted():
    h=OBJ["historical_values_not_production_authority"]
    for key in [
        "D_shared_5","latent_width_96","d_gene_160","D_global_224","search_rank_320",
        "feature_sketch_dimension_512","donor_resamples_256","matched_null_replicates_256",
        "visible_fraction_0_6","triplets_per_stratum_64","group_presentation_floor_16",
        "importance_weight_ratio_64"
    ]:
        assert key in h

def test_real_hardware_and_risk_controls_are_separated():
    assert "D_shared, D_private, D_total, D_obs" in OBJ["classes"]["REAL_DATA_DERIVED"]["variables"]
    assert "maximum tokens per microbatch" in OBJ["classes"]["HARDWARE_DERIVED_BEFORE_TRAINING"]["variables"]
    assert OBJ["synthetic_data_may_set_production_values"] is False
    assert OBJ["training_authorized"] is False
