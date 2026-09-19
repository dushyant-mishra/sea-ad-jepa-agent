from __future__ import annotations

import sys

import pytest

from scripts.agent import evaluate_full104_target_panel_capacity_from_cache_v1 as evaluator


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
