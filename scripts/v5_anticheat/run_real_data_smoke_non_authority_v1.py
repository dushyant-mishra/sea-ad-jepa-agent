#!/usr/bin/env python3
"""Tiny deterministic real-data mechanics smoke for prospective V5.

This script is intentionally incapable of creating production dimension,
threshold, biology, postqualification, or training authority.  It validates a
hash-locked 50K discovery transport, its frozen row identity against the full
reader-fit metadata, operator measurement support, canonical packing identity,
and the V2 representation/gradient firewall on a tiny deterministic subset.

The discovery corpus is used only as REAL_DATA_SMOKE_NON_AUTHORITY.  It is not a
substitute for FULL104 expression closure.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import sqlite3
import tempfile
import zipfile
from collections import Counter
from pathlib import Path
from typing import BinaryIO

import numpy as np
import torch

from sea_ad_jepa.v5.biology_observation_adapter_v2 import BiologyObservationAdapterV2
from sea_ad_jepa.v5.data_first_geometry import (
    evidence_telemetry,
    operator_homogeneous_microbatch_plan,
    pack_valid_tokens,
)
from sea_ad_jepa.v5.representation_firewall_v2 import validate_routing_manifest_v2


DISCOVERY_NPZ_BASENAME = "FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.npz"
FREEZE_BASENAME = "FOUNDATION_DISCOVERY_SAMPLE_FREEZE.csv"
AUDIT_BASENAME = "FOUNDATION_DISCOVERY_EXPRESSION_AUDIT.json"
BUNDLE_MANIFEST_BASENAME = "BUNDLE_SHA256_MANIFEST.csv"
SUPPORT_RELATIVE = "support/FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz"
METADATA_RELATIVE = "metadata/foundation_metadata_rows.sqlite"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def find_unique_suffix(names: list[str], suffix: str) -> str:
    matches = [name for name in names if name.endswith(suffix)]
    if len(matches) != 1:
        raise RuntimeError(f"expected exactly one member ending {suffix!r}, got {matches}")
    return matches[0]


class ConcatenatedParts(io.RawIOBase):
    """Seekable read-only virtual concatenation without materializing the outer ZIP."""

    def __init__(self, paths: list[Path]):
        super().__init__()
        if not paths:
            raise ValueError("at least one part is required")
        self.paths = paths
        self.sizes = [path.stat().st_size for path in paths]
        self.starts = []
        total = 0
        for size in self.sizes:
            self.starts.append(total)
            total += size
        self.total = total
        self.pos = 0
        self.handles: list[BinaryIO] = [path.open("rb") for path in paths]

    def readable(self) -> bool:
        return True

    def seekable(self) -> bool:
        return True

    def tell(self) -> int:
        return self.pos

    def seek(self, offset: int, whence: int = os.SEEK_SET) -> int:
        if whence == os.SEEK_SET:
            target = offset
        elif whence == os.SEEK_CUR:
            target = self.pos + offset
        elif whence == os.SEEK_END:
            target = self.total + offset
        else:
            raise ValueError("invalid whence")
        if target < 0:
            raise ValueError("negative seek")
        self.pos = min(target, self.total)
        return self.pos

    def readinto(self, b) -> int:
        data = self.read(len(b))
        n = len(data)
        b[:n] = data
        return n

    def read(self, size: int = -1) -> bytes:
        if self.pos >= self.total:
            return b""
        if size is None or size < 0:
            size = self.total - self.pos
        remaining = min(size, self.total - self.pos)
        out = bytearray()
        while remaining:
            part_index = max(i for i, start in enumerate(self.starts) if start <= self.pos)
            local = self.pos - self.starts[part_index]
            take = min(remaining, self.sizes[part_index] - local)
            handle = self.handles[part_index]
            handle.seek(local)
            chunk = handle.read(take)
            if len(chunk) != take:
                raise IOError("short read from discovery transport part")
            out.extend(chunk)
            self.pos += take
            remaining -= take
        return bytes(out)

    def close(self) -> None:
        for handle in getattr(self, "handles", []):
            handle.close()
        super().close()


def assembled_sha256(parts: list[Path]) -> tuple[int, str]:
    h = hashlib.sha256()
    total = 0
    for path in parts:
        with path.open("rb") as f:
            for block in iter(lambda: f.read(8 << 20), b""):
                total += len(block)
                h.update(block)
    return total, h.hexdigest()


def bundle_manifest(archive: zipfile.ZipFile) -> dict[str, tuple[int, str]]:
    name = find_unique_suffix(archive.namelist(), BUNDLE_MANIFEST_BASENAME)
    rows = csv.DictReader(io.StringIO(archive.read(name).decode("utf-8")))
    out: dict[str, tuple[int, str]] = {}
    for row in rows:
        rel = row.get("relative_path") or row.get("path") or row.get("file")
        size = row.get("size_bytes") or row.get("bytes") or row.get("size")
        digest = row.get("sha256") or row.get("sha_256")
        if rel and size and digest:
            out[str(rel)] = (int(size), str(digest))
    if SUPPORT_RELATIVE not in out or METADATA_RELATIVE not in out:
        raise RuntimeError("bundle manifest is missing support or metadata authority")
    return out


def read_npy_prefix(npz_path: Path, member: str, count: int) -> np.ndarray:
    with zipfile.ZipFile(npz_path) as archive, archive.open(member) as stream:
        major, minor = np.lib.format.read_magic(stream)
        if major == 1:
            shape, fortran, dtype = np.lib.format.read_array_header_1_0(stream)
        elif major in (2, 3):
            shape, fortran, dtype = np.lib.format.read_array_header_2_0(stream)
        else:
            raise RuntimeError(f"unsupported npy version {major}.{minor}")
        if fortran:
            raise RuntimeError(f"{member} unexpectedly uses Fortran order")
        dtype = np.dtype(dtype)
        if count > int(np.prod(shape)):
            raise RuntimeError(f"requested prefix exceeds {member} length")
        payload = stream.read(dtype.itemsize * count)
        if len(payload) != dtype.itemsize * count:
            raise RuntimeError(f"short payload while reading {member}")
        return np.frombuffer(payload, dtype=dtype, count=count).copy()


def summarize_rows(dense: np.ndarray, support_mask: np.ndarray) -> np.ndarray:
    values = dense[:, support_mask]
    detected = values > 0
    width = values.shape[1]
    if width < 1:
        raise RuntimeError("summary support cannot be empty")
    mean = values.mean(axis=1)
    rms = np.sqrt(np.square(values).mean(axis=1))
    maximum = values.max(axis=1)
    detection_fraction = detected.sum(axis=1) / width
    return np.column_stack([mean, rms, maximum, detection_fraction]).astype(np.float32)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--discovery-part", action="append", type=Path, required=True)
    p.add_argument("--expected-assembled-sha256", required=True)
    p.add_argument("--expression-meta-zip", type=Path, required=True)
    p.add_argument("--expected-expression-meta-sha256", required=True)
    p.add_argument("--calibration-zip", type=Path, required=True)
    p.add_argument("--expected-calibration-sha256", required=True)
    p.add_argument("--metadata-sqlite", type=Path, required=True)
    p.add_argument("--smoke-cells", type=int, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()

    if a.smoke_cells < 2:
        raise ValueError("smoke-cells must be >=2 for packing-order mechanics")
    parts = list(a.discovery_part)
    if len(parts) != 2:
        raise ValueError("this frozen transport requires exactly two ordered discovery parts")
    if any(not path.is_file() for path in parts):
        raise FileNotFoundError("a discovery transport part is missing")

    expression_meta_sha = sha256_file(a.expression_meta_zip)
    calibration_sha = sha256_file(a.calibration_zip)
    if expression_meta_sha != a.expected_expression_meta_sha256:
        raise RuntimeError("expression metadata ZIP SHA mismatch")
    if calibration_sha != a.expected_calibration_sha256:
        raise RuntimeError("calibration bundle SHA mismatch")
    assembled_size, assembled_sha = assembled_sha256(parts)
    if assembled_sha != a.expected_assembled_sha256:
        raise RuntimeError("assembled discovery transport SHA mismatch")

    with zipfile.ZipFile(a.expression_meta_zip) as meta_zip:
        freeze_name = find_unique_suffix(meta_zip.namelist(), FREEZE_BASENAME)
        audit_name = find_unique_suffix(meta_zip.namelist(), AUDIT_BASENAME)
        freeze_bytes = meta_zip.read(freeze_name)
        audit = json.loads(meta_zip.read(audit_name).decode("utf-8"))
    freeze_sha = hashlib.sha256(freeze_bytes).hexdigest()
    if freeze_sha != audit["freeze_sha256"]:
        raise RuntimeError("frozen discovery-row CSV SHA mismatch")
    freeze_rows = list(csv.DictReader(io.StringIO(freeze_bytes.decode("utf-8"))))
    if len(freeze_rows) != int(audit["cells"]):
        raise RuntimeError("freeze/audit row count mismatch")

    stable_keys = [int(row["stable_key"]) for row in freeze_rows]
    composite_rows = [(row["sample"], int(row["sample_row"])) for row in freeze_rows]
    sample_rows = [int(row["sample_row"]) for row in freeze_rows]
    if len(set(stable_keys)) != len(stable_keys):
        raise RuntimeError("stable_key is not unique in frozen discovery rows")
    if max(stable_keys) >= 2**63 or min(stable_keys) < 0:
        raise RuntimeError("stable_key cannot be represented by V5 torch.int64 keyed RNG")
    if len(set(composite_rows)) != len(composite_rows):
        raise RuntimeError("(sample,sample_row) is not unique")
    # A and B both use sample_row 0..24999.  The smoke records this explicitly
    # so no later reader can accidentally promote sample_row to a global key.
    sample_row_globally_unique = len(set(sample_rows)) == len(sample_rows)

    with zipfile.ZipFile(a.calibration_zip) as cal_zip:
        manifest = bundle_manifest(cal_zip)
        support_name = find_unique_suffix(cal_zip.namelist(), SUPPORT_RELATIVE)
        support_bytes = cal_zip.read(support_name)
    support_size, support_expected_sha = manifest[SUPPORT_RELATIVE]
    support_sha = hashlib.sha256(support_bytes).hexdigest()
    if len(support_bytes) != support_size or support_sha != support_expected_sha:
        raise RuntimeError("operator-address observation-state member fails bundle manifest")
    support = np.load(io.BytesIO(support_bytes), allow_pickle=False)
    states = np.asarray(support["states"], dtype=np.uint8)
    operator_index = np.asarray(support["operator_index"], dtype=np.int32)
    matrix_id = np.asarray(support["matrix_id"])
    address_index = np.asarray(support["molecular_address_index"], dtype=np.int32)
    if states.ndim != 2 or not np.array_equal(operator_index, np.arange(states.shape[0])):
        raise RuntimeError("operator observation state has invalid operator identity")
    if not np.array_equal(address_index, np.arange(states.shape[1], dtype=np.int32)):
        raise RuntimeError("operator observation state has invalid address identity")

    metadata_size, metadata_expected_sha = manifest[METADATA_RELATIVE]
    metadata_sha = sha256_file(a.metadata_sqlite)
    if a.metadata_sqlite.stat().st_size != metadata_size or metadata_sha != metadata_expected_sha:
        raise RuntimeError("metadata SQLite fails bundle manifest identity")

    con = sqlite3.connect(f"file:{a.metadata_sqlite}?mode=ro&immutable=1", uri=True)
    cur = con.cursor()
    columns = (
        "source,matrix_id,operator_index,local_row,donor_id,cell_id,native_class,"
        "broad_class,support_fingerprint,stable_key,in_original_t1,partition"
    )
    sql = f"select {columns} from cells where matrix_id=? and local_row=?"
    for global_row, row in enumerate(freeze_rows):
        got = cur.execute(sql, (row["matrix_id"], int(row["local_row"]))).fetchone()
        expected = (
            row["source"],
            row["matrix_id"],
            int(row["operator_index"]),
            int(row["local_row"]),
            row["donor_id"],
            row["cell_id"],
            row["native_class"],
            row["broad_class"],
            row["support_fingerprint"],
            int(row["stable_key"]),
            int(row["in_original_t1"]),
            "reader_fit",
        )
        if got != expected:
            raise RuntimeError(f"freeze/full-metadata identity mismatch at global row {global_row}")
    con.close()

    # Derive a tiny operator-homogeneous subset from frozen order, not biology.
    operator_counts = Counter(int(row["operator_index"]) for row in freeze_rows)
    chosen_operator = None
    for row in freeze_rows:
        op = int(row["operator_index"])
        if operator_counts[op] >= a.smoke_cells:
            chosen_operator = op
            break
    if chosen_operator is None:
        raise RuntimeError("no operator can supply requested smoke cell count")
    chosen = [
        (global_row, row)
        for global_row, row in enumerate(freeze_rows)
        if int(row["operator_index"]) == chosen_operator
    ][: a.smoke_cells]
    if any(row["matrix_id"] != str(matrix_id[chosen_operator]) for _, row in chosen):
        raise RuntimeError("freeze/support matrix identity mismatch")

    with ConcatenatedParts(parts) as virtual_zip:
        with zipfile.ZipFile(virtual_zip) as discovery_zip:
            inner_name = find_unique_suffix(discovery_zip.namelist(), DISCOVERY_NPZ_BASENAME)
            with tempfile.NamedTemporaryFile(prefix="jepa_real_smoke_", suffix=".npz", delete=False) as tmp:
                inner_path = Path(tmp.name)
                h = hashlib.sha256()
                with discovery_zip.open(inner_name) as src:
                    while True:
                        block = src.read(8 << 20)
                        if not block:
                            break
                        tmp.write(block)
                        h.update(block)
                inner_sha = h.hexdigest()
    try:
        if inner_sha != audit["output_sha256"]:
            raise RuntimeError("inner discovery expression NPZ SHA mismatch")
        with np.load(inner_path, allow_pickle=False) as expression_npz:
            shape = tuple(map(int, expression_npz["shape"]))
            fmt = expression_npz["format"].item().decode("ascii")
            indptr = np.asarray(expression_npz["indptr"], dtype=np.int32)
        if shape != (int(audit["cells"]), int(audit["addresses"])) or fmt != "csr":
            raise RuntimeError("discovery expression structure disagrees with audit")
        if len(indptr) != shape[0] + 1 or int(indptr[-1]) != int(audit["nnz"]):
            raise RuntimeError("discovery CSR pointer/nnz disagreement")
        max_row = max(global_row for global_row, _ in chosen)
        prefix_nnz = int(indptr[max_row + 1])
        indices = read_npy_prefix(inner_path, "indices.npy", prefix_nnz).astype(np.int32, copy=False)
        data = read_npy_prefix(inner_path, "data.npy", prefix_nnz).astype(np.float64, copy=False)
    finally:
        inner_path.unlink(missing_ok=True)

    dense = np.zeros((a.smoke_cells, shape[1]), dtype=np.float32)
    measurement_mask = states[chosen_operator] == 1
    if not measurement_mask.any():
        raise RuntimeError("chosen operator has no measured-scalar addresses")
    real_row_metrics = []
    for local_smoke_row, (global_row, row) in enumerate(chosen):
        start, stop = int(indptr[global_row]), int(indptr[global_row + 1])
        idx = indices[start:stop]
        values = data[start:stop]
        if len(idx) and not np.all(idx[1:] >= idx[:-1]):
            raise RuntimeError("CSR indices are not sorted")
        if not np.isfinite(values).all() or np.any(values <= 0):
            raise RuntimeError("sparse stored expression must be finite and positive")
        bad = idx[~measurement_mask[idx]]
        if len(bad):
            raise RuntimeError(
                f"expression/support mismatch: row {global_row} has nonzero outside MEASURED_SCALAR"
            )
        dense[local_smoke_row, idx] = values.astype(np.float32)
        real_row_metrics.append(
            {
                "global_freeze_row": global_row,
                "sample": row["sample"],
                "sample_row": int(row["sample_row"]),
                "stable_key": int(row["stable_key"]),
                "nnz": int(len(idx)),
            }
        )

    # Hide exactly one measured address per cell solely to exercise identity-safe
    # query packing.  This is not a production mask fraction or threshold.
    measured_ids = np.flatnonzero(measurement_mask)
    hidden = np.zeros_like(dense, dtype=bool)
    hidden_ids = []
    for row_index, (_, row) in enumerate(chosen):
        payload = f"JEPA_V5_REAL_SMOKE_ONLY|{row['stable_key']}".encode("ascii")
        slot = int.from_bytes(hashlib.sha256(payload).digest()[:8], "big") % len(measured_ids)
        gene = int(measured_ids[slot])
        hidden[row_index, gene] = True
        hidden_ids.append(gene)
    measured_matrix = np.broadcast_to(measurement_mask, dense.shape).copy()
    valid = measured_matrix & ~hidden
    if np.any(hidden & ~measured_matrix):
        raise RuntimeError("smoke hidden target escaped measured support")

    expression_t = torch.from_numpy(dense)
    valid_t = torch.from_numpy(valid)
    packed = pack_valid_tokens(expression_t, valid_t)
    reverse = torch.arange(a.smoke_cells - 1, -1, -1)
    packed_reverse = pack_valid_tokens(expression_t[reverse], valid_t[reverse])
    inverse = torch.argsort(reverse)
    if not torch.equal(packed.canonical_gene_ids, packed_reverse.canonical_gene_ids[inverse]):
        raise RuntimeError("packing order changed canonical gene identity")
    if not torch.equal(packed.expression, packed_reverse.expression[inverse]):
        raise RuntimeError("packing order changed expression payload")

    measured_count = int(measurement_mask.sum())
    packing_capacity = max(1, a.smoke_cells // 2)
    packing_plan = operator_homogeneous_microbatch_plan(
        [chosen_operator] * a.smoke_cells,
        {chosen_operator: measured_count},
        max_teacher_tokens_per_microbatch=measured_count * packing_capacity,
    )

    common_core = (states == 1).all(axis=0)
    if int(common_core.sum()) < 1:
        raise RuntimeError("common measured core is empty")
    student_state = summarize_rows(dense, measurement_mask)
    teacher_state = summarize_rows(dense, common_core)
    observation_features = np.column_stack(
        [
            np.full(a.smoke_cells, measured_count / shape[1], dtype=np.float32),
            (dense[:, measurement_mask] > 0).mean(axis=1).astype(np.float32),
            dense[:, measurement_mask].mean(axis=1).astype(np.float32),
        ]
    )
    perturbed_dense = dense.copy()
    for row_index, gene in enumerate(hidden_ids):
        perturbed_dense[row_index, gene] = 0.0
    perturbed_student_state = summarize_rows(perturbed_dense, measurement_mask)

    torch.manual_seed(20260910)
    adapter = BiologyObservationAdapterV2(
        state_width=student_state.shape[1],
        observation_feature_width=observation_features.shape[1],
        observation_width=observation_features.shape[1],
    ).eval()
    with torch.no_grad():
        baseline = adapter(
            student_biology_state=torch.from_numpy(student_state),
            teacher_common_core_state=torch.from_numpy(teacher_state),
            observation_features=torch.from_numpy(observation_features),
        )
        perturbed = adapter(
            student_biology_state=torch.from_numpy(perturbed_student_state),
            teacher_common_core_state=torch.from_numpy(teacher_state),
            observation_features=torch.from_numpy(observation_features),
        )
    if not all(
        bool(torch.isfinite(t).all())
        for t in (
            baseline.z_bio_prediction,
            baseline.z_bio_anchor,
            baseline.z_obs,
            perturbed.z_bio_prediction,
            perturbed.z_obs,
        )
    ):
        raise RuntimeError("adapter smoke produced nonfinite output")

    firewall = validate_routing_manifest_v2(
        {
            "z_bio_direct_fields": ["common_core_expression", "common_core_detection"],
            "z_obs_direct_fields": [
                "measurement_mask",
                "depth",
                "detected_genes",
                "operator_support_state",
            ],
            "common_core_anchor_present": True,
            "native_support_biology_route": "PREDICT_COMMON_CORE_ANCHORED_Z_BIO",
            "observation_gradient_into_biology_allowed": False,
            "categorical_identity_embeddings_allowed": False,
            "same_cell_interventions": [
                "SUPPORT_FAMILY",
                "MASK_IDENTITY",
                "EVIDENCE_FRACTION",
                "MEASUREMENT_DEPTH",
            ],
            "objective_inputs": {
                "BASE_JEPA_CELL_STATE": ["z_bio"],
                "RELATIONAL_GEOMETRY": ["z_bio"],
                "BIOLOGICAL_CHECKPOINT_SELECTION": ["z_bio"],
                "DOWNSTREAM_BIOLOGY_READOUT": ["z_bio"],
                "GENE_LEDGER_RECONSTRUCTION": ["z_bio", "z_obs"],
            },
            "objective_gradient_targets": {
                "BASE_JEPA_CELL_STATE": ["z_bio"],
                "RELATIONAL_GEOMETRY": ["z_bio"],
                "BIOLOGICAL_CHECKPOINT_SELECTION": [],
                "DOWNSTREAM_BIOLOGY_READOUT": [],
                "GENE_LEDGER_RECONSTRUCTION": ["z_obs"],
            },
        }
    )

    part_sha256 = [sha256_file(path) for path in parts]
    implementation_sha256 = {
        "smoke_script": sha256_file(Path(__file__)),
        "representation_firewall_v2": sha256_file(
            Path(__file__).resolve().parents[2] / "src" / "sea_ad_jepa" / "v5" / "representation_firewall_v2.py"
        ) if (Path(__file__).resolve().parents[2] / "src" / "sea_ad_jepa" / "v5" / "representation_firewall_v2.py").is_file() else None,
        "biology_observation_adapter_v2": sha256_file(
            Path(__file__).resolve().parents[2] / "src" / "sea_ad_jepa" / "v5" / "biology_observation_adapter_v2.py"
        ) if (Path(__file__).resolve().parents[2] / "src" / "sea_ad_jepa" / "v5" / "biology_observation_adapter_v2.py").is_file() else None,
    }

    result = {
        "schema": "JEPA_V5_REAL_DATA_SMOKE_NON_AUTHORITY_V1",
        "status": "PASS_REAL_DATA_SMOKE_NON_AUTHORITY_MECHANICS_ONLY",
        "scope": "tiny deterministic hash-locked discovery subset; NOT FULL104 closure",
        "inputs": {
            "discovery_parts": [
                {"path": str(path), "sha256": digest}
                for path, digest in zip(parts, part_sha256)
            ],
            "assembled_discovery_size_bytes": assembled_size,
            "assembled_discovery_sha256": assembled_sha,
            "inner_expression_npz_sha256": inner_sha,
            "expression_meta_zip_sha256": expression_meta_sha,
            "freeze_sha256": freeze_sha,
            "calibration_bundle_sha256": calibration_sha,
            "support_member_sha256": support_sha,
            "metadata_sqlite_sha256": metadata_sha,
        },
        "implementation": {
            "sha256": implementation_sha256,
            "note": "Fingerprints describe the exact local code used for this non-authority smoke; branch publication is a separate provenance event.",
        },
        "identity": {
            "freeze_rows_verified_against_full_reader_metadata": len(freeze_rows),
            "stable_key_unique": True,
            "stable_key_torch_int64_compatible": True,
            "sample_plus_sample_row_unique": True,
            "sample_row_globally_unique": sample_row_globally_unique,
            "sample_row_alias_trap_detected": not sample_row_globally_unique,
            "sample_counts": dict(sorted(Counter(row["sample"] for row in freeze_rows).items())),
        },
        "expression": {
            "shape": list(shape),
            "nnz": int(audit["nnz"]),
            "format": fmt,
            "chosen_operator": chosen_operator,
            "chosen_matrix_id": str(matrix_id[chosen_operator]),
            "chosen_rows": real_row_metrics,
            "all_smoke_nonzeros_within_measured_scalar_support": True,
            "measured_scalar_addresses_chosen_operator": measured_count,
            "common_measured_core_addresses": int(common_core.sum()),
        },
        "mask_and_packing": {
            "smoke_cells": a.smoke_cells,
            "hidden_targets_per_cell": 1,
            "hidden_gene_ids": hidden_ids,
            "packed_valid_tokens_per_cell": int(packed.expression.shape[1]),
            "reverse_order_replay_exact": True,
            "microbatch_plan": [list(batch) for batch in packing_plan],
            "evidence_telemetry": evidence_telemetry(
                measured_count=measured_count,
                hidden_count=1,
                vocabulary_size=shape[1],
            ),
        },
        "representation_firewall": firewall,
        "adapter_forward": {
            "smoke_summary_state_width_non_authority": int(student_state.shape[1]),
            "observation_feature_width_non_authority": int(observation_features.shape[1]),
            "z_bio_shape": list(baseline.z_bio_prediction.shape),
            "z_obs_shape": list(baseline.z_obs.shape),
            "mask_identity_perturbation_executed": True,
            "thresholds_applied": False,
            "biology_interpretation_permitted": False,
        },
        "runtime": {
            "torch_version": torch.__version__,
            "cuda_available": torch.cuda.is_available(),
            "protected_gradient_gpu_step": (
                "NOT_RUN_CPU_RUNTIME" if not torch.cuda.is_available() else "NOT_RUN_BY_THIS_SMOKE"
            ),
        },
        "production_dimensions_set": False,
        "production_thresholds_set": False,
        "biology_conclusions_created": False,
        "shortcut_superiority_authority_created": False,
        "postqualification_created": False,
        "full104_expression_binding_closed": False,
        "training_authorized": False,
    }
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
