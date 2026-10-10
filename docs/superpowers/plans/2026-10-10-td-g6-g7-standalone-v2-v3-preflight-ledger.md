# SDD ledger — plan: docs/superpowers/plans/2026-10-10-td-g6-g7-standalone-v2-v3-preflight.md

Execution mode: inline/native coordinator session.

Pre-flight interfaces:
- Task 1 common gate -> Tasks 2/3 runtime consumers: exact V3 preflight/mapping schemas and V2 runtime authority; no conflict after controlling amendment.
- Task 2 G6 -> Task 4 cross-entrypoint binding: both use the common authority validator; exact script SHA binding must be symmetric.
- Task 3 G7 -> Task 4 cross-entrypoint binding: both use the common authority validator; G7 remains independently source-authenticating.
- Task 5 documentation consumes exact candidate SHAs/test evidence from Tasks 1-4.

Ruling: original standalone V2 spec's V2 preflight schemas are superseded by the V3-preflight amendment because PR #252/#254 exposed the contract defect and PR #255 prospectively repairs it. Cost if wrong: future value path would bind to a superseded preflight receipt and must not be executed.

Environment limitation: coordinator cannot execute repository pytest in its container; no RED/GREEN or PASS claims may be made here. Candidate code may be prepared, but task completion remains pending canonical-machine qualification.
