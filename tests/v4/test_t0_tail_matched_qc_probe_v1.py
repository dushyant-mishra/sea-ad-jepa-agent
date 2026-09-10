"""Matched-QC step 4: the acceptance checks, and the control that saves it.

Most of these verify the contract's own acceptance conditions from the published
artifact. The important ones are the last group, covering the two corrections.

The size-matched control is what makes the headline number interpretable. The
matched coherence collapses to roughly zero, and without a control that would
read as "the held-out program was the QC confound". The control shows a design
that *retains* the confound gives the same roughly-zero value at the same sample
size, so the collapse is a power effect and no inference about confounding is
available. A test therefore asserts the control exists, is populated, and is
reported alongside the matched value — because publishing the matched value
without it would be publishing a misleading result.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "outputs" / "t0_tail_matched_qc_20260910"
REPORT = PKG / "T0_TAIL_MATCHED_QC_PROBE.json"
DONORS = PKG / "T0_TAIL_MATCHED_QC_DONORS.csv"
PAIRS = PKG / "T0_TAIL_MATCHED_QC_PAIRS.csv"
CONTRACT = ROOT / "configs" / "v4" / "t0_tail_matched_qc_contract_v1.json"


def _report() -> dict:
    return json.loads(REPORT.read_text(encoding="utf-8"))


def _rows(path: Path) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_the_published_parts_exist() -> None:
    for path in (REPORT, DONORS, PAIRS, CONTRACT):
        assert path.is_file(), path


def test_the_contract_is_the_owners_and_frozen() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert contract["status"] == "FROZEN_BEFORE_EXECUTION"
    assert contract["schema"] == "JEPA_T0_TAIL_MATCHED_QC_CONTRACT_V1"
    assert len(_report()["contract_sha256"]) == 64


def test_the_eligibility_minima_are_the_frozen_ones() -> None:
    report = _report()
    assert report["minimum_matched_pairs"] == 5
    assert report["minimum_decision_donors"] == 10


def test_one_to_one_no_replacement_within_each_donor() -> None:
    by_donor: dict[str, list[tuple[str, str]]] = {}
    for row in _rows(PAIRS):
        by_donor.setdefault(row["donor_id"], []).append(
            (row["tail_stable_key"], row["rest_stable_key"]))
    for donor, pairs in by_donor.items():
        tails = [p[0] for p in pairs]
        rests = [p[1] for p in pairs]
        assert len(set(tails)) == len(tails), donor
        assert len(set(rests)) == len(rests), donor
        assert not set(tails) & set(rests), donor


def test_the_pair_count_equals_the_minimum_group_count() -> None:
    for row in _rows(DONORS):
        expected = min(int(row["tail_common_support"]),
                       int(row["rest_common_support"]))
        assert int(row["matched_pairs"]) == expected, row["donor_id"]


def test_every_pair_distance_is_published_and_finite() -> None:
    rows = _rows(PAIRS)
    assert rows
    for row in rows:
        assert "np.float64" not in row["rank_distance_squared"]
        value = float(row["rank_distance_squared"])
        assert value >= 0.0 and np.isfinite(value)


def test_common_support_retention_is_reported() -> None:
    for row in _rows(DONORS):
        assert 0.0 < float(row["tail_retained_fraction"]) <= 1.0
        assert 0.0 < float(row["rest_retained_fraction"]) <= 1.0
        assert int(row["tail_common_support"]) <= int(row["tail_total"])
        assert int(row["rest_common_support"]) <= int(row["rest_total"])


def test_no_scoring_feature_entered_and_no_caliper_was_used() -> None:
    report = _report()
    assert report["scoring_features_entering_validation"] == 0
    assert report["holdout_decision_features"] == 6146
    assert report["caliper_used"] is False
    assert report["balance_gate_defined"] is False


def test_the_frozen_grouping_was_never_recomputed() -> None:
    report = _report()
    assert report["tail_labels_recomputed"] is False
    assert report["frozen_tail_mask_modified"] is False
    assert report["frozen_qc_veto_modified"] is False


def test_the_scope_invariants_hold() -> None:
    report = _report()
    assert report["diagnostic_only"] is True
    assert report["frozen_tail_terminal"] == "RARE_TAIL_UNDERDETERMINED_MEASUREMENT"
    assert report["training_authorized"] is False
    for flag in ("t0_v20_modified", "frozen_tail_mask_modified",
                 "tail_labels_recomputed", "frozen_qc_veto_modified",
                 "qc_alpha_modified", "frozen_target_modified",
                 "tail_threshold_modified", "successor_estimator_designed",
                 "reads_at8"):
        assert report[flag] is False, flag
    assert report["pathology_blind"] is True


# --- the two corrections ---------------------------------------------------

def test_both_corrections_are_declared_in_the_artifact() -> None:
    """Applied under standing authority, and recorded rather than silent."""
    corrections = {c["id"] for c in _report()["contract_corrections_applied"]}
    assert corrections == {"FIXED_DENOMINATOR_BALANCE",
                           "SIZE_MATCHED_UNMATCHED_CONTROL"}
    for correction in _report()["contract_corrections_applied"]:
        assert correction["contract_quantity_still_reported"] is True
        assert correction["why"]
    assert _report()["contract_prescribed_quantities_all_reported"] is True


def test_both_balance_measures_are_reported() -> None:
    """The contract's own and the comparable one."""
    for row in _rows(DONORS):
        for column in ("q_detect_smd_pre", "q_detect_smd_post",
                       "q_detect_smd_pre_fixed_denominator",
                       "q_detect_smd_post_fixed_denominator",
                       "q_depth_smd_pre_fixed_denominator",
                       "q_depth_smd_post_fixed_denominator"):
            assert "np.float64" not in row[column], column
            float(row[column])


def test_the_fixed_denominator_pre_value_equals_the_frozen_pre_value() -> None:
    """They must agree, since the fixed denominator IS the pre-match spread.

    If they disagreed, the correction would be measuring something other than
    the quantity it is meant to make comparable.
    """
    for row in _rows(DONORS):
        for metric in ("q_depth", "q_detect"):
            frozen = float(row["%s_smd_pre" % metric])
            fixed = float(row["%s_smd_pre_fixed_denominator" % metric])
            assert abs(frozen - fixed) < 1e-9, (row["donor_id"], metric)


def test_the_size_matched_control_is_present_and_populated() -> None:
    """Without it the matched coherence would be a misleading headline."""
    control = _report()["size_matched_control"]
    assert control is not None
    assert control["replicates"] >= 10
    assert control["min"] <= control["mean"] <= control["max"]
    assert "matched_inside_control_range" in control
    assert control["what_it_isolates"]


def test_the_matched_value_is_compared_against_the_control() -> None:
    report = _report()
    control = report["size_matched_control"]
    observed = report["matched_coherence"]["mean_pairwise_cosine"]
    assert control["matched_observed"] == observed
    inside = control["min"] <= observed <= control["max"]
    assert control["matched_inside_control_range"] == inside


def test_the_limits_forbid_choosing_a_method_after_the_result() -> None:
    limits = " ".join(_report()["interpretation_limits"]).lower()
    assert "do not choose a balance threshold" in limits
    assert "cannot rescue the frozen rare-tail terminal" in limits
