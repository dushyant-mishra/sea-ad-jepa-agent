# Real B2 output schema requirements — 2026-09-09

The real raw-source population authority artifact should be machine-readable and replayable.

## Required top-level fields

- `schema`
- `source_sha256`
- `source_bytes`
- `logical_row_authority_root_sha256`
- `population_raw_source_root_sha256`
- `rows_expected`
- `rows_attempted`
- `rows_proven`
- `skipped_rows`
- `duplicate_logical_indices`
- `mismatch_counts`
- `proofs`
- `pathology_values_read`
- `real_execution_ready`

## Required proof fields

Each proof must contain:

- `logical_index`
- `expression_row`
- `canonical_cell_id`
- `donor_id`
- `source_library`
- `stored_values_in_row`

## Required mismatch fields

- `cell_id_mismatch`
- `donor_id_mismatch`
- `expression_row_mismatch`
- `source_library_mismatch`
- `source_digest_mismatch`

All must be zero for acceptance.

## Required manifest fields

For every emitted file:

- filename;
- bytes;
- sha256.

The package root must be computed from these emitted bytes.
