# JEPA G7 — corrected local attachment source-admissibility probe V2, 2026-10-27

**Disposition:** `INSUFFICIENT_TO_AUTHORIZE_AUTHENTIC_G7_E3`.

This is a bounded, read-only examination of ZIP metadata and CSV headers from the local `expression.zip` and `FOUNDATION_CALIBRATION_BUNDLE_20260824.zip` attachments. It is **not** a re-audit of the immutable historical archive, nor biological source authentication. The split 41K expression ZIP, external upstream data and PyTorch checkpoints were not read or executed. All original donor/cell identifiers are omitted from this report.

## Verified within the two inspected archives

- `expression.zip` contains an expression audit identifying **50,000 selected rows**, **41,238 address features**, **35 audited shards**, and transformation `log1p(raw_count*10000/full_source_library) exactly once`.
- The 42 sampled operator metadata CSVs share the columns `stable_key`, `cell_id`, `donor_id`, `source_library`; those fields permit sample/operator lineage descriptions but do not themselves authenticate molecule-level counts or physical read identities.
- The sample-freeze CSV header exposes `sample`, `sample_row`, `source`, `matrix_id`, `operator_index`, `local_row`, `donor_id`, `cell_id`, `native_class`, `broad_class`, `support_fingerprint`, `stable_key`, `in_original_t1`, `selection_seed`, and `expression_read_before_freeze`. The header has no direct molecular read-evidence, evidence-rights-token, or actual G7 V3 deciding-row-digest columns; the semantics of the `expression_read_before_freeze` column have **not** been verified from its name.
- The calibration status declares **50,000 expression rows**, **6,351,753 metadata cells**, **42 operators**, and `dev_sealed_expression_included=false`, `pathology_fields_included=false`.

## What is *not* established

These two inspected bundles do not independently authenticate a raw physical observation producer with cell/donor/source/operator/address, measured-zero versus unmeasured/collision states, source-specific rights, exact query-excluded raw library depth, and the G7 V3 deciding-row digest and consumer link. The archived expression values are normalized, and `source_library` is not an independently authenticated per-query raw-count measurement. Attempting numerical inversion of a transformed expression value would not be a substitute for a verified raw count/measurement provenance record.

This probe does **not** claim the original raw source cannot exist elsewhere: the split 41K archive contents, upstream source stores, and historical audit indices were intentionally not reopened. It only rejects the inference that **the two inspected local bundles already satisfy** the real G7 E3 source gate.

## Narrow unblock requirement

Locate or obtain an authenticated source/producer that can bind an immutable input identity and exact physical measurement to the eventual G7 V3 deciding-row digest, preserving source-specific measured/structural-absent/collision distinctions and query-excluded depth. Only then qualify the existing real G7 consumer without replacing the provenance gate with regexes, normalization heuristics, or selected-cell sample metadata.

**Global restriction:** `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`.

## Self-audit correction from V1

The original local probe described the mere presence of `expression_read_before_freeze` as a "selection field" and logged `G7_LOCAL_METADATA_PROBE_PASS`. V2 corrects both: **column presence is not semantic provenance**, and successful metadata inspection is **not** a G7 source gate PASS. The original file remains preserved as the historical snapshot. No original ZIP contents were modified, no protected/large split-41K/checkpoint data were read, and no additional biological inference is justified.
