"""The decomposition must rebuild the frozen max statistic exactly.

A decomposition is only worth reading if its parts reassemble into the statistic
they claim to decompose. These tests do that reassembly from the published
components -- the per-donor CSV and the per-replicate CSV -- rather than from any
value the report asserts about itself, and they check the result against the
digest-bound QC record in the committed adjudication decision.

They are cheap by construction: nothing here re-runs the 999-replicate null. The
point is that the published parts are sufficient to reconstruct the whole, which
is what makes the artifact checkable by someone who did not run it.

Scope invariants are tested too. The diagnostic must not have moved the tail
terminal, touched the tail mask, or acquired training authority, and a report
that quietly did any of those would still look like a decomposition.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "outputs" / "t0_tail_qc_decomposition_20260910"
REPORT = PKG / "T0_TAIL_QC_METRIC_DECOMPOSITION.json"
DONORS = PKG / "T0_TAIL_QC_DONOR_COMPONENTS.csv"
REPLICATES = PKG / "T0_TAIL_QC_REPLICATE_COMPONENTS.csv"

CONFIRMATION = (ROOT / "outputs" / "t0_sensitivity_recovery_v2final_20260910"
                / "T0_V20_ADJUDICATION_DECISION.json")

METRICS = ("Q_DEPTH", "Q_DETECT")


def _report() -> dict:
    return json.loads(REPORT.read_text(encoding="utf-8"))


def _rows(path: Path) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _committed_qc() -> dict:
    decision = json.loads(CONFIRMATION.read_text(encoding="utf-8"))
    return decision["tail_preflight"]["qc"]


def test_the_published_parts_exist() -> None:
    """Without all three the artifact is not independently checkable."""
    for path in (REPORT, DONORS, REPLICATES):
        assert path.is_file(), path


def test_the_donor_components_reconstruct_the_observed_components() -> None:
    """Mean across donors of the absolute contrast, rebuilt from the CSV."""
    rows = _rows(DONORS)
    report = _report()
    depth = np.array([float(r["q_depth_abs"]) for r in rows])
    detect = np.array([float(r["q_detect_abs"]) for r in rows])
    rebuilt = {"Q_DEPTH": depth.mean(), "Q_DETECT": detect.mean()}
    for entry in report["per_metric"]:
        published = float(entry["observed_mean_abs_standardized_contrast"])
        assert rebuilt[entry["metric"]] == pytest.approx(published, rel=0,
                                                         abs=1e-15), entry["metric"]


def test_the_absolute_columns_are_the_absolute_of_the_signed() -> None:
    for row in _rows(DONORS):
        for metric in ("q_depth", "q_detect"):
            assert abs(float(row["%s_signed" % metric])) == \
                float(row["%s_abs" % metric]), (row["donor_id"], metric)


def test_the_replicate_max_is_the_max_of_the_two_components() -> None:
    """T_max[r] = max(T_depth[r], T_detect[r]) for every replicate."""
    for row in _rows(REPLICATES):
        depth = float(row["t_depth"])
        detect = float(row["t_detect"])
        assert float(row["t_max"]) == max(depth, detect), row["replicate"]
        expected = METRICS[0] if depth >= detect else METRICS[1]
        if depth != detect:
            assert row["argmax_metric"] == expected, row["replicate"]


def test_the_replicates_reconstruct_the_frozen_exceedance_count_and_p() -> None:
    """The regression check, rebuilt from the published null components."""
    report = _report()
    regression = report["frozen_max_statistic_regression"]
    statistic = float(regression["observed_max_statistic"])
    rows = _rows(REPLICATES)
    assert len(rows) == regression["replicates"]

    null_max = np.array([float(r["t_max"]) for r in rows])
    tolerance = 1e-15 * max(1.0, abs(statistic))
    ge = int(np.sum(null_max >= statistic - tolerance))
    assert ge == regression["ge"], (ge, regression["ge"])

    p_upper = (1 + ge) / (len(rows) + 1)
    assert p_upper == pytest.approx(regression["p_upper"], rel=0, abs=1e-15)


def test_the_reconstruction_matches_the_committed_qc_record() -> None:
    """The whole point: this decomposes the veto, not a lookalike."""
    report = _report()
    regression = report["frozen_max_statistic_regression"]
    committed = _committed_qc()
    assert regression["observed_max_statistic"] == \
        committed["max_mean_abs_standardized_qc_contrast"]
    assert regression["p_upper"] == committed["p_upper"]
    assert regression["replicates"] == committed["replicates"]
    assert regression["veto"] is True and committed["veto"] is True
    assert regression["reproduces_frozen_record_exactly"] is True


def test_exactly_one_component_attains_the_maximum() -> None:
    report = _report()
    attaining = [c["metric"] for c in report["per_metric"]
                 if c["attains_frozen_maximum"]]
    assert len(attaining) == 1, attaining
    assert report["larger_component"] == attaining[0]
    statistic = float(
        report["frozen_max_statistic_regression"]["observed_max_statistic"])
    values = [float(c["observed_mean_abs_standardized_contrast"])
              for c in report["per_metric"]]
    assert max(values) == statistic


def test_the_component_p_values_are_labelled_non_authoritative() -> None:
    """They must not be readable as gates."""
    for entry in _report()["per_metric"]:
        assert "component_descriptive_p_upper" in entry
        assert "non-authoritative" in entry["caveat"].lower()
        assert "not a p-value gate" in entry["caveat"].lower()


def test_the_argmax_counts_account_for_every_replicate() -> None:
    stability = _report()["null_argmax_stability"]
    assert sum(stability["null_argmax_counts"].values()) == \
        stability["replicates"]
    assert set(stability["null_argmax_counts"]) == set(METRICS)


def test_the_leave_one_donor_out_covers_every_donor() -> None:
    report = _report()
    loo = report["leave_one_donor_out"]
    assert len(loo["per_held_out_donor"]) == len(report["per_donor"])
    held = {r["held_out_donor"] for r in loo["per_held_out_donor"]}
    assert held == {r["donor_id"] for r in report["per_donor"]}
    flips = loo["donors_whose_removal_flips_the_larger_component"]
    assert loo["larger_component_is_stable_to_single_donor_removal"] == (not flips)


def test_the_donor_count_matches_the_committed_veto() -> None:
    report = _report()
    assert len(report["per_donor"]) == _committed_qc()["donors"]


def test_the_scope_invariants_hold() -> None:
    """A report that had moved the tail would still look like a decomposition."""
    report = _report()
    assert report["diagnostic_only"] is True
    assert report["frozen_tail_terminal"] == "RARE_TAIL_UNDERDETERMINED_MEASUREMENT"
    assert report["training_authorized"] is False
    for flag in ("t0_v20_modified", "frozen_qc_gate_modified",
                 "qc_alpha_modified", "tail_definition_modified",
                 "tail_mask_recalculated", "remediation_designed_or_tested",
                 "reads_at8"):
        assert report[flag] is False, flag
    assert report["pathology_blind"] is True


def test_the_correlation_caveat_is_present() -> None:
    """The larger component must not be presented as a causal mechanism."""
    caveat = _report()["correlated_components_caveat"].lower()
    assert "correlated" in caveat
    assert "not evidence of a unique causal mechanism" in caveat


def test_provenance_binds_the_inputs() -> None:
    provenance = _report()["provenance"]
    for key in ("confirmation_matrix_sha256", "target_package_root_sha256",
                "tail_package_root_sha256", "tail_threshold"):
        assert provenance[key] is not None, key
    assert len(provenance["confirmation_matrix_sha256"]) == 64
    for key in ("membership", "feature_split",
                "frozen_qc_randomization_module", "decomposition_module"):
        assert len(provenance[key]["sha256_raw_bytes"]) == 64, key
