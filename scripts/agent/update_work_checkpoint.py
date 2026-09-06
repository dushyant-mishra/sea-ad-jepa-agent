#!/usr/bin/env python3
"""Regenerate the local JEPA checkpoint and deterministic peer takeover note."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    from scripts.agent.work_checkpoint import (
        atomic_write_json,
        build_checkpoint,
        validate_checkpoint,
    )
except ModuleNotFoundError:  # Support direct `python scripts/agent/...` execution.
    from work_checkpoint import atomic_write_json, build_checkpoint, validate_checkpoint


def render_takeover_markdown(checkpoint: dict[str, Any]) -> str:
    """Render a deterministic, non-authoritative view of a checkpoint."""
    git = checkpoint["git"]
    actions = "\n".join(
        f"{index}. `{action}`"
        for index, action in enumerate(checkpoint["next_authorized_actions"], 1)
    )
    blockers = "\n".join(
        f"- `{blocker}`" for blocker in checkpoint["unresolved_blockers"]
    ) or "- None"
    return (
        "# JEPA Peer Takeover\n\n"
        "> Generated from `CURRENT_WORK_CHECKPOINT.json`; the JSON is authoritative.\n\n"
        "Codex (`CODEX`) and Claude Code (`CLAUDE_CODE`) are equal implementation "
        "peers. Neither can self-promote; both cannot promote their own "
        "conclusion-bearing work.\n\n"
        f"- Branch: `{git['branch']}`\n"
        f"- HEAD: `{git['head_sha']}`\n"
        f"- origin/main: `{git['origin_main_sha']}`\n"
        f"- Gate: `{checkpoint['gates']['current']}`\n"
        f"- Checkpoint SHA-256: `{checkpoint['checkpoint_semantic_sha256']}`\n\n"
        "## Exact next actions\n\n"
        f"{actions}\n\n"
        "## Unresolved blockers\n\n"
        f"{blockers}\n\n"
        "Validate the checkpoint before acting. Any mismatch is a STOP.\n"
    )


def update(repo: Path, worktree: Path, state_path: Path, checkpoint_path: Path, takeover_path: Path) -> dict[str, Any]:
    state = json.loads(state_path.read_text(encoding="utf-8"))
    checkpoint = build_checkpoint(repo, worktree, state)
    atomic_write_json(checkpoint_path, checkpoint)
    takeover_path.parent.mkdir(parents=True, exist_ok=True)
    takeover_path.write_text(render_takeover_markdown(checkpoint), encoding="utf-8", newline="\n")
    errors = validate_checkpoint(checkpoint, repo, worktree)
    if errors:
        raise RuntimeError(f"generated checkpoint failed validation: {errors}")
    return checkpoint


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--worktree", type=Path, required=True)
    parser.add_argument("--state", type=Path, default=Path("docs/agent/CURRENT_WORK_CHECKPOINT_STATE.json"))
    parser.add_argument("--checkpoint", type=Path, default=Path("docs/agent/CURRENT_WORK_CHECKPOINT.json"))
    parser.add_argument("--takeover", type=Path, default=Path("docs/agent/CLAUDE_TAKEOVER.md"))
    args = parser.parse_args()
    checkpoint = update(args.repo, args.worktree, args.state, args.checkpoint, args.takeover)
    print(checkpoint["checkpoint_semantic_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
