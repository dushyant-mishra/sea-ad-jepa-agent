from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/v4/stage81a3_uniform_context_data_qualification.py"
SPEC = importlib.util.spec_from_file_location("ucdq", SCRIPT)
ucdq = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(ucdq)
CFG_PATH = ROOT / "configs/v4/stage81a3_uniform_context_data_qualification.yaml"
CFG = yaml.safe_load(CFG_PATH.read_text(encoding="utf-8"))


def test_exact_ensembl_mapping():
    out = ucdq.map_features([("ENSG1", "A")], {"ENSG1"}, {}, set())
    assert out["frozen4096_exact_ensembl_overlap"] == 1


def test_ensembl_version_stripping():
    out = ucdq.map_features([("ENSG1.12", "A")], {"ENSG1"}, {}, set())
    assert out["frozen4096_total_supported"] == 1


def test_ambiguous_symbol_rejection():
    out = ucdq.map_features([("", "AMB")], {"ENSG1"}, {}, {"AMB"})
    assert out["frozen4096_ambiguous"] == 1 and out["frozen4096_total_supported"] == 0


def test_structurally_unmeasured_is_not_zero():
    out = ucdq.map_features([], {"ENSG1"}, {}, set())
    assert out["missingness_semantics"] == "support_mask_separate_from_measured_zero"
    assert out["frozen4096_structurally_unmeasured"] == 4096


def test_duplicate_symbol_different_ensembl_not_merged():
    out = ucdq.map_features([("ENSG1", "S"), ("ENSG2", "S")], {"ENSG1", "ENSG2"}, {}, {"S"})
    assert out["frozen4096_total_supported"] == 2


def test_duplicate_rows_for_same_ensembl_are_recorded():
    out = ucdq.map_features([("ENSG1", "A"), ("ENSG1", "A")], {"ENSG1"}, {}, set())
    assert out["frozen4096_total_supported"] == 1
    assert out["frozen4096_duplicate_conflict"] == 1


def test_same_entity_pairing_calculation():
    out = ucdq.pairing_metrics(["a", "b"], ["a", "b"], 0.95)
    assert out["n_exact_matches"] == 2 and out["fraction_spatial_matched"] == 1


def test_pairing_gate_is_point_95():
    out = ucdq.pairing_metrics([str(i) for i in range(95)], [str(i) for i in range(100)], 0.95)
    assert out["pairing_class"] == "SAME_ENTITY_EXACT"


def base_role(**changes):
    row = {"spatial_entity_type": "CELL", "measurement_semantics": "RAW_UMI_COUNT", "pairing_class": "SAME_ENTITY_EXACT", "physical_geometry": True, "frozen4096_supported": 4096, "frozen4096_support_fraction": 1.0, "source_feature_count": 20000, "pathology_blind_provenance": "CLEAR_PATHOLOGY_BLIND", "exact_donors": 1, "forced_role": ""}
    row.update(changes)
    return row


def test_broad_gate_is_point_90():
    role, _ = ucdq.role_for(base_role(frozen4096_supported=3687, frozen4096_support_fraction=3687 / 4096), CFG)
    assert role == "CORE_SAME_ENTITY_BROAD_CONTEXT"


def test_high_plex_gate_is_512():
    role, _ = ucdq.role_for(base_role(source_feature_count=1000, frozen4096_supported=512, frozen4096_support_fraction=0.125), CFG)
    assert role == "CORE_CELL_RESOLVED_HIGH_PLEX_CONTEXT"


def test_targeted_gate_is_50():
    role, _ = ucdq.role_for(base_role(source_feature_count=100, frozen4096_supported=50, frozen4096_support_fraction=50 / 4096, pathology_blind_provenance="UNKNOWN"), CFG)
    assert role == "CELL_RESOLVED_TARGETED_CONTEXT"


def test_spot_cannot_qualify_as_cell_or_nucleus():
    role, _ = ucdq.role_for(base_role(spatial_entity_type="SPOT", measurement_semantics="RAW_SPOT_UMI_COUNT", exact_donors=2), CFG)
    assert role == "MULTIDONOR_SPOT_CONTEXT"


def test_normalized_matrix_cannot_be_direct_core():
    role, _ = ucdq.role_for(base_role(measurement_semantics="NORMALIZED_CONTINUOUS"), CFG)
    assert role == "UNRESOLVED"


def test_embedding_is_not_physical_context():
    assert "EMBEDDING_NOT_PHYSICAL" in CFG["coordinate_classes"]["nonphysical"]
    assert "EMBEDDING_NOT_PHYSICAL" not in CFG["coordinate_classes"]["physical"]


def test_exact_donor_identity_only_and_fuzzy_rejection():
    manifest = pd.DataFrame([{"dataset_id": "A", "sample_id": "a", "candidate_donor_id": "8667", "brain_region": "x", "technology": "t"}, {"dataset_id": "B", "sample_id": "b", "candidate_donor_id": "Br8667", "brain_region": "y", "technology": "t"}])
    graph = pd.DataFrame([{"left_dataset": "A", "left_sample": "a", "right_dataset": "B", "right_sample": "b", "exact_same_person": "False", "fuzzy_matching_used": "False"}])
    rows, _ = ucdq.union_find_groups(manifest, graph)
    assert rows[0]["canonical_person_group_id"] != rows[1]["canonical_person_group_id"]


def test_same_person_multi_region_grouping_uses_exact_edge():
    manifest = pd.DataFrame([{"dataset_id": "A", "sample_id": "a", "candidate_donor_id": "D1", "brain_region": "x", "technology": "t"}, {"dataset_id": "B", "sample_id": "b", "candidate_donor_id": "D1", "brain_region": "y", "technology": "t"}])
    graph = pd.DataFrame([{"left_dataset": "A", "left_sample": "a", "right_dataset": "B", "right_sample": "b", "exact_same_person": "True", "fuzzy_matching_used": "False"}])
    rows, _ = ucdq.union_find_groups(manifest, graph)
    assert rows[0]["canonical_person_group_id"] == rows[1]["canonical_person_group_id"]


def test_pathology_columns_are_quarantined():
    columns = ucdq.safe_columns(["donor_id", "diagnosis", "Braak score", "x"])
    assert columns == ["donor_id", "x"]


def test_identifiability_logic():
    broad = {**base_role(), "qualification_role": "CORE_SAME_ENTITY_BROAD_CONTEXT", "n_exact_matches": 1200, "technology": "Slide-tags"}
    high = {**base_role(exact_donors=4), "qualification_role": "CORE_CELL_RESOLVED_HIGH_PLEX_CONTEXT", "n_exact_matches": 1000, "technology": "MERFISH"}
    result = ucdq.identifiability([broad, high], CFG)
    assert result == {"BOUNDED_REAL_CONTEXT_VALUE_IDENTIFIABLE": "YES", "CROSS_DONOR_CONTEXT_VALUE_IDENTIFIABLE": "YES", "CROSS_TECHNOLOGY_CONTEXT_REPLICATION_IDENTIFIABLE": "YES"}


def test_no_role_threshold_adaptation():
    assert CFG["role_gates"]["CORE_SAME_ENTITY_BROAD_CONTEXT"]["min_frozen4096_support_fraction"] == 0.90
    assert CFG["role_gates"]["CORE_CELL_RESOLVED_HIGH_PLEX_CONTEXT"]["min_frozen4096_supported"] == 512
    assert CFG["pairing"]["exact_min_fraction_spatial_matched"] == 0.95


def test_contract_hash_stability():
    contract = ROOT / "results/v4/stage81a3_uniform_context_data_qualification_contract.json"
    expected = json.dumps(CFG, indent=2, sort_keys=True) + "\n"
    assert contract.read_text(encoding="utf-8") == expected
    lines = (ROOT / "results/v4/stage81a3_uniform_context_data_qualification_contract.sha256").read_text(encoding="utf-8").splitlines()
    assert lines[0].startswith(ucdq.sha256(CFG_PATH))
    assert lines[1].startswith(ucdq.sha256(contract))
