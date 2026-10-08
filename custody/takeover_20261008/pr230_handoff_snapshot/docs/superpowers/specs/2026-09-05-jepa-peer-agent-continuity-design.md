# JEPA Peer-Agent Continuity Design

**Status:** Prospective design awaiting user review
**Scope:** Engineering continuity and auditability only; no scientific authority is changed by this document.

## Purpose

Codex and Claude Code are equal implementation agents. Either may start, pause,
review, or resume a JEPA task. Neither agent receives scientific authority from
its identity, and neither may self-promote conclusion-bearing work.

The durable repository state—not chat history—is the handoff authority.

## Invariants

- The dirty canonical workspace at `D:/Jepa project` remains untouched.
- Work occurs in an explicitly recorded isolated worktree.
- Only the 104 `reader_fit` donors are lawful unless a later prospective
  authority explicitly expands access.
- Reader-validation, reader-oracle, DEV, SEALED, and pathology expression remain
  closed.
- Real F1, fresh-u0 training, and other expensive scientific execution remain
  unauthorized until their required gates pass.
- Historical artifacts and branches are immutable evidence.
- Every conclusion-bearing result must pass the permanent implementation
  verifier before promotion.

## Peer model

The current work unit records an `implementing_agent` of `codex`, `claude`, or
`human`, but this field is provenance only. The next agent must validate the
recorded Git state, inputs, hashes, tests, and firewall before continuing.

Either agent may:

- implement an approved task;
- run engineering tests and synthetic diagnostics;
- identify and preserve a STOP;
- prepare a checkpoint for the other agent.

Neither agent may:

- reinterpret an unverified artifact as frozen authority;
- alter a scientific rule after inspecting its outcome;
- certify its own conclusion-bearing implementation;
- silently continue from a mismatched worktree, commit, input, or checkpoint.

## Persistent entry points

### `CLAUDE.md`

Claude Code's automatic entry point. It contains only stable project rules and
points to the current machine-readable checkpoint and active execution plan.
It does not duplicate volatile scientific history.

### `docs/exec-plans/active/JEPA_SCIENTIFIC_BLOCKER_EXECUTION.md`

The approved dependency-ordered plan. It identifies the current work unit and
records which later units are blocked.

### `docs/agent/CURRENT_WORK_CHECKPOINT.json`

The machine-readable continuity authority. Required fields include:

- schema version and checkpoint status;
- canonical repository and isolated worktree paths in Windows and WSL form;
- branch, HEAD, base commit, and expected remote base;
- implementing agent and previous agent;
- active work unit, last completed step, and exact next action;
- modified/untracked file list and byte hashes;
- conclusion-bearing source and input hashes;
- commands already run and their terminal results;
- current scientific authorization and explicit forbidden actions;
- firewall counters;
- unresolved failures and whether continuation is lawful;
- checkpoint semantic SHA-256.

The checkpoint is regenerated deterministically and written atomically.

### `docs/agent/CLAUDE_TAKEOVER.md`

A compact human-readable rendering of the checkpoint. It tells Claude where to
resume, what not to rerun, and which claims remain provisional. It never
supersedes the JSON checkpoint.

### `scripts/agent/update_work_checkpoint.py`

A deterministic, non-scientific utility that inventories the current worktree,
hashes declared files, verifies required fields, computes the checkpoint root,
and writes staging-first before atomic publication. It does not read expression,
checkpoints, outcomes, or protected metadata.

## Codex-to-Claude consultation bridge

The authenticated Antigravity Claude Code CLI is used directly; no third-party
MCP server is installed. Consultation mode is read-only and bounded:

- invoke Claude with non-interactive JSON output;
- use restricted permissions and no autonomous writes;
- provide only the active contract, relevant source files, tests, and question;
- impose explicit turn and cost bounds where supported;
- save the exact prompt, response, Claude version, worktree HEAD, input hashes,
  and response hash under a review artifact;
- never create an automatic Codex-to-Claude-to-Codex loop.

Claude takeover is different from consultation: the user opens or continues an
interactive Claude Code session in the recorded worktree. Claude reads
`CLAUDE.md`, validates `CURRENT_WORK_CHECKPOINT.json`, and resumes the exact next
action.

## Periodic implementation verification

Verification occurs at four boundaries:

1. **Before editing:** validate worktree identity, authority hashes, and scope.
2. **After each behavior change:** run a red-green TDD cycle and focused mutation
   tests.
3. **Before commit or expensive compute:** inspect the complete diff, run the
   independent calculation where applicable, verify firewalls, and refresh the
   checkpoint.
4. **Before scientific promotion:** invoke exactly one independent implementation
   verifier unless a broader scientific board is explicitly required.

Routine work uses no agents. A verifier is invoked only at a conclusion-bearing
promotion boundary. Self-review can find defects but cannot replace that veto.

## Handoff protocol

Before either agent yields:

1. Stop at a resumable boundary when possible.
2. Verify no unexpected process is still mutating outputs.
3. Run the relevant focused tests.
4. Record the exact Git diff and file hashes.
5. Refresh and validate the checkpoint atomically.
6. Update the human-readable takeover note.
7. Commit completed verified units; leave unfinished work explicit and unclaimed.

The receiving agent must fail closed on any mismatch. It must not repair the
record merely to make continuation possible.

## First scientific work unit after continuity setup

The first active work unit is the synthetic C2 gradient-path bisection. It will
preserve the historical defective and simplified healthy cases, vary one
prospectively declared factor at a time, and identify the first operation that
restores the 48 mandatory attention-normalization/Q/K/V gradients. Until the
implementation and provenance are independently verified, its result remains
`PROVISIONAL` and cannot amend DEC-013 or authorize training.

## Acceptance criteria

- Both CLIs can read the same worktree and checkpoint.
- A checkpoint round-trip is deterministic.
- Dirty-file, wrong-HEAD, corrupted-hash, and forbidden-access mutations fail.
- Consultation mode cannot write project files.
- A simulated Codex-to-Claude and Claude-to-Codex takeover resumes the same next
  action without relying on chat context.
- No scientific data or result is accessed during continuity-system tests.
