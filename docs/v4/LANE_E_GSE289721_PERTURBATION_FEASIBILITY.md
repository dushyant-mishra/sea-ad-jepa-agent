# Lane E — GSE289721 independent reconnaissance and feasibility verdict

Status: RECONNAISSANCE COMPLETE — NOT PROMOTED TO BENCHMARK TRUTH
Date: 2026-09-26
Lane: E (independent perturbation-data agent)
Branch: `lane-e/gse289721-recon-20260926`
Worktree base: `origin/main` at `c49b13bd75c2d23716c777336db8fbfc78c09cd0`

TRAINING=OFF · AUDIT_B_N1=UNOPENED · PROTECTED_FULL104_OUTCOMES=UNOPENED ·
D_SHARED_G5=UNOPENED · RARE_TAIL_MOLECULAR=UNOPENED · THERAPEUTIC_RANKING=OFF

---

## 1. The verdict, in plain language

**This is the best-structured perturbation dataset the project has looked at so
far, and it is still not safe to call it ground truth yet.** Two specific things
have to be measured first, and both can be measured from files that are already
public — no email to the authors, no collaboration, no new experiment.

**Is this good news or bad news?** Cautiously good. The two defects that ruined
the previous candidates are *absent by construction* here:

- **GSE301119 died of a depth mismatch.** Roughly 50 cells per perturbed unit
  were compared against a pooled reference of roughly 1,425 cells — a 19.8x gap
  — and the effects then failed the dataset's own control-versus-control test.
  In GSE289721 the comparison is 3 guides against 6 control guides inside the
  *same* droplet run, so the control pool is about **2x** the size of a target
  pool, not 20x. That is a structurally different and much healthier design.
- **GSE335887 named a target (ARID5B) with no deposited guide.** Here the guide
  table is **complete**: every one of the 6 named targets has all 3 of its
  guides deposited with full 20-mer sequences, and all 6 control guides are
  deposited too. Nothing is missing.

**What still has to be checked before anything is scored.** Two open items, in
order of how much they could hurt:

1. **Only about 13% of cells carry a usable guide label.** The paper analyses
   5,872 "perturbed" cells out of 44,913 sequenced. The other ~87% failed the
   authors' guide-count cutoff. That is the dominant limit on statistical power,
   and the per-target breakdown of those 5,872 cells is **not stated anywhere in
   the deposit**. If one target landed at 150 cells, that target is not
   evaluable and must be dropped rather than scored as a disagreement.
2. **The deposit and the paper disagree about which cell line this is.** GEO
   says `cell line: IMR90` on all 8 samples; the paper says the CROP-seq used
   `FA10`. One of the two is wrong. Until that is resolved we do not actually
   know the genetic background of the cells we would be scoring against.

**What does this mean for the project?** GSE289721 can plausibly support a
*qualified, narrow* evaluation: does JEPA predict the right direction and shape
of transcriptional response when one of 6 specific genes is knocked down in
human iPSC-derived microglia, with and without an immune stimulus. It can
**never** support a claim about generalizing across people — there is one
genetic background and two differentiations in the entire dataset.

**What is still fine?** Everything the project already relies on is untouched.
This lane opened no protected outcome, ran no training, and computed nothing
over FULL104. Feature-space alignment is clean: all 6 target genes resolve to
exact, current Ensembl IDs that are already in the project's frozen address
registry and in the measured common-core set, so there is no identity ambiguity
to litigate later.

**One thing to be honest about up front:** a target being a *hit* in this paper
is not the same as that target being *engaged*. The paper reports **no
knockdown efficiency at all** — no qPCR, no on-target transcript reduction
from the single-cell data. Engagement is therefore unproven by the authors, but
— and this is the important part — it is **directly measurable by us** from the
deposited matrices, because the system is CRISPRi (dCas9-KRAB), which suppresses
transcription of the target's own mRNA, and all 6 target genes are present as
rows in the deposited count matrix.

---

## 2. Classification against the audits index

Per the standing rule, the proposed work was classified before any heavy call.

| Item | Classification | Basis |
|---|---|---|
| GSE289721 accession facts | `OPEN` | String `GSE289721` appears nowhere in the repository. No prior record exists. |
| GSE178317 role | `ALREADY_AUDITED` | Registered in `docs/v4/STAGE81A2R_ALL_DOWNLOADED_DATASET_IDENTITY_AUDIT.md` line 16 as `primary_microglial_perturbation_training`; 16 matrices, 536,608 cells, 33,538 features. |
| GSE301119 role | `ALREADY_AUDITED` | Same audit, line 34: `myeloid_auxiliary_training`, 2 matrices, 55,763 cells. Recorded in `docs/v4/PRE_STAGE81A2_HARMONIZATION.md` as having unequal CRISPRa/CRISPRi feature universes. |
| Frozen address space | `ALREADY_AUDITED` | `results/v4/stage81a2r_foundation_molecular_address_registry_candidate.csv`, 41,238 addresses, frozen at commit `95d2cafe`. Cited, not recomputed. |

Only the GSE289721 reconnaissance was new computation.

---

## 3. Source-authenticated accession facts

Every field below was read from the primary record. Retrieval method: direct
HTTP to NCBI (the interactive GEO page is behind a captcha for automated
fetchers; the machine-readable `form=text` endpoint is not).

Primary record retrieved:
`https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE289721&targ=self&form=text&view=brief`
→ archived at `docs/v4/lane_e_gse289721_evidence/GSE289721_geo_series_record.txt`
(SHA-256 `598c1dc5a611d7f5a42322422a3bb6e73f05a012f5ac4459fb47556a2a291dfe`)

| Field | Value (verbatim from GEO) | Source |
|---|---|---|
| Accession | GSE289721 | `!Series_geo_accession` |
| Status | Public on Dec 31 2025 | `!Series_status` |
| Title | High throughput identification of genetic regulators of microglial inflammatory processes in Alzheimer's disease. | `!Series_title` |
| Submission date | Feb 15 2025 | `!Series_submission_date` |
| Last update | Jan 01 2026 | `!Series_last_update_date` |
| PubMed ID | 41340152 | `!Series_pubmed_id` |
| DOI | 10.1186/s12974-025-03562-9 | Journal of Neuroinflammation |
| PMCID | PMC12729107 | PMC |
| Contact | Andrew Sproul, Pathology and Cell Biology, Columbia University | `!Series_contact_*` |
| Contributors | Cardona CL, Wei L, Kim J, Angeles E, Singh G, Chen S, Patel R, Ifediora N, Canoll P, Teich AF, Hargus G, Chavez A, Sproul AA | `!Series_contributor` |
| Platform | GPL24676 — Illumina NovaSeq 6000, Homo sapiens (taxid 9606) | `!Series_platform_id` |
| Series type | Expression profiling by high throughput sequencing | `!Series_type` |
| BioProject | PRJNA1224254 | `!Series_relation` |
| Samples | GSM8797509 – GSM8797516 (8) | `!Series_sample_id` |

**Overall design (verbatim):** "Human iPS-derived microglia were infected with
sgRNA targeting hit of interest on day 21. Cells were treated with either
vehicle or poly(I:C) on day 35 for 2 hours and collected for single-cell
RNA-sequencing. CRISPR guide libraries were also generated for downstream
analysis."

**Summary (verbatim):** "We sought to assess at scale how AD GWAS hits influence
human microglial inflammatory responses. We conducted CRISPR inhibition screens
of 119 AD GWAS hits in parallel along with 52 control genes in human iPSC-derived
microglia, with reactive oxygen species produced in response to the viral mimic
poly(I:C) as a readout. Top hits that either decreased or increased ROS in
response to poly(I:C) when knocked down were then interrogated via perturb-seq."

### 3.1 BioProject discrepancy — FLAGGED

The paper's data availability statement cites **two different** archives:

- "All raw single-cell RNA sequencing data have been submitted to GEO accession
  # GSE289721" — this series, BioProject **PRJNA1224254**
- "raw sequencing data from our CRISPRi screening experiments have been
  deposited in the NCBI Sequence Read Archive (SRA) under BioProject accession
  number **PRJNA1152984**"

These are distinct BioProjects. **PRJNA1152984 is the 119-gene pooled ROS
screen and is NOT part of GSE289721.** Anyone reading "119 AD GWAS hits" in the
GEO summary and expecting 119 perturbations in this deposit will be wrong. The
deposit contains only the 6-target perturb-seq follow-up. This is the single
most likely way for another lane to misread this accession.

---

## 4. Assay structure and complete sample inventory

All 8 GSMs share: organism *Homo sapiens*; `cell type: microglia`;
`genotype: dCas9-KRAB-MeCEP2` (the deposit's spelling; MeCP2 is intended);
chemistry Chromium Next GEM Single Cell 3' v3.1 dual index; instrument
NovaSeq 6000; `!Sample_library_strategy = RNA-Seq`; alignment to GRCh38 with
`cellranger-7.1.0 count` using `feature_ref4.csv`.

| GSM | Library | Title | Treatment | Modality | Supp. files | SRX | BioSample |
|---|---|---|---|---|---|---|---|
| GSM8797509 | SS001 | scRNA-seq, iMGLs vehicle XP1, GEX | vehicle | GEX | barcodes/features/matrix | SRX27694969 | SAMN46855378 |
| GSM8797510 | SS001F | scRNA-seq, iMGLs vehicle XP1, GDO | vehicle | GDO | **NONE** | SRX27694970 | SAMN46855377 |
| GSM8797511 | SS002 | scRNA-seq, iMGLs polyIC XP1, GEX | poly(I:C) | GEX | barcodes/features/matrix | SRX27694971 | SAMN46855376 |
| GSM8797512 | SS002F | scRNA-seq, iMGLs polyIC XP1, GDO | poly(I:C) | GDO | **NONE** | SRX27694972 | SAMN46855375 |
| GSM8797513 | AS001 | scRNA-seq, iMGLs vehicle XP2, GEX | vehicle | GEX | barcodes/features/matrix | SRX27694973 | SAMN46855374 |
| GSM8797514 | AS001F | scRNA-seq, iMGLs vehicle XP2, GDO | vehicle | GDO | **NONE** | SRX27694974 | SAMN46855373 |
| GSM8797515 | AS002 | scRNA-seq, iMGLs polyIC XP2, GEX | poly(I:C) | GEX | barcodes/features/matrix | SRX27694975 | SAMN46855372 |
| GSM8797516 | AS002F | scRNA-seq, iMGLs polyIC XP2, GDO | poly(I:C) | GDO | **NONE** | SRX27694976 | SAMN46855371 |

**The 4 GDO samples deposit no supplementary files.** This is not a gap: the
guide counts are folded into the GEX sample's own feature-barcode matrix. The
deposit states it explicitly — "barcodes.tsv, features.tsv, and matrix.mtx
containing counts for mRNA GEX and guide counts GDO" — and it was verified
directly (§5).

### 4.1 Measured matrix dimensions (verified by download)

`features.tsv.gz` is **byte-identical in content across all 4 GEX libraries**
(decompressed MD5 `711d10ba076a7251693146325ac2aa47`; the four `.gz` SHA-256s
differ only because gzip headers embed per-file timestamps).

- Total feature rows: **36,673**
- `Gene Expression` rows: **36,601** (rows 1–36,601)
- `CRISPR Guide Capture` rows: **72** (rows 36,602–36,673)

| Library | Condition | CellRanger barcodes | matrix.mtx.gz |
|---|---|---|---|
| SS001 | vehicle XP1 | 12,752 | 171,080,282 B |
| SS002 | poly(I:C) XP1 | 13,450 | 160,413,551 B |
| AS001 | vehicle XP2 | 10,540 | 137,071,587 B |
| AS002 | poly(I:C) XP2 | 11,826 | 149,165,887 B |
| **Total** | | **48,568** | **617,731,307 B** |

All barcodes carry the `-1` suffix, i.e. each library is an independently
barcoded 10x lane. **There is no cell hashing and no genetic multiplexing**, so
cells cannot be demultiplexed to any sub-unit below the lane.

---

## 5. Biological replication — what is the independent experimental unit?

This is the question that sank GSE178317's four capture wells. The answer here:

**The independent experimental unit is the differentiation. n = 2. There is
exactly one genetic background.**

| Level | Count | Independent? |
|---|---|---|
| Genetic background / donor | **1** | n/a — no between-donor contrast exists |
| iPSC line | **1** (identity disputed, §5.1) | n/a |
| Differentiation ("CROP-seq experiment") | **2** — XP1, XP2 | **Yes.** Paper: "Two independent CROP-seq experiments were conducted." |
| 10x lane | 4 | No — 2 lanes per differentiation are a vehicle/stimulus split of one transduced pool |
| Cell | 48,568 barcodes | No — pseudoreplicates within a lane |

**The vehicle and poly(I:C) lanes within one XP are a split of a single
transduced culture**, not independent replicates of each other. That is the
correct design for a *paired* treatment contrast, and it is a genuine strength:
it means the stimulus effect is estimated within-prep. But it caps the effective
replication of the stimulus contrast at **2 pairs**.

The design's real strength is at the perturbation level: because this is a
pooled CROP-seq, the control cells sit in the **same droplet run, same
differentiation, same transduction, same sequencing lane** as the perturbed
cells. Guide-versus-control is therefore internally controlled and free of the
batch confound. This is exactly the property GSE301119 lacked.

### 5.1 UNRESOLVED — cell line identity contradiction

| Source | Claim |
|---|---|
| GEO, all 8 GSMs | `!Sample_source_name_ch1 = IMR90` and `!Sample_characteristics_ch1 = cell line: IMR90` |
| Paper (PMC12729107) | "FA10 hiPSCs were differentiated into iMGLs" for CROP-seq |

These cannot both describe the deposited cells. IMR90 is a fetal-lung-fibroblast
derived iPSC line; FA10 (FA0000010) is an unrelated commercial line. **The
genetic background of the deposited data is therefore NOT ESTABLISHED.** Sex,
age, ancestry and *APOE* genotype of the line are all
`NOT_STATED_IN_DEPOSIT`. Since *APOE* genotype materially conditions microglial
inflammatory phenotype, this is not a cosmetic metadata slip.

This is resolvable without the authors: the deposited GEX matrices support
genotype inference (X/Y-linked expression gives sex immediately; common-SNP
inference from the raw reads gives more). It should be resolved before scoring,
and recorded as a measured finding, not an assumption.

---

## 6. Guide library — complete, with one mislabel

Deposited file: `GSE289721_feature_ref4.csv.gz` (884 B, SHA-256
`4b0188608f15b7466b89436c3c7a0a79b7ace2cce4c92e90f043f29af8f24608`), archived
decompressed at `docs/v4/lane_e_gse289721_evidence/GSE289721_feature_ref4_asdeposited.csv`.

**72 rows = 24 unique guides x 3 pattern variants.** The triplication is a
CellRanger convention, not three separate guides: each protospacer is declared
three times with staggered capture patterns `(BC)GTTNAANNGCTAT`,
`(BC)GGTTNAANNGCTAT`, `(BC)GGGTTNAANNGCTAT`, and the `sequence` column is
identical across the triplet. **Any recovery must sum guide UMIs across the 3
rows sharing a `name` before calling an assignment.** Treating the 72 rows as 72
guides would silently split every guide's evidence three ways.

| Target | Guides deposited | Protospacers | Ensembl |
|---|---|---|---|
| AGFG2 | 3 (AGFG2-2, -3, -4) | all present, 20-mer | ENSG00000106351 |
| EED | 3 (EED-2, -4, -5) | all present, 20-mer | ENSG00000074266 |
| MS4A6A | 3 (MS4A6A-1, -3, -4) | all present, 20-mer | ENSG00000110077 |
| INPP5D | 3 (INPP5D-3, -4, -5) | all present, 20-mer | ENSG00000168918 |
| PVR | 3 (PVR-1, -2, -4) | all present, 20-mer | ENSG00000073008 |
| RABEP1 | 3 (RABEP1-3, -5, -6) | all present, 20-mer | ENSG00000029725 |
| NEG_CTRL-1…6 | 6 | all present, 20-mer | annotated `Non-Targeting` |

**Completeness: PASS.** 6/6 named targets have all 3 guides with actual
sequences. No repeat of the GSE335887 / ARID5B failure. Guide naming implies the
parent library had ≥6 guides per gene (numbers 1–6 appear) and 3 were selected
per gene for CROP-seq, consistent with the paper's "three distinct gRNAs per
gene, selected from our previous screen."

Note the guide numbering is non-contiguous (e.g. AGFG2 uses 2,3,4; MS4A6A uses
1,3,4). Which 3 of 6 were chosen, and on what criterion, is
`NOT_STATED_IN_DEPOSIT`. If selection was by screen performance, the guides are
a *winner's subset* and their apparent potency is upward-biased.

### 6.1 The negative controls are mislabelled — and this matters

The deposit annotates all 6 NEG_CTRL guides as
`target_gene_id = Non-Targeting`, `target_gene_name = Non-Targeting`.

**The paper says otherwise:** the negative controls are guides against "two
non-essential genes (*CABP5*, *SAGE1*) that are not expressed in iMGLs."

Six control guides, at the paper's stated three guides per gene, is exactly
3 x *CABP5* + 3 x *SAGE1*. So these are almost certainly **gene-targeting guides
that recruit dCas9-KRAB to two real genomic loci**, not scrambled non-targeting
sequences. The deposit's `Non-Targeting` annotation is therefore very likely
wrong, and **which of NEG_CTRL-1…6 belongs to which control gene is not
recoverable from the deposit** — the IDs carry no gene assignment.

Two consequences, one bad and one good:

- **Bad:** a KRAB domain parked at a real promoter can have local chromatin
  effects. This is a weaker negative control than a true scrambled guide, and it
  is not the control the deposit claims it is.
- **Good, and important:** 6 control guides in two groups of 3 means a
  **structurally matched control-versus-control test is available** — 3 guides
  vs 3 guides, exactly mirroring a 3-guide target vs 3-guide control test. This
  is a better-matched neutral control than GSE301119 ever had, and it is the
  backbone of the qualification protocol in §9.

Resolvable without the authors by aligning the 6 twenty-mers to GRCh38 and
checking whether they fall in the *CABP5* / *SAGE1* promoter regions;
Supplementary Table S2 of the paper should also carry the assignment.

---

## 7. Guide-to-cell assignment

**Direct capture, not an enrichment library.** `feature_type = CRISPR Guide
Capture` with a capture-sequence pattern, processed through
`cellranger count`'s feature-barcoding path. This is materially better than
GSE178317, where sgRNA assignment required a separate mapping and demux/z-score
workflow that GEO does not expose.

**Per-cell assignments are NOT deposited, but are fully recoverable.** No
`protospacer_calls_per_cell.csv` is present. What *is* present is better than a
partial table: the raw per-cell guide UMI counts sit in rows 36,602–36,673 of
each deposited `matrix.mtx`, and the paper states the assignment rule verbatim:

> "Non-targeted cells were defined as having less than 5 counts for all gRNA
> sequences. For all other cells, the perturbation was assigned based on the
> guide that had the highest number of counts for that cell."

So the authors' exact labels can be reproduced deterministically from public
files. **Recovery is a solved problem here.**

**But the rule itself is weak, and the weakness has a direction.** It is a
winner-take-all argmax with **no purity ratio and no multiplet exclusion**: a
cell with 6 UMIs of guide A and 5 of guide B is confidently called A. Cells
carrying two guides — unavoidable at any appreciable MOI — are silently assigned
to one of them. Misassignment mixes perturbed and unperturbed transcriptomes
within a label, which **attenuates every effect estimate toward zero**.

This matters for how a negative result is read: under this rule, "JEPA predicted
an effect and the data show none" is *not* evidence against JEPA until the
assignment quality is measured. That is the central low-power-versus-real-
disagreement confound for this dataset, and §10 specifies the diagnostic.

---

## 8. Per-target engagement — unproven by the authors, measurable by us

**The paper reports no knockdown efficiency.** No qPCR, no on-target transcript
reduction from the single-cell data, no percent-knockdown figure anywhere in the
CROP-seq section. By the project's standard — *a screen without demonstrable
engagement cannot be ground truth* — the dataset is **not qualified as
deposited**.

**But engagement is directly measurable here, and the conditions are favourable:**

1. **CRISPRi, not CRISPR-KO.** dCas9-KRAB-MeCP2 silences transcription at the
   TSS, so the target's own mRNA should fall. This is exactly what a 3' scRNA-seq
   count matrix measures. (Under CRISPR-KO an indel often leaves transcript
   abundance unchanged, which is what made engagement so hard to demonstrate in
   the CRISPRbrain pair — 1 of 31 shared targets.)
2. **All 6 target genes are present as rows in the deposited matrix** — verified
   directly in `features.tsv`:

   | Gene | Feature row | Ensembl (deposit) | In frozen registry | Address index | Measured set |
   |---|---|---|---|---|---|
   | INPP5D | 5,793 | ENSG00000168918 | `current_exact` | 12372 | HVS_COMMON |
   | AGFG2 | 13,978 | ENSG00000106351 | `current_exact` | 3285 | HVS_COMMON |
   | MS4A6A | 19,787 | ENSG00000110077 | `current_exact` | 3726 | HVS_COMMON |
   | EED | 20,399 | ENSG00000074266 | `current_exact` | 1251 | HVS_COMMON |
   | RABEP1 | 28,256 | ENSG00000029725 | `current_exact` | 478 | HVS_COMMON |
   | PVR | 32,230 | ENSG00000073008 | `current_exact` | 1211 | HVS_COMMON |

   Registry source: `results/v4/stage81a2r_foundation_molecular_address_registry_candidate.csv`
   (frozen at `95d2cafe`); support source:
   `results/v4/stage81a2r_foundation_molecular_address_measurement_support_candidate.csv.gz`,
   all six `measured_address=True`,
   `measurement_status=addressable_measured_zero_or_nonzero_at_runtime`.

   Every Ensembl ID in the deposited guide table matches the registry ID exactly.
   **Feature-space alignment carries no identity ambiguity.**

3. The 6 targets divide by screen direction: **high-ROS hits AGFG2, EED, MS4A6A**;
   **low-ROS hits INPP5D, PVR, RABEP1**. The directional split is itself a
   testable structure, not just a target list.

**The engagement risk that remains is detection, not design.** CRISPRi knockdown
is only visible in a target whose transcript is detected often enough per cell to
measure a decrease. INPP5D and MS4A6A are well-expressed in microglia and should
be straightforward. AGFG2, EED, PVR and RABEP1 are the ones at risk of being too
sparsely detected in 3' droplet data for a per-cell knockdown estimate. Per-gene
detection rate is measurable from the deposited matrix and is a **gate**, not a
footnote — see §9 Gate 2.

---

## 9. Prespecified qualification protocol

**Frozen before any model is scored, and before any effect is inspected.** The
thresholds below are committed in this document; if a gate fails, the response is
to stop or to drop the affected target — never to widen the tolerance.

Design requirements, stated prospectively:

- **Matched-reference design.** Every target effect is estimated **within a
  single library** (one differentiation x one treatment), comparing that target's
  3-guide cell pool against the 6-guide control pool **from the same library**.
  No pooling of control cells across libraries. No cross-library reference. This
  is what GSE301119 violated.
- **Unequal-group diagnostic.** Report, per target x library, the control:target
  cell-count ratio and the per-cell median UMI depth of both groups. Any effect
  estimator must be run on depth-matched groups (subsample the larger pool to the
  smaller, with common random numbers across conditions so target and control see
  the same draws).
- **Neutral control.** The control pool splits 3/3 (CABP5 guides vs SAGE1 guides,
  once §6.1 is resolved; otherwise a frozen, seed-derived 3/3 split of
  NEG_CTRL-1…6). This control-vs-control contrast is run through the **identical**
  pipeline as a real target contrast and **must come out near zero**.

### Gates, in order

**Gate 0 — provenance.** The 4 GEX matrices download with the SHA-256 recorded in
§11; feature files decompress to MD5 `711d10ba076a7251693146325ac2aa47`; barcode
counts equal 12,752 / 13,450 / 10,540 / 11,826.
*Fail ⇒ the deposit changed; stop and re-authenticate.*

**Gate 1 — assignment recovery.** Reproduce the authors' labels from the
deposited guide rows (sum the 3 pattern rows per guide; `<5` total guide UMIs ⇒
unassigned; else argmax). The recovered count of assigned cells must land within
±10% of the paper's 2,899 (vehicle) and 2,973 (poly(I:C)).
*Fail ⇒ the deposited matrices do not reproduce the published analysis; report
that and stop. Do not proceed with a self-invented assignment rule.*

**Gate 2 — engagement, per target.** For each of the 6 targets, in each library,
test whether cells assigned to that target's guides show **lower expression of
that target's own transcript** than same-library control cells, on depth-matched
groups.
- Qualifying threshold, frozen: **≥25% reduction in mean normalized target
  expression, one-sided p < 0.05, consistent in sign in both XP1 and XP2.**
- A target failing this is **DROPPED from scoring entirely.** It is not scored as
  a JEPA disagreement. An unengaged target carries no information about the model.
- Detection precondition: the target must be detected in **≥10% of control cells**
  in that library, else the knockdown test is underpowered and the target is
  dropped as `NOT_ESTIMABLE` rather than `NOT_ENGAGED` — these two must be
  reported as distinct outcomes.

**Gate 3 — neutral control must be near zero.** Run the 3-vs-3 control split
through the full effect pipeline.
- Frozen requirement: the **median absolute control-vs-control effect must be
  < 50% of the median absolute real target effect**, and the control-vs-control
  differential-expression call count at the paper's own threshold
  (adjusted p ≤ 0.05, |log2FC| ≥ 1) must be **< 20% of the median call count
  across real targets.**
- This is the direct repair of the GSE301119 failure, where the fake-null median
  (−1.504) came out **larger** than the real median effect (−1.344).

**Gate 4 — replication across differentiation.** Each qualifying target's effect
vector must correlate positively between XP1 and XP2 (Spearman > 0, computed on
the shared measured address set). With n=2 this is a consistency check, not a
significance test, and must be reported as such.

### What would DISQUALIFY GSE289721

Any one of the following ends the dataset's use as evaluation truth:

1. **Gate 3 fails** — control-versus-control effects are comparable in magnitude
   to real target effects. This is the GSE301119 disqualifier and it is
   non-negotiable.
2. **Gate 2 fails for ≥4 of 6 targets** — fewer than 3 engaged targets leaves too
   thin a basis for any concordance claim, and echoes the CRISPRbrain outcome
   (engagement in 1 of 31).
3. **Gate 1 fails** — the deposited matrices cannot reproduce the published
   perturbed-cell counts, meaning the public files are not the analysed files.
4. **Per-target assigned-cell count falls below 100 in both differentiations** for
   a target — that target is dropped; if this removes ≥4 targets, see (2).
5. **Control:target cell ratio exceeds 5x** for a target after assignment —
   the imbalance regime that produced the GSE301119 artifact. (Expected ~2x, so
   this should not trigger; it is a tripwire, not a prediction.)
6. **The cell-line contradiction (§5.1) cannot be resolved** *and* the evaluation
   claim depends on genetic background. For a within-line perturbation-response
   claim it does not; for anything about *APOE* or ancestry it does.

### What GSE289721 may never be used for

- Any claim about **generalization across people or genotypes** — n=1 background.
- Any claim requiring **more than 2 independent biological replicates**.
- Any **therapeutic ranking** — out of scope and off under this lane's footer.
- Promotion to **training data**. It is an evaluation candidate only, and §12
  explains why even that needs a firewall.

---

## 10. Power and estimability diagnostics

**The governing number: ~13% of cells carry a usable guide label.** The paper
analyses 5,872 perturbed cells (2,899 vehicle + 2,973 poly(I:C)) against 44,913
sequenced — 48,568 CellRanger barcodes in the deposit. Roughly 87% of cells fall
below the `<5` guide-UMI cutoff.

Whether 5,872 is pooled across XP1+XP2 or is per-experiment is
**NOT_STATED_IN_DEPOSIT.** The per-target and per-guide breakdown is
**NOT_STATED_IN_DEPOSIT** and is not derivable from any deposited summary — it
must be measured by running Gate 1.

Under a uniform-distribution assumption (which will not hold — lentiviral guide
representation is typically log-normal with several-fold spread), 5,872 assigned
cells across 24 guides gives roughly:

| Unit | Cells (uniform assumption) |
|---|---|
| per guide | ~245 |
| per target (3 guides) | ~734 |
| control pool (6 guides) | ~1,468 |
| **control : target ratio** | **~2.0x** |

That ratio is the headline structural improvement: **2x here versus 19.8x in
GSE301119.**

These are projections, not measurements. They must be replaced by measured
counts from Gate 1 before any effect is interpreted.

### Separating low power from genuine biological disagreement

Every reported disagreement between JEPA and this dataset must be accompanied by
the evidence that the dataset *could have* detected the predicted effect:

1. **Per-target cell counts** (measured, per library) with exact binomial CIs.
2. **Guide support**: how many of the 3 guides per target independently carry
   cells above threshold. A target resting on 1 of 3 guides is a single-guide
   result and must be labelled as such — off-target effects are not separable
   from on-target ones at n=1 guide.
3. **Assignment purity**: for each assigned cell, the ratio of top-guide UMIs to
   total guide UMIs. Report the distribution. Low purity quantifies the
   attenuation described in §7, and the attenuation factor should be estimated
   and reported alongside every effect size.
4. **Detection rate** of each measured address in control cells, so a null result
   on an undetected gene is never reported as a biological disagreement.
5. **Minimum detectable effect (MDE)**: for each target x address, the smallest
   log fold change detectable at 80% power given the measured cell counts and
   detection rate. **A disagreement is only reportable when JEPA's predicted
   effect exceeds the MDE.** Below the MDE the correct verdict is
   `UNDERPOWERED`, not `MODEL_WRONG`.
6. **Positive control**: poly(I:C) versus vehicle in control cells must produce a
   strong, coherent interferon response. If the stimulus contrast is not
   recoverable, the dataset cannot resolve anything subtler, and no perturbation
   result from it should be believed.

---

## 11. Acquisition plan — authenticated, no large download in this lane

Per the lane constraint, no raw data was downloaded. Only small
metadata/supplementary files were retrieved. Everything below is verified to
exist at the stated size.

### Already retrieved and authenticated (this lane)

| File | Bytes | SHA-256 |
|---|---|---|
| GSE289721 series record (`form=text`) | 2,807 | `598c1dc5a611d7f5a42322422a3bb6e73f05a012f5ac4459fb47556a2a291dfe` |
| GSM full metadata (`targ=gsm&form=text`) | 24,140 | `b034e4eb12702ab19dd3ad5af4ef711340070f85e456e770b1331762bca094f4` |
| `GSE289721_feature_ref4.csv.gz` | 884 | `4b0188608f15b7466b89436c3c7a0a79b7ace2cce4c92e90f043f29af8f24608` |
| `feature_ref4.csv` (decompressed) | 7,882 | `61151ab5886d40eaabfa222440fa7136f70bd2b60a3a4ac1f6b023dfe7033d19` |
| `filelist.txt` | 922 | `3ac7920d4f061867e3365d31eb32d68313cd33b6af68994b75cf5d3013251a57` |
| `GSM8797509_SS001_features.tsv.gz` | 333,951 | `663a34a599a17300ea69b3956c934197e5139a72dc3070a593ad5cd947629369` |
| `GSM8797511_SS002_features.tsv.gz` | 333,951 | `e9c7e0fa48cf2dd152db04f351c53df07a0413c31c86496925f530e566daad9b` |
| `GSM8797513_AS001_features.tsv.gz` | 333,951 | `8fac81a079100dea751793085d3e41f22ac2024b0a7d85bb4830a064f2723a4d` |
| `GSM8797515_AS002_features.tsv.gz` | 333,951 | `3a7805ead3a3cffea6b2287da22df447a461fa5eadcb5212e4f46ae68cb0e486` |
| `GSM8797509_SS001_barcodes.tsv.gz` | 63,758 | `ac27bc131372912f70bb78e5f684f85beec1cd988b2c2eae2c49af977a6d81fe` |
| `GSM8797511_SS002_barcodes.tsv.gz` | 66,953 | `71664f2096f3cd93d70f24f8f9596889c9d91542f26af01b449cc5405b50d78e` |
| `GSM8797513_AS001_barcodes.tsv.gz` | 53,506 | `beb0ba7879cd0b01f5b5cebb41fea8df32a435c186e453e590c7b634126a8ae5` |
| `GSM8797515_AS002_barcodes.tsv.gz` | 59,474 | `d66a6babf87a287e624eea19c4e79a7f13be50cf9e8b4b13f07981cb56241322` |

Retained outside git at `D:\jepa_laneE_outputs_20260926\`. The three smallest
primary-source files are committed under `docs/v4/lane_e_gse289721_evidence/`.

### Step 1 — acquire the 4 GEX matrices (NOT the RAW.tar)

Fetch the 4 `matrix.mtx.gz` per-sample, **not** `GSE289721_RAW.tar`. The tar is
619,325,440 B and contains the same 12 files; the per-sample route is
617,731,307 B of matrices and permits partial/resumable acquisition and
per-file hashing.

```
https://ftp.ncbi.nlm.nih.gov/geo/samples/GSM8797nnn/<GSM>/suppl/<GSM>_<LIB>_matrix.mtx.gz
  GSM8797509_SS001  171,080,282 B
  GSM8797511_SS002  160,413,551 B
  GSM8797513_AS001  137,071,587 B
  GSM8797515_AS002  149,165,887 B
```

Record the SHA-256 of each on arrival and compare against the sizes in
`GSE289721_suppl_filelist.txt`. Total on-disk ~618 MB, well inside a normal
working budget.

### Step 2 — supplementary tables from the paper

Table S1 (full gRNA library oligos), **Table S2 (CROP-seq gRNA constructs —
resolves the CABP5/SAGE1 control assignment, §6.1)**, Table S4 and S5 (CROP-seq
DEG by target). These are small; Table S2 is the priority because it closes the
negative-control mislabel.

### Step 3 — NOT required, explicitly

`GSE289721_RAW.tar` (redundant), and SRA BioProject **PRJNA1152984** (the
119-gene ROS screen — a different experiment, not this deposit, §3.1). Neither is
needed for the qualification protocol. Do not acquire either on the assumption
that "119 targets" are available here.

---

## 12. Overlap with existing training and benchmark data

| Corpus | Overlap | Assessment |
|---|---|---|
| **FULL104** (SEA-AD, 104 postmortem donors) | **None.** iPSC-derived cells from a commercial line; no SEA-AD donor. | Donor axis clean. |
| **Address space** | 36,601 gene rows against the frozen 41,238-address registry; all 6 targets `current_exact` and in HVS_COMMON. | Alignment clean, no identity ambiguity. |
| **GSE178317** (Kampmann/Dräger iTF-microglia CROP-seq) | **INPP5D is targeted in BOTH.** Registered in the project audit as `primary_microglial_perturbation_training`. | **Contamination risk — see below.** |
| **GSE301119** (primary macrophage, `myeloid_auxiliary_training`) | No target overlap established; different cell type (macrophage, not microglia). | Different lab, different cell type. Independent. |
| **CRISPRbrain** (Kampmann, WTC11) | Same lab lineage as GSE178317; different from this deposit. | Independent of GSE289721. |

### The INPP5D contamination finding — act on this

`INPP5D` appears in the Dräger/Kampmann CROP-seq DEG target list recorded in
`docs/external_perturbation_benchmarks.md`, and GSE178317 is registered as a
**training** candidate. If the model is trained on GSE178317's INPP5D
perturbation response, then **INPP5D in GSE289721 is not a held-out target** —
the model would have seen a real measurement of that same perturbation in the
same cell type.

Required handling, prospectively:

- **Score INPP5D separately and label it `TRAINING_OVERLAP_SUSPECT`.** Never
  pool it into a headline concordance number with the other 5.
- Confirm whether GSE178317 actually entered training. The audit registers it as
  a candidate with `MATERIALIZATION POLICY NEEDED`, which is not the same as
  "used". This is a direct question for the training-provenance lane, not
  something to assume in either direction.
- The remaining 5 targets — **AGFG2, EED, MS4A6A, PVR, RABEP1** — have no
  recorded overlap with any project training corpus and are the clean set.

### The independence this dataset genuinely has

Unlike the CRISPRbrain pair — which was **not** independent replication because
it shared a lab, a paper and a guide library — GSE289721 is from **Sproul/Chavez
at Columbia**, with its **own guide library** (sequences deposited, §6), a
different iPSC line, and a different stimulus paradigm from the Kampmann work.
For the 5 non-overlapping targets, this is genuine external data.

---

## 13. Explicitly NOT determinable from the deposit

Recorded as `NOT_STATED_IN_DEPOSIT` — no estimate substituted.

1. **Per-target and per-guide cell counts.** Must be measured (Gate 1).
2. **Whether 2,899 / 2,973 are pooled across XP1+XP2 or per-experiment.**
3. **Cell line identity** — GEO says IMR90, paper says FA10 (§5.1). Unresolved.
4. **Sex, age, ancestry and *APOE* genotype** of the line. Absent from both.
5. **Which NEG_CTRL guide targets *CABP5* vs *SAGE1*** (§6.1). Deposit annotates
   all 6 as `Non-Targeting`, which the paper contradicts.
6. **Knockdown efficiency for any target.** No qPCR, no on-target reduction
   reported (§8). Measurable by us; unproven by the authors.
7. **Which 3 of ≥6 available guides per gene were selected, and why.**
8. **MOI / transduction efficiency**, hence the expected multi-guide cell rate.
9. **Whether XP1 and XP2 used separate iPSC thaws**, or one thaw split into two
   differentiations — this determines whether n=2 is truly 2 or closer to 1.
10. **Poly(I:C) delivery method** (transfected vs naked) — affects which
    sensing pathway is engaged and therefore what response JEPA should predict.
11. **Cell counts before/after QC per library** beyond the CellRanger barcode
    counts measured in §4.1.

---

## 14. Preliminary feasibility verdict

**QUALIFIED-FEASIBLE, PENDING GATES 1–3. NOT PROMOTED TO BENCHMARK TRUTH.**

The dataset is worth the ~618 MB and the analysis time, because it is the first
candidate whose *design* does not contain the flaw that killed its predecessors:
the control cells sit in the same droplet run as the perturbed cells at roughly a
2:1 ratio, the guide library is complete and deposited with sequences, the
assignment rule is published and reproducible from public files, and CRISPRi
makes on-target engagement measurable in the very matrix being scored.

It is **not** qualified today, for three reasons that are all resolvable with
public files and no new experiment: engagement is unproven, the per-target cell
counts are unknown and ~87% of cells carry no guide label, and the deposit
contradicts the paper about which cell line this is.

Its ceiling is fixed and should be stated whenever it is cited: **one genetic
background, two differentiations, six targets, of which five are clean of
training overlap.** That supports a narrow, honest claim — whether JEPA predicts
the right transcriptional response to knocking down specific genes in human
iPSC-derived microglia, with and without an immune stimulus — and supports
nothing about variation between people.

**Recommended next action:** acquire the 4 matrices (§11 Step 1) and Table S2,
then run Gates 0–3 in that order. Gate 2 (engagement) and Gate 3 (neutral
control) are the decision points. If either fails, the correct outcome is to
record the failure and stop — as the project did with GSE301119 — not to adjust
the protocol frozen above.

---

TRAINING=OFF · AUDIT_B_N1=UNOPENED · PROTECTED_FULL104_OUTCOMES=UNOPENED ·
D_SHARED_G5=UNOPENED · RARE_TAIL_MOLECULAR=UNOPENED · THERAPEUTIC_RANKING=OFF
