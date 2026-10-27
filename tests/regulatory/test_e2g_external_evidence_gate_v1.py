"""Hostile local tests for the non-authorizing external-E2G intake gate."""
import csv
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/regulatory/e2g_external_evidence_gate_v1.py"
spec = importlib.util.spec_from_file_location("e2g_evidence_gate", SCRIPT)
gate = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(gate)


def write_table(path, records):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)


def inputs(tmp_path):
    stage = tmp_path / "stage75.csv"
    prediction = tmp_path / "e2g.csv"
    mapping = tmp_path / "map.csv"
    rows = [{
        "tf": "SPI1", "target_gene": gene, "existing_stage75_edge": "True",
        "stage75_evidence_tier": "Tier A",
        "peak_to_gene_support": "proximity_only:promoter_proximal;peaks=1",
        "sea_ad_multiome_support": "exact_barcode_linkage_available_edge_support_not_inferred",
        "direction_evidence_type": "predicted_response_sign_from_coactivity",
        "allowed_model_role": "soft_v4b_prior_candidate_with_matched_controls",
        "prohibited_claim": "validated_grn_causal_controller_or_experimentally_established_direction",
    } for gene in ["APOE", "TREM2"]]
    write_table(stage, rows)
    write_table(mapping, [
        {"target_gene": "APOE", "target_ensembl_id": "ENSG00000000001"},
        {"target_gene": "TREM2", "target_ensembl_id": "ENSG00000000002"},
    ])
    write_table(prediction, [{
        "chrom": "chr19", "start": "100", "end": "200",
        "target_ensembl_id": "ENSG00000000001", "score": "0.81",
        "genome_build": "GRCh38", "biosample": "unverified_context",
        "source_dataset": "synthetic_test_fixture", "model_family": "scE2G",
        "model_version": "test-only", "exposure_class": "INDEPENDENCE_UNDETERMINED",
    }])
    return stage, prediction, mapping


def mutate(path, column, value):
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    rows[0][column] = value
    write_table(path, rows)


def test_stage75_only_is_read_only_and_not_established(tmp_path):
    stage, _, _ = inputs(tmp_path)
    before = gate._hash(stage)
    result = gate.audit(stage, expected_count=2)
    assert gate._hash(stage) == before
    assert result["stage75"]["candidate_tf_gene_rows"] == 2
    assert result["e2g"]["status"] == "NOT_RUN_NO_EXTERNAL_PREDICTIONS"
    assert result["e2g"]["tf_target_edge_validation_count"] is None
    assert not any(result["authority"].values())


def test_real_prediction_is_annotation_not_tf_support(tmp_path):
    stage, pred, mapping = inputs(tmp_path)
    result = gate.audit(stage, pred, mapping, expected_count=2)
    assert result["e2g"]["target_gene_annotation_overlap"] == 1
    assert result["e2g"]["candidate_tf_target_rows_with_annotated_target"] == 1
    assert result["e2g"]["tf_target_edge_validation_count"] is None
    assert result["e2g"]["status"] == "ANNOTATION_ONLY__NO_TF_EDGE_CONFIRMATION"
    assert not any(result["authority"].values())


@pytest.mark.parametrize("column,value", [
    ("genome_build", "GRCh37"), ("start", "-10"), ("end", "100"),
    ("score", "1.1"), ("model_version", ""), ("exposure_class", ""),
    ("target_ensembl_id", "APOE"), ("chrom", "chromosome19"),
    ("source_dataset", ""),
])
def test_malformed_e2g_fails_closed(tmp_path, column, value):
    stage, pred, mapping = inputs(tmp_path)
    mutate(pred, column, value)
    with pytest.raises(gate.EvidenceGateError):
        gate.audit(stage, pred, mapping, expected_count=2)


def test_duplicate_mapping_fails_closed(tmp_path):
    stage, pred, mapping = inputs(tmp_path)
    with mapping.open("a", encoding="utf-8") as f:
        f.write("APOE,ENSG00000000002\n")
    with pytest.raises(gate.EvidenceGateError):
        gate.audit(stage, pred, mapping, expected_count=2)


def test_prediction_requires_map(tmp_path):
    stage, pred, _ = inputs(tmp_path)
    with pytest.raises(gate.EvidenceGateError):
        gate.audit(stage, pred, expected_count=2)


def test_no_empty_missing_stage75_or_upgrade_of_proximity(tmp_path):
    stage, _, _ = inputs(tmp_path)
    with pytest.raises(gate.EvidenceGateError):
        gate.audit(stage, expected_count=96)
    mutate(stage, "peak_to_gene_support", "experimentally_validated:enhancer")
    with pytest.raises(gate.EvidenceGateError):
        gate.audit(stage, expected_count=2)


def test_predicted_sign_cannot_become_causal_direction(tmp_path):
    stage, _, _ = inputs(tmp_path)
    mutate(stage, "direction_evidence_type", "validated_activator")
    with pytest.raises(gate.EvidenceGateError):
        gate.audit(stage, expected_count=2)
