# JEPA Authority Freshness Policy

Date: 2026-10-05
Status: `CURRENT_GOVERNANCE_POLICY`

## Rule

`UPDATE_CANONICAL_SURFACE_WHEN_CURRENT_TASK_CLOSES_OR_NEXT_AUTHORIZED_TASK_CHANGES`

The repository must not allow a completed, blocked, retracted, or superseded task to remain advertised as the current scientific task.

## Trigger events

Refresh the canonical surface whenever any of the following happens:

1. the current task reaches a terminal result;
2. the current task is blocked or stopped;
3. a successor task is prospectively authorized;
4. a controlling retraction/supersession changes what future agents should do next;
5. a newly merged audit changes the scientific frontier even if no model/source code changed.

## Files that move together

At minimum update, or verify still accurate:

- `START_HERE.md`;
- `README.md` current-status/current-task language;
- `docs/agent/JEPA_LATEST_HANDOFF_POINTER.json`;
- `docs/agent/CURRENT_AUTHORITY_INDEX.md`;
- `docs/agent/CURRENT_SUPERSESSION_MAP.md`;
- `docs/agent/memory-os/ACTIVE_STATE.md`;
- `docs/agent/memory-os/NEXT_ALLOWED_ACTION.json`.

Generic aliases should route to canonical current state rather than hard-code scientific tasks whenever possible.

## Fail-closed behavior

The current-authority guard must fail when:

- the pointer advertises a task already recorded complete by current authority;
- canonical files disagree about the current task;
- a generic next-action alias hard-codes a superseded task;
- current task/status fields are absent from the live pointer;
- the freshness rule itself is absent from the canonical surface.

## Historical preservation

Freshness is a routing rule, not permission to rewrite history. Historical result, audit, custody, and handoff artifacts retain their exact original claims and provenance. Current files supersede their startup/next-action role without deleting historical evidence.

## Current application

The terminal target-lineage reconstruction is complete and merged. The current frontier is premise qualification prefreeze. `TRAINING=OFF`; Stage-A real-RNA execution is not yet authorized.
