# Audit handoff — physical ETL completion, 2026-09-24

Branch `physical/etl-completion-claude-20260924`, draft **PR #118**, base PR #77
`9a2a30e4` (verified ancestor). Reviewed PR #117, #86, #91, #92, #94 without
merging any.

**Section 3 is the intended entry point.** It lists where this work is most
likely wrong, including one requirement of the assignment I did not meet.

---

## 1. Commits and producer digests

```
b0b182fa  WP-F  cross-study comparability matrix
3ad4871b  WP-B  GSE335887 metadata-only identity contract
e440377d  WP-E  GSE311359 BIN1 feature identity resolved
ecb7e5d8  WP-D  bulk V2 executed (GSE254205, GSE240609, GSE241858)
a1887f96  WP-C  GSE301119 donor-aware transcriptome ETL
0be6b762  WP-A  physical inventory, 16 assets rehashed
```

```
physical_source_inventory_vnext.py               c65f631e73fe096c95d9972851c6b012e9d2768cd3715e8c2024f1a0884f5b42
build_gse301119_donor_aware_transcriptome_v1.R   ffca3d1b6e81eae1519808cbc57daf18bade9df8c394318de058a649c63dbc75
build_cross_study_comparability_matrix_v1.py     0bfc56893bfdbea3d2b77df625a4011fd867f467c0fb98cb2f2a856c5ebf068f
compare_gse178317_vs_crisprbrain_support_qualified_v3.py  452b9bf25d7a613a94f97992e2ec56bc5f987b81874eeee0c5c4ee0bfde06dc2
manifest_committed_outputs_v1.py                 a2c45c961a1840528fb364a0bca71849f9fadea64d147cd5e3f746db274d940f
```

Heavy outputs, referenced not committed:

```
CRISPRi_donor_aware_log2fc_matrix.rds   29,391,063 B  7f550f436333cf6159f54ff7b3221617952fcc13ac2b9d68c4cf572d53b39e43
CRISPRa_donor_aware_log2fc_matrix.rds   21,338,886 B  474202c0705a57bdc939ce483fe7612d9082fb57d80d94eefd8bd3d3c509ba93
GSE254205_drug_response_effects_v2.csv  18,499,094 B  ebbdff66af55104fdbb1ffca9f548916a353fcbeb5c1f2d12a098da908cf1f18
GSE241858_genotype_context_effects.csv  25,212,094 B  1b6916e5fc2f0190ccff096950e970bfadc88e117fa10cbbde3ed67a8efe1488
GSE240609_coculture_effects.csv         13,862,000 B  ebcc63ae10b57e14ba11fcf7bec237f4341aac69685388a182d9bebae74b3d8f
```

## 2. Claims and what backs each

| claim | evidence | independently checkable |
|---|---|---|
| 16 assets authentic, 4,450,940,052 B, 0 mismatches | rehashed from disk vs `.sha256` sidecars | yes — rerun the producer |
| GSE254205 V1→V2 changes no number | 108,351 rows both sides, `max\|delta\|=0.000e+00` on log2fc/se/n | yes — both CSVs on disk |
| GSE240609 identity freeze correct | 4 PR #94 digests recomputed from the tar | yes |
| GSE311359 BIN1 resolvable without authors | `features.tsv` col 1: `BIN1_enh_1/2/2_AS` | yes — one gunzip |
| only BIN1 affected | 381 guides, 381 distinct IDs, 1 shared name | yes |
| feature tables identical across 7 samples | one distinct signature | yes |
| ARID5B has no deposited guides | absent from both feature references | yes |
| GSE335887 library is 30×2+5 NTC | deposited feature reference | yes |
| WTC11 for all 8 GSMs | GEO sample records | yes |
| CRISPRi −1.0518 / CRISPRa +1.9731 | our donor-aware ETL | **producer not independently reproduced** |
| Day-8 × GSE301119 share 5 targets | recomputed from both libraries | yes |
| GSE301119 union 208 / intersection 204 | guide×donor metadata | yes |

---

## 3. Where this is most likely wrong — audit these first

### 3.1 An assignment requirement I did not meet

The brief required *"negative tests for same-size tampering, duplicate guides,
mismatched donors, bad joins, missing controls, gene collisions, zero-fill and
silent test skips"* and *"zero-skips CI plus actual heavy-data execution"*.

**No adversarial tests were written for any of the five new producers.** `tests/`
contains nothing for the inventory, the donor-aware R producer, the comparability
matrix or the support-qualified comparison. The only producer in this lane with
a proven negative-test suite is `manifest_committed_outputs_v1.py`, whose four
tamper modes were demonstrated in an earlier commit.

This is the largest gap in the work. The heavy execution happened; the
adversarial half did not. Treat every producer here as `CODE_UNTESTED` even where
its output is `PHYSICAL_DATA_VERIFIED`.

### 3.2 My own transcriptome-wide output was never independently reproduced

The brief asked for *"an independent reproduction"* for GSE301119. What I
reproduced was **PR #91's support census** — group counts, cell counts, the HEXA
limitation — before computing effects. Nobody reproduced the log2FC matrices.

The direction asymmetry (CRISPRi down, CRISPRa up) is suggestive but is **not**
proof of correctness: a sign error in the contrast would flip both together and
still look coherent. A second implementation should recompute at least a handful
of targets from the raw pseudobulk.

### 3.3 The cross-study 5-target result is not fully independent

Day-8 values come from our GSE178317 recovery; GSE301119 values come from our
donor-aware ETL. **Both sides of that comparison are our own pipeline.** If the
pipeline has a systematic sign or normalisation defect, it would agree with
itself. The consistency is evidence about the ETL, not about biology, and is
labelled that way — but a reviewer should not read it as cross-validation.

### 3.4 Bulk V2 outputs were executed, not reproduced

GSE254205, GSE240609 and GSE241858 ran through the parallel lanes' V2 producers.
I verified their **inputs** (digests, design completeness) and, for GSE254205,
proved V1/V2 parity. I did not independently reimplement their effect
computation. The parity proof covers "V2 did not change V1", not "V1 was right".

### 3.5 Descriptive columns in the comparability matrix are assertions

The shared-target *counts* are recomputed from source. The `intervention`,
`cell_model`, `protocol_and_time`, `biological_units`, `controls` and
`limitation` columns are hand-authored from the record. They carry no digest and
should be read as my summary, not as derived data.

### 3.6 Known-weak items carried forward

* GSE335887 **10x chemistry unresolved** — series prose says v2; kb-python
  processing leaves no chemistry field to corroborate. Not guessed.
* **13 of 180 panel antibodies** absent from the previously reported shared 167;
  unexplained.
* GSE301119 **two donors**; no population claim is licensed.
* `FCGR2C` is targeted but structurally unmeasured in both GSE301119 modalities.
* GSE311359's other 82 targets are confirmed unaffected by the BIN1 defect but
  still inherit name-keyed aggregation and should be reproduced under ID keying.

---

## 4. Exposure

No reserved outcome opened. GSE335887 response profiles remain
`UNOPENED_RESERVED`; **no HDF5 file was downloaded**, so the required key-access
log is correctly empty. The only CRISPRbrain access read the target-identity
column to compare target sets — no `Log2FC`, `P Value` or `FDR` displayed or
computed. That is narrower than the aggregate self-gene QC counts already
declared on 2026-09-24 and adds no new exposure.

## 5. Exact missing sources

* **GSE175721** — the depositor-described tab-separated per-cell cell-to-guide
  metadata. Re-searched today: PMC8776770's only data table (MOESM10) holds
  figure source data across 23 `Fig*` sheets and no assignment; the Data
  Availability statement reads *"available from the corresponding authors upon
  request"*. Contact: Bilal Cakir / In-Hyun Park, Yale.
* **GSE335887 ARID5B** — guide sequences from the publication's Table S2.
* **GSE311359** — none. Needs an ID-keyed rebuild, not an external file.

## 6. Not done

ID-keyed GSE311359 V2 rebuild; GSE254205 snRNA-seq / ATAC / LD-sort (all three
physically verified, none opened); independent differentiation-preparation
census for GSE335887; 10x chemistry resolution; adversarial test suites per 3.1;
independent reproduction per 3.2.

## 7. Status vocabulary used

`PASS_PHYSICAL_QC_ONLY` · `PASS_DEVELOPMENT_ETL` · `PASS_DEVELOPMENT_ETL_PARTIAL`
· `NOT_ESTIMABLE` · `STOP_AUTHOR_SOURCE_MISSING` · `STOP_PENDING_PHYSICAL_V2_REBUILD`
· `UNOPENED_RESERVED`

No study carries a blanket `ETL_COMPLETE`. `CODE_TEST_PASS`,
`PHYSICAL_DATA_VERIFIED`, `BIOLOGICAL_REPLICATION` and `PROSPECTIVE_CONFIRMATION`
are distinct: this lane reaches the second for most studies, the first for almost
none (see 3.1), and the third and fourth for none at all.

```
TRAINING=OFF · AUDIT_B_N1=UNOPENED · PROTECTED_FULL104_OUTCOMES=UNOPENED
D_SHARED_G5=UNOPENED · RARE_TAIL_MOLECULAR=UNOPENED · THERAPEUTIC_RANKING=OFF
```
