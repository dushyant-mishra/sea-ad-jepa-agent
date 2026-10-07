# JEPA V63/V64 duplication recheck — 2026-10-06

Status: HISTORICAL_RECONCILIATION__NO_NEW_SCIENTIFIC_AUTHORITY

## Purpose

Re-audit newly surfaced V63/V64 files against historical GitHub work before proposing any new Nott/NIH-CARD target work.

## Findings

1. The newly uploaded `NIHMS1066836-supplement-Table_S5.xlsx` is byte-identical to the authenticated Nott Table S5 already used in V64. Local SHA-256:
   `81c99689533d9da372cecdd469e7ff02cc985720105b83b3bd66c3ac8c93972e`.
   This exactly matches the V64 handoff authority.

2. Nott Table S5 was already processed well beyond discovery:
   - C3 exact identity retained 102,701 / 104,802 contact pairs.
   - `E2_NOTT_CANDIDATE` was instantiated with 20,709 edges, 5,253 genes, and 7,390 promoter anchors.
   - upstream cross-checks, attrition accounting, deterministic rebuild, and same-study accessibility limitation were recorded.
   Therefore do NOT rebuild E2 from the workbook as new work.

3. The NIH-CARD schema/pairing problem was also later closed on real files. V64 handoff records:
   - RNA 1,501,089 x 38,606;
   - ATAC same nuclei x 521,217 peaks;
   - exact 1,501,089 pairing bijection with independent corroboration;
   - 87,384 microglia, 357 donors, 282 donors meeting the frozen >=100-MG support threshold.
   Therefore the earlier `h5ad_schema_probe.py` plus A/B receipts are historical bounded fixtures/mechanics, not the current real-data blocker.

4. The uploaded V63 fixture/probe hashes match the V63 custody manifest exactly:
   - `h5ad_schema_probe.py` `8e6dc7b634b1bcad0486c2e933c37ad61b94080f1ad19e8e2dfe8c556c2250c8`
   - `A_receipt.json` `f84de0e7109ccde8d7d600723c7e43d0546d6086a3d283983b46ef4761ea5070`
   - `B_receipt.json` `b6b384149bcb2e550828df9275cdf48f45040f95de886168892803f4c8505866`
   - `truth.json` `973fc71c97256904a8d16445a213576ddc5bb8dba2869ca6f6e5ba60b486121b`
   - `make_fixtures.py` `4b6ce2e4a23b40d83913c28a4704ac923d5fb9a2ded555a638895586cc3b3ca5`
   - Corces MOESM12 `a3a6fa5c0e5d3080c7d45287f19cb37edf862ed05f6a904c92b64c6333ef3327`
   - Corces MOESM5 `2d1aa847e0f075728e73b91e9d793450e278166edbb2f2a082e264f873c94707`
   These are already-custodied historical assets, not newly discovered evidence.

5. The V64 target-architecture handoff already recognized the factorized hypothesis:
   `Z_global`, `Z_query`, `Z_reg`, `Z_response`, with no premature fusion.
   It also already measured the E2/NIH-CARD shared activity-expression bias and prohibited counting separate resources as automatically independent evidence.

6. The actual unfinished V64 scientific/execution boundary was downstream:
   - finish the exact admissible-control sampler (`A_exact = A_interior union A_supplement`), including chain boundaries/gaps/minus-strand/unproven regions;
   - pass the frozen exact-sampler qualification, including 32 real-edge comparisons to brute-force liftOver;
   - rerun Phase A;
   - STOP FOR AUDIT before opening Phase B matrix correspondence;
   - then build the coverage + evidence-independence atlas;
   - only then run the factorized-target architecture tournament.

## Spillover verdict

Do not restart Nott ingestion, E2 construction, NIH-CARD pairing/schema discovery, or Corces donor/contact audit. Those are completed historical work.

The live question is whether later V64/V73 work subsequently completed or superseded the exact-control/Phase-A boundary. Audit that lineage before any new Stage-B design or execution.

Hard boundaries unchanged: TRAINING=OFF; protected outcomes remain closed unless separately authorized; no target winner promoted by this reconciliation.