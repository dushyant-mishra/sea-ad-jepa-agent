from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from scripts.agent.claude_peer_bridge import (
    build_consult_command,
    consult,
    discover_claude,
)


def _tree_hash(root: Path, excluded: Path | None = None) -> str:
    digest = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        if excluded is not None and excluded in path.parents:
            continue
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def test_discover_claude_accepts_explicit_executable(tmp_path: Path) -> None:
    executable = tmp_path / "claude.exe"
    executable.write_bytes(b"fake")
    assert discover_claude(executable) == executable.resolve()


def test_discover_claude_selects_highest_antigravity_version(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    for version in ("2.0.1", "2.3.0", "2.12.0"):
        executable = (
            tmp_path
            / ".antigravity-ide"
            / "extensions"
            / f"anthropic.claude-code-{version}-win32-x64"
            / "resources"
            / "native-binary"
            / "claude.exe"
        )
        executable.parent.mkdir(parents=True)
        executable.write_bytes(b"fake")
    assert "2.12.0" in str(discover_claude(None))


def test_consult_command_is_restricted_and_one_response_only(tmp_path: Path) -> None:
    executable = tmp_path / "claude.exe"
    executable.write_bytes(b"fake")
    command = build_consult_command(executable, "Return JSON", max_turns=1)
    joined = " ".join(command)
    assert "--print" in command
    assert "--output-format" in command and "json" in command
    assert "--restricted" in command
    assert "--strict-mcp-config" in command
    assert "--permission-mode" in command and "dontAsk" in command
    assert "--tools=" in command
    assert "--max-budget-usd" in command
    assert "dangerously-skip-permissions" not in joined
    assert "acceptEdits" not in joined
    with pytest.raises(ValueError, match="exactly one response"):
        build_consult_command(executable, "Return JSON", max_turns=2)


def test_consult_records_valid_advisory_without_project_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "source.txt").write_text("unchanged\n", encoding="utf-8")
    prompt = project / "prompt.txt"
    prompt.write_text("Return one JSON object.\n", encoding="utf-8")
    out = project / "review"
    before = _tree_hash(project, excluded=out)

    def fake_run(argv, **kwargs):
        if "--version" in argv:
            return subprocess.CompletedProcess(argv, 0, "2.1.260\n", "")
        if "auth" in argv:
            return subprocess.CompletedProcess(
                argv, 0, json.dumps({"loggedIn": True}), ""
            )
        return subprocess.CompletedProcess(
            argv,
            0,
            json.dumps({"type": "result", "result": '{"verdict":"ADVISORY"}'}),
            "",
        )

    monkeypatch.setattr("scripts.agent.claude_peer_bridge.subprocess.run", fake_run)
    executable = tmp_path / "claude.exe"
    executable.write_bytes(b"fake")
    result = consult(
        executable,
        prompt,
        out,
        {"repo_head": "abc", "declared_inputs": {"source.txt": "123"}},
    )
    assert result["status"] == "CONSULTATION_COMPLETE"
    assert result["advisory_only"] is True
    assert result["single_response_enforced"] is True
    assert _tree_hash(project, excluded=out) == before
    published = json.loads((out / "CLAUDE_PEER_CONSULTATION.json").read_text("utf-8"))
    assert published == result
    assert "token" not in json.dumps(published).lower()


@pytest.mark.parametrize(
    "returncode,stdout,expected",
    [(1, "{}", "STOP_CLAUDE_PROCESS_FAILED"), (0, "not-json", "STOP_CLAUDE_RESPONSE_INVALID")],
)
def test_failed_or_malformed_response_cannot_pass(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    returncode: int,
    stdout: str,
    expected: str,
) -> None:
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("test", encoding="utf-8")
    executable = tmp_path / "claude.exe"
    executable.write_bytes(b"fake")

    def fake_run(argv, **kwargs):
        if "--version" in argv:
            return subprocess.CompletedProcess(argv, 0, "2.1.260\n", "")
        if "auth" in argv:
            return subprocess.CompletedProcess(argv, 0, '{"loggedIn":true}', "")
        return subprocess.CompletedProcess(argv, returncode, stdout, "failure")

    monkeypatch.setattr("scripts.agent.claude_peer_bridge.subprocess.run", fake_run)
    result = consult(executable, prompt, tmp_path / "out", {})
    assert result["status"] == expected
    assert result["advisory_only"] is True
    assert result["status"] != "CONSULTATION_COMPLETE"


def test_published_consultation_carries_no_account_identity_or_username(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Provenance must never publish account identity or the local username.

    `claude auth status --json` returns email, orgId, orgName and a projects
    directory. A denylist of secret-ish key names does not catch these, so the
    auth summary is allowlisted and local user paths are redacted. This artifact
    is committed to a public repository.
    """
    home = tmp_path / "Users" / "someuser"
    home.mkdir(parents=True)
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.setattr("scripts.agent.claude_peer_bridge.Path.home", lambda: home)

    prompt = tmp_path / "prompt.txt"
    prompt.write_text("Return one JSON object.\n", encoding="utf-8")

    def fake_run(argv, **kwargs):
        if "--version" in argv:
            return subprocess.CompletedProcess(argv, 0, "2.1.260\n", "")
        if "auth" in argv:
            return subprocess.CompletedProcess(
                argv,
                0,
                json.dumps(
                    {
                        "loggedIn": True,
                        "apiProvider": "firstParty",
                        "authMethod": "claude.ai",
                        "subscriptionType": "team",
                        "email": "someone@example.invalid",
                        "orgId": "00000000-0000-4000-8000-000000000000",
                        "orgName": "Some Lab Somewhere",
                        "projectsDirectory": str(home / ".claude" / "projects"),
                        "analyticsDisabled": False,
                    }
                ),
                "",
            )
        return subprocess.CompletedProcess(
            argv, 0, json.dumps({"type": "result", "result": '{"verdict":"ADVISORY"}'}), ""
        )

    monkeypatch.setattr("scripts.agent.claude_peer_bridge.subprocess.run", fake_run)
    executable = home / "claude.exe"
    executable.write_bytes(b"fake")
    result = consult(executable, prompt, tmp_path / "out", {})

    blob = json.dumps(result)
    for forbidden in (
        "someone@example.invalid",
        "00000000-0000-4000-8000-000000000000",
        "Some Lab Somewhere",
        "someuser",
    ):
        assert forbidden not in blob, f"published provenance leaked {forbidden!r}"

    # The useful, non-identifying provenance must survive.
    assert result["auth_status"]["loggedIn"] is True
    assert result["auth_status"]["apiProvider"] == "firstParty"
    assert "email" not in result["auth_status"]
    assert "orgId" not in result["auth_status"]
