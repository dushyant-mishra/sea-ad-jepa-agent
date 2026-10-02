#!/usr/bin/env python3
from __future__ import annotations

import csv
import gzip
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import numpy as np


REQUIRED_DATASETS = {
    "FULL104_LIKE",
    "STAGE4_LIKE",
    "SCENICPLUS_LIKE",
    "MORABITO_LIKE",
    "PERTURBATION_LIKE",
    "SPATIAL_LIKE",
    "CHECKPOINT_TWIN",
}

REQUIRED_CHECKPOINTS = {
    "HEALTHY",
    "COLLAPSED",
    "SOURCE_SHORTCUT",
    "DONOR_SHORTCUT",
    "PRIVATE_STATE_LEAK",
    "OVERCONFIDENT_UNRECOVERABLE",
    "CORRUPT_MANIFEST",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def read_csv(path: Path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def overlap(a0, a1, b0, b1):
    return max(int(a0), int(b0)) < min(int(a1), int(b1))


def linear_r2(X, y):
    X = np.asarray(X, float)
    y = np.asarray(y, float)
    A = np.c_[np.ones(len(X)), X]
    beta, *_ = np.linalg.lstsq(A, y, rcond=None)
    pred = A @ beta
    denom = float(((y - y.mean()) ** 2).sum())
    return 0.0 if denom == 0 else 1.0 - float(((y - pred) ** 2).sum()) / denom


def multivariate_r2(X, Y):
    Y = np.asarray(Y, float)
    return float(np.mean([linear_r2(X, Y[:, j]) for j in range(Y.shape[1])]))


def validate(root: Path):
    errors = []
    obs = root / "observable_raw"
    truth = root / "hidden_truth"
    if not obs.exists():
        return ["OBSERVABLE_ROOT_MISSING"]
    if not truth.exists():
        errors.append("HIDDEN_TRUTH_ROOT_MISSING")

    for p in obs.rglob("*"):
        if any(tok in p.name.lower() for tok in ("truth", "latent_answer", "answer_key")):
            errors.append(f"TRUTH_FIREWALL_PATH:{p.relative_to(obs)}")

    manifest_path = obs / "MANIFEST.json"
    if not manifest_path.exists():
        return errors + ["MANIFEST_MISSING"]
    manifest = json.loads(manifest_path.read_text())
    datasets = set(manifest.get("dataset_families", []))
    if datasets != REQUIRED_DATASETS:
        errors.append("DATASET_FAMILY_SET_MISMATCH")

    for name, rec in manifest.get("files", {}).items():
        p = obs / name
        if not p.exists():
            errors.append(f"MANIFEST_FILE_MISSING:{name}")
            continue
        if p.stat().st_size != rec.get("bytes"):
            errors.append(f"BYTE_MISMATCH:{name}")
        if sha256(p) != rec.get("sha256"):
            errors.append(f"DIGEST_MISMATCH:{name}")

    # FULL104 structural missingness stays explicit.
    full = np.load(obs / "FULL104_LIKE/rna_counts.npz", allow_pickle=False)
    if full["matrix"].shape != full["availability"].shape:
        errors.append("FULL104_AVAILABILITY_SHAPE_MISMATCH")
    if np.any(full["matrix"][full["availability"] == 0] != 0):
        errors.append("FULL104_STRUCTURAL_MISSING_NONZERO")
    full_contract = json.loads((obs / "FULL104_LIKE/contract.json").read_text())
    if full_contract.get("structural_missingness_is_not_zero") is not True:
        errors.append("FULL104_MISSINGNESS_SEMANTICS_LOST")

    # Stage4 controls: same promoter by construction row, distinct nonoverlap intervals, frozen distance tolerance.
    intervals = {r["interval_id"]: r for r in read_csv(obs / "STAGE4_LIKE/intervals_5kb.csv")}
    pairs = read_csv(obs / "STAGE4_LIKE/matched_pairs.csv")
    if not pairs:
        errors.append("STAGE4_NO_PAIRS")
    for r in pairs:
        if r["linked_interval"] == r["control_interval"]:
            errors.append(f"STAGE4_CONTROL_EQUALS_LINKED:{r['edge_id']}")
            continue
        a = intervals[r["linked_interval"]]
        b = intervals[r["control_interval"]]
        if a["chrom"] == b["chrom"] and overlap(a["start"], a["end"], b["start"], b["end"]):
            errors.append(f"STAGE4_LINKED_CONTROL_OVERLAP:{r['edge_id']}")
        ld, cd = int(r["linked_distance"]), int(r["control_distance"])
        if abs(ld - cd) > max(round(ld * 0.10), 10000):
            errors.append(f"STAGE4_DISTANCE_MATCH_FAIL:{r['edge_id']}")
        if r["linked_accessible"] != r["control_accessible"]:
            errors.append(f"STAGE4_ASYMMETRIC_ACCESSIBILITY:{r['edge_id']}")
        if r["trimmed"] not in {"0", "1"}:
            errors.append(f"STAGE4_BAD_TRIM_STATE:{r['edge_id']}")

    stage4_contract = json.loads((obs / "STAGE4_LIKE/decision_contract.json").read_text())
    if stage4_contract.get("control_construction") != "PROMOTER_FIXED_DISTAL_MATCHED_CONTROL":
        errors.append("STAGE4_CONTROL_CONSTRUCTION_NOT_FROZEN_MATCHED")
    if stage4_contract.get("overlap_policy") != "ALL_OVERLAPS":
        errors.append("STAGE4_OVERLAP_POLICY_NOT_ALL")
    g2 = stage4_contract.get("G2", {})
    if g2.get("status") != "OPEN_PROSPECTIVE_SPECIFICATION_REQUIRED":
        errors.append("STAGE4_G2_SPEC_GAP_SILENTLY_CLOSED")
    if g2.get("numeric_threshold_frozen_here") is not False:
        errors.append("STAGE4_G2_POSTHOC_THRESHOLD_PRESENT")

    # Crosswalk must enumerate ALL geometric overlaps, including peaks mapping to >1 window.
    observed = {
        (r["peak"], r["interval_id"])
        for r in read_csv(obs / "STAGE4_LIKE/all_overlap_crosswalk.csv")
    }
    expected = set()
    scenic_matrix = np.load(obs / "SCENICPLUS_LIKE/paired_multiome.npz", allow_pickle=False)
    for peak in scenic_matrix["peaks"].tolist():
        chrom, coords = str(peak).split(":")
        ps, pe = map(int, coords.split("-"))
        for wid, w in intervals.items():
            if chrom == w["chrom"] and overlap(ps, pe, w["start"], w["end"]):
                expected.add((str(peak), wid))
    if observed != expected:
        missing = len(expected - observed)
        extra = len(observed - expected)
        errors.append(f"STAGE4_ALL_OVERLAP_CROSSWALK_MISMATCH:missing={missing}:extra={extra}")
    by_peak = defaultdict(int)
    for peak, _ in observed:
        by_peak[peak] += 1
    if max(by_peak.values(), default=0) < 2:
        errors.append("STAGE4_OVERLAP_POSITIVE_CONTROL_ABSENT")

    # SCENIC+ donor identity: suffix collisions must exist, and metadata—not suffix—must be authority.
    scenic_cfg = json.loads((obs / "SCENICPLUS_LIKE/route_config.json").read_text())
    if scenic_cfg.get("donor_map_source") != "EXPLICIT_METADATA_JOIN":
        errors.append("SCENIC_DONOR_MAP_NOT_METADATA_AUTHORITY")
    if scenic_cfg.get("barcode_suffix_is_donor") is not False:
        errors.append("SCENIC_SUFFIX_DONOR_INFERENCE_ALLOWED")
    if scenic_cfg.get("ranking_seed") != 20261001:
        errors.append("SCENIC_RANKING_SEED_NOT_PINNED")
    if scenic_cfg.get("blas_threads") != 1:
        errors.append("SCENIC_BLAS_NOT_PINNED")
    if scenic_cfg.get("union_scoring_reuse") is not True:
        errors.append("SCENIC_UNION_SCORING_REUSE_DISABLED")
    if scenic_cfg.get("rankings_shared_across_routes") is not False:
        errors.append("SCENIC_ROUTE_RANKINGS_ILLEGALLY_SHARED")
    if scenic_cfg.get("immutable_script_snapshot_required") is not True:
        errors.append("SCENIC_IMMUTABLE_EXECUTION_NOT_REQUIRED")
    if scenic_cfg.get("shard_completion_requires_disk_reread") is not True:
        errors.append("SCENIC_SHARD_REREAD_NOT_REQUIRED")
    if scenic_cfg.get("merge_requires_exact_ordered_motif_axis") is not True:
        errors.append("SCENIC_MOTIF_AXIS_MERGE_NOT_EXACT")

    scenic_meta = read_csv(obs / "SCENICPLUS_LIKE/metadata.csv")
    suffix_to_donors = defaultdict(set)
    barcodes = set()
    for r in scenic_meta:
        barcodes.add(r["barcode"])
        suffix_to_donors[r["barcode"].rsplit("-", 1)[-1]].add(r["donor"])
    if not any(len(ds) > 1 for ds in suffix_to_donors.values()):
        errors.append("SCENIC_SUFFIX_COLLISION_POSITIVE_CONTROL_ABSENT")
    fragment_barcodes = set()
    with gzip.open(obs / "SCENICPLUS_LIKE/fragments.tsv.gz", "rt", encoding="utf-8") as fh:
        for line in fh:
            f = line.rstrip("\n").split("\t")
            if len(f) != 5:
                errors.append("SCENIC_FRAGMENT_FIELD_COUNT")
                break
            fragment_barcodes.add(f[3])
    if not fragment_barcodes.issubset(barcodes):
        errors.append("SCENIC_FRAGMENT_BARCODE_OUTSIDE_AUTHORITY")

    # Morabito-like nuclei must remain separate even though donors overlap.
    mrna = np.load(obs / "MORABITO_LIKE/rna.npz", allow_pickle=False)
    matac = np.load(obs / "MORABITO_LIKE/atac.npz", allow_pickle=False)
    if set(mrna["nuclei"].tolist()) & set(matac["nuclei"].tolist()):
        errors.append("MORABITO_FAKE_CELL_PAIRING")
    if not (set(mrna["donors"].tolist()) & set(matac["donors"].tolist())):
        errors.append("MORABITO_SHARED_DONOR_STRUCTURE_ABSENT")

    # Perturbation and spatial interfaces retain their intended semantics.
    pert = np.load(obs / "PERTURBATION_LIKE/cell_guide_umi.npz", allow_pickle=False)
    if pert["counts"].shape[1] != len(pert["guides"]):
        errors.append("PERTURBATION_GUIDE_AXIS_MISMATCH")
    spatial = json.loads((obs / "SPATIAL_LIKE/panel_contract.json").read_text())
    if spatial.get("program_3_not_measured_by_design") is not True:
        errors.append("SPATIAL_MISSING_PROGRAM_POSITIVE_CONTROL_ABSENT")
    if spatial.get("missing_program_is_not_biological_absence") is not True:
        errors.append("SPATIAL_MISSINGNESS_SEMANTICS_LOST")

    # Checkpoint twins are qualified from actual outputs, not JSON labels.
    cp_file = obs / "CHECKPOINT_TWIN/checkpoint_outputs.npz"
    cp = np.load(cp_file, allow_pickle=False)
    ids = cp["checkpoint_ids"].tolist()
    if set(ids) != REQUIRED_CHECKPOINTS:
        errors.append("CHECKPOINT_TWIN_SET_MISMATCH")
    else:
        reps = cp["representations"]
        unc = cp["uncertainty"]
        eval_idx = np.asarray(cp["eval_global_indices"], dtype=int)
        cp_cell_ids = [str(x) for x in cp["cell_ids"].tolist()]
        index = {str(k): i for i, k in enumerate(ids)}
        meta_rows = read_csv(obs / "FULL104_LIKE/metadata.csv")
        meta_by_cell = {r["cell_id"]: r for r in meta_rows}
        if set(cp_cell_ids) - set(meta_by_cell):
            errors.append("CHECKPOINT_CELL_ID_NOT_IN_FULL104_AUTHORITY")
            cp_meta = []
        else:
            cp_meta = [meta_by_cell[c] for c in cp_cell_ids]
        source_map = {"SEA_AD": 0.0, "NPH52": 1.0, "HVS": 2.0}
        source_y = np.array([source_map[r["source"]] for r in cp_meta]) if cp_meta else np.array([])
        donor_y = np.array([float(r["donor"][1:]) for r in cp_meta]) if cp_meta else np.array([])

        if len(eval_idx) != reps.shape[1] or len(cp_cell_ids) != reps.shape[1]:
            errors.append("CHECKPOINT_EVAL_AXIS_LENGTH_MISMATCH")
        if float(np.var(reps[index["HEALTHY"]])) <= 0.1:
            errors.append("CHECKPOINT_HEALTHY_COLLAPSED")
        if float(np.var(reps[index["COLLAPSED"]])) >= 0.01:
            errors.append("CHECKPOINT_COLLAPSE_POSITIVE_CONTROL_WEAK")
        if source_y.size and linear_r2(reps[index["SOURCE_SHORTCUT"]], source_y) <= 0.9:
            errors.append("CHECKPOINT_SOURCE_SHORTCUT_POSITIVE_CONTROL_WEAK")
        if donor_y.size and linear_r2(reps[index["DONOR_SHORTCUT"]], donor_y) <= 0.9:
            errors.append("CHECKPOINT_DONOR_SHORTCUT_POSITIVE_CONTROL_WEAK")

        truth_latents = np.load(truth / "LATENTS.npz", allow_pickle=False)
        private = truth_latents["z_reg_private"][eval_idx]
        if multivariate_r2(reps[index["PRIVATE_STATE_LEAK"]], private) <= 0.8:
            errors.append("CHECKPOINT_PRIVATE_LEAK_POSITIVE_CONTROL_WEAK")
        if float(np.median(unc[index["OVERCONFIDENT_UNRECOVERABLE"]])) >= 0.1:
            errors.append("CHECKPOINT_OVERCONFIDENCE_POSITIVE_CONTROL_WEAK")

        cp_manifest = json.loads((obs / "CHECKPOINT_TWIN/checkpoint_manifest.json").read_text())
        corrupt = cp_manifest.get("corrupt_manifest_case", {})
        if corrupt.get("checkpoint_id") != "CORRUPT_MANIFEST":
            errors.append("CHECKPOINT_CORRUPT_MANIFEST_CASE_MISSING")
        if corrupt.get("declared_output_sha256") == sha256(cp_file):
            errors.append("CHECKPOINT_CORRUPT_MANIFEST_POSITIVE_CONTROL_WEAK")

    return errors


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    args = ap.parse_args()
    errs = validate(Path(args.root))
    if errs:
        print("\n".join(errs))
        raise SystemExit(1)
    print("PASS: V72 coupled multi-dataset synthetic fixture")
