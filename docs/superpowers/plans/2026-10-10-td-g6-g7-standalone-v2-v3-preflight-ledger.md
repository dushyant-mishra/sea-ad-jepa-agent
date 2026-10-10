# SDD ledger — plan: docs/superpowers/plans/2026-10-10-td-g6-g7-standalone-v2-v3-preflight.md

Execution mode: inline/native coordinator session.

Pre-flight interfaces:
- Task 1 common gate -> Tasks 2/3 runtime consumers: exact V3 preflight/mapping schemas and V2 runtime authority; no conflict after controlling amendment.
- Task 2 G6 -> Task 4 cross-entrypoint binding: both use the common authority validator; exact script SHA binding must be symmetric.
- Task 3 G7 -> Task 4 cross-entrypoint binding: both use the common authority validator; G7 remains independently source-authenticating.
- Task 5 documentation consumes exact candidate SHAs/test evidence from Tasks 1-4.

Ruling: original standalone V2 spec's V2 preflight schemas are superseded by the V3-preflight amendment because PR #252/#254 exposed the contract defect and PR #255 prospectively repairs it. Cost if wrong: future value path would bind to a superseded preflight receipt and must not be executed.

Ruling: G7 now requires a genuine G6 V2 PASS receipt bound to the same preflight, runtime authorization and exact G6/G7 code SHAs. This enforces the frozen G6-then-G7 sequence mechanically while keeping G7 scientifically independent of G6 values. Cost if wrong: an operator could skip a failed G6 and still perform G7 value reads.

Ruling: global S174 custody may hash all shards and read shape/cell-ID geometry, but must not open every shard's count-data array merely for custody. Count arrays are opened only for shards with natural Sample-A overlap that G7 will actually compare. Cost if wrong: G7 would inspect corrected values outside its natural-overlap scope.

Ruling: G6 spends its namespace at execution start by writing a non-PASS start marker, so even an early failure cannot leave an apparently reusable empty namespace. Cost if wrong: a failed value-read attempt could be silently retried in-place and blur custody.

Implementation candidate branch: `impl/td-g6g7-standalone-v2-v3preflight-20261010`, stacked on PR #255 head `bf253a4dd62d943398f9ff59ed8b1e74777140a5` at branch creation.

Environment limitation: coordinator cannot execute repository pytest in its container; no RED/GREEN or PASS claims may be made here. Candidate code may be prepared and reviewed structurally, but task completion remains pending canonical-machine qualification.
