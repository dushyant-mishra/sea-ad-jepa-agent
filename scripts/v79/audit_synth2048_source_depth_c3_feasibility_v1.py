#!/usr/bin/env python3
"""Read-only source-depth and C2/C3 observability audit for exact PR547 FIT ZIP.

This is NOT a target test, a learned representation run, a candidate score, or
a new synthetic realization. The only observations are fit-side measurements
from the owner-authorized frozen development FIT archive. No query values,
model training, controller/latent truth, or human data are read or exported.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import zipfile

import numpy as np


SCHEMA = "JEPA_SYNTH2048_EXACT_FIT_SOURCE_C2_C3_OBSERVABILITY_V1"
EXPECTED_ZIP_SIZE = 25023562
EXPECTED_ZIP_SHA256 = "87fe3ec2038305c797c439cd9780036fe22cc22b647242749b1af0bfb444c06f"
MEMBER_DIGESTS = {
    "teacher_measured.npz": "f38133844359017174e070fb5e4b5afc48334db86c80f17e99ef7b54014d6cc1",
    "student_qexcluded.npz": "a1fce3b79beb0d7632a0ffcdc9f28e94aadb4a594e9c76a8f6f6c48d1b99a0b5",
    "roster_evaluation_only.npz": "0427f1221f55e607cf32abb827db1be1026274b2acf3134f3a05e9f513a48c18",
    "atac_separate_nucleus_negative.npz": "26b35ab4e43ad3ee3e98c81d017b300dab2e70945a608e25154d9346ba2df321",
    "DEVELOPMENT_RECEIPT.json": "91310b3c3d86e28ce19a4090c624b53d4a6d0e31b5984dc9a8e159d08a4b1b0d",
}
SOURCES = ("SYNTH_A", "SYNTH_B", "SYNTH_C")
SPLITS = ("train", "val", "test")
N_CELLS, N_GENES, N_DONORS = 1440, 2048, 36
EXPECTED_Q = (1672, 1673, 1674, 1675)
AUTHORITY = "TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED"


class AuditRefusal(ValueError):
    pass


def demand(condition: bool, reason: str) -> None:
    if not bool(condition):
        raise AuditRefusal("REFUSE_SYNTH2048_FIT_AUDIT__" + reason)


def _npz(raw: bytes) -> dict[str, np.ndarray]:
    with np.load(BytesIO(raw), allow_pickle=False) as f:
        arrays = {name: f[name] for name in f.files}
    demand(all(x.dtype.kind != "O" for x in arrays.values()), "OBJECT_ARRAY_FORBIDDEN")
    return arrays


def load_verified_zip(path: Path) -> tuple[dict, dict, dict, dict]:
    """Independently verify artifact AND member bytes before reading raw arrays."""
    p = Path(path)
    demand(p.is_file() and not p.is_symlink(), "FIT_MISSING")
    demand(p.stat().st_size == EXPECTED_ZIP_SIZE, "FIT_SIZE_CHANGED")
    demand(sha256(p.read_bytes()).hexdigest() == EXPECTED_ZIP_SHA256, "FIT_SHA_CHANGED")
    with zipfile.ZipFile(p) as f:
        demand(len(f.namelist()) == 5 and set(f.namelist()) == set(MEMBER_DIGESTS),
               "FIT_MEMBERS_CHANGED")
        for name, digest in MEMBER_DIGESTS.items():
            item = f.getinfo(name)
            demand(not item.is_dir() and item.file_size < 75_000_000,
                   "OVERSIZED_MEMBER")
            demand(sha256(f.read(name)).hexdigest() == digest,
                   "MEMBER_SHA_CHANGED_" + name)
        receipt = json.loads(f.read("DEVELOPMENT_RECEIPT.json"))
        student = _npz(f.read("student_qexcluded.npz"))
        roster = _npz(f.read("roster_evaluation_only.npz"))
        # Reads only structurally measured-support boolean; deliberately never
        # accesses teacher q counts or the separate-nucleus ATAC arrays.
        with np.load(BytesIO(f.read("teacher_measured.npz")), allow_pickle=False) as teacher:
            teacher_support = teacher["rna_support"].copy()
    demand(receipt.get("schema") == "JEPA_EXPANDED_COMMON_WORLD_DEVELOPMENT_FIT_ONLY_V1",
           "RECEIPT_SCHEMA")
    demand(receipt.get("all_six_candidate_recoverability") == "UNASSESSED",
           "FORGED_C_GRADE")
    demand(receipt.get("controller_truth_exported") is False
           and receipt.get("model_training_or_controller_scoring_executed") is False
           and receipt.get("real_biology_or_production_authority") is False,
           "FIT_AUTHORITY_FORGED")
    demand(receipt.get("frozen_dimensions") == {
        "cells": N_CELLS, "genes": N_GENES, "donors": N_DONORS,
    }, "DIMENSIONS_CHANGED")
    return receipt, student, roster, {"teacher_support": teacher_support}


def validate_view_roles(
    receipt: dict, student: dict[str, np.ndarray],
    teacher_support: np.ndarray,
) -> tuple[list[np.ndarray], list[np.ndarray], np.ndarray]:
    roles = receipt["frozen_preoutcome_address_roles"]
    addr = student["rna_base_address_ids"]
    cnt = student["rna_base_counts"]
    support = student["rna_base_support"]
    depth = student["projected_base_depth"]
    q = roles["query_addresses"]
    views = roles["relational_views_3x512"]
    panels = roles["query_other8_panels"]
    demand(q == list(EXPECTED_Q), "QUERY_IDS_CHANGED")
    demand(len(views) == 3 and all(len(a) == 512 for a in views),
           "DISJOINT_512_VIEWS_REQUIRED")
    demand(len(panels) == 4 and all(len(a) == 8 for a in panels),
           "FOUR_OTHER8_PANELS_REQUIRED")
    assigned = [int(v) for group in (*views, q, *panels) for v in group]
    demand(len(assigned) == len(set(assigned)), "PANEL_ALIAS")
    demand(all(0 <= v < N_GENES for v in assigned), "PANEL_OUT_OF_RANGE")
    demand(cnt.shape == support.shape == (N_CELLS, N_GENES - len(q)),
           "STUDENT_COUNT_OR_RIGHTS_DIMENSIONS")
    demand(cnt.dtype == np.int32 and support.dtype == np.bool_
           and addr.dtype == np.int32 and depth.dtype == np.int64,
           "STUDENT_DTYPE_CHANGED")
    demand(np.array_equal(addr, np.setdiff1d(np.arange(N_GENES), q).astype(np.int32)),
           "GENE_IDS_SHIFTED_OR_QUERY_VISIBLE")
    demand(np.array_equal(cnt.sum(axis=1, dtype=np.int64), depth),
           "BASE_DEPTH_LEAK_OR_MISMATCH")
    demand(not np.any(cnt < 0) and not np.any(cnt[~support]),
           "STRUCTURAL_ABSENCE_AS_DETECTION")
    demand(teacher_support.shape == (N_CELLS, N_GENES)
           and teacher_support.dtype == np.bool_, "TEACHER_MEASUREMENT_SUPPORT")
    demand(np.all(teacher_support[:, q]), "C3_QUERY_NOT_STRUCTURALLY_MEASURED")
    # Every C2 512-address view and C3 other-eight-gene panel must be
    # structurally measured for every cell, not merely observed nonzero.
    lookup = np.full(N_GENES, -1, dtype=np.int32)
    lookup[addr] = np.arange(len(addr), dtype=np.int32)
    arrays = [np.asarray(v, dtype=np.int32) for v in views]
    c3 = [np.asarray(v, dtype=np.int32) for v in panels]
    demand(all(np.all(lookup[v] >= 0) and np.all(support[:, lookup[v]])
               for v in (*arrays, *c3)), "PANEL_NOT_MEASURED_IN_ALL_SOURCES")
    demand(not np.any(np.isin(EXPECTED_Q, addr)), "QUERY_IN_STUDENT")
    return arrays, c3, lookup


def summarize_verified_fit(
    receipt: dict,
    student: dict[str, np.ndarray],
    roster: dict[str, np.ndarray],
    extra: dict,
) -> dict:
    views, panels, lookup = validate_view_roles(receipt, student, extra["teacher_support"])
    cnt = student["rna_base_counts"]
    depth = student["projected_base_depth"]
    source = roster["synthetic_source"]
    split = roster["split"]
    donor = roster["donor_id"]
    demand(source.shape == split.shape == donor.shape == (N_CELLS,), "ROSTER_LENGTH")
    demand(donor.dtype == np.int32 and len(set(donor.tolist())) == N_DONORS,
           "DONOR_ROSTER_CHANGED")
    demand(set(source.tolist()) == set(SOURCES), "SOURCE_ROSTER_CHANGED")
    demand(set(split.tolist()) == set(SPLITS), "SPLIT_ROSTER_CHANGED")
    for d in np.unique(donor):
        rows = donor == d
        demand(len(set(source[rows].tolist())) == 1
               and len(set(split[rows].tolist())) == 1,
               "DONOR_CROSSES_SPLIT_OR_SOURCE")
    per_source: dict[str, dict] = {}
    for s in SOURCES:
        ix = source == s
        demand(ix.sum() > 0, "SOURCE_EMPTY")
        per_source[s] = {
            "cells": int(ix.sum()),
            "donors": int(len(np.unique(donor[ix]))),
            "cells_by_split": {part: int(np.sum(ix & (split == part))) for part in SPLITS},
            "donors_by_split": {
                part: int(len(np.unique(donor[ix & (split == part)])))
                for part in SPLITS
            },
            "median_student_base_depth": float(np.median(depth[ix])),
            "mean_student_base_depth": float(np.mean(depth[ix])),
            "median_detected_base_genes": float(np.median((cnt[ix] > 0).sum(axis=1))),
            "C2_per_view_median_detected_genes": [
                float(np.median((cnt[ix][:, lookup[v]] > 0).sum(axis=1)))
                for v in views
            ],
            "C3_per_panel_median_detected_other8": [
                float(np.median((cnt[ix][:, lookup[p]] > 0).sum(axis=1)))
                for p in panels
            ],
            "C3_query_and_other8_structurally_estimable_cells": int(ix.sum()),
        }
    medians = [per_source[s]["median_student_base_depth"] for s in SOURCES]
    ratio = float(max(medians) / min(medians)) if min(medians) > 0 else None
    return {
        "schema": SCHEMA,
        "exact_parent_fit_sha256": EXPECTED_ZIP_SHA256,
        "status": "DESCRIPTIVE_OBSERVABILITY_ONLY__NO_TD_OR_JEPA_GATE_PASS",
        "source_support_is_prospective_simulation_not_human_calibration": True,
        "all_three_C2_512_address_views_present": True,
        "C2_relational_correct_cell_biology": "UNASSESSED",
        "four_C3_query_plus_other8_panels_present": True,
        "C3_learned_context_above_wrong_query": "UNASSESSED",
        "per_source": per_source,
        "source_depth_median_max_to_min_ratio": ratio,
        "source_and_donor_not_independently_randomized": True,
        "student_q_values_or_teacher_q_values_read": False,
        "controller_truth_or_sealed_v80_used": False,
        "training_or_student_scoring_executed": False,
        "selection_or_threshold_freeze_produced": False,
        "C1_C2_C3_C4_C5_C6_status": "ALL_UNASSESSED",
        "conclusion": (
            "Mechanically all four C3 q+other8 panels are measured across all "
            "three artificial sources in new 2048 FIT; unlike original #536 "
            "old 48-gene source restriction. However depth and detection "
            "differ by source. This descriptive report DOES NOT establish "
            "source-generalizable contextual biology or JEPA recovery."
        ),
        "authority": AUTHORITY,
    }


def run(path: Path) -> dict:
    receipt, student, roster, extra = load_verified_zip(path)
    return summarize_verified_fit(receipt, student, roster, extra)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fit-zip", type=Path, required=True)
    ap.add_argument("--report", type=Path, required=True)
    args = ap.parse_args()
    result = run(args.fit_zip)
    demand(not args.report.exists(), "REPORT_WOULD_OVERWRITE")
    args.report.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "source_depth_ratio": result["source_depth_median_max_to_min_ratio"],
        "C1_C6": result["C1_C2_C3_C4_C5_C6_status"],
        "training": result["training_or_student_scoring_executed"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
