# Scientific correction: published CRISPRbrain DE row ≠ assayed raw RNA gene

Date: 2026-09-24 ET. Addendum; **does not rewrite original historical receipts**. Original source and outcome-exposure identities unchanged. Executed and adversarially tested in [CI 36090091644](https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions/runs/36090091644), on the two SHA-verified, otherwise reserved 31-target profile tables; downloadable artifact ID `10844904133`. Only `Gene` and `name` labels were accessed for this new check; numeric Log2FC/FDR/effect columns were neither used nor reported.

The older metadata receipts and prose sometimes say “13,489 shared measured genes” or `per_target_assay_label_present`, but the evidence they actually establish is **13,489 gene labels that appear somewhere in each published differential-expression table**. That is *not* proof the raw assay measured the gene in each target group, that an absent DE row corresponds to undetected raw RNA, or that missing DE rows equal zero effects. The 2026-09-24 V1 `CRISPRbrain` metadata record remains useful as a published-table identity census; this addendum narrows its interpretation without silently changing older immutable hashes.

## Real source-bound per-target published DE row census

| Released table | Target–gene DE rows | Unique screenwide gene labels | Target self-gene DE rows |
|---|---:|---:|---:|
| WTC11 TF-induced iTF-MG Day 12 | 505,527 | 16,398 | 30 of 31 |
| WTC11 cytokine-induced iMG Day 28 | 417,630 | 13,936 | 29 of 31 |

Exactly **31 shared target identities** and **13,489 labels appear somewhere in both published tables**. For each individual matched perturbation, only **12,944–13,407** genes have a released DE row in **both** screens (median **13,090**). Across the official July-2026 HGNC approved-primary subset, shared per-target released-row counts range **12,831–13,291** (median **12,977**). These values are measured metadata counts from the executed script, **not prediction scores or biological effect sizes**.

The joint absence of a published POU5F1 own-gene DE row from both screens, and SMAD3 own row from the iMG screen, cannot be interpreted as failed targeting or raw-gene structural absence: first verify original GEX `var` feature/capture identities, raw nonzero counts, provider row filtering, minimum-count rules and guide group metadata **without reading reserved numerical response profiles**. This reconciles the previously identified **116 unresolved HGNC labels** as *identifier mapping* gaps, separate from within-target published-row sparsity. Missing-identity and missing-row axes must not be conflated.

The new source-bound script is `scripts/gse335887_target_row_coverage_v1.py`, with synthetic negative tests and physical CI. Its per-target output includes set hashes and exact `both_primary_HGNC_published_de_rows`; it records `raw_assay_gene_detection_NOT_VERIFIED=true`. **Do not use published DE row presence as the observation mask for raw-count models**, and do not select confirmation features by looking at their reserved response values.

Next legitimate step on Claude's physical drive: metadata-only inspection of original GSE335887 `h5ad/h5mu` GEX feature identities and sample/guide manifests; generate separate `RAW_ASSAYED`, `RAW_DETECTED` and `PUBLISHED_DE_ROW` masks plus provenance without opening effect or FDR columns. Recheck exact WTC11 differentiation-batch labels and the unresolved 10x chemistry. Reserve the previously unopened transcriptome effects for a separately frozen, narrowly scoped protocol/stage experiment.

**Terminal:** `PUBLISHED_ROW_METADATA_PHYSICALLY_VERIFIED__RAW_ASSAY_AND_REPLICATE_AUTHORITY_STILL_OPEN`; no new predictor, training or therapeutic conclusion.
