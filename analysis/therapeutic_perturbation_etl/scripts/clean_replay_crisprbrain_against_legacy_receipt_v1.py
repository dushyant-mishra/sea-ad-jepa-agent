#!/usr/bin/env python3
"""Fail-closed clean-head physical CRISPRbrain replay of the dirty 2026-09-25 receipt.

Unlike the historical strict-replay script, this creates a NEW evidence
generation at the current clean committed head and compares to the original
dirty result. It never changes the original receipt or claims its historical
worktree was clean. Use only in a disposable clean checkout: the producer
regenerates its already-committed evidence CSVs/receipt at their existing paths.
No protected JEPA data or training is accessed.
"""
from __future__ import annotations

import argparse
from collections.abc import Mapping
import hashlib
import json
from pathlib import Path
import subprocess
import sys

REPO_REL = Path("analysis/therapeutic_perturbation_etl")
RECEIPT_REL = REPO_REL / "evidence/crisprbrain_reliability/CRISPRBRAIN_SCREEN_RELIABILITY_RECEIPT_V1.json"
PRODUCER_REL = REPO_REL / "scripts/assess_crisprbrain_screen_reliability_v1.py"
ORIGINAL_DIRTY_HEAD = "b2ae68e03a96e45b6d1963ca86ae3d7b646c19a3"
# Exclusions are strictly non-scientific generation metadata. Inputs and
# outputs are compared in full, not excluded.
VOLATILE = frozenset({"generated_utc", "environment", "git_head", "git_dirty"})


class ReplayError(RuntimeError):
    """An explicit failure is required; never emit a green partial receipt."""


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def flatten(value: object, path: str = ""):
    if isinstance(value, dict):
        for k in sorted(value):
            yield from flatten(value[k], path + "/" + str(k))
    elif isinstance(value, list):
        for i, val in enumerate(value):
            yield from flatten(val, path + "/" + str(i))
    else:
        yield path, value


def compare_scientific_fields(original: Mapping, fresh: Mapping) -> dict[str, object]:
    """Strict comparison of every field except four explicitly volatile fields."""
    old = dict(flatten({k: v for k, v in original.items() if k not in VOLATILE}))
    new = dict(flatten({k: v for k, v in fresh.items() if k not in VOLATILE}))
    errors = []
    for k in sorted(old.keys() | new.keys()):
        if k not in old:
            errors.append("only in clean replay: " + k)
        elif k not in new:
            errors.append("only in historical result: " + k)
        elif type(old[k]) is not type(new[k]) or old[k] != new[k]:
            errors.append("value changed: " + k)
    return {
        "fields_compared": len(old.keys() | new.keys()),
        "fields_exact_match": len(errors) == 0,
        "different_field_paths": errors[:40],
        "different_field_count": len(errors),
    }


def validate_original_outputs(repo: Path, original: Mapping) -> list[dict]:
    """Rehash all seven committed small CSVs BEFORE the producer overwrites them."""
    outputs = original.get("outputs")
    if not isinstance(outputs, list) or len(outputs) != 7:
        raise ReplayError("historical receipt must declare exactly seven CSV outputs")
    expected_names = {
        "concordance_by_abundance.csv",
        "fdr_threshold_sensitivity.csv",
        "jointly_significant_rows.csv",
        "non_replication_classification.csv",
        "per_target_concordance.csv",
        "target_engagement.csv",
        "target_identity.csv",
    }
    if {Path(o.get("path", "")).name for o in outputs} != expected_names:
        raise ReplayError("historical output census differs from seven frozen tables")
    root = repo.resolve()
    verified = []
    seen = set()
    for item in outputs:
        raw = str(item["path"])
        path = (root / raw).resolve()
        if raw in seen or path != (root / RECEIPT_REL.parent / path.name).resolve():
            raise ReplayError("duplicate/path-escaped or unexpected historical output: " + raw)
        seen.add(raw)
        if not path.is_file() or sha256_file(path) != item["sha256"]:
            raise ReplayError("committed output absent or hash drift: " + raw)
        verified.append({
            "relative_path": raw,
            "rows_in_original_receipt": item["rows"],
            "original_sha256": item["sha256"],
        })
    return verified


def replay(repo: Path, report: Path) -> dict[str, object]:
    repo = repo.resolve()
    report = report.resolve()
    if report.exists():
        raise ReplayError("refuse to overwrite an existing clean-replay report")
    if repo == report or repo in report.parents:
        raise ReplayError("clean-replay report must be OUTSIDE checked-out repo")
    current_head = git(repo, "rev-parse", "HEAD")
    if len(current_head) != 40 or git(repo, "status", "--porcelain"):
        raise ReplayError("STOP: must start from a clean exact-commit checkout")
    receipt_path = repo / RECEIPT_REL
    producer = repo / PRODUCER_REL
    if not producer.is_file() or not receipt_path.is_file():
        raise ReplayError("source producer or original receipt absent in clean checkout")
    original_receipt_sha = sha256_file(receipt_path)
    old = json.loads(receipt_path.read_text(encoding="utf-8"))
    if old.get("git_dirty") is not True or old.get("git_head") != ORIGINAL_DIRTY_HEAD:
        raise ReplayError("original receipt is not the expected historically dirty source")
    if old.get("status") != "COMPLETE":
        raise ReplayError("original result was not complete")
    if sha256_file(producer) != old.get("producer_sha256"):
        raise ReplayError("committed producer source SHA differs from executed dirty receipt")
    committed_tables = validate_original_outputs(repo, old)
    original_inputs = old.get("inputs")
    if not isinstance(original_inputs, list) or len(original_inputs) != 8:
        raise ReplayError("original input SHA census is incomplete")
    if not all(x.get("digest_match") is True for x in original_inputs):
        raise ReplayError("historical receipt declared missing or mismatched inputs")

    # No separate outdir: the existing producer calls p.relative_to(repo).
    # Running it in a disposable clean checkout at the SAME relative paths
    # preserves the original output path grammar and exact 7-table census.
    cmd = [sys.executable, str(producer), "--repo", str(repo)]
    proc = subprocess.run(cmd, text=True, capture_output=True, timeout=1500)
    if proc.returncode:
        raise ReplayError(
            "physical producer failed in clean checkout (exit %d): %s"
            % (proc.returncode, (proc.stderr + "\n" + proc.stdout)[-2200:])
        )
    fresh = json.loads(receipt_path.read_text(encoding="utf-8"))
    if fresh.get("git_head") != current_head or fresh.get("git_dirty") is not False:
        raise ReplayError("new producer execution lacked a clean-head provenance record")
    if fresh.get("producer_sha256") != old["producer_sha256"]:
        raise ReplayError("producer SHA changed across executions")
    if fresh.get("inputs") != original_inputs:
        raise ReplayError("physical input SHA receipts differ from historical inputs")
    if fresh.get("outputs") != old["outputs"]:
        raise ReplayError("physical output rows/digests/paths differ from original receipt")
    for original in committed_tables:
        p = repo / original["relative_path"]
        if sha256_file(p) != original["original_sha256"]:
            raise ReplayError("regenerated CSV bytes differ: " + original["relative_path"])
    scientific = compare_scientific_fields(old, fresh)
    if not scientific["fields_exact_match"]:
        raise ReplayError(
            "%d receipt scientific fields changed; first paths: %s"
            % (scientific["different_field_count"], scientific["different_field_paths"][:12])
        )
    changed = git(repo, "status", "--porcelain", "--untracked-files=all").splitlines()
    expected_changed = {RECEIPT_REL.as_posix()} | {
        Path(row["relative_path"]).as_posix() for row in committed_tables
    }
    unexpected = []
    for entry in changed:
        p = entry[3:].strip().strip('"').replace("\\", "/")
        if p not in expected_changed:
            unexpected.append(p)
    if unexpected:
        raise ReplayError("clean-run generated unauthorized files: " + repr(unexpected[:8]))

    audit = {
        "schema": "V26_CRISPRBRAIN_CLEAN_HEAD_PHYSICAL_REPLAY_V1",
        "status": "CLEAN_HEAD_PHYSICALLY_REPLAYED_AND_EXACTLY_REPRODUCED",
        "independent_replay_source_commit": current_head,
        "initial_worktree_clean": True,
        "historical_receipt_git_dirty": True,
        "historical_receipt_git_head": ORIGINAL_DIRTY_HEAD,
        "historical_receipt_sha256": original_receipt_sha,
        "historical_producer_sha256": old["producer_sha256"],
        "clean_producer_sha256": fresh["producer_sha256"],
        "clean_generated_receipt_sha256": sha256_file(receipt_path),
        "eight_input_receipts_match_exactly": True,
        "original_outputs_authenticated_before_replay": len(committed_tables),
        "regenerated_csv_sha256_exact_matches": len(committed_tables),
        "scientific_fields_compared": scientific["fields_compared"],
        "scientific_fields_equal": scientific["fields_exact_match"],
        "source_scope": "SAME_PUBLIC_GSE335887_SCREEN_TABLES__WITHIN_STUDY_PROTOCOL_COMPARISON_ONLY",
        "readout_gene_identity": "SYMBOL_ONLY__NO_AUTHENTICATED_READOUT_ENSEMBL_ID",
        "training_authorized": False,
        "scientifically_qualified_for_independent_replication": False,
        "protected_outcomes_opened": False,
    }
    report.parent.mkdir(parents=True, exist_ok=True)
    with report.open("x", encoding="utf-8") as f:
        json.dump(audit, f, indent=2, sort_keys=True)
        f.write("\n")
    return audit


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", type=Path, default=Path("."))
    ap.add_argument("--report", type=Path, required=True)
    args = ap.parse_args()
    try:
        audit = replay(args.repo, args.report)
    except (ReplayError, subprocess.CalledProcessError, OSError, ValueError) as exc:
        print("STOP_CRISPRBRAIN_CLEAN_REPLAY: " + str(exc), file=sys.stderr)
        return 1
    print("CLEAN_REPLAY_REPORT_JSON=" + json.dumps(audit, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
