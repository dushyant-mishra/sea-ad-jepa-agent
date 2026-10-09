from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from sea_ad_jepa.v4.rare_state_audit import qc_earning


def test_constant_baseline_does_not_invalidate_mae_contract() -> None:
    actual = np.array([0.0, 1.0, 2.0])
    base = np.ones(3)
    quality = np.array([0.1, 1.0, 1.9])
    base_mae = np.abs(actual - base).mean()
    quality_mae = np.abs(actual - quality).mean()
    assert (base_mae - quality_mae) / base_mae > 0


def test_qc_earning_thresholds_are_exact() -> None:
    assert qc_earning([0.10] * 7 + [-0.01] * 3, [0.50] * 10, [-0.10]) == "EARNED"
    assert qc_earning([0.099] * 10, [0.50] * 10, [0.0]) == "PARTIAL"
