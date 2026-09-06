#!/usr/bin/env python3
"""Restricted, advisory-only bridge to the authenticated Antigravity Claude CLI."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from scripts.agent.work_checkpoint import atomic_write_json, sha256_file
except ModuleNotFoundError:  # Support direct `python scripts/agent/...` execution.
    from work_checkpoint import atomic_write_json, sha256_file


_SENSITIVE_KEY = re.compile(r"token|secret|password|credential|api.?key", re.I)


def _version_key(path: Path) -> tuple[int, ...]:
    match = re.search(r"claude-code-([0-9.]+)-", path.as_posix())
    return tuple(int(part) for part in match.group(1).split(".")) if match else (0,)


def discover_claude(explicit: Path | None) -> Path:
    """Resolve an explicit CLI or the highest-version Antigravity Claude CLI."""
    if explicit is not None:
        candidate = Path(explicit).resolve()
        if not candidate.is_file():
            raise FileNotFoundError(f"Claude executable not found: {candidate}")
        return candidate
    profile = Path(os.environ.get("USERPROFILE", Path.home()))
    candidates = list(
        (profile / ".antigravity-ide" / "extensions").glob(
            "anthropic.claude-code-*-win32-x64/resources/native-binary/claude.exe"
        )
    )
    candidates = [candidate.resolve() for candidate in candidates if candidate.is_file()]
    if not candidates:
        raise FileNotFoundError("No Antigravity Claude CLI installation found")
    return max(candidates, key=_version_key)


def build_consult_command(
    executable: Path, prompt: str, max_turns: int = 1
) -> list[str]:
    """Construct one restricted, tool-free, non-interactive advisory request."""
    if max_turns != 1:
        raise ValueError("restricted consultation permits exactly one response")
    if not prompt.strip():
        raise ValueError("prompt must not be empty")
    return [
        str(Path(executable)),
        "--print",
        prompt,
        "--output-format",
        "json",
        "--restricted",
        "--strict-mcp-config",
        "--permission-mode",
        "dontAsk",
        "--max-budget-usd",
        "0.25",
        "--tools=",
    ]


def _run(argv: list[str], cwd: Path | None = None, timeout: int = 600):
    return subprocess.run(
        argv,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout,
    )


def _scrub(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: ("[REDACTED]" if _SENSITIVE_KEY.search(str(key)) else _scrub(item))
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_scrub(item) for item in value]
    return value


def _auth_summary(executable: Path) -> dict[str, Any]:
    completed = _run([str(executable), "auth", "status", "--json"], timeout=30)
    try:
        parsed = json.loads(completed.stdout) if completed.returncode == 0 else {}
    except json.JSONDecodeError:
        parsed = {}
    return _scrub(parsed)


def consult(
    executable: Path,
    prompt_path: Path,
    output_dir: Path,
    provenance: dict[str, Any],
    *,
    max_turns: int = 1,
    cwd: Path | None = None,
) -> dict[str, Any]:
    """Run a restricted consultation and atomically publish an advisory record."""
    executable = discover_claude(executable)
    prompt_path = Path(prompt_path).resolve()
    output_dir = Path(output_dir).resolve()
    prompt = prompt_path.read_text(encoding="utf-8")
    argv = build_consult_command(executable, prompt, max_turns=max_turns)
    version_result = _run([str(executable), "--version"], timeout=30)
    started = datetime.now(timezone.utc).isoformat()
    try:
        completed = _run(argv, cwd=cwd, timeout=600)
        process_error = None
    except subprocess.TimeoutExpired as exc:
        completed = subprocess.CompletedProcess(argv, 124, exc.stdout or "", exc.stderr or "")
        process_error = "TIMEOUT"
    finished = datetime.now(timezone.utc).isoformat()

    parsed_response: Any = None
    response_valid = False
    if completed.returncode == 0:
        try:
            parsed_response = json.loads(completed.stdout)
            response_valid = isinstance(parsed_response, dict)
        except (json.JSONDecodeError, TypeError):
            pass
    if completed.returncode != 0:
        status = "STOP_CLAUDE_PROCESS_FAILED"
    elif not response_valid:
        status = "STOP_CLAUDE_RESPONSE_INVALID"
    else:
        status = "CONSULTATION_COMPLETE"

    process_diagnostic = None
    if completed.returncode != 0:
        error_payload = None
        for diagnostic_stream in (completed.stdout, completed.stderr):
            try:
                candidate = json.loads(diagnostic_stream)
            except (json.JSONDecodeError, TypeError):
                continue
            if isinstance(candidate, dict):
                error_payload = candidate
                break
        if isinstance(error_payload, dict):
            process_diagnostic = {
                key: error_payload.get(key)
                for key in ("type", "is_error", "terminal_reason", "api_error_status", "result")
            }

    record = {
        "schema": "CLAUDE_PEER_CONSULTATION_V1",
        "status": status,
        "advisory_only": True,
        "scientific_promotion_authority": False,
        "single_response_enforced": True,
        "restriction": {
            "tools": "DISABLED",
            "mcp": "STRICTLY_DISABLED",
            "permission_mode": "dontAsk",
            "process_timeout_seconds": 600,
            "budget_ceiling_usd": 0.25,
        },
        "executable": str(executable),
        "executable_sha256": sha256_file(executable),
        "version": version_result.stdout.strip(),
        "auth_status": _auth_summary(executable),
        "prompt_path": str(prompt_path),
        "prompt_sha256": sha256_file(prompt_path),
        "provenance": _scrub(provenance),
        "argv": argv,
        "started_utc": started,
        "finished_utc": finished,
        "exit_code": completed.returncode,
        "process_error": process_error,
        "process_diagnostic": process_diagnostic,
        "stdout_sha256": hashlib.sha256(completed.stdout.encode("utf-8")).hexdigest(),
        "stderr_sha256": hashlib.sha256(completed.stderr.encode("utf-8")).hexdigest(),
        "response": parsed_response if response_valid else None,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    atomic_write_json(output_dir / "CLAUDE_PEER_CONSULTATION.json", record)
    return record


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("consult")
    run.add_argument("--executable", type=Path)
    run.add_argument("--prompt", type=Path, required=True)
    run.add_argument("--out", type=Path, required=True)
    run.add_argument("--repo", type=Path, default=Path.cwd())
    run.add_argument("--max-turns", type=int, default=1)
    run.add_argument("--provenance", type=Path)
    return parser


def main() -> int:
    args = _parser().parse_args()
    executable = discover_claude(args.executable)
    provenance = (
        json.loads(args.provenance.read_text(encoding="utf-8"))
        if args.provenance
        else {}
    )
    result = consult(
        executable,
        args.prompt,
        args.out,
        provenance,
        max_turns=args.max_turns,
        cwd=args.repo,
    )
    print(json.dumps({"status": result["status"], "output": str(args.out)}))
    return 0 if result["status"] == "CONSULTATION_COMPLETE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
