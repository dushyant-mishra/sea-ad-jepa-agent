#!/usr/bin/env python3
"""Repair the frozen GitHub review-mirror preflight without rescanning files."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import shutil
from collections import Counter
from pathlib import Path, PurePosixPath


BOOLEAN_FIELDS = {
    "git_present_exact",
    "git_present_different",
    "decision_bearing",
    "sensitive_or_protected",
    "large_or_generated",
    "fresh_hash_performed",
    "git_filter_alters_bytes",
    "exact_byte_preservation_possible",
}

DIRECT_SYNC = "PROPOSE_REVIEW_MIRROR"
LEDGER_DONOR = "LEDGER_HASH_ONLY_DONOR_LEVEL"
LEDGER_FILTER = "LEDGER_HASH_ONLY_GIT_FILTER_ALTERED"
LEDGER_ARCHIVE = "LEDGER_HASH_ONLY_ARCHIVE_MEMBER"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def normalize_boolean(value: str) -> str:
    """Normalize the original serialized provenance flag without weakening it."""
    if value in ("True", "False"):
        return value
    if value == "":
        return "False"
    if re.fullmatch(r"<re\.Match object;.*>", value):
        return "True"
    raise ValueError(f"unrecognized Boolean provenance value: {value!r}")


def normalize_boolean_fields(row: dict[str, str]) -> dict[str, str]:
    out = dict(row)
    for field in BOOLEAN_FIELDS.intersection(out):
        out[field] = normalize_boolean(out[field])
    return out


def default_exclusion_reason(source_path: str) -> str | None:
    """Return a narrow default exclusion for generated historical output trees."""
    path = source_path.replace("\\", "/")
    low = path.casefold()
    if not low.startswith(("outputs/", "exports/", "results/", "archive/")):
        return None
    if "pytest" in low:
        return "PYTEST_GENERATED_OUTPUT"
    segments = [segment.casefold() for segment in PurePosixPath(path).parts]
    for segment in segments:
        if (
            segment.startswith("_staging")
            or segment == "staging"
            or "prepublication" in segment
            or "pre_publication" in segment
            or "concern_unexecuted" in segment
            or segment.startswith("failed")
            or "failed_review" in segment
            or segment.startswith("retry")
            or segment.startswith("stale")
            or segment == "fake_gate"
            or segment.startswith("aborted")
        ):
            return f"NONCANONICAL_OUTPUT_COPY:{segment}"
    return None


def disposition_for(row: dict[str, str]) -> str:
    source = row.get("source_local_path", row.get("path", ""))
    if "::" in source:
        return LEDGER_ARCHIVE
    if row.get("sensitive_class") == "DONOR_LEVEL_HUMAN_DATA_REVIEW_REQUIRED":
        return LEDGER_DONOR
    if normalize_boolean(row.get("git_filter_alters_bytes", "False")) == "True":
        return LEDGER_FILTER
    return DIRECT_SYNC


def _safe_segment(segment: str) -> str:
    cleaned = re.sub(r"[<>:\"|?*]", "_", segment).rstrip(" .")
    return cleaned or "_"


def historical_destination(source_path: str) -> str:
    source = source_path.replace("\\", "/")
    if "::" in source:
        raise ValueError("archive member identifiers are inventory-only")
    parts = list(PurePosixPath(source).parts)
    if parts and parts[0].casefold() == "outputs":
        parts = parts[1:]
    elif parts and parts[0].casefold() in {"exports", "archive"}:
        pass
    return str(PurePosixPath("docs", "history", *(_safe_segment(x) for x in parts)))


def assign_unique_destinations(rows: list[dict[str, str]]) -> list[str]:
    assigned: list[str] = []
    used: set[str] = set()
    for row in rows:
        base = historical_destination(row["source_local_path"])
        candidate = base
        key = candidate.casefold()
        if key in used:
            stem, suffix = os.path.splitext(base)
            digest = row.get("filesystem_sha256", row.get("sha256", ""))[:12] or "nohash"
            candidate = f"{stem}__sha256_{digest}{suffix}"
            key = candidate.casefold()
            counter = 2
            while key in used:
                candidate = f"{stem}__sha256_{digest}_{counter}{suffix}"
                key = candidate.casefold()
                counter += 1
        used.add(key)
        assigned.append(candidate)
    return assigned


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), [normalize_boolean_fields(row) for row in reader]


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def candidate_repair(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], Counter]:
    kept: list[dict[str, str]] = []
    excluded = Counter()
    for row in rows:
        reason = default_exclusion_reason(row["source_local_path"])
        if reason:
            excluded[reason.split(":", 1)[0]] += 1
            continue
        out = dict(row)
        disposition = disposition_for(out)
        out["repair_disposition"] = disposition
        out["repair_reason"] = ""
        if disposition != DIRECT_SYNC:
            out["proposed_repo_path"] = ""
            out["recommended_action"] = disposition
            out["repair_reason"] = disposition
        kept.append(out)

    direct = [row for row in kept if row["repair_disposition"] == DIRECT_SYNC]
    historical = [
        row
        for row in direct
        if row["source_local_path"].replace("\\", "/").casefold().startswith(("outputs/", "exports/", "archive/"))
        or row["classification"].startswith("HISTORICAL_")
        or row["classification"] == "SUPERSEDED_BUT_IMPORTANT"
    ]
    new_paths = assign_unique_destinations(historical)
    for row, path in zip(historical, new_paths):
        row["proposed_repo_path"] = path
    # Fail closed if any remaining direct destination is blank or case-insensitively duplicated.
    paths = [row["proposed_repo_path"] for row in direct]
    if any(not path for path in paths):
        raise RuntimeError("direct sync candidate has no proposed_repo_path")
    if len(paths) != len({path.casefold() for path in paths}):
        raise RuntimeError("conflicting proposed_repo_path remains after repair")
    return kept, excluded


def git_revision(repo: Path, revision: str) -> str:
    import subprocess

    return subprocess.run(
        ["git", "rev-parse", revision],
        cwd=repo,
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    ).stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repo", type=Path, required=True)
    args = parser.parse_args()
    input_dir = args.input.resolve()
    output_dir = args.output.resolve()
    staging = output_dir.with_name(output_dir.name + ".staging")
    if output_dir.exists() or staging.exists():
        raise FileExistsError("fresh output and staging paths are required")
    staging.mkdir(parents=True)
    initial_head = git_revision(args.repo, "HEAD")
    initial_origin_main = git_revision(args.repo, "refs/remotes/origin/main")

    source_names = [
        "GITHUB_REMOTE_BASELINE.json",
        "GITHUB_MISSING_HISTORY_INVENTORY.csv",
        "GITHUB_CURRENT_REVIEW_SURFACE.csv",
        "GITHUB_EXCLUDED_SENSITIVE_LARGE.csv",
        "GITHUB_CANDIDATE_CONTENT_MANIFEST.csv",
        "GITHUB_KNOWN_HISTORY_GAPS.md",
    ]
    input_hashes = {name: sha256_file(input_dir / name) for name in source_names}

    # Repair every inherited CSV carrying Boolean provenance fields.
    repaired_tables: dict[str, tuple[list[str], list[dict[str, str]]]] = {}
    for name in (
        "GITHUB_MISSING_HISTORY_INVENTORY.csv",
        "GITHUB_CURRENT_REVIEW_SURFACE.csv",
        "GITHUB_EXCLUDED_SENSITIVE_LARGE.csv",
    ):
        repaired_tables[name] = read_csv(input_dir / name)
        write_csv(staging / name, *repaired_tables[name])

    fields, original_candidates = read_csv(input_dir / "GITHUB_CANDIDATE_CONTENT_MANIFEST.csv")
    candidates, excluded_counts = candidate_repair(original_candidates)
    candidate_fields = fields + ["repair_disposition", "repair_reason"]
    write_csv(staging / "GITHUB_CANDIDATE_CONTENT_MANIFEST.csv", candidate_fields, candidates)

    back_fields, original_backfill = read_csv(input_dir / "GITHUB_PROPOSED_HISTORICAL_BACKFILL.csv")
    by_source = {row["source_local_path"]: row for row in candidates}
    backfill: list[dict[str, str]] = []
    for row in original_backfill:
        candidate = by_source.get(row["path"])
        if not candidate or candidate["repair_disposition"] != DIRECT_SYNC:
            continue
        out = dict(row)
        out["proposed_repo_path"] = candidate["proposed_repo_path"]
        out["recommended_action"] = DIRECT_SYNC
        out["repair_disposition"] = DIRECT_SYNC
        out["repair_reason"] = ""
        backfill.append(out)
    back_fields = back_fields + ["repair_disposition", "repair_reason"]
    write_csv(staging / "GITHUB_PROPOSED_HISTORICAL_BACKFILL.csv", back_fields, backfill)

    shutil.copy2(input_dir / "GITHUB_REMOTE_BASELINE.json", staging / "GITHUB_REMOTE_BASELINE.json")
    shutil.copy2(input_dir / "GITHUB_KNOWN_HISTORY_GAPS.md", staging / "GITHUB_KNOWN_HISTORY_GAPS.md")

    boolean_bad = 0
    for _, rows in repaired_tables.values():
        for row in rows:
            boolean_bad += sum(row[field] not in {"True", "False"} for field in BOOLEAN_FIELDS.intersection(row))
    for row in candidates:
        boolean_bad += sum(row[field] not in {"True", "False"} for field in BOOLEAN_FIELDS.intersection(row))
    direct = [row for row in candidates if row["repair_disposition"] == DIRECT_SYNC]
    direct_paths = [row["proposed_repo_path"] for row in direct]
    assertions = {
        "terminal_status": "PASS_GITHUB_REVIEW_MIRROR_PREFLIGHT_REPAIR_AWAITING_EXTERNAL_REVIEW",
        "source_preflight_manifest_sha256": sha256_file(input_dir / "GITHUB_PREFLIGHT_MANIFEST.csv"),
        "source_package_sha256_reviewed": "9b9701387f1cf071add367f6c2ad71d986a90b07585cc7d77f3640fcce2771c4",
        "input_hashes": input_hashes,
        "counts": {
            "original_candidates": len(original_candidates),
            "repaired_candidates_including_ledger_only": len(candidates),
            "direct_sync_candidates": len(direct),
            "historical_backfill": len(backfill),
            "ledger_only_donor": sum(row["repair_disposition"] == LEDGER_DONOR for row in candidates),
            "ledger_only_git_filter_altered": sum(row["repair_disposition"] == LEDGER_FILTER for row in candidates),
            "excluded_by_default": dict(excluded_counts),
        },
        "assertions": {
            "conflicting_proposed_repo_paths": len(direct_paths) - len({x.casefold() for x in direct_paths}),
            "malformed_boolean_fields": boolean_bad,
            "donor_level_sync_candidates": sum(
                row["repair_disposition"] == DIRECT_SYNC
                and row["sensitive_class"] == "DONOR_LEVEL_HUMAN_DATA_REVIEW_REQUIRED"
                for row in candidates
            ),
            "pytest_output_backfill": sum("pytest" in row["path"].casefold() for row in backfill),
            "git_filter_altered_direct_sync": sum(
                row["repair_disposition"] == DIRECT_SYNC and row["git_filter_alters_bytes"] == "True"
                for row in candidates
            ),
            "archive_member_literal_repo_paths": sum("::" in path for path in direct_paths),
            "commit_performed": False,
            "push_performed": False,
        },
        "chronology_class": "RECOVERED_HISTORICAL_BYTES__BACKFILLED_20260902",
        "git_identity": {
            "head_before": initial_head,
            "origin_main_before": initial_origin_main,
        },
        "notes": [
            "No filesystem rescan was performed; this repair derives from the frozen preflight CSVs.",
            "Archive ZIP member identifiers remain inventory-only and are never literal repository paths.",
            "No pytest recovered-authority exception was allowlisted in this repair.",
            "Git-filter-altered and donor-level bytes are ledger/hash-only, not direct sync candidates.",
        ],
    }
    required_zero = [
        "conflicting_proposed_repo_paths",
        "malformed_boolean_fields",
        "donor_level_sync_candidates",
        "pytest_output_backfill",
        "git_filter_altered_direct_sync",
        "archive_member_literal_repo_paths",
    ]
    if any(assertions["assertions"][key] != 0 for key in required_zero):
        raise RuntimeError(f"repair assertions failed: {assertions['assertions']}")
    (staging / "GITHUB_PREFLIGHT_REPAIR_ASSERTIONS.json").write_text(
        json.dumps(assertions, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    plan = f"""# GitHub Review-Mirror Sync Plan — Repaired Preflight

Terminal: `PASS_GITHUB_REVIEW_MIRROR_PREFLIGHT_REPAIR_AWAITING_EXTERNAL_REVIEW`

No commit or push is authorized by this package.

## Mechanical repair

- Direct sync candidates: {len(direct):,}
- Historical backfill candidates: {len(backfill):,}
- Donor-level ledger/hash-only rows: {assertions['counts']['ledger_only_donor']}
- Git-filter-altered ledger/hash-only rows: {assertions['counts']['ledger_only_git_filter_altered']}
- Pytest-generated historical outputs proposed for backfill: 0
- Conflicting proposed repository destinations: 0
- Malformed Boolean provenance fields: 0

Historical destinations preserve their source run/stage/version hierarchy under `docs/history/`.
Generated pytest trees and staging/prepublication/failed/retry copies are excluded by default.
The chronology label remains `RECOVERED_HISTORICAL_BYTES__BACKFILLED_20260902`.

External review is required before any backfill commit or push.
"""
    (staging / "GITHUB_PROPOSED_SYNC_PLAN.md").write_text(plan, encoding="utf-8")

    final_head = git_revision(args.repo, "HEAD")
    final_origin_main = git_revision(args.repo, "refs/remotes/origin/main")
    if final_head != initial_head or final_origin_main != initial_origin_main:
        raise RuntimeError("Git revision identity changed during repair")

    manifest_name = "GITHUB_PREFLIGHT_MANIFEST.csv"
    members = sorted(path for path in staging.iterdir() if path.name != manifest_name)
    manifest_rows = [
        {"path": path.name, "bytes": str(path.stat().st_size), "sha256": sha256_file(path)}
        for path in members
    ]
    write_csv(staging / manifest_name, ["path", "bytes", "sha256"], manifest_rows)
    staging.replace(output_dir)
    print(json.dumps({
        "status": assertions["terminal_status"],
        "output": str(output_dir),
        "manifest_sha256": sha256_file(output_dir / manifest_name),
        "counts": assertions["counts"],
        "assertions": assertions["assertions"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
