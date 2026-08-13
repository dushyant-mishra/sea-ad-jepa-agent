from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from sea_ad_jepa.v4.rare_state_audit import transfer_coverage, transfer_performance


def test_unidentifiable_units_are_not_performance_failures() -> None:
    assert transfer_performance([float("nan")], [float("nan")]) == "NOT-IDENTIFIABLE"


def test_transfer_performance_and_coverage_are_separate() -> None:
    assert transfer_performance([0.81, 0.90], [0.82, 0.91]) == "STRONG"
    assert transfer_coverage(2, 10) == "SPARSE"


def test_transfer_thresholds_are_exact() -> None:
    assert transfer_performance([0.80], [0.80]) == "STRONG"
    assert transfer_performance([0.60], [0.79]) == "MODERATE"
    assert transfer_coverage(3, 4) == "BROAD"
    assert transfer_coverage(1, 4) == "PARTIAL"
