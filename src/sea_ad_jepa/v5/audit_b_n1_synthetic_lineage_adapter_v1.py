"""Synthetic-only corrected-source lineage adapter for PR63 crash-safe machinery.

This deliberately cannot open real FULL104 or issue an execution authority.
Its only job is to exercise actual PR63 journal and accumulator mechanics against
explicitly checked synthetic source/donor/fold/target provenance.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable, Mapping

import numpy as np

from . import audit_b_n1_crashsafe_runtime_v1 as runtime
from .audit_b_n1_cpu_burden_assembly_v1 import (
    N1DonorTensorAccumulator,
    SOURCE_NAMES, SOURCE_DONORS, FOLD_DONORS,
)
from .audit_b_n1_result_contract_v1 import N1_TARGET_COUNT


MODE = "SYNTHETIC_ONLY__NO_PHYSICAL_N1_AUTHORITY"


def _i8(value: Any, label: str, shape: tuple[int, ...] | None = None) -> np.ndarray:
    arr = np.asarray(value)
    if arr.dtype != np.int64 or not arr.flags.c_contiguous:
        raise ValueError(f"{label} must be contiguous exact int64")
    if shape is not None and arr.shape != shape:
        raise ValueError(f"{label} wrong shape: {arr.shape} != {shape}")
    return arr


def _digest(arr: np.ndarray) -> str:
    return hashlib.sha256(arr.astype("<i8", copy=False).tobytes(order="C")).hexdigest()


def _sha_root(value: str, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(
        c not in "0123456789abcdef" for c in value
    ):
        raise ValueError(f"{label} must be a frozen 64-character lowercase SHA-256")
    return value


@dataclass(frozen=True)
class SyntheticBound:
    context: dict[str, Any]
    frozen_targets: np.ndarray
    donor_source_code: np.ndarray
    fold_by_donor: np.ndarray


def bind_synthetic_lineage(
    *, frozen_targets: Any, core_addresses: Any, donor_source_code: Any,
    fold_by_donor: Any, cell_donor: Any, src_of_cell: Any,
    stream_source_by_donor: Any, donor_nnz: Any, donor_umi: Any,
    expected_cell_donor_sha256: str, expected_donor_source_sha256: str,
    source_names: tuple[str, ...], stream_root_sha256: str,
    code_root_sha256: str, parameter_root_sha256: str, rng_root_sha256: str,
) -> SyntheticBound:
    """Authenticate a self-contained synthetic stand-in; never a physical receipt.

    Expected digests act as independently pinned *test fixture* authorities.
    An actual physical adapter must instead read frozen externally reviewed
    input receipts, and independently authenticate all files.
    """
    if tuple(source_names) != tuple(SOURCE_NAMES):
        raise ValueError("source-name order differs from corrected HVS/NPH52/SEA_AD")
    source = _i8(donor_source_code, "donor_source_code", (104,))
    fold = _i8(fold_by_donor, "fold_by_donor", (104,))
    stream_source = _i8(stream_source_by_donor, "stream_source_by_donor", (104,))
    donors = _i8(cell_donor, "cell_donor")
    src = _i8(src_of_cell, "src_of_cell", donors.shape)
    core = _i8(core_addresses, "core_addresses")
    targets = _i8(frozen_targets, "frozen_targets", (N1_TARGET_COUNT,))
    if core.ndim != 1 or not np.all(np.diff(core) > 0):
        raise ValueError("core order must be one-dimensional and strictly increasing")
    if np.unique(targets).size != N1_TARGET_COUNT or not np.isin(targets, core).all():
        raise ValueError("frozen targets must be distinct members of the canonical core")
    if donors.ndim != 1 or donors.size == 0 or np.any(donors < 0) or np.any(donors >= 104):
        raise ValueError("cell donor IDs outside synthetic 104-donor registry")
    if not np.array_equal(source, stream_source):
        raise ValueError("stream donor source differs from corrected source vector")
    if not np.array_equal(source[donors], src):
        raise ValueError("cell-to-donor source invariant violated")
    if tuple(np.bincount(source, minlength=3)) != tuple(SOURCE_DONORS):
        raise ValueError("donor/source census mismatch")
    if tuple(np.bincount(fold, minlength=4)) != tuple(FOLD_DONORS):
        raise ValueError("donor/fold census mismatch")
    if np.any(source < 0) or np.any(source >= 3) or np.any(fold < 0) or np.any(fold >= 4):
        raise ValueError("invalid source or fold codes")
    nnz = _i8(donor_nnz, "donor_nnz", (104, core.size))
    umi = _i8(donor_umi, "donor_umi", (104, core.size))
    if np.any(nnz < 0) or np.any(umi < nnz):
        raise ValueError("synthetic raw-UMI statistics incompatible with detection")
    if _digest(donors) != _sha_root(expected_cell_donor_sha256, "expected donor digest"):
        raise ValueError("synthetic pass1 donor identity differs from frozen test authority")
    if _digest(source) != _sha_root(expected_donor_source_sha256, "source digest"):
        raise ValueError("synthetic corrected donor/source vector differs from frozen test authority")
    roots = {
        name: _sha_root(root, name)
        for name, root in {
            "stream_root_sha256": stream_root_sha256,
            "code_root_sha256": code_root_sha256,
            "parameter_root_sha256": parameter_root_sha256,
            "rng_root_sha256": rng_root_sha256,
        }.items()
    }
    ctx = {
        "schema": runtime.CONTEXT_SCHEMA,
        "scope": MODE,
        "source_names": list(SOURCE_NAMES),
        "donor_source_sha256": _digest(source),
        "fold_by_donor_sha256": _digest(fold),
        "cell_donor_sha256": _digest(donors),
        "src_of_cell_sha256": _digest(src),
        "core_sha256": _digest(core),
        "target_order_sha256": _digest(targets),
        "donor_nnz_sha256": _digest(nnz),
        "donor_umi_sha256": _digest(umi),
        **roots,
    }
    return SyntheticBound(ctx, targets.copy(), source.copy(), fold.copy())


def run_synthetic_journal(
    *, bound: SyntheticBound, journal_dir: Path,
    compute_unit: Callable[[int, int, int, int], list[dict[str, Any]]],
    stop_after_new_units: int | None = None,
) -> int:
    if bound.context.get("scope") != MODE:
        raise ValueError("only synthetic integration experiments are permitted")
    # The exact production accumulator validates every newly computed unit
    # BEFORE the crash-safe runtime commits it to the journal.
    validator = N1DonorTensorAccumulator(
        frozen_targets=bound.frozen_targets,
        donor_source_code=bound.donor_source_code,
        fold_by_donor=bound.fold_by_donor,
    )

    def checked(ti: int, fi: int, ri: int, target: int) -> list[dict[str, Any]]:
        rows = compute_unit(ti, fi, ri, target)
        if not isinstance(rows, list):
            raise ValueError("synthetic observations must be a list")
        validator.ingest(
            target_index=ti, fold_index=fi, rung_index=ri,
            observations=[SimpleNamespace(**r) for r in rows],
        )
        return rows

    return runtime.run_resumable_units(
        journal_dir=journal_dir, frozen_targets=bound.frozen_targets,
        compute_unit=checked, stop_after_new_units=stop_after_new_units,
        execution_context=bound.context,
    )


def finalize_synthetic_journal(
    *, bound: SyntheticBound, journal_dir: Path,
    result_artifact: Path, result_receipt: Path,
) -> dict[str, Any]:
    if bound.context.get("scope") != MODE:
        raise ValueError("only synthetic integration experiments are permitted")
    return runtime.finalize_from_journal(
        journal_dir=journal_dir,
        result_artifact=result_artifact, result_receipt=result_receipt,
        frozen_targets=bound.frozen_targets,
        donor_source_code=bound.donor_source_code,
        fold_by_donor=bound.fold_by_donor,
        execution_context=bound.context,
    )
