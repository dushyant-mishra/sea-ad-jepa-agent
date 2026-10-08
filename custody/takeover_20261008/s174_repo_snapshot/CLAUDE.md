# Claude Code Entry Point — JEPA

Codex and Claude Code are equal implementation peers. Authority comes from
prospectively frozen files, hashes, executable tests, and external review—not
from which agent wrote the code.

Before acting:

1. Read `AGENTS.md`.
2. Read `docs/agent/CURRENT_WORK_CHECKPOINT.json`.
3. Validate it with:
   `python scripts/agent/work_checkpoint.py validate --worktree . --checkpoint docs/agent/CURRENT_WORK_CHECKPOINT.json`
4. Read `docs/exec-plans/active/JEPA_SCIENTIFIC_BLOCKER_EXECUTION.md`.
5. Stop on any identity, authority, firewall, or worktree mismatch.

If the generated checkpoint is absent, regenerate it from the committed state
input with:
`python scripts/agent/update_work_checkpoint.py --worktree .`

Either peer may implement, test, review, commit, and prepare a handoff. Neither
peer may self-promote conclusion-bearing work, weaken a frozen scientific rule,
or merge scientific review branches merely to simplify continuity. Use the
restricted peer bridge only for advisory consultation; normal takeover occurs
by validating the same checkpoint and working in the declared worktree.
