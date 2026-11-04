# Posthoc Stage75 × E2G source-TSS and geometry positivity audit (2026-10-27)

**Authority:** `SOURCE_COMPATIBILITY_ONLY__POSTHOC_NON_DECIDING__NO_REGULATORY_VALIDATION__NO_TRAINING`

The previous source-hash-bounded Stage75 fine-grain upload and seven public E2G BEDPE comparisons remain unmodified. A new local diagnostic was developed **after** the prior recurrence analysis and a PRDX1 TSS anomaly were known. It is not a preregistered biological hypothesis test.

## Stage75C distance semantics: corrected

Independent inspection of the tracked source `scripts/run_stage75c_peak_gene_preflight_annotation_v1.py`, function `annotate_peaks`, proves that Stage75 `abs_distance_to_tss` is **absolute distance from the integer peak midpoint to the nearest GENCODE v44 gene-level TSS**. It was not the minimum interval-edge-to-TSS distance. The previous exploratory PRDX1 20,545-bp discrepancy used an inappropriate edge-versus-midpoint comparison and is superseded.

The matched E2G BEDPE source reports a source-specific target TSS. The correct comparable diagnostic is `abs( floor((peak_start + peak_end)/2) - source_e2g_tss )`. Across the original 266 TF×reference-element matches, collapse repeated TF labels and predicted intervals before reporting annotation provenance. There are **106 unique gene+physical peak+external source+TSS units**, representing **27 distinct physical gene+peak combinations**.

| Absolute disagreement, midpoint-based | Unique source–gene–peak–TSS units |
|---|---:|
| ≤500 bp | 90 |
| 501–2,000 bp | 13 |
| >2,000 bp | 3 |

The three >2kb mismatches are **one PRDX1 physical peak** (`chr1:45543742-45544241`) seen in three different external reference sources (rE2G LPS 1h, LPS 4h; scE2G coronary-myeloid). The Stage75 gene-level TSS distance is **1,259 bp**; external PRDX1 TSS `chr1:45521938` is **22,053 bp from the peak midpoint**, giving **20,794 bp** disagreement. The cause is **not established**; different gene/transcript annotation conventions are a possibility, not an adjudication of correct identity.

In an explicitly **posthoc source-distance sensitivity** deleting source-gene-peak matches with >2kb disagreement, the original 149-hypothesis source r50 counts change only for LPS-1h **34→31**, LPS-4h **43→40** and coronary-myeloid **59→56**. The strict three-rE2G-macrophage plus one scE2G-macrophage recurrence remains **26/149**, because those PRDX1 source matches were not in the strict recurring set. Do not treat a 2kb threshold as a new prospective pass/fail criterion.

## Why the apparent motif overlap has weak geometric comparability

The wider Stage75 historical 27-gene candidate scaffold contains **85 physical peaks**: 56 with a selected motif leading-edge hit and 29 with no such Stage75 motif hit. Prior raw recurrence was **12/56** versus **6/29**, but the motif-hit peaks were broader (median **1,354.5 vs 430 bp**) and closer to their assigned TSS (median **2,635 vs 7,830 bp**).

The follow-on posthoc protocol was recorded **before** computing the matched outcome. It specifies exact-gene one-to-one optimal caliper matching *without replacement*: peak-width ratio ≤2 and `(midpoint-to-TSS distance+1kb)` ratio ≤2; choose minimum total absolute log2 ratio deviation and maximize qualifying pair count. Outcome values must not enter matching.

**Only 9 eligible motif/nonmotif peak pairs across 7 genes** meet those requirements. Of these, **4/9 motif-hit peaks and 2/9 other peaks** meet strict cross-macrophage-source recurrence; the two discordant motif-only matches are **TREM2** and **TXNIP**, whereas both sides of two CTSB pairs recur. Seven distinct genes and nine nonindependent pairs do **not** provide inferential power or biological null calibration. No p-values, enrichment call, TF ranking, or claim of validated specificity.

**Critical structural test:** 37 of the 56 physical motif-hit peaks are reused by multiple historical TF labels. Across the source table, all seven E2G overlap indicators are *exactly identical* for any same-gene/same-physical-peak records with different TF labels. Thus **a gene+interval match cannot independently discriminate TF identity**. The previous 149 TF-gene-peak hypotheses or 26 recurrent annotations are *not* independent TF regulation measurements.

## Durable results and reproducibility

- `docs/agent/JEPA_E2G_POSTHOC_TSS_GEOMETRY_DIAGNOSTIC_PROTOCOL_20261027.md`: explicitly posthoc protocol and limitations.
- `results/regulatory/e2g_stage75_tss_106_unique_source_peak_comparisons_v1_20261027.csv`: full deduplicated 106-row midpoint source comparison.
- `results/regulatory/e2g_stage75_9_within_gene_geometry_matched_peaks_v1_20261027.csv`: nine caliper-qualified outcome-blind pairs and geometry.
- `results/regulatory/stage75_e2g_r50_266_source_element_matches_v1_20261027.csv`: the preexisting 266 matches in GitHub-normalized LF text.
- `results/regulatory/stage75_e2g_85_scaffold_peak_recurrence_controls_v1_20261027.csv`: preexisting 85 physical-peak geometry and source outcomes in GitHub-normalized LF text.
- The existing `results/regulatory/stage75_e2g_149_peak_7context_recurrence_v1_20261027.csv`: previous 149 hypotheses, same LF normalization.
- The 21,817-byte chat-local download bundle `JEPA_STAGE75_E2G_TSS_GEOMETRY_FOLLOWON_20261027.zip` (SHA-256 `91695b9e34422295625f7f8593fdff62f51bdcb3a719b4d1f41772d4e134936e`) contains the full original-source-hash-verified local Python analysis, the GitHub-normalized variant, 10 passing adversarial local tests, protocol, results and receipt. **The package is held in the originating chat, not a claimed GitHub-hosted zip.**

### Hard scientific boundary

All original observations remain geometrical agreement among *predicted*, often promoter-proximal regulatory annotations. They are not TF occupancy, measured enhancer action, independent adult human microglia replication, a donor time series, or a causal regulatory effect. Source-specific genome build/interval convention, exact external Ensembl identities (notably HLA legacy ambiguity), and shared ENCODE/SCREEN exposure remain unresolved. Original graph negative priors stay negative. No target/representation winner, Stage4, or real training is authorized. Draft PR remains unmerged.
