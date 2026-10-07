# JEPA Project Library expression-axis archaeology — 2026-10-07

Status: documentation-only audit checkpoint. No training, Stage A execution, protected outcome access, or target promotion.

## Why this checkpoint exists

A broader Project/Library search was performed after recognizing that prior archaeology had focused too heavily on GitHub plus chat uploads. The goal was to recover evidence relevant to the historical 41,238-column expression-axis identity and the known risk that gene/address identities could become detached from RNA values.

## Newly recovered historical evidence from Project/Library

### 1. Frozen 41,238-address registry exists
Historical Project/Library material records the Stage81A2R freeze at commit `95d2cafe5cde68773f81c4aa64afc5788ae1d73b` and specifically lists:

- `results/v4/stage81a2r_foundation_molecular_address_registry_candidate.csv`
- `results/v4/stage81a2r_foundation_molecular_address_measurement_support_candidate.csv.gz`
- `results/v4/stage81a2r_foundation_molecular_address_injectivity_audit.json`
- `results/v4/stage81a2r_foundation_molecular_address_source_provenance_candidate.csv.gz`

The registry has 41,238 rows with fields including:

- `molecular_address_index`
- `molecular_address_id`
- `identity_class`
- `current_ensembl_gene_id`
- `legacy_source_exact_id`
- `source_native_anchor`
- `symbol`
- `biotype`

Historical closure states that the final distinct universal molecular-address count is exactly 41,238 with zero exact cross-layer or within-layer duplicate equivalence classes.

### 2. Matrix-specific feature mapping sidecars exist
Historical Project/Library material records per-dataset feature-order hashes and mapping sidecars. One concrete example is:

`data/processed/v4/pre_stage81a2/mappings/feature_universe_a7391464dbde2f15.csv.gz`

with columns:

- `source_feature_index`
- `source_feature_id`
- `source_symbol`
- `source_stable_id`
- `canonical_symbol`
- `canonical_stable_id`
- `mapping_method`
- `mapping_status`

This establishes that the project had machinery for binding source feature positions to canonical molecular identities, rather than relying on gene-name joins alone.

### 3. Measurement-support table binds address index and address identity
Historical material shows the measurement-support object has columns including:

- `matrix_id`
- `source_dataset_id`
- `molecular_address_index`
- `molecular_address_id`
- `identity_class`
- `measured_address`
- `measurement_status`
- `measurement_provenance_key`
- `source_feature_universe_hash`
- `molecular_address_registry_semantic_hash`

This is highly relevant to the historical gene-ID/RNA-value jumble risk.

### 4. Later F1 repair explicitly solved positional expression-address binding
Project Library contains `derive_contextual_target_f1_querydesign_repair_v2.py`, which requires:

- namespace length == 41,238;
- program-weight address order == canonical namespace address order;
- observation-state `molecular_address_index == arange(41238)`;
- operator index canonical;
- every expression block width == 41,238.

It emits `F1_ADDRESS_NAMESPACE_BINDING.csv` with one row per position binding:

- `position`
- `canonical_address_id`
- `program_weight_address_id`
- `observation_state_address_index`
- `expression_interface_column`
- `tokenizer_gene_id`
- reporting-only symbol

and records `expression_interface_column = position` and `tokenizer_gene_id = position` after the ordered checks pass. It also pins the production expression materializer path/hash and level-4 block-manifest hash.

This proves the project eventually closed this class of positional-identity bug for the later full-expression interface.

## What this does NOT yet prove

The authenticated historical discovery expression archive is now known exactly:

- outer archive SHA-256 `63239898b9c93f29c20b62b84dc9b94c2c87e3e3f2b7958b7435847e3b9541f7`
- inner 50,000 x 41,238 NPZ SHA-256 `4c50f1de2446b07bbf3199bba80ebc89749c8104cb7668664ed705dbfc579d92`

The recovered original TD34 producer assumes sparse-matrix column index `j` is Molecular Ledger address index `j`.

The Project/Library archaeology above shows that a canonical 41,238-address registry and matrix-specific feature-order machinery existed, and that a later F1 path explicitly proved expression-column identity. However, this checkpoint has NOT yet recovered a direct execution receipt or producer binding the exact historical 50K NPZ hash `4c50f1de...` to the frozen Stage81A2R ordered address registry.

Therefore the current classification remains:

`TD34_PANEL_SELECTION_GENEALOGY_RECOVERED__HISTORICAL_50K_EXPRESSION_COLUMN_TO_ADDRESS_BINDING_NOT_YET_DIRECTLY_PROVEN`

and TD41/TD43 numerical biology remains scientific-interest evidence only until this exact bridge is recovered or independently reconstructed from primary producer provenance.

## Strongest next search targets

Search Project Library, GitHub history, and local machine for any of:

1. the producer/materializer that created the exact `4c50f1de...` 50K NPZ;
2. a receipt/manifest for that NPZ containing `feature_order_sha256`, `molecular_address_registry_semantic_hash`, or ordered address IDs;
3. historical local manifests under the 2026-09-09 handoff family, especially:
   - `JEPA_HANDOFF_SMALL_ARTIFACTS_20260909_FINAL_R2.zip`
   - `JEPA_LOCAL_FILE_MANIFEST_20260909_FINAL.csv`
   - `JEPA_LOCAL_FILE_MANIFEST_20260909_FINAL.json`
   - `JEPA_NEW_CHAT_HANDOFF_20260909_FINAL_R2.md`
   - `JEPA_NEW_CHAT_HANDOFF_STATE_20260909_FINAL_R2.json`
   - `SHA256SUMS_FINAL_R2.txt`
   - `jepa_r2_recovered/`
4. the Stage81A2R registry/injectivity/provenance files listed above if available as physical local files.

## Governance

- Training OFF.
- Stage A execution OFF.
- Protected outcomes remain closed.
- No target winner.
- No representation winner.
- TD41/TD43 are not promoted by this archaeology.
- Later F1 positional-binding success must not be retroactively assumed for the earlier 50K discovery NPZ without an explicit lineage bridge.
