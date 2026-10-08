from __future__ import annotations

import dataclasses
import hashlib
import inspect
import json
import subprocess
import sys
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
VALIDATOR = ROOT / "scripts/agent/validate_full104_target_qualification_sample_v1_20260921.py"


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


def _file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_synthetic_sample_package(tmp_path: Path) -> tuple[Path, Full104TargetQualificationSampleReceiptV1]:
    rows, donors = _synthetic_full104_like_rows()
    a = authority()
    selector = RetainedQualificationRowSelectorV1(a)
    selector.update(rows, donors)
    selection, donor_code, rank, retained = selector.finalize()

    sample_dir = tmp_path / "sample"
    sample_dir.mkdir()

    full_n = np.full(104, 44_207, dtype=np.int64)
    full_n[102] = 44_212
    full_n[103] = 81
    assert int(full_n.sum()) == 4_553_407

    fold = np.arange(104, dtype=np.int64) % 4
    source = np.empty(104, dtype=np.int64)
    source[:41] = 0
    source[41:58] = 1
    source[58:] = 2

    arrays = {
        "selection_rows": ("selection_rows_i64.npy", selection),
        "donor_code": ("donor_code_i64.npy", donor_code),
        "row_rank": ("row_rank_i64.npy", rank),
        "retained_count_by_donor": ("retained_count_by_donor_i64.npy", retained),
        "full_donor_n": ("full_donor_n_i64.npy", full_n),
        "fold_by_donor": ("fold_by_donor_i64.npy", fold),
        "donor_source_code": ("donor_source_code_i64.npy", source),
    }
    for _, (name, value) in arrays.items():
        np.save(sample_dir / name, value, allow_pickle=False)

    rec = receipt(
        a,
        selection_rows_file_sha256=_file_sha(sample_dir / arrays["selection_rows"][0]),
        donor_code_file_sha256=_file_sha(sample_dir / arrays["donor_code"][0]),
        row_rank_file_sha256=_file_sha(sample_dir / arrays["row_rank"][0]),
        retained_count_by_donor_file_sha256=_file_sha(
            sample_dir / arrays["retained_count_by_donor"][0]
        ),
        full_donor_n_file_sha256=_file_sha(sample_dir / arrays["full_donor_n"][0]),
        fold_by_donor_file_sha256=_file_sha(sample_dir / arrays["fold_by_donor"][0]),
        donor_source_code_file_sha256=_file_sha(
            sample_dir / arrays["donor_source_code"][0]
        ),
        builder_source_sha256=_file_sha(BUILDER),
    )
    payload = {
        "schema": "V5_FULL104_TARGET_QUALIFICATION_SAMPLE_RECEIPT_V1",
        **rec.__dict__,
        "sample_receipt_sha256": rec.canonical_digest(),
        "authority": a.__dict__,
        "file_names": {role: name for role, (name, _) in arrays.items()},
    }
    (sample_dir / "sample_receipt.json").write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )
    return sample_dir, rec




def test_validator_optional_full_source_replay_is_metadata_only_and_fail_closed(
    tmp_path: Path,
) -> None:
    source = VALIDATOR.read_text(encoding="utf-8")
    assert "_replay_full_source_selection" in source
    assert "_independent_priority" in source
    assert "meta_sha256" in source
    # The replay may load the materialized identity arrays, but must never
    # deserialize Level-4 expression/count matrices.
    assert "sp.load_npz" not in source
    assert ".iter_blocks(" not in source
    assert "X_log1p10k" not in source

    sample_dir, _ = _write_synthetic_sample_package(tmp_path)
    cmd = [
        sys.executable,
        str(VALIDATOR),
        "--sample-dir",
        str(sample_dir),
        "--builder-source",
        str(BUILDER),
        "--level4-root",
        str(tmp_path / "level4"),
    ]
    bad = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    assert bad.returncode != 0
    assert "--level4-root and --split-receipt must be supplied together" in (
        bad.stdout + bad.stderr
    )

def test_downstream_validator_accepts_typed_package_and_rejects_corruption(
    tmp_path: Path,
) -> None:
    sample_dir, rec = _write_synthetic_sample_package(tmp_path)
    cmd = [
        sys.executable,
        str(VALIDATOR),
        "--sample-dir",
        str(sample_dir),
        "--builder-source",
        str(BUILDER),
    ]
    ok = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    assert ok.returncode == 0, ok.stdout + ok.stderr
    parsed = json.loads(ok.stdout.strip().splitlines()[-1])
    assert parsed["status"] == "PASS_FULL104_TARGET_QUALIFICATION_SAMPLE_V1"
    assert parsed["sample_receipt_sha256"] == rec.canonical_digest()

    # A single-byte-equivalent semantic corruption (rewrite an array) must fail
    # before downstream target evaluation can use the package.
    x = np.load(sample_dir / "selection_rows_i64.npy", allow_pickle=False)
    x = np.array(x, copy=True)
    x[0], x[1] = x[1], x[0]
    np.save(sample_dir / "selection_rows_i64.npy", x, allow_pickle=False)
    bad = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    assert bad.returncode != 0
    assert "hash mismatch" in (bad.stdout + bad.stderr)
