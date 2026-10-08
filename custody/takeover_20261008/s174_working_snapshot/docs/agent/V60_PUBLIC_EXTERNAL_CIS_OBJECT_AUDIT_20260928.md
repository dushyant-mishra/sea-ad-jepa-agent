# V60 — fully public external cis-object audit

**Date 2026-09-28. Branch `claude/v59-r3-audit-and-external-cis-20260928`, from
`3324ad27`. `TRAINING=OFF`. `TD60=BLOCKED`. No molecular regulatory outcome
opened. No target-gene, program-gene, Stage75F-edge or confirmation-cohort
overlap was computed for any candidate.**

## The rubric, frozen before any candidate was scored

Structural and provenance criteria only. Restated from V59 and unchanged, with
two additions forced by the no-DUA decision.

| # | criterion |
|---|---|
| P1 | source-cohort independence from FULL104/SEA-AD, Morabito, GSE214979, GSE272082 |
| P2 | microglial specificity |
| P3 | donor count **and which donor count** — substrate donors, not headline donors |
| P4 | does RNA contribute to enhancer→gene definition? |
| P5 | does link direction come from **contact**, perturbation, **covariance**, or accessibility geometry? |
| P6 | do disease labels or disease loci participate in feature selection? |
| P7 | donor/cohort overlap risk |
| P8 | does instantiating the object require any of OUR measurements? |
| **P10** | **fully public, no DUA, end-to-end reconstructible** — new, and now disqualifying |
| **P11** | **stable feature identity** — genomic coordinates + genome build, ideally Ensembl IDs |
| P9 | which nuisance classes remain shared |

**Method externality ≠ substrate externality.** A pretrained method applied to
*our* confirmation ATAC is not an independent object. Applied to an external
public substrate, it can be.

---

## Card 1 — Corces adult human brain atlas, **GSE147672**

| field | finding |
|---|---|
| accession | **GSE147672** (BioProject PRJNA616031), 162 samples |
| public access | **OPEN_PUBLIC, no DUA.** Supplementary distribution includes the scATAC SummarizedExperiment (barcodes / peaks / rds), per-cell-type IDR and overlap peak sets, bigwigs, and `GSE147672_RAW.tar` |
| overall design | verbatim: **"Bulk ATAC-seq, single-cell ATAC-seq and HiChIP"** — activity *and* contact in one public accession |
| species/tissue | human adult brain, 7 regions (bulk), 6 regions (scATAC) |
| **donor counts (P3)** | **39 cognitively healthy donors for bulk ATAC; scATAC from only 10 samples.** The headline 39 is not the substrate n for the single-cell layer. |
| microglial specificity (P2) | microglia present as **Cluster 24** of 24, explicitly grouped among "less abundant cell types (less than 20% of cells; i.e. microglia, astrocytes, and OPCs)". **No explicit microglial cell count is stated.** |
| **RNA in link definition (P4)** | **No.** The study generates no RNA. GTEx v8 bulk RNA is used downstream to validate predictions and for MAPT haplotype analysis — not to define links. |
| **link direction (P5)** | **two distinct link sets.** HiChIP H3K27ac loops → **833,975 predicted 3D interactions** (contact-defined). Co-accessibility → **2,822,924 putative pairwise interactions** (**covariance-defined, within-ATAC**). |
| disease selection (P6) | **none.** Donors are **cognitively healthy only**; the cohort contains no AD or PD cases. Stronger than Kosoy's mixed AD/control substrate. |
| **overlap risk (P7)** | **MATERIAL.** Donors came "from **Stanford University, the University of Washington, or Banner Health**". **University of Washington is a SEA-AD/FULL104 source institution.** |
| requires our data (P8) | **No.** |
| feature identity (P11) | **hg38** throughout; hg19 conversion used only for GWAS analysis. Peaks distributed as coordinate BED-like sets. |

**The two properties that matter most, and they point opposite ways.**

*In favour:* Corces contains **no RNA at all**. An enhancer→gene object built from
its HiChIP loops therefore *cannot* encode RNA↔ATAC covariance, which is the
circularity the whole external-object strategy exists to escape. That is a
stronger guarantee than Kosoy, where RNA existed in the study even though it did
not define links.

*Against:* **the University of Washington overlap is with SEA-AD — our primary
internal modality anchor.** This is not a distant hypothetical like the ROSMAP
constraint; it is a named shared institution with the cohort we intended to use
for the internal anchor step.

**The two link sets are not interchangeable, and only one is admissible.**
Co-accessibility is a covariance estimator over ATAC. Adopting it would rebuild
the circularity in a single modality. **Only the HiChIP contact loops may be
used.** This must be frozen explicitly, because the co-accessibility set is
larger (2.8M vs 834k) and would otherwise look like the more attractive resource.

---

## Card 2 — FreshMicro / Kosoy: **DISQUALIFIED on P10**

Retained as published/supporting evidence only. Construction is attractive —
ABC, contact × accessibility, genome-wide, RNA-free links, 150 microglial donors
— but the object is behind the AD Knowledge Portal and, under the no-DUA
decision, is **not reconstructible or auditable end-to-end**. P10 is
disqualifying regardless of how good P4/P5/P6 look.

The ROS/MAP → ROSMAP mutual-exclusivity constraint from V59 still stands and
still binds any future ROSMAP adoption.

---

## Cards 3 and 4 — NOT YET AUDITED, and I will not assert them

**scE2G** and **ABC-on-a-public-substrate** were not audited in this pass. I have
not verified whether scE2G's model weights, code and required reference inputs
are reproducibly public, nor whether an ABC run could be assembled entirely from
public inputs. **Recording them as unaudited rather than scoring them from the
description**, because P10 is precisely the criterion that cannot be judged from
a paper.

Note for that audit: both are **methods**, so they inherit P1/P2/P3/P7 from
whatever substrate they are instantiated on. Instantiating either on Corces
inherits Corces's UW overlap. Instantiating either on *our* ATAC fails P8.

---

## Selection

**Provisional selection: Corces GSE147672 HiChIP contact loops, restricted to
the microglia cluster's cCREs.** It is the only fully public candidate audited
so far that satisfies P4, P5, P6, P8, P10 and P11 simultaneously.

**Not yet frozen.** Three facts must be established first, all provenance-only:

1. **Microglial depth.** "<20% grouped with astrocytes and OPCs" over 70,631
   cells is not a number. If the microglia cluster is small, the cell-type
   specific peak set may be too thin to define a usable cis object — and that
   would be a feasibility failure, not a biological one.
2. **The UW overlap (P7).** Whether Corces's UW donors can be excluded, or
   whether the overlap must simply be carried as a named dependency against the
   SEA-AD anchor step. Note the parallel: this is the same structural situation
   as GSE214979's UCI donors 1224/1230/1238.
3. **Which distributed file actually carries the HiChIP loops**, and in what
   coordinate representation — the supplementary listing shows scATAC products
   explicitly but the loop calls may sit inside `GSE147672_RAW.tar`.

**Substrate n is 10 donors for the single-cell layer.** That is below every
confirmation scale we care about and well below the n=18 the gate must clear. It
does not disqualify the object — a cis map is not estimated per confirmation
donor — but it does mean the map's own stability is weakly determined, and any
claim of donor-robustness for the *map* would be unsupported.

---

## What this changes about the plan

The external object is now **fully public and disease-free by construction**,
which is a genuine improvement over Kosoy on P6 and P10. But it is **not free of
overlap with our own confirmation cohort**, which Kosoy was thought to be. So
Outcome 2 persists under a different dependency: not "unresolved donor identity
behind a portal" but "**a named shared institution with SEA-AD**".

That dependency is at least *nameable and boundable*, which the Kosoy one was
not. It can enter the nuisance class explicitly, and it argues for running
**Morabito before SEA-AD** — which was already the V50 red-team recommendation,
now reinforced for an independent reason.

## Self-audit

**Starting SHA** `3324ad27`; ending SHA in the commit. Branch/worktree as above.
**Changed files:** this document — class **docs**.

**Sources consulted:** NCBI eutils (`db=gds`) for GSE147672 summary and SOFT
header; the GEO FTP supplementary listing; the Corces 2020 open-access record
(PMC7606627). **Access class:** all `OPEN_PUBLIC`. **No controlled data was
requested or downloaded. No file was downloaded at all** — only listings and
metadata were read.

**Protected outcomes opened: NO. Molecular biological outcomes opened: NO.**
No overlap with target genes, program genes or Stage75F edges was computed.

**Positive control on the method:** the `db=gds` pipeline correctly identified
GSE160523 as a *mouse* study in the previous pass, so it demonstrably
distinguishes wrong accessions rather than confirming whatever it is given.

**Strongest alternative explanation for the selection:** that the UW overlap is
negligible in practice, since Corces used 10 scATAC samples of which only a
subset are UW, and SEA-AD has 46 donors. Possibly true — and exactly the
reasoning this project has already been burned by twice. It stays a named
dependency until donor-level evidence says otherwise.

**Strongest criticism of my own audit:** I have selected an object whose
microglial depth I cannot state, from a distributed file set where I have not
confirmed the HiChIP loops are separately available. Both are checkable without
a DUA, and until they are checked this selection is **provisional, not frozen**.
I am also aware that Corces is the candidate the brief listed first, and that I
found in its favour — the UW finding is the evidence that I was not simply
ratifying the suggestion.

**What remains unknown:** microglial cell count and peak-set size; HiChIP loop
file location and format; scE2G and ABC public reconstructibility; whether
Corces UW donors overlap SEA-AD at the person level.
