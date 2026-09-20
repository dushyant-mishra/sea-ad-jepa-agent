from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from sea_ad_jepa.v5.full104_census_receipt_v2 import (
    canonical_sha,
    core_zero_crosscheck,
    eligible_targets_all_folds,
    kish_ess,
    source_stratified_fold_assignment,
)


def test_core_zero_crosscheck_uses_two_independent_pass1_views() -> None:
    per_cell = np.asarray([2, 1, 0], dtype=np.int32)
    donor_addr = np.asarray(
        [[1, 99, 1, 0], [0, 99, 0, 1]],
        dtype=np.int32,
    )
    core = np.asarray([0, 2, 3], dtype=np.int64)
    got = core_zero_crosscheck(per_cell, donor_addr, core)
    assert got["core_nonzero_sum_per_cell"] == 3
    assert got["core_nonzero_sum_donor_address"] == 3
    assert got["core_measured_zero_count"] == 6
    assert got["core_measured_zero_frequency"] == pytest.approx(2 / 3)


def test_core_zero_crosscheck_fails_on_accumulation_disagreement() -> None:
    per_cell = np.asarray([2, 1, 0], dtype=np.int32)
    donor_addr = np.asarray([[1, 0, 0], [0, 0, 1]], dtype=np.int32)
    with pytest.raises(ValueError, match="independent core-nonzero accumulations disagree"):
        core_zero_crosscheck(per_cell, donor_addr, np.asarray([0, 1, 2]))


def test_source_stratified_fold_assignment_is_deterministic_and_complete() -> None:
    source = np.asarray([0] * 8 + [1] * 6 + [2] * 10, dtype=np.int64)
    a = source_stratified_fold_assignment(
        source, n_folds=2, source_names=("A", "B", "C"), namespace="TEST"
    )
    b = source_stratified_fold_assignment(
        source, n_folds=2, source_names=("A", "B", "C"), namespace="TEST"
    )
    assert np.array_equal(a, b)
    assert set(map(int, a)) == {0, 1}
    for code in range(3):
        assert set(map(int, a[source == code])) == {0, 1}


def test_target_eligibility_requires_every_outer_fold() -> None:
    counts = np.asarray(
        [[2, 2, 0], [2, 0, 2], [2, 2, 0], [2, 0, 2]],
        dtype=np.int32,
    )
    core = np.asarray([0, 1, 2], dtype=np.int64)
    folds = np.asarray([0, 0, 1, 1], dtype=np.int64)
    eligible, per_fold = eligible_targets_all_folds(
        counts,
        core,
        folds,
        min_nonzero_cells_per_donor=1,
        min_train_donors=1,
        min_validation_donors=1,
    )
    assert tuple(per_fold) == (3, 3)
    assert np.array_equal(eligible, core)


def test_kish_ess_never_turns_cells_into_independent_donors() -> None:
    equal = np.asarray([10, 10, 10, 10], dtype=np.int64)
    skewed = np.asarray([1, 1, 1, 100], dtype=np.int64)
    assert kish_ess(equal) == pytest.approx(4.0)
    assert 1.0 < kish_ess(skewed) < 4.0


def test_census_reports_kish_only_as_descriptive_cell_count_imbalance() -> None:
    source = Path(
        "analysis/v5_full104_census_20260918/full104_readonly_census_receipts_v2.py"
    ).read_text(encoding="utf-8")
    assert '"independent_donor_units": int(donor_src.size)' in source
    assert "cell_count_weight_kish_ess_descriptive_only" in source
    assert "kish_ess_is_inferential_donor_sample_size" in source
    assert "must not be used as a donor-level power or confirmation sample size" in source
    assert "kish_ess_donor_equivalents" not in source


def test_checked_in_support_authority_matches_census_builder_semantic_root() -> None:
    support_path = Path("docs/agent/V5_SUPPORT_ESTIMABILITY_AUTHORITY_20260915.json")
    support = json.loads(support_path.read_text(encoding="utf-8"))
    assert canonical_sha(support) == (
        "cab2cecdd5ff31c2fbcaff408e1b1b7548eb2f72c1d3213931f1ce39188b6e08"
    )
    assert support["full104_substrate_sha256"] == (
        "66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29"
    )
    assert support["missing_value_semantics_id"] == "UNMEASURED_IS_MISSING_NOT_ZERO"
    assert support["training_authorized"] is False


def test_census_authority_builder_rederives_receipts_and_excludes_local_paths() -> None:
    source = Path(
        "scripts/agent/build_full104_census_authority_v2_20260918.py"
    ).read_text(encoding="utf-8")

    for token in (
        "if summary != expected_summary:",
        "if split != expected_split:",
        "if eligibility != expected_eligibility:",
        "derive_expected_receipts(",
        "AUTHORITY_REVISION_ID",
        "repo_relpath",
        "refuse to overwrite existing census authority",
    ):
        assert token in source

    forbidden = (
        '"path": str(args.support_authority)',
        '"pass1_physical_binding_path":',
        '"summary_path":',
        '"split_path":',
        '"target_eligibility_path":',
    )
    assert [token for token in forbidden if token in source] == []


def test_census_authority_builder_binds_code_provenance() -> None:
    source = Path(
        "scripts/agent/build_full104_census_authority_v2_20260918.py"
    ).read_text(encoding="utf-8")
    for token in (
        '"builder": builder_binding',
        '"receipt_generator":',
        '"physical_binding_verifier":',
        '"census_receipt_library":',
        "executed census builder bytes differ from --repo builder bytes",
    ):
        assert token in source
