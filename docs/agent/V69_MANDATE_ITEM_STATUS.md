# V69 mandate items 1–17 — status, artifact, and what is missing

One row per item of the owner mandate. `DONE` means an artifact exists and is
authenticated. `PARTIAL` means something real exists but the item is not satisfied.
`NOT STARTED` means exactly that. Nothing here is marked done on the strength of a
plan.

Branch `claude/v69-scenicplus-external-network-20261001`.

---

| # | Item | Status | Evidence / what is missing |
|---|---|---|---|
| 1 | Acquire the complete substrate, SHA-pinned | **DONE** | Metadata, filtered matrix, motif collection, HGNC motif2TF, hg38 analysis-set FASTA and cbust all byte-complete against server-declared `Content-Length` with SHA-256. Matrix dimensions, feature types, RNA/peak counts and genome build recorded from the file, not from its name. Fragments **complete**: 63,641,120,882 bytes local == declared, sha256 `b7c5aa2d39fb1a3c6e5c9cf06dc83cdcf2c5bb3239151c4276a73f675cb71e8f`, status `PASS__BYTE_COMPLETE_AND_DIGESTED`. |
| 2 | Microglial development cohort from ACTUAL metadata fields | **DONE** | `V69_GSE214979_COHORT_FREEZE_V1`. Fields audited not assumed; donor column `id`, annotation `predicted.id` agreeing exactly with `subs`. ALL_MICROGLIA 3,179/15 donors; DEV_NO_MORABITO_OVERLAP 2,534/12. Exclusion set verified to equal exactly the UCI-repository donors; individual overlap with Morabito explicitly **UNVERIFIED**. Pathology blindness proven by a value-flip positive control. |
| 3 | Two independent network routes | **PARTIAL** | Route-A substrate and 150,561-region universe built; Route-A cisTopic input built in-container. Route-B QC **executed to completion** over the full 63.6 GB file — 5,831,261,753 records scanned, 23,522,438 cohort records, 2,342 of 2,534 cells passing, **12 of 12 donors** passing against a minimum of 8 (`receipts/V69_ROUTEB_FRAGMENT_QC_V1.json`). No consensus peaks, no Route-B region universe yet. **No network on either route.** |
| 4 | Custom cisTarget database, official v10 resources | **PARTIAL** | Official v10nr_clust_public (10,249 motifs) and HGNC motif2TF acquired and SHA-pinned; Stage75F resources explicitly **not** used as authority. Builder written, runs end-to-end in-container, region FASTA reconciles exactly (150,561 = 150,561). Benchmarks run to **measure** cost. **The full database is not built.** |
| 5 | Build broad networks | **NOT STARTED** | No eRegulons exist. TF scope is frozen broad; the Stage75F ten carry no privileged status. |
| 6 | Donor stability | **NOT STARTED** | Procedure and thresholds frozen in advance. See self-audit S14: nuclei per donor range 17 to 415, so leave-one-donor-out is not a uniform perturbation — flagged before any stability number exists. |
| 7 | Route-A vs Route-B robustness | **NOT STARTED** (rule frozen) | `ROUTE_STABLE` defined prospectively: same TF in both routes, target-gene Jaccard ≥ 0.30, and program-level donor stability in both. 50% reciprocal region overlap, not exact boundaries. Averaging the routes is forbidden. |
| 8 | Required negative controls | **PARTIAL** | All seven (C1–C7) defined and frozen before any result. **C1's denominator is built**: 1,605 TFs, direct supply 0–144, 110 TFs with zero direct motifs. C2–C7 are not computed. C7 (route-sensitivity positive control) is mandatory precisely so the agreement test *can* fail. |
| 9 | Freeze before Stage 4 | **NOT STARTED** | There is no network to freeze. No Stage-4 result has been inspected. |
| 10 | FULL104 structural crosswalk | **PARTIAL** | Address-resolution substrate built: 35,445/36,601 genes resolve to FULL104 addresses; source support SEA-AD 35,445, NPH52 30,436, HVS 17,947; 1,156 STRUCTURALLY_UNMEASURED. **Per-program reporting is impossible until programs exist**, and the receipt says so rather than letting global overlap stand in for it. |
| 11 | NIH-CARD Stage-4 structural crosswalk | **PARTIAL** | Vocabulary reconciled across all 8 shards (4,372 genes / 32,153 intervals / 37,419 pair keys). **Build resolved empirically as hg38**, 57/57 against the design artifact's hg38 columns and 0/57 against hg19, so no liftOver is needed. 4,370/4,372 Stage-4 genes present in GSE214979; 22,991/32,153 intervals (71.5%) reached by a peak. Structural only — no Stage-4 effect estimate read. Per-program reporting pending programs. |
| 12 | Other source adapters | **NOT STARTED** | Target interface (V69 schema + adapter plan) exists from the parallel lane. No adapter instantiated. |
| 13 | Preserve the Stage-4 hidden-confound result | **DONE (by non-action)** | Not modified, not tuned, not explained away. Recorded in the freeze as a boundary. |
| 14 | Do not pool outcomes | **DONE (by design)** | Freeze forbids averaging routes, pooling cells across cohorts, and single weighted evidence scores. No outcome exists to pool. |
| 15 | Required deliverables | **PARTIAL** | Acquisition, custody, metadata audit, microglia selection, donor exclusions, Route-A substrate, motif acquisition, environment manifest and CI-equivalent test receipts exist. Fragment QC, consensus peaks, both networks, stability, controls, comparison, frozen program table and the source eligibility maps do not. |
| 16 | Scientific fallback | **DONE (frozen in advance)** | Program/module level is a pre-declared success mode, not a failure. Selecting whichever route agrees with Stage 4 is forbidden. |
| 17 | Stop condition | **NOT REACHED** | See the end-state string in the lane status document. Honest status: substrate authenticated, networks not built. |

---

## Tests

50 tests across six files, all passing. Every fail-closed contract is exercised on
degenerate inputs, and each file contains at least one test proving the PASS path is
reachable — so no assertion in this lane is a check that cannot fail.

Specific failure modes proven reachable: truncated download, absent remote length,
remote object changed mid-run, permuted cell dictionary, duplicate barcodes, mixed
genome builds, RNA-only matrix, ambiguous published annotation, missing annotation
column (and a near-miss column name that must *not* satisfy it), vocabulary
disagreement across shards, and interval coverage counted from first-hit only.

## Governance

Stage-4 correspondence **UNOPENED** · Morabito **PROTECTED** · recoverability TEST
**SEALED** · training **OFF** · pathology labels **never used in construction** ·
Stage-4 hidden-confound result **unmodified**.
