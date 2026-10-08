# Cross-study gene identity authority — 2026-09-24

Status: DESIGN FROZEN / PHYSICAL ANNOTATION BYTES NOT YET AUTHENTICATED.

## Canonical project gene key

Use **unversioned Ensembl human gene ID** (`ENSG...`) as the canonical
cross-study key.

Always retain the study's original identifier and namespace. Accepted source
namespaces are:

- HGNC approved symbol
- Ensembl gene ID (versioned or unversioned)
- NCBI Entrez Gene ID

Never replace the original source identifier in place.

## Why this matches existing project history

The current `cross_study_feature_contract_v1.py` already implements this
architecture. It maps every accepted source namespace to one canonical
unversioned Ensembl ID, rejects unmapped genes, rejects duplicate canonical
collisions, distinguishes structurally unmeasured from assayed-undetected, and
does not guess aliases.

The missing production authority is the external frozen annotation release.

## Frozen annotation sources to acquire and hash

1. HGNC archived complete set: **2026-07-07 quarterly snapshot**.
   Required fields include HGNC ID, approved symbol, previous/alias symbols,
   Entrez ID and Ensembl gene ID.
2. Ensembl **release 116 (June 2026), human GRCh38.p14** for canonical Ensembl
   gene IDs and current gene annotation.

These are proposed authority roots, not yet authenticated project artifacts.
Download once, record exact byte SHA-256 and file size, then build the mapping
table only from those frozen bytes.

## Mapping rules

1. Direct Ensembl ID -> strip only a validated version suffix.
2. Approved HGNC symbol -> map only through the frozen HGNC record.
3. Entrez ID -> map only through the frozen HGNC record.
4. Previous/alias symbols -> REVIEWED_ALIAS only when the frozen record maps
   uniquely to one current HGNC record and one Ensembl gene ID.
5. One source ID mapping to multiple genes, or multiple source IDs collapsing
   to one canonical gene within the same study -> STOP for manual/versioned
   resolution.
6. Unmapped features are recorded in a source-specific NOT_MAPPED inventory;
   they are never silently dropped.
7. Cross-study matrices use a full union plus explicit assay masks. Missing
   feature != measured zero.

## Production gate still required

No real cross-study benchmark should run until the exact HGNC and Ensembl files
are present, hashed, and a frozen mapping receipt records:

- annotation release names
- source file SHA-256 values
- every input namespace
- mapped/unmapped counts per study
- alias resolutions
- collision inventory
- final mapping-table SHA-256

TRAINING remains OFF; this contract is nomenclature authority only.
