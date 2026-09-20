"""Read-only physical FULL104 Level-4 shakedown.

This module authenticates and exercises the real Level-4 substrate without
opening target-panel, masking-policy, protected, or training outcomes.  It does
not consume a pass1 cache and therefore cannot accidentally substitute a
historical/smaller pass1 artifact for the physical FULL104 data.
"""
from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
import re
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time
from typing import Any, Mapping

import numpy as np
import scipy.sparse as sp

FULL104_BLOCK_MANIFEST_SHA256 = "66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29"
CANONICAL_REGISTRY_SHA256 = "7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd"
OBSERVATION_STATE_SHA256 = "852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537"
EXPECTED_BLOCKS = 8915
EXPECTED_ROWS = 4_553_407
EXPECTED_DONORS = 104
EXPECTED_OPERATORS = 42
EXPECTED_ADDRESSES = 41_238
EXPECTED_SOURCES = ("HVS", "NPH52", "SEA_AD")

MANIFEST_COLUMNS = (
    "block_key",
    "source",
    "operator_index",
    "matrix_id",
    "rows",
    "nnz",
    "counts_path",
    "counts_sha256",
    "meta_path",
    "meta_sha256",
)
META_COLUMNS = (
    "selection_row",
    "canonical_cell_id",
    "donor_id",
    "expression_row",
    "primary_row_weight",
    "source_library",
)


# Narrow numeric grammar for the authenticated source_library CSV field.
# Accepts plain integers, integral decimals and legitimate scientific notation.
# Rejects underscore separators, hex/alternate syntax, NaN and Infinity at the
# syntax layer, before Decimal ever sees the token.
_SOURCE_LIBRARY_TOKEN = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$")


def _parse_source_library(raw: object, block_key: str) -> int:
    """Parse an on-disk positive integral source-library value exactly.

    Two layers. First a narrow decimal/scientific grammar, so underscore
    separators, hex and alternate syntax, NaN and Infinity are rejected as
    syntax rather than reaching Decimal. Then exact decimal semantics, so
    binary rounding cannot turn a large integer into an off-by-one.
    """

    token = str(raw).strip()
    if not _SOURCE_LIBRARY_TOKEN.match(token):
        raise ValueError(f"invalid source_library: {block_key}")
    try:
        value = Decimal(token)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"invalid source_library: {block_key}") from exc
    if not value.is_finite() or value <= 0 or value != value.to_integral_value():
        raise ValueError(f"invalid source_library: {block_key}")
    return int(value)


def _canonical_sha(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _resolve_under(root: Path, relative: str) -> Path:
    rel = Path(relative)
    if rel.is_absolute():
        raise ValueError("FULL104 manifest paths must be relative")
    resolved_root = root.resolve()
    path = (resolved_root / rel).resolve()
    try:
        path.relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError("FULL104 manifest path escapes Level-4 root") from exc
    return path


def _rss_bytes() -> int | None:
    try:
        import psutil  # type: ignore

        return int(psutil.Process().memory_info().rss)
    except Exception:
        try:
            import resource

            value = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
            # Linux reports KiB; macOS reports bytes.
            return value * 1024 if value < 10**10 else value
        except Exception:
            return None


def _gpu_memory_used_mib_for_current_pid() -> float | None:
    executable = shutil.which("nvidia-smi")
    if executable is None:
        return None
    try:
        proc = subprocess.run(
            [
                executable,
                "--query-compute-apps=pid,used_gpu_memory",
                "--format=csv,noheader,nounits",
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if proc.returncode != 0:
            return None
        import os

        pid = str(os.getpid())
        total = 0.0
        matched = False
        for line in proc.stdout.splitlines():
            parts = [item.strip() for item in line.split(",")]
            if len(parts) != 2 or parts[0] != pid:
                continue
            total += float(parts[1])
            matched = True
        return total if matched else 0.0
    except Exception:
        return None


def _load_registry(path: Path) -> tuple[str, ...]:
    if sha256_file(path) != CANONICAL_REGISTRY_SHA256:
        raise ValueError("canonical registry root mismatch")
    indices: list[int] = []
    ids: list[str] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        names = tuple(reader.fieldnames or ())
        if "molecular_address_index" not in names or "molecular_address_id" not in names:
            raise ValueError("canonical registry lacks model-facing address fields")
        for row in reader:
            indices.append(int(row["molecular_address_index"]))
            ids.append(str(row["molecular_address_id"]))
    if len(indices) != EXPECTED_ADDRESSES:
        raise ValueError("canonical registry row count mismatch")
    if indices != list(range(EXPECTED_ADDRESSES)):
        raise ValueError("canonical registry ordering mismatch")
    if any(not value for value in ids) or len(set(ids)) != EXPECTED_ADDRESSES:
        raise ValueError("canonical registry identifiers must be nonempty and unique")
    return tuple(ids)


@dataclass(frozen=True)
class Full104PhysicalShakedownReceiptV1:
    full104_block_manifest_sha256: str
    canonical_registry_sha256: str
    observation_state_sha256: str
    block_count: int
    row_count: int
    donor_count: int
    operator_count: int
    address_count: int
    source_names: tuple[str, ...]
    total_nnz: int
    elapsed_seconds: float
    rows_per_second: float
    blocks_per_second: float
    peak_rss_bytes: int | None
    peak_current_process_gpu_memory_mib: float | None
    normalization_probe_columns: tuple[int, ...]
    terminal_masking_outcomes_inspected: bool = False
    target_panel_ladder_authorized: bool = False
    protected_outcomes_authorized: bool = False
    training_authorized: bool = False

    def validate(self) -> None:
        if self.full104_block_manifest_sha256 != FULL104_BLOCK_MANIFEST_SHA256:
            raise ValueError("physical shakedown binds a different FULL104 manifest")
        if self.canonical_registry_sha256 != CANONICAL_REGISTRY_SHA256:
            raise ValueError("physical shakedown binds a different canonical registry")
        if self.observation_state_sha256 != OBSERVATION_STATE_SHA256:
            raise ValueError("physical shakedown binds a different observation state")
        if self.block_count != EXPECTED_BLOCKS:
            raise ValueError("physical shakedown block count mismatch")
        if self.row_count != EXPECTED_ROWS:
            raise ValueError("physical shakedown row count mismatch")
        if self.donor_count != EXPECTED_DONORS:
            raise ValueError("physical shakedown donor count mismatch")
        if self.operator_count != EXPECTED_OPERATORS:
            raise ValueError("physical shakedown operator count mismatch")
        if self.address_count != EXPECTED_ADDRESSES:
            raise ValueError("physical shakedown address count mismatch")
        if tuple(self.source_names) != EXPECTED_SOURCES:
            raise ValueError("physical shakedown source set mismatch")
        if self.total_nnz <= 0:
            raise ValueError("physical shakedown total_nnz must be positive")
        if not np.isfinite(self.elapsed_seconds) or self.elapsed_seconds <= 0:
            raise ValueError("physical shakedown elapsed time must be positive")
        if not np.isfinite(self.rows_per_second) or self.rows_per_second <= 0:
            raise ValueError("physical shakedown row throughput must be positive")
        if not np.isfinite(self.blocks_per_second) or self.blocks_per_second <= 0:
            raise ValueError("physical shakedown block throughput must be positive")
        if self.peak_rss_bytes is not None and self.peak_rss_bytes <= 0:
            raise ValueError("peak RSS must be positive when available")
        if (
            self.peak_current_process_gpu_memory_mib is not None
            and self.peak_current_process_gpu_memory_mib < 0
        ):
            raise ValueError("GPU memory cannot be negative")
        if not self.normalization_probe_columns:
            raise ValueError("normalization probe columns must be nonempty")
        for name in (
            "terminal_masking_outcomes_inspected",
            "target_panel_ladder_authorized",
            "protected_outcomes_authorized",
            "training_authorized",
        ):
            if getattr(self, name) is not False:
                raise ValueError(f"{name} must remain False")

    def canonical_digest(self) -> str:
        self.validate()
        payload = asdict(self)
        payload["source_names"] = list(self.source_names)
        payload["normalization_probe_columns"] = list(self.normalization_probe_columns)
        return _canonical_sha(
            {"schema": "V5_FULL104_PHYSICAL_SHAKEDOWN_RECEIPT_V1", **payload}
        )


def run_physical_shakedown(
    *,
    level4_root: Path,
    registry_path: Path,
    observation_state_path: Path,
) -> Full104PhysicalShakedownReceiptV1:
    level4_root = Path(level4_root)
    manifest_path = level4_root / "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv"
    if sha256_file(manifest_path) != FULL104_BLOCK_MANIFEST_SHA256:
        raise ValueError("FULL104 block manifest root mismatch")
    if sha256_file(observation_state_path) != OBSERVATION_STATE_SHA256:
        raise ValueError("observation-state root mismatch")
    _load_registry(registry_path)

    with manifest_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != MANIFEST_COLUMNS:
            raise ValueError("FULL104 block manifest schema mismatch")
        manifest = [dict(row) for row in reader]
    if len(manifest) != EXPECTED_BLOCKS:
        raise ValueError("FULL104 block manifest does not contain 8,915 blocks")
    if len({row["block_key"] for row in manifest}) != EXPECTED_BLOCKS:
        raise ValueError("FULL104 block manifest contains duplicate block keys")

    operator_ids = {int(row["operator_index"]) for row in manifest}
    if len(operator_ids) != EXPECTED_OPERATORS:
        raise ValueError("FULL104 manifest does not contain exactly 42 operators")
    source_names = tuple(sorted({str(row["source"]) for row in manifest}))
    if source_names != tuple(sorted(EXPECTED_SOURCES)):
        raise ValueError("FULL104 manifest source set mismatch")

    selection_seen = np.zeros(EXPECTED_ROWS, dtype=np.bool_)
    donors: set[str] = set()
    donor_source: dict[str, str] = {}
    total_rows = 0
    total_nnz = 0
    width: int | None = None
    probe_columns: tuple[int, ...] | None = None
    peak_rss = _rss_bytes()
    peak_gpu = _gpu_memory_used_mib_for_current_pid()
    start = time.perf_counter()

    for index, row in enumerate(manifest):
        counts_path = _resolve_under(level4_root, row["counts_path"])
        meta_path = _resolve_under(level4_root, row["meta_path"])
        if not counts_path.is_file() or not meta_path.is_file():
            raise ValueError(f"FULL104 block file missing: {row['block_key']}")
        if sha256_file(counts_path) != row["counts_sha256"]:
            raise ValueError(f"FULL104 counts hash mismatch: {row['block_key']}")
        if sha256_file(meta_path) != row["meta_sha256"]:
            raise ValueError(f"FULL104 metadata hash mismatch: {row['block_key']}")

        matrix = sp.load_npz(counts_path).tocsr()
        expected_rows = int(row["rows"])
        expected_nnz = int(row["nnz"])
        if matrix.shape[0] != expected_rows or matrix.nnz != expected_nnz:
            raise ValueError(f"FULL104 block geometry mismatch: {row['block_key']}")
        if width is None:
            width = int(matrix.shape[1])
            if width != EXPECTED_ADDRESSES:
                raise ValueError("FULL104 expression width does not equal 41,238 addresses")
            probe_columns = tuple(sorted({0, 1, width // 2, width - 2, width - 1}))
        elif int(matrix.shape[1]) != width:
            raise ValueError("FULL104 expression block widths disagree")
        if matrix.data.size:
            values = np.asarray(matrix.data)
            if (
                not np.all(np.isfinite(values))
                or np.any(values < 0)
                or not np.allclose(values, np.rint(values))
            ):
                raise ValueError(f"FULL104 counts are not raw nonnegative integers: {row['block_key']}")

        with meta_path.open(newline="", encoding="utf-8") as handle:
            meta_reader = csv.DictReader(handle)
            if tuple(meta_reader.fieldnames or ()) != META_COLUMNS:
                raise ValueError(f"FULL104 metadata schema mismatch: {row['block_key']}")
            selection: list[int] = []
            libraries: list[int] = []
            block_donors: list[str] = []
            for meta in meta_reader:
                selection.append(int(meta["selection_row"]))
                block_donors.append(str(meta["donor_id"]))
                expression_row = int(meta["expression_row"])
                weight = float(meta["primary_row_weight"])
                library = _parse_source_library(meta["source_library"], row["block_key"])
                if expression_row < 0:
                    raise ValueError(f"negative expression_row: {row['block_key']}")
                if not np.isfinite(weight) or weight <= 0:
                    raise ValueError(f"invalid primary_row_weight: {row['block_key']}")
                if library <= 0:
                    raise ValueError(f"invalid source_library: {row['block_key']}")
                libraries.append(library)

        sel = np.asarray(selection, dtype=np.int64)
        libs = np.asarray(libraries, dtype=np.float64)
        if sel.size != expected_rows or libs.size != expected_rows:
            raise ValueError(f"FULL104 metadata row count mismatch: {row['block_key']}")
        if np.any(sel < 0) or np.any(sel >= EXPECTED_ROWS):
            raise ValueError(f"FULL104 selection_row out of range: {row['block_key']}")
        if np.unique(sel).size != sel.size or np.any(selection_seen[sel]):
            raise ValueError("duplicate selection_row across FULL104 blocks")
        selection_seen[sel] = True

        source = str(row["source"])
        for donor in block_donors:
            if not donor:
                raise ValueError("empty donor_id in FULL104 metadata")
            prior = donor_source.setdefault(donor, source)
            if prior != source:
                raise ValueError("donor appears under multiple source identities")
            donors.add(donor)

        # Exercise the exact production sparse normalization over every
        # nonzero in the physical block.  This intentionally mirrors
        # Full104ManifestStreamV1.iter_blocks instead of probing a few columns.
        assert probe_columns is not None
        normalized_block = matrix.astype(np.float64).tocsr(copy=True)
        if normalized_block.data.size:
            data_rows = np.repeat(
                np.arange(normalized_block.shape[0], dtype=np.int64),
                np.diff(normalized_block.indptr),
            )
            normalized_block.data = np.log1p(
                normalized_block.data * (10000.0 / libs[data_rows])
            )
            if (
                not np.all(np.isfinite(normalized_block.data))
                or np.any(normalized_block.data < 0)
            ):
                raise ValueError("FULL104 log1p10K normalization produced invalid values")

        total_rows += expected_rows
        total_nnz += expected_nnz
        rss = _rss_bytes()
        if rss is not None:
            peak_rss = rss if peak_rss is None else max(peak_rss, rss)
        gpu = _gpu_memory_used_mib_for_current_pid()
        if gpu is not None:
            peak_gpu = gpu if peak_gpu is None else max(peak_gpu, gpu)

    elapsed = time.perf_counter() - start
    if total_rows != EXPECTED_ROWS or not np.all(selection_seen):
        raise ValueError("FULL104 physical stream does not close over exactly 4,553,407 rows")
    if len(donors) != EXPECTED_DONORS:
        raise ValueError("FULL104 physical stream does not contain exactly 104 donors")
    if width != EXPECTED_ADDRESSES or probe_columns is None:
        raise ValueError("FULL104 expression width was not established")

    receipt = Full104PhysicalShakedownReceiptV1(
        full104_block_manifest_sha256=FULL104_BLOCK_MANIFEST_SHA256,
        canonical_registry_sha256=CANONICAL_REGISTRY_SHA256,
        observation_state_sha256=OBSERVATION_STATE_SHA256,
        block_count=len(manifest),
        row_count=total_rows,
        donor_count=len(donors),
        operator_count=len(operator_ids),
        address_count=width,
        source_names=tuple(sorted(source_names)),
        total_nnz=total_nnz,
        elapsed_seconds=float(elapsed),
        rows_per_second=float(total_rows / elapsed),
        blocks_per_second=float(len(manifest) / elapsed),
        peak_rss_bytes=peak_rss,
        peak_current_process_gpu_memory_mib=peak_gpu,
        normalization_probe_columns=probe_columns,
    )
    receipt.validate()
    return receipt
