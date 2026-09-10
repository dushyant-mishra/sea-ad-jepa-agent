"""The held-out thinning probe must validate on genes that did not select.

Three things make this artifact worth anything, and all three are tested from
the published files rather than from the report's own claims: the frozen tail
grouping was held fixed, no SCORING feature entered the validation, and the
unthinned control reproduced the committed frozen coherence object exactly.

The support-count tests deserve a word. `support_ok` is True at every level, and
that carries no information: the grouping is fixed by the contract, so the tail
and rest counts cannot move. The test asserts the counts are identical across
levels precisely to confirm that reading -- if they had moved, the labels would
have been recomputed somewhere and the diagnostic would be measuring something
else.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "outputs" / "t0_tail_holdout_thinning_20260910"
REPORT = PKG / "T0_TAIL_HOLDOUT_THINNING_PROBE.json"
LEVELS = PKG / "T0_TAIL_HOLDOUT_THINNING_LEVELS.csv"
DONORS = PKG / "T0_TAIL_HOLDOUT_THINNING_DONORS.csv"
CONTRACT = ROOT / "configs" / "v4" / "t0_tail_holdout_thinning_contract_v1.json"
PARENT = ROOT / "configs" / "v4" / "t0_tail_depth_thinning_contract_v1.json"
DECISION = (ROOT / "outputs" / "t0_sensitivity_recovery_v2final_20260910"
            / "T0_V20_ADJUDICATION_DECISION.json")


def _report() -> dict:
    return json.loads(REPORT.read_text(encoding="utf-8"))


def _rows(path: Path) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _committed_coherence() -> dict:
    decision = json.loads(DECISION.read_text(encoding="utf-8"))
    return decision["tail_preflight"]["support"]["coherence"]


def test_the_published_parts_exist() -> None:
    for path in (REPORT, LEVELS, DONORS, CONTRACT, PARENT):
        assert path.is_file(), path


def test_the_contract_was_frozen_and_is_the_owners() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert contract["status"] == "FROZEN_BEFORE_EXECUTION"
    assert contract["schema"] == "JEPA_T0_TAIL_HOLDOUT_THINNING_CONTRACT_V1"
    report = _report()
    assert report["implements_contract"].endswith(
        "t0_tail_holdout_thinning_contract_v1.json")
    assert len(report["contract_sha256"]) == 64
    assert len(report["parent_contract_sha256"]) == 64


def test_the_intervention_identity_matches_the_parent_contract() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    parent = json.loads(PARENT.read_text(encoding="utf-8"))
    intervention = contract["measurement_intervention"]
    assert intervention["retention_levels"] == parent["retention_levels"]
    assert intervention["draws_per_level"] == parent["draws_per_level"]
    assert _report()["provenance"]["seed_namespace"] == \
        parent["seed_derivation"]["namespace"]


def test_the_baseline_reproduces_the_committed_coherence_object() -> None:
    """The check that makes this a diagnostic of the frozen result."""
    report = _report()
    assert report["baseline_reproduces_committed_coherence"] is True
    baseline = next(r for r in report["per_level"]
                    if r["label"] == "BASELINE_UNTHINNED")
    committed = _committed_coherence()
    for field, value in committed.items():
        observed = baseline["coherence"][field]
        if isinstance(value, float):
            assert float(observed) == float(value), field
        else:
            assert int(observed) == int(value), field


def test_the_control_level_is_exact() -> None:
    report = _report()
    assert report["control_level_exact"] is True
    baseline = next(r for r in report["per_level"]
                    if r["label"] == "BASELINE_UNTHINNED")
    controls = [r for r in report["per_level"] if r["retention"] == 1.0]
    assert len(controls) == 3
    for row in controls:
        assert row["coherence"]["mean_pairwise_cosine"] == \
            baseline["coherence"]["mean_pairwise_cosine"]
        assert row["coherence"]["p_upper_exact"] == \
            baseline["coherence"]["p_upper_exact"]
        assert row["prenormalisation_l2_norms"] == \
            baseline["prenormalisation_l2_norms"]
        assert row["mean_donor_cosine_to_unthinned"] == pytest.approx(1.0)
        assert row["min_donor_cosine_to_unthinned"] == pytest.approx(1.0)


def test_no_scoring_feature_entered_the_validation() -> None:
    """The whole point: validate on genes that did not define the grouping."""
    report = _report()
    assert report["scoring_features_entering_validation"] == 0
    assert report["holdout_addresses"] == 7015
    assert report["scoring_addresses_excluded"] == 28061
    assert report["holdout_decision_features"] == 6146


def test_the_tail_labels_were_never_recomputed() -> None:
    report = _report()
    assert report["tail_labels_recomputed_after_thinning"] is False
    assert report["frozen_tail_mask_modified"] is False
    assert report["holdout_scale_refit"] is False


def test_the_support_counts_are_identical_at_every_level() -> None:
    """Fixed grouping means they cannot move; movement would mean re-selection.

    This is also why support_ok being True everywhere carries no information.
    """
    report = _report()
    baseline = next(r for r in report["per_level"]
                    if r["label"] == "BASELINE_UNTHINNED")
    for row in report["per_level"]:
        assert row["tail_counts"] == baseline["tail_counts"], row["retention"]
        assert row["rest_counts"] == baseline["rest_counts"], row["retention"]
        assert row["donors"] == baseline["donors"], row["retention"]


def test_the_vector_builder_was_instrumented_by_exactly_one_line() -> None:
    """A second change would mean the frozen construction was not reused."""
    instrumentation = _report()["holdout_vector_builder_instrumentation"]
    assert instrumentation["changed_lines"] == 1
    assert "_prenorms.append" in instrumentation["added"]
    assert "_prenorms.append" not in instrumentation["removed"]


def test_every_level_and_draw_was_executed() -> None:
    report = _report()
    thinned = [r for r in report["per_level"] if r["label"] == "THINNED"]
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    intervention = contract["measurement_intervention"]
    expected = (len(intervention["retention_levels"])
                * intervention["draws_per_level"])
    assert len(thinned) == expected
    assert len(_rows(LEVELS)) == expected + 1  # plus the baseline row


def test_the_level_csv_agrees_with_the_report() -> None:
    report = _report()
    rows = {(r["label"], r["retention"], r["draw"]): r for r in _rows(LEVELS)}
    for entry in report["per_level"]:
        key = (entry["label"],
               "" if entry["retention"] is None else str(entry["retention"]),
               "" if entry["draw"] is None else str(entry["draw"]))
        row = rows[key]
        coherence = entry.get("coherence") or {}
        if coherence:
            assert float(row["mean_pairwise_cosine"]) == \
                pytest.approx(coherence["mean_pairwise_cosine"], rel=0,
                              abs=1e-15)
            assert float(row["p_upper_exact"]) == \
                pytest.approx(coherence["p_upper_exact"], rel=0, abs=1e-18)


def test_the_csv_numbers_parse(  ) -> None:
    """Regression for the numpy 2.x repr defect found in step 2."""
    for row in _rows(LEVELS):
        for column in ("mean_pairwise_cosine", "p_upper_exact"):
            if row[column]:
                assert "np.float64" not in row[column]
                float(row[column])
    for row in _rows(DONORS):
        assert "np.float64" not in row["prenormalisation_l2_norm"]
        float(row["prenormalisation_l2_norm"])


def test_the_donor_csv_covers_every_donor_at_every_level() -> None:
    report = _report()
    donors = len(report["per_level"][0]["donors"])
    rows = _rows(DONORS)
    assert len(rows) == donors * len(report["per_level"])


def test_the_provenance_binds_the_authorities() -> None:
    provenance = _report()["provenance"]
    for key in ("confirmation_matrix_sha256", "discovery_matrix_sha256",
                "target_package_root_sha256", "tail_package_root_sha256",
                "feature_role_authority_sha256", "holdout_address_ids_sha256",
                "holdout_decision_mask_sha256", "holdout_scale_sha256",
                "frozen_tail_label_signature_sha256",
                "confirmation_cell_signature_sha256"):
        assert len(provenance[key]) == 64, key
    assert len(provenance["donor_set"]) == 18


def test_the_scope_invariants_hold() -> None:
    report = _report()
    assert report["diagnostic_only"] is True
    assert report["frozen_tail_terminal"] == "RARE_TAIL_UNDERDETERMINED_MEASUREMENT"
    assert report["training_authorized"] is False
    for flag in ("t0_v20_modified", "frozen_target_modified",
                 "frozen_tail_threshold_modified", "frozen_tail_mask_modified",
                 "qc_alpha_modified", "coherence_rule_modified",
                 "holdout_scale_refit", "remediation_designed_or_tested",
                 "matched_qc_analysis_designed", "reads_at8"):
        assert report[flag] is False, flag
    assert report["pathology_blind"] is True


def test_the_interpretation_limits_travel_with_the_numbers() -> None:
    """Above all the one that says this is not a matched-QC analysis."""
    limits = " ".join(_report()["interpretation_limits"]).lower()
    assert "not yet a common-support" in limits or "matched-qc" in limits
    assert "not proof" in limits
    assert "baseline tail/rest depth differences are not removed" in limits
