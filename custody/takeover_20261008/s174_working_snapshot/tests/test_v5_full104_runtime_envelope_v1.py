from __future__ import annotations

import json
from pathlib import Path

import pytest

from sea_ad_jepa.v5 import full104_runtime_envelope_v1 as runtime
from sea_ad_jepa.v5.full104_runtime_envelope_v1 import (
    CANONICAL_REGISTRY_SHA256,
    FULL104_BLOCK_MANIFEST_SHA256,
    OBSERVATION_STATE_SHA256,
    SENTINEL_NAME,
    prepare_fresh_runtime,
    validate_runtime_envelope,
)


ANCHOR = "1" * 40


def prepare(root: Path):
    return prepare_fresh_runtime(
        root,
        scientific_anchor_git_oid=ANCHOR,
        full104_block_manifest_sha256=FULL104_BLOCK_MANIFEST_SHA256,
        canonical_registry_sha256=CANONICAL_REGISTRY_SHA256,
        observation_state_sha256=OBSERVATION_STATE_SHA256,
    )


def test_fresh_runtime_starts_empty_and_is_root_bound(tmp_path):
    root = tmp_path / "runtime"
    envelope = prepare(root)
    assert envelope.training_authorized is False
    assert envelope.terminal_masking_authorized is False
    assert envelope.target_panel_ladder_authorized is False
    assert (root / SENTINEL_NAME).is_file()

    observed = validate_runtime_envelope(
        root,
        expected_scientific_anchor_git_oid=ANCHOR,
    )
    assert observed.canonical_digest() == envelope.canonical_digest()


def test_nonempty_runtime_is_rejected_before_any_full104_work(tmp_path):
    root = tmp_path / "runtime"
    root.mkdir()
    (root / "leftover.txt").write_text("old", encoding="utf-8")
    with pytest.raises(ValueError, match="must start absent or empty"):
        prepare(root)


@pytest.mark.parametrize(
    "name",
    [
        "stage81a3_old.npy",
        "t1_checkpoint_u0200.pt",
        "discovery_matrix.npy",
        "ridge8_results.csv",
        "qualification_800_v1.json",
        "placeholder_support.json",
    ],
)
def test_runtime_validation_rejects_historical_or_placeholder_path_tokens(tmp_path, name):
    root = tmp_path / "runtime"
    prepare(root)
    (root / name).write_text("supporting only", encoding="utf-8")
    with pytest.raises(ValueError, match="spillover token"):
        validate_runtime_envelope(
            root,
            expected_scientific_anchor_git_oid=ANCHOR,
        )


def test_runtime_validation_rejects_known_historical_bytes_even_with_innocent_name(
    tmp_path, monkeypatch
):
    root = tmp_path / "runtime"
    prepare(root)
    artifact = root / "innocent.bin"
    artifact.write_bytes(b"historical supporting bytes")
    digest = runtime.sha256_file(artifact)
    monkeypatch.setattr(runtime, "FORBIDDEN_RUNTIME_SHA256", frozenset({digest}))
    with pytest.raises(ValueError, match="known historical/supporting artifact"):
        validate_runtime_envelope(
            root,
            expected_scientific_anchor_git_oid=ANCHOR,
        )


def test_runtime_validation_rejects_unallowlisted_innocent_file(tmp_path):
    root = tmp_path / "runtime"
    prepare(root)
    artifact = root / "current-looking.json"
    artifact.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="unapproved file in fresh FULL104 runtime envelope"):
        validate_runtime_envelope(
            root,
            expected_scientific_anchor_git_oid=ANCHOR,
        )
    observed = validate_runtime_envelope(
        root,
        expected_scientific_anchor_git_oid=ANCHOR,
        allowed_relative_paths=("current-looking.json",),
    )
    assert observed.scientific_anchor_git_oid == ANCHOR


def test_live_scientific_head_is_derived_and_dirty_worktree_fails(monkeypatch, tmp_path):
    worktree = tmp_path / "repo"
    worktree.mkdir()
    calls = []

    class Result:
        def __init__(self, stdout):
            self.stdout = stdout

    def clean_run(args, **kwargs):
        calls.append(tuple(args))
        if args[-2:] == ["rev-parse", "HEAD"]:
            return Result("a" * 40 + "\n")
        if args[-2:] == ["status", "--porcelain"]:
            return Result("")
        raise AssertionError(args)

    monkeypatch.setattr(runtime.subprocess, "run", clean_run)
    assert runtime.live_clean_scientific_head(worktree) == "a" * 40
    assert any("rev-parse" in call for call in calls)

    def dirty_run(args, **kwargs):
        if args[-2:] == ["rev-parse", "HEAD"]:
            return Result("b" * 40 + "\n")
        if args[-2:] == ["status", "--porcelain"]:
            return Result("?? historical.npy\n")
        raise AssertionError(args)

    monkeypatch.setattr(runtime.subprocess, "run", dirty_run)
    with pytest.raises(ValueError, match="must be clean"):
        runtime.live_clean_scientific_head(worktree)


def test_runtime_envelope_rejects_wrong_scientific_anchor(tmp_path):
    root = tmp_path / "runtime"
    prepare(root)
    with pytest.raises(ValueError, match="scientific anchor mismatch"):
        validate_runtime_envelope(
            root,
            expected_scientific_anchor_git_oid="2" * 40,
        )


def test_runtime_envelope_rejects_self_consistent_flag_escalation(tmp_path):
    root = tmp_path / "runtime"
    prepare(root)
    path = root / SENTINEL_NAME
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["terminal_masking_authorized"] = True
    semantic = dict(payload)
    semantic.pop("runtime_envelope_sha256", None)
    payload["runtime_envelope_sha256"] = runtime.canonical_sha(semantic)
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="terminal_masking_authorized must remain False"):
        validate_runtime_envelope(
            root,
            expected_scientific_anchor_git_oid=ANCHOR,
        )


def test_runtime_envelope_cli_is_nonterminal_and_requires_real_root_inputs():
    source = Path("scripts/agent/prepare_full104_runtime_envelope_v1.py").read_text(
        encoding="utf-8"
    )
    compile(source, "scripts/agent/prepare_full104_runtime_envelope_v1.py", "exec")
    assert "--level4-root" in source
    assert "--registry" in source
    assert "--observation-state" in source
    assert "--worktree" in source
    assert "live_clean_scientific_head" in source
    assert "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv" in source
    assert '"target_panel_ladder_authorized": False' in source
    assert '"terminal_masking_authorized": False' in source
    assert '"training_authorized": False' in source
