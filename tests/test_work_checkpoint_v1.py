from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from scripts.agent.work_checkpoint import (
    atomic_write_json,
    authority_path_dirty,
    authority_worktree_oid,
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
    refusals = ("AUTHORITY_MISSING", "AUTHORITY_LOCAL_NOT_DECLARED_UNTRACKED")

    # Absent from the bound tree and never declared as a local authority.
    state = _state(git_repo)
    state["authorities"] = [
        {"path": "no/such/authority.txt", "sha256": empty_digest, "status": "FROZEN_AUTHORITY"}
    ]
    checkpoint = build_checkpoint(git_repo, git_repo, state)
    errors = validate_checkpoint(checkpoint, git_repo, git_repo)
    assert any(error.startswith(refusals) for error in errors), errors
    assert not any(error.startswith("AUTHORITY_HASH_MISMATCH") for error in errors)

    # Declared as a local authority and listed as untracked, but genuinely
    # absent: the disk branch must also refuse before hashing.
    state = _state(git_repo)
    state["authorities"].append(
        {"path": "vanished.json", "sha256": empty_digest, "status": "LOCAL_AUTHORITY"}
    )
    state["allowed_untracked_files"] = ["vanished.json"]
    checkpoint = build_checkpoint(git_repo, git_repo, state)
    errors = validate_checkpoint(checkpoint, git_repo, git_repo)
    assert any(error.startswith(refusals) for error in errors), errors
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
    bound = tracked_blob_at(git_repo, checkpoint["git"]["head_sha"], "authority.txt")
    assert authority_path_dirty(git_repo, "authority.txt", bound["oid"]) is True


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
    """Authority bytes come from the bound commit, and divergence is caught.

    An earlier version of this test ratified a hole. It asserted that after a
    later commit replaced the declared authority there was no authority-level
    complaint, which is exactly the wrong expectation: dirtiness was being
    measured with `git status` against whatever HEAD happened to be current, so
    the worktree was "clean" with respect to the new commit and a completely
    different file could stand in for the authority unnoticed. Dirtiness is now
    measured against the bound object id.
    """
    repo, blob_sha, _ = _crlf_repo(tmp_path)
    checkpoint = build_checkpoint(repo, repo, _crlf_state(repo, blob_sha))
    bound = checkpoint["git"]["head_sha"]
    bound_entry = tracked_blob_at(repo, bound, "authority.txt")

    (repo / "authority.txt").write_bytes(b"COMPLETELY DIFFERENT AUTHORITY\n")
    _git(repo, "add", "authority.txt")
    _git(repo, "commit", "-m", "second authority revision")
    assert _git(repo, "rev-parse", "HEAD") != bound
    assert _git(repo, "status", "--porcelain") == "", "clean against the NEW head"

    errors = validate_checkpoint(checkpoint, repo, repo)
    assert any(error.startswith("HEAD_MISMATCH") for error in errors)
    assert any(error.startswith("AUTHORITY_DIRTY") for error in errors), errors
    # The bytes still resolve from the bound commit, not the later one.
    assert sha256_tracked_blob(repo, bound_entry["oid"]) == blob_sha


def test_the_worktree_oid_is_computed_through_the_clean_filter(tmp_path: Path) -> None:
    """A CRLF checkout must still match the bound object id.

    This is what lets dirtiness be exact without any line-ending handling in
    Python: git applies the same clean filter a commit would.
    """
    repo, blob_sha, disk_sha = _crlf_repo(tmp_path)
    head = _git(repo, "rev-parse", "HEAD")
    entry = tracked_blob_at(repo, head, "authority.txt")
    assert b"\r\n" in (repo / "authority.txt").read_bytes()
    assert disk_sha != blob_sha
    assert authority_worktree_oid(repo, "authority.txt") == entry["oid"]
    assert authority_path_dirty(repo, "authority.txt", entry["oid"]) is False

    (repo / "authority.txt").unlink()
    assert authority_worktree_oid(repo, "authority.txt") is None
    assert authority_path_dirty(repo, "authority.txt", entry["oid"]) is True
    assert authority_path_dirty(repo, ":authority.txt", entry["oid"]) is True


# ---------------------------------------------------------------------------
# Authority path identity
#
# An independent review found two fail-closed defects in the blob-authority
# repair, and both were reproduced before this suite was written.
#
# First, the declared path reached Git as a pathspec rather than as an
# identity, so `:authority.txt`, `:(literal)authority.txt` and
# `./authority.txt` all resolved to the committed `authority.txt` blob and the
# returned path was never compared with the declared one. Three spellings named
# one authority.
#
# Second, a miss in the bound tree fell through to `Path(worktree) / relative`
# with no containment or declaration requirement, so
# `../outside_authority.txt` validated cleanly with `allowed_untracked_files`
# empty: a file outside the repository became a checkpoint authority.
# ---------------------------------------------------------------------------

import os as _os
import subprocess as _subprocess

from scripts.agent.work_checkpoint import (
    canonical_authority_path,
    resolve_local_authority,
)


def test_canonical_authority_path_accepts_only_one_spelling() -> None:
    assert canonical_authority_path("docs/agent/thing.json") == "docs/agent/thing.json"
    assert canonical_authority_path("AGENTS.md") == "AGENTS.md"
    for hostile in (
        ":authority.txt",                  # pathspec magic
        ":(literal)authority.txt",         # explicit literal magic
        ":(glob)authority.txt",
        "./authority.txt",                 # noncanonical same-directory prefix
        "../outside_authority.txt",        # parent escape
        "docs/../AGENTS.md",               # embedded escape
        "docs//agent.json",                # empty component
        "/etc/passwd",                     # POSIX absolute
        "C:/Windows/win.ini",              # Windows absolute
        "docs\\agent\\thing.json",         # separator ambiguity
        "docs/agent\x00.json",             # NUL
        "",
        None,
        42,
    ):
        assert canonical_authority_path(hostile) is None, hostile


def test_pathspec_magic_cannot_alias_a_tracked_authority(git_repo: Path) -> None:
    """Each alias resolved to the real blob before the repair."""
    head = _git(git_repo, "rev-parse", "HEAD")
    genuine = _blob_sha(git_repo, "authority.txt")
    for alias in (":authority.txt", ":(literal)authority.txt", "./authority.txt"):
        assert tracked_blob_at(git_repo, head, alias) is None, alias
        state = _state(git_repo)
        state["authorities"] = [
            {"path": alias, "sha256": genuine, "status": "FROZEN_AUTHORITY"}
        ]
        checkpoint = build_checkpoint(git_repo, git_repo, state)
        errors = validate_checkpoint(checkpoint, git_repo, git_repo)
        assert any(error.startswith("AUTHORITY_PATH_NOT_CANONICAL") for error in errors), (
            alias,
            errors,
        )
        assert errors, f"{alias} must never validate"


def test_an_out_of_root_authority_is_refused(git_repo: Path, tmp_path: Path) -> None:
    """`../outside` validated cleanly before the repair."""
    outside = tmp_path / "outside_authority.txt"
    outside.write_bytes(b'{"external": true}\n')
    for spelling in ("../outside_authority.txt", str(outside)):
        state = _state(git_repo)
        state["authorities"].append(
            {"path": spelling, "sha256": sha256_file(outside), "status": "FROZEN_AUTHORITY"}
        )
        checkpoint = build_checkpoint(git_repo, git_repo, state)
        errors = validate_checkpoint(checkpoint, git_repo, git_repo)
        assert any(error.startswith("AUTHORITY_PATH_NOT_CANONICAL") for error in errors), (
            spelling,
            errors,
        )


def test_an_undeclared_local_file_is_not_an_authority(git_repo: Path) -> None:
    """A tree miss must not mean "local authority"."""
    sneaky = git_repo / "sneaky.json"
    sneaky.write_bytes(b'{"sneaky": true}\n')
    state = _state(git_repo)
    state["authorities"].append(
        {"path": "sneaky.json", "sha256": sha256_file(sneaky), "status": "LOCAL_AUTHORITY"}
    )
    state["allowed_untracked_files"] = []
    checkpoint = build_checkpoint(git_repo, git_repo, state)
    errors = validate_checkpoint(checkpoint, git_repo, git_repo)
    assert any(
        error.startswith("AUTHORITY_LOCAL_NOT_DECLARED_UNTRACKED") for error in errors
    ), errors


def test_an_ignored_local_file_is_not_an_authority(git_repo: Path) -> None:
    """Declaring an ignored file must not admit it.

    The untracked inventory honours `--exclude-standard`, so an ignored path is
    not in it and cannot become an authority even when declared.
    """
    (git_repo / ".gitignore").write_text("ignored.json\n", encoding="utf-8")
    _git(git_repo, "add", ".gitignore")
    _git(git_repo, "commit", "-m", "ignore rule")
    ignored = git_repo / "ignored.json"
    ignored.write_bytes(b'{"ignored": true}\n')
    assert _git(git_repo, "status", "--porcelain") == "", "ignored file must be invisible"

    state = _state(git_repo)
    state["authorities"].append(
        {"path": "ignored.json", "sha256": sha256_file(ignored), "status": "LOCAL_AUTHORITY"}
    )
    state["allowed_untracked_files"] = ["ignored.json"]
    checkpoint = build_checkpoint(git_repo, git_repo, state)
    errors = validate_checkpoint(checkpoint, git_repo, git_repo)
    assert any(
        error.startswith("AUTHORITY_LOCAL_NOT_DECLARED_UNTRACKED") for error in errors
    ), errors


def _link_dir(link: Path, target: Path) -> str:
    """Create the strongest available directory link, returning its kind.

    Real symlinks need a privilege this checkout does not hold on Windows, so a
    junction is used instead. A junction is the sharper attack: Python reports
    `is_symlink()` False for it, so it slips the symlink guard and must be
    caught by the containment check on the resolved path.
    """
    try:
        _os.symlink(str(target), str(link), target_is_directory=True)
        return "symlink"
    except OSError:
        completed = _subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(link), str(target)],
            capture_output=True,
            text=True,
        )
        if completed.returncode or not link.exists():
            raise RuntimeError(
                "neither symlink nor junction could be created; the escape guard "
                "is untested on this platform"
            )
        return "junction"


def test_a_linked_authority_escaping_the_worktree_is_refused(
    git_repo: Path, tmp_path: Path
) -> None:
    """A canonical in-repo path must not reach outside via a reparse point.

    Canonicalisation alone cannot stop this: the declared path is a perfectly
    ordinary relative path. Only resolving it and requiring containment does.
    """
    outside = tmp_path / "outside_tree"
    outside.mkdir()
    payload = outside / "authority.json"
    payload.write_bytes(b'{"external": true}\n')
    kind = _link_dir(git_repo / "linked", outside)

    relative = "linked/authority.json"
    state = _state(git_repo)
    state["authorities"].append(
        {"path": relative, "sha256": sha256_file(payload), "status": "LOCAL_AUTHORITY"}
    )
    state["allowed_untracked_files"] = sorted(
        set(state["allowed_untracked_files"]) | {relative}
    )
    checkpoint = build_checkpoint(git_repo, git_repo, state)
    errors = validate_checkpoint(checkpoint, git_repo, git_repo)
    assert errors, f"a {kind} escape must never validate"
    assert any(
        error.startswith("AUTHORITY_OUTSIDE_WORKTREE")
        or error.startswith("AUTHORITY_LOCAL_IS_SYMLINK")
        or error.startswith("AUTHORITY_LOCAL_NOT_DECLARED_UNTRACKED")
        for error in errors
    ), (kind, errors)
    # And the direct guard reports containment, not merely a declaration miss.
    resolved, reason = resolve_local_authority(
        git_repo, relative, {relative}, {relative}
    )
    assert resolved is None
    assert reason in {"AUTHORITY_OUTSIDE_WORKTREE", "AUTHORITY_LOCAL_IS_SYMLINK"}, reason


def test_a_legitimately_declared_local_authority_still_validates(git_repo: Path) -> None:
    """The guards must discriminate rather than refuse every local authority."""
    local = git_repo / "local_authority.json"
    local.write_bytes(b'{"local": true}\n')
    state = _state(git_repo)
    state["authorities"].append(
        {"path": "local_authority.json", "sha256": sha256_file(local),
         "status": "LOCAL_AUTHORITY"}
    )
    state["allowed_untracked_files"] = ["local_authority.json"]
    checkpoint = build_checkpoint(git_repo, git_repo, state)
    assert validate_checkpoint(checkpoint, git_repo, git_repo) == []
    resolved, reason = resolve_local_authority(
        git_repo, "local_authority.json", {"local_authority.json"}, {"local_authority.json"}
    )
    assert reason is None and resolved == local.resolve()
