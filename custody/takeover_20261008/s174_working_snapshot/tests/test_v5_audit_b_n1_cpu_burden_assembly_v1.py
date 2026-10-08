from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest

from sea_ad_jepa.v5.audit_b_n1_cpu_burden_assembly_v1 import (
    N1DonorTensorAccumulator,
    SOURCE_NAMES,
    validate_donor_geometry,
)
from sea_ad_jepa.v5.audit_b_n1_result_contract_v1 import (
    EXPECTED_TENSOR_SHAPE, POLICY_ORDER,
)
from sea_ad_jepa.v5.audit_b_production_burden_v1 import BURDEN_RUNGS, POLICIES


def _sources_folds():
    source = np.asarray([0]*41 + [1]*17 + [2]*46, dtype=np.int64)
    fold = np.asarray(
        [0]*11+[1]*10+[2]*10+[3]*10
        + [0]*5+[1]*4+[2]*4+[3]*4
        + [0]*12+[1]*12+[2]*11+[3]*11,
        dtype=np.int64,
    )
    return source, fold


def _acc():
    source, fold = _sources_folds()
    return N1DonorTensorAccumulator(
        frozen_targets=np.arange(256, dtype=np.int64),
        donor_source_code=source, fold_by_donor=fold,
    )


def _rows(acc, *, target_index=0, fold_index=0, rung_index=0):
    rung = BURDEN_RUNGS[rung_index]
    return [
        SimpleNamespace(
            target_col=int(acc.targets[target_index]),
            fold_index=fold_index,
            donor_code=int(d),
            source_code=int(acc.source[d]),
            policy_id=policy,
            rung_numerator=rung.numerator,
            rung_denominator=rung.denominator,
            normalized_delta_detected=0.0 if policy == "UNIFORM_RANDOM" else (p + 1) / 100,
            normalized_delta_umi=0.0 if policy == "UNIFORM_RANDOM" else (p + 1) / 200,
        )
        for d in np.flatnonzero(acc.folds == fold_index)
        for p, policy in enumerate(POLICIES)
    ]


def test_frozen_n1_prefix_and_source_fold_geometry_are_strict() -> None:
    acc = _acc()
    assert acc.detected.shape == EXPECTED_TENSOR_SHAPE
    assert np.isnan(acc.detected).all()
    assert not acc.seen.any()
    source, fold = _sources_folds()
    with pytest.raises(ValueError, match="256-target"):
        N1DonorTensorAccumulator(
            frozen_targets=np.arange(255), donor_source_code=source,
            fold_by_donor=fold,
        )
    with pytest.raises(ValueError, match="source"):
        N1DonorTensorAccumulator(
            frozen_targets=np.arange(256), donor_source_code=source[::-1][1:],
            fold_by_donor=fold,
        )
    with pytest.raises(ValueError, match="fold"):
        N1DonorTensorAccumulator(
            frozen_targets=np.arange(256), donor_source_code=source,
            fold_by_donor=np.zeros(104, dtype=np.int64),
        )


def test_ingest_requires_all_four_policies_exact_donors_and_rng_metadata() -> None:
    acc = _acc()
    rows = _rows(acc)
    with pytest.raises(ValueError, match="incomplete"):
        acc.ingest(
            target_index=0, fold_index=0, rung_index=0,
            observations=rows[:-1],
        )
    assert not acc.seen.any()
    with pytest.raises(ValueError, match="duplicate"):
        acc.ingest(
            target_index=0, fold_index=0, rung_index=0,
            observations=rows + [rows[0]],
        )
    assert not acc.seen.any()
    with pytest.raises(ValueError, match="identity"):
        acc.ingest(
            target_index=0, fold_index=0, rung_index=0,
            observations=[SimpleNamespace(**{**vars(r), "target_col": 1}) for r in rows],
        )
    assert not acc.seen.any()
    with pytest.raises(ValueError, match="identity"):
        acc.ingest(
            target_index=0, fold_index=0, rung_index=0,
            observations=[SimpleNamespace(**{**vars(r), "source_code": 2}) for r in rows],
        )
    assert not acc.seen.any()


def test_atomic_in_memory_cell_and_duplicate_fold_consumption() -> None:
    acc = _acc()
    rows = _rows(acc)
    acc.ingest(target_index=0, fold_index=0, rung_index=0, observations=rows)
    fold0 = np.flatnonzero(acc.folds == 0)
    fold1 = np.flatnonzero(acc.folds == 1)
    assert acc.seen[0, :, 0, fold0].all()
    assert not acc.seen[0, :, 0, fold1].any()
    assert all(np.isfinite(acc.detected[0, p, 0, fold0]).all() for p in range(3))
    with pytest.raises(ValueError, match="duplicate"):
        acc.ingest(target_index=0, fold_index=0, rung_index=0, observations=rows)
    with pytest.raises(ValueError, match="missing"):
        acc.finalize()


def test_uniform_base_cannot_carry_nonzero_delta_or_nans() -> None:
    acc = _acc()
    rows = _rows(acc)
    contaminated = list(rows)
    contaminated[0] = SimpleNamespace(
        **{**vars(rows[0]), "normalized_delta_detected": 0.3}
    )
    with pytest.raises(ValueError, match="uniform base"):
        acc.ingest(target_index=0, fold_index=0, rung_index=0, observations=contaminated)
    contaminated[0] = SimpleNamespace(
        **{**vars(rows[0]), "normalized_delta_umi": float("nan")}
    )
    with pytest.raises(ValueError, match="nonfinite"):
        acc.ingest(target_index=0, fold_index=0, rung_index=0, observations=contaminated)
    assert not acc.seen.any()


def test_complete_256_x_3_x_6_x_104_assembly_preserves_source_robustness() -> None:
    acc = _acc()
    for target_index in range(256):
        for fold_index in range(4):
            for rung_index in range(6):
                acc.ingest(
                    target_index=target_index,
                    fold_index=fold_index, rung_index=rung_index,
                    observations=_rows(
                        acc, target_index=target_index,
                        fold_index=fold_index, rung_index=rung_index,
                    ),
                )
    result = acc.finalize()
    assert np.all(result["donor_normalized_delta_detected"][:, 0, :, :] == 0.02)
    assert np.all(result["donor_normalized_delta_detected"][:, 1, :, :] == 0.03)
    assert np.all(result["donor_normalized_delta_detected"][:, 2, :, :] == 0.04)
    assert np.all(result["donor_normalized_delta_umi"][:, 2, :, :] == 0.02)
    assert np.array_equal(result["donor_source_code"], acc.source)
    assert np.array_equal(result["target_cols"], np.arange(256))


def test_raw_burden_cannot_use_nonfull104_or_unaligned_umi() -> None:
    source, fold = _sources_folds()
    targets = np.arange(256, dtype=np.int64)
    core = np.arange(17186, dtype=np.int64)
    nnz = np.ones((104, 17186), dtype=np.int32)
    umi = np.full((104, 17186), 2, dtype=np.int32)
    stream = SimpleNamespace(
        target_cols=targets,
        target_ids=targets.astype(object),
        universe_cols=core,
        fold_by_donor=fold,
        source_by_donor=np.asarray([SOURCE_NAMES[int(s)] for s in source], dtype=object),
    )
    out = validate_donor_geometry(
        frozen_targets=targets, core_addresses=core,
        donor_nnz=nnz, donor_umi=umi,
        donor_source_code=source, fold_by_donor=fold,
        stream=stream,
    )
    assert all(x.shape[0] in (256, 17186, 104) for x in out)
    umi[0, 0] = 0
    with pytest.raises(ValueError, match="UMI >= nnz"):
        validate_donor_geometry(
            frozen_targets=targets, core_addresses=core,
            donor_nnz=nnz, donor_umi=umi,
            donor_source_code=source, fold_by_donor=fold,
            stream=stream,
        )
    umi[0, 0] = 2
    stream.target_ids = targets.astype(str)
    with pytest.raises(ValueError, match="integer molecular address"):
        validate_donor_geometry(
            frozen_targets=targets, core_addresses=core,
            donor_nnz=nnz, donor_umi=umi,
            donor_source_code=source, fold_by_donor=fold,
            stream=stream,
        )
