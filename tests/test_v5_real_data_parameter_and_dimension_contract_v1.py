import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REG=json.loads((ROOT/"docs"/"agent"/"v5_anticheat"/"results"/"V5_REAL_DATA_PARAMETER_REGISTRY_V1.json").read_text())
CONTRACT=json.loads((ROOT/"docs"/"agent"/"V5_DIMENSION_AND_PARAMETER_DERIVATION_CONTRACT_CANDIDATE_V1.json").read_text())

def test_real_registry_geometry_and_no_synthetic_authority():
    assert REG["inputs"]["synthetic_data_used"] is False
    assert REG["population_geometry"]["cells"]==4553407
    assert REG["population_geometry"]["donors"]==104
    assert REG["population_geometry"]["donor_operator_source_groups"]==1400
    assert REG["measurement_support_geometry"]["common_measured_all_operators"]==17186
    assert REG["donor_folds"]["derived_outer_folds"]==5
    diag=REG["population_geometry"]["groups_below_diagnostic_floor"]
    assert diag["floor"]==16
    assert diag["groups"]==192
    assert "does not create schedule or training authority" in diag["role"]

def test_D_family_cannot_reuse_historical_widths():
    assert CONTRACT["population_authority"]["sampled_or_synthetic_population_may_close_dimension_authority"] is False
    assert CONTRACT["dimension_family"]["D_shared"]["full_null_geometry_refit_required"] is True
    assert CONTRACT["dimension_family"]["D_private"]["zero_is_lawful"] is True
    assert CONTRACT["dimension_family"]["d_gene"]["historical_160_is_authority"] is False
    assert CONTRACT["dimension_family"]["candidate_search_rank"]["historical_320_is_authority"] is False
    assert CONTRACT["historical_non_authority_guard"]["historical_96"]=="NOT_AUTHORITY"
    assert CONTRACT["training_authorized"] is False
