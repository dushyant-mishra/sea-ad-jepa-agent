"""The depth-thinning probe must be a measurement, not a moving target.

The probe's whole value rests on two things being true: that it reproduces the
frozen classification when it is told not to perturb anything, and that what it
publishes is readable by someone who did not run it. Both are tested here from
the artifacts rather than from claims the report makes about itself.

The float-parseability tests are regression tests for a defect this artifact
actually had. Under numpy 2.x `repr(np.float64(x))` renders as
`np.float64(...)`, so two columns of the cell CSV were published in a form no
CSV reader could parse as a number -- a machine-readable file that was not
machine-readable.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "outputs" / "t0_tail_depth_thinning_20260910"
REPORT = PKG / "T0_TAIL_DEPTH_THINNING_PROBE.json"
CELLS = PKG / "T0_TAIL_DEPTH_THINNING_CELLS.csv"
LEVELS = PKG / "T0_TAIL_DEPTH_THINNING_LEVELS.csv"
CONTRACT = ROOT / "configs" / "v4" / "t0_tail_depth_thinning_contract_v1.json"


def _report() -> dict:
    return json.loads(REPORT.read_text(encoding="utf-8"))


def _contract() -> dict:
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def _rows(path: Path) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_the_published_parts_exist() -> None:
    for path in (REPORT, CELLS, LEVELS, CONTRACT):
        assert path.is_file(), path


def test_the_contract_was_frozen_before_execution() -> None:
    contract = _contract()
    assert contract["status"] == "FROZEN_BEFORE_EXECUTION"
    report = _report()
    assert report["retention_levels"] == contract["retention_levels"]
    assert report["draws_per_level"] == contract["draws_per_level"]


def test_the_control_level_perturbs_nothing() -> None:
    """The frozen acceptance check, verified from the published rows.

    A harness that moves the cell when asked not to cannot measure what moving
    it does, so this is the test the rest of the probe depends on.
    """
    controls = [r for r in _report()["per_level"] if r["retention"] == 1.0]
    assert len(controls) == _contract()["draws_per_level"]
    for row in controls:
        assert row["mean_abs_displacement"] == 0.0
        assert row["median_abs_displacement"] == 0.0
        assert row["p95_abs_displacement"] == 0.0
        assert row["tail_to_rest_flips"] == 0
        assert row["rest_to_tail_flips"] == 0
        assert row["original_tail_cells"] == row["thinned_tail_cells"]
        assert row["mean_within_donor_spearman"] == pytest.approx(1.0)
        assert row["mean_q_detect_before"] == row["mean_q_detect_after"]
        assert row["mean_q_depth_before"] == row["mean_q_depth_after"]


def test_the_baseline_reproduced_the_frozen_tail_mask() -> None:
    assert _report()["baseline_reproduced_the_frozen_tail_mask"] is True
    assert _report()["control_level_reproduced_exactly"] is True


def test_every_level_and_draw_was_executed() -> None:
    report = _report()
    expected = len(report["retention_levels"]) * report["draws_per_level"]
    assert len(report["per_level"]) == expected
    assert len(_rows(LEVELS)) == expected
    seen = {(r["retention"], r["draw"]) for r in report["per_level"]}
    assert len(seen) == expected


def test_the_cell_csv_columns_parse_as_floats() -> None:
    """Regression: numpy 2.x reprs float64 as "np.float64(...)"."""
    rows = _rows(CELLS)
    assert rows
    for column in ("baseline_centered", "thinned_centered",
                   "signed_displacement"):
        for row in rows[:200]:
            value = row[column]
            assert "np.float64" not in value, (column, value)
            float(value)


def test_the_level_csv_columns_parse_as_floats() -> None:
    for row in _rows(LEVELS):
        for column in ("mean_abs_displacement", "median_abs_displacement",
                       "mean_within_donor_spearman"):
            assert "np.float64" not in row[column], (column, row[column])
            float(row[column])


def test_the_signed_displacement_is_the_difference_it_claims() -> None:
    """Rebuilt from the two score columns rather than trusted."""
    for row in _rows(CELLS)[:500]:
        expected = float(row["thinned_centered"]) - float(row["baseline_centered"])
        assert float(row["signed_displacement"]) == pytest.approx(
            expected, rel=0, abs=1e-12)


def test_the_control_rows_in_the_cell_csv_show_no_movement() -> None:
    control = [r for r in _rows(CELLS) if r["retention"] == "1.0"]
    assert control, "the control level must appear in the cell CSV"
    for row in control:
        assert float(row["signed_displacement"]) == 0.0
        assert row["baseline_tail"] == row["thinned_tail"]


def test_thinning_reduced_the_measured_depth_where_it_should() -> None:
    """Confirms the intervention did what it claims, per level."""
    for row in _report()["per_level"]:
        if row["retention"] == 1.0:
            continue
        assert row["mean_q_detect_after"] < row["mean_q_detect_before"]
        assert row["mean_q_depth_after"] < row["mean_q_depth_before"]


def test_flip_rates_are_consistent_with_their_counts() -> None:
    for row in _report()["per_level"]:
        original = row["original_tail_cells"]
        if original:
            assert row["tail_to_rest_flip_rate"] == pytest.approx(
                row["tail_to_rest_flips"] / original)
        assert row["net_tail_change"] == (row["thinned_tail_cells"]
                                          - row["original_tail_cells"])
        assert row["thinned_tail_cells"] == (
            original - row["tail_to_rest_flips"] + row["rest_to_tail_flips"])


def test_the_donor_and_cell_counts_are_stable() -> None:
    report = _report()
    assert report["donors"] == 18
    counts = {r["cells"] for r in report["per_level"]}
    assert len(counts) == 1, counts


def test_the_scope_invariants_hold() -> None:
    report = _report()
    assert report["diagnostic_only"] is True
    assert report["frozen_tail_terminal"] == "RARE_TAIL_UNDERDETERMINED_MEASUREMENT"
    assert report["training_authorized"] is False
    for flag in ("t0_v20_modified", "frozen_qc_gate_modified",
                 "qc_alpha_modified", "tail_definition_modified",
                 "tail_rule_or_threshold_modified",
                 "remediation_designed_or_tested", "reads_at8"):
        assert report[flag] is False, flag
    assert report["pathology_blind"] is True


def test_the_interpretation_limits_travel_with_the_numbers() -> None:
    """A flip rate without its limits invites the causal reading it cannot support."""
    limits = " ".join(_report()["interpretation_limits"]).lower()
    assert "does not by itself establish" in limits
    assert "correlated" in limits
    assert "no p-value or gate" in limits
