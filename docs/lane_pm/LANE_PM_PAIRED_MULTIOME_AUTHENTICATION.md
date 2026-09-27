# Paired-Multiome Authentication Lane — verdict and frozen eligibility

**Lane:** `lane/paired-multiome-authentication-20260926` · **Base:** `c49b13bd` (origin/main)
**Date:** 2026-09-26 · **Scope:** provenance and eligibility only. No biological outcome was inspected.

---

## Read this first (plain language)

**This is mixed news, and the useful half is genuinely useful.**

One of the two new datasets is real and usable. **GSE214979 (Anderson) is the only
dataset this project has found where the RNA and the ATAC come from the same
individual nucleus** — all 105,332 of them, verified cell by cell, not inferred
from the word "multiome". That is a capability we did not previously have:
Morabito (GSE174367), the dataset already in hand, measured RNA and ATAC in
*separate* nuclei from the same brains, so it can only ever support donor-level
comparison. GSE214979 can support cell-level work.

**But it is small, and two things about it are broken.** Fifteen people is
fifteen people. With n=15 you can only detect an effect of about 1.6 standard
deviations — roughly twice the size of the largest real effects anyone reports in
this literature. This dataset is a *confirmation* instrument, not a discovery
instrument, and it will only confirm something very large. Separately, I found
two donors whose sex and age are **swapped** between two parts of the same
deposit, and those two donors are exactly the pair that shared one pooled
sequencing lane. That affects 10.4% of the nuclei. It is fixable by dropping
them — together with one donor that has only 17 microglia, that leaves 12 usable
people — but it must not be ignored.

**The second dataset, GSE272082, cannot be qualified yet — not because it is bad,
but because the one number that decides everything is missing.** Nobody deposited
cell-type labels. There is no way to know how many microglia there are, per
donor or in total, without downloading data and annotating it ourselves. I did
not estimate it. And its real sample size is **9 people**, not 27: the three
brain regions come from the same nine donors, and six of them contributed three
regions each. At n=9 the smallest detectable effect is about 2.2 standard
deviations, which is not a realistic target.

**Both owner-supplied descriptions had errors, and both traps in the brief were
real.** GSE214979 is not a second cohort — it is literally the same sample
records as GSE214637, filed under a parent accession. And GSE272082's three
regions are not 27 independent units.

**What is still fine:** Morabito is untouched and its PR #164 findings stand. No
protected SEA-AD outcome, sealed result or masking artifact was opened. Neither
new dataset has ever appeared anywhere in this repository's history, so both are
genuinely unexposed. Nothing here blocks the teacher-target experiment running in
parallel.

---

## Verdicts

| Dataset | State | One-line reason |
|---|---|---|
| **GSE214979** (Anderson, = GSE214637 subseries) | **CONDITIONAL** | Same-nucleus pairing VERIFIED at 105,332/105,332; but n=15, and 2 donors carry a demographic label swap. Usable after exclusions. |
| **GSE214637** (Anderson parent) | **NOT A DATASET** | SuperSeries container. Holds no data of its own; its supplementary directory returns HTTP 404. Must never be counted as a cohort. |
| **GSE272082** (sEOAD, 3 regions) | **NEEDS_AUTHENTICATION** | Microglia count is undeposited and unknowable without acquisition. Effective n=9. Blocked on a 0.77 GiB acquisition, not on a flaw. |
| **GSE174367** (Morabito) | **CONDITIONAL** (unchanged) | Per PR #164. Not re-authenticated here; placed relatively below. |

---

## Trap 1 — GSE214979 is a SUBSERIES, not a replication cohort

**CONFIRMED from both primary records.** This is the single most important
finding for anyone assembling an evidence base.

From `GSE214637_self_brief.txt` (SHA-256 `1e22ac67…`):

```
!Series_relation = SuperSeries of: GSE214911
!Series_relation = SuperSeries of: GSE214979
```

From `GSE214979_self_brief.txt` (SHA-256 `b50b1742…`):

```
!Series_relation = SubSeries of: GSE214637
```

Three independent confirmations that they are one cohort, not two:

1. **Sample containment.** GSE214637 lists 48 GSMs. GSE214979 lists 40 of those
   same 48. The remaining 8 (GSM6617833–GSM6617840) are GSE214911, a **ChIP-seq**
   subseries — a different assay, not a replication.
2. **Every GSM declares dual membership.** Each of the 40 sample records carries
   both `!Sample_series_id = GSE214637` **and** `!Sample_series_id = GSE214979`.
   They are the same physical records filed under two accessions.
3. **The parent holds no data.** `ftp.ncbi.nlm.nih.gov/geo/series/GSE214nnn/GSE214637/suppl/`
   returns **HTTP 404 — Object not found**. All five data files live under
   GSE214979.

**Consequence:** citing GSE214637 and GSE214979 as two datasets would double-count
the same 105,332 nuclei and the same 15 people, inflating the apparent evidence
base by exactly 2x. The correct statement is: *one cohort, 15 donors, reachable
by two accession numbers.*

---

## Trap 2 — GSE272082 is n=9 people, and the deposit is larger than its own design text

**Effective independent n = 9.** Not 27, not 21, not 20.

GEO deposits one row per library and no donor key. Reconstructing donors by the
invariant person-level attributes the deposit does record (sex, age at death,
post-mortem interval) yields **9 donors across 21 region-libraries**:

| Donor | Sex | Age | PMI (h) | Group | Regions | Libraries |
|---|---|---|---|---|---|---|
| 1 | M | 61 | 22.4 | Control | PFC, EC, HIP | NIH01, NIH02, NIH03 |
| 2 | M | 62 | 12.5 | Control | PFC, EC, HIP | NIH04, NIH05, NIH06 |
| 3 | F | 62 | 18.9 | Control | PFC, EC, HIP | NIH28, NIH29, NIH30 |
| 4 | M | 62 | 48 | Control | PFC | UT04 |
| 5 | M | 65 | 24 | Control | PFC | UT09 |
| 6 | F | 61 | 24.2 | sEOAD | PFC, EC, HIP | NIH10, NIH11, NIH12 |
| 7 | F | 64 | 24.3 | sEOAD | PFC, EC, HIP | NIH13, NIH14, NIH15 |
| 8 | M | 62 | 20.5 | sEOAD | PFC, EC, HIP | NIH16, NIH17, NIH18 |
| 9 | M | 59 | 68 | sEOAD | PFC | UT2105 |

5 Control + 4 sEOAD = 9 donors, matching the record's own summary. Region
composition **PFC 9 / EC 6 / HIP 6 = 21**.

The donor grouping is an **INFERENCE**, not a deposited fact — GEO publishes no
donor key for this series. It is well supported (each triple shares an exact
PMI to one decimal place, which is effectively a donor fingerprint) but it is
reconstructed, and is labelled as such in the artifacts.

### Three defects found in the GSE272082 record

1. **The series design text is stale.** `!Series_overall_design` states
   "prefrontal cortex (PFC, n=9), entorhinal cortex (EC, n=6), and hippocampus
   (HIP, n=5)" = 20. The deposit actually contains **21** libraries: NIH30
   (hippocampus, added 2025-11-14) completes donor 3 and was never reflected in
   the design text. The **publication agrees with the files, not the design
   text** — PMC12710691 states PFC n=9, EC n=6, **HIP n=6**. Two independent
   sources give 21; only the GEO prose gives 20.
2. **Two donors carry contradictory disease labels.** Libraries **UT04** and
   **UT09** are titled `"UT04,sEOAD"` and `"UT09,sEOAD"` but their
   `disease state` characteristic says **Control** (4 conflicting GSM records:
   GSM8392671, GSM8392672, GSM8392691, GSM8392692). The characteristics field is
   the correct one — only that reading yields the 4 sEOAD / 5 control split the
   summary and paper both state. **Anyone parsing sample titles instead of
   characteristics gets the group label wrong for 2 of 9 donors (22%).**
3. **Site and PMI are confounded with nothing useful but must be tracked.** The
   three UT libraries (UTHealth, Houston) are PFC-only, all male, and carry the
   two extreme PMIs in the cohort (48 h and 68 h, vs 12.5–24.3 h for the 18 NIH
   libraries). Whether this matters is UNDETERMINED here; it is recorded so a
   later estimator cannot be surprised by it.

### Total nuclei

**76,173 nuclei passing QC** — stated in the publication (Sci Adv 2025;11(51):eadw4917,
PMID 41406216, PMC12710691). The owner-supplied ">70,000" is confirmed.
The GEO record itself says "over 70,000" and states no exact figure.

---

## Same-nucleus pairing determination

| Dataset | Determination | Evidence |
|---|---|---|
| **GSE214979** | **VERIFIED PAIRED** | 105,332 / 105,332 barcodes (100.00%) carry non-zero RNA **and** ATAC counts on the same row of the series cell metadata. |
| **GSE272082** | **PAIRED BY CONSTRUCTION, UNVERIFIED** | 10x Chromium Multiome ATAC+GEX (CG000338), Cell Ranger ARC v2.0.2, one `filtered_feature_bc_matrix.h5` per library carrying both feature types. Not verified against the matrices — they were not downloaded. |
| **GSE174367** | **SEPARATE NUCLEI** | Established in PR #164: 16-mer barcode overlap 190 vs 9,893 expected (1.9% of null). Donor-level evaluation only. |

### Why GSE214979's pairing claim survives scrutiny

Three independent lines, none of which is the word "multiome" in the title:

1. **Per-cell measurement.** Every barcode row in
   `GSE214979_cell_metadata.csv.gz` carries `nCount_RNA`, `nFeature_RNA`,
   `percent.mt` **and** `nCount_ATAC`, `nFeature_ATAC`, `nucleosome_signal`,
   `TSS.enrichment`, `blacklist_fraction`. One barcode, both modalities, 100% of
   105,332 cells with no exceptions. Barcodes are unique and complete — 105,332
   rows, 105,332 distinct barcodes, no duplicates, no null donor.
2. **The depositor says so explicitly**, in the GSM records:
   `!Sample_data_processing = Processed files include paired scRNAseq and scATACseq counts from the same cells`
3. **The file format requires it.** A single 10x HDF5 `filtered_feature_bc_matrix.h5`
   carrying both Gene Expression and Peaks feature types over one barcode list —
   the format cannot represent unpaired modalities.

**This makes GSE214979 the only same-nucleus RNA+ATAC resource available to this
project.** It is the property that distinguishes it from Morabito and it is
verified, not assumed.

---

## Donor and microglia census

### GSE214979 — measured, complete

Total 105,332 nuclei / 15 donors. Cell types partition exactly:
Excitatory 39,884 · Oligodendrocytes 34,784 · Inhibitory 16,331 · Astrocytes 6,255 ·
OPCs 4,193 · **Microglia 3,179** · Pericytes 442 · Endothelial 264.

**Microglia = 3,179 (3.02% of nuclei).** Per donor, sorted ascending:

| Donor | Nuclei | Microglia | Mic % | Group | Repository |
|---|---:|---:|---:|---|---|
| **4313** | 1,410 | **17** | 1.21 | AD | HBSFRC |
| **HCTZZT** | 2,443 | **26** | 1.06 | Ctrl | Miami |
| 3586 | 9,700 | 152 | 1.57 | Ctrl | HBSFRC |
| 1230 | 4,631 | 161 | 3.48 | Ctrl | UCI |
| 4443 | 4,671 | 171 | 3.66 | AD | HBSFRC |
| NT1261 | 5,871 | 192 | 3.27 | Ctrl | *(blank)* |
| 1224 | 7,161 | 201 | 2.81 | Ctrl | UCI |
| 3329 | 7,320 | 211 | 2.88 | AD | HBSFRC |
| 4481 | 11,290 | 233 | 2.06 | AD | HBSFRC |
| 4627 | 8,864 | 241 | 2.72 | AD | HBSFRC |
| HCT17HEX | 8,522 | 264 | 3.10 | Ctrl | Miami |
| NT1271 | 6,686 | 265 | 3.96 | Ctrl | *(blank)* |
| 1238 | 11,723 | 283 | 2.41 | Ctrl | UCI |
| 4305 | 6,466 | 347 | 5.37 | AD | HBSFRC |
| 4482 | 8,574 | 415 | 4.84 | AD | HBSFRC |

**Minimum per-donor microglia = 17 (donor 4313).** Median 211, max 415.

The brief warned that "15 donors with 20 microglia each cannot support a
donor-level test." That warning lands: **donor 4313 has 17 microglia and HCTZZT
has 26.** Retention by threshold:

| Min microglia/donor | Donors retained | Microglia retained |
|---:|---:|---:|
| 10 | 15 | 3,179 |
| 20 | 14 | 3,162 |
| **50** | **13** | **3,136** |
| 100 | 13 | 3,136 |
| 200 | 9 | 2,460 |
| 300 | 2 | 762 |

A ≥50-microglia floor costs 2 donors and only 43 microglia (1.4%) — a cheap,
well-placed cut. Beyond 150 the cost turns sharp.

### GSE272082 — UNKNOWN, and deliberately not estimated

**Microglia count per donor: `NOT_STATED_IN_DEPOSIT`.
Total microglia: `NOT_STATED_IN_DEPOSIT`.**

Exhausted before declaring it unknown:

- **The deposit.** `filelist.txt` (SHA-256 `d0f87ad1…`) enumerates all 84 files
  in the 35 GiB archive. Every one is a Cell Ranger ARC primary output —
  `raw_feature_bc_matrix.h5`, `filtered_feature_bc_matrix.h5`,
  `atac_fragments.tsv.gz`, `.tbi`. **No cell metadata, no cell-type annotation,
  no clustering result is deposited at any level.**
- **The publication** (PMC12710691). Eight major cell types are identified, but
  per-cell-type counts are not given, and microglia are **not broken down by
  donor or by region**.
- **Supplementary data S1–S10B** exist but sit behind science.org, which returns
  HTTP 403 to automated fetch. Not retrieved.

The number is therefore obtainable **only by acquiring the matrices and
annotating cell types ourselves** — our annotation, not the depositors'. That is
a real cost and a real methodological commitment, and it is the reason this
dataset is `NEEDS_AUTHENTICATION` rather than `QUALIFIED` or `DISQUALIFIED`.

---

## The GSE214979 defect that must not be ignored

**Two donors have their sex and age swapped between two parts of the same deposit.**

| Source | HCT17HEX | HCTZZT |
|---|---|---|
| GEO sample records (GSM6619548 / GSM6619549) | **M, 84**, BA9 | **F, 77**, BA11 |
| Series cell metadata (`GSE214979_cell_metadata.csv.gz`) | **F, 77**, BA9 | **M, 84**, BA9 |

The demographics are transposed between the two donors. And these two donors are
**exactly the pair that shared pooled GEM lane 6** (HCT17HEX 8,522 nuclei +
HCTZZT 2,443 nuclei).

A label swap between the two occupants of a single genotype-demultiplexed lane is
the precise shape of a cell-to-donor join error. This project has already paid
for that lesson once: `cell_donor` is the join between the cell representation
and the donor-level outcome, and when it is wrong, donor-held-out evaluation
silently stops holding anything out. Here the join is not merely at risk of being
wrong — **the deposit does not agree with itself about it.**

A related inconsistency in the same two donors: their RNA and ATAC sample records
disagree about brain region (HCT17HEX BA9 vs BA10; HCTZZT BA11 vs BA12). If the
two modalities are the same nuclei — which is this dataset's central claim — the
region annotation cannot differ between them.

**Exposure:** 2 of 15 donors (13%), **10,965 of 105,332 nuclei (10.41%)**, and
**290 of 3,179 microglia (9.12%)**.

**Frozen remedy:** exclude HCT17HEX and HCTZZT. Combined with the ≥50-microglia
floor motivated above, the rule excludes **three** donors, not two — HCT17HEX for
the label swap alone, 4313 for low microglia alone, HCTZZT for both — leaving
**n=12 (6 AD / 6 Ctrl)**, 92,957 nuclei and 2,872 microglia. The two criteria
overlap on one donor only; the resulting cohort is derived in
`lane_pm_gse214979_census_report_v1.json` (`frozen_exclusions`) rather than
asserted, because that overlap is exactly where an off-by-one would enter.

### Pooling structure — donor assignment here is inferred, not physical

The deposit states its own demultiplexing method:

```
!Sample_data_processing = Sample demultiplexing was done with cellSNP and vireo
  to get a list of barcodes assigned to each sample.
```

Barcode-suffix × donor occupancy across **17 GEM lanes / 15 donors** shows:

- **3 pooled lanes carrying two donors each** — lane 5 (4313 + 4482), lane 6
  (HCT17HEX + HCTZZT), lane 7 (4305 + 4443). In these lanes, which donor a cell
  belongs to is a **genotype-based statistical inference**, not a physical
  separation. It carries a misassignment rate that the deposit does not report.
- **5 donors with two libraries each** — 1224, 1238, 3586, 4481, 4627 ("rep1"/"rep2").
  These are **technical replicates, not biological replicates.** The independent
  unit is the donor: **20 RNA libraries is not n=20; n=15.** This is the same
  failure mode as GSE178317 (four capture wells, one pooled prep), already
  documented in this project.

Note that the two donors with the fewest microglia (4313, HCTZZT) are both the
**minority partner in a pooled lane** — 14% and 22% of their lane's nuclei
respectively. Their low counts track low overall yield, not a measured biological
scarcity of microglia. Whether their unusually low microglial *fraction* (1.21%,
1.06%, against 2.06–5.37% elsewhere) is biology or a demultiplexing artifact is
**UNDETERMINED from the deposit**.

---

## Prior exposure register

**Neither new dataset has ever been seen by this project.** Searched by accession
value across the full repository, not one spelling of a key:

| Accession | Tracked files on `origin/main` | Commits in **all** history (`git log --all -S`) | Verdict |
|---|---:|---:|---|
| GSE214637 | 0 | 0 | **UNEXPOSED** |
| GSE214979 | 0 | 0 | **UNEXPOSED** |
| GSE272082 | 0 | 0 | **UNEXPOSED** |
| GSE174367 | 235 | many | **HEAVILY EXPOSED** (Morabito, by design) |

Both new candidates are genuinely untouched and can serve as confirmation sets.
Morabito cannot serve that role in the same way — it has been inspected
extensively, including the Stage75F regulator work.

---

## Donor independence

### From FULL104 (SEA-AD development cohort)

**No overlap. Determination: INDEPENDENT, with a stated limit.**

FULL104 donor identity is the SEA-AD identifier string of the form
`H18.06.004`, `H19.03.306`, `H20.33.001` (88 distinct SEA-AD donor IDs are
recoverable from tracked tables at this HEAD; the full 104-donor roster lives in
local `data/`, not in committed artifacts, and was not opened).

- **GSE214979** donor IDs: `1224 1230 1238 3329 3586 4305 4313 4443 4481 4482
  4627 HCT17HEX HCTZZT NT1261 NT1271`. Brain banks, per the deposit's own
  `Repository` field: **UCI (3), HBSFRC (8), Miami (2), blank (2)**.
- **GSE272082** donor libraries: `NIH01–NIH30, UT04, UT09, UT2105`. Sources:
  **NIH NeuroBioBank and UTHealth Houston**.
- **FULL104 / SEA-AD**: Seattle — ACT study and UW ADRC.

The identifier namespaces are structurally disjoint and the brain banks are
disjoint. **Limit to the claim:** neither deposit publishes a crosswalk to any
common identifier, so person-level non-overlap cannot be *proved* from the
deposits alone — it is inferred from disjoint source institutions. This is the
strongest statement the records support and it should not be reported as more.

### Between the two new datasets

**INDEPENDENT.** Different banks (UCI/HBSFRC/Miami vs NIH NeuroBioBank/UTHealth),
different regions (DLPFC/BA46/BA9/BA11 vs PFC/EC/HIP), different cohorts
(late-onset AD vs sporadic **early**-onset AD; GSE272082 ages 59–65, GSE214979
ages 49–92).

### Against Morabito GSE174367 — **an unresolved risk, flag this**

**GSE214979 draws 3 of its 15 donors (1224, 1230, 1238) from repository `UCI`.
Morabito GSE174367 is a UC Irvine dataset.**

Morabito's donors are deposited under pseudonyms (`Sample-40`, `Sample-101`), so
no crosswalk to the UCI ADRC identifiers `1224/1230/1238` is possible from either
deposit. **Determination: UNDETERMINED — possible donor overlap, unquantified.**

This matters concretely. PR #164 qualified Morabito as an evaluation candidate,
and this lane qualifies GSE214979 as another. **If the two are used together as
independent evidence and they share UCI donors, they are not independent**, and
the shared-infrastructure failure mode this project documented for CRISPRbrain
(1/31 joint engagement, concordance at chance) applies in its donor-overlap form.
Resolving it requires donor-level metadata that neither GEO deposit contains.

**Frozen rule until resolved:** GSE214979 and GSE174367 may each be used
independently, but a claim resting on *agreement between them* must either
exclude donors 1224, 1230 and 1238, or carry this caveat explicitly.

---

## Source-file inventory

All byte sizes are exact `Content-Length` values from the NCBI FTP endpoint, not
the human-readable listing. **GEO publishes no SHA-256 for any of these files** —
digests below are computed on what was actually retrieved.

### GSE214979 (series-level; the parent GSE214637 has no supplementary directory)

| File | Bytes | Needed? | Digest |
|---|---:|---|---|
| `GSE214979_cell_metadata.csv.gz` | 8,820,297 | **REQUIRED — retrieved** | SHA-256 `8ce4e0c78747cfa6fb2a556468893df0d378e3f53085e52955f3ecdcc944394b` |
| `GSE214979_filtered_feature_bc_matrix.h5` | 1,369,492,123 | **REQUIRED — not retrieved** | not computed (not downloaded) |
| `GSE214979_unfiltered_feature_bc_matrix.h5` | 1,558,740,382 | optional (QC only) | not computed |
| `GSE214979_atac_fragments.tsv.gz` | **63,641,120,882** | only for peak recall | not computed |
| `GSE214979_atac_fragments.tsv.gz.tbi.gz` | 6,719,411 | with fragments only | not computed |

The retrieved cell metadata authenticates by exact byte-length match against the
server's `Content-Length` (8,820,297). The owner's "~1.3 GB processed matrix" is
confirmed (1.275 GiB). The fragment archive is **59.27 GiB** — 46x the processed
matrix, materially larger than "considerably larger" conveys.

### GSE272082

`GSE272082_RAW.tar` = **38,076,518,400 bytes (35.46 GiB)** — owner's "~35.5 GB"
confirmed exactly. Contents enumerated from `filelist.txt` without downloading:

| Class | Files | Bytes | GiB | Needed? |
|---|---:|---:|---:|---|
| `filtered_feature_bc_matrix.h5` | 21 | 832,041,774 | 0.77 | **REQUIRED** |
| `raw_feature_bc_matrix.h5` | 21 | 1,507,078,266 | 1.40 | no |
| `atac_fragments.tsv.gz` | 21 | 35,715,709,589 | 33.26 | only for peak recall |
| `.tbi.gz` | 21 | 21,617,514 | 0.02 | with fragments only |
| **Total** | **84** | **38,076,447,143** | **35.46** | |

**Acquisition plan: fetch only the 21 filtered matrices — 0.77 GiB, 2.2% of the
archive.** GEO serves per-sample supplementary files individually, so the 35 GiB
tar never needs to be transferred. That 0.77 GiB is exactly what is required to
resolve the blocking microglia census.

### Primary records archived (in `docs/lane_pm/geo_records/`)

| Record | Bytes | SHA-256 |
|---|---:|---|
| `GSE214637_self_brief.txt` | 4,252 | `1e22ac671e8b6bd98668fae711d14aeefe2d52ed3da975c1b4ec6531ad37584b` |
| `GSE214979_self_brief.txt` | 4,537 | `b50b17427f1eb14c603494793fe3edd1fed53540ef1a882782ea6862c1a79499` |
| `GSE214911_self_brief.txt` | 3,510 | `039aa8beed271c2f374cf182a59f63f6aab8bfc127876e0dca12f877fc53a380` |
| `GSE214979_gsm_full.txt` | 158,137 | `655a95b8f749efc2ad19f131fe0740ef53ccaf6751bc0af3c28b0c0549c8bc2f` |
| `GSE272082_self_brief.txt` | 4,425 | `4435ce35f11e4cb03e890cb2cbf353f8d6d82d88dbc1fa1e644c8ca1def7f1a4` |
| `GSE272082_gsm_full.txt` | 137,710 | `e7c1b32959f4778198607a13f93938a5cb23c3ed0eda0b7f5086414670c84f9c` |
| `GSE272082_filelist.txt` | 6,909 | `d0f87ad1454c6e802c8ee1d1c8145ec1872f9c966871dc1531dadb63eda56f83` |
| `pmid41406216_esummary.xml` | 3,494 | `d81a7c9565ac534acedc7085907c128362e8c14d21e5e4882b675327ffe5b6b6` |

---

## Frozen evaluation eligibility

Thresholds below are frozen **before** any biological comparison is run. No
outcome was inspected in setting them.

### Detectable effect size — stated honestly

Two-sample t-test, α=0.05 two-sided, 80% power. This is the **minimum** effect
each design can detect; anything smaller is invisible to it.

| Design | n | Min detectable Cohen's *d* |
|---|---|---:|
| GSE214979, all donors | 7 AD / 8 Ctrl | **1.57** |
| **GSE214979, after frozen exclusions** | **6 AD / 6 Ctrl** | **1.80** |
| GSE272082 | 4 sEOAD / 5 Ctrl | **2.19** |
| GSE174367 (illustrative 9/9) | 18 donors | **1.41** |

**These are very large effects.** A *d* of 1.7 means the two group means are
separated by roughly 1.7 standard deviations. Donor-level transcriptomic
differences in this literature typically sit near *d* ≈ 0.3–0.8. **None of these
three datasets is adequately powered for a realistic donor-level AD effect**, and
no combination of them repairs that, because the limit is the number of people,
not the number of cells.

This is not a reason to discard them. It is a reason to be precise about what
they can do: they can **confirm a large, pre-specified effect** and they can
support **cell-level** questions where the unit of analysis is the nucleus. They
cannot discover a modest donor-level difference.

The project's standing rule applies directly: **cells improve the measurement of
the donor representation X; they never increase the independent sample size of a
donor-level outcome Y.** 3,179 microglia across 15 people is n=15.

### GSE214979 — CONDITIONAL, eligible for two test classes

**Frozen inclusion rule:** exclude HCT17HEX and HCTZZT (demographic label swap,
pooled lane 6); require ≥50 microglia per donor. **Result: n=12 (6 AD / 6 Ctrl),
92,957 nuclei, 2,872 microglia.** Both criteria were fixed before any outcome was
examined and each is independently justified. The cohort is *derived* by
`frozen_exclusions()` in the census script, not asserted here.

- **Cell-level paired-modality evaluation — ELIGIBLE.** Unique to this dataset:
  does an RNA-derived representation predict the *same nucleus's* chromatin
  state? Unit = nucleus, **n = 92,957** after the frozen exclusions (105,332
  before). Donor must be a grouping factor in every model, and the three pooled
  lanes must be carried as a covariate.
- **Donor-level AD/control evaluation — ELIGIBLE BUT UNDERPOWERED**, n=12,
  *d* ≥ 1.80 only. Must be pre-registered; must not be used for discovery.
- **Replication of a Morabito finding — CONDITIONAL** on the unresolved UCI
  donor-overlap question above.

### GSE272082 — NEEDS_AUTHENTICATION

**Blocked on exactly one unknown: the microglia census.** The gate to clear it:

1. Acquire the 21 `filtered_feature_bc_matrix.h5` files (0.77 GiB).
2. Count microglia per **donor** — the reconstructed 9, not the 21 libraries.
3. Apply the same ≥50-microglia-per-donor floor.
4. Verify same-nucleus pairing directly from the matrices (shared barcode list
   across GEX and Peaks feature types), rather than resting on format.
5. Resolve the UT04/UT09 label conflict in favour of the characteristics field
   and record the decision.

If it clears, the eligible test is a **donor-level, region-stratified**
comparison at **n=9**, *d* ≥ 2.19 — and the region axis must enter as a
within-donor repeated measure, never as extra donors. Three of nine donors
contribute PFC only, so a three-region design is unbalanced by construction.

**Do not promote this dataset on the strength of 35 GiB.** Size is not
qualification. Its 76,173 nuclei rest on 9 people.

### Relative placement against Morabito (GSE174367)

Morabito is **not re-authenticated here**; PR #164 stands. Placing the three:

| | GSE214979 | GSE272082 | GSE174367 |
|---|---|---|---|
| Donors (independent n) | **15** (12 after exclusions) | **9** | **18** |
| Microglia | **3,179 measured** | **UNKNOWN** | 4,126 RNA / 12,232 ATAC |
| Same-nucleus pairing | **VERIFIED** | unverified | **NO — separate nuclei** |
| Prior exposure | none | none | extensive |
| Local assets | metadata only | none | **10/10 authenticated** |
| Acquisition cost | 1.28 GiB | 0.77 GiB | 0 (on disk) |
| Min detectable *d* | 1.80 | 2.19 | 1.41 |

- **Morabito remains the strongest donor-level instrument** — most donors, most
  microglia, already on disk, already authenticated. Its five unsatisfied
  readiness gates are unchanged by this lane.
- **GSE214979 is the only cell-level instrument.** It is the strict complement to
  Morabito rather than a competitor, and that is its entire value: it answers a
  question Morabito structurally cannot.
- **GSE272082 ranks last** on every axis that has been measured, and its decisive
  axis has not been measured at all.

**None of the three is promoted to QUALIFIED by this lane.**

---

## What I could NOT determine

Stated as UNKNOWN, never as zero:

1. **GSE272082 microglia counts**, total and per donor — not deposited, not in
   the publication. Requires acquisition plus our own annotation.
2. **Donor overlap between GSE214979 (UCI donors 1224/1230/1238) and Morabito
   GSE174367** — Morabito's pseudonymised donor IDs make this unresolvable from
   the deposits. **Material risk; flagged.**
3. **Which of the two conflicting demographic records is correct for HCT17HEX /
   HCTZZT** — the deposit contradicts itself and offers no tiebreak.
4. **Whether the low microglial fraction in 4313 and HCTZZT is biological or a
   demultiplexing artifact** — both are minority partners in pooled lanes.
5. **Person-level non-overlap with FULL104** — inferred from disjoint brain banks
   and disjoint ID namespaces; not provable from the deposits.
6. **SHA-256 of the large GEO archives** — GEO publishes no digests and the files
   were deliberately not downloaded.
7. **Genotype-demultiplexing misassignment rate for GSE214979's 3 pooled lanes** —
   not reported by the depositors.
8. **GSE272082 supplementary data S1–S10B** — science.org returns HTTP 403 to
   automated fetch; may contain the missing cell-type counts.

---

## Reproduction

Executed from this branch at base `c49b13bd`, worktree verified clean
(`git status --porcelain` empty) before the runs.

```bash
python scripts/lane_pm/lane_pm_paired_multiome_census_v1.py \
  --cell-metadata <path>/GSE214979_cell_metadata.csv.gz \
  --out-dir results/lane_pm

python scripts/lane_pm/lane_pm_geo_donor_reconstruction_v1.py \
  --gsm-text docs/lane_pm/geo_records/GSE272082_gsm_full.txt \
  --out-dir results/lane_pm --label GSE272082
```

`GSE214979_cell_metadata.csv.gz` (8,820,297 bytes, SHA-256 `8ce4e0c7…`) is **not
committed** — it is a source artifact referenced by path, size and digest per the
project's large-artifact rule. Retrieve from
`https://ftp.ncbi.nlm.nih.gov/geo/series/GSE214nnn/GSE214979/suppl/GSE214979_cell_metadata.csv.gz`.

Outcome columns present in that file (`Braak`, `APOE_Status`) were **never read**;
the census script asserts their exclusion and records the assertion in its report.
Group assignment (`Status`) was read — it is cohort design, already public in the
GEO record, and necessary to state per-group donor counts.

---

TRAINING=OFF · AUDIT_B_N1=UNOPENED · PROTECTED_FULL104_OUTCOMES=UNOPENED · D_SHARED_G5=UNOPENED · RARE_TAIL_MOLECULAR=UNOPENED · THERAPEUTIC_RANKING=OFF
