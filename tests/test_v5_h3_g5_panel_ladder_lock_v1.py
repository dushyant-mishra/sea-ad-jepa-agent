from __future__ import annotations

import sys

import pytest

from scripts.agent import evaluate_full104_target_panel_capacity_from_cache_v1 as evaluator
from sea_ad_jepa.v5 import masking_terminal_one_rung_executor_v1 as terminal_executor


def test_h3_g5_blocker_stops_panel_ladder_before_any_file_io(monkeypatch, tmp_path):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "evaluate_full104_target_panel_capacity_from_cache_v1.py",
            "--cache-dir", str(tmp_path / "missing-cache"),
            "--parameters-authority", str(tmp_path / "missing-parameters.json"),
            "--out-dir", str(tmp_path / "out"),
            "--workers", "1",
        ],
    )
    with pytest.raises(SystemExit, match="STOP_H3_EQUIVALENCE_POWER_OPEN"):
        evaluator.main()
    assert not (tmp_path / "out").exists()


def test_terminal_executor_is_hard_stopped_before_any_full104_outcome_access():
    with pytest.raises(ValueError, match="STOP_H3_G5_TERMINAL_MASKING_UNAUTHORIZED"):
        terminal_executor._assert_terminal_scientific_design_ready()


def test_precision_and_run_contract_builders_are_locked_on_h3_g5():
    precision_source = (
        __import__("pathlib").Path(
            "scripts/agent/build_full104_precision_authority_v4_20260918.py"
        ).read_text(encoding="utf-8")
    )
    contract_source = (
        __import__("pathlib").Path(
            "scripts/agent/build_full104_masking_run_contract_v4_20260918.py"
        ).read_text(encoding="utf-8")
    )
    assert "STOP_G5_NULL_EQUIVALENCE_MARGIN_BASIS_OPEN" in precision_source
    assert "STOP_H3_G5_TERMINAL_RUN_CONTRACT_UNAUTHORIZED" in contract_source
    assert "--null-equivalence-margin-numerator" in precision_source
    assert "--null-equivalence-margin-denominator" in precision_source
