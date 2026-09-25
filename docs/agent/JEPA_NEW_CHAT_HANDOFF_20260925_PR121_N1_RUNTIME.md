# JEPA NEW CHAT HANDOFF — 2026-09-25 — PR121 / N1 / runtime assets

**Governance:** This is a documentation-only snapshot from live GitHub heads, NOT a merge or scientific qualification. Main was `c49b13bd75c2d23716c777336db8fbfc78c09cd0` at branch creation. First read `START_HERE.md`, the existing V25 canonical handoff/pointer/state and historical audit index on main; then this successor. **Always re-fetch heads before modifying code.** This handoff does not supersede frozen formulas, the main V25 handoff, or any controlled execution authorization. No prior smaller-run artifacts can stand in for FULL104.

## Exact live PR heads verified September 25

| PR | head SHA | role | status |
|---|---|---|---|
| 77 | `9a2a30e4c4c99be2a8f948aba680524c786d2737` | published experimental ETL code/results, reported 58MB committed outputs | open draft |
| 86 | `0ffb62cac6ea3d6e0e1b9cef3fa3e95f2d581e91` | GSE254205 V2 assayed-undetected semantics | open draft |
| 91 | `56600f66492b18af20edcfe5d11761d2cdca9383` | GSE301119 guide-by-donor support census | open draft |
| 92 | `bc09c0f432db6e17bec3047baeb0812975043937` | GSE311359 BIN1 duplicate display-label STOP, historical V1 | open draft |
| 94 | `9cc155a659f9a70bf2f1e7a1fd9cc05283089cbf` | GSE240609 GEO sample-identity authority | open draft |
| 117 | `9c524f49dd1486e6c7f4a4b211ef70bff4082db6` | cross-study metadata, Day8, frozen HGNC | open draft |
| 118 | `d719ce1619f8cf6b6b101bc7188b903bc906891b` | original physical ETL audit handoff, accepted defects | open draft |
| 119 | `ed3e7b8ccf5b8fe2ecc367a911fec9c1a9a98255` | independent 16-asset fail-closed inventory and 10 synthetic adversaries | open draft |
| 120 | `136d1257467a7d80690d9f287ca7399c7138e038` | prospective all-104 corrected N1 raw-count verifier, 9 synthetic adversaries | open draft |
| 121 | `aaf561cfdc60ffe29c4d79094c16ce5e524f7d2d` | Claude PR118 repairs, physical receipts, 53 adversaries, caveats | open draft |

PR121 base: `physical/etl-completion-claude-20260924`. Its two latest GitHub workflows **passed at the exact PR121 head**: inventory run `36152332948`, producer run `36152332956`. These are CI evidence, not independent biological or physical confirmation by this chat. PR119 and PR121 overlap on the inventory defect; compare and consolidate rather than blindly merge. PR92's BIN1 V1 STOP remains historically correct; PR121 V2 is the successor.

## PR121 — what Claude claims, and what remains scientifically open

Read `analysis/therapeutic_perturbation_etl/PR118_AUDIT_RESPONSE_20260925.md`, `PR118_REPAIR_QUALIFICATION_CONTRACT_20260925.md`, `SELF_AUDIT_20260925.md`, the R/Python producer scripts, all red-team tests and committed JSON receipts **at PR121 head**. PR121 reports P0-1..P0-5 and P1-7 fixed and physically tested; P1-6/P1-8 partial; P2-9 blocked. Claimed: 16/16 physical assets (4,450,940,052 bytes); 53 adversaries across four producers; GSE301119 two modalities/two donors independently *implemented* with max discrepancy ~1.776e-15 over ~22.7M entries; GSE254205 108,351/108,351 values match exactly at stored six-decimal precision; GSE311359 BIN1 identity-keyed V2 removes 14 phantom rows and matches all 2,434 unaffected non-BIN1 units. **Do not silently promote these claims beyond the actual PR121 receipts and independent review.**

**Critical S4:** The same author wrote the R producer, Python reproducer and their common estimand specification. Relabel any `INDEPENDENT_REPRODUCED` as `IMPLEMENTATION_REPRODUCED` for scientific governance; a *different author* must derive the estimand from first principles and independently check source-level biological contrast and direction. Exact agreement cannot validate a shared wrong estimand. Two donors are not population replication. GSE178317 four capture wells share one pooled preparation. BIN1 feature IDs resolve display-name collisions but do not prove protospacer sequence, guide efficiency or cis causality. GSE335887 ARID5B has no authenticated deposited guide; no blanket 31-target direct-intervention claim.

**Still open:** independent GSE241858 and GSE240609 bulk recalculation; HGNC 13,373 resolved /116 unresolved common-feature crosswalk applied to physical scope; independent GSE301119 estimand authorship; GSE335887 prep count/run chemistry; GSE175721 author-provided per-cell guide assignment; protected GSE254205 ancillary snRNA/ATAC/LD-sort remain unopened. Corrected status/exposure registry is on PR121; do not reuse PR118's stale readiness JSON or hand-authored matrix descriptions. The PR121 response says acceptance criteria **not met**. Do not call ETL_COMPLETE, BIOLOGICAL_REPLICATION or PROSPECTIVE_CONFIRMATION.

## FULL104 / N1 — separate track, never displaced by ETL

Original FULL104: 4,553,407 cells, 104 donors, 42 operators, 41,238 addresses, 17,186 strict-core genes, 8,915 Level-4 count blocks. Historical original N1 source encoding failed and was quarantined. Corrected derivative SHA-256 `4b15ee5238c6e48d931329d222a9488a7b4f122c58767b6615a0b480afc4800b`, 363,053,057 bytes; frozen pass1 SHA `37f79e49f11364daa487ad9e5a5680f72378daf338852765d2f52e1e98d90ba1`. PR83/85 qualified the corrected adapter and hardened authorization/receipt handling; PR120 adds an outcome-blind **prospective** exact all-104 ×17,186 donor_nnz and donor_umi raw-count reaggregation from all 8,915 raw blocks, with nine synthetic tests passing. **The real physical all-104 raw-count comparison HAS NOT been verified.** Use `analysis/v5_full104_information_channel_redteam_20260920/N1_ALL104_RAW_REAGGREGATION_RUNBOOK_20260925.md` on PR120. Have an independent reviewer inspect accumulator and cell/donor/source lineage before trusting a physical PASS; then separately verify crash-safe resume and existing governance authorization. Never run real N1 masks based solely on synthetic CI.

## Local assets available in this chat, not committed as binaries

`docs/agent/JEPA_RUNTIME_LOCAL_ASSETS_SHA256_20260925.json` on this handoff branch lists **all 29 physically present local files**, 1,329,773,116 bytes, exact relative paths/sizes/SHA-256. They include original historical T1 checkpoint ZIPs, the 410MB foundation calibration bundle, two 304MB split expression ZIP parts, 3.6MB expression metadata, an unqualified 1.5MB NPZ, metadata/Day8/HGNC cross-study small ZIPs, two prior Claude handoff Markdown files, WSL/status notes and the cross-study audit directory. The binary files and exact local CSV/text bytes **have not been uploaded to GitHub by this handoff**: the connected GitHub text-file API cannot transfer 1.3GB of local runtime files, and the current container has no direct GitHub network route. **Do not confuse the published inventory with uploaded data.** The PR77/PR117/PR121 branches already contain many *separately committed* scripts/results; compare SHA and content before declaring any local asset redundant. Recover the remaining exact bytes from conversation attachments or GPU laptop by hash; do not rename or fabricate URLs.

The split expression parts were physically concatenated in this chat and the combined ZIP's SHA-256 `63239898b9c93f29c20b62b84dc9b94c2c87e3e3f2b7958b7435847e3b9541f7`, size 607,959,761 and ZIP CRC all verified; temporary joined file removed. Foundation calibration bundle: 60 ZIP members, 2,777,579,957 uncompressed bytes. `checkpoints.zip` contains T1 u0000/u0205; `t1_checkpoint_u0200.zip` contains T1 u0010/u0025/u0050/u0100/u0200. Historical trajectories are **not** evidence that current FULL104 N1 training ran. The 1.5MB NPZ includes object-array metadata; do not load untrusted pickle.

## Exact new-chat startup

1. Open `START_HERE.md` on live main, then `docs/agent/JEPA_LATEST_HANDOFF_POINTER.json`, V25 canonical handoff/state/runtime asset manifest and historical audit index. Then read **this** September 25 successor and its runtime SHA manifest.
2. Re-fetch live heads of PR77, 86, 91, 92, 94, 117, 118, 119, 120, 121. Check the latest GitHub Actions *at the exact head SHA* and branch ancestry. Avoid merges until overlapping code and scope are reconciled.
3. Audit PR121 **source and receipts** against its qualification contract. Specifically independently derive GSE301119 donor-aware estimand and sign; do not accept implementation agreement as scientific independence. Independently recompute GSE241858/GSE240609; verify HGNC missingness and exposure registry.
4. Have the GPU-laptop lane run PR120's outcome-blind full-104 physical verifier on the SHA-pinned corrected derivative and all authenticated raw blocks, after independent static review. Return small receipts, source hashes and per-mismatch diagnostics, not >30GB data.
5. Reconcile PR119's 16-root hardening with PR121's own V2 inventory; preserve both negative-test coverage and frozen expected-source roots, avoid duplicate/contradictory gates. Preserve the original PR118 and PR92 as historical audit evidence.
6. Restore exact local files by manifest if needed; never let historical smaller-run T1 artifacts or placeholders silently substitute for FULL104. Do not open protected GSE335887 or GSE254205 ancillary outcomes. All actual training remains OFF.

**Hard status:** `TRAINING=OFF` · `AUDIT_B_N1=UNOPENED` · `PROTECTED_FULL104_OUTCOMES=UNOPENED` · `D_SHARED_G5=UNOPENED` · `RARE_TAIL_MOLECULAR=UNOPENED` · `THERAPEUTIC_RANKING=OFF`. This docs-only handoff adds no authorization or biological evidence.
