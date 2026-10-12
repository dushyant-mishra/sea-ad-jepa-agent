# GSE272082 pairing-authentication delta

Date: 2026-10-12  
Status: `PAIRING_BY_PROTOCOL_CONFIRMED__BARCODE_LEVEL_PAIRING_AND_MICROGLIA_CENSUS_PENDING`

## What was verified

Public GEO and the associated Science Advances paper confirm that GSE272082 is a human single-nucleus multiome study generated with the 10x Chromium Single Cell Multiome ATAC + Gene Expression protocol and processed with Cell Ranger ARC v2.0.2.

The GEO Series currently contains 42 samples covering matched ATAC and GEX entries under the same donor/library identifiers, with >70,000 nuclei from nine donors across prefrontal cortex, entorhinal cortex and hippocampus. The public study summary reports four sEOAD and five control donors. Disease labels are not used anywhere in V79 synthetic tuning.

Representative GEX and ATAC sample pages both state that Cell Ranger ARC jointly aligned/quantified snRNA-seq and snATAC-seq from the same multiome library protocol. GEX entries expose filtered/raw feature-barcode H5 files; ATAC entries expose fragment files.

## What is not yet physically verified

This audit did not download the 35.5 GB GEO RAW archive or compare barcode sets across every matched GEX/ATAC deposition. Therefore exact barcode-level RNA↔ATAC pairing is not promoted to `VERIFIED_SAME_NUCLEUS` here.

A microglia-specific cell census was also not reconstructed from the deposit in this pass.

Prior project concerns about sample/disease-label inconsistencies are therefore not overwritten by the public high-level study summary; they remain provenance issues for any later deciding use.

## Synthetic-lane role

GSE272082 may be treated as:

`PAIRED_MULTIOME_BY_PROTOCOL_AND_SAMPLE_ID__SECONDARY_VALIDATOR_PENDING_BARCODE_LEVEL_AUTH`

It may inform assay geometry and secondary future validation design. It must not be used as deciding same-nucleus validation until exact barcode-level pairing and the relevant cell-type census are authenticated.

No reacquisition or new ETL is justified unless this secondary validator becomes decision-relevant after the primary GSE214979 route.
