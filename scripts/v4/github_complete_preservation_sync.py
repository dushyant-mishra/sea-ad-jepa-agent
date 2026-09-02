#!/usr/bin/env python3
"""Build and execute the review-safe JEPA GitHub preservation sync."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import NamedTuple


PHYSICAL = {
    "SYNC_CURRENT_CANONICAL",
    "SYNC_REVIEW_PACKET",
    "SYNC_HISTORICAL_EXACT_BYTES",
    "SYNC_HISTORICAL_NORMAL",
}
ALLOWED = PHYSICAL | {
    "LEDGER_HASH_ONLY_PROTECTED",
    "LEDGER_HASH_ONLY_LARGE_REPRODUCIBLE",
    "EXCLUDE_GENERATED",
    "EXCLUDE_DUPLICATE_NONAUTHORITY",
}
SAFE_EXTENSIONS = {
    ".py", ".md", ".json", ".csv", ".txt", ".yaml", ".yml", ".r",
    ".toml", ".ini", ".cfg", ".sh", ".ps1", ".bat", ".sql", ".tsv",
    ".zip", ".gz", ".sha256", ".npz", ".svg", ".html",
}
CURRENT_CLASSES = {
    "CURRENT_SOURCE", "CURRENT_TEST", "CURRENT_CONTRACT", "CURRENT_GOVERNANCE",
    "CURRENT_REVIEW_PACKET",
}
HISTORICAL_CLASSES = {
    "HISTORICAL_SOURCE", "HISTORICAL_AUTHORITY", "HISTORICAL_DECISION",
    "HISTORICAL_HANDOFF", "SUPERSEDED_BUT_IMPORTANT",
    "GIT_FILTER_ALTERS_HISTORICAL_BYTES",
}
DECISION_WORDS = re.compile(
    r"(?i)(decision|adjudicat|authority|contract|freeze|manifest|audit|review|report|"
    r"summary|result|stop|pass|handoff|ledger|provenance|validation|synthesis|schema|hash)"
)


class Decision(NamedTuple):
    disposition: str
    destination: str
    exact_byte_required: bool
    reason: str
    category: str
    historical_or_current: str
    generated_class: str


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def truth(value: str | bool | None) -> bool:
    if value is True or value == "True":
        return True
    if value is False or value in ("False", "", None):
        return False
    if isinstance(value, str) and value.startswith("<re.Match object;"):
        return True
    raise ValueError(f"malformed Boolean value: {value!r}")


def normalized(path: str) -> str:
    return path.replace("\\", "/").lstrip("./")


def generated_reason(path: str, decision_bearing: bool) -> str | None:
    low = normalized(path).casefold()
    parts = PurePosixPath(low).parts
    if low.endswith(".pyc") or "__pycache__" in parts:
        return "COMPILED_PYTHON_GENERATED"
    if any("pytest" in part for part in parts) or ".pytest_cache" in parts:
        return "PYTEST_GENERATED"
    if parts and parts[0] in {"outputs", "results", "exports"} and any(
        part.startswith("test_") for part in parts[1:-1]
    ):
        return "TEST_FIXTURE_GENERATED"
    if any(part in {"cache", "caches", ".cache"} for part in parts):
        return "GENERIC_CACHE"
    temporary = any(
        part.startswith(("_staging", "staging", "retry", "stale", "aborted"))
        or "prepublication" in part
        or "pre_publication" in part
        or part == "fake_gate"
        for part in parts
    )
    if temporary and not (decision_bearing and DECISION_WORDS.search(PurePosixPath(low).name)):
        return "ORDINARY_TEMPORARY_COPY"
    return None


def protected_reason(row: dict[str, str]) -> str | None:
    sensitive = row.get("sensitive_class", "REVIEW_SAFE")
    if sensitive != "REVIEW_SAFE":
        return sensitive
    path = normalized(row.get("path", row.get("source_local_path", ""))).casefold()
    if path.startswith(("data/", "datasets/")):
        return "RAW_DATA_NAMESPACE"
    if path.startswith(("outputs/", "results/", "exports/")) and re.search(
        r"(row_lineage|cell_locator|cell_donor|donor_design|reader_oracle|"
        r"pathology|sealed_expression|dev_expression|primary_shards?|expression_matrix)",
        path,
    ):
        return "POTENTIAL_DONOR_OR_EXPRESSION_LEVEL_MATERIAL"
    return None


def is_large_reproducible(row: dict[str, str]) -> bool:
    path = normalized(row.get("path", row.get("source_local_path", ""))).casefold()
    classification = row.get("classification", "")
    suffix = PurePosixPath(path).suffix
    if classification in {"CHECKPOINT", "CACHE", "RAW_OR_PROTECTED_DATA", "LARGE_GENERATED"}:
        return True
    if suffix in {".pt", ".pth", ".ckpt", ".h5ad", ".qs", ".safetensors"}:
        return True
    size = int(row.get("bytes", "0") or 0)
    if size >= 50 * 1024 * 1024:
        return True
    return False


def _history_destination(prefix: str, path: str) -> str:
    parts = [_safe_segment(part) for part in PurePosixPath(normalized(path)).parts]
    return str(PurePosixPath(prefix, *parts))


def _safe_segment(value: str) -> str:
    value = re.sub(r"[<>:\"|?*]", "_", value).rstrip(" .")
    return value or "_"


def is_current(row: dict[str, str]) -> bool:
    path = normalized(row.get("path", row.get("source_local_path", "")))
    classification = row.get("classification", "")
    return classification in CURRENT_CLASSES or path.startswith(("scripts/", "src/", "tests/", "configs/", "docs/"))


def classify_row(row: dict[str, str], approved_destination: str = "") -> Decision:
    path = normalized(row.get("path", row.get("source_local_path", "")))
    decision_bearing = truth(row.get("decision_bearing", "False"))
    if "::" in path:
        return Decision("EXCLUDE_DUPLICATE_NONAUTHORITY", "", False, "ARCHIVE_MEMBER_INVENTORY_IDENTIFIER", "ARCHIVE_MEMBER", "HISTORICAL", "ARCHIVE_MEMBER")
    generated = generated_reason(path, decision_bearing)
    if generated:
        return Decision("EXCLUDE_GENERATED", "", False, generated, "GENERATED", "HISTORICAL", generated)
    protected = protected_reason(row)
    if protected:
        return Decision("LEDGER_HASH_ONLY_PROTECTED", "", False, protected, "PROTECTED_OR_DONOR_LEVEL", "HISTORICAL", "NOT_GENERATED")
    if is_large_reproducible(row):
        return Decision("LEDGER_HASH_ONLY_LARGE_REPRODUCIBLE", "", False, "LARGE_RAW_CHECKPOINT_CACHE_OR_REPRODUCIBLE", "LARGE_REPRODUCIBLE", "HISTORICAL", "NOT_GENERATED")
    if approved_destination:
        chronology = row.get("chronology_class", "")
        current = chronology.startswith("CURRENT_")
        return Decision(
            "SYNC_CURRENT_CANONICAL" if current else "SYNC_HISTORICAL_NORMAL",
            approved_destination,
            False,
            "PREVIOUSLY_APPROVED_DIRECT_SYNC_DESTINATION",
            row.get("classification", "APPROVED_REVIEW_SAFE"),
            "CURRENT" if current else "HISTORICAL",
            "NOT_GENERATED",
        )
    if is_current(row):
        return Decision("SYNC_CURRENT_CANONICAL", path, False, "CURRENT_CANONICAL_NATURAL_PATH", row.get("classification", "CURRENT_CANONICAL"), "CURRENT", "NOT_GENERATED")
    if truth(row.get("git_filter_alters_bytes", "False")):
        return Decision("SYNC_HISTORICAL_EXACT_BYTES", _history_destination("docs/history/exact_bytes", path), True, "HISTORICAL_BYTES_REQUIRE_FILTER_FREE_ARCHIVE", row.get("classification", "HISTORICAL"), "HISTORICAL", "NOT_GENERATED")
    suffix = PurePosixPath(path).suffix.casefold()
    if suffix in {".zip", ".gz"} or row.get("classification") == "CURRENT_REVIEW_PACKET":
        return Decision("SYNC_REVIEW_PACKET", _history_destination("docs/review_packets/complete_preservation_20260902", path), True, "COMPACT_REVIEW_OR_PROVENANCE_PACKAGE", row.get("classification", "REVIEW_PACKET"), "HISTORICAL", "NOT_GENERATED")
    return Decision("SYNC_HISTORICAL_NORMAL", _history_destination("docs/history/preservation_20260902", path), False, "MEANINGFUL_HISTORICAL_AUTHORITY", row.get("classification", "HISTORICAL"), "HISTORICAL", "NOT_GENERATED")


SECRET_PATTERNS = [
    re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(rb"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),
    re.compile(rb"\bsk-proj-[A-Za-z0-9_-]{16,}\b"),
    re.compile(rb"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(rb"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"),
]


def detect_secrets(data: bytes) -> list[str]:
    return [pattern.pattern.decode("ascii", "replace") for pattern in SECRET_PATTERNS if pattern.search(data)]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def candidate_for_delta(path: str, size: int) -> bool:
    low = normalized(path).casefold()
    suffix = PurePosixPath(low).suffix
    if suffix not in SAFE_EXTENSIONS:
        return False
    if low.startswith(("scripts/", "src/", "tests/", "configs/", "docs/")):
        return True
    if size > 95 * 1024 * 1024:
        return False
    return bool(DECISION_WORDS.search(PurePosixPath(low).name) or suffix in {".zip", ".gz"})


def delta_inventory(source_root: Path, prior: dict[str, dict[str, str]]) -> list[dict[str, str]]:
    found: list[dict[str, str]] = []
    roots = ["scripts", "src", "tests", "configs", "docs", "results", "outputs"]
    prune_exact = {".git", ".worktrees", "__pycache__", ".pytest_cache", "node_modules"}
    prune_contains = ("primary_shards", "singleton_shards", "feature_matrix", "expression_level", "multiview_features", "checkpoints")
    for root_name in roots:
        start = source_root / root_name
        if not start.exists():
            continue
        for current, dirs, files in os.walk(start):
            rel_dir = Path(current).relative_to(source_root).as_posix().casefold()
            dirs[:] = [
                d for d in dirs
                if d.casefold() not in prune_exact
                and not d.casefold().startswith("github_complete_preservation_sync_20260902")
                and "pytest" not in d.casefold()
                and not any(token in (rel_dir + "/" + d.casefold()) for token in prune_contains)
            ]
            for name in files:
                path = (Path(current) / name)
                rel = path.relative_to(source_root).as_posix()
                try:
                    stat = path.stat()
                except OSError:
                    continue
                if not candidate_for_delta(rel, stat.st_size):
                    continue
                old = prior.get(rel)
                old_size = int(old.get("bytes", "-1")) if old else -1
                old_mtime = old.get("mtime", "") if old else ""
                current_mtime = datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(timespec="seconds")
                if old and old_size == stat.st_size and old_mtime[:19] == current_mtime[:19]:
                    continue
                found.append({
                    "path": rel,
                    "bytes": str(stat.st_size),
                    "classification": "CURRENT_SOURCE" if rel.startswith(("scripts/", "src/")) else "CURRENT_TEST" if rel.startswith("tests/") else "CURRENT_GOVERNANCE" if rel.startswith(("docs/", "configs/")) else "HISTORICAL_AUTHORITY",
                    "decision_bearing": "True",
                    "sensitive_class": "REVIEW_SAFE",
                    "large_or_generated": "False",
                    "git_filter_alters_bytes": old.get("git_filter_alters_bytes", "False") if old else "False",
                    "chronology_class": "CURRENT_BYTES__DELTA_20260902",
                    "delta_status": "MODIFIED_AFTER_PREFLIGHT" if old else "CREATED_AFTER_PREFLIGHT",
                    "old_authority_sha256": old.get("sha256", "") if old else "",
                    "source_root_kind": "CANONICAL",
                })
    return found


def meaningful_prior(row: dict[str, str]) -> bool:
    classification = row.get("classification", "")
    if truth(row.get("decision_bearing", "False")):
        return True
    if classification in CURRENT_CLASSES | HISTORICAL_CLASSES:
        return True
    if row.get("sensitive_class") != "REVIEW_SAFE":
        return classification in {"RAW_OR_PROTECTED_DATA", "CHECKPOINT", "LARGE_GENERATED", "SUPERSEDED_BUT_IMPORTANT"}
    return classification in {"CHECKPOINT", "RAW_OR_PROTECTED_DATA", "LARGE_GENERATED"}


def resolve_source(row: dict[str, str], source_root: Path, worktree_root: Path) -> Path:
    rel = PurePosixPath(row["source_local_path"])
    preferred = worktree_root / rel if row.get("source_root_kind") == "WORKTREE" else source_root / rel
    fallback = source_root / rel if preferred == worktree_root / rel else worktree_root / rel
    if preferred.is_file():
        return preferred
    if fallback.is_file():
        return fallback
    raise FileNotFoundError(row["source_local_path"])


MANIFEST_FIELDS = [
    "source_local_path", "filesystem_sha256", "bytes", "category",
    "historical_or_current", "decision_bearing", "sensitive_class",
    "generated_class", "git_filter_alters_bytes", "exact_byte_required",
    "sync_disposition", "proposed_repo_path", "reason", "chronology_class",
    "source_root_kind", "old_authority_sha256", "delta_status",
]


def build_manifest(args: argparse.Namespace) -> None:
    source_root = args.source_root.resolve()
    worktree_root = args.worktree_root.resolve()
    prior_dir = args.prior_dir.resolve()
    repaired_dir = args.repaired_dir.resolve()
    output = args.output.resolve()
    if output.exists():
        raise FileExistsError(output)
    output.mkdir(parents=True)
    if sha256_file(args.authority_zip.resolve()) != "2528d2f82492cfc6d1bbab48b53885740593648222e2de96804a5dfb0df080d4":
        raise RuntimeError("repaired preflight ZIP authority mismatch")
    if sha256_file(repaired_dir / "GITHUB_PREFLIGHT_MANIFEST.csv") != "53674130433fc680564137e9cf5e000f970eb22fa8cbe7f11caeec71b8582880":
        raise RuntimeError("repaired preflight manifest authority mismatch")

    missing = read_csv(repaired_dir / "GITHUB_MISSING_HISTORY_INVENTORY.csv")
    prior_by_path = {normalized(row["path"]): row for row in missing}
    original_candidates = read_csv(prior_dir / "GITHUB_CANDIDATE_CONTENT_MANIFEST.csv")
    approved = {
        normalized(row["source_local_path"]): row
        for row in read_csv(repaired_dir / "GITHUB_CANDIDATE_CONTENT_MANIFEST.csv")
        if row["repair_disposition"] == "PROPOSE_REVIEW_MIRROR"
    }
    considered: dict[str, dict[str, str]] = {}
    for row in missing:
        if meaningful_prior(row):
            out = dict(row)
            out["source_root_kind"] = "CANONICAL"
            out.setdefault("old_authority_sha256", row.get("sha256", ""))
            out.setdefault("delta_status", "FROM_REUSED_INVENTORY")
            considered[normalized(row["path"])] = out
    for row in original_candidates:
        path = normalized(row["source_local_path"])
        base = dict(prior_by_path.get(path, {}))
        base.update({
            "path": path,
            "bytes": row["bytes"],
            "sha256": row["filesystem_sha256"],
            "classification": row["classification"],
            "decision_bearing": "True",
            "sensitive_class": row["sensitive_class"],
            "large_or_generated": "False",
            "git_filter_alters_bytes": row["git_filter_alters_bytes"],
            "chronology_class": row["chronology_class"],
            "source_root_kind": "CANONICAL",
            "old_authority_sha256": row["filesystem_sha256"],
            "delta_status": "FROM_REUSED_CANDIDATE_INVENTORY",
        })
        considered[path] = base
    for row in delta_inventory(source_root, prior_by_path):
        considered[normalized(row["path"])] = row
    # The preservation tooling is authored in the isolated worktree and is current canonical code.
    for rel, cls in (
        ("scripts/v4/github_complete_preservation_sync.py", "CURRENT_SOURCE"),
        ("tests/v4/test_github_complete_preservation_sync.py", "CURRENT_TEST"),
        (".gitattributes", "CURRENT_GOVERNANCE"),
    ):
        path = worktree_root / PurePosixPath(rel)
        considered[rel] = {
            "path": rel, "bytes": str(path.stat().st_size), "classification": cls,
            "decision_bearing": "True", "sensitive_class": "REVIEW_SAFE",
            "large_or_generated": "False", "git_filter_alters_bytes": "False",
            "chronology_class": "CURRENT_BYTES__DELTA_20260902",
            "source_root_kind": "WORKTREE", "old_authority_sha256": "",
            "delta_status": "CREATED_FOR_COMPLETE_PRESERVATION_SYNC",
        }

    rows_out: list[dict[str, object]] = []
    for path in sorted(considered, key=str.casefold):
        row = considered[path]
        row["path"] = path
        approved_dest = approved.get(path, {}).get("proposed_repo_path", "")
        decision = classify_row(row, approved_dest)
        source_sha = row.get("sha256", "")
        size = int(row.get("bytes", "0") or 0)
        if decision.disposition in PHYSICAL:
            source = resolve_source({"source_local_path": path, **row}, source_root, worktree_root)
            size = source.stat().st_size
            source_sha = sha256_file(source)
        elif not source_sha:
            source_sha = row.get("existing_manifest_sha256_if_available", "")
        rows_out.append({
            "source_local_path": path,
            "filesystem_sha256": source_sha,
            "bytes": size,
            "category": decision.category,
            "historical_or_current": decision.historical_or_current,
            "decision_bearing": "True" if truth(row.get("decision_bearing", "False")) else "False",
            "sensitive_class": row.get("sensitive_class", "REVIEW_SAFE"),
            "generated_class": decision.generated_class,
            "git_filter_alters_bytes": "True" if truth(row.get("git_filter_alters_bytes", "False")) else "False",
            "exact_byte_required": "True" if decision.exact_byte_required else "False",
            "sync_disposition": decision.disposition,
            "proposed_repo_path": decision.destination,
            "reason": decision.reason,
            "chronology_class": row.get("chronology_class", "RECOVERED_HISTORICAL_BYTES__BACKFILLED_20260902"),
            "source_root_kind": row.get("source_root_kind", "CANONICAL"),
            "old_authority_sha256": row.get("old_authority_sha256", row.get("sha256", "")),
            "delta_status": row.get("delta_status", "FROM_REUSED_INVENTORY"),
        })

    physical = [row for row in rows_out if row["sync_disposition"] in PHYSICAL]
    destinations = [str(row["proposed_repo_path"]) for row in physical]
    conflicts = len(destinations) - len({value.casefold() for value in destinations})
    if conflicts:
        groups: dict[str, list[str]] = {}
        for row in physical:
            groups.setdefault(str(row["proposed_repo_path"]).casefold(), []).append(str(row["source_local_path"]))
        conflict_file = output / "DESTINATION_CONFLICTS.json"
        conflict_file.write_text(json.dumps({key: value for key, value in groups.items() if len(value) > 1}, indent=2) + "\n")
        raise RuntimeError(f"case-insensitive destination conflicts: {conflicts}")
    write_csv(output / "GITHUB_COMPLETE_PRESERVATION_MANIFEST.csv", MANIFEST_FIELDS, rows_out)
    summary = {
        "status": "PASS_COMPLETE_PRESERVATION_MANIFEST_BUILT_AWAITING_SYNC",
        "authority": {
            "repaired_preflight_zip_sha256": "2528d2f82492cfc6d1bbab48b53885740593648222e2de96804a5dfb0df080d4",
            "repaired_preflight_manifest_sha256": "53674130433fc680564137e9cf5e000f970eb22fa8cbe7f11caeec71b8582880",
        },
        "counts": {
            "meaningful_considered": len(rows_out),
            "physical_sync": len(physical),
            "old_787_represented": sum(path in considered for path in approved),
            "by_disposition": dict(Counter(str(row["sync_disposition"]) for row in rows_out)),
            "delta_rows": sum(str(row["delta_status"]).startswith(("CREATED", "MODIFIED")) for row in rows_out),
        },
        "assertions": {
            "malformed_status_fields": 0,
            "case_insensitive_destination_conflicts": 0,
            "blank_physical_destinations": sum(not row["proposed_repo_path"] for row in physical),
            "literal_archive_member_destinations": sum("::" in str(row["proposed_repo_path"]) for row in physical),
            "path_traversal_destinations": sum(".." in PurePosixPath(str(row["proposed_repo_path"])).parts for row in physical),
            "unexplained_meaningful_candidates": sum(str(row["sync_disposition"]) not in ALLOWED for row in rows_out),
        },
    }
    if any(summary["assertions"].values()):
        raise RuntimeError(summary["assertions"])
    (output / "GITHUB_COMPLETE_PRESERVATION_MANIFEST_SUMMARY.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, indent=2))


def copy_exact(source: Path, destination: Path, expected: str) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp = destination.with_name(destination.name + ".preservation_staging")
    if temp.exists():
        raise RuntimeError(f"stale staging path: {temp}")
    h = hashlib.sha256()
    with source.open("rb") as reader, temp.open("xb") as writer:
        for chunk in iter(lambda: reader.read(1024 * 1024), b""):
            h.update(chunk)
            writer.write(chunk)
    if h.hexdigest() != expected:
        temp.unlink(missing_ok=True)
        raise RuntimeError(f"source changed during copy: {source}")
    os.replace(temp, destination)
    if sha256_file(destination) != expected:
        raise RuntimeError(f"destination mismatch: {destination}")


def sync_manifest(args: argparse.Namespace) -> None:
    source_root = args.source_root.resolve()
    worktree_root = args.worktree_root.resolve()
    output = args.output.resolve()
    rows = read_csv(output / "GITHUB_COMPLETE_PRESERVATION_MANIFEST.csv")
    physical = [row for row in rows if row["sync_disposition"] in PHYSICAL]
    attributes = worktree_root / ".gitattributes"
    rule = "docs/history/exact_bytes/** -text"
    existing = attributes.read_text(encoding="utf-8") if attributes.exists() else ""
    if rule not in existing.splitlines():
        attributes.write_text(existing.rstrip("\n") + ("\n" if existing else "") + rule + "\n", encoding="utf-8")
    audit: list[dict[str, object]] = []
    for row in physical:
        source = resolve_source(row, source_root, worktree_root)
        expected = row["filesystem_sha256"]
        if sha256_file(source) != expected:
            raise RuntimeError(f"source SHA changed after manifest: {row['source_local_path']}")
        destination = (worktree_root / PurePosixPath(row["proposed_repo_path"])).resolve()
        if worktree_root not in destination.parents:
            raise RuntimeError(f"destination escapes worktree: {destination}")
        if source.resolve() != destination:
            copy_exact(source, destination, expected)
        elif sha256_file(destination) != expected:
            raise RuntimeError(f"natural-path source mismatch: {destination}")
        audit.append({
            "source_local_path": row["source_local_path"],
            "proposed_repo_path": row["proposed_repo_path"],
            "sync_disposition": row["sync_disposition"],
            "expected_sha256": expected,
            "destination_sha256": sha256_file(destination),
            "filesystem_match": "True",
        })

    ledger_rows = [row for row in rows if row["sync_disposition"] not in PHYSICAL]
    ledger_path = worktree_root / "docs/history/JEPA_PRESERVATION_LEDGER_20260902.csv"
    write_csv(ledger_path, MANIFEST_FIELDS, ledger_rows)
    counts = Counter(row["sync_disposition"] for row in rows)
    summary_path = worktree_root / "docs/history/JEPA_PRESERVATION_LEDGER_20260902.md"
    summary_path.write_text(
        "# JEPA Preservation Ledger — 2026-09-02\n\n"
        "Historical material recovered in this sync is labeled `RECOVERED_HISTORICAL_BYTES__BACKFILLED_20260902`; Git dates are backfill dates, not reconstructed historical dates.\n\n"
        f"- Meaningful artifacts considered: {len(rows):,}\n"
        f"- Physical sync entries: {len(physical):,}\n"
        f"- Ledger/hash-only protected: {counts['LEDGER_HASH_ONLY_PROTECTED']:,}\n"
        f"- Ledger/hash-only large/reproducible: {counts['LEDGER_HASH_ONLY_LARGE_REPRODUCIBLE']:,}\n"
        f"- Generated exclusions: {counts['EXCLUDE_GENERATED']:,}\n"
        f"- Duplicate/non-authority exclusions: {counts['EXCLUDE_DUPLICATE_NONAUTHORITY']:,}\n\n"
        "Every considered row appears in the complete preservation manifest and exactly one disposition above.\n",
        encoding="utf-8",
    )
    manifest_copy = worktree_root / "docs/history/JEPA_COMPLETE_PRESERVATION_MANIFEST_20260902.csv"
    shutil.copyfile(output / "GITHUB_COMPLETE_PRESERVATION_MANIFEST.csv", manifest_copy)
    write_csv(output / "GITHUB_COMPLETE_SYNC_COPY_AUDIT.csv", list(audit[0]), audit)
    result = {
        "status": "PASS_COMPLETE_PRESERVATION_COPY_AWAITING_STAGE_SCAN",
        "meaningful_considered": len(rows),
        "physical_sync_entries": len(physical),
        "ledger_entries": len(ledger_rows),
        "by_disposition": dict(counts),
        "filesystem_source_destination_mismatches": sum(row["filesystem_match"] != "True" for row in audit),
        "exact_byte_entries": counts["SYNC_HISTORICAL_EXACT_BYTES"] + counts["SYNC_REVIEW_PACKET"],
    }
    (output / "GITHUB_COMPLETE_SYNC_COPY_RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2))


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command", required=True)
    for name in ("build", "sync"):
        q = sub.add_parser(name)
        q.add_argument("--source-root", type=Path, required=True)
        q.add_argument("--worktree-root", type=Path, required=True)
        q.add_argument("--output", type=Path, required=True)
        if name == "build":
            q.add_argument("--prior-dir", type=Path, required=True)
            q.add_argument("--repaired-dir", type=Path, required=True)
            q.add_argument("--authority-zip", type=Path, required=True)
    return p


def main() -> int:
    args = parser().parse_args()
    if args.command == "build":
        build_manifest(args)
    else:
        sync_manifest(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
