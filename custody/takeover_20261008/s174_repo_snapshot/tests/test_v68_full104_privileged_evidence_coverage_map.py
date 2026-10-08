import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"results/v64/V68_FULL104_PRIVILEGED_EVIDENCE_COVERAGE_MAP_V1.json"

def load():
    return json.loads(P.read_text())

def test_full104_backbone_counts_are_frozen():
    c=load()["full104_backbone"]
    assert c["reader_fit_cells"]==4553407
    assert c["donors"]==104
    assert c["canonical_addresses"]==41238
    assert sum(c["source_cells"].values())==4553407

def test_stage4_is_not_misreported_as_full104_cell_fraction():
    s=load()["evidence_layers"]["stage4_nihcard"]
    assert s["direct_measurement"]["microglia"]==84129
    assert "not a numerator for FULL104 cell coverage" in s["transport_interpretation"]
    assert s["current_limit"].startswith("Stage 4 remains unopened")

def test_morabito_coverage_is_feature_not_cell_coverage():
    m=load()["evidence_layers"]["morabito_crosswalk"]
    assert m["canonical_addresses_resolved"]==41238
    assert m["donor_level_rna_atac_eligible_addresses"]==37966
    assert 0.92 < m["eligible_fraction"] < 0.93
    assert "does not mean 92% of FULL104 cells" in m["interpretation"]

def test_scenicplus_current_broad_coverage_is_unknown():
    s=load()["evidence_layers"]["scenic_plus"]
    assert s["current_qualified_broad_network"] is False
    assert s["historical_stage75f"]["validated_eregulon_network"] is False
    assert s["coverage_status"].startswith("NOT_YET_QUANTIFIABLE")

def test_perturbation_and_spatial_are_not_promoted_to_global_coverage():
    c=load()["evidence_layers"]
    assert "NO_VALID_GLOBAL_FULL104_PERCENTAGE" in c["perturbation"]["coverage_status"]
    assert "NO_VALID_WHOLE_FULL104_STATE_COVERAGE_PERCENTAGE" in c["spatial"]["coverage_status"]

def test_prediction_and_direct_measurement_are_distinguished():
    rules=" ".join(load()["reporting_rules"])
    assert "direct multimodal cell coverage separately" in rules
    assert "predicted from directly measured support" in rules

def test_governance_remains_sealed():
    g=load()["governance"]
    assert g["stage4"]=="NOT_AUTHORIZED"
    assert g["correspondence"]=="UNOPENED"
    assert g["training"]=="OFF"
    assert g["recoverability_TEST"]=="SEALED"
