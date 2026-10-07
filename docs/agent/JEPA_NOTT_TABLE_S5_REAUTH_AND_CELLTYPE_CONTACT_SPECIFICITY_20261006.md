# JEPA Nott Table S5 re-authentication and cell-type contact specificity audit — 2026-10-06

Status: documentation-only audit checkpoint. No training, no Stage 4 authorization, no protected Morabito opening, no JEPA target/program gene join, no biological correspondence verdict.

## Exact workbook identity

User supplied `NIHMS1066836-supplement-Table_S5.xlsx` in the active ChatGPT runtime.

- bytes: `36,876,140`
- SHA-256: `81c99689533d9da372cecdd469e7ff02cc985720105b83b3bd66c3ac8c93972e`

This exactly matches the V64 chat-runtime custody manifest and the V63 authentication receipt. This closes the file-identity question for this runtime. The binary remains user-supplied/hash-bound; this checkpoint does not claim the XLSX bytes are stored in Git.

## Workbook structure independently reproduced from the exact XLSX

The workbook contains 12 sheets. The three chromatin-contact sheets reproduce the historical V63 row counts and schema exactly:

| sheet | data rows | schema |
|---|---:|---|
| Microglia interactome | 104,802 | chr1,start1,end1,chr2,start2,end2,count,expected,fdr,ClusterLabel,ClusterSize,ClusterType,ClusterNegLog10P,ClusterSummit |
| Neuronal interactome | 93,290 | same 14-column schema |
| Oligo interactome | 61,895 | same 14-column schema |

No duplicate exact contact rows were found in any of the three sheets after canonicalizing each interaction as an undirected pair of genomic 5-kb bins.

## Same-study cell-type specificity of the physical contact substrate

Before joining any JEPA genes or target programs, exact contact-pair overlap was measured across the three same-study interactomes.

Pairwise exact-edge overlap:

| comparison | shared exact contacts | Jaccard | fraction of first map shared | fraction of second map shared |
|---|---:|---:|---:|---:|
| Microglia vs Neuronal | 19,999 | 0.1123 | 0.1908 | 0.2144 |
| Microglia vs Oligodendrocyte | 17,485 | 0.1172 | 0.1668 | 0.2825 |
| Neuronal vs Oligodendrocyte | 19,964 | 0.1476 | 0.2140 | 0.3225 |

Exact contacts present in all three maps: `9,117`.

Contacts unique to one map relative to the other two:

- Microglia: `76,435 / 104,802 = 72.93%`
- Neuronal: `62,444 / 93,290 = 66.94%`
- Oligodendrocyte: `33,563 / 61,895 = 54.23%`

## Anchor annotation check inside the same workbook

There are `71,266` unique genomic 5-kb anchors in the microglia interactome. Each anchor was tested for interval overlap against enhancer and promoter annotations from the three same-study cell-type sheets.

Enhancer overlap of microglia contact anchors:

- microglia enhancers: `23,974 / 71,266 = 33.64%`
- neuronal enhancers: `22,751 / 71,266 = 31.92%`
- oligodendrocyte enhancers: `17,916 / 71,266 = 25.14%`

Promoter overlap of microglia contact anchors:

- microglia promoters: `12,598 / 71,266 = 17.68%`
- neuronal promoters: `12,614 / 71,266 = 17.70%`
- oligodendrocyte promoters: `12,493 / 71,266 = 17.53%`

Interpretation: enhancer context carries modest same-study cell-type specificity, whereas promoter overlap is essentially non-discriminatory at this substrate level. Therefore a future specificity statistic should not treat promoter presence alone as evidence of microglial specificity.

## Scientific interpretation

This is useful structural evidence: Nott Table S5 contains substantial cell-type-specific physical-contact structure under a same-study comparison. Therefore the Nott object can support a specificity test that asks whether a prospectively frozen JEPA program is preferentially wired in the relevant cell type relative to neuronal and oligodendrocyte comparators.

This does **not** validate any JEPA target or program. Exact-edge specificity can reflect both biology and interaction-calling power/assay properties, and no target gene, pathway, state or RNA-derived candidate was joined in this audit. The correct current claim is:

`NOTT_S5_AUTHENTICATED__SAME_STUDY_CONTACT_SPECIFICITY_SUBSTRATE_AVAILABLE__NO_PROGRAM_VALIDATION_PERFORMED`

Nott contacts remain physical wiring evidence, not activity, causality, or state-specific expression evidence.

## Governance boundary

- TRAINING=OFF
- Stage A OFF
- Stage 4 NOT AUTHORIZED
- Real NIH-CARD biological correspondence UNOPENED
- TEST sealed
- Morabito protected
- no qualified target winner
- no qualified representation winner

Any future use should freeze the candidate program and the exact specificity statistic before joining program genes to this workbook, and should use the neuronal and oligodendrocyte maps as same-study comparators rather than treating the microglia map alone as positive evidence.
