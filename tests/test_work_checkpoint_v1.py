from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from scripts.agent.work_checkpoint import (
    atomic_write_json,
    build_checkpoint,
    canonical_json_bytes,
    semantic_sha256,
    sha256_file,
    validate_checkpoint,
)


def _git(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-c", "safe.directory=*", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


@pytest.fixture()
def git_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.name", "Checkpoint Test")
    _git(repo, "config", "user.email", "checkpoint@example.invalid")
    (repo / "authority.txt").write_text("authority-v1\n", encoding="utf-8")
    _git(repo, "add", "authority.txt")
    _git(repo, "commit", "-m", "initial")
    _git(repo, "remote", "add", "origin", str(repo))
    _git(repo, "fetch", "origin", "main:refs/remotes/origin/main")
    return repo


def _state(repo: Path) -> dict:
    return {
        "active_agent": "CODEX",
        "authorities": [
            {
                "path": "authority.txt",
                "sha256": sha256_file(repo / "authority.txt"),
                "status": "FROZEN_AUTHORITY",
            }
        ],
        "gates": {"current": "PASS_TO_IMPLEMENT_CONTINUITY_AND_C2_ONLY"},
        "unresolved_blockers": ["C2_GRADIENT_SEVERING_CONDITION_UNRESOLVED"],
        "assets": {"local": ["authority.txt"], "remote_only": []},
        "next_authorized_actions": ["CONTINUITY", "C2_FORENSIC_CLOSURE"],
        "allowed_tracked_modifications": [],
        "allowed_untracked_files": [],
    }


def test_canonical_json_and_semantic_root_ignore_insertion_order() -> None:
    left = {"z": [3, 2, 1], "a": {"b": True, "a": None}}
    right = {"a": {"a": None, "b": True}, "z": [3, 2, 1]}
    assert canonical_json_bytes(left) == canonical_json_bytes(right)
    assert semantic_sha256(left) == semantic_sha256(right)


def test_semantic_root_excludes_only_its_own_field() -> None:
    base = {"x": 1, "checkpoint_semantic_sha256": "old"}
    changed_root = {"x": 1, "checkpoint_semantic_sha256": "new"}
    changed_value = {"x": 2, "checkpoint_semantic_sha256": "old"}
    assert semantic_sha256(base) == semantic_sha256(changed_root)
    assert semantic_sha256(base) != semantic_sha256(changed_value)


def test_atomic_write_json_roundtrip(tmp_path: Path) -> None:
    target = tmp_path / "checkpoint.json"
    payload = {"b": 2, "a": 1}
    atomic_write_json(target, payload)
    assert target.read_bytes() == canonical_json_bytes(payload) + b"\n"
    assert not list(tmp_path.glob("*.staging"))


def test_build_and_validate_clean_checkpoint(git_repo: Path) -> None:
    checkpoint = build_checkpoint(git_repo, git_repo, _state(git_repo))
    assert checkpoint["git"]["head_sha"] == _git(git_repo, "rev-parse", "HEAD")
    assert checkpoint["git"]["branch"] == "main"
    assert checkpoint["checkpoint_semantic_sha256"] == semantic_sha256(checkpoint)
    assert validate_checkpoint(checkpoint, git_repo, git_repo) == []


@pytest.mark.parametrize(
    "mutation,expected",
    [
        (lambda c: c["git"].__setitem__("head_sha", "0" * 40), "HEAD_MISMATCH"),
        (lambda c: c["git"].__setitem__("branch", "wrong"), "BRANCH_MISMATCH"),
        (
            lambda c: c["authorities"][0].__setitem__("sha256", "0" * 64),
            "AUTHORITY_HASH_MISMATCH",
        ),
    ],
)
def test_identity_mutations_fail_closed(
    git_repo: Path, mutation, expected: str
) -> None:
    checkpoint = build_checkpoint(git_repo, git_repo, _state(git_repo))
    mutation(checkpoint)
    checkpoint["checkpoint_semantic_sha256"] = semantic_sha256(checkpoint)
    assert any(error.startswith(expected) for error in validate_checkpoint(checkpoint, git_repo, git_repo))


def test_corrupted_semantic_root_fails(git_repo: Path) -> None:
    checkpoint = build_checkpoint(git_repo, git_repo, _state(git_repo))
    checkpoint["gates"]["current"] = "CORRUPTED"
    assert "CHECKPOINT_SEMANTIC_SHA256_MISMATCH" in validate_checkpoint(
        checkpoint, git_repo, git_repo
    )


def test_changed_or_missing_authority_fails(git_repo: Path) -> None:
    checkpoint = build_checkpoint(git_repo, git_repo, _state(git_repo))
    (git_repo / "authority.txt").write_text("changed\n", encoding="utf-8")
    errors = validate_checkpoint(checkpoint, git_repo, git_repo)
    assert any(error.startswith("AUTHORITY_HASH_MISMATCH") for error in errors)
    (git_repo / "authority.txt").unlink()
    errors = validate_checkpoint(checkpoint, git_repo, git_repo)
    assert any(error.startswith("AUTHORITY_MISSING") for error in errors)


def test_unexpected_dirty_file_fails_but_declared_dirty_file_passes(git_repo: Path) -> None:
    (git_repo / "scratch.txt").write_text("work\n", encoding="utf-8")
    checkpoint = build_checkpoint(git_repo, git_repo, _state(git_repo))
    assert checkpoint["git"]["untracked_files"] == ["scratch.txt"]
    checkpoint["allowed_untracked_files"] = []
    checkpoint["checkpoint_semantic_sha256"] = semantic_sha256(checkpoint)
    assert any(
        error.startswith("UNTRACKED_FILES_MISMATCH")
        for error in validate_checkpoint(checkpoint, git_repo, git_repo)
    )
    checkpoint["allowed_untracked_files"] = ["scratch.txt"]
    checkpoint["checkpoint_semantic_sha256"] = semantic_sha256(checkpoint)
    assert validate_checkpoint(checkpoint, git_repo, git_repo) == []


def test_tracked_modification_must_be_declared(git_repo: Path) -> None:
    (git_repo / "authority.txt").write_text("modified\n", encoding="utf-8")
    state = _state(git_repo)
    state["authorities"][0]["sha256"] = sha256_file(git_repo / "authority.txt")
    checkpoint = build_checkpoint(git_repo, git_repo, state)
    assert checkpoint["git"]["tracked_modifications"] == ["authority.txt"]
    checkpoint["allowed_tracked_modifications"] = []
    checkpoint["checkpoint_semantic_sha256"] = semantic_sha256(checkpoint)
    assert any(
        error.startswith("TRACKED_MODIFICATIONS_MISMATCH")
        for error in validate_checkpoint(checkpoint, git_repo, git_repo)
    )


def test_serialized_checkpoint_is_valid_json(git_repo: Path, tmp_path: Path) -> None:
    checkpoint = build_checkpoint(git_repo, git_repo, _state(git_repo))
    target = tmp_path / "checkpoint.json"
    atomic_write_json(target, checkpoint)
    assert json.loads(target.read_text(encoding="utf-8")) == checkpoint


def test_resolve_canonical_repo_from_main_worktree(git_repo: Path) -> None:
    from scripts.agent.work_checkpoint import resolve_canonical_repo

    assert resolve_canonical_repo(git_repo) == git_repo.resolve()


def test_resolve_canonical_repo_from_linked_worktree(git_repo: Path, tmp_path: Path) -> None:
    """A linked worktree must resolve to the canonical repo, not to itself.

    This is the takeover path: an arriving peer knows only its own worktree and
    must not be required to hardcode the canonical repository path.
    """
    from scripts.agent.work_checkpoint import resolve_canonical_repo

    linked = tmp_path / "linked"
    _git(git_repo, "worktree", "add", str(linked), "-b", "peer-branch")
    assert resolve_canonical_repo(linked) == git_repo.resolve()
    assert resolve_canonical_repo(linked) != linked.resolve()
