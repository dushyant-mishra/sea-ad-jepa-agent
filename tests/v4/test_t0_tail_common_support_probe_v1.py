"""Step 4 must be a restriction of the frozen analysis, not a new one.

The artifact is only worth reading if the unrestricted control reproduces both
committed objects, the restriction only ever removes cells, the frozen labels
were never recomputed, and the declared outcome follows from the two frozen
results rather than from prose. All of that is tested from the published files.

The outcome-derivation test matters most. The contract declared four joint
outcomes in advance, and the value of that is lost if the reported outcome could
have been chosen after seeing the numbers. So the test recomputes which outcome
the two frozen results imply and requires the artifact to agree.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "outputs" / "t0_tail_common_support_20260910"
REPORT = PKG / "T0_TAIL_COMMON_SUPPORT_PROBE.json"
DONORS = PKG / "T0_TAIL_COMMON_SUPPORT_DONORS.csv"
CONTRACT = ROOT / "configs" / "v4" / "t0_tail_common_support_contract_v1.json"
DECISION = (ROOT / "outputs" / "t0_sensitivity_recovery_v2final_20260910"
            / "T0_V20_ADJUDICATION_DECISION.json")


def _report() -> dict:
    return json.loads(REPORT.read_text(encoding="utf-8"))


def _rows() -> list[dict[str, str]]:
    with open(DONORS, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _committed() -> dict:
    return json.loads(DECISION.read_text(encoding="utf-8"))["tail_preflight"]


def test_the_published_parts_exist() -> None:
    for path in (REPORT, DONORS, CONTRACT):
        assert path.is_file(), path


def test_the_contract_was_frozen_before_execution() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert contract["status"] == "FROZEN_BEFORE_EXECUTION"
    assert len(contract["joint_outcomes_declared_in_advance"]) == 4
    assert len(_report()["contract_sha256"]) == 64


def test_the_control_reproduces_the_committed_coherence() -> None:
    control = _report()["unrestricted"]["coherence"]
    for field, value in _committed()["support"]["coherence"].items():
        if isinstance(value, float):
            assert float(control[field]) == float(value), field
        else:
            assert int(control[field]) == int(value), field


def test_the_control_reproduces_the_committed_qc_veto() -> None:
    control = _report()["unrestricted"]["qc_veto"]
    committed = _committed()["qc"]
    assert control["max_mean_abs_standardized_qc_contrast"] == \
        committed["max_mean_abs_standardized_qc_contrast"]
    assert control["p_upper"] == committed["p_upper"]
    assert control["replicates"] == committed["replicates"]
    assert control["donors"] == committed["donors"]
    assert control["veto"] is True
    assert _report()["control_reproduces_committed_coherence_and_veto"] is True


def test_the_restriction_only_removes_cells() -> None:
    for row in _rows():
        assert int(row["tail_after"]) <= int(row["tail_before"]), row["donor_id"]
        assert int(row["rest_after"]) <= int(row["rest_before"]), row["donor_id"]
        assert int(row["tail_after"]) >= 0 and int(row["rest_after"]) >= 0


def test_the_common_support_box_is_within_donor_and_ordered() -> None:
    for row in _rows():
        assert float(row["q_depth_low"]) <= float(row["q_depth_high"])
        assert float(row["q_detect_low"]) <= float(row["q_detect_high"])
    boxes = _report()["per_donor_common_support_box"]
    assert len(boxes) == len(_rows())
    for donor, box in boxes.items():
        assert len(box["low"]) == 2 and len(box["high"]) == 2, donor


def test_the_declared_outcome_follows_from_the_frozen_results() -> None:
    """Recomputed, so the outcome cannot have been chosen after the fact."""
    report = _report()
    restricted = report["restricted"]
    capable = restricted["support_ok"]
    fires = restricted["qc_veto"]["veto"]
    coherent = restricted["coherence_ok"]
    if not capable:
        expected = "NOT_DECISION_CAPABLE_AFTER_RESTRICTION"
    elif fires:
        expected = "QC_ASSOCIATION_STILL_FIRES__RESTRICTION_INSUFFICIENT"
    elif coherent:
        expected = "CONFOUND_NOT_DETECTABLE_AND_HOLDOUT_COHERENCE_SURVIVES"
    else:
        expected = "CONFOUND_NOT_DETECTABLE_AND_HOLDOUT_COHERENCE_COLLAPSES"
    assert report["declared_outcome"] == expected


def test_both_frozen_questions_were_asked_of_the_restricted_set() -> None:
    """Without the QC recomputation the coherence result is uninterpretable."""
    restricted = _report()["restricted"]
    assert "coherence" in restricted
    assert "qc_veto" in restricted
    for field in ("max_mean_abs_standardized_qc_contrast", "p_upper", "veto"):
        assert field in restricted["qc_veto"], field


def test_the_contrast_is_reported_before_and_after() -> None:
    """The change in the confound must be visible, not asserted."""
    for row in _rows():
        for column in ("q_depth_contrast_before", "q_depth_contrast_after",
                       "q_detect_contrast_before", "q_detect_contrast_after"):
            assert "np.float64" not in row[column]
            float(row[column])


def test_the_support_minima_were_inherited_unchanged() -> None:
    minima = _report()["frozen_support_minima"]
    assert minima == {"MIN_TAIL_CELLS": 5, "MIN_REST_CELLS": 20,
                      "MIN_DECISION_DONORS": 10}
    assert _report()["support_minima_modified"] is False


def test_no_scoring_feature_entered_and_no_thinning_was_applied() -> None:
    report = _report()
    assert report["scoring_features_entering_validation"] == 0
    assert report["thinning_applied"] is False
    assert report["holdout_decision_features"] == 6146


def test_the_labels_were_never_recomputed() -> None:
    report = _report()
    assert report["tail_labels_recomputed"] is False
    assert report["frozen_tail_mask_modified"] is False
    assert report["holdout_scale_refit"] is False


def test_the_restriction_is_declared_parameter_free() -> None:
    report = _report()
    assert report["restriction_rule"] == "PER_DONOR_COMMON_SUPPORT"
    assert report["restriction_parameter_free"] is True


def test_the_scope_invariants_hold() -> None:
    report = _report()
    assert report["diagnostic_only"] is True
    assert report["frozen_tail_terminal"] == "RARE_TAIL_UNDERDETERMINED_MEASUREMENT"
    assert report["training_authorized"] is False
    for flag in ("t0_v20_modified", "frozen_target_modified",
                 "frozen_tail_mask_modified", "tail_labels_recomputed",
                 "qc_alpha_modified", "coherence_alpha_modified",
                 "support_minima_modified", "holdout_scale_refit",
                 "thinning_applied", "successor_estimator_designed",
                 "reads_at8"):
        assert report[flag] is False, flag
    assert report["pathology_blind"] is True


def test_the_limits_state_that_restriction_may_not_balance() -> None:
    limits = " ".join(_report()["interpretation_limits"]).lower()
    assert "does not guarantee balanced" in limits
    assert "must be read before any coherence result" in limits


def test_the_provenance_binds_the_authorities() -> None:
    provenance = _report()["provenance"]
    for key in ("confirmation_matrix_sha256", "discovery_matrix_sha256",
                "target_package_root_sha256", "tail_package_root_sha256",
                "feature_role_authority_sha256", "holdout_address_ids_sha256",
                "holdout_decision_mask_sha256"):
        assert len(provenance[key]) == 64, key
    assert len(provenance["donor_set"]) == 18
