from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from sea_ad_jepa.v5 import audit_b_n1_crashsafe_runtime_v1 as rt
from sea_ad_jepa.v5 import audit_b_n1_synthetic_lineage_adapter_v1 as adapter
from sea_ad_jepa.v5.audit_b_production_burden_v1 import POLICIES, BURDEN_RUNGS


def digest(arr):
    return hashlib.sha256(np.asarray(arr, dtype="<i8").tobytes()).hexdigest()


def fixture_kwargs():
    source = np.asarray([0] * 41 + [1] * 17 + [2] * 46, dtype=np.int64)
    fold = np.asarray(
        [0] * 11 + [1] * 10 + [2] * 10 + [3] * 10
        + [0] * 5 + [1] * 4 + [2] * 4 + [3] * 4
        + [0] * 12 + [1] * 12 + [2] * 11 + [3] * 11,
        dtype=np.int64,
    )
    core = np.arange(1000, 1256, dtype=np.int64)
    donors = np.arange(104, dtype=np.int64)
    return dict(
        frozen_targets=core.copy(), core_addresses=core,
        donor_source_code=source, fold_by_donor=fold,
        cell_donor=donors, src_of_cell=source.copy(),
        stream_source_by_donor=source.copy(),
        donor_nnz=np.ones((104, 256), dtype=np.int64),
        donor_umi=np.full((104, 256), 2, dtype=np.int64),
        expected_cell_donor_sha256=digest(donors),
        expected_donor_source_sha256=digest(source),
        expected_fold_sha256=digest(fold),
        expected_core_sha256=digest(core),
        expected_target_order_sha256=digest(core),
        expected_donor_nnz_sha256=digest(np.ones((104, 256), dtype=np.int64)),
        expected_donor_umi_sha256=digest(np.full((104, 256), 2, dtype=np.int64)),
        source_names=("HVS", "NPH52", "SEA_AD"),
        stream_root_sha256="a" * 64, code_root_sha256="b" * 64,
        parameter_root_sha256="c" * 64, rng_root_sha256="d" * 64,
    )


def fake_compute(bound, calls):
    def compute(ti, fi, ri, target):
        calls.append((ti, fi, ri))
        rung = BURDEN_RUNGS[ri]
        rows = []
        for d in np.flatnonzero(bound.fold_by_donor == fi):
            for policy in POLICIES:
                value = 0.0 if policy == "UNIFORM_RANDOM" else (ti + 1) * 1e-3
                rows.append({
                    "target_col": target, "fold_index": fi,
                    "donor_code": int(d),
                    "source_code": int(bound.donor_source_code[d]),
                    "policy_id": policy, "rung_numerator": rung.numerator,
                    "rung_denominator": rung.denominator,
                    "normalized_delta_detected": value,
                    "normalized_delta_umi": value / 2,
                })
        return rows
    return compute


def test_synthetic_lineage_binds_corrected_sources_and_exact_execution_roots():
    bound = adapter.bind_synthetic_lineage(**fixture_kwargs())
    assert bound.context["scope"] == adapter.MODE
    assert bound.context["schema"] == rt.CONTEXT_SCHEMA
    assert bound.context["cell_donor_sha256"] == digest(np.arange(104))
    assert np.array_equal(bound.donor_source_code, fixture_kwargs()["donor_source_code"])


@pytest.mark.parametrize("field,expected", [
    ("source_names", "source-name order"),
    ("stream_source_by_donor", "stream donor source"),
    ("src_of_cell", "cell-to-donor source"),
    ("donor_source_code", "corrected donor/source"),
    ("cell_donor", "synthetic pass1 donor identity"),
    ("fold_by_donor", "donor/fold census"),
    ("frozen_targets", "frozen targets"),
    ("donor_umi", "synthetic raw-UMI"),
    ("code_root_sha256", "frozen 64-character"),
])
def test_lineage_negative_controls(field, expected):
    kw = fixture_kwargs()
    if field == "source_names":
        kw[field] = ("HVS", "SEA_AD", "NPH52")
    elif field == "stream_source_by_donor":
        kw[field][41], kw[field][58] = kw[field][58], kw[field][41]
    elif field == "src_of_cell":
        kw[field][41], kw[field][58] = kw[field][58], kw[field][41]
    elif field == "donor_source_code":
        kw[field][41], kw[field][58] = kw[field][58], kw[field][41]
        kw["stream_source_by_donor"] = kw[field].copy()
        kw["src_of_cell"] = kw[field].copy()
    elif field == "cell_donor":
        kw[field][0] = 1  # same source; independently pinned donor digest differs
    elif field == "fold_by_donor":
        kw[field][0] = 1
    elif field == "frozen_targets":
        kw[field][0] = kw[field][1]
    elif field == "donor_umi":
        kw[field][0, 0] = 0
    elif field == "code_root_sha256":
        kw[field] = "unreviewed"
    with pytest.raises(ValueError, match=expected):
        adapter.bind_synthetic_lineage(**kw)


def test_context_bound_interruption_resume_and_changed_roots_rejected(tmp_path):
    bound = adapter.bind_synthetic_lineage(**fixture_kwargs())
    journal = tmp_path / "journal"
    calls = []
    fn = fake_compute(bound, calls)
    assert adapter.run_synthetic_journal(
        bound=bound, journal_dir=journal, compute_unit=fn, stop_after_new_units=2,
    ) == 2
    ctx = json.loads((journal / rt.CONTEXT_NAME).read_text())
    assert ctx["context_sha256"] == rt.canonical_digest(bound.context)
    first = json.loads((journal / rt.unit_name(0, 0, 0)).read_text())
    assert first["context_sha256"] == ctx["context_sha256"]
    assert len(calls) == 2
    assert adapter.run_synthetic_journal(
        bound=bound, journal_dir=journal, compute_unit=fn, stop_after_new_units=1,
    ) == 1
    assert len(calls) == 3

    altered = dict(bound.context)
    altered["parameter_root_sha256"] = "f" * 64
    with pytest.raises(ValueError, match="execution context drift"):
        adapter.run_synthetic_journal(
            bound=replace(bound, context=altered), journal_dir=journal,
            compute_unit=lambda *_: (_ for _ in ()).throw(AssertionError("should not compute")),
        )
    assert len(calls) == 3
    with pytest.raises(ValueError, match="requires execution context"):
        rt.run_resumable_units(
            journal_dir=journal, frozen_targets=bound.frozen_targets,
            compute_unit=fn, stop_after_new_units=1,
        )
    with pytest.raises(ValueError, match="execution context drift"):
        rt.read_unit(
            journal_dir=journal, target_index=0, fold_index=0, rung_index=0,
        )


def test_rehashed_unit_with_different_context_is_rejected_on_resume(tmp_path):
    bound = adapter.bind_synthetic_lineage(**fixture_kwargs())
    journal = tmp_path / "journal"
    fn = fake_compute(bound, [])
    adapter.run_synthetic_journal(
        bound=bound, journal_dir=journal, compute_unit=fn, stop_after_new_units=1,
    )
    path = journal / rt.unit_name(0, 0, 0)
    record = json.loads(path.read_text())
    record["context_sha256"] = "e" * 64
    record["record_sha256"] = rt.canonical_digest({
        key: value for key, value in record.items() if key != "record_sha256"
    })
    path.write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises(ValueError, match="journal unit execution context drift"):
        adapter.run_synthetic_journal(
            bound=bound, journal_dir=journal, compute_unit=fn,
            stop_after_new_units=1,
        )


def test_existing_legacy_journal_cannot_adopt_new_context(tmp_path):
    bound = adapter.bind_synthetic_lineage(**fixture_kwargs())
    journal = tmp_path / "legacy"
    fn = fake_compute(bound, [])
    rt.run_resumable_units(
        journal_dir=journal, frozen_targets=bound.frozen_targets,
        compute_unit=fn, stop_after_new_units=1,
    )
    with pytest.raises(ValueError, match="existing journal units lack"):
        adapter.run_synthetic_journal(
            bound=bound, journal_dir=journal, compute_unit=fn,
            stop_after_new_units=1,
        )


def test_bad_donor_policy_duplicate_fails_before_unit_publication(tmp_path):
    bound = adapter.bind_synthetic_lineage(**fixture_kwargs())
    journal = tmp_path / "journal"
    fn = fake_compute(bound, [])
    def duplicate(ti, fi, ri, target):
        rows = fn(ti, fi, ri, target)
        rows[-1] = rows[0]
        return rows
    with pytest.raises(ValueError, match="missing/duplicate/extra"):
        adapter.run_synthetic_journal(
            bound=bound, journal_dir=journal,
            compute_unit=duplicate, stop_after_new_units=1,
        )
    assert not (journal / rt.unit_name(0, 0, 0)).exists()


def test_partial_synthetic_finalization_fails_closed(tmp_path):
    bound = adapter.bind_synthetic_lineage(**fixture_kwargs())
    journal = tmp_path / "journal"
    adapter.run_synthetic_journal(
        bound=bound, journal_dir=journal,
        compute_unit=fake_compute(bound, []), stop_after_new_units=1,
    )
    with pytest.raises(ValueError, match="missing N1 journal unit"):
        adapter.finalize_synthetic_journal(
            bound=bound, journal_dir=journal,
            result_artifact=tmp_path / "result.npz",
            result_receipt=tmp_path / "result.json",
        )
    assert not (tmp_path / "result.npz").exists()


def test_same_census_fold_permutation_is_not_authenticated():
    kw = fixture_kwargs()
    kw["fold_by_donor"][0], kw["fold_by_donor"][11] = (
        kw["fold_by_donor"][11], kw["fold_by_donor"][0]
    )
    assert tuple(np.bincount(kw["fold_by_donor"], minlength=4)) == (28, 26, 25, 25)
    with pytest.raises(ValueError, match="synthetic fold assignment differs"):
        adapter.bind_synthetic_lineage(**kw)


def test_same_set_different_target_order_is_not_authenticated():
    kw = fixture_kwargs()
    kw["frozen_targets"][0], kw["frozen_targets"][1] = (
        kw["frozen_targets"][1], kw["frozen_targets"][0]
    )
    with pytest.raises(ValueError, match="synthetic target order differs"):
        adapter.bind_synthetic_lineage(**kw)


def test_valid_shape_changed_donor_statistics_rejected():
    kw = fixture_kwargs()
    kw["donor_umi"][12, 7] += 1
    with pytest.raises(ValueError, match="synthetic donor umi differs"):
        adapter.bind_synthetic_lineage(**kw)


@pytest.mark.parametrize("field,expected", [
    ("frozen_targets", "target_order_sha256"),
    ("donor_source_code", "donor_source_sha256"),
    ("fold_by_donor", "fold_by_donor_sha256"),
])
def test_bound_arrays_cannot_mutate_between_validation_and_first_unit(
    field, expected, tmp_path,
):
    bound = adapter.bind_synthetic_lineage(**fixture_kwargs())
    arr = getattr(bound, field)
    arr[0] += 1
    with pytest.raises(ValueError, match=expected):
        adapter.run_synthetic_journal(
            bound=bound, journal_dir=tmp_path / "journal",
            compute_unit=lambda *_: (_ for _ in ()).throw(AssertionError("should not compute")),
            stop_after_new_units=1,
        )
    assert not (tmp_path / "journal" / rt.CONTEXT_NAME).exists()


def test_context_mutation_before_first_unit_is_rejected(tmp_path):
    bound = adapter.bind_synthetic_lineage(**fixture_kwargs())
    bound.context["rng_root_sha256"] = "e" * 64
    with pytest.raises(ValueError, match="execution context drift"):
        adapter.run_synthetic_journal(
            bound=bound, journal_dir=tmp_path / "journal",
            compute_unit=lambda *_: (_ for _ in ()).throw(AssertionError("should not compute")),
            stop_after_new_units=1,
        )


def test_full_core_synthetic_geometry_binds_without_physical_data():
    """Exercise native 17,186-feature donor-statistic shapes on CPU, no N1."""
    kw = fixture_kwargs()
    core = np.arange(17186, dtype=np.int64)
    nnz = np.ones((104, 17186), dtype=np.int64)
    umi = np.full((104, 17186), 3, dtype=np.int64)
    kw.update(
        core_addresses=core,
        donor_nnz=nnz,
        donor_umi=umi,
        expected_core_sha256=digest(core),
        expected_donor_nnz_sha256=digest(nnz),
        expected_donor_umi_sha256=digest(umi),
    )
    bound = adapter.bind_synthetic_lineage(**kw)
    assert bound.frozen_targets.shape == (256,)
    assert bound.context["core_sha256"] == digest(core)
    assert bound.context["scope"] == adapter.MODE
