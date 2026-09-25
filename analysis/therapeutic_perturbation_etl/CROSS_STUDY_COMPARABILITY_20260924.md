# Cross-study comparability matrix — recomputed from authenticated sources

Date: 2026-09-24. Every shared-target figure below is recomputed from each
study's own authenticated guide or target source, not inherited from a catalogue
or a prior document.

## Handoff claims, independently verified

| claim | verdict |
|---|---|
| GSE335887 shares **zero** direct targets with Day-8 | **CONFIRMED** (0) |
| GSE335887 shares **zero** direct gene targets with GSE293118 | **CONFIRMED** — GSE293118 has 6 direct targets, none shared |
| GSE335887 shares **SPI1** with both GSE301119 arms | **CONFIRMED** — CRISPRi 9 guide×donor groups / 102 cells; CRISPRa 7 groups / 97 cells |
| GSE311359 **MAF is nominated only**, not an equivalent intervention | **CONFIRMED** |

## Two findings the handoff does not contain

### 1. Day-8 and GSE301119 share five authenticated direct targets

This is the largest authenticated shared-target set in the collection, and it
was not previously stated:

```
CSF1R  CSF2RA  CSF2RB  TGFBR1  TGFBR2
```

Engagement direction across three independent arms — two labs, two cell models,
two protocols:

```
target     Day-8 CRISPRi   301119 CRISPRi   301119 CRISPRa
CSF1R            -0.181           -0.505           +0.542
CSF2RA           -0.806           -2.274           +1.978
CSF2RB           -0.905           -1.552           +3.188
TGFBR1           -0.454           -1.404           +1.765
TGFBR2           -0.512           -0.774           +1.102
```

**5 of 5 down under interference in both studies; 5 of 5 up under activation.**

What this does and does not establish: it shows the ETL measures target
engagement consistently across independently produced datasets, which is a
pipeline result. It is **not** evidence that downstream transcriptional
responses agree, and it is not biological replication — iTF-MG microglia and
primary macrophages are different cell types, and engagement agreement says
nothing about whether the rest of the transcriptome responds alike.

### 2. The two GSE301119 modalities do not target identical gene sets

```
CRISPRi targets   206
CRISPRa targets   206
union             208
intersection      204
CRISPRi-only      RPL11, RPL7
CRISPRa-only      CDKN2A, TP53
```

PR #91's "206/206 in both donors for each modality" is correct per modality, but
the modalities differ from each other. **A paired CRISPRi/CRISPRa comparison is
possible on 204 genes, not 206.** The four exceptions are biologically
sensible — ribosomal genes tested only for knockdown, tumour suppressors only
for activation — which is why they must not be silently dropped or imputed.

## Nominated is not direct

Counted separately so a reader cannot mistake one for the other:

```
GSE301119 x GSE311359 NOMINATED   5   BIN1, CD86, IFNGR1, IRF5, MERTK
GSE335887 x GSE311359 NOMINATED   1   MAF
GSE178317 x GSE311359 NOMINATED   0
```

A nominated cis gene is an assertion about which gene an element *may* regulate.
It is not an authenticated direct intervention and is never counted as a shared
target. GSE293118's 77 unmatched noncoding elements are treated the same way.

## The matrix

`evidence/cross_study/CROSS_STUDY_COMPARABILITY_MATRIX_V1.csv` carries, per
study: intervention, cell model, protocol and time, biological units, controls,
assay readout, response-outcome exposure, limitation, and authenticated direct
target count.

**A shared gene symbol is not experimental comparability.** Cell model, protocol,
differentiation age, control design and readout all differ across these studies.
Those columns exist precisely so a shared symbol cannot silently license pooling.

## Remaining STOPs, with the exact missing source

**GSE175721** — `STOP_AUTHOR_SOURCE_MISSING`, searched and confirmed today. The
paper is Cakir et al., Nat Commun 2022, PMC8776770. Its only data table,
MOESM10, contains figure source data across 23 `Fig*`/`FigS*` sheets and no
per-cell assignment. The Data Availability statement reads: *"All relevant data
supporting this study are available from the corresponding authors upon
request."* **Exact missing source:** the depositor-described tab-separated
per-cell metadata file carrying the cell-to-guide assignment, from Bilal Cakir /
In-Hyun Park, Yale.

**GSE311359** — `STOP_PENDING_PHYSICAL_V2_REBUILD`. No longer author-blocked:
the authentic feature identity was found in the deposited `features.tsv` column
1. Requires an ID-keyed rebuild, not an external file.

**GSE335887 ARID5B** — no authenticated protospacer in the deposit. **Exact
missing source:** the guide sequences for ARID5B from the publication's
Table S2.

```
TRAINING=OFF · AUDIT_B_N1=UNOPENED · PROTECTED_FULL104_OUTCOMES=UNOPENED
D_SHARED_G5=UNOPENED · THERAPEUTIC_RANKING=OFF
```
