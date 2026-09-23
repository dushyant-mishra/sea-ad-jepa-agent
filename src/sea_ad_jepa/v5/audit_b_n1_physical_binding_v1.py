"""CPU-only, outcome-blind FULL104 N1 physical aggregate/split binding.

This is an input authenticator, NOT the N1 executor. The known heavy NPZ contains
both donor_nnz and donor_umi; the latter's physical semantics were independently
checked on six complete donor rows in the immutable PR #59 qualification receipt.
The raw aggregate, source/fold vectors and address order are all checked BY VALUE.
No mask or policy burden is computed here. No generated result authorizes N1.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

import numpy as np

HEAVY_ARTIFACT_SHA256 = "f77dff47df71e2b97895f6e850db4d2a2ebdab441d195dedf91f582b4d53b5ae"
DONOR_UMI_QUALIFICATION_FILE_SHA256 = (
    "bbd2b95b882f52c313a3623bab55e5d7ff6562cdba27e48f9c84009075cf713d"
)
SPLIT_RECEIPT_FILE_SHA256 = (
    "56f045d7dc80fde7e30c97632c1d109286e4b8f9f033b77476521c2822980585"
)
SPLIT_RECEIPT_CANONICAL_SHA256 = (
    "5d616c9c509d8224d15d6e8c163ca38b4b5140a44fdab4c2fa00efad7a8f01e4"
)
MANIFEST_SHA256 = "66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29"
CORE_SIZE = 17_186
N_DONORS = 104
N_LEDGER = 41_238
MAX_FLOAT64_EXACT_INT = 2**53 - 1  # The existing assembler converts counts to float64.
SOURCE_NAMES = ("HVS", "NPH52", "SEA_AD")
EXPECTED_SOURCE_COUNTS = (41, 17, 46)
EXPECTED_FOLD_COUNTS = (28, 26, 25, 25)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def int64_digest(arr: np.ndarray) -> str:
    x = np.asarray(arr)
    if x.dtype != np.int64:
        raise ValueError("frozen array must be int64 without coercion")
    return hashlib.sha256(np.ascontiguousarray(x, dtype="<i8").tobytes()).hexdigest()


def donor_order_digest(duniq: list[str]) -> str:
    return hashlib.sha256("\x1f".join(duniq).encode("utf-8")).hexdigest()


def canonical_digest(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"),
                                    ensure_ascii=True, allow_nan=False).encode("utf-8")).hexdigest()


def validate_bound_arrays(
    *,
    core: np.ndarray,
    duniq: list[str],
    donor_src: np.ndarray,
    donor_nnz: np.ndarray,
    donor_umi: np.ndarray,
    source_names: list[str],
    independent_receipt: Mapping[str, Any],
    split_receipt: Mapping[str, Any],
) -> dict[str, str]:
    """Pure testable value-binding; production loader separately pins actual bytes."""
    for name, arr, shape in (
        ("core", core, (CORE_SIZE,)),
        ("donor_src", donor_src, (N_DONORS,)),
        ("donor_nnz", donor_nnz, (N_DONORS, CORE_SIZE)),
        ("donor_umi", donor_umi, (N_DONORS, CORE_SIZE)),
    ):
        if not isinstance(arr, np.ndarray) or arr.dtype != np.int64 or arr.shape != shape:
            raise ValueError(f"{name} must be exact frozen int64 geometry {shape}")
    if np.any(core < 0) or np.any(core >= N_LEDGER) or not np.all(np.diff(core) > 0):
        raise ValueError("strict-core order/range is invalid")
    if len(duniq) != N_DONORS or duniq != sorted(set(duniq)):
        raise ValueError("donor identity/order is not the sorted unique FULL104 registry")
    if tuple(source_names) != SOURCE_NAMES:
        raise ValueError("source-name ordering differs from frozen HVS/NPH52/SEA_AD")
    if not np.array_equal(np.bincount(donor_src, minlength=3), EXPECTED_SOURCE_COUNTS):
        raise ValueError("FULL104 donor/source counts are inconsistent")
    if np.any(donor_nnz < 0) or np.any(donor_umi < donor_nnz):
        raise ValueError("detected/UMI counts must be nonnegative with raw UMI >= detected")

    if independent_receipt.get("verdict") != "DONOR_UMI_INDEPENDENTLY_QUALIFIED":
        raise ValueError("independent qualification receipt does not assert qualification")
    if independent_receipt.get("artifact_sha256") != HEAVY_ARTIFACT_SHA256:
        raise ValueError("independent qualification binds the wrong heavy artifact")
    if independent_receipt.get("block_manifest_sha256") != MANIFEST_SHA256:
        raise ValueError("independent qualification binds the wrong FULL104 manifest")
    if independent_receipt.get("donors_checked") is None or len(independent_receipt["donors_checked"]) != 6:
        raise ValueError("qualification must record exactly six sampled donor IDs")
    if independent_receipt.get("donor_nnz_exact_match") is not True or independent_receipt.get("donor_umi_exact_match") is not True:
        raise ValueError("independent donor row comparison was not an exact match")
    if independent_receipt.get("comparison_tolerance") != "none; exact integer equality":
        raise ValueError("qualification tolerance was modified")
    if independent_receipt.get("blocks_verified") != 8915 or independent_receipt.get("blocks_containing_subset") != 387:
        raise ValueError("qualified metadata/count coverage differs from frozen evidence")
    if independent_receipt.get("cells_accounted_exactly_once") != 4_553_407:
        raise ValueError("qualified cell-accounting closure differs from FULL104")
    if independent_receipt.get("n1_burden_calculated") is not False or independent_receipt.get("training_authorized") is not False:
        raise ValueError("independent qualification has inappropriate outcome/training status")

    orders = {
        "strict_core_order_sha256": int64_digest(core),
        "donor_order_sha256": donor_order_digest(duniq),
        "donor_source_vector_sha256": int64_digest(donor_src),
    }
    for name, digest in orders.items():
        if independent_receipt.get(name) != digest:
            raise ValueError(f"{name} differs from independently qualified physical array")

    if split_receipt.get("receipt_sha256") != SPLIT_RECEIPT_CANONICAL_SHA256:
        raise ValueError("outer split has the wrong frozen canonical digest")
    if split_receipt.get("donor_ids") != duniq:
        raise ValueError("split donor identity/order differs from authenticated heavy NPZ")
    split_source = np.asarray(split_receipt.get("donor_source_code"))
    split_fold = np.asarray(split_receipt.get("fold_by_donor"))
    if not np.array_equal(split_source, donor_src):
        raise ValueError("split donor source VECTOR disagrees with heavy aggregate")
    if (split_fold.shape != (N_DONORS,) or not np.issubdtype(split_fold.dtype, np.integer)
            or np.any(split_fold < 0) or np.any(split_fold > 3)
            or not np.array_equal(np.bincount(split_fold, minlength=4), EXPECTED_FOLD_COUNTS)):
        raise ValueError("outer split donor fold vector is invalid")
    # Source-by-fold grid catches coordinated value drift not detectable by histograms.
    expected_grid = ((11, 10, 10, 10), (5, 4, 4, 4), (12, 12, 11, 11))
    for s, row in enumerate(expected_grid):
        actual = tuple(int(np.count_nonzero((donor_src == s) & (split_fold == f))) for f in range(4))
        if actual != row:
            raise ValueError("donor source-by-fold table differs from frozen split")
    # Existing N1 assembler converts to float64, so fail closed rather than round
    # a legitimate high-count integer into a different scientific quantity.
    if np.any(donor_nnz > MAX_FLOAT64_EXACT_INT) or np.any(donor_umi > MAX_FLOAT64_EXACT_INT):
        raise ValueError("donor raw counts exceed exact float64 conversion range")
    for row in donor_umi:
        if sum(int(v) for v in row) > MAX_FLOAT64_EXACT_INT:
            raise ValueError("donor UMI row total exceeds exact float64 accumulation range")
    return {
        **orders,
        "donor_nnz_array_sha256": int64_digest(donor_nnz),
        "donor_umi_array_sha256": int64_digest(donor_umi),
        "fold_by_donor_sha256": int64_digest(split_fold.astype(np.int64, copy=False)),
    }


def inspect_physical_inputs(
    *, heavy_artifact: Path, independent_receipt: Path, split_receipt: Path,
) -> dict[str, Any]:
    """Read only named authenticated inputs. Never open the Level-4 count blocks."""
    for path, expected, role in (
        (heavy_artifact, HEAVY_ARTIFACT_SHA256, "heavy artifact"),
        (independent_receipt, DONOR_UMI_QUALIFICATION_FILE_SHA256, "donor UMI qualification"),
        (split_receipt, SPLIT_RECEIPT_FILE_SHA256, "frozen split receipt"),
    ):
        if sha256_file(path) != expected:
            raise ValueError(f"{role} physical file SHA-256 mismatch")
    independent = json.loads(independent_receipt.read_text(encoding="utf-8"))
    split = json.loads(split_receipt.read_text(encoding="utf-8"))
    with np.load(heavy_artifact, allow_pickle=True) as z:
        roles = ("core", "duniq", "donor_src", "source_names", "donor_nnz", "donor_umi")
        if any(role not in z.files for role in roles):
            raise ValueError("heavy artifact lacks a mandatory N1 physical input")
        core = z["core"]
        duniq = [str(x) for x in z["duniq"]]
        donor_src = z["donor_src"]
        source_names = [str(x) for x in z["source_names"]]
        nnz = z["donor_nnz"]
        umi = z["donor_umi"]
        binding = validate_bound_arrays(
            core=core, duniq=duniq, donor_src=donor_src, donor_nnz=nnz,
            donor_umi=umi, source_names=source_names,
            independent_receipt=independent, split_receipt=split,
        )
    payload = {
        "schema": "V5_FULL104_AUDIT_B_N1_PHYSICAL_INPUT_PREFLIGHT_V1",
        "state": "READY_FOR_INDEPENDENT_REVIEW__N1_NOT_EXECUTED",
        "heavy_artifact_sha256": HEAVY_ARTIFACT_SHA256,
        "independent_qualifier_file_sha256": DONOR_UMI_QUALIFICATION_FILE_SHA256,
        "outer_split_file_sha256": SPLIT_RECEIPT_FILE_SHA256,
        "outer_split_canonical_sha256": SPLIT_RECEIPT_CANONICAL_SHA256,
        "scope": "EXISTING_HEAVY_AGGREGATE_PLUS_SIX_DONOR_INDEPENDENT_SEMANTIC_CHECK",
        **binding,
        "n1_targets_selected": False,
        "masks_executed": False,
        "burden_calculated": False,
        "precision_calculated": False,
        "training_authorized": False,
    }
    return {**payload, "receipt_sha256": canonical_digest(payload)}
