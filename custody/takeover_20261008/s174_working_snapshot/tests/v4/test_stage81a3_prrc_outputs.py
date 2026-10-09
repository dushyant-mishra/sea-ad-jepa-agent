from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
CONFIG = yaml.safe_load((ROOT / "configs/v4/stage81a3_preref_resolution_rare_context.yaml").read_text())
REPORT = json.loads((ROOT / CONFIG["outputs"]["report"]).read_text())


def test_governance_and_hard_gates() -> None:
    assert all(REPORT["hard_gates"].values())
    assert REPORT["governance"]["pathology_opened"] is False
    assert REPORT["governance"]["development_expression_accessed"] is False
    assert REPORT["governance"]["sealed_expression_accessed"] is False
    assert REPORT["governance"]["intrinsic_optimizer_updates"] == 0
    assert REPORT["governance"]["context_optimizer_updates"] == 0


def test_transfer_taxonomy_is_separated() -> None:
    matrix = REPORT["transfer_taxonomy"]["matrix"]
    assert matrix["performance_where_identifiable"] == "STRONG"
    assert matrix["identifiability_coverage"] == "PARTIAL"
    assert matrix["identifiable_units"] == 10 and matrix["total_units"] == 36


def test_qc_repair_uses_fixed_contract_and_earns_measurement_stream() -> None:
    assert REPORT["qc"]["classification"] == "EARNED"
    frame = pd.read_csv(ROOT / CONFIG["outputs"]["qc"])
    assert len(frame) == 36
    assert set(("process_base_mae", "process_plus_quality_mae", "relative_mae_improvement", "process_plus_quality_spearman")) <= set(frame)


def test_rare_comparisons_use_one_paired_sample() -> None:
    frame = pd.read_csv(ROOT / CONFIG["outputs"]["rare_preservation"])
    assert frame.paired_representation_sample.astype(bool).all()
    assert frame.groupby("annotation").n_evaluated_cells.nunique().eq(1).all()
    assert (frame.loc[frame.representation.str.contains("LEDGER"), "ledger_gene_tokens_used"] == 4096).all()
    rep_status = frame.loc[frame.representation.str.contains("REP160"), "production_frozen_basis"].astype(str).str.lower()
    assert rep_status.eq("false").all()


def test_real_context_probe_was_not_run_without_eligible_asset() -> None:
    assert REPORT["context_data"]["real_probe_eligible_assets"] == 0
    assert REPORT["context_data"]["context_optimizer_updates"] == 0
    assert REPORT["context_classification"].startswith("B.")


def test_stage_remains_unfrozen_and_not_stage81b() -> None:
    assert REPORT["ready_for_human_a3_freeze_review"] is False
    assert REPORT["primary_classification"].startswith("B.")
