# AGENTS.md — JEPA Project

## Mission

Build a pathology-blind human-brain RNA foundation representation that preserves
and infers meaningful biological programs from incomplete heterogeneous molecular
evidence. Exact missing-transcript reconstruction is not the biological objective.

## Mandatory startup

1. Read `docs/agent/CURRENT_WORK_CHECKPOINT.json`.
2. Validate it with `scripts/agent/work_checkpoint.py` before acting.
3. Read `docs/exec-plans/active/JEPA_SCIENTIFIC_BLOCKER_EXECUTION.md`.
4. Stop on any Git, authority, file, firewall, or next-action mismatch.

Codex and Claude Code are equal implementation peers. Either may implement,
test, review, commit, and hand off through the same checkpoint. Neither agent may
self-promote conclusion-bearing work.

## Repository topology

- Canonical project: `D:/Jepa project`.
- Same files under WSL: `/mnt/d/Jepa project`.
- WSL is a compute backend, not a second repository.
- Preserve dirty canonical workspaces. Use an isolated worktree for scoped work.
- Do not reset, clean, stash, rewrite history, or alter user changes.

## Hard scientific invariants

- No pathology labels during foundation representation learning.
- DEV/SEALED RNA stay closed unless explicitly authorized.
- `MEASURED_SCALAR`, `STRUCTURALLY_UNMEASURED`,
  `MEASURED_COLLISION_UNRESOLVED`, and artificial masks are distinct.
- Measured zero remains measured evidence.
- Lower loss is not biological success; rotation is not information loss.
- Rare/local failures cannot be hidden by aggregate means.
- Historical T1 is not a qualified biological model and must not be rehabilitated.
- Old conclusion-bearing results remain immutable historical evidence.

## Implementation governance

`MANDATORY_IMPLEMENTATION_VERIFIER_V1` is permanent project governance.
Conclusion-bearing code requires implementer, independent implementation
verifier with veto, specialist review, and then any expensive compute or
scientific promotion. A change of agent, phase name, or architecture does not
waive this rule.

## Working discipline

- Repository authority and stronger executable scientific evidence outrank prompt
  wording; document genuine conflicts and fail closed.
- Write behavior tests before implementation changes.
- Use targeted reads, `rg`, compact artifacts, and hashes.
- Keep routine work single-agent. Add scoped independent critics only at a real
  scientific/promotion boundary.
- Never invent unfrozen thresholds, estimands, biological mappings, observation
  semantics, rare criteria, or production weights.
- Save large evidence to files and report only decision-changing results.
