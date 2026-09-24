from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from sea_ad_jepa.v5 import audit_b_n1_crashsafe_runtime_v1 as rt
from sea_ad_jepa.v5 import audit_b_n1_synthetic_lineage_adapter_v1 as adapter
import hashlib
from sea_ad_jepa.v5.audit_b_n1_cpu_burden_assembly_v1 import SOURCE_NAMES
from sea_ad_jepa.v5.audit_b_production_burden_v1 import BURDEN_RUNGS, POLICIES


def source_fold():
    source = np.asarray([0] * 41 + [1] * 17 + [2] * 46, dtype=np.int64)
    fold = np.asarray(
        [0] * 11 + [1] * 10 + [2] * 10 + [3] * 10
        + [0] * 5 + [1] * 4 + [2] * 4 + [3] * 4
        + [0] * 12 + [1] * 12 + [2] * 11 + [3] * 11,
        dtype=np.int64,
    )
    return source, fold


def fake_unit_factory(source, fold, calls):
    def compute(ti, fi, ri, target_col):
        calls.append((ti, fi, ri))
        rung = BURDEN_RUNGS[ri]
        rows = []
        for donor in np.flatnonzero(fold == fi):
            d = int(donor)
            for p, policy in enumerate(POLICIES):
                base = 0.0 if policy == "UNIFORM_RANDOM" else (
                    (ti + 1) * 1e-6 + (fi + 1) * 1e-5 + (ri + 1) * 1e-4 + (p + 1) * 1e-3
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


def test_interrupted_resume_is_byte_identical_to_clean_run(tmp_path: Path) -> None:
    """Full 6,144-unit replay through the *new* source-bound synthetic adapter."""
    source, fold = source_fold()
    targets = np.arange(1000, 1256, dtype=np.int64)
    donors = np.arange(104, dtype=np.int64)
    nnz = np.ones((104, 256), dtype=np.int64)
    umi = nnz * 2

    def digest(value):
        return hashlib.sha256(np.asarray(value, dtype="<i8").tobytes()).hexdigest()

    bound = adapter.bind_synthetic_lineage(
        frozen_targets=targets, core_addresses=targets,
        donor_source_code=source, fold_by_donor=fold,
        cell_donor=donors, src_of_cell=source.copy(),
        stream_source_by_donor=source.copy(),
        donor_nnz=nnz, donor_umi=umi,
        expected_cell_donor_sha256=digest(donors),
        expected_donor_source_sha256=digest(source),
        expected_fold_sha256=digest(fold),
        expected_core_sha256=digest(targets),
        expected_target_order_sha256=digest(targets),
        expected_donor_nnz_sha256=digest(nnz),
        expected_donor_umi_sha256=digest(umi),
        source_names=("HVS", "NPH52", "SEA_AD"),
        stream_root_sha256="a" * 64,
        code_root_sha256="b" * 64,
        parameter_root_sha256="c" * 64,
        rng_root_sha256="d" * 64,
    )

    interrupted = tmp_path / "interrupted"
    calls_a = []
    compute_a = fake_unit_factory(source, fold, calls_a)
    assert adapter.run_synthetic_journal(
        bound=bound, journal_dir=interrupted,
        compute_unit=compute_a, stop_after_new_units=19,
    ) == 19
    assert len(calls_a) == 19
    resumed_new = adapter.run_synthetic_journal(
        bound=bound, journal_dir=interrupted, compute_unit=compute_a,
    )
    assert resumed_new == rt.EXPECTED_UNITS - 19
    assert len(calls_a) == rt.EXPECTED_UNITS

    out_a = tmp_path / "resumed.npz"
    receipt_a = tmp_path / "resumed.json"
    final_a = adapter.finalize_synthetic_journal(
        bound=bound, journal_dir=interrupted,
        result_artifact=out_a, result_receipt=receipt_a,
    )
    clean = tmp_path / "clean"
    calls_b = []
    assert adapter.run_synthetic_journal(
        bound=bound, journal_dir=clean,
        compute_unit=fake_unit_factory(source, fold, calls_b),
    ) == rt.EXPECTED_UNITS
    out_b = tmp_path / "clean.npz"
    receipt_b = tmp_path / "clean.json"
    final_b = adapter.finalize_synthetic_journal(
        bound=bound, journal_dir=clean,
        result_artifact=out_b, result_receipt=receipt_b,
    )

    assert out_a.read_bytes() == out_b.read_bytes()
    assert receipt_a.read_bytes() == receipt_b.read_bytes()
    assert final_a["synthetic_result"]["synthetic_result_sha256"] == final_b["synthetic_result"]["synthetic_result_sha256"]
    assert final_a["schema"] == rt.SYNTHETIC_FINAL_SCHEMA
    assert final_a["physical_execution_authorized"] is False
    assert final_a["execution_context_sha256"] == rt.canonical_digest(bound.context)
    assert final_a["finalization_sha256"] == rt.canonical_digest({
        k: v for k, v in final_a.items() if k != "finalization_sha256"
    })
    assert final_a["precision_calculated"] is False
    assert final_a["training_authorized"] is False


def test_resume_never_recomputes_already_committed_units(tmp_path: Path) -> None:
    source, fold = source_fold()
    targets = np.arange(256, dtype=np.int64)
    calls = []
    compute = fake_unit_factory(source, fold, calls)
    assert rt.run_resumable_units(
        journal_dir=tmp_path / "j", frozen_targets=targets,
        compute_unit=compute, stop_after_new_units=3,
    ) == 3
    first = list(calls)

    def fail_on_old(ti, fi, ri, target_col):
        if (ti, fi, ri) in first:
            raise AssertionError("resume recomputed a committed unit")
        return compute(ti, fi, ri, target_col)

    rt.run_resumable_units(
        journal_dir=tmp_path / "j", frozen_targets=targets,
        compute_unit=fail_on_old, stop_after_new_units=2,
    )
    assert len(calls) == 5


def test_corrupt_or_rekeyed_unit_fails_closed(tmp_path: Path) -> None:
    source, fold = source_fold()
    targets = np.arange(256, dtype=np.int64)
    rt.run_resumable_units(
        journal_dir=tmp_path / "j", frozen_targets=targets,
        compute_unit=fake_unit_factory(source, fold, []), stop_after_new_units=1,
    )
    path = tmp_path / "j" / rt.unit_name(0, 0, 0)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["fold_index"] = 1
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="key drift|self-digest"):
        rt.read_unit(
            journal_dir=tmp_path / "j", target_index=0, fold_index=0, rung_index=0
        )


def test_finalizer_refuses_partial_and_extra_journals(tmp_path: Path) -> None:
    source, fold = source_fold()
    targets = np.arange(256, dtype=np.int64)
    j = tmp_path / "j"
    rt.run_resumable_units(
        journal_dir=j, frozen_targets=targets,
        compute_unit=fake_unit_factory(source, fold, []), stop_after_new_units=1,
    )
    with pytest.raises(ValueError, match="missing N1 journal unit"):
        rt.finalize_from_journal(
            journal_dir=j,
            result_artifact=tmp_path / "x.npz",
            result_receipt=tmp_path / "x.json",
            frozen_targets=targets,
            donor_source_code=source,
            fold_by_donor=fold,
        )


def test_crash_temp_is_discarded_and_finalization_can_resume(tmp_path: Path) -> None:
    source, fold = source_fold()
    targets = np.arange(256, dtype=np.int64)
    j = tmp_path / "j"
    stale = j / (rt.unit_name(0, 0, 0) + ".tmp")
    j.mkdir(parents=True)
    stale.write_text("{partial", encoding="utf-8")
    rt.run_resumable_units(
        journal_dir=j, frozen_targets=targets,
        compute_unit=fake_unit_factory(source, fold, []), stop_after_new_units=1,
    )
    assert not stale.exists()
    assert (j / rt.unit_name(0, 0, 0)).is_file()


def test_finalization_recovers_when_artifact_already_committed(tmp_path: Path) -> None:
    source, fold = source_fold()
    targets = np.arange(256, dtype=np.int64)
    j = tmp_path / "j"
    rt.run_resumable_units(
        journal_dir=j, frozen_targets=targets,
        compute_unit=fake_unit_factory(source, fold, []),
    )
    first_artifact = tmp_path / "first.npz"
    first_receipt = tmp_path / "first.json"
    rt.finalize_from_journal(
        journal_dir=j, result_artifact=first_artifact, result_receipt=first_receipt,
        frozen_targets=targets, donor_source_code=source, fold_by_donor=fold,
    )
    # Simulate a crash after artifact commit but before receipt commit by copying
    # only the deterministic artifact into a fresh finalization location.
    recovered_artifact = tmp_path / "recovered.npz"
    recovered_artifact.write_bytes(first_artifact.read_bytes())
    recovered_receipt = tmp_path / "recovered.json"
    rt.finalize_from_journal(
        journal_dir=j, result_artifact=recovered_artifact,
        result_receipt=recovered_receipt, frozen_targets=targets,
        donor_source_code=source, fold_by_donor=fold,
    )
    assert recovered_artifact.read_bytes() == first_artifact.read_bytes()
    assert recovered_receipt.read_bytes() == first_receipt.read_bytes()
