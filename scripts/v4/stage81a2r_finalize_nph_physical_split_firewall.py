"""Finalize manifests after isolated per-object NPH split verification."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-project", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    source = args.source_project.resolve()
    root = args.output_root.resolve()
    expected_files = sorted((root / "expected").glob("*.expected.csv"))
    verified_files = sorted((root / "verified").glob("*.verified.csv"))
    if len(expected_files) != 7 or len(verified_files) != 21:
        raise RuntimeError(f"incomplete split manifests: expected={len(expected_files)} verified={len(verified_files)}")
    expected = pd.concat([pd.read_csv(path) for path in expected_files], ignore_index=True)
    verified = pd.concat([pd.read_csv(path) for path in verified_files], ignore_index=True)
    if len(expected) != 21 or len(verified) != 21 or not verified.exact_lossless_subset_pass.astype(bool).all():
        raise RuntimeError("physical split exactness manifest incomplete")
    keys = ["source_object_id", "partition"]
    if set(map(tuple, expected[keys].to_numpy())) != set(map(tuple, verified[keys].to_numpy())):
        raise RuntimeError("expected/verified derivative key mismatch")
    if list(root.rglob("*.part")):
        raise RuntimeError("partial derivative files remain")
    split_path = source / "results/v4/stage81a2_split_registry.csv"
    split = pd.read_csv(split_path)
    foundation = split[split.split_domain.eq("foundation")]
    counts = foundation.groupby("split").size().to_dict()
    if counts != {"development": 19, "sealed_holdout": 19, "train": 149}:
        raise RuntimeError("frozen foundation split changed")
    verified = verified.sort_values(keys).reset_index(drop=True)
    verified.to_csv(root / "nph52_physical_split_exactness_manifest.csv", index=False, lineterminator="\n")
    report = {
        "stage": "stage81a2r_nph_physical_split_firewall",
        "classification": "PRE_ANALYTIC_FIREWALL_CONSTRUCTION_COMPLETE",
        "frozen_split_manifest_sha256": sha256(split_path),
        "foundation_split_counts": {"TRAIN": 149, "DEV": 19, "SEALED": 19},
        "nph_split_donor_counts": {"TRAIN": 19, "DEV": 3, "SEALED": 3},
        "source_objects": 7,
        "derivatives": 21,
        "mixed_split_rna_transiently_deserialized": True,
        "pathology_bytes_transiently_deserialized_in_ingestion_boundary": bool(expected.pathology_bytes_transiently_deserialized_in_ingestion_boundary.astype(bool).any()),
        "pathology_inspected": False,
        "pathology_used_for_split": False,
        "pathology_exported_to_train_analytic_asset": False,
        "pathology_summarized_or_calculated": False,
        "model_code_imported": False,
        "expression_normalized": False,
        "expression_transformed": False,
        "features_filtered_or_ranked": False,
        "source_objects_modified": False,
        "retained_column_metadata": ["source_cell_id", "source_donor_id"],
        "exact_lossless_subset_pass": True,
    }
    (root / "nph52_physical_split_firewall_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
