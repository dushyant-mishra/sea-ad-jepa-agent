# Next parallel workstreams — 2026-09-09

The work should proceed in parallel where dependencies permit, but not by letting downstream claims outrun upstream authority.

## Workstream 1 — Real B2 raw-source population authority

Owner: Claude or current executor with local dataset access.

Dependency: committed runner and permission to execute production command.

Output: replayed 20,804-row raw-source population authority.

## Workstream 2 — Replay/verifier hardening

Owner: independent reviewer.

Dependency: none; can start now.

Output: verifier that reads only emitted artifacts and externally supplied roots.

## Workstream 3 — Technical-completeness production materialization

Owner: after Workstream 1 completes.

Dependency: replayed raw-source population authority.

Output: replayed technical-completeness authority over real dataset.

## Workstream 4 — Authority-DAG interface for teacher/student

Owner: design lane.

Dependency: can proceed as design only.

Output: teacher/student input contract requiring authority roots, not detached arrays.

## Workstream 5 — Branch governance

Owner: project maintainer lane.

Dependency: do not merge R5/R6 production claims before replay.

Output: live branches reduced after accepted artifacts are known; stale review branches documented before deletion.

## Workstream 6 — Handoff ledger

Owner: every lane.

Dependency: continuous.

Output: every material change has a short status document naming branch, commit, roots, STOP/PASS disposition, and next blocker.
