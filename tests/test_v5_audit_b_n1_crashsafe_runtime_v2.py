from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from sea_ad_jepa.v5 import audit_b_n1_crashsafe_runtime_v2 as rt
from sea_ad_jepa.v5.audit_b_production_burden_v1 import BURDEN_RUNGS, POLICIES


def _sha(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def source_fold() -> tuple[np.ndarray, np.ndarray]:
    source = np.asarray([0] * 41 + [1] * 17 + [2] * 46, dtype=np.int64)
    fold = np.asarray(
        [0] * 11 + [1] * 10 + [2] * 10 + [3] * 10
        + [0] * 5 + [1] * 4 + [2] * 4 + [3] * 4
        + [0] * 12 + [1] * 12 + [2] * 11 + [3] * 11,
        dtype=np.int64,
    )
    return source, fold


def digest_i8(x: np.ndarray) -> str:
    return hashlib.sha256(
        np.asarray(x).astype("<i8", copy=False).tobytes(order="C")
    ).hexdigest()


def make_context(targets: np.ndarray, source: np.ndarray, fold: np.ndarray, *, tag: str = "a"):
    return rt.build_context(
        code_sha256=_sha("code-" + tag),
        data_identity_sha256=_sha("synthetic-data-" + tag),
        frozen_targets_sha256=digest_i8(targets),
        donor_source_sha256=digest_i8(source),
        fold_by_donor_sha256=digest_i8(fold),
        core_order_sha256=_sha("core-" + tag),
        parameters_sha256=_sha("params-" + tag),
        rng_authority_sha256=_sha("rng-" + tag),
        stream_identity_sha256=_sha("stream-" + tag),
    )


def fake_unit_factory(source, fold, calls):
    def compute(ti, fi, ri, target_col):
        calls.append((ti, fi, ri))
        rung = BURDEN_RUNGS[ri]
        rows = []
        for donor in np.flatnonzero(fold == fi):
            d = int(donor)
            for p, policy in enumerate(POLICIES):
                base = 0.0 if policy == "UNIFORM_RANDOM" else (
                    (ti + 1) * 1e-6 + (fi + 1) * 1e-5
                    + (ri + 1) * 1e-4 + (p + 1) * 1e-3
                )
                rows.append({
                    "target_col": int(target_col),
                    "fold_index": fi,
                    "donor_code": d,
                    "source_code": int(source[d]),
                    "policy_id": policy,
                    "rung_numerator": rung.numerator,
                    "rung_denominator": rung.denominator,
                    "normalized_delta_detected": base,
                    "normalized_delta_umi": base / 2.0,
                })
        return rows
    return compute


def test_context_is_synthetic_only_and_self_hashed():
    source, fold = source_fold()
    targets = np.arange(1000, 1256, dtype=np.int64)
    context = make_context(targets, source, fold)
    assert rt.validate_context(context) == context
    assert context["scope"] == rt.SCOPE
    assert context["physical_execution_authorized"] is False
    assert context["training_authorized"] is False
    bad = dict(context)
    bad["physical_execution_authorized"] = True
    bad["context_sha256"] = rt.canonical_digest(
        {k: v for k, v in bad.items() if k != "context_sha256"}
    )
    with pytest.raises(ValueError, match="physical_execution_authorized"):
        rt.validate_context(bad)


def test_interrupted_resume_is_byte_identical_and_context_bound(tmp_path: Path):
    source, fold = source_fold()
    targets = np.arange(1000, 1256, dtype=np.int64)
    context = make_context(targets, source, fold)

    interrupted = tmp_path / "interrupted"
    calls_a = []
    compute_a = fake_unit_factory(source, fold, calls_a)
    assert rt.run_resumable_units(
        journal_dir=interrupted, context=context, frozen_targets=targets,
        compute_unit=compute_a, stop_after_new_units=19,
    ) == 19
    assert rt.run_resumable_units(
        journal_dir=interrupted, context=context, frozen_targets=targets,
        compute_unit=compute_a,
    ) == rt.EXPECTED_UNITS - 19

    out_a, receipt_a = tmp_path / "resumed.npz", tmp_path / "resumed.json"
    final_a = rt.finalize_from_journal(
        journal_dir=interrupted, context=context,
        result_artifact=out_a, result_receipt=receipt_a,
        frozen_targets=targets, donor_source_code=source, fold_by_donor=fold,
    )

    clean = tmp_path / "clean"
    calls_b = []
    assert rt.run_resumable_units(
        journal_dir=clean, context=context, frozen_targets=targets,
        compute_unit=fake_unit_factory(source, fold, calls_b),
    ) == rt.EXPECTED_UNITS
    out_b, receipt_b = tmp_path / "clean.npz", tmp_path / "clean.json"
    final_b = rt.finalize_from_journal(
        journal_dir=clean, context=context,
        result_artifact=out_b, result_receipt=receipt_b,
        frozen_targets=targets, donor_source_code=source, fold_by_donor=fold,
    )

    assert out_a.read_bytes() == out_b.read_bytes()
    assert receipt_a.read_bytes() == receipt_b.read_bytes()
    assert final_a["execution_context_sha256"] == context["context_sha256"]
    assert final_a["synthetic_result"]["synthetic_result_sha256"] == final_b["synthetic_result"]["synthetic_result_sha256"]
    assert final_a["physical_execution_authorized"] is False
    assert final_a["training_authorized"] is False


def test_resume_rejects_changed_execution_context_before_compute(tmp_path: Path):
    source, fold = source_fold()
    targets = np.arange(256, dtype=np.int64)
    context = make_context(targets, source, fold, tag="original")
    j = tmp_path / "j"
    calls = []
    rt.run_resumable_units(
        journal_dir=j, context=context, frozen_targets=targets,
        compute_unit=fake_unit_factory(source, fold, calls),
        stop_after_new_units=2,
    )
    altered = make_context(targets, source, fold, tag="altered")
    with pytest.raises(ValueError, match="execution context differs"):
        rt.run_resumable_units(
            journal_dir=j, context=altered, frozen_targets=targets,
            compute_unit=lambda *args: (_ for _ in ()).throw(
                AssertionError("compute must not run under changed context")
            ),
            stop_after_new_units=1,
        )
    assert len(calls) == 2


def test_validly_rehashed_unit_from_other_context_is_rejected(tmp_path: Path):
    source, fold = source_fold()
    targets = np.arange(256, dtype=np.int64)
    context = make_context(targets, source, fold, tag="original")
    j = tmp_path / "j"
    rt.run_resumable_units(
        journal_dir=j, context=context, frozen_targets=targets,
        compute_unit=fake_unit_factory(source, fold, []), stop_after_new_units=1,
    )
    path = j / rt.unit_name(0, 0, 0)
    row = json.loads(path.read_text(encoding="utf-8"))
    row["context_sha256"] = _sha("stale-other-context")
    row["record_sha256"] = rt.canonical_digest(
        {k: v for k, v in row.items() if k != "record_sha256"}
    )
    path.write_text(json.dumps(row), encoding="utf-8")
    with pytest.raises(ValueError, match="key/context drift: context_sha256"):
        rt.run_resumable_units(
            journal_dir=j, context=context, frozen_targets=targets,
            compute_unit=fake_unit_factory(source, fold, []),
            stop_after_new_units=1,
        )


def test_finalizer_rejects_source_permutation_with_same_counts(tmp_path: Path):
    source, fold = source_fold()
    targets = np.arange(256, dtype=np.int64)
    context = make_context(targets, source, fold)
    j = tmp_path / "j"
    # A complete journal is not necessary: source binding is checked first.
    rt.run_resumable_units(
        journal_dir=j, context=context, frozen_targets=targets,
        compute_unit=fake_unit_factory(source, fold, []), stop_after_new_units=1,
    )
    swapped = source.copy()
    swapped[0], swapped[41] = swapped[41], swapped[0]
    assert np.array_equal(np.bincount(swapped, minlength=3), np.bincount(source, minlength=3))
    with pytest.raises(ValueError, match="donor source vector differs"):
        rt.finalize_from_journal(
            journal_dir=j, context=context,
            result_artifact=tmp_path / "x.npz", result_receipt=tmp_path / "x.json",
            frozen_targets=targets, donor_source_code=swapped, fold_by_donor=fold,
        )


def test_frozen_target_order_is_bound_by_value(tmp_path: Path):
    source, fold = source_fold()
    targets = np.arange(256, dtype=np.int64)
    context = make_context(targets, source, fold)
    changed = targets.copy()
    changed[0], changed[1] = changed[1], changed[0]
    with pytest.raises(ValueError, match="frozen target order differs"):
        rt.run_resumable_units(
            journal_dir=tmp_path / "j", context=context, frozen_targets=changed,
            compute_unit=fake_unit_factory(source, fold, []), stop_after_new_units=1,
        )


def test_duplicate_observation_fails_even_if_unit_is_validly_rehashed(tmp_path: Path):
    source, fold = source_fold()
    targets = np.arange(256, dtype=np.int64)
    context = make_context(targets, source, fold)
    j = tmp_path / "j"
    rt.run_resumable_units(
        journal_dir=j, context=context, frozen_targets=targets,
        compute_unit=fake_unit_factory(source, fold, []), stop_after_new_units=1,
    )
    path = j / rt.unit_name(0, 0, 0)
    row = json.loads(path.read_text(encoding="utf-8"))
    row["observations"].append(dict(row["observations"][0]))
    row["record_sha256"] = rt.canonical_digest(
        {k: v for k, v in row.items() if k != "record_sha256"}
    )
    path.write_text(json.dumps(row), encoding="utf-8")
    # Finish only the first target/fold/rung is impossible; invoke finalizer and
    # verify the malformed committed unit is rejected before missing later units.
    with pytest.raises(ValueError, match="missing/duplicate/extra"):
        rt.finalize_from_journal(
            journal_dir=j, context=context,
            result_artifact=tmp_path / "x.npz", result_receipt=tmp_path / "x.json",
            frozen_targets=targets, donor_source_code=source, fold_by_donor=fold,
        )


def test_stale_temp_is_discarded_but_does_not_gain_authority(tmp_path: Path):
    source, fold = source_fold()
    targets = np.arange(256, dtype=np.int64)
    context = make_context(targets, source, fold)
    j = tmp_path / "j"
    stale = j / (rt.unit_name(0, 0, 0) + ".tmp")
    j.mkdir(parents=True)
    stale.write_text("{partial", encoding="utf-8")
    rt.run_resumable_units(
        journal_dir=j, context=context, frozen_targets=targets,
        compute_unit=fake_unit_factory(source, fold, []), stop_after_new_units=1,
    )
    assert not stale.exists()
    assert (j / rt.unit_name(0, 0, 0)).is_file()



def test_context_rejects_extra_fields_even_when_rehashed():
    source, fold = source_fold()
    targets = np.arange(256, dtype=np.int64)
    context = make_context(targets, source, fold)
    context["unexpected"] = "not-authority"
    context["context_sha256"] = rt.canonical_digest(
        {k: v for k, v in context.items() if k != "context_sha256"}
    )
    with pytest.raises(ValueError, match="unexpected or missing"):
        rt.validate_context(context)


def test_resume_rejects_validly_rehashed_wrong_target_col(tmp_path: Path):
    source, fold = source_fold()
    targets = np.arange(256, dtype=np.int64)
    context = make_context(targets, source, fold)
    j = tmp_path / "j"
    rt.run_resumable_units(
        journal_dir=j, context=context, frozen_targets=targets,
        compute_unit=fake_unit_factory(source, fold, []), stop_after_new_units=1,
    )
    path = j / rt.unit_name(0, 0, 0)
    row = json.loads(path.read_text(encoding="utf-8"))
    row["target_col"] = int(targets[1])
    row["record_sha256"] = rt.canonical_digest(
        {k: v for k, v in row.items() if k != "record_sha256"}
    )
    path.write_text(json.dumps(row), encoding="utf-8")
    with pytest.raises(ValueError, match="committed journal target differs"):
        rt.run_resumable_units(
            journal_dir=j, context=context, frozen_targets=targets,
            compute_unit=fake_unit_factory(source, fold, []), stop_after_new_units=1,
        )
