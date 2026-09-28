# V49 project-wide modality inventory — identification-focused

Date: 2026-09-28  
Base: PR #178 `1ceaf3e9a3de15cd2386da7398e8620510ed8be1`  
Status: `RECONNAISSANCE_AND_ACQUISITION_PLAN_ONLY__NO_BIOLOGICAL_OUTCOME_OPENED__TRAINING_OFF`

## Why this inventory exists

The relational-control audit established that a shared latent visible only through two RNA views is not, in the unrestricted case, identifiable as biological rather than technical. The next useful information must therefore come from measurement channels with different failure modes.

This inventory asks a narrower question than "what datasets exist?":

> Which modalities already exist for project cohorts, or in closely relevant external cohorts, that can help distinguish biological cell-state structure from RNA capture / nuclear-quality structure?

Same-nucleus pairing is especially valuable, but is **not automatically biological proof**: RNA and ATAC can still share nuclear-quality effects. Every cross-modal identification analysis therefore needs technical negative controls before biological outcomes are opened.

---

## Access audit correction — public vs controlled

For the current project, “available in a publication” is **not** the same as “freely downloadable”. The following access classes are controlling:

| Resource | Access class for the data needed here | Can proceed now without a DUA? |
|---|---|---|
| SEA-AD processed snRNA/snATAC + spatial resources on Allen/AWS | **OPEN PUBLIC** | **YES** |
| SEA-AD raw 10x snRNA/snATAC/Multiome + harmonized IAC individual-level resources | **CONTROLLED** | NO |
| GSE174367 Morabito processed snRNA/snATAC | **OPEN GEO** | **YES** |
| GSE214979 same-nucleus Multiome processed matrix, metadata, fragments | **OPEN GEO** | **YES** |
| GSE272082 Multiome processed files / GEO archive | **OPEN GEO** | **YES** |
| ROSMAP 2025 multiregion snATAC/snMultiome (syn66271521/syn66271522) | **CONTROLLED; DUA REQUIRED** | **NO** unless access is already approved |
| ROSMAP predecessor multiome / PFC study | **CONTROLLED; DUA REQUIRED** | NO |
| ROSMAP GAGE-seq syn66400203 | **CONTROLLED; DUA REQUIRED** | NO |
| HVS raw WGS | **RESTRICTED NeMO/NDA** | NO |
| Kosoy human microglia regulome | **MIXED**: some derived processed products are open-distribution; individual-level/raw data are governed by AD Knowledge Portal access requirements | Only for the explicitly open derived products |

**Planning consequence:** do not put ROSMAP on the immediate execution critical path unless the user already has approved ROSMAP/AD Knowledge Portal access. The immediate public-data path is SEA-AD processed data + GSE214979 + GSE272082 + the already-local Morabito resource.

The exact SEA-AD same-nucleus linkage also needs an access check: the Allen portal makes processed RNA/ATAC public, while raw 10x Multiome is controlled. Do not assume that the open processed files expose every identifier needed for exact RNA↔ATAC nucleus pairing; prove that from public metadata first. If they do not, record PAIRING_REQUIRES_CONTROLLED_METADATA rather than requesting or using protected data implicitly.

## A. FULL104 sources

### 1. SEA-AD — highest-priority internal cross-modal opportunity

**Current project use:** RNA matrices across 11 regions; 46 FULL104 reader-fit donors and 4,118,213 reader-fit nuclei.

**Official SEA-AD modalities now available:**
- snRNA-seq
- snATAC-seq
- **10x Multiome RNA + ATAC from the same nucleus**
- MERFISH / Vizgen MERSCOPE spatial transcriptomics
- 10x Xenium spatial transcriptomics
- quantitative neuropathology images and measurements
- postmortem MRI volumetrics
- whole-genome sequencing and SNP array genotypes
- clinical / cognitive / neuropathology metadata

The 2026 SEA-AD release explicitly states that its gene-expression data include both singleome RNA and Multiome GEX. The public microglia release likewise states that singleome RNA and Multiome GEX were aligned separately with Cell Ranger and Cell Ranger ARC.

**Critical unresolved project question:** we have not yet proved, row by row, which FULL104 SEA-AD nuclei came from singleome RNA libraries versus Multiome libraries. Therefore we must not yet claim that a given FULL104 nucleus already has paired ATAC.

**Immediate action:** use exact SEA-AD cell/library identifiers to build a metadata-only map:
`FULL104 SEA_AD selection_row -> SEA-AD cell_id -> library_prep -> assay_origin {snRNA, multiome-GEX} -> paired ATAC availability`.

Do this before downloading new biology, and firewall pathology/cognitive columns during the join.

Primary/public sources:
- SEA-AD data portal: https://brain-map.org/consortia/sea-ad/our-data
- Nature Neuroscience 2024: DOI 10.1038/s41593-024-01774-5
- SEA-AD controlled raw study: Synapse `syn26223298`
- SEA-AD WGS/SNP: NIAGADS `NG00174`

### 2. HVS — transcriptome + genetics, not paired ATAC

**Current project use:** snRNA-seq from 41 reader-fit donors.

Public Human Variation Study (Science 2023) generated:
- snRNA-seq
- **whole-genome sequencing**

The full published study contains 75 neurosurgical donors. FULL104 uses a subset and must retain its own frozen donor identity.

**Value for current problem:** WGS is an orthogonal causal/genetic layer and can support eQTL/genotype-linked plausibility, but it does not provide same-cell technical separation analogous to Multiome.

Source: Science 2023, DOI 10.1126/science.adf2359; NeMO project “A Multimodal atlas of human brain cell types: Human variation RNAseq & WGS (Lein)”.

### 3. NPH52 — transcriptome + pathology/CSF/physiology, no paired ATAC found

**Current project use:** snRNA-seq from 17 reader-fit donors.

Original Cell 2023 cohort:
- 52 living NPH biopsy donors
- snRNA-seq
- tissue amyloid / phospho-tau histopathology
- CSF biomarker / clinical context
- independent acute-slice physiology used in the study

No same-nucleus ATAC/Multiome companion has been verified for the original NPH52 cohort.

These non-RNA layers are biologically valuable but are not replacements for a same-nucleus RNA/ATAC identification test.

Source: Cell 2023, DOI 10.1016/j.cell.2023.08.005.

---

## B. External multimodal resources already in project history

### 4. GSE174367 — Morabito/Swarup

**Project status:** physically authenticated and already present in the project; do not re-download or re-authenticate.

Modalities:
- snRNA-seq
- snATAC-seq
- bulk RNA-seq

RNA and ATAC are **different nuclei from the same donor cohort**, not same-nucleus pairs.

Project-authenticated useful scope:
- 18 shared RNA/ATAC donors
- 4,126 microglial RNA nuclei
- 12,232 microglial ATAC nuclei
- full ATAC matrix 219,070 peaks × 143,401 nuclei

**Role now:** donor-level orthogonal replication. It cannot by itself provide cell-by-cell RNA↔ATAC correspondence.

### 5. GSE214979 — same-nucleus DLPFC Multiome

**Project status:** pairing/authentication completed in PR #182; biological evaluation not executed.

Public deposit:
- 105,332 nuclei
- 7 AD + 8 control donors
- same-nucleus snRNA + snATAC
- 10x Multiome

Project audit additionally identified donor-label conflicts and froze exclusions; do not silently restore those donors.

**Role:** excellent cell-level technical-development dataset, but small donor N.

The GSE214637 SuperSeries also contains a small ChIP-seq companion (GSE214911; ZEB1/MEF2C-focused), useful only as targeted regulatory context, not cohort-wide validation.

### 6. GSE272082 — sEOAD Multiome

**Project status:** accession authenticated prospectively; cell-type census still requires acquisition.

Public deposit:
- >70,000 nuclei
- 4 sEOAD + 5 controls
- PFC, EC, HIP
- 10x Chromium Multiome ATAC + Gene Expression
- Cell Ranger ARC output

**Role:** useful second same-nucleus technical replication, but n=9 donors is too small for strong donor-level claims.

**Acquisition rule:** download filtered matrices / metadata first; do not fetch the entire raw archive merely to establish the microglial subset.

---

## C. High-value multimodal resources not yet integrated

### 7. ROSMAP multiregion epigenome + Multiome — top independent candidate

Cell 2025 study:
- **111 individuals**
- 384 postmortem samples
- six regions
- 799 single-nucleus libraries across snRNA, snATAC and snMultiome
- 1,217,165 QC snATAC nuclei
- 2,263,395 QC snRNA nuclei
- **288,480 nuclei with paired high-quality snRNA + snATAC**
- 67 cell subtypes including microglia/immune states

Data:
- snATAC: Synapse `syn66271521`
- snMultiome: Synapse `syn66271522`
- prior PFC study: `syn52293417` — **subsumed, not an independent replication**

**Access:** controlled AD Knowledge Portal / ROSMAP DUA.

**Role:** strongest independent paired-RNA/ATAC candidate currently identified because it combines same-nucleus pairing with much larger donor N than GSE214979/GSE272082.

Source: Cell 2025, DOI 10.1016/j.cell.2025.06.031.

### 8. Kosoy et al. human microglia regulome — donor-level microglia-specific orthogonal layer

Nature Genetics 2022:
- primary human microglia from 150 donors
- transcriptome and chromatin-accessibility profiling
- project registry records RNA n=127, ATAC n=107, both n=88 from the publication
- Hi-C available on a small subset
- genotype/regulatory analyses

Data lead: AD Knowledge Portal `syn26207321` (controlled).

**Role:** exceptionally relevant microglia-specific donor-level regulatory evidence. Not single-cell paired, so it cannot test a cell-level JEPA state directly.

Source: DOI 10.1038/s41588-022-01149-1.

### 9. ROSMAP GAGE-seq — same-nucleus RNA + 3D genome

Science 2026 study:
- 20 ROSMAP PFC donors: 10 AD + 10 non-AD
- 23,825 nuclei
- **joint RNA expression + single-cell 3D genome contacts from the same nuclei**
- the same 20 donors also have snATAC in the recent ROSMAP AD study
- Xenium spatial data used as an additional comparison layer

**Role:** highly orthogonal mechanistic follow-up after RNA/ATAC: if the same state relationship is visible in transcription, accessibility and 3D chromatin organization, a pure RNA-capture explanation becomes substantially less plausible.

Do not count these 20 donors as independent of the larger ROSMAP cohort.

---

## D. Secondary / supporting modalities

- **SEA-AD spatial transcriptomics (MERFISH + Xenium):** different measurement technology and spatial context; valuable third-channel robustness, particularly after cell-type/state definitions are frozen.
- **SEA-AD WGS/SNP:** genetic anchoring on the same donor cohort.
- **HVS WGS:** independent genetic anchoring in living neurosurgical tissue.
- **GSE214637 ChIP-seq companion:** targeted ZEB1/MEF2C regulatory context only.
- **GSE289721:** RNA + CRISPR Guide Capture; valuable perturbational biology, but one genetic background / two differentiations and not a technical-identification replacement.
- **GSE301119:** CRISPRa/CRISPRi transcriptomic perturbation resource; useful causal support, not an orthogonal measurement of the same native state.

---

## E. Acquisition / execution priority

### P0 — no new biological download first
1. Build the **SEA-AD exact assay-origin linkage** for the FULL104 cells already used.
2. Quantify how many existing FULL104 SEA-AD nuclei are Multiome-GEX and therefore have exact paired ATAC counterparts.
3. Use metadata and assay identifiers only. Do not open protected pathology or target outcomes.

### P1 — external identification cohort
4. Prepare/access ROSMAP `syn66271522` paired multiregion Multiome. This is the strongest independent candidate.
5. Use GSE214979 for rapid same-nucleus control development because it is already authenticated by the project.

### P2 — independent complementary checks
6. Reuse Morabito GSE174367 for separate-nuclei donor-level replication.
7. Acquire the minimal filtered-matrix subset of GSE272082 to authenticate microglia and run a second same-nucleus check.

### P3 — mechanistic depth
8. Add Kosoy primary-microglia RNA/ATAC for microglia-specific donor-level regulatory evidence.
9. Add ROSMAP GAGE-seq for same-nucleus RNA↔3D-genome evidence.
10. Add SEA-AD MERFISH/Xenium and WGS only after the cross-modal statistic and exposure firewall are frozen.

---

## F. Required cross-modal specificity gate

Multiome does **not** automatically solve the identifiability problem. Before any biological outcome is interpreted, freeze a control gate that has to:

1. reject independent/null RNA↔ATAC correspondence;
2. reject measured technical/QC-driven shared structure;
3. reject shared nuclear-quality / library-quality synthetic negatives that perturb both modalities;
4. retain a planted cross-modal biological latent positive;
5. report each cohort separately, with donor as the independent unit for cross-donor claims.

Only after that gate is frozen should the real SEA-AD / ROSMAP relational correspondence be inspected.

---

## Bottom line

The project is **not data-starved for orthogonal evidence**. We had been using only a fraction of what is available.

The most valuable sequence is:

`existing SEA-AD Multiome linkage -> cross-modal technical gate -> ROSMAP 111-donor paired Multiome -> GSE214979 / GSE272082 -> Morabito -> Kosoy / GAGE-seq / spatial`

No target is promoted and no training is authorized by this inventory.

`TRAINING=OFF`
