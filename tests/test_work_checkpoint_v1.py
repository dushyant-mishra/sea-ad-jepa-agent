from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from scripts.agent.work_checkpoint import (
    atomic_write_json,
    authority_path_dirty,
    build_checkpoint,
    canonical_json_bytes,
    semantic_sha256,
    sha256_file,
    sha256_tracked_blob,
    tracked_blob_at,
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


def _blob_sha(repo: Path, relative: str, commit: str = "HEAD") -> str:
    """SHA-256 of the committed Git object payload for *relative*.

    A tracked authority's declared digest is the blob digest, which is what
    survives a checkout on a platform where Git rewrites line endings.
    """
    entry = tracked_blob_at(repo, _git(repo, "rev-parse", commit), relative)
    assert entry is not None, f"{relative} is not tracked at {commit}"
    digest = sha256_tracked_blob(repo, entry["oid"])
    assert digest is not None
    return digest


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
                "sha256": _blob_sha(repo, "authority.txt"),
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
    """A tracked authority that is edited or deleted must fail closed.

    Both now surface as `AUTHORITY_DIRTY` rather than a digest mismatch: the
    committed blob is still intact, so the honest complaint is that the working
    copy no longer matches the authority the checkpoint is bound to. Validating
    the pristine blob while the worktree carried different bytes would let an
    edited authority pass.
    """
    checkpoint = build_checkpoint(git_repo, git_repo, _state(git_repo))
    (git_repo / "authority.txt").write_text("changed\n", encoding="utf-8")
    errors = validate_checkpoint(checkpoint, git_repo, git_repo)
    assert any(error.startswith("AUTHORITY_DIRTY") for error in errors)
    (git_repo / "authority.txt").unlink()
    errors = validate_checkpoint(checkpoint, git_repo, git_repo)
    assert any(error.startswith("AUTHORITY_DIRTY") for error in errors)


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


# ---------------------------------------------------------------------------
# Pre-existing CRLF / blob-authority validator defect
#
# `validate_checkpoint` hashed an authority's worktree bytes, but a declared
# authority digest is the Git blob digest. Wherever Git rewrites line endings
# on checkout (`core.autocrlf=true`), every declared digest became
# unverifiable: on the JEPA Windows checkout all four declared authorities
# failed with hashes that differed from the committed ones. The repair reads
# tracked authority bytes from the object database, pinned to the commit the
# checkpoint is bound to.
# ---------------------------------------------------------------------------


def _crlf_repo(tmp_path: Path) -> tuple[Path, str, str]:
    """A repo whose committed blob is LF while its checkout is CRLF.

    This reproduces the defect on any platform, so the regression does not
    depend on the developer machine being Windows. The file is written as exact
    LF bytes, committed, and then re-checked-out with `core.autocrlf=true` so
    Git materialises CRLF in the worktree while `git status` stays clean.
    """
    repo = tmp_path / "crlf"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.name", "Checkpoint Test")
    _git(repo, "config", "user.email", "checkpoint@example.invalid")
    _git(repo, "config", "core.autocrlf", "false")
    target = repo / "authority.txt"
    target.write_bytes(b"line-one\nline-two\n")
    _git(repo, "add", "authority.txt")
    _git(repo, "commit", "-m", "lf authority")
    _git(repo, "remote", "add", "origin", str(repo))
    _git(repo, "fetch", "origin", "main:refs/remotes/origin/main")

    blob_sha = _blob_sha(repo, "authority.txt")

    # Force a fresh checkout under autocrlf so the worktree bytes become CRLF.
    _git(repo, "config", "core.autocrlf", "true")
    target.unlink()
    _git(repo, "checkout", "--", "authority.txt")
    disk_sha = sha256_file(target)
    return repo, blob_sha, disk_sha


def _crlf_state(repo: Path, blob_sha: str) -> dict:
    state = _state(repo)
    state["authorities"] = [
        {"path": "authority.txt", "sha256": blob_sha, "status": "FROZEN_AUTHORITY"}
    ]
    return state


def test_lf_blob_checked_out_as_crlf_validates_from_blob_bytes(tmp_path: Path) -> None:
    """The exact defect: clean tree, CRLF on disk, LF in the object database."""
    repo, blob_sha, disk_sha = _crlf_repo(tmp_path)
    assert b"\r\n" in (repo / "authority.txt").read_bytes(), "checkout must be CRLF"
    assert disk_sha != blob_sha, "the platform transform must actually change bytes"
    assert _git(repo, "status", "--porcelain") == "", "Git must consider the tree clean"

    checkpoint = build_checkpoint(repo, repo, _crlf_state(repo, blob_sha))
    assert validate_checkpoint(checkpoint, repo, repo) == []


def test_the_crlf_disk_digest_never_becomes_authoritative(tmp_path: Path) -> None:
    """Declaring the worktree digest must fail, which is the old behaviour.

    Without this the repair could be silently reverted: the previous
    implementation accepted exactly this declaration and rejected the blob one.
    """
    repo, blob_sha, disk_sha = _crlf_repo(tmp_path)
    checkpoint = build_checkpoint(repo, repo, _crlf_state(repo, disk_sha))
    errors = validate_checkpoint(checkpoint, repo, repo)
    assert any(error.startswith("AUTHORITY_HASH_MISMATCH") for error in errors)
    assert any(blob_sha in error for error in errors), (
        "the reported actual digest must be the blob digest"
    )


def test_a_wrong_blob_digest_fails(tmp_path: Path) -> None:
    repo, blob_sha, _ = _crlf_repo(tmp_path)
    state = _crlf_state(repo, "0" * 64)
    checkpoint = build_checkpoint(repo, repo, state)
    assert any(
        error.startswith("AUTHORITY_HASH_MISMATCH")
        for error in validate_checkpoint(checkpoint, repo, repo)
    )


def test_a_missing_authority_stops_before_any_digest(git_repo: Path) -> None:
    """A failed object lookup must never be digested as empty bytes.

    `sha256(b"")` is `e3b0c442...`; if a missing path reached the hash step, a
    declaration of that constant would validate.
    """
    empty_digest = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    state = _state(git_repo)
    state["authorities"] = [
        {"path": "no/such/authority.txt", "sha256": empty_digest, "status": "FROZEN_AUTHORITY"}
    ]
    checkpoint = build_checkpoint(git_repo, git_repo, state)
    errors = validate_checkpoint(checkpoint, git_repo, git_repo)
    assert any(error.startswith("AUTHORITY_MISSING") for error in errors)
    assert not any(error.startswith("AUTHORITY_HASH_MISMATCH") for error in errors)


def test_a_dirty_authority_fails_even_when_declared_modifiable(git_repo: Path) -> None:
    """Listing an authority as an allowed modification must not exempt it."""
    (git_repo / "authority.txt").write_text("edited\n", encoding="utf-8")
    state = _state(git_repo)
    state["allowed_tracked_modifications"] = ["authority.txt"]
    checkpoint = build_checkpoint(git_repo, git_repo, state)
    errors = validate_checkpoint(checkpoint, git_repo, git_repo)
    assert not any(error.startswith("TRACKED_MODIFICATIONS_MISMATCH") for error in errors)
    assert any(error.startswith("AUTHORITY_DIRTY") for error in errors)
    assert authority_path_dirty(git_repo, "authority.txt") is True


def test_symlink_and_submodule_authorities_are_refused(git_repo: Path) -> None:
    """Only a regular tracked blob may serve as an authority.

    Both entries are written through the index with an explicit mode so the
    test does not depend on the platform supporting real symlinks.
    """
    oid = _git(git_repo, "hash-object", "-w", "authority.txt")
    head = _git(git_repo, "rev-parse", "HEAD")
    _git(git_repo, "update-index", "--add", "--cacheinfo", f"120000,{oid},link_authority")
    _git(git_repo, "update-index", "--add", "--cacheinfo", f"160000,{head},sub_authority")
    _git(git_repo, "commit", "-m", "irregular entries")

    for relative in ("link_authority", "sub_authority"):
        state = _state(git_repo)
        state["authorities"] = [
            {"path": relative, "sha256": "0" * 64, "status": "FROZEN_AUTHORITY"}
        ]
        checkpoint = build_checkpoint(git_repo, git_repo, state)
        errors = validate_checkpoint(checkpoint, git_repo, git_repo)
        assert any(error.startswith("AUTHORITY_NOT_REGULAR_FILE") for error in errors), (
            relative,
            errors,
        )


def test_an_untracked_local_authority_keeps_disk_byte_behaviour(git_repo: Path) -> None:
    """The repair must not silently redefine every authority as a Git object."""
    local = git_repo / "local_authority.json"
    local.write_bytes(b'{"local": true}\n')
    assert tracked_blob_at(git_repo, _git(git_repo, "rev-parse", "HEAD"), local.name) is None

    state = _state(git_repo)
    state["authorities"].append(
        {"path": local.name, "sha256": sha256_file(local), "status": "LOCAL_AUTHORITY"}
    )
    state["allowed_untracked_files"] = [local.name]
    checkpoint = build_checkpoint(git_repo, git_repo, state)
    assert validate_checkpoint(checkpoint, git_repo, git_repo) == []

    local.write_bytes(b'{"local": false}\n')
    assert any(
        error.startswith("AUTHORITY_HASH_MISMATCH")
        for error in validate_checkpoint(checkpoint, git_repo, git_repo)
    )


def test_validation_does_not_mutate_the_index_or_worktree(tmp_path: Path) -> None:
    """Validating is read-only with respect to Git state."""
    repo, blob_sha, _ = _crlf_repo(tmp_path)
    checkpoint = build_checkpoint(repo, repo, _crlf_state(repo, blob_sha))
    before_index = _git(repo, "ls-files", "-s")
    before_status = _git(repo, "status", "--porcelain")
    before_bytes = (repo / "authority.txt").read_bytes()

    assert validate_checkpoint(checkpoint, repo, repo) == []

    assert _git(repo, "ls-files", "-s") == before_index
    assert _git(repo, "status", "--porcelain") == before_status
    assert (repo / "authority.txt").read_bytes() == before_bytes


def test_the_bound_head_is_used_not_a_later_commit(tmp_path: Path) -> None:
    """Authority bytes come from the commit the checkpoint is bound to.

    After a later commit changes the authority, the checkpoint bound to the
    earlier HEAD must not silently validate against the new blob.
    """
    repo, blob_sha, _ = _crlf_repo(tmp_path)
    checkpoint = build_checkpoint(repo, repo, _crlf_state(repo, blob_sha))
    bound = checkpoint["git"]["head_sha"]

    (repo / "authority.txt").write_bytes(b"line-one\nline-two\nline-three\n")
    _git(repo, "add", "authority.txt")
    _git(repo, "commit", "-m", "second authority revision")
    assert _git(repo, "rev-parse", "HEAD") != bound

    errors = validate_checkpoint(checkpoint, repo, repo)
    # HEAD moved, so the snapshot comparison must complain, but the authority
    # itself still resolves against the bound commit rather than the new one.
    assert any(error.startswith("HEAD_MISMATCH") for error in errors)
    assert not any(error.startswith("AUTHORITY_HASH_MISMATCH") for error in errors)
    assert not any(error.startswith("AUTHORITY_DIRTY") for error in errors)
