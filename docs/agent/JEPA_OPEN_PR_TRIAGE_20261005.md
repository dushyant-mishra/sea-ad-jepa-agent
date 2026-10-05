# JEPA OPEN-PR TRIAGE — 2026-10-05

This ledger distinguishes **navigation cleanup** from **scientific retraction**. Closing a handoff PR does not delete its branch or invalidate preserved historical evidence.

## Closed in cleanup tranche 2

The following PRs were closed because their primary role was superseded handoff/takeover/navigation. Each received a preservation notice naming PR #210 / the Oct-5 target-authority reset as successor authority:

| PR | Historical role | Cleanup classification |
|---|---|---|
| #37 | Sep-21 FULL104 ETL + safe-lane takeover | `SUPERSEDED__HANDOFF_NAVIGATION` |
| #150 | V28 verified evidence/new-chat handoff | `SUPERSEDED__HANDOFF_NAVIGATION__HISTORICAL_EVIDENCE_PRESERVED` |
| #159 | V32 teacher/Stage75 local-evidence handoff | `SUPERSEDED__HANDOFF_NAVIGATION` |
| #167 | V38 reviewed takeover/branch map | `SUPERSEDED__HANDOFF_NAVIGATION` |
| #183 | V45 handoff + custody-gap boundary | `SUPERSEDED__HANDOFF_NAVIGATION__CUSTODY_HISTORY_PRESERVED` |
| #190 | V51 regulatory-redteam/chat-custody handoff | `SUPERSEDED__HANDOFF_NAVIGATION__HISTORICAL_EVIDENCE_PRESERVED` |
| #197 | V63 external-regulatory handoff/chat custody | `SUPERSEDED__HANDOFF_NAVIGATION__CUSTODY_HISTORY_PRESERVED` |
| #208 | V75 chat-runtime custody + 160-D takeover | `SUPERSEDED__HANDOFF_NAVIGATION__CUSTODY_HISTORY_PRESERVED` |

PR #208 receives an additional scientific qualification: V75's 100K measurement result remains valid within scope, but its proposed learned-160D next action is superseded.

## Intentionally retained open

- PR #210 — current Oct-5 custody + historical target-authority reconciliation.
- PR #211 — current authority-surface cleanup and consistency guard.
- PR #207 — V75 measurement authority remains scientifically relevant; only its next-action text is superseded.
- PR #178 — corrective historical authority containing S9/gradient retractions and target-comparison result.
- PR #163 — unresolved prospective target-design evidence; no target winner selected.
- substantive experiment, ETL, review, and data PRs remain open until individually classified.

## Not yet bulk-closed

Custody/data-publication PRs carrying unique historical bytes (for example V45 publication/custody branches) require explicit evidence-preservation review before closure. Scientific experiment/review PRs are not closed merely because they are old.

## Current guardrail

PR #211 adds a fail-closed validator and CI workflow for the canonical current-authority surface. The guard checks the Oct-5 pointer/date, training-OFF boundary, 500K-not-authorized boundary, no-qualified-target boundary, and separation of width 160 from biological-dimension authority.

## Next triage tranche

1. inventory remaining open PRs by type: `CURRENT`, `SUPERSEDED`, `HISTORICAL_EVIDENCE`, `CUSTODY_ONLY`, `INCOMPLETE_STOPPED`, `DEFERRED`;
2. prioritize docs-only handoff branches and duplicate custody PRs;
3. separately audit unique-byte custody/data-publication PRs before closure;
4. do not delete branches until exact ancestry and unique-evidence preservation are verified.
