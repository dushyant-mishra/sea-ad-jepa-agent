# V64 unrestricted regulatory resource registry

**Date:** 2026-09-30  
**Status:** access/licensing reconnaissance only; no external resource ingested

This registry exists to enforce the project's rule:

> **Access status and license/terms status are separate facts.**

The core architecture should remain reproducible without a new DUA, dbGaP approval, EGA approval, or controlled individual-level GTEx access.

## Strong open core

### FANTOM5
Direct public downloads. FANTOM states FANTOM5/FANTOM6 data by RIKEN are licensed CC BY 4.0.

Role: promoter/TSS activity evidence.

### GENCODE
The official data-access page states all GENCODE project data are open access and directly available.

Role: base annotation-defined candidate transcript/TSS universe.

Conservative terms note: the registry does not infer a per-file data license merely from the CC-BY license on GENCODE publications.

### eQTL Catalogue
Direct FTP access. The official licence page states all catalogue data are CC BY 4.0 and code is Apache 2.0.

Role: genetic association/fine-mapping evidence.

### Dong/Roussos multi-region brain atlas supplementary material
The open article is CC BY 4.0, including material covered by that license unless separately credited.

Role: brain promoter-isoform and promoter-resolved enhancer-link evidence.

## Public resources whose data licence should remain conservative

### SCREEN / ENCODE cCRE registry
SCREEN states all data are publicly available to download. MIT notices were found for cCRE pipeline code, but that is not treated as proof of the data license.

Record:
- access = PUBLIC_DOWNLOAD
- data terms = NOT VERIFIED

Role: standardized cCRE coordinates/classification, not independent confirmation of activity.

### Nott processed regulatory files
Publicly downloadable, but the project already records reuse terms as unknown.

Record:
- access = PUBLIC_DOWNLOAD
- terms = UNKNOWN

Do not silently upgrade this to open-license status.

### GEO datasets
GEO states public records can be accessed/downloaded without login. Public repository access is not, by itself, recorded here as an explicit reuse license.

Use dataset/paper-specific terms where available.

## Open estimator code

### SCARlink
Public repository with MIT license.

### SCENT
Package DESCRIPTION states `License: MIT + file LICENSE`.

These are software licenses. When both are run on the same NIH-CARD paired cells, they remain different estimators of one paired-observational evidence family.

## Architecture rule

No resource enters the core because it is merely convenient to download.

For each resource actually ingested later, record:
- version/release;
- exact downloaded artifact;
- SHA-256;
- recovery locator;
- access status;
- license/terms status;
- genome build;
- mapping receipt if converted.

## Governance

No download or ingestion is authorized by this registry alone.
Training remains OFF.
