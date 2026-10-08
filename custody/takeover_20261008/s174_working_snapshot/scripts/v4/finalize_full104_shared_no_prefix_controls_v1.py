#!/usr/bin/env python3
"""Close required nonselecting controls after an independently verified empty prefix."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path

import numpy as np


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def atomic_text(path: Path, text: str) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--independent", type=Path, required=True)
    ap.add_argument("--comparison", type=Path, required=True)
    ap.add_argument("--freeze", type=Path, required=True)
    ap.add_argument("--plan", type=Path, required=True)
    ap.add_argument("--plan-authority", type=Path, required=True)
    ap.add_argument("--source-sensitivity", type=Path, required=True)
    ap.add_argument("--physical-sensitivity", type=Path, required=True)
    ap.add_argument("--feature-audit", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    a = ap.parse_args()

    independent = json.loads(a.independent.read_text(encoding="utf-8"))
    comparison = json.loads(a.comparison.read_text(encoding="utf-8"))
    authority = json.loads(a.plan_authority.read_text(encoding="utf-8"))
    feature_audit = json.loads(a.feature_audit.read_text(encoding="utf-8"))
    if independent["ALL"]["lawful_contiguous_prefix"] or independent["ALL"]["one_se_candidate"] is not None:
        raise SystemExit("shared prefix is not empty")
    if comparison["status"] != "PASS_EXACT_INDEPENDENT_PRODUCTION_AGREEMENT":
        raise SystemExit("independent/production comparison did not pass")
    if sha256(a.plan) != authority["plan_file_sha256"]:
        raise SystemExit("lossless plan hash mismatch")
    if feature_audit.get("protected_or_heldout_expression_opened") is not False:
        raise SystemExit("feature firewall is not explicitly closed")

    with np.load(a.plan, allow_pickle=False) as z:
        required = {"global_weight", "stratum_n", "donor_id", "operator_index", "selection_row"}
        if not required.issubset(z.files):
            raise SystemExit(f"lossless plan missing {sorted(required-set(z.files))}")
        weight = np.asarray(z["global_weight"], dtype=np.float64)
        n = np.asarray(z["stratum_n"], dtype=np.int64)
        rows = np.asarray(z["selection_row"], dtype=np.int64)
        donors = np.asarray(z["donor_id"])
        operators = np.asarray(z["operator_index"], dtype=np.int64)
    if len(np.unique(rows)) != len(rows):
        raise SystemExit("selection rows are not unique")
    if not np.isfinite(weight).all() or np.any(weight < 0):
        raise SystemExit("invalid global weights")

    singleton = n == 1
    limited = (n == 2) | (n == 3)
    mass = {
        "schema": "full104-weighted-null-stratum-mass-v1",
        "status": "PASS_WEIGHTED_NULL_STRATUM_MASS_REPORTED",
        "rows": int(len(rows)),
        "donors": int(len(np.unique(donors))),
        "operators": int(len(np.unique(operators))),
        "total_global_weight": float(weight.sum(dtype=np.float64)),
        "unshufflable_singleton_rows": int(singleton.sum()),
        "unshufflable_singleton_global_weight_mass": float(weight[singleton].sum(dtype=np.float64)),
        "limited_permutation_n2_n3_rows": int(limited.sum()),
        "limited_permutation_n2_n3_global_weight_mass": float(weight[limited].sum(dtype=np.float64)),
        "plan_sha256": sha256(a.plan),
        "plan_semantic_sha256": authority["plan_semantic_sha256"],
        "selection_role": "NONSELECTING_D_INDEPENDENT_FIREWALL_REPORT",
    }

    report_rows = [
        ("value-only", "NOT_APPLICABLE_NO_QUALIFIED_SHARED_STATE", "requires a frozen shared D; lawful prefix is empty", ""),
        ("visibility/support-only", "NOT_APPLICABLE_NO_QUALIFIED_SHARED_STATE", "requires a frozen shared D; lawful prefix is empty", ""),
        ("source deletion", "PRESENT_HASH_BOUND_LEVEL4", "existing FULL104 nonselecting sensitivity", sha256(a.source_sensitivity)),
        ("equal-source sensitivity", "PRESENT_HASH_BOUND_LEVEL4", "existing FULL104 nonselecting sensitivity", sha256(a.source_sensitivity)),
        ("physical-support strata", "PRESENT_HASH_BOUND_LEVEL4", "existing FULL104 nonselecting sensitivity", sha256(a.physical_sensitivity)),
        ("operator/source decodability", "NOT_APPLICABLE_NO_QUALIFIED_SHARED_STATE", "requires qualified shared coordinates; lawful prefix is empty", ""),
        ("weighted singleton/limited-permutation mass", "PASS_COMPUTED_FROM_AUTHENTICATED_FULL104_PLAN", "D-independent frozen-null control", "PENDING_LOCAL_ARTIFACT"),
    ]
    out = a.output_dir
    out.mkdir(parents=True, exist_ok=False)
    mass_path = out / "FULL104_WEIGHTED_NULL_STRATUM_MASS.json"
    atomic_text(mass_path, json.dumps(mass, indent=2, sort_keys=True) + "\n")
    report_rows[-1] = (*report_rows[-1][:-1], sha256(mass_path))
    controls = out / "FULL104_REQUIRED_NONSELECTING_CONTROLS.csv"
    with controls.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["required_report", "status", "reason", "artifact_sha256"])
        w.writerows(report_rows)

    result = {
        "schema": "full104-shared-no-prefix-control-closure-v1",
        "status": "PASS_REQUIRED_NONSELECTING_CONTROLS_CLOSED",
        "routing_status": independent["status"],
        "downstream_consumable": False,
        "D_shared": None,
        "input_sha256": {
            "independent": sha256(a.independent), "comparison": sha256(a.comparison),
            "freeze": sha256(a.freeze), "plan": sha256(a.plan),
            "plan_authority": sha256(a.plan_authority), "source_sensitivity": sha256(a.source_sensitivity),
            "physical_sensitivity": sha256(a.physical_sensitivity), "feature_audit": sha256(a.feature_audit),
        },
    }
    result_path = out / "FULL104_SHARED_NO_PREFIX_CONTROL_CLOSURE.json"
    atomic_text(result_path, json.dumps(result, indent=2, sort_keys=True) + "\n")
    manifest = out / "FULL104_SHARED_NO_PREFIX_CONTROL_MANIFEST.csv"
    files = [result_path, controls, mass_path, Path(__file__).resolve()]
    with manifest.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["path", "bytes", "sha256"])
        for path in files: w.writerow([str(path), path.stat().st_size, sha256(path)])
    root = out / "FULL104_SHARED_NO_PREFIX_CONTROL_ROOT_SHA256.txt"
    atomic_text(root, sha256(manifest) + "\n")
    print(json.dumps({"status": result["status"], "manifest_sha256": sha256(manifest)}))


if __name__ == "__main__":
    main()
