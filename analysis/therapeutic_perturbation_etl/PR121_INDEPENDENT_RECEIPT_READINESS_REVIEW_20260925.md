# Independent PR #121 review: physical receipts vs readiness assertions

Date: 2026-09-25. Base reviewed: `aaf561cfdc60ffe29c4d79094c16ce5e524f7d2d`. This is **read-only review code**, not a retroactive change to PR #121 or physical execution on an external drive.

## Confirmed discrepancy (six stale fields across four studies)

The committed `evidence/CURATOR_ASSERTION_REGISTRY_V2.json` was authored before the physical results subsequently committed **in the same PR**. It still reports:

| Study | V2 registry claim | Later receipt establishes (strict scope) |
|---|---|---|
| GSE301119 | `PENDING_P0_3` | All-gene two-language **implementation** reproduction across both modalities. The R producer, Python reproducer and estimator specification were authored by one lane; a genuinely independent estimand review remains open. |
| GSE254205 | `NOT_DONE` | Nine-sample bulk comparison is implementation-reproduced for 108,351 rows **to six-decimal stored precision only**. The predeclared full-precision 1e-9 acceptance criterion was not testable against rounded CSV. Other three assays remain reserved. |
| GSE178317 | `NOT_DONE` | All 39 engagement values independently recomputed to **stored precision**, but neither a new biological preparation nor an independent validation cohort was created. |
| GSE311359 | `STOP_PENDING_PHYSICAL_V2_REBUILD`, `BIN1_NOT_ESTIMABLE_UNTIL_ID_KEYED_REBUILD`, `PENDING_P1_7` | Physically executed ID-keyed V2 has zero phantom rows and distinct BIN1_enh_1 / BIN1_enh_2 / BIN1_enh_2_AS. The 2,434 non-BIN1 units reproduce exactly. Protospacer sequence, efficiency and cis causality remain unproven; no third-party biological replication is established. |

The `STUDY_SOURCE_INVENTORY_RECEIPT_V2.json` embeds the earlier registry. The `cross_study_v3/CROSS_STUDY_COMPARABILITY_RECEIPT_V2.json` pins its old SHA. **Do not edit V2 in place**: that would invalidate provenance and make historical receipts appear to describe a registry they never consumed. A historical snapshot may legitimately remain old, but a current machine-readable readiness view must be explicitly versioned and routed away from it.

## Executable negative gate introduced here

`scripts/audit_receipt_readiness_consistency_v1.py` opens **only committed metadata JSON**, verifies receipt-scope conditions and rejects claims that either lag or overstate the actual receipts. In addition to the four comparisons it asserts that GSE335887 remains `UNOPENED_RESERVED`, GSE175721 retains `STOP_AUTHOR_SOURCE_MISSING`, and GSE254205 bulk remains development-exposed.

`tests/test_pr121_receipt_readiness_consistency_v1.py` contains a mandatory positive fixture formed by applying only the six correct-status edits to a *copy* of the historical V2 assertions, plus adversarial altered-receipt, missing-evidence, false-independence, precision-overclaim and protected-exposure checks. Actual V2 is intentionally **known-red**. Green CI means the **detector works**, not that the original PR #121 status has been repaired.

## Required versioned follow-through before status promotion

1. Produce **V3** curator assertions with source paths and digests referring to exact physical receipts. Use `IMPLEMENTATION_REPRODUCED`, `IMPLEMENTATION_REPRODUCED_TO_STORED_PRECISION`, and `PASS_DEVELOPMENT_ETL_ID_KEYED` as scope-specific statuses, not `INDEPENDENT_REPRODUCED` or `ETL_COMPLETE`. Keep the old V2 and its dependent historical receipts byte-identical.
2. Re-run the cross-study metadata-only producer into a **new versioned** directory with V3 explicitly supplied; compare its computed columns against the prior V3 matrix to show no accidental numeric or exposure changes. Record both registry and metadata-contract hashes before reading and afterward.
3. Route **current** readiness consumers to V3 after independent review; leave historical V2 consumers labeled with their original creation time. Add the receipt checker as a mandatory upstream gate of any new current readiness report.
4. Have a different author derive GSE301119's scientific estimand from the biological question and raw experimental design *before* reading the existing mathematical specification. Only that distinct review can address S4. No additional self-authored implementation comparison closes it.
5. The still-unfinished work is independent GSE241858 and GSE240609 bulk recomputation, authenticated HGNC/Ensembl crosswalk, GSE175721 cell-to-guide source and GSE335887 ARID5B evidence. Keep all training, N1, D_shared, protected and therapeutic-ranking stops.

This review is **not** a request to re-run 221 million GSE178317 SRA spots, to regenerate completed historical T0/T1, or to reopen protected outcomes.
