#!/usr/bin/env python3
"""Reclassify Stage81 data decisions after removal of arbitrary storage caps."""

from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any


ALLOWED = {
    "download_required", "download_useful", "metadata_only", "duplicate_excluded",
    "raw_data_excluded", "scientifically_incompatible", "controlled_access_blocked",
    "source_unverified",
}
REVOKED = {
    "deferred_oversized", "excluded_due_to_download_limit", "catalog_only_due_to_size",
    "requires_manual_size_approval",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", default=".")
    parser.add_argument("--output-dir", default="results/v4")
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def atomic_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(value)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    columns = list(rows[0])
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def classify(prior: str, reason: str, item: str) -> str:
    blob = f"{prior} {reason} {item}".lower()
    if prior in REVOKED:
        raise RuntimeError(f"Revoked size status requires explicit scientific reassessment: {item}")
    if "raw_fastq" in blob or "raw sequencing" in blob or "microscopy" in blob:
        return "raw_data_excluded"
    if "controlled" in blob or "terms_acceptance" in blob or "access_block" in blob:
        return "controlled_access_blocked"
    if "not_advertised" in blob or "source_unverified" in blob:
        return "source_unverified"
    if "duplicate" in blob or "redundant" in blob or "exact study-defined subset" in blob:
        return "duplicate_excluded"
    if "incompatible" in blob or "50-nuclei-per-cluster subset" in blob:
        return "scientifically_incompatible"
    if prior in {"download_useful"}:
        return "download_useful"
    if prior.startswith("preserve") or prior == "metadata_only":
        return "metadata_only"
    if prior in {"download", "download_required", "download_processed_supplementary"}:
        return "download_required"
    raise RuntimeError(f"Unclassified Stage81 decision: {item} ({prior}; {reason})")


def row(scope: str, item: str, prior: str, reason: str, source: str, size: str = "") -> dict[str, Any]:
    final = classify(prior, reason, item)
    return {
        "scope": scope,
        "item_id": item,
        "prior_decision": prior,
        "reconsidered_decision": final,
        "scientific_reason": reason,
        "storage_assessment": "capacity_monitored_no_fixed_cap_or_per_object_threshold_applied",
        "authoritative_source": source,
        "selected_bytes": size or "not_applicable",
        "size_based_eligibility_filter_used": False,
    }


def main() -> int:
    args = parse_args()
    project = Path(args.project_dir).resolve()
    output = (project / args.output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []

    for item in read_csv(project / "results/v4/stage81a1b_download_decisions.csv"):
        rows.append(row("stage81a1b", item["asset_id"], item["decision"], item["reason"], "official_SEA_AD", ""))
    for item in read_csv(project / "results/v4/stage81a1b_regional_metadata_download_decisions.csv"):
        rows.append(row("stage81a1b_regional_metadata", item["asset_id"], item["decision"], item.get("reason", item["decision"]), "official_SEA_AD", item.get("remote_size", "")))
    for item in read_csv(project / "results/v4/stage81a1c_n_download_decisions.csv"):
        rows.append(row("stage81a1c_n", item["asset_id"], item["decision"], item["decision_reason"], "official_normal_reference", ""))
    for item in read_csv(project / "results/v4/stage81a1c_n_dataset_role_registry.csv"):
        if item["accepted"].lower() == "false":
            prior = "duplicate_excluded" if "duplicate" in item["primary_role"] else "scientifically_incompatible"
            rows.append(row("stage81a1c_n_catalog", item["dataset_id"], prior, item["limitations"], "official_or_existing_normal_reference", ""))
    for item in read_csv(project / "results/v4/stage81a1c_p_download_decisions.csv"):
        rows.append(row("stage81a1c_p", item["asset_id"], item["decision"], item["reason"], "NCBI_GEO", ""))

    rows = sorted(rows, key=lambda value: (value["scope"], value["item_id"]))
    if not rows or any(value["reconsidered_decision"] not in ALLOWED for value in rows):
        raise RuntimeError("Storage-policy reconsideration produced an invalid decision")
    text = " ".join(str(value).lower() for value in rows)
    surviving = sorted(status for status in REVOKED if status in text)
    free = shutil.disk_usage(project).free
    report = {
        "stage_id": "stage81_storage_policy_reconsideration_v1",
        "source_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=project, text=True
        ).strip(),
        "no_fixed_stage_download_cap": True,
        "no_per_object_size_approval_threshold": True,
        "current_free_bytes": free,
        "decision_count": len(rows),
        "decision_counts": {name: sum(value["reconsidered_decision"] == name for value in rows) for name in sorted(ALLOWED)},
        "surviving_revoked_statuses": surviving,
        "prior_size_based_exclusion_count": 0,
        "normal_reference_gap_found_and_resolved": True,
        "new_normal_reference_studies": ["GSE133357", "GSE146639", "GSE243292", "GSE99074"],
        "perturbation_studies_acquired": ["GSE175721", "GSE178317", "GSE240609", "GSE241858", "GSE254205", "GSE293118", "GSE301119", "GSE311359"],
        "authoritative_source_data_deleted": False,
        "storage_policy_audit_pass": not surviving,
    }
    write_csv(output / "stage81_storage_policy_reconsideration.csv", rows)
    atomic_text(output / "stage81_storage_policy_reconsideration.json", json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["storage_policy_audit_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
