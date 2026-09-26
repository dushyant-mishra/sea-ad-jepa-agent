# Lane D - verification receipt

`TRAINING=OFF · AUDIT_B_N1=UNOPENED · PROTECTED_FULL104_OUTCOMES=UNOPENED ·
D_SHARED_G5=UNOPENED · RARE_TAIL_MOLECULAR=UNOPENED · THERAPEUTIC_RANKING=OFF`

This file records **what was actually verified, by whom, and how** - so that a
reader who was not present can tell which statements in this package rest on a
check I ran and which rest on a record I read.

Lane D was interrupted once by a session rate limit. Commit `f63eff5d` carries
the label `INCOMPLETE_INTERRUPTED` and is superseded. The content listed under
"verified in this session" below was checked after the resume and no longer
carries that label. Nothing else in this package is asserted as verified.

---

## 1. Verified in this session, by direct execution against primary sources

| Claim | How it was checked | Result |
|---|---|---|
| Five GSE174367 files authentic | SHA-256 of each file recomputed and compared to `stage72a_resource_inventory_v1.csv` and `stage38a_download_manifest_v1.csv` | 5/5 **AUTHENTICATED** |
| cisTarget databases authentic | SHA-1 of both 35 GB / 13.9 GB feathers recomputed and compared to the vendor `sha1sum.txt` files | 2/2 **AUTHENTICATED** |
| Historical inventory figures | matrix shapes read from the h5 files; microglial counts recomputed from the cell metadata | 10/10 reproduce exactly |
| Stage75F freeze intact | SHA-256, row count and column schema of all 7 source tables recomputed against the frozen manifest | 7/7 match; outputs 10 / 96 / 3 |
| Donor and sample overlap | recomputed from both cell-metadata files | 18 shared, 2 ATAC-only, 0 covariate mismatches |
| No cell-level RNA-ATAC pairing | barcode-set arithmetic plus GEM-suffix collision table | 190 vs 9,893 expected; 17/18 suffixes name different samples |
| Zero GSE174367 donors in FULL104 | `stage81a2_global_donor_registry.csv` queried for `study_id == GSE174367` | 0 of 385 persons |
| Gene overlap and collisions | recomputed against the 41,238-address registry, **exact unbounded tie enumeration** | 38,838 covered; 294 collisions |
| Peak coordinates, hg38 build | every peak parsed; containment against `hg38.chrom.sizes` | 0 out-of-bounds; `hg38_CONSISTENT` |
| Peak-to-gene over all 219,070 peaks | re-derived from GENCODE v44 | counts in the main report |
| Stage75C frozen table reproduces | replayed and compared row by row | 219,070/219,070 distance; 219,070/219,070 gene among tied-nearest |
| Independent implementation agrees | brute-force reimplementation on a 1,500-peak sample | 1,500/1,500 exact |
| Mapping is position-sensitive | controlled +50 kb shift on 20,000 peaks | 99.99% distances moved, 63.8% genes reassigned |
| cisTarget mapping counts | recomputed from the coverage and mapping tables and the per-batch unmapped files | 86/91 mapped, 5 never mapped, 0 exact |
| **ATAC counts unused by Stage75F** | see section 2 | **confirmed** |
| **Stage73 / Stage73R figures** | see section 3 | **confirmed** |

## 2. The independence claim, verified directly

This is the load-bearing claim of the lane, so it was checked against the code
rather than taken from a summary.

Searched all seven Stage75F analysis scripts
(`stage75f_run_primary_motif_pilot.py`, `stage75f_run_secondary_motif_pilot.py`,
`stage75f_assemble_primary_tf_region_gene_evidence.py`,
`stage75f_assemble_secondary_tf_region_gene_evidence.py`,
`stage75f_audit_cistarget_region_mapping.py`,
`stage75f_integrate_regulatory_evidence.py`,
`stage75f_prepare_out_of_core_batches.py`) for any read of the accessibility
counts - `csc.h5`, `mg_snatac`, `accessibility`, or the `matrix["data"]` array.

**Result: zero matches. No Stage75F script reads the ATAC counts.**

Two corroborating facts from the same code:

* `stage75f_prepare_out_of_core_batches.py` line 112 sets `bed["score"] = 0`
  before writing the batch BED files. The signal column is a hardcoded
  constant, so no accessibility value reaches the motif screen.
* `run_stage75c_peak_gene_preflight_annotation_v1.py` line 107 reads
  `handle["matrix"]["features"]["name"][:]` and nothing else. It takes the peak
  interval strings and never touches `data`, `indices` or `indptr`.

**Conclusion.** The microglial ATAC fragment matrix
(219,070 x 12,232, 17,891,090 stored nonzeros) is present on disk, carries no
RNA value, and has never entered any Stage75F statistic or any JEPA training
input. It is available as an independent outcome. This is the basis for the
`CONDITIONALLY INDEPENDENT` verdict.

## 3. The Stage73 figures, verified directly

These were first surfaced by a background search whose session was terminated.
Rather than relay them, each number was read from the primary table.

From `results/tables/stage73_graph_control_results_v1.csv` - three conditions
are bit-identical, which is the mode-label bug:

| condition | mean_score |
|---|---|
| `context_grn_aux` | 0.3236108129998988 |
| `gene_label_permuted_grn_aux` | 0.3236108129998988 |
| `target_shuffled_grn_aux` | 0.3236108129998988 |

From `results/tables/stage73_bootstrap_delta_ci_v1.csv`:
`context_grn_vs_target_shuffled` and `context_grn_vs_gene_label_permuted` both
have `mean_delta = 0.0` and CI `[0.0, 0.0]` over **1,000** iterations. A
zero-width interval is only possible if the control *is* the thing it controls.

From `results/tables/stage73r_graph_control_integrity_audit_v1.csv` after the
repair - the controls are now provably distinct:

| graph | diff_nnz vs context | fraction changed | adjacency corr | distinct |
|---|---:|---:|---:|---|
| `context_grn_aux` | 0 | 0.000 | 1.000 | False |
| `target_shuffled_grn_aux` | 1,196 | 0.462 | 0.489 | True |
| `gene_label_permuted_grn_aux` | 1,858 | 0.835 | 0.007 | True |
| `string_graph_aux` | 1,298 | 0.958 | -0.046 | True |

From `results/tables/stage73r_prediction_lock_decision_v1.csv`:

| quantity | value |
|---|---|
| `context_graph_mean` | 0.323611 |
| `no_graph_mean` | 0.311254 |
| `string_graph_mean` | 0.331809 |
| `target_shuffled_mean` | **0.332290** |
| `gene_label_permuted_mean` | 0.313402 |
| `beats_no_graph_mean` | True |
| `beats_string_mean` | **False** |
| `beats_target_shuffled_mean` | **False** |
| `bootstrap_vs_all_graph_controls_positive` | **False** |
| `context_graph_prediction_lock` | **False** |

**Confirmed: the context graph beat the no-graph baseline and lost to its own
target-shuffled control.** This is why the evaluation spec makes the structural
distinctness gate blocking rather than advisory.

## 4. Not verified, and labelled as such

| Statement | Status |
|---|---|
| GSE174367 donors are disjoint from FULL104 donors *as people* | **INFERRED, not proven.** De-identified IDs share no namespace across cohorts. Verified: zero GSE174367 rows in the donor registry, and different brain banks. Not verifiable from identifiers alone. |
| The peak coordinates are hg38 *per peak* | **NECESSARY CONDITION ONLY.** Containment against `hg38.chrom.sizes` passes, which rules out hg19/T2T at contig tails. No liftOver round-trip was run. `NOT_EXECUTED`. |
| GENCODE v44, hg38.chrom.sizes and the motif2tf table match their upstream releases | **NOT VERIFIABLE.** No vendor digest is published for these three files. Their SHA-256 values were established by this lane and become the local reference, which is a weaker guarantee than an upstream match. |
| Any biological result | **NOT_EXECUTED.** Five of six prerequisite gates are unsatisfied. |

## 5. Reproduction

```
python scripts/lane_d/lane_d_gse174367_benchmark_readiness_v1.py \
    --repo-root "<repo>" --out-dir "<out>"
python scripts/lane_d/lane_d_physical_asset_inventory_v1.py \
    --repo-root "<repo>" --out-dir "<out>" \
    --duplicate-search-roots "<repo>/data;<repo>/outputs"
python scripts/lane_d/lane_d_peak_coordinate_map_audit_v1.py \
    --repo-root "<repo>" --out-dir "<out>"
python scripts/lane_d/lane_d_peak_to_gene_full_universe_v1.py \
    --repo-root "<repo>" --out-dir "<out>"
python scripts/lane_d/lane_d_write_receipts_v1.py \
    --out-dir "<out>" --receipts-path "<repo>/results/lane_d/laneD_artifact_receipts_v1.csv"
```

The cisTarget SHA-1 verification is expensive (49 GB read) and was run
separately; its results are recorded in
`results/lane_d/laneD_physical_asset_inventory_v1.csv`. Every artifact is
listed by absolute path, byte size and SHA-256 in
`results/lane_d/laneD_artifact_receipts_v1.csv`.

Audit runtime: Python 3.9, numpy 1.24.2, pandas 1.5.3, h5py 3.2.1. This is
**not** the Stage75F execution runtime, which was the
`scenicplus:1.0a2-container.1` container under WSL2.
