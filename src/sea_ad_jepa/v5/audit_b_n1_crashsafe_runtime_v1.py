"""Crash-safe deterministic N1 journal/finalizer infrastructure.

This module is deliberately outcome-blind infrastructure. It does not know how to
open FULL104, choose partners, generate masks, or compute burden. A future
source-bound physical adapter must supply already-validated unit observations.

The unit geometry is fixed at 256 targets x 4 folds x 6 rungs. Each unit is
committed as one immutable JSON file. Finalization replays units through the
existing N1 accumulator and writes a deterministic NPZ plus the frozen
AuditBN1ResultReceiptV1. Interrupted and uninterrupted synthetic executions must
therefore converge to byte-identical final artifacts.
"""
from __future__ import annotations

from dataclasses import asdict
import hashlib
import io
import json
import os
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable, Mapping
import zipfile

import numpy as np

from .audit_b_n1_cpu_burden_assembly_v1 import N1DonorTensorAccumulator
from .audit_b_n1_result_contract_v1 import (
    AuditBN1ResultReceiptV1,
    N1_TARGET_COUNT,
    N_RUNGS,
    array_sha256,
)

SCHEMA = "V5_AUDIT_B_N1_CRASHSAFE_JOURNAL_V1"
FINAL_SCHEMA = "V5_AUDIT_B_N1_CRASHSAFE_FINALIZATION_V1"
N_FOLDS = 4
EXPECTED_UNITS = N1_TARGET_COUNT * N_FOLDS * N_RUNGS


def canonical_digest(payload: Mapping[str, Any]) -> str:
    raw = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def unit_name(target_index: int, fold_index: int, rung_index: int) -> str:
    if not (0 <= target_index < N1_TARGET_COUNT):
        raise ValueError("target_index outside N1 geometry")
    if not (0 <= fold_index < N_FOLDS):
        raise ValueError("fold_index outside N1 geometry")
    if not (0 <= rung_index < N_RUNGS):
        raise ValueError("rung_index outside N1 geometry")
    return f"t{target_index:04d}_f{fold_index}_r{rung_index}.json"


def validate_unit_record(
    record: Mapping[str, Any], *, target_index: int, fold_index: int,
    rung_index: int,
) -> dict[str, Any]:
    if record.get("schema") != SCHEMA:
        raise ValueError("journal unit schema mismatch")
    expected = {
        "target_index": target_index,
        "fold_index": fold_index,
        "rung_index": rung_index,
    }
    for key, value in expected.items():
        if record.get(key) != value:
            raise ValueError(f"journal unit key drift: {key}")
    observations = record.get("observations")
    if not isinstance(observations, list) or not observations:
        raise ValueError("journal unit has no observations")
    body = {k: v for k, v in record.items() if k != "record_sha256"}
    if record.get("record_sha256") != canonical_digest(body):
        raise ValueError("journal unit self-digest mismatch")
    return dict(record)


def commit_unit(
    *, journal_dir: Path, target_index: int, fold_index: int, rung_index: int,
    target_col: int, observations: list[dict[str, Any]],
) -> Path:
    journal_dir.mkdir(parents=True, exist_ok=True)
    final = journal_dir / unit_name(target_index, fold_index, rung_index)
    if final.exists():
        existing = json.loads(final.read_text(encoding="utf-8"))
        validate_unit_record(
            existing, target_index=target_index, fold_index=fold_index,
            rung_index=rung_index,
        )
        return final

    payload: dict[str, Any] = {
        "schema": SCHEMA,
        "target_index": int(target_index),
        "target_col": int(target_col),
        "fold_index": int(fold_index),
        "rung_index": int(rung_index),
        "observations": observations,
    }
    payload["record_sha256"] = canonical_digest(payload)
    stage = final.with_suffix(".json.tmp")
    # A crash may leave an uncommitted temp file. It has no authority because
    # only the atomically renamed final path is a committed unit.
    if stage.exists():
        stage.unlink()
    fd = os.open(str(stage), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, sort_keys=True, separators=(",", ":"))
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(stage, final)
    return final


def read_unit(
    *, journal_dir: Path, target_index: int, fold_index: int, rung_index: int,
) -> dict[str, Any]:
    path = journal_dir / unit_name(target_index, fold_index, rung_index)
    if not path.is_file():
        raise ValueError(f"missing N1 journal unit: {path.name}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    return validate_unit_record(
        payload, target_index=target_index, fold_index=fold_index,
        rung_index=rung_index,
    )


def run_resumable_units(
    *, journal_dir: Path, frozen_targets: np.ndarray,
    compute_unit: Callable[[int, int, int, int], list[dict[str, Any]]],
    stop_after_new_units: int | None = None,
) -> int:
    targets = np.asarray(frozen_targets)
    if (
        targets.shape != (N1_TARGET_COUNT,)
        or not np.issubdtype(targets.dtype, np.integer)
        or np.unique(targets).size != N1_TARGET_COUNT
    ):
        raise ValueError("frozen_targets must be the exact 256 unique integer N1 order")
    if stop_after_new_units is not None and stop_after_new_units < 0:
        raise ValueError("stop_after_new_units must be nonnegative")
    committed = 0
    for ti, raw_target in enumerate(targets):
        for fi in range(N_FOLDS):
            for ri in range(N_RUNGS):
                final = journal_dir / unit_name(ti, fi, ri)
                if final.exists():
                    read_unit(
                        journal_dir=journal_dir, target_index=ti,
                        fold_index=fi, rung_index=ri,
                    )
                    continue
                if stop_after_new_units is not None and committed >= stop_after_new_units:
                    return committed
                observations = compute_unit(ti, fi, ri, int(raw_target))
                commit_unit(
                    journal_dir=journal_dir, target_index=ti,
                    fold_index=fi, rung_index=ri, target_col=int(raw_target),
                    observations=observations,
                )
                committed += 1
    return committed


def _deterministic_npy_bytes(array: np.ndarray) -> bytes:
    buf = io.BytesIO()
    np.lib.format.write_array(buf, np.asarray(array), allow_pickle=False)
    return buf.getvalue()


def write_deterministic_npz(path: Path, arrays: Mapping[str, np.ndarray]) -> None:
    stage = path.with_suffix(path.suffix + ".tmp")
    path.parent.mkdir(parents=True, exist_ok=True)
    if stage.exists():
        stage.unlink()
    with zipfile.ZipFile(stage, "w", compression=zipfile.ZIP_STORED) as zf:
        for name in sorted(arrays):
            info = zipfile.ZipInfo(f"{name}.npy", date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_STORED
            info.create_system = 0
            info.external_attr = 0
            zf.writestr(info, _deterministic_npy_bytes(np.asarray(arrays[name])))
    if path.exists():
        if sha256_file(path) != sha256_file(stage):
            raise ValueError("existing result artifact differs from deterministic journal replay")
        stage.unlink()
    else:
        os.replace(stage, path)


def finalize_from_journal(
    *, journal_dir: Path, result_artifact: Path, result_receipt: Path,
    frozen_targets: np.ndarray, donor_source_code: np.ndarray,
    fold_by_donor: np.ndarray,
) -> dict[str, Any]:
    acc = N1DonorTensorAccumulator(
        frozen_targets=frozen_targets,
        donor_source_code=donor_source_code,
        fold_by_donor=fold_by_donor,
    )
    seen_files: set[str] = set()
    for ti, raw_target in enumerate(np.asarray(frozen_targets)):
        for fi in range(N_FOLDS):
            for ri in range(N_RUNGS):
                row = read_unit(
                    journal_dir=journal_dir, target_index=ti,
                    fold_index=fi, rung_index=ri,
                )
                if int(row.get("target_col")) != int(raw_target):
                    raise ValueError("journal target identity differs from frozen target order")
                observations = [SimpleNamespace(**x) for x in row["observations"]]
                acc.ingest(
                    target_index=ti, fold_index=fi, rung_index=ri,
                    observations=observations,
                )
                seen_files.add(unit_name(ti, fi, ri))
    extras = {
        p.name for p in journal_dir.glob("t*_f*_r*.json")
        if p.name not in seen_files
    }
    if extras:
        raise ValueError("journal contains extra N1 unit files")
    if len(seen_files) != EXPECTED_UNITS:
        raise ValueError("journal does not contain the full N1 unit census")

    arrays = acc.finalize()
    write_deterministic_npz(result_artifact, arrays)
    artifact_sha = sha256_file(result_artifact)
    receipt = AuditBN1ResultReceiptV1(
        result_artifact_sha256=artifact_sha,
        target_cols_sha256=array_sha256(arrays["target_cols"], dtype="<i8"),
        donor_normalized_delta_detected_sha256=array_sha256(
            arrays["donor_normalized_delta_detected"], dtype="<f8"
        ),
        donor_normalized_delta_umi_sha256=array_sha256(
            arrays["donor_normalized_delta_umi"], dtype="<f8"
        ),
        donor_source_code_sha256=array_sha256(
            arrays["donor_source_code"], dtype="<i8"
        ),
    )
    canonical = receipt.canonical_digest()
    payload = {
        "schema": FINAL_SCHEMA,
        "result_receipt": asdict(receipt),
        "result_receipt_sha256": canonical,
        "journal_units": EXPECTED_UNITS,
        "precision_calculated": False,
        "terminal_masking_outcomes_inspected": False,
        "terminal_masking_authorized": False,
        "training_authorized": False,
    }
    stage = result_receipt.with_suffix(result_receipt.suffix + ".tmp")
    result_receipt.parent.mkdir(parents=True, exist_ok=True)
    if stage.exists():
        stage.unlink()
    encoded = json.dumps(payload, sort_keys=True, indent=2) + "\n"
    if result_receipt.exists():
        if result_receipt.read_text(encoding="utf-8") != encoded:
            raise ValueError("existing result receipt differs from deterministic journal replay")
        return payload
    fd = os.open(str(stage), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(encoded)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(stage, result_receipt)
    return payload
