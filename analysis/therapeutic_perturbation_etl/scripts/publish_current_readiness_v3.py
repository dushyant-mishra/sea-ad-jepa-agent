#!/usr/bin/env python3
"""Fail-closed CURRENT V3 readiness overlay on immutable historical V2 metadata.

This does NOT regenerate biological effects or upstream cross-study computed
columns: it pins and REUSES the byte-identical historical computed matrix,
and publishes only a versioned curator assertion CSV / readiness receipt.

Historical V2 registry, physical inventory and cross-study V2 receipt remain
unchanged. CPU-only; does not inspect protected outcomes or qualify training.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

from audit_receipt_readiness_consistency_v1 import check, load, RECEIPTS

ROOT = Path(__file__).resolve().parents[1]
V2 = "evidence/CURATOR_ASSERTION_REGISTRY_V2.json"
V3 = "evidence/CURATOR_ASSERTION_REGISTRY_V3.json"
INV = "evidence/physical_inventory_v2/STUDY_SOURCE_INVENTORY_RECEIPT_V2.json"
CROSS = "evidence/cross_study_v3/CROSS_STUDY_COMPARABILITY_RECEIPT_V2.json"
MATRIX = "evidence/cross_study_v3/CROSS_STUDY_COMPUTED_MATRIX_V2.csv"
HISTORICAL_V2_SHA256 = "7141c2cd4c675cb99cd3e64baf04d6ef348cf403bb0b6a5ee4ac3b212d7af763"
EXPECTED = {
    "GSE301119": {"independent_reproduction": "IMPLEMENTATION_REPRODUCED"},
    "GSE254205": {"independent_reproduction": "IMPLEMENTATION_REPRODUCED_TO_STORED_PRECISION"},
    "GSE178317": {"independent_reproduction": "IMPLEMENTATION_REPRODUCED_TO_STORED_PRECISION"},
    "GSE311359": {
        "etl_status": "PASS_DEVELOPMENT_ETL_ID_KEYED",
        "biological_estimability": "SEQUENCE_IDENTITY_UNPROVEN_CIS_CAUSALITY_UNPROVEN",
        "independent_reproduction": "ID_KEYED_V1_NONBIN1_PARITY_ONLY",
    },
}
STABLE_FIELDS = (
    "outcome_exposure", "independent_units", "blocking_missing_source",
)
COLUMNS = (
    "study", "etl_status", "biological_estimability", "outcome_exposure",
    "independent_reproduction", "independent_units", "scientific_estimand_status",
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(1024 * 1024), b""):
            h.update(c)
    return h.hexdigest()


def git_blob_sha(path: Path) -> str:
    raw = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def verified_inputs(root: Path) -> dict:
    v2p, v3p = root / V2, root / V3
    v2, v3 = load(v2p), load(v3p)
    if sha256(v2p) != HISTORICAL_V2_SHA256:
        raise ValueError("STOP_HISTORICAL_V2_REGISTRY_DIGEST_DRIFT")
    if (v3.get("registry_id") != "PERTURBATION_CURATOR_ASSERTION_REGISTRY_V3"
        or v3.get("_historical_registry_v2", {}).get("github_blob_sha") != git_blob_sha(v2p)
        or v3.get("_historical_registry_v2", {}).get("sha256_bound_by_historical_receipts") != sha256(v2p)):
        raise ValueError("STOP_V3_HISTORICAL_PARENT_UNBOUND")
    old, new = v2.get("assertions", {}), v3.get("assertions", {})
    if not isinstance(old, dict) or set(old) != set(new):
        raise ValueError("STOP_ASSERTION_STUDY_SET_CHANGED")
    for study, prev in old.items():
        cur = new[study]
        expected = EXPECTED.get(study, {})
        for field in ("etl_status", "biological_estimability", "independent_reproduction"):
            if cur.get(field) != expected.get(field, prev.get(field)):
                raise ValueError(f"STOP_UNEXPECTED_V3_STATUS: {study}/{field}")
        for field in STABLE_FIELDS:
            if cur.get(field) != prev.get(field):
                raise ValueError(f"STOP_PROTECTED_OR_BIOLOGICAL_SCOPE_CHANGED: {study}/{field}")
        if study not in EXPECTED and cur.get("limitation") != prev.get("limitation"):
            raise ValueError(f"STOP_UNRELATED_STUDY_REWRITTEN: {study}")
    receipts = {study: load(root / rel) for study, rel in RECEIPTS.items()}
    problems = check(v3, receipts)
    if problems:
        raise ValueError("STOP_READINESS_RECEIPT_DISAGREEMENT: " + "|".join(problems))
    for study in EXPECTED:
        bound = new[study].get("v3_receipt_evidence", {})
        source = root / RECEIPTS[study]
        if (bound.get("path") != "analysis/therapeutic_perturbation_etl/" + RECEIPTS[study]
            or bound.get("github_blob_sha") != git_blob_sha(source)):
            raise ValueError(f"STOP_UNBOUND_V3_RECEIPT: {study}")
    inventory, cross = load(root / INV), load(root / CROSS)
    if (inventory.get("assertion_registry_sha256") != sha256(v2p)
        or inventory.get("curator_assertions", {}).get("entries") != old):
        raise ValueError("STOP_HISTORICAL_INVENTORY_ASSERTIONS_CHANGED")
    cross_before = cross.get("input_digests_before_open", {}).get("assertion_registry")
    cross_after = cross.get("input_digests_after_read", {}).get("assertion_registry")
    if cross_before != sha256(v2p) or cross_after != sha256(v2p):
        raise ValueError("STOP_HISTORICAL_CROSS_STUDY_REGISTRY_BINDING_CHANGED")
    matrix_digest = sha256(root / MATRIX)
    if cross.get("computed_matrix_csv_sha256") != matrix_digest:
        raise ValueError("STOP_HISTORICAL_COMPUTED_MATRIX_DRIFT")
    return {
        "v2_sha256": sha256(v2p), "v3_sha256": sha256(v3p),
        "inventory_v2_sha256": sha256(root / INV),
        "cross_study_v2_sha256": sha256(root / CROSS),
        "cross_study_computed_v2_sha256": matrix_digest,
        "receipt_sha256": {study: sha256(root / path) for study, path in RECEIPTS.items()},
        "assertions": new,
    }


def publish(root: Path, out_dir: Path) -> Path:
    if out_dir.exists():
        raise ValueError("STOP_OUTPUT_EXISTS_USE_NEW_VERSIONED_DIRECTORY")
    status = verified_inputs(root)  # no output until all validation passes
    out_dir.parent.mkdir(parents=True, exist_ok=True)
    staging = out_dir.parent / (out_dir.name + ".staging-" + str(os.getpid()))
    if staging.exists():
        raise ValueError("STOP_STAGING_EXISTS")
    staging.mkdir()
    try:
        csv_path = staging / "CURRENT_CURATOR_ASSERTIONS_V3.csv"
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=COLUMNS, lineterminator="\n")
            w.writeheader()
            for study, a in sorted(status["assertions"].items()):
                w.writerow({key: study if key == "study" else a.get(key, "") for key in COLUMNS})
        receipt = {
            "schema": "CURRENT_PERTURBATION_READINESS_OVERLAY_V3",
            "status": "DRAFT_METADATA_STATUS_ONLY_NOT_SCIENTIFIC_AUTHORITY",
            "v2_historical_registry_sha256": status["v2_sha256"],
            "v3_current_registry_sha256": status["v3_sha256"],
            "historical_inventory_v2_sha256": status["inventory_v2_sha256"],
            "historical_cross_study_v2_receipt_sha256": status["cross_study_v2_sha256"],
            "historical_cross_study_v2_computed_matrix_sha256": status["cross_study_computed_v2_sha256"],
            "computed_matrix_rederived": False,
            "computed_matrix_source": MATRIX,
            "curator_assertions_v3_csv_sha256": sha256(csv_path),
            "physical_receipt_sha256": status["receipt_sha256"],
            "known_open_science": [
                "GSE301119 independent estimand review / real two-arm NT null",
                "GSE254205 full-precision tolerance not testable from rounded outputs",
                "GSE311359 guide sequences and direct cis causality unproven",
                "GSE178317 has only one pooled biological preparation",
            ],
            "training_authorized": False,
            "protected_outcome_opened": False,
            "therapeutic_ranking": False,
        }
        (staging / "CURRENT_READINESS_OVERLAY_RECEIPT_V3.json").write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        staging.rename(out_dir)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return out_dir


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--out-dir", type=Path, required=True)
    args = ap.parse_args(argv)
    try:
        path = publish(args.root, args.out_dir)
    except (OSError, ValueError, KeyError, TypeError) as e:
        print(str(e), file=sys.stderr)
        return 1
    print(f"PASS_V3_CURRENT_STATUS_METADATA_ONLY: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
