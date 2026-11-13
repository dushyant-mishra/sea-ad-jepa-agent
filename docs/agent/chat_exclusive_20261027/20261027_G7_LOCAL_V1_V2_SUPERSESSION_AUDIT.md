# Local G7 archive inspection V1 → V2: explicit supersession (2026-10-27)

**Authoritative outcome for these inputs:** `INSUFFICIENT_TO_AUTHORIZE_AUTHENTIC_G7_E3`, **not** biological or source verification.

This document preserves a chat-only, two-archive metadata examination that was not previously committed with the project audit. The read-only historical scripts and JSON outputs now exist as individually frozen files under `docs/agent/chat_exclusive_20261027/`:

- `20261027_G7_LOCAL_HEADER_PROBE_V1_SUPERSEDED.py` and `20261027_G7_LOCAL_HEADER_RESULT_V1_SUPERSEDED.json`.
- `20261027_G7_LOCAL_HEADER_PROBE_V2_CORRECTED.py` and `20261027_G7_LOCAL_HEADER_RESULT_V2_CORRECTED.json`.

The original local report PDFs do not exist; the original Markdown report files had separate local SHA256 `6642a9673e7d71ae7314e7858016c682019d06e46fe9d3c6140b00fbbdd33c2f` (V1) and `bcfc9fe5c254f5a038d4a24a02c7a66c5800fc239066014612ae7d1f0e231128` (V2), as registered in the full local-source inventory. This summary retains their scientific findings rather than claiming the exact Markdown bytes were transferred. The uploaded originals can be reacquired by these SHA identities.

## Exactly what the historical probes read

Only ZIP directory entries and bounded CSV headers inside historical `expression.zip` and `FOUNDATION_CALIBRATION_BUNDLE_20260824.zip`. They **did not open** the split 41K ZIP expression payload, checkpoint tensors, source-level RNA raw reads, current physical deciding rows, protected cohorts, or external issuer records.

The expression audit declared:
- 50,000 selected expression rows; 41,238 address features; 35 audited shards.
- Transform `log1p(raw_count*10000/full_source_library)` exactly once. This is **normalized expression**, not independent physical raw-molecule evidence.
- 42 operator metadata CSV headers: `stable_key, cell_id, donor_id, source_library`. The source-library label is not a q-excluded normalizer attestation.
- Sample-freeze header: `sample, sample_row, source, matrix_id, operator_index, local_row, donor_id, cell_id, native_class, broad_class, support_fingerprint, stable_key, in_original_t1, selection_seed, expression_read_before_freeze`. These are **column names only**, not established provenance semantics.

The calibration status declared 50,000 expression sample rows; 6,351,753 metadata rows; 42 operators; no DEV/SEALED expression and no pathology fields. This status is a **source declaration** rather than an independently inspected semantic guarantee.

## Crucial V1 mistake, V2 correction

V1 used the misleading log line `G7_LOCAL_METADATA_PROBE_PASS` and interpreted the mere presence of `expression_read_before_freeze` as a selection field. Neither validates that field's semantics or authenticates source content. V2 changed the log to `G7_LOCAL_METADATA_INSPECTION_COMPLETE__G7_E3_UNQUALIFIED`, renamed the output key to `expression_read_before_freeze_column_present`, and explicitly declined the semantic inference.

**Never accept the V1 result as current G7 PASS.** Keep it as a historical negative example. The two ZIP bundles on their own do not authenticate:
- Physical source/cell/donor/operator/address/read identity, nor independent biological-measurement uniqueness.
- Genuine raw count and per-assay measured-zero/structural-absence/collision/rights-withheld status.
- Actual rights-aware q-excluded denominator and normalization provenance, including when visible library totals retain withheld counts.
- Producer-issued G7 V3 exact deciding-row digest and consumer mapping.

These conclusions are **only about the two inspected archives**. Do not claim rawcount source stores or archived split 41K payloads elsewhere cannot supply the missing evidence; they were outside this particular probe's scope.

## Independent successor consequence

Macha #449 R1/R2 hostile RED therefore remains controlling. PR #470 scoped R3/R4/R5 mechanical improvement cannot cure it. Historical package integrity PR #471 verifies archive bytes but does not transform any archive field into a present-day authenticated issuer. The correct next action is an independently authenticated source/producer for the actual deciding physical rows and query-excluded normalization lineage, not unnormalizing `log1p` as an invented raw-count proof.

**Authority remains** `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`.
