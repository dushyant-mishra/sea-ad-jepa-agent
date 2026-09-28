# V49 SEA-AD exact Multiome-linkage preflight

Status: `PROSPECTIVE_METADATA_ONLY__DO_NOT_OPEN_PATHOLOGY__NO_TRAINING_AUTHORITY`

## Question

Which SEA-AD nuclei already present in FULL104 came from 10x Multiome GEX libraries and therefore have a same-nucleus ATAC measurement available?

Do **not** infer this from donor membership. Prove it per nucleus / library.

## Inputs allowed before biological outcome access

1. frozen FULL104 SEA-AD cell identity / selection-row map;
2. official SEA-AD cell metadata containing only identifiers required for assay provenance;
3. official Multiome library manifest / library-prep identifiers;
4. ATAC barcode/library index needed to establish counterpart existence.

Explicitly exclude disease/pathology/cognition columns from the working table.

## Required output columns

- `selection_row`
- `full104_donor_id`
- `full104_source = SEA_AD`
- `seaad_cell_id`
- `barcode`
- `library_prep_id`
- `ar_id` or frozen donor/library join identifier
- `rna_assay_origin ∈ {SINGLEOME_RNA, MULTIOME_GEX, UNKNOWN}`
- `paired_atac_counterpart ∈ {TRUE,FALSE,UNKNOWN}`
- `atac_counterpart_key`

No expression value, ATAC peak value, pathology value or target outcome belongs in this table.

## Fail-closed rules

- one FULL104 nucleus must map to at most one SEA-AD cell id;
- a Multiome-GEX call requires an authenticated Multiome library identifier;
- paired-ATAC TRUE requires the exact same nucleus/barcode-library identity, not merely same donor;
- unmatched or ambiguous identities are UNKNOWN, never FALSE or biological zero;
- any donor/pathology field accidentally entering the output beyond the minimum identity join must fail the producer;
- report counts by region/library/donor but do not inspect target relational outcomes.

## Deliverable

A SHA-bound receipt with:
- total FULL104 SEA-AD nuclei checked;
- exact unique matches;
- singleome RNA count;
- Multiome-GEX count;
- exact paired-ATAC count;
- unknown/ambiguous count;
- donor coverage of the paired subset;
- source-file digests and producer digest.

Only after this receipt is audited should ATAC values be opened for the cross-modal specificity gate.
