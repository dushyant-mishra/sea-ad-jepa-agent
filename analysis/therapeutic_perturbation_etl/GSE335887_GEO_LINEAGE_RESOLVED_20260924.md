# GSE335887 primary-source physical sample provenance — V2 (2026-09-24 ET)

Authority: **public GEO SAMPLE METADATA**, not experimental response. Supersedes this lane's earlier assumption that donor/line provenance was wholly unavailable. This metadata does not independently authenticate a cross-experiment effect or biological uncertainty. Source: [GSE335887](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE335887), public GEO family SOFT, original gzipped source SHA-256 `bbd48241a687edc5bfd78b518520bf7b04228901bb4a067f7b02170c9a85bf71`, 6,747 bytes. CI [run 36085974625](https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions/runs/36085974625), full 8-sample JSON artifact `GSE335887-PUBLIC-METADATA-ONLY`, ID 10843801776, 36,698-byte JSON SHA-256 `498464c29033e05b128bc044e62b19e757b0498944f9c31ef49f4a028ba496a3`. Physical GEO parser skipped numerical expression tables, and all metadata-firewall adversaries passed after correcting a faulty *test fixture*.

**Resolved source identity:** all eight GSE335887 assay-library accessions explicitly record **WTC11** as their parental iPSC cell line. Eight GSMs are **NOT eight biological replicates**. This experiment tests TF-directed (iTF-MG, Day 12) versus cytokine-directed (iMG, Day 28) differentiation from the same parental cell-line background, *not donor-to-donor or independent-study transport*. Differentiation protocol and collection stage are jointly changed; their effects cannot be isolated by this two-arm design.

| GSM | Source name | Library | Recorded processed grouping |
|---|---|---|---|
| GSM9822530 | WTC11 iTF-MG | CITE ADT | `iTF_processed_cite_crop.h5mu` |
| GSM9822531 | WTC11 iTF-MG | paired CROP GEX | same paired h5mu |
| GSM9822532 | WTC11 iTF-MG | guide enrichment | same paired h5mu |
| GSM9822533 | WTC11 iMG | CITE ADT | `iMG_processed_cite_crop.h5mu` |
| GSM9822534 | WTC11 iMG | paired CROP GEX | same paired h5mu |
| GSM9822535 | WTC11 iMG | guide enrichment | same paired h5mu |
| GSM9822536 | WTC11 iTF-MG | second CROP GEX | `iTF_processed_merged_crop.h5ad` |
| GSM9822537 | WTC11 iTF-MG | second CROP guide enrichment | same merged h5ad |

Peer-reviewed source: [McQuade et al., *Neuron*, published July 29, 2026](https://doi.org/10.1016/j.neuron.2026.07.001) explicitly reports 31 targets ×2 sgRNAs plus 5 NTCs = 65 pooled elements, both protocols harvested on the same calendar day, and **two separately differentiated/stained/sequenced iTF CROP preparations** whose expression effects were subsequently *merged*. The public metadata reveals one iMG paired CITE/GEX/guide library group; independent iMG preparation count beyond that group is **NOT_VERIFIED**. Do not treat iTF CROP and paired iTF CITE as independent expression/protein biological replication, or treat paired iMG CROP and iMG CITE as independent experiments.

**Source-document errors and technical ambiguity:** CRISPRbrain's iPSC-Microglia CITE screen description incorrectly calls the iMG preparation six-TF driven; the GSE335887 accession, detailed sample metadata, and peer-reviewed paper identify iMG as cytokine-directed. Older catalog descriptions also disagree on 10x chemistry with newer publication versus GEO overall-design prose; record chemistry as **CONFLICTING_SOURCE_DESCRIPTIONS** pending read-group / FASTQ / Cell Ranger or exact laboratory manifest, do not choose the preferred version. The paper describes a ~180-antibody reagent panel, while the processed shared CITE measurement universe is 167 literal labels (170 each before intersection); selection/filtering and exact antibody IDs require an assay-specific manifest.

**Scope ruling:** the physically verified 31/31 shared targets and 13,489 shared RNA labels identify a *within-parental-line, cross-differentiation-protocol candidate*. Study accession and independent parental-line axes are shared; the aim cannot be independent external replication. Its published CROP profiles have not been viewed by this lane beyond metadata labels; protect their transcriptome-wide DE outcomes until an explicitly constrained, frozen protocol comparison is authorized.

Next: freeze and authenticate original Table S2 guide protospacer map; authenticate replicate assignment in processed `h5ad/h5mu` without reading outcomes, preserve biological grouping; resolve HGNC/Ensembl source release; physically bind gene/protein assay panels and chemistry before any model/transport claims.
