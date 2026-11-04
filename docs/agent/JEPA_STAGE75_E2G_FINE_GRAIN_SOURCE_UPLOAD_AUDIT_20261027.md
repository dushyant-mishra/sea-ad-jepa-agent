# JEPA: uploaded Stage75 fine-grain peak/motif evidence × public E2G interval audit

Date: 2026-10-27  
Status: **PASS source-file custody and exploratory coordinate calculation; BLOCKED for validated regulatory claims**  
Scope: Read-only, source-separated, **no JEPA target/model selection, no real training, no Stage4**.

## What was physically available

The new Macha file `stage75_peak_gene_evidence_bundle_20261027.zip` was read in this session: 34,213 bytes, SHA-256 `af87f3936550bb28e4b8294d1009e932ea23fc4bab55e5c1e7ff54641f045a27`. Its four members match the supplied `SHA256SUMS.txt`:

| Uploaded member | Rows | SHA-256 |
| --- | ---: | --- |
| `results/tables/stage75f_primary_tf_region_gene_evidence_v1.csv` | 53 | `b200c24aff1719e5d3cee28a5f674274bce2ef6fa624fd47de48b4a459333257` |
| `results/tables/stage75f_secondary_tf_region_gene_evidence_v1.csv` | 266 | `6699029b0c658c7ec6d49a1887e66c39bb824ca9cc0cf2d8586c1c8ae4ea6efe` |
| `results/tables/stage75f_candidate_peak_gene_links_v1.csv` | 91 | `6ea7328d18cd6c0ad3eea8690d1fc5220a99722fe094015fc2f88c6a2962adb8` |
| `results/reports/stage75c_peak_gene_preflight_annotation_report_v1.md` | document | `eea7af41a243b79f0087a36722be87e73f98c1bb6873bb2f67de97b0c52e3d33` |

The evidence rows cover 96 unique TF–gene pairs, exactly 27 target symbols and seven TFs; there are 149 distinct **TF–gene–query-peak** hypotheses, but only 56 distinct *physical Stage75 query peaks*. All 319 motif evidence rows agree on exact chrom/start/end and nearest-gene label with the supplied 91-peak candidate scaffold. No TF–gene pair or peak-scaffold record is silently dropped. The primary and secondary pair-level evidence aggregate (TF, gene, evidence row count, unique peak count and motif class) has FNV1a-32 fingerprint `d62d726a`, equal to the independently fetched GitHub-tracked frozen F5c/F7 summaries (24+72 rows). This fingerprint is a consistency diagnostic, **not** a cryptographic replacement for the SHA-256 input-file hashes.

All 319 detailed rows explicitly remain `region_gene_support_class=proximity_only_nearest_gene`, `tf_target_support_class=stage72b_candidate_coactivity`, `evidence_interpretation=candidate_tf_region_gene_evidence_not_validated_regulation` and `validated_regulation=false`. A `direct` motif class means **direct motif-annotation support in the cisTarget method**, *not direct TF occupancy or causal binding*.

The seven public E2G browser-track files are present locally and their bytes match the previously frozen SHA-256 manifests from the successful seven-source survey. These are public thresholded **prediction** files, not new biological or donor-level measurements. Their gene labels are symbols; they do not independently authenticate the Ensembl gene IDs. Historical `HLA-DPA1` and `HLA-DPB1` have separate legacy/current Ensembl addresses in an earlier local registry. No symbol-to-Ensembl collapse or causal claim is permissible.

## A qualified geometric comparison, not a source/build-validated conclusion

A fixed local protocol (`PROSPECTIVE_LOCAL_JOIN_PROTOCOL.md`, SHA-256 `f69c4498aeec4943082af3f461145fb6d7cb2f0d33b1abbebbd173375317fa92`) was saved **before** inspecting any Stage75–E2G overlaps. For every distinct TF–gene–peak hypothesis, it required an exact target-gene symbol and chromosome plus reciprocal enhancer-interval overlap. The primary descriptive cutoff is **0.50**, with 0.20 and 0.80 as threshold sensitivity checks. The 319 motif evidence rows are **not** treated as 319 independent peaks. Observations are 149 units × 7 source contexts = **1,043 TF–gene–peak × source** combinations.

**Genome-build uncertainty remains important.** The source pipeline configuration names hg38 chromosome sizes and GENCODE v44, and the E2G portal documents GRCh38; however, the upload does *not* contain independently authenticated genomic-build and zero-based half-open interval-convention attestations tracing both actual data origins. This is **conditional coordinate concordance** only. For any authoritative finding, verify the original ATAC source header/references and the external BEDPE track provenance, along with current molecular-address authority. Do not silently supply a build attestation merely because the coordinate overlap is plausible.

| E2G public reference context | 149 hypotheses with any same-gene bp overlap | Reciprocal ≥0.20 | Reciprocal ≥0.50 | Reciprocal ≥0.80 | TF–gene pairs with ≥0.50 |
| --- | ---: | ---: | ---: | ---: | ---: |
| ENCODE-rE2G inflammatory macrophage, treatment **unspecified** | 102 | 82 | **40** | 14 | 34 |
| ENCODE-rE2G macrophage, LPS-labelled 1h | 107 | 72 | **34** | 9 | 31 |
| ENCODE-rE2G macrophage, LPS-labelled 4h | 110 | 79 | **43** | 12 | 40 |
| scE2G Macrophages 3 | 115 | 76 | **36** | 8 | 35 |
| scE2G Macrophages 1 | 120 | 107 | **51** | 16 | 45 |
| ENCODE-rE2G broad brain | 55 | 39 | **3** | 0 | 3 |
| scE2G coronary-artery myeloid | 122 | 101 | **59** | 12 | 56 |

The broad-brain reference has fewer predicted links for this gene panel (17/27 symbols in its thresholded reference browser track), so its low concordance is **not** evidence that these genes are absent from brain or nonregulatory in brain. Model score scales and file-level thresholds are not comparable effects; the LPS labels do not establish a paired donor time course.

## Recurrence, genomic-unit collapse and distance-to-TSS

At reciprocal ≥0.50, across **all three** inflammatory-macrophage ENCODE-rE2G files **and at least one** selected scE2G macrophage file:

- **26 / 149** TF–gene–peak hypotheses recur. The 26 reuse only **12 distinct physical query peaks**, represent **23 distinct TF–gene hypotheses**, and cover **9 target-gene labels**. These counts are different scientific units and must not be interchanged.
- The nine labels are `AP1G1`, `C1QB`, `CTSB`, `FCER1G`, `HLA-DPB1`, `HLA-DRA`, `TREM2`, `TXNIP`, `TYROBP`. This is a **descriptive set of gene labels**, *not a ranked or selected gene panel.* `HLA-DPB1` remains source-address ambiguous; excluding it removes one recurring TF–gene–peak hypothesis.
- **8 / 26** have a `direct` motif-annotation class and **18 / 26** have `extended_only`. Neither class identifies experimental TF binding.
- **0 / 26** recurring hypotheses have Stage75's recorded nearest-gene distance ≥20 kb. Thus the strongest recurrence is **promoter/proximal-biased**, and does not demonstrate a shared distal regulatory enhancer–TF mechanism.
- Across *any* of seven reference contexts, **70 / 149** distinct TF–gene–peak hypotheses have ≥0.50 overlap; those 70 reuse **27 distinct physical peaks**. This broader number is less biologically specific than the macrophage cross-family criterion, and does not change authorization.

## Controls and limitations

1. **Source-spatial background (same coordinates, disregard gene identity):** 109–122 / 149 tested hypotheses overlap at least one E2G element from any target gene in most macrophage/myeloid tracks. Even same-gene bp-overlap rates are 102–122 / 149 there. This demonstrates a crowded predicted-element landscape around selected peaks. A zero-bp spatial overlap is not a biological negative either.
2. **Deterministic local peak translations (±20/50/100kb, same target-gene label, widths conserved):** yields 3–17 reciprocal-0.50 matches per 894 translated hypothesis trials across the seven sources, compared with 3–59 original hypothesis matches at ≥0.50. **This is a geometry sanity check, not a valid expression-, distance-, accessibility-, or donor-matched regulatory null.** Promoter-centered Stage75 input selection means shifting far away almost guarantees attenuation, so no p-values, effect sizes or biological specificity inference follows.
3. **Within the 91-peak Stage75 candidate scaffold:** 85 peaks belong to the 27-gene panel; 56 of those have a motif-support row, while 29 do not. At the three-macrophage-plus-one-scE2G geometric recurrence criterion, **12/56** of the motif-tagged peaks and **6/29** of the other proximity-candidate peaks recur. The groups differ markedly in median width (1,354.5 vs 430 bp) and recorded nearest-gene distance (2,635 vs 7,830 bp); this comparison is therefore **not evidence of TF-motif-specific enrichment.** No statistical test was performed.
4. The Stage75 cisTarget motif database used SCREEN regions, and the ENCODE regulatory predictions may reuse similar ENCODE/SCREEN candidate-element annotations; exact source lineage and overlap exposure still need an independent audit. Cross-model interval agreement cannot automatically be counted as independent biological confirmation.
5. The uploaded detailed evidence has source-native genomic peaks, but it does not provide exact-donor TF occupancy, a controlled perturbation, scE2G retraining on the SEA-AD multiome, donor-level replication, or reconciled source gene identities.

**Gate:** No target selection, no representation winner, no real training, no Stage4, no causal regulatory claim, no independent adult human microglia validation. The historical graph/architecture negative priors remain closed. No new biological evidence grade is assigned to the 96 TF–gene hypotheses. Everything in this report is a cross-reference *mechanics/compatibility* result, conditional on explicit build and identity attestation.

## Reproducible outputs

- `audit_uploaded_stage75_e2g.py` + `test_uploaded_stage75_e2g_audit.py`: hash-gated local join and eight fail-closed tests (8 PASS), together with 15 previous custody/reference tests (23 PASS).
- `stage75_e2g_7source_audit_receipt_v1.json`: byte hashes, exactly 96 TF–gene pairs, 149 unique TF–gene–peak hypotheses, 7 public source hashes and per-source report counters.
- `stage75_e2g_7source_summary_v1.csv`: compact 7-source aggregate.
- `stage75_96_pairs_x_7sources_aggregate_v1.csv`: 672 TF–gene–source descriptive rows.
- `stage75_149_tf_gene_peak_cross_source_recurrence_v1.csv`: collapsed genomic-unit cross-reference recurrence and motif/proximity labels.
- `stage75_e2g_7source_tf_gene_peak_diagnostic_v1.csv`: 1,043 TF–gene–peak × source units.
- `stage75_e2g_7source_r50_provisional_interval_matches_v1.csv`: 266 element-to-query-peak overlap rows; **do not treat as independent regulatory edges**.
- `stage75_candidate_peak_scaffold_control_recurrence_v1.csv` and related control output: unbalanced within-scaffold reference diagnostic.

The input ZIP remains read-only and is **not** published as a raw source in the GitHub review branch. Reviewer access to the local ZIP or Macha's original source custody remains necessary to independently validate its 319 original motif rows.