"""Pin Audit G's corrected equal-donor interpretation in hosted CI.

Hosted GitHub Actions cannot access the Windows-only calibration-cache directory.
Therefore hosted CI verifies:
1. the committed physical-audit summary/manifest evidence;
2. a compact content-addressed equal-donor fixture derived from that evidence;
3. the selector implementation remains expression-content blind.

Physical requalification is a separate fail-closed script executed where the
cache/pass1 files actually exist. Hosted CI never claims to have physically
re-read those bytes.

Nothing here opens terminal masking outcomes, D_shared, pathology/DEV/SEALED
data, or training.
"""
from __future__ import annotations

import inspect
import json
from pathlib import Path

from sea_ad_jepa.v5.full104_control_calibration_cache_v1 import row_priority


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / (
    "analysis/v5_full104_information_channel_redteam_20260920/evidence/audit_g/"
    "HOSTED_AUDIT_G_EQUAL_DONOR_FIXTURE_V1.json"
)
SUMMARY = ROOT / (
    "analysis/v5_full104_information_channel_redteam_20260920/evidence/audit_g/"
    "CALIBRATION_CACHE_COVERAGE_SUMMARY.json"
)
CACHE_MANIFEST = ROOT / (
    "analysis/v5_full104_pass1_rebuild_20260920/evidence/calibration_cache/"
    "cache_manifest.json"
)

SOURCE_SHARE_TOLERANCE = 0.01
COMPLEXITY_RELATIVE_TOLERANCE = 0.01
LOW_TAIL_RATIO_BAND = (0.80, 1.20)


def _load(path: Path) -> dict:
    assert path.is_file(), f"required committed evidence missing: {path}"
    return json.loads(path.read_text(encoding="utf-8"))


def test_committed_fixture_is_bound_to_current_cache_role_and_geometry():
    fx = _load(FIXTURE)
    summary = _load(SUMMARY)
    manifest = _load(CACHE_MANIFEST)

    assert fx["cache_role"] == (
        "CONTROL_CALIBRATION_ONLY__FORBIDDEN_FOR_TERMINAL_MASKING_QUALIFICATION_V1"
    )
    assert manifest["cache_role_id"] == fx["cache_role"]
    assert summary["cache_role"] == fx["cache_role"]

    assert fx["population_cells"] == summary["population_cells"] == 4_553_407
    assert fx["cached_cells"] == summary["cached_cells"] == 105_553
    assert fx["donors"] == summary["donors"] == 104
    assert fx["per_donor_cap"] == summary["per_donor_cap"] == manifest["max_rows_per_donor"] == 1024
    assert fx["donors_at_cap"] == summary["donors_at_cap"] == 103
    assert summary["donors_below_cap"] == 1
    assert summary["min_retained_per_donor"] == 81
    assert summary["max_retained_per_donor"] == 1024

    assert fx["terminal_masking_outcomes_inspected"] is False
    assert fx["training_authorized"] is False


def test_source_shares_match_equal_donor_target_not_population_marginal():
    fx = _load(FIXTURE)
    summary = _load(SUMMARY)
    by_source = {r["group"]: r for r in summary["composition"]["source"]}

    total_observed = sum(int(r["observed_rows"]) for r in fx["source_design"])
    assert total_observed == fx["cached_cells"]

    for row in fx["source_design"]:
        src = row["source"]
        observed = int(row["observed_rows"]) / total_observed
        target = float(row["equal_donor_target"])
        assert abs(observed - target) < SOURCE_SHARE_TOLERANCE
        assert int(by_source[src]["cells_cached"]) == int(row["observed_rows"])

    # The one short donor is fully retained rather than silently under-sampled.
    short = fx["short_donors"]
    assert short == [{
        "donor_code": 96, "source": "NPH52",
        "available_cells": 81, "retained_cells": 81,
    }]

    # Population marginal is explicitly not the design target.
    assert by_source["SEA_AD"]["share_full"] > 0.85
    assert by_source["SEA_AD"]["share_cached"] < 0.60


def test_complexity_shift_matches_equal_donor_expectation():
    fx = _load(FIXTURE)
    summary = _load(SUMMARY)
    c = fx["complexity"]
    observed = float(summary["coverage"]["core_nonzero_count"]["cached"]["mean"])
    expected = float(c["equal_donor_expected_mean_core_nonzeros"])

    assert abs(observed - float(c["observed_cache_mean_core_nonzeros"])) < 1e-12
    assert abs(observed - expected) / expected < COMPLEXITY_RELATIVE_TOLERANCE

    population = float(summary["coverage"]["core_nonzero_count"]["full"]["mean"])
    assert abs(population - expected) / expected > 0.10


def test_low_tail_retention_matches_equal_donor_hash_sampling_expectation():
    fx = _load(FIXTURE)
    summary = _load(SUMMARY)
    lt = fx["low_tail"]
    cov = summary["coverage"]["core_nonzero_count"]["low_tail"]

    assert int(summary["coverage"]["core_nonzero_count"]["tail_definition"]["low_threshold"]) == 438
    assert int(cov["cells_in_full"]) == int(lt["population_cells"]) == 45_655
    assert int(cov["cells_in_cache"]) == int(lt["observed_cache_cells"]) == 403

    ratio = float(lt["observed_cache_cells"]) / float(
        lt["expected_cache_cells_equal_donor_hash_sampling"]
    )
    lo, hi = LOW_TAIL_RATIO_BAND
    assert lo < ratio < hi
    assert abs(ratio - float(lt["observed_expected_ratio"])) < 1e-15


def test_within_donor_selection_is_blind_to_expression_content():
    """Static guard: selector may depend on identity, never expression content."""
    source = inspect.getsource(row_priority)
    assert "selection_row" in source and "donor_code" in source
    for forbidden in ("counts", "expression", "nnz", "library", "matrix", "value"):
        assert forbidden not in source, (
            f"row_priority now references {forbidden!r}; Audit G must be re-derived "
            "before its corrected interpretation can be inherited"
        )


def test_withdrawn_findings_remain_explicitly_withdrawn():
    fx = _load(FIXTURE)
    assert fx["audit_outcome"] == "NO_ISSUE_FOUND"
    withdrawn = set(fx["withdrawn_claims"])
    assert "G_CACHE_BIASED_TOWARD_HIGH_COMPLEXITY_CELLS" in withdrawn
    assert "G_LOW_TAIL_SUPPRESSED" in withdrawn
