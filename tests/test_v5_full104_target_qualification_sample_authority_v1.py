from __future__ import annotations

import dataclasses
import hashlib
import inspect
from pathlib import Path

import numpy as np
import pytest

from sea_ad_jepa.v5.full104_target_qualification_sample_authority_v1 import (
    EXPECTED_SAMPLE_CELLS,
    Full104TargetQualificationSampleAuthorityV1,
    Full104TargetQualificationSampleReceiptV1,
    RetainedQualificationRowSelectorV1,
)


ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts/agent/build_full104_target_qualification_sample_v1_20260921.py"


def h(x: str) -> str:
    return hashlib.sha256(x.encode()).hexdigest()


def authority(**updates) -> Full104TargetQualificationSampleAuthorityV1:
    values = dict(
        authority_id="TEST_FULL104_TARGET_QUALIFICATION_SAMPLE",
        population_authority_sha256=h("population"),
        full104_block_manifest_sha256=h("level4-manifest"),
        dataset_etl_atlas_sha256=h("etl"),
        outer_split_receipt_sha256=h("split"),
    )
    values.update(updates)
    return Full104TargetQualificationSampleAuthorityV1(**values)


def test_current_geometry_is_exact_and_nonexecuting() -> None:
    a = authority()
    a.validate()
    assert a.expected_sample_cells == EXPECTED_SAMPLE_CELLS == 105_553
    assert a.masking_authorized is False
    assert a.training_authorized is False


def test_priority_is_deterministic_and_identity_only() -> None:
    a = authority()
    x = a.selection_priority(donor_code=1, selection_row=10)
    assert x == a.selection_priority(donor_code=1, selection_row=10)
    assert x != a.selection_priority(donor_code=1, selection_row=11)
    assert x != a.selection_priority(donor_code=2, selection_row=10)

    source = inspect.getsource(Full104TargetQualificationSampleAuthorityV1.selection_priority)
    for forbidden in (
        "expression",
        "library_size",
        "nnz",
        "operator",
        "region",
        "class_",
        "pathology",
        "source_library",
    ):
        assert forbidden not in source


@pytest.mark.parametrize(
    "field",
    [
        "expression_used_for_selection",
        "library_size_used_for_selection",
        "nnz_used_for_selection",
        "operator_used_for_selection",
        "region_used_for_selection",
        "class_used_for_selection",
        "pathology_used_for_selection",
        "masking_authorized",
        "training_authorized",
    ],
)
def test_forbidden_selection_or_authority_inputs_fail_closed(field: str) -> None:
    with pytest.raises(ValueError, match=field):
        authority(**{field: True}).validate()


def test_cap_and_expected_sample_geometry_are_frozen() -> None:
    with pytest.raises(ValueError, match="per_donor_cap"):
        authority(per_donor_cap=2048).validate()
    with pytest.raises(ValueError, match="expected_sample_cells"):
        authority(expected_sample_cells=105_552).validate()


def test_sample_is_role_distinct_from_control_calibration_cache() -> None:
    a = authority()
    assert "TARGET_QUALIFICATION_ONLY" in a.sample_role_id
    assert "CONTROL_CALIBRATION" not in a.sample_role_id


def test_root_changes_change_sample_authority_digest() -> None:
    a = authority()
    b = dataclasses.replace(a, outer_split_receipt_sha256=h("other-split"))
    assert a.canonical_digest() != b.canonical_digest()


def test_priority_rejects_row_alias_and_invalid_donor_inputs() -> None:
    a = authority()
    with pytest.raises(ValueError, match="donor_code"):
        a.selection_priority(donor_code=-1, selection_row=0)
    with pytest.raises(ValueError, match="selection_row"):
        a.selection_priority(donor_code=0, selection_row=-1)
    with pytest.raises(ValueError, match="selection_row"):
        a.selection_priority(donor_code=0, selection_row=4_553_407)


def _synthetic_full104_like_rows() -> tuple[np.ndarray, np.ndarray]:
    rows = []
    donors = []
    cursor = 0
    for donor in range(104):
        n = 1026 if donor < 103 else 81
        rows.extend(range(cursor, cursor + n))
        donors.extend([donor] * n)
        cursor += n
    return np.asarray(rows, dtype=np.int64), np.asarray(donors, dtype=np.int64)


def test_streaming_selector_closes_exact_current_sample_geometry() -> None:
    rows, donors = _synthetic_full104_like_rows()
    a = authority()

    one = RetainedQualificationRowSelectorV1(a)
    # Deliberately feed multiple chunks to prove streaming order does not change
    # the deterministic donor-wise selection.
    cut = rows.size // 3
    one.update(rows[:cut], donors[:cut])
    one.update(rows[cut:2 * cut], donors[cut:2 * cut])
    one.update(rows[2 * cut:], donors[2 * cut:])
    sel1, donor1, rank1, retained1 = one.finalize()

    two = RetainedQualificationRowSelectorV1(a)
    two.update(rows, donors)
    sel2, donor2, rank2, retained2 = two.finalize()

    assert sel1.size == 105_553
    assert np.unique(sel1).size == sel1.size
    assert np.array_equal(sel1, sel2)
    assert np.array_equal(donor1, donor2)
    assert np.array_equal(rank1, rank2)
    assert np.array_equal(retained1, retained2)
    assert np.all(retained1[:103] == 1024)
    assert retained1[103] == 81


def test_builder_is_metadata_only_and_binds_current_identity_roots() -> None:
    source = BUILDER.read_text(encoding="utf-8")
    assert "meta_sha256" in source
    assert "selection_row" in source
    assert "outer_split_receipt_sha256" in source
    assert "EXPECTED_BLOCK_MANIFEST_SHA256" in source
    assert "expression_opened_by_builder" in source
    # The qualification sample builder must not deserialize or iterate expression.
    assert "sp.load_npz" not in source
    assert ".iter_blocks(" not in source
    assert "toarray(" not in source
    assert "X_log1p10k" not in source


def receipt(a: Full104TargetQualificationSampleAuthorityV1, **updates):
    values = dict(
        sample_authority_sha256=a.canonical_digest(),
        full104_block_manifest_sha256=a.full104_block_manifest_sha256,
        population_authority_sha256=a.population_authority_sha256,
        dataset_etl_atlas_sha256=a.dataset_etl_atlas_sha256,
        outer_split_receipt_sha256=a.outer_split_receipt_sha256,
        retained_cells=105_553,
        retained_donors=104,
        donors_at_cap=103,
        min_retained_per_donor=81,
        max_retained_per_donor=1024,
        selection_rows_file_sha256=h("selection"),
        donor_code_file_sha256=h("donor"),
        row_rank_file_sha256=h("rank"),
        retained_count_by_donor_file_sha256=h("retained"),
        full_donor_n_file_sha256=h("full-n"),
        fold_by_donor_file_sha256=h("fold"),
        donor_source_code_file_sha256=h("source"),
        builder_source_sha256=h("builder"),
    )
    values.update(updates)
    return Full104TargetQualificationSampleReceiptV1(**values)


def test_typed_receipt_binds_authority_and_every_array_role() -> None:
    a = authority()
    rec = receipt(a)
    rec.validate_against_authority(a)
    assert len(rec.canonical_digest()) == 64
    assert rec.expression_opened_by_builder is False
    assert rec.masking_authorized is False
    assert rec.training_authorized is False


def test_receipt_cannot_bind_a_different_sampling_authority() -> None:
    a = authority()
    rec = receipt(a)
    other = dataclasses.replace(a, outer_split_receipt_sha256=h("other-split"))
    with pytest.raises(ValueError, match="sample authority digest mismatch"):
        rec.validate_against_authority(other)


def test_receipt_geometry_and_file_digests_fail_closed() -> None:
    a = authority()
    with pytest.raises(ValueError, match="retained_cells mismatch"):
        receipt(a, retained_cells=105_552).validate()
    with pytest.raises(ValueError, match="selection_rows_file_sha256"):
        receipt(a, selection_rows_file_sha256="bad").validate()
