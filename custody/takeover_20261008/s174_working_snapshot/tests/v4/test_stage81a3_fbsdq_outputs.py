from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "v4"))

from stage81a3_foundation_biological_state_domain_qualification import cleanup_audit_cache

CONFIG = yaml.safe_load((ROOT / "configs/v4/stage81a3_foundation_biological_state_domain_qualification.yaml").read_text())
REPORT = json.loads((ROOT / CONFIG["outputs"]["report"]).read_text())


def read_output(name: str) -> pd.DataFrame:
    return pd.read_csv(ROOT / CONFIG["outputs"][name])


def test_governance_and_primary_result_are_conservative() -> None:
    assert REPORT["all_hard_gates_pass"] is True
    assert REPORT["stage81a3_complete"] is False
    assert REPORT["stage81a3_frozen"] is False
    assert REPORT["ready_for_stage81b"] is False
    assert REPORT["ready_for_human_a3_freeze_review"] is False
    assert REPORT["classifications"]["primary"].startswith("B.")


@pytest.mark.parametrize("name,expected", [
    ("neural_optimizer_updates", 0), ("backward_calls_on_real_rna", 0), ("ema_updates", 0),
    ("development_expression_forbidden", True), ("sealed_expression_forbidden", True),
    ("pathology_blind", True), ("stage81b_started", False), ("production_basis_frozen", False),
])
def test_fixed_governance_contract(name: str, expected: object) -> None:
    assert CONFIG["governance"][name] == expected


@pytest.mark.parametrize("name,expected", [
    ("cells_per_matrix_cap", 2048), ("dimensions", 160), ("donor_folds", 8),
    ("relative_eigengap_threshold", 0.01), ("axis_median_correlation_threshold", 0.90),
    ("axis_p10_correlation_threshold", 0.80), ("subspace_median_correlation_threshold", 0.90),
])
def test_fixed_basis_contract(name: str, expected: float) -> None:
    assert CONFIG["basis"][name] == expected


def test_basis_sample_and_vocabulary_contract() -> None:
    sample = REPORT["basis_fit_sample"]
    assert len(sample["per_matrix"]) == 36
    assert max(sample["per_matrix"].values()) <= 2048
    assert sample["donor_balanced"] is True
    assert REPORT["vocabulary"] == 4096
    assert REPORT["molecular_ledger_contract"] == "PRESERVED"


@pytest.mark.parametrize("basis_key", ["BALANCED_PCA160", "BALANCED_REP160"])
def test_candidate_basis_is_160d_and_not_frozen(basis_key: str) -> None:
    artifact = REPORT["basis_artifacts"][basis_key]
    assert artifact["status"] == "NOT PRODUCTION FROZEN BASIS"
    with np.load(ROOT / artifact["path"], allow_pickle=False) as data:
        assert data["components"].shape == (4096, 160)
        assert data["eigenvalues"].shape == (160,)
        assert data["artifact_status"].item() == "NOT PRODUCTION FROZEN BASIS"


def test_rep_complexity_gate_is_applied_exactly() -> None:
    gate = REPORT["rep_complexity_gate"]
    assert gate["relative_distance_improvement"] < 0.05
    assert gate["favorable_matrix_fraction"] >= 0.70
    assert gate["dataset_transfer_degradation"] <= 0.02
    assert gate["technology_imprint_worsening"] <= 0.02
    assert gate["earned"] is False


def test_countsplit_rows_cover_every_matrix_and_basis() -> None:
    frame = read_output("countsplit_reproducibility")
    assert len(frame) == 72
    assert frame.matrix_id.nunique() == 36
    assert set(frame.basis) == {"BALANCED_PCA160", "BALANCED_REP160"}


def test_transfer_holdouts_and_label_compatibility_are_explicit() -> None:
    donor = read_output("donor_transfer")
    matrix = read_output("matrix_transfer")
    dataset = read_output("dataset_transfer")
    technology = read_output("technology_transfer")
    assert len(donor) == 16 and donor.donor_fold.nunique() == 8
    assert len(matrix) == 72 and matrix.holdout_id.nunique() == 36
    assert len(dataset) == 26 and dataset.holdout_id.nunique() == 13
    assert len(technology) == 8 and technology.holdout_id.nunique() == 4
    assert (matrix.status == "not_identifiable_incompatible_label_vocabularies").sum() == 52


def test_evidence_and_depth_curves_use_fixed_levels() -> None:
    evidence = read_output("evidence_response")
    depth = read_output("depth_response")
    assert set(evidence.visible_fraction.round(2)) == {0.2, 0.4, 0.6, 0.8, 1.0}
    assert set(evidence.sequence) == {0, 1, 2, 3}
    assert set(depth.depth_fraction.round(2)) == {0.25, 0.5, 0.75, 1.0}


def test_coordinate_accountability_covers_both_160d_bases() -> None:
    frame = read_output("coordinate_accountability")
    assert len(frame) == 320
    assert frame.groupby("basis").coordinate.nunique().eq(160).all()
    for name in ("countsplit_reliability", "biological_evidence_response_auc", "measurement_depth_response_auc", "technology_eta_squared", "donor_id_eta_squared"):
        assert name in frame.columns


def test_provenance_identifiers_never_enter_model_streams() -> None:
    policy = read_output("observation_input_policy").set_index("descriptor").classification
    for name in ("dataset_id", "matrix_id", "donor_id", "sample_id", "specimen_id"):
        assert policy[name] == "PROVENANCE ONLY"
    assert policy["measurement_mask"] == "REQUIRED MEASUREMENT-STREAM INPUT"


def test_readout_has_one_current_fbsdq_section() -> None:
    text = (ROOT / "docs/v4/STAGE81A3_CALIBRATION_AND_SYNTHETIC_MECHANICS_READOUT.md").read_text()
    assert text.count("## Foundation Biological State, Observation Process, Uncertainty Decomposition And Domain Transfer Qualification") == 1
    assert "Specific Pre-Freeze Contract Revision Required".upper() in text.upper()


def test_cleanup_removes_only_dedicated_regular_file_cache(tmp_path: Path) -> None:
    cache = tmp_path / "stage81a3_fbsdq"
    cache.mkdir()
    (cache / "fold_basis.npz").write_bytes(b"temporary")
    cleanup_audit_cache(cache)
    assert not cache.exists()


def test_cleanup_rejects_unexpected_nested_cache_entry(tmp_path: Path) -> None:
    cache = tmp_path / "stage81a3_fbsdq"
    (cache / "unexpected").mkdir(parents=True)
    with pytest.raises(RuntimeError, match="unexpected cache entry"):
        cleanup_audit_cache(cache)
    assert (cache / "unexpected").is_dir()
