# GSE335887 — metadata-only identity contract; reserved outcomes untouched

Date: 2026-09-24
Scope: **METADATA ONLY.** No `.X`, no assay numerical layer, no differential
expression, no FDR, no expression value was read from any GSE335887 file.

```
guide library                 CONFIRMED FROM SOURCE, and it contradicts the prose
feature-ID -> protospacer     PRESENT, complete, all distinct
antibody panel                180 features, IDs resolved
parental line                 WTC11 for both models - NOT eight donors
model attribution             iMG is cytokine-directed; catalog was wrong
10x chemistry                 series claims v2; NOT run-level confirmed
reserved outcomes             UNOPENED
```

## What was accessed

Only whitelisted identity metadata:

| source | what was read |
|---|---|
| GEO series SOFT record | title, summary, overall design, sample ids |
| GEO sample SOFT records | title, source, cell line, growth/extract protocol, instrument, processing |
| `GSE335887_itf_feature_reference.csv.gz` | 4,381 B, sha256 `fd2c3fa5b517c81bbd158516dacb00416f1883a654c795e126916620f77f225f` |
| `GSE335887_img_feature_reference.csv.gz` | 4,381 B, sha256 `cbc733178cefa49f660e2728debb834eed4520a3691834ba212102b3a0f6c533` |

**No HDF5 file was opened.** The `.h5mu`, `.h5ad` and `feature_bc_matrix.h5`
assets were listed from the FTP directory and not downloaded, so no HDF5 key
access log is required — the correct log is empty.

## Guide library — confirmed, and the count in circulation is wrong

The feature reference carries the complete authentic chain:
`id`, `name`, `read`, `pattern`, **`sequence`** (protospacer), `feature_type`,
`target_gene_id` (Ensembl), `target_gene_name`.

```
total features            245
  CRISPR Guide Capture     65
  Antibody Capture        180
distinct target genes      30   (+ Non-Targeting)
guides per target           2   for all 30
non-targeting guides        5   non-targeting_h3_532, h6_711, h3_594, h5_749, h5_546
unique feature IDs        245   all distinct
unique protospacers        65   all distinct
targets carrying Ensembl   30
```

So the library is **30 targets x 2 guides + 5 non-targeting = 65**, not
"31 targets x 2 guides plus NTCs".

### The 31st target is ARID5B, and it has no deposited guides

```
GEO deposited guide targets                30
CRISPRbrain screen targets                 31
in CRISPRbrain but NOT in the GEO library  ARID5B
in the GEO library but not in CRISPRbrain  (none)
```

`ARID5B` appears nowhere in either feature reference. The deposit is internally
inconsistent about this: the sample extract protocol states the library was
*"generated targeting 31 genes"*, while the deposited feature reference contains
30 with guides.

**Consequence.** Under the rule that intervention identity requires an authentic
feature-ID to protospacer to target map, **ARID5B currently has no authenticated
protospacer evidence in this deposit** and must be excluded from any
source-audited cross-study target set, or sourced independently from the
publication's Table S2. Every statement of the form "the 31 shared targets"
should be read as 30 authenticated plus one unevidenced.

The 30 authenticated targets:

```
ARID2 ATMIN BHLHE40 BHLHE41 BPTF CEBPD CNOT10 DEAF1 DNMT1 FOXK1 IRF9 MAF
MEF2C MEF2D MITF POU5F1 PRDM1 RELA RUNX1 SALL4 SMAD3 SPI1 SREBF1 STAT1
STAT2 TCF4 ZNF148 ZNF532 ZNF644 ZNF783
```

### The two models share one library, exactly

The iTF and iMG feature references are **row-for-row identical**: same 245
features, same 65 guide IDs, same protospacers. Library identity is therefore
not a confounder between the two models. Their differing SHA-256 reflects gzip
container bytes, not content.

## Antibody panel — IDs resolved

```
antibody features          180
unique antibody IDs        180   TotalSeq A-series catalog ids (A0006, A0007, ...)
unique display names       180
unique barcodes            180
duplicated display names   none
```

Examples: `A0006` CD86, `A0007` PD-L1, `A0020` HVEM, `A0023` PVR, `A0024`
Nectin-2, `A0026` CD47, `A0031` CD40.

The series summary says "~180 surface proteins", and the panel is exactly 180.
The 167 protein labels previously reported as shared between the two screens is
therefore a property of the analysed output, not of the panel; 13 panel
antibodies do not appear in that shared set and the reason is not established
here. **No cross-assay protein comparison should use display names**; the
catalog ID and barcode are the identity, and they are now available.

## Experimental identity

```
parental line        WTC11 for every sample, both models
models               iTF-MG  six-TF doxycycline-induced (Draeger et al. 2022)
                     iMG     cytokine-directed (McQuade et al. 2018)
vector               CROP-seq pMK1334
timepoint (series)   Day 12, ~20,000 microglia
processing           kb-python v0.29.1 (kallisto-bustools), GRCh38 / hg38
instrument           Illumina NovaSeq X
```

Two prior claims are settled against the source:

1. **The eight GSM accessions are not eight donors.** Every sample records
   `cell line: WTC11`. They are assay libraries from one parental line.
2. **The CRISPRbrain catalog is wrong to call iMG TF-derived.** GEO and the
   sample titles state cytokine-directed differentiation. PR #117's correction
   is confirmed from the primary record.

## Unresolved, and deliberately not guessed

* **10x chemistry.** The series overall design states `10X Chromium (v2)`. That
  is a series-level prose claim, not run-level evidence, and processing was done
  with kb-python rather than Cell Ranger, so no Cell Ranger chemistry field is
  available to corroborate it. **Not resolved.** Any chemistry-adjusted
  attribution must wait for authentic run-level evidence.
* **Differentiation/preparation census.** The number of independent
  differentiation preparations per model is not established by the metadata read
  here. Protocol and differentiation age change together between iTF-MG and iMG,
  so their effects are not separately identifiable, and this remains a
  within-WTC11 protocol-plus-age comparison rather than donor or study-external
  replication.
* **The 13 panel antibodies absent from the shared 167.**

## Exposure

No response value was read. The only CRISPRbrain access in this work read the
**target-identity column** of the 31-target screens to compare target sets; no
`Log2FC`, `P Value` or `FDR` value was displayed or computed. That access is
narrower than the aggregate self-gene QC counts already declared on
2026-09-24 and adds no new outcome exposure.

GSE335887 response profiles remain `UNOPENED_RESERVED`.

```
TRAINING=OFF · AUDIT_B_N1=UNOPENED · PROTECTED_FULL104_OUTCOMES=UNOPENED
D_SHARED_G5=UNOPENED · THERAPEUTIC_RANKING=OFF
```
