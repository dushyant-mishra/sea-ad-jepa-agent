# TD G6/G7 standalone V2 static audit — 2026-10-10

Status: `STATIC_AUDIT_HARDENED__UNQUALIFIED__DO_NOT_EXECUTE`

Candidate: PR #258, branch `impl/td-g6g7-standalone-v2-v3preflight-20261010`.
Recorded head at this audit checkpoint: `c5d9c64cf42dc8c12d91672458689c0a0a67f472`.
Base: PR #255 head `bf253a4dd62d943398f9ff59ed8b1e74777140a5`.

No corrected expression value was read during this audit. No runtime value authorization exists.

## Defects found before qualification

1. **Mapping and driver PASS terminals were conflated.**
   - Mapping must be `PASS_TD_RELATIONAL_MAPPING_PREFLIGHT_VALUE_BLIND`.
   - Driver must be `PASS_TD_RELATIONAL_PREFLIGHT_DRIVER_VALUE_BLIND`.
   - The common gate and tests now distinguish them.

2. **Shared custody code was initially outside runtime code binding.**
   The runtime authority now binds the shared common module in addition to G6 and G7.

3. **Working-tree code identity was CRLF/LF-sensitive.**
   Runtime code identity now uses LF-normalized text hashes and exact entrypoint paths for common/G6/G7, plus exact implementation commit.

4. **Dirty code was not initially rejected.**
   The common gate now requires all three controlling scripts to be Git-tracked and clean relative to the bound commit.

5. **G7 sequencing was initially operator-only.**
   G7 now requires a genuine `JEPA_TD_RELATIONAL_G6_RECEIPT_V2` with `PASS_TD_G6_SOURCE_LIBRARY_EXACT`, bound to the same preflight, mapping, runtime authorization and common/G6/G7 code identity.

6. **G7 initially authenticated the G1b freeze/cache without cryptographically ingesting the actual G1b PASS result.**
   G7 now derives both `S174_REBUILD_G1B_RESULT_V1.json` and `S174_REBUILD_G1B_FREEZE_V1.json` directly from exact immutable pass commit `4ab8e2101f2e595d9a97df05517d6e672768ecec`; it requires `G1b_pass=true`, R1-R7 all true, and the exact frozen G1b freeze SHA `0513421e45865f290bddf8b0be56d64c7d9c5297bf0150ea6b9df286514b5f8f`.

7. **Global S174 custody initially inspected more count data than necessary.**
   Global custody now hashes every shard and checks shape/cell-ID geometry without opening all count arrays. Count values are opened only on shards with genuine natural Sample-A overlap being compared.

8. **G6 failed-attempt namespace reuse risk.**
   G6 now writes a non-PASS execution-start marker immediately after authority validation so any later failed attempt permanently spends the namespace.

## Still unverified

The coordinator environment cannot run the repository pytest suite because it cannot retrieve the checkout over the network. GitHub reports no status checks for the candidate. Therefore no RED/GREEN or PASS claim is made.

The candidate must remain `DO NOT EXECUTE` until:
1. PR #255 produces a reviewed V3 G4/G5 PASS;
2. PR #258 is reconciled to that exact accepted lineage;
3. its focused tests are executed on the canonical machine with actual results recorded;
4. only then, after a separate explicit owner decision, may a V2 runtime value authorization object be created.

Even future G6+G7 PASS stops before corrected TD56/TD57B/TD57C/TD59 biological replay.

Hard terminal:
`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
