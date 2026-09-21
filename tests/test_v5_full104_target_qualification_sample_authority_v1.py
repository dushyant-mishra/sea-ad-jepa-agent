from __future__ import annotations

import dataclasses
import hashlib
import inspect

import pytest

from sea_ad_jepa.v5.full104_target_qualification_sample_authority_v1 import (
    EXPECTED_SAMPLE_CELLS,
    Full104TargetQualificationSampleAuthorityV1,
)


def h(x: str) -> str:
    return hashlib.sha256(x.encode()).hexdigest()


def authority(**updates) -> Full104TargetQualificationSampleAuthorityV1:
    values = dict(
        authority_id="TEST_FULL104_TARGET_QUALIFICATION_SAMPLE",
        population_authority_sha256=h("population"),
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
