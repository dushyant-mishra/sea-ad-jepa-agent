"""Prospective, metadata-only repair of the *separately named* FULL104 heavy NPZ.

Original frozen NPZ, raw count blocks and numeric sufficient statistics NEVER
change. Requires an independently reconstructed 8,915-block Level-4 metadata
census before writing anything. This is an artifact derivative + lineage
attestation, NOT new scientific qualification or permission to run Audit-B N1.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path
import secrets
import shutil
import zipfile

import numpy as np

from sea_ad_jepa.v5 import audit_b_n1_source_lineage_v1 as lineage

SCHEMA = "V5_FULL104_N1_CANONICAL_SOURCE_DERIVATIVE_V1"
REPAIRED_KEYS = frozenset(("source_names.npy", "src_of_cell.npy"))
KNOWN_FIRST_APPEARANCE = ("HVS", "SEA_AD", "NPH52")
REPAIR_STATE = "DERIVATIVE_BUILT__REQUALIFICATION_REQUIRED__N1_STOP"


def source_sha256(path: Path) -> str:
    """Normalized code hash independent of Git Windows checkout newlines."""
    raw = path.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(raw).hexdigest()


def npy_bytes(array: np.ndarray, *, allow_pickle: bool) -> bytes:
    buffer = io.BytesIO()
    np.save(buffer, array, allow_pickle=allow_pickle)
    return buffer.getvalue()


def inner_member_sha256s(path: Path) -> dict[str, str]:
    """Hash uncompressed NPY payloads, rather than trusting the enclosing ZIP."""
    hashes: dict[str, str] = {}
    with zipfile.ZipFile(path, "r") as archive:
        members = archive.infolist()
        if len(members) != len({m.filename for m in members}):
            raise ValueError("duplicate NPZ member names: ambiguous source arrays")
        if not members or any(not m.filename.endswith(".npy") for m in members):
            raise ValueError("NPZ has unexpected/empty/non-NPY members")
        for member in members:
            hasher = hashlib.sha256()
            with archive.open(member, "r") as reader:
                for chunk in iter(lambda: reader.read(8 << 20), b""):
                    hasher.update(chunk)
            hashes[member.filename] = hasher.hexdigest()
    if not REPAIRED_KEYS.issubset(hashes):
        raise ValueError("original NPZ lacks mandatory source fields")
    return hashes


def _validated_replacement(
    original: Path, level4_root: Path
) -> tuple[dict, dict[str, bytes], dict[str, str]]:
    # This replays the FULL independent metadata census, not the old
    # self-consistency check that trusted the defective stored names.
    audit = lineage.audit_original_heavy_source_lineage(
        heavy_artifact=original, level4_root=level4_root
    )
    if audit["state"] != "QUARANTINED_SOURCE_ENCODING__N1_STOP":
        raise ValueError("original artifact not in the expected quarantined state")
    if audit["source_name_order_matches"] is not False:
        raise ValueError("expected original source-name order defect was not found")
    if audit["src_of_cell_equals_donor_src_at_metadata_donor"] is not False:
        raise ValueError("expected original per-cell source defect was not found")
    if audit["stored_source_names"] != list(KNOWN_FIRST_APPEARANCE):
        raise ValueError("unexpected source-name defect; no generic blind repair")
    expected_mismatch = sum(lineage.SOURCE_CELLS[1:])
    if audit["src_of_cell_mismatch_count"] != expected_mismatch:
        raise ValueError("per-cell defect is not the known first-appearance swap")

    with np.load(original, allow_pickle=True) as archive:
        old_names = archive["source_names"]
        old_codes = archive["src_of_cell"]
        donor_src = archive["donor_src"]
        if tuple(str(x) for x in old_names) != KNOWN_FIRST_APPEARANCE:
            raise ValueError("physical source names differ from audited labels")
        if old_names.dtype != np.dtype("O") or old_names.shape != (3,):
            raise ValueError("unexpected original source-name array representation")
        if old_codes.dtype != np.int64 or old_codes.shape != (lineage.N_CELLS,):
            raise ValueError("unexpected original per-cell source representation")
        if np.any(old_codes < 0) or np.any(old_codes >= 3):
            raise ValueError("invalid original per-cell source code")
        if lineage.int64_digest(donor_src) != audit["canonical_donor_source_vector_sha256"]:
            raise ValueError("donor_src differs from metadata-verified canonical vector")
        correction = np.asarray(
            [lineage.SOURCES.index(str(name)) for name in old_names],
            dtype=np.int64,
        )
        corrected_cell_codes = correction[old_codes]
        if lineage.int64_digest(corrected_cell_codes) != audit[
            "metadata_source_vector_sha256"
        ]:
            raise ValueError("canonical remap does NOT match independently verified Level-4 metadata")
        canonical_names = np.asarray(lineage.SOURCES, dtype=old_names.dtype)
        if canonical_names.dtype != old_names.dtype or canonical_names.shape != old_names.shape:
            raise ValueError("source-name dtype/shape changed by repair")

    replacement = {
        "source_names.npy": npy_bytes(canonical_names, allow_pickle=True),
        "src_of_cell.npy": npy_bytes(corrected_cell_codes, allow_pickle=False),
    }
    return audit, replacement, {
        "corrected_per_cell_source_sha256": lineage.int64_digest(corrected_cell_codes),
        "canonical_donor_source_vector_sha256": lineage.int64_digest(donor_src),
    }


def _copy_npz_with_two_replacements(
    *, original: Path, stage: Path, replacement: dict[str, bytes],
) -> None:
    """Copy every unrelated NPY payload byte-for-byte inside a fresh ZIP."""
    with zipfile.ZipFile(original, "r") as src:
        members = src.infolist()
        if len(members) != len({m.filename for m in members}):
            raise ValueError("duplicate original NPZ members")
        with zipfile.ZipFile(
            stage, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=6,
            allowZip64=True,
        ) as dst:
            for member in members:
                meta = zipfile.ZipInfo(member.filename, date_time=(1980, 1, 1, 0, 0, 0))
                meta.compress_type = zipfile.ZIP_DEFLATED
                meta.external_attr = 0o600 << 16
                if member.filename in replacement:
                    dst.writestr(meta, replacement[member.filename], compress_type=zipfile.ZIP_DEFLATED)
                else:
                    with src.open(member, "r") as reader, dst.open(meta, "w", force_zip64=True) as writer:
                        shutil.copyfileobj(reader, writer, length=8 << 20)
    # Windows fsync requires a writable handle.
    with stage.open("rb+") as handle:
        os.fsync(handle.fileno())


def build_canonical_source_derivative(
    *,
    original: Path, level4_root: Path, out: Path, out_receipt: Path,
) -> dict:
    original = original.resolve()
    out = out.resolve()
    out_receipt = out_receipt.resolve()
    if len({original, out, out_receipt}) != 3:
        raise ValueError("original, derivative and receipt must have distinct paths")
    if out.exists() or out_receipt.exists():
        raise FileExistsError("derivative or receipt exists; refuse overwrite")
    if lineage.sha256_file(original) != lineage.ORIGINAL_HEAVY_SHA256:
        raise ValueError("original heavy NPZ physical SHA mismatch")

    audit, replacement, vector_hashes = _validated_replacement(original, level4_root)
    old_members = inner_member_sha256s(original)
    if any(key not in old_members for key in ("donor_src.npy", "donor_nnz.npy", "donor_umi.npy", "core.npy", "duniq.npy")):
        raise ValueError("original archive lacks indispensable unchanged donor/target arrays")

    out.parent.mkdir(parents=True, exist_ok=True)
    out_receipt.parent.mkdir(parents=True, exist_ok=True)
    intent = out.with_name(out.name + ".repair-intent.json")
    fd = os.open(str(intent), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump({
            "schema": "V5_N1_CANONICAL_SOURCE_REPAIR_INTENT_V1",
            "original_sha256": lineage.ORIGINAL_HEAVY_SHA256,
            "out": str(out), "no_n1_execution": True,
        }, handle, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())

    stage = out.with_name("." + out.name + ".staged-" + secrets.token_hex(8))
    _copy_npz_with_two_replacements(original=original, stage=stage, replacement=replacement)
    new_members = inner_member_sha256s(stage)
    if new_members.keys() != old_members.keys():
        raise ValueError("derivative member inventory differs from the original")
    changes = sorted(
        name for name in old_members if old_members[name] != new_members[name]
    )
    if changes != sorted(REPAIRED_KEYS):
        raise ValueError("derivative changed non-source member(s), or failed to repair both fields")
    if new_members["source_names.npy"] != hashlib.sha256(replacement["source_names.npy"]).hexdigest():
        raise ValueError("corrected source_names payload mismatch")
    if new_members["src_of_cell.npy"] != hashlib.sha256(replacement["src_of_cell.npy"]).hexdigest():
        raise ValueError("corrected src_of_cell payload mismatch")
    with np.load(stage, allow_pickle=True) as check:
        if tuple(str(x) for x in check["source_names"]) != lineage.SOURCES:
            raise ValueError("corrected source_names are not canonical")
        if check["src_of_cell"].dtype != np.int64 or (
            lineage.int64_digest(check["src_of_cell"]) != audit["metadata_source_vector_sha256"]
        ):
            raise ValueError("corrected per-cell source is not independent metadata truth")
    result_sha = lineage.sha256_file(stage)
    os.replace(stage, out)  # Crash before separate receipt leaves artifact INADMISSIBLE.
    body = {
        "schema": SCHEMA,
        "state": REPAIR_STATE,
        "original_heavy_sha256": lineage.ORIGINAL_HEAVY_SHA256,
        "corrected_derivative_sha256": result_sha,
        "full104_manifest_sha256": lineage.MANIFEST_SHA256,
        "source_lineage_audit": audit,
        "source_lineage_source_normalized_sha256": source_sha256(Path(lineage.__file__)),
        "derivative_builder_source_normalized_sha256": source_sha256(Path(__file__)),
        "old_npy_member_sha256s": old_members,
        "corrected_npy_member_sha256s": new_members,
        "changed_members": changes,
        **vector_hashes,
        "independent_six_donor_raw_count_evidence_transported": False,
        "successor_physical_binding_approved": False,
        "n1_targets_selected": False,
        "masks_executed": False,
        "burden_calculated": False,
        "precision_calculated": False,
        "training_authorized": False,
    }
    attestation = {**body, "receipt_sha256": lineage.canonical_digest(body)}
    fd = os.open(str(out_receipt), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(attestation, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    return attestation
