# External enhancer-to-gene compatibility audit — 2026-10-27

**Status:** `READ_ONLY_COMPATIBILITY_AUDIT__NO_E2G_PREDICTIONS_EVALUATED__NO_TARGET_OR_TRAINING_AUTHORITY`

## Scope and active custody

This is a separate **non-authorizing** regulatory-evidence audit, based on `main` at
`c2bd13e8389dd25dc61612ef2aea88dc53099029`. It is **not** a change to
Target Discovery Tasks 0–4, PR #313/#314, the Stage75 frozen evidence, the
post-TD tournament harness, or FULL104. No sample-level matrices or protected
pathology were opened, no RNA/ATAC model or classifier was trained, and no
new target/representation is selected.

Read the active Oct-17 V7 custody in draft PR #323:
`docs/agent/JEPA_SUCCESSOR_HANDOFF_V7_20261017.md`;
PR #322:
`docs/agent/JEPA_LANE_AUDIT_SNAPSHOT_V7_20261017.md`.
At inspection, the exact Task4 candidate was PR #427 @
`64535753acfab0993165b5666797808f20cd8743`; independent Macha
acceptance and real Windows recheck were absent. Do not use older Oct-13
handoff as current Task4 authority. This audit does **not** resolve that gate.

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

## Evidence actually verified (repository-level, not experimental execution)

The file
`results/v4/stage81a1b_existing_regulatory_evidence_integration.csv`
(blob `87117c485c25f9c7295a6ac4ba5ca48b45c844aa`) has:

- **96 unique TF→target-gene rows**, **7 TFs**, **27 unique target-gene
  symbols**, with **58 Tier A / 38 Tier B** historical entries.
- All **96** have `gse174367_atac_support =
  not_gene_mappable_from_processed_peak_matrix`.
- All **96** have `sea_ad_multiome_support =
  exact_barcode_linkage_available_edge_support_not_inferred`.
- All **96** have `direction_evidence_type =
  predicted_response_sign_from_coactivity`.
- All 96 `peak_to_gene_support` entries are explicitly **proximity-only**.
  They are **not** resolved TF-bound enhancer→gene interval relationships.

This is a **TF→gene hypothesis ledger**, not a validated
enhancer→gene atlas. Counting an E2G prediction for a target gene does **not**
validate that a particular Stage75 TF controls that gene. A TF-motif-on-peak
and peak-to-gene interval chain, with compatible identities/provenance,
would be required before even *regulatory support* could be discussed;
a model-predicted chain still is not causal perturbation evidence.

The June-2026 SEA-AD acquisition receipt
`results/v4/stage81a1b_acquisition_report.json` records 144,023 RNA multiome
nuclei, 138,118 ATAC multiome nuclei and 133,084 exact linked nuclei in MTG.
It records **zero fragment assets downloaded / eleven access-blocked** and a
processed peak matrix. Exact pairing establishes modality identity, not
enhancer–gene regulatory links. None of these counts implies a microglia-only
cell count, sufficient per-cluster fragments, or prospective validation.

## External methods assessed

| Method | Frozen source head inspected | Input/interface | Classification |
| --- | --- | --- | --- |
| scE2G | `EngreitzLab/scE2G@b76d2068d4a549ea4c193e071a913cc7a2291e09` | indexed per-cluster ATAC fragments; raw paired RNA counts for multiome arm; cell identities and annotations | **BLOCKED** for native SEA-AD execution: fragments not acquired |
| ENCODE-rE2G | `EngreitzLab/ENCODE_rE2G@d039062b7092de338ed10a77ea208b3d5b06e89c` | ABC/accessibility workflow or existing atlas predictions, relevant biosample | **REFERENCE CANDIDATE**, but adult-brain microglia context and atlas access not qualified |
| Original ENCODE-E2G | `karbalayghareh/ENCODE-E2G@7b4a65357c78bb8f9464b1e3fd91b7bc579e6d78` | CRISPRi enhancer-gene labels, feature tables and TSS; logistic regression, chromosome-held-out benchmark | **METHOD REVIEW**, not run |
| GraphReg | `karbalayghareh/GraphReg@f5cec7fc784c2f503c359f2c7da95a8353c38e5c` | sequence/epigenome, 3D contacts, CAGE and matched cell contexts | **METHOD REVIEW**, input eligibility not established; no root LICENSE file seen |

The ENCODE-rE2G current README identifies release `v1.0.0` as the model
version used in the 2026 paper, and says it is built atop ABC; the latest
`main` is not automatically identical to the published run.
Its pretrained scores/thresholds depend on the supplied assay/model; there
is no generic, lawful default for an adult microglial assay.

The original ENCODE-E2G source has explicit distance/contact/promoter/
enhancer feature ablations. This is useful for **controls and attribution**
even if no external model is run. Its model uses held-out chromosomes,
not donor/source-held-out adult microglia transport. The original GraphReg
provides enhancer/TF motif attribution against experimental CRISPRi
comparators, but its TensorFlow graph model and source-domain assumptions
are not justification to reopen our previously negative graph auxiliary.

The scE2G Nature Genetics paper (Aug 2026) studies single-cell ATAC and
multiome applications and indicates approximate minimum useful **per-cell-type**
evidence of >=100 cells, >=2 million ATAC fragments and >=1 million RNA UMIs.
A pooled MTG total cannot substitute for cluster-specific QC. scE2G was
trained on K562 CRISPR data and applied to additional cell types; this is
**transfer evidence**, not direct perturbational microglial validation.

Public sources:
- https://www.nature.com/articles/s41588-026-02695-8
- https://www.nature.com/articles/s41586-026-10781-4
- https://github.com/EngreitzLab/scE2G
- https://github.com/EngreitzLab/ENCODE_rE2G
- https://github.com/karbalayghareh/ENCODE-E2G
- https://github.com/karbalayghareh/GraphReg

## Runnable, non-authorizing interface implemented

`scripts/regulatory/e2g_external_evidence_gate_v1.py` reads the historical
Stage75 table *without modifying it* and writes a hash-bound JSON receipt.
Without E2G predictions it outputs
`NOT_RUN_NO_EXTERNAL_PREDICTIONS`. It fails closed if the 96 historical rows
drift, duplicates appear, proximity gets silently promoted into validation,
or a predicted coactivity direction is silently rewritten.

Example, after checking out the audit branch:

```bash
python scripts/regulatory/e2g_external_evidence_gate_v1.py \
  --stage75 results/v4/stage81a1b_existing_regulatory_evidence_integration.csv \
  --output /tmp/e2g_stage75_read_only_receipt.json
pytest -q tests/regulatory/test_e2g_external_evidence_gate_v1.py
```

A **future, separately authorized** data adapter may produce canonical
predictions with required columns:
`chrom,start,end,target_ensembl_id,score,genome_build,biosample,
source_dataset,model_family,model_version,exposure_class`.
An independent one-to-one symbol→unversioned-Ensembl map is required with
`target_gene,target_ensembl_id`. Native E2G exports must **not** simply be
renamed without validating their coordinate/build, score semantics,
normalization and metadata. The gate rejects invalid coordinates, mismatched
genome builds (defaults to GRCh38), unversioned-ID violations, ambiguous
maps, untracked assay/model identities and missing exposure classification.

Even after a permitted mapping, the output is only:
`ANNOTATION_ONLY__NO_TF_EDGE_CONFIRMATION`. It reports **distinct
target-gene coverage and TF→gene rows with annotated targets**, while
`tf_target_edge_validation_count` remains null, not zero. No chromosome
or held-donor biological-performance claims are produced by this gate.

## Honest blocker/feasibility register

| Question | What is established | Next legal/necessary action |
| --- | --- | --- |
| Can native scE2G run on MTG today? | No verified local fragment files; processed ATAC peak matrix only | Inspect controlled-access eligibility, then acquire and hash-bind authorized indexed fragments and check exact paired-cell/cluster QC |
| Can a published rE2G atlas be used immediately? | Model and atlas exist; adult-brain microglia relevance and specific distributed files unverified | Register exact publication release, inspect biosample catalogue, record context/donor/exposure, then parse predictions |
| Can historical 96 TF edges be called enhancer links? | No; only TF→gene with proximity annotations | Verify peak intervals, TF motif/binding, genome build and canonical gene IDs before joining |
| Should GraphReg be added as a JEPA graph objective? | No; no new independent graph-specific increment measured | Keep methodology/reference only, with randomized and distance-only controls if an authorized new estimand is defined |
| Is independent AD-microglia regulation/causality validated? | Not by the above assets | Require direct context-specific genetic/perturbation evidence and honest development-exposure accounting |

## Prospective controls for any later eligible comparison

Before looking at target outcomes: freeze model/reference release;
coordinate build, interval conventions and 1:1 gene IDs; same source-cell
context; all missingness and source overlap; permitted roles for
development-exposed versus protected datasets. Predeclare a matched
**distance-only** baseline, **ABC-only** baseline when lawful source inputs
exist, **matched randomized element→gene links**, interval/sample/cluster
stratification, and donor/study held-out checks where independent units
exist. Do **not** use old model-generated regulatory edges as clean external
ground truth; do not call an RNA/coactivity or E2G prediction causal.

Final classification:
`EXTERNAL_E2G_COMPATIBILITY_DOCUMENTED__DIRECT_SCORE_COMPARISON_NOT_ESTIMABLE__NO_TRAINING_AUTHORITY`.
Machine receipt:
`results/regulatory/external_e2g_compatibility_audit_v1_20261027.json`.
