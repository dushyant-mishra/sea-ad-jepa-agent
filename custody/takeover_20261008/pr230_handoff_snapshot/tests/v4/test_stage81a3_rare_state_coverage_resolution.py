from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
SCRIPT = ROOT / "scripts/v4/stage81a3_rare_state_coverage_resolution.py"
CONFIG_PATH = ROOT / "configs/v4/stage81a3_rare_state_coverage_resolution.yaml"
CONFIG = yaml.safe_load(CONFIG_PATH.read_text())
SPEC = importlib.util.spec_from_file_location("rscr", SCRIPT)
RSCR = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(RSCR)


def test_exact_target_and_fixed_metric_contract() -> None:
    assert tuple(CONFIG["target_populations"]) == RSCR.TARGETS
    assert RSCR.TARGETS == (
        "CN LAMP5-CXCL14 GABASubclass",
        "STR RSPO2 GABASubclass",
        "VipSubclass",
        "EpendymalSubclass",
    )
    assert CONFIG["fixed"]["knn_k"] == RSCR.KNN_K == 15
    assert CONFIG["fixed"]["target_cell_cap"] == 256
    assert CONFIG["fixed"]["ledger_gene_tokens"] == 4096


def test_governance_closes_forbidden_inputs_and_training() -> None:
    governance = CONFIG["governance"]
    assert governance == {
        "pathology_opened": False,
        "development_expression_accessed": False,
        "sealed_expression_accessed": False,
        "train_expression_only": True,
        "intrinsic_optimizer_updates": 0,
        "intrinsic_backward_calls": 0,
        "ema_updates": 0,
        "context_optimizer_updates": 0,
        "stage81b_started": False,
        "production_basis_frozen": False,
    }


def test_donor_balanced_sampling_is_deterministic_capped_and_unique() -> None:
    frame = pd.DataFrame({
        "annotation": np.repeat(RSCR.TARGETS, 300),
        "donor_id": np.tile(np.repeat([f"d{i}" for i in range(20)], 15), 4),
        "source_key": [f"key-{i}" for i in range(1200)],
        "dataset_id": "dataset",
        "technology": "snRNA-seq",
        "region": "brain",
    })
    first, _ = RSCR.sample_targets(frame, 256)
    second, _ = RSCR.sample_targets(frame, 256)
    assert first.source_key.tolist() == second.source_key.tolist()
    assert not first.source_key.duplicated().any()
    assert first.groupby("annotation").size().eq(256).all()
    assert first.groupby("annotation").donor_id.nunique().eq(20).all()


def test_unidentifiable_state_is_not_failed() -> None:
    rows = []
    for annotation in RSCR.TARGETS:
        for representation in RSCR.REPRESENTATIONS:
            rows.append({"annotation": annotation, "representation": representation, "identifiable": annotation != RSCR.TARGETS[0], "same_class_knn_purity": 0.8, "donor_heldout_recall": 0.8})
    decisions, proposal, _, critical = RSCR.classify(pd.DataFrame(rows))
    assert decisions.set_index("annotation").loc[RSCR.TARGETS[0], "decision"] == "NOT IDENTIFIABLE"
    assert proposal.startswith("B.")
    assert critical is False


def test_outputs_preserve_paired_cells_full_ledger_and_basis_status() -> None:
    report_path = ROOT / CONFIG["outputs"]["report"]
    if not report_path.exists():
        return
    report = json.loads(report_path.read_text())
    frame = pd.read_csv(ROOT / CONFIG["outputs"]["targeted_preservation"])
    assert frame.groupby("annotation").paired_target_cell_hash.nunique().eq(1).all()
    assert frame.groupby("annotation").paired_reference_cell_hash.nunique().eq(1).all()
    assert frame.groupby("annotation").n_target_cells.nunique().eq(1).all()
    assert (frame.loc[frame.representation.str.contains("LEDGER"), "ledger_gene_tokens_used"] == 4096).all()
    assert not frame.loc[frame.representation.str.contains("LEDGER"), "learned_ledger_pooling_used"].astype(bool).any()
    assert frame.loc[frame.representation.eq("BALANCED_PCA160"), "production_basis_status"].eq("NOT PRODUCTION FROZEN BASIS").all()
    assert frame.loc[frame.representation.str.contains("REP160"), "production_basis_status"].str.startswith("DIAGNOSTIC CONTROL").all()
    assert report["molecular_ledger"]["parameter_hash_before"] == report["molecular_ledger"]["parameter_hash_after"]
    assert report["governance"]["intrinsic_optimizer_updates"] == 0
    assert report["governance"]["context_optimizer_updates"] == 0


def test_script_contains_no_pathology_sampling_or_training_operations() -> None:
    text = SCRIPT.read_text().lower()
    assert "optimizer.step" not in text
    assert ".backward(" not in text
    assert "stage81b" in text
    assert "pathology_blind" in text
    assert "plaque" not in text
    assert "braak" not in text
