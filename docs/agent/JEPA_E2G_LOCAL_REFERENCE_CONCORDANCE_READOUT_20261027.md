# JEPA: public E2G reference-coordinate concordance — local readout

**Date:** 2026-10-27  
**Status:** `EXTERNAL_PUBLIC_REFERENCE_ONLY__NO_STAGE75_INTERVAL_JOIN__NO_REGULATORY_OR_TRAINING_AUTHORITY`

## Assets actually read

Seven full, publicly served BEDPE/browser-track files recovered through the public Enhancer2Gene GraphQL portal, transferred by hash-verified GitHub Action run `40530121781`, downloaded as a temporary Actions artifact, and independently SHA-256 verified in this runtime against the earlier fixed-source survey. No request to the requester-pays `gs://e2g` bulk bucket, no GCS billing credentials, no private source-level assays or donor-level data.

Fixed group of seven: ENCODE-rE2G inflammatory macrophage with **treatment condition unspecified**, ENCODE-rE2G inflammatory macrophage LPS-labelled 1h and 4h, scE2G Macrophages 3, scE2G Macrophages 1, ENCODE-rE2G broad-brain sample, and scE2G coronary-myeloid sample. They are **not** authenticated as biological replicates or a longitudinal time course. They do not include a verified adult-brain microglial reference. Chromosome coordinates are interpreted as the portal's reported human reference; a source-level genome-build harmonization has **not** been completed against Stage75.

## Prespecified exact-boundary diagnostic

The original reference comparison protocol was saved before calculating cross-source recurrence. It used an exact genomic enhancer interval + exact target symbol + reported TSS as a recurrence key. Of **190** predicted links for the 27 frozen Stage75 target symbols in the treatment-unqualified macrophage reference, **one** had identical interval boundaries in all three rE2G macrophage files, and this one was promoter-proximal (NPC2). This does **not** imply that only one shared regulatory element exists: independently called peak boundaries can shift, making exact-coordinate equality an overstrict standard.

A baseline-matched set of 27 nonpanel genes had **two** exact shared intervals. This indicates the exact-match statistic is not biologically discriminatory here.

## Explicitly posthoc, geometry-tolerant sensitivity analysis

After observing that exact-boundary issue, a separate **posthoc method sensitivity test** used reciprocal genomic overlap ≥0.50, and a stricter ≥0.80 check, requiring **all three pairwise elements** to satisfy the cutoff and match target symbol/chromosome/TSS. This is a reference annotation comparison; it cannot estimate a treatment effect or establish causality.

| Group | Reference source links | Three-context recurring links, 50% | Fraction, 50% | Recurring links, 80% | Fraction, 80% |
|---|---:|---:|---:|---:|---:|
| 27 historical Stage75 gene symbols | 190 | 126 | 66.3% | 111 | 58.4% |
| 27 same-chromosome, same baseline-link-count nonpanel controls (first matching rule) | 190 | 110 | 57.9% | 89 | 46.8% |
| 27 nonpanel controls using sensitivity matching weighted toward both link count and distal fraction | 185 | 109 | 58.9% | 91 | 49.2% |

The initial controls were not perfectly matched for distal burden in **CTSB** and **IRF8**, so a second matching variant was reported transparently. All controls were selected based only on the first **treatment-unqualified** reference and chromosome, with a ≥1 Mb TSS separation, **without consulting the other two files' recurrence outcomes**. These controls are not independent donors and cannot justify a p-value, an effect claim, or target re-ranking.

The historic panel had 59 geometrically distal (≥20 kb enhancer midpoint→TSS) links in the first source; **30/59 (50.8%)** recurred at ≥50% overlap. The panel's proximal links recurred **96/131 (73.3%)**. Matched controls by initial count alone had distal recurrence **33/78 (42.3%)** and proximal recurrence **77/112 (68.8%)**, but the distal burdens differ, hence these fractions are not controlled comparisons of biology.

## Cross-method overlap is substantial, but is not independent biological confirmation

Among the panel's **126** geometrically recurring rE2G macrophage links, **91 (72.2%)** overlap an enhancer with the same target symbol in **at least one** selected scE2G macrophage reference (reciprocal overlap ≥0.50). **21/30** of the recurring ≥20kb elements have such a cross-model overlap. By contrast, the initial link-count-matched nonpanel control has **55/110 (50.0%)** cross-model overlapping elements, and the alternate distal-balanced controls have **61/109 (56.0%)**. A selected broad-brain rE2G reference overlaps **26/126** panel recurring links; the coronary-myeloid scE2G reference overlaps **92/126**. These numbers reflect different reference cell contexts and thresholded models and should never be interpreted as validated microglial regulation or disease effects.

The public browser tracks **only supply gene symbols**, not canonical Ensembl identities. Historical HLA-DPA1 and HLA-DPB1 legacy-address collisions remain unresolved for authoritative external joins. Reported TSS positions for all 27 panel symbols were consistent across available E2G references, but that coordinate consistency **does not establish Ensembl-ID identity**.

## Files retained

- `e2g_local_reference_concordance_v1.py`: exact-boundary diagnostic, frozen SHA validation, control matching and outputs.
- `e2g_local_geometry_sensitivity_v1.py`: posthoc overlap sensitivity and 126-element coordinate catalogue.
- `e2g_control_balance_sensitivity_v1.py`: alternate matching diagnostics.
- `e2g_cross_method_control_audit_v1.py`: cross-model control comparison.
- `test_e2g_local_concordance_v1.py`: nine offline hostile tests, **9 passed**.
- `e2g_reference_concordance_20261027/`: gene-level summaries, matched controls, 126-element coordinate catalogue, exact-key catalogue, source-hash-bound receipts and sensitivity readouts.
- `verified-seven-public-e2g-tracks.zip`: **public**, SHA-verified source files, not to be committed into the GitHub repository.

## Hold/next gate

For the future Macha Stage75 interval join, **do not filter only to the 21 cross-model distal elements or treat them as selected targets**. Bring forward all 126 recurrent intervals and ideally the complete 27-gene, seven-source prediction space and matched negative controls. Require true genome-build and 0-based half-open attestation, **canonical unversioned Ensembl identities**, Stage75 fine-grained TF-motif-hit/peak tuples, and the original modality/sample provenance. Use robust, source-independent controls before any biological or regulatory inference.

**Cannot presently claim:** independent microglial enhancer validation; target gene causality; TF→gene causal edges; longitudinal/LPS-response effects; AD pathology progression; any chosen JEPA target, architecture or real training authority.

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`