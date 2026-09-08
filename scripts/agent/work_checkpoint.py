#!/usr/bin/env python3
"""Build and validate deterministic, agent-neutral JEPA work checkpoints."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any


REQUIRED_STATE_FIELDS = (
    "active_agent",
    "authorities",
    "gates",
    "unresolved_blockers",
    "assets",
    "next_authorized_actions",
    "allowed_tracked_modifications",
    "allowed_untracked_files",
)


def canonical_json_bytes(value: Any) -> bytes:
    """Return deterministic UTF-8 JSON bytes for JSON-compatible *value*."""
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def semantic_sha256(payload: dict[str, Any]) -> str:
    """Hash a checkpoint excluding only its self-referential root field."""
    semantic = copy.deepcopy(payload)
    semantic.pop("checkpoint_semantic_sha256", None)
    return hashlib.sha256(canonical_json_bytes(semantic)).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git(worktree: Path, *args: str, allow_failure: bool = False) -> str | None:
    completed = subprocess.run(
        ["git", "-c", "safe.directory=*", "-C", str(worktree), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode:
        if allow_failure:
            return None
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise RuntimeError(f"git {' '.join(args)} failed: {detail}")
    return completed.stdout.strip()


def resolve_canonical_repo(worktree: Path) -> Path:
    """Return the canonical repository root that owns *worktree*.

    A linked worktree resolves to the repository holding the shared object
    store, not to itself. This lets an arriving peer validate a checkpoint
    knowing only its own worktree, without hardcoding the canonical path.
    """
    common = _git(Path(worktree), "rev-parse", "--git-common-dir")
    common_path = Path(common or ".git")
    if not common_path.is_absolute():
        common_path = Path(worktree) / common_path
    return common_path.resolve().parent


def _git_snapshot(repo: Path, worktree: Path) -> dict[str, Any]:
    head = _git(worktree, "rev-parse", "HEAD")
    branch = _git(worktree, "branch", "--show-current")
    origin_main = _git(worktree, "rev-parse", "origin/main", allow_failure=True)
    remote_url = _git(repo, "remote", "get-url", "origin", allow_failure=True)
    tracked = sorted(
        set(
            filter(
                None,
                (_git(worktree, "diff", "--name-only", "--relative") or "").splitlines()
                + (
                    _git(worktree, "diff", "--cached", "--name-only", "--relative")
                    or ""
                ).splitlines(),
            )
        )
    )
    untracked = sorted(
        filter(
            None,
            (
                _git(worktree, "ls-files", "--others", "--exclude-standard") or ""
            ).splitlines(),
        )
    )
    return {
        "repo_path": str(repo.resolve()),
        "worktree_path": str(worktree.resolve()),
        "branch": branch,
        "head_sha": head,
        "origin_main_sha": origin_main,
        "origin_url": remote_url,
        "tracked_modifications": tracked,
        "untracked_files": untracked,
    }


def build_checkpoint(repo: Path, worktree: Path, state: dict[str, Any]) -> dict[str, Any]:
    """Bind declared scientific/engineering state to the current Git/filesystem state."""
    missing = [key for key in REQUIRED_STATE_FIELDS if key not in state]
    if missing:
        raise ValueError(f"missing required state fields: {missing}")
    checkpoint = copy.deepcopy(state)
    checkpoint["schema"] = "JEPA_WORK_CHECKPOINT_V1"
    checkpoint["git"] = _git_snapshot(Path(repo), Path(worktree))
    checkpoint["checkpoint_semantic_sha256"] = semantic_sha256(checkpoint)
    return checkpoint


def validate_checkpoint(
    checkpoint: dict[str, Any], repo: Path, worktree: Path
) -> list[str]:
    """Return all fail-closed checkpoint mismatches; an empty list means PASS."""
    errors: list[str] = []
    if checkpoint.get("schema") != "JEPA_WORK_CHECKPOINT_V1":
        errors.append("SCHEMA_MISMATCH")
    if checkpoint.get("checkpoint_semantic_sha256") != semantic_sha256(checkpoint):
        errors.append("CHECKPOINT_SEMANTIC_SHA256_MISMATCH")

    try:
        actual = _git_snapshot(Path(repo), Path(worktree))
    except RuntimeError as exc:
        return errors + [f"GIT_STATE_UNAVAILABLE:{exc}"]
    expected = checkpoint.get("git", {})
    comparisons = (
        ("head_sha", "HEAD_MISMATCH"),
        ("branch", "BRANCH_MISMATCH"),
        ("origin_main_sha", "ORIGIN_MAIN_MISMATCH"),
        ("origin_url", "ORIGIN_URL_MISMATCH"),
        ("repo_path", "REPO_PATH_MISMATCH"),
        ("worktree_path", "WORKTREE_PATH_MISMATCH"),
    )
    for key, label in comparisons:
        if expected.get(key) != actual.get(key):
            errors.append(f"{label}:{expected.get(key)!r}!={actual.get(key)!r}")

    declared_tracked = sorted(checkpoint.get("allowed_tracked_modifications", []))
    declared_untracked = sorted(checkpoint.get("allowed_untracked_files", []))
    if actual["tracked_modifications"] != declared_tracked:
        errors.append(
            "TRACKED_MODIFICATIONS_MISMATCH:"
            f"{actual['tracked_modifications']!r}!={declared_tracked!r}"
        )
    if actual["untracked_files"] != declared_untracked:
        errors.append(
            f"UNTRACKED_FILES_MISMATCH:{actual['untracked_files']!r}!={declared_untracked!r}"
        )

    authorities = checkpoint.get("authorities")
    if not isinstance(authorities, list) or not authorities:
        errors.append("AUTHORITIES_MISSING")
    else:
        for authority in authorities:
            relative = authority.get("path") if isinstance(authority, dict) else None
            expected_hash = authority.get("sha256") if isinstance(authority, dict) else None
            if not relative or not expected_hash:
                errors.append(f"AUTHORITY_DECLARATION_INVALID:{authority!r}")
                continue
            target = Path(worktree) / relative
            if not target.is_file():
                errors.append(f"AUTHORITY_MISSING:{relative}")
                continue
            actual_hash = sha256_file(target)
            if actual_hash != expected_hash:
                errors.append(
                    f"AUTHORITY_HASH_MISMATCH:{relative}:{actual_hash}!={expected_hash}"
                )
    return errors


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    """Durably publish canonical JSON using a sibling staging file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, staging_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".staging", dir=path.parent
    )
    staging = Path(staging_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(canonical_json_bytes(payload) + b"\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(staging, path)
    except BaseException:
        staging.unlink(missing_ok=True)
        raise


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("build", "validate"):
        child = subparsers.add_parser(command)
        child.add_argument("--repo", type=Path, default=None)
        child.add_argument("--worktree", type=Path, required=True)
    build = subparsers.choices["build"]
    build.add_argument("--state", type=Path, required=True)
    build.add_argument("--output", type=Path, required=True)
    validate = subparsers.choices["validate"]
    validate.add_argument("--checkpoint", type=Path, required=True)
    return parser


def main() -> int:
    args = _parser().parse_args()
    repo = args.repo or resolve_canonical_repo(args.worktree)
    if args.command == "build":
        state = json.loads(args.state.read_text(encoding="utf-8"))
        checkpoint = build_checkpoint(repo, args.worktree, state)
        atomic_write_json(args.output, checkpoint)
        print(checkpoint["checkpoint_semantic_sha256"])
        return 0
    checkpoint = json.loads(args.checkpoint.read_text(encoding="utf-8"))
    errors = validate_checkpoint(checkpoint, repo, args.worktree)
    if errors:
        print(json.dumps({"status": "STOP", "errors": errors}, indent=2))
        return 1
    print(json.dumps({"status": "PASS", "checkpoint": str(args.checkpoint)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
