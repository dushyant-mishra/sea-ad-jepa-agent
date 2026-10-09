#!/usr/bin/env python3
"""Freeze a reviewable FULL104 shared-state candidate from two independent sketches."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
ADDRESS_N = 41_238


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def write_json_atomic(path: Path, value) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def main() -> None:
    raise RuntimeError("SUPERSEDED_DO_NOT_USE: pre-refit Level-1 freezer cannot consume the active promotion DAG")
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase2-root", required=True)
    parser.add_argument("--dimension", type=int, required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    root = Path(args.phase2_root).resolve()
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    d = args.dimension

    analytic = root / "shared_analytic_level1_v2"
    empirical = root / "shared_empirical_level1_v2"
    ladder = root / "ladder_adjudication_level1"
    shortcut = root / "shared_shortcut_fold_audit_level1"
    features = root / "multiview_features_level1"
    architecture = root / "pregeometry_audits"
    amendment = root / "shared_procedure_amendment_v2"
    required = {
        "analytic_manifest": analytic / "SHARED_LEVEL1_ANALYTIC_DIAGNOSTIC_MANIFEST.csv",
        "empirical_manifest": empirical / "SHARED_LEVEL1_EMPIRICAL_PACKAGE_MANIFEST.csv",
        "ladder_manifest": ladder / "PHASE2_SHARED_LADDER_ADJUDICATION_MANIFEST.csv",
        "shortcut_manifest": shortcut / "SHARED_SHORTCUT_FOLD_AUDIT_MANIFEST.csv",
        "feature_manifest": features / "PHASE2_MULTIVIEW_FEATURE_MANIFEST.csv",
        "architecture_manifest": architecture / "PHASE2_PREGEOMETRY_AUDIT_MANIFEST.csv",
        "procedure_manifest": amendment / "PHASE2_SHARED_PROCEDURE_AMENDMENT_MANIFEST.csv",
    }
    missing = [str(path) for path in required.values() if not path.is_file()]
    if missing:
        raise RuntimeError(f"missing authenticated inputs: {missing}")

    ladder_result = json.loads((ladder / "PHASE2_SHARED_SAMPLE_LADDER_ADJUDICATION.json").read_text())
    selection = json.loads((empirical / "SHARED_DIMENSION_SELECTION_LEVEL.json").read_text())
    shortcut_result = json.loads((shortcut / "PHASE2_SHARED_OBSERVATION_SHORTCUT_AUDIT.json").read_text())
    if ladder_result["status"] != "SHARED_STATE_CANDIDATE_CONVERGED" or not ladder_result["successive_level_converged"]:
        raise RuntimeError("successive-level convergence unavailable")
    if int(ladder_result["candidate_D_shared"]) != d or int(selection["candidate_D_shared"]) != d:
        raise RuntimeError("dimension disagrees with frozen empirical selection")

    bases = {}
    for label in "AB":
        z = np.load(analytic / f"SHARED_OVERCOMPLETE_BASIS_{label}.npz", allow_pickle=False)
        bases[label] = {name: np.asarray(z[name]) for name in z.files}
    stats = analytic / "sufficient_statistics"
    strata = pd.read_csv(stats / "DONOR_OPERATOR_STRATA.csv", dtype={"donor_id": str})
    donor_counts = strata.groupby("donor_id").size()
    weights = strata.donor_id.map((1.0 / donor_counts).to_dict()).to_numpy(np.float64)
    weights /= weights.sum()
    scores = {}
    for label in "AB":
        means = np.asarray(np.load(stats / f"{label}_stratum_mean.npy", mmap_mode="r"), np.float64)
        scores[label] = (means - bases[label]["mean"]) @ bases[label]["components"][:, :d]
    cross = scores["B"].T @ (weights[:, None] * scores["A"])
    u, _, vt = np.linalg.svd(cross, full_matrices=False)
    rotation_b_to_a = u @ vt
    aligned_b = scores["B"] @ rotation_b_to_a
    alignment_r2 = 1.0 - float(np.sum(weights[:, None] * (scores["A"] - aligned_b) ** 2)) / max(
        float(np.sum(weights[:, None] * scores["A"] ** 2)), np.finfo(float).eps
    )

    projections = np.load(features / "PHASE2_SKETCH_PROJECTIONS.npz", allow_pickle=False)
    lifted = {}
    for label in "AB":
        component = bases[label]["components"][:, :d].astype(np.float64)
        if label == "B":
            component = component @ rotation_b_to_a
        value_col = projections[f"{label}_value_col"]
        value_sign = projections[f"{label}_value_sign"].astype(np.float64)
        visibility_col = projections[f"{label}_visibility_col"]
        visibility_sign = projections[f"{label}_visibility_sign"].astype(np.float64)
        if len(value_col) != ADDRESS_N or len(visibility_col) != ADDRESS_N:
            raise RuntimeError("address projection geometry mismatch")
        lifted[f"{label}_value_weight"] = value_sign[:, None] * component[value_col]
        lifted[f"{label}_visibility_weight"] = visibility_sign[:, None] * component[256 + visibility_col]
        bias = -bases[label]["mean"] @ bases[label]["components"][:, :d]
        lifted[f"{label}_bias"] = bias if label == "A" else bias @ rotation_b_to_a
    value_weight = (lifted["A_value_weight"] + lifted["B_value_weight"]) * 0.5
    visibility_weight = (lifted["A_visibility_weight"] + lifted["B_visibility_weight"]) * 0.5
    bias = (lifted["A_bias"] + lifted["B_bias"]) * 0.5
    basis_path = out / "FULL104_SHARED_STATE_CANDIDATE_BASIS.npz"
    np.savez_compressed(
        basis_path,
        value_weight=value_weight.astype(np.float32),
        visibility_weight=visibility_weight.astype(np.float32),
        bias=bias.astype(np.float64),
        rotation_B_to_A=rotation_b_to_a.astype(np.float64),
        A_value_weight=lifted["A_value_weight"].astype(np.float32),
        A_visibility_weight=lifted["A_visibility_weight"].astype(np.float32),
        A_bias=lifted["A_bias"].astype(np.float64),
        B_aligned_value_weight=lifted["B_value_weight"].astype(np.float32),
        B_aligned_visibility_weight=lifted["B_visibility_weight"].astype(np.float32),
        B_aligned_bias=lifted["B_bias"].astype(np.float64),
    )

    contract = {
        "schema": "full104-shared-state-candidate-v1",
        "status": "CANDIDATE_AWAITING_ORDERED_COUNCIL",
        "sample_level": 1,
        "cells": 345_017,
        "donors": 104,
        "operators": 42,
        "D_shared": d,
        "dimension_authority": "DERIVE_ON_104_FIT",
        "selection": "smallest jointly empirical-null-supported contiguous prefix within one donor SE of best in both independent sketches",
        "successive_level_convergence": ladder_result["comparison"],
        "empirical_matched_null_replicates": 256,
        "empirical_matched_null_rng_authority": "matched_null",
        "analytic_null_role": "DIAGNOSTIC_ONLY",
        "basis_construction": "equal average of sketch A and donor-equal donor-by-operator Procrustes-aligned sketch B",
        "basis_exact_input_semantics": "log1p10k value channel plus measured-scalar visibility channel; identity/labels excluded",
        "A_B_aligned_score_r2_donor_equal": alignment_r2,
        "architecture_capacity": {
            "classification": "FROZEN_ARCHITECTURE_CAPACITY",
            "token_and_CELL_width": 160,
            "D_shared_truncated_to_capacity": False,
            "note": "160 is authenticated production token/CELL width, not a derived shared-state dimension or code-fixed output ceiling",
        },
        "shortcut_diagnostics": shortcut_result,
        "known_review_risks": [
            "candidate coordinates are highly operator-decodable; source/support sensitivity must be adjudicated",
            "empirical permutation stability null uses the frozen observed coordinate basis and must be reviewed for adequacy",
            "operator-unseen transfer is unestimable because every frozen donor fold contains every operator represented in its held donors",
        ],
        "forbidden_selection_inputs_used": False,
        "biology_program_rare_pathology_or_protected_labels_used": False,
        "private_standardization_direct_basis_optimizer_training_started": False,
        "input_hashes": {name: sha(path) for name, path in required.items()},
        "basis_sha256": sha(basis_path),
        "code_sha256": sha(Path(__file__)),
    }
    contract_path = out / "FULL104_SHARED_STATE_CANDIDATE.json"
    write_json_atomic(contract_path, contract)
    lineage = pd.DataFrame([
        {"artifact": name, "classification": "FROZEN_AUTHORITY" if name in {"architecture_manifest", "procedure_manifest"} else "DERIVE_ON_104_FIT", "path": str(path.relative_to(ROOT)), "sha256": sha(path)}
        for name, path in required.items()
    ] + [{"artifact": "shared_candidate_basis", "classification": "DERIVE_ON_104_FIT", "path": str(basis_path.relative_to(ROOT)), "sha256": sha(basis_path)}])
    lineage_path = out / "FULL104_SHARED_STATE_INPUT_LINEAGE.csv"
    lineage.to_csv(lineage_path, index=False, lineterminator="\n")
    package_files = [basis_path, contract_path, lineage_path, Path(__file__)]
    manifest_path = out / "FULL104_SHARED_STATE_CANDIDATE_MANIFEST.csv"
    pd.DataFrame([
        {"path": str(path.relative_to(ROOT)), "bytes": path.stat().st_size, "sha256": sha(path)} for path in package_files
    ]).to_csv(manifest_path, index=False, lineterminator="\n")
    anchor = out / "FULL104_SHARED_STATE_CANDIDATE_ROOT_SHA256.txt"
    anchor.write_text(sha(manifest_path) + "\n", encoding="ascii")
    print(json.dumps({"status": contract["status"], "D_shared": d, "alignment_r2": alignment_r2, "manifest_sha256": sha(manifest_path)}, indent=2))


if __name__ == "__main__":
    main()
