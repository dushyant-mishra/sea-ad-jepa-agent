# FULL104 dataset ETL and composition atlas — 2026-09-21

Status: `CURRENT_FULL104_RECONNAISSANCE__DATASET_DESIGN_INPUT__NOT_MODEL_INPUT_AUTHORITY`

This package is the reproducible dataset-understanding lane for the current JEPA V5/FULL104 project. It exists because pathology-blind modeling does **not** imply that pipeline designers should be blind to source composition, donor imbalance, brain-region coverage, cell-class schemas, measurement support, collisions, or ETL transformations.

## What is included

- `scripts/extract_full104_dataset_sql_aggregates_v1_20260921.py`: authenticated named SQL aggregation over the 2.7 GB row metadata SQLite.
- `scripts/build_full104_dataset_etl_atlas_v3_20260921.py`: hash-verifying atlas builder over compact SQL aggregates plus support/address authorities.
- `evidence/FULL104_DATASET_ETL_SQL_AGGREGATE_SHA256.csv`: content-addressed manifest for all ten named SQL aggregate caches. The SQL CSVs are reproducible intermediates and are not duplicated in the review tree; rerun the extractor to recreate them byte-for-byte.
- `evidence/`: V3 machine-readable atlas, compact final tables, and output SHA manifest.
- `FULL104_DATASET_ETL_ATLAS_REPORT_20260921.md`: narrative interpretation of the machine evidence.
- `FULL104_DATASET_ETL_REPRODUCIBILITY_RECEIPT_V1.json`: independent fresh-replay receipt.
- `environment/`: exact inventory and role classification for heavy/local artifacts available in the chat environment.
- `FULL104_DATASET_ETL_GITHUB_CONTENT_MANIFEST_20260921.csv`: content manifest for the committed review package.

## Authenticated heavy inputs (reference only)

- `FOUNDATION_CALIBRATION_BUNDLE_20260824.zip`
  - bytes: `410278055`
  - SHA-256: `07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444`
- `metadata/foundation_metadata_rows.sqlite`
  - bytes: `2709786624`
  - SHA-256: `a771f08be31a840b5472448c438a153fbca7de93ba2ed31fe692eaeda02e6913`

Heavy files are not duplicated into GitHub. Reuse requires exact content authentication.

## Reproduction

```bash
python scripts/extract_full104_dataset_sql_aggregates_v1_20260921.py \
  --bundle-root /path/to/foundation_calibration_bundle_20260824 \
  --out-dir /tmp/full104_etl_sql \
  --query-id ALL

python scripts/build_full104_dataset_etl_atlas_v3_20260921.py \
  --bundle-root /path/to/foundation_calibration_bundle_20260824 \
  --sql-cache-dir /tmp/full104_etl_sql \
  --out-dir /tmp/full104_etl_atlas
```

The 2026-09-21 independent replay regenerated all 10 named SQL aggregates plus their manifest byte-for-byte, then regenerated all 13 machine atlas outputs byte-for-byte. The raw SQL aggregate CSVs are therefore treated as reproducible caches; their row counts, byte counts and SHA-256 values are committed in the SQL manifest.

## Important scientific findings

- full metadata: 6,351,753 cells / 149 donors; reader-fit: 4,553,407 cells / 104 donors / 42 operators;
- reader partitions are donor-disjoint;
- reader-fit cell mass is HVS 4.36%, NPH52 5.19%, SEA_AD 90.44%, whereas donor mass is 39.42%, 16.35%, 44.23%;
- operator semantics differ radically by source: HVS/NPH52 operators are native-class-pure; SEA_AD operators are region matrices containing 17–26 native classes;
- SEA_AD donor×region coverage is ragged (2, 3, 9, 10, or 11 regions per donor);
- NPH52 broad-class metadata is absent for all reader-fit cells, so cross-source taxonomy cannot be created by a naïve label join;
- 41,238-address namespace; 17,186 measured by all 42 operators; 17,346 measured by all three source families; 289 measured by no operator;
- exact support geometry has 9 patterns (HVS 1, NPH52 7, SEA_AD 1), making support a strong source-identifying route;
- observation states `MEASURED_SCALAR`, `STRUCTURALLY_UNMEASURED`, and `MEASURED_COLLISION_UNRESOLVED` must remain distinct;
- address identity mapping is heterogeneous (`current_exact`, `legacy_exact`, `source_native_anchored`) and must remain provenance-aware.

## Firewall

Dataset knowledge may inform ETL, sampling, nuisance/decoy design, and interpretation. It must not smuggle pathology or protected outcomes into model-facing selection.

```text
TERMINAL_MASKING_OUTCOMES = UNOPENED
D_SHARED                  = SEALED
PATHOLOGY                  = SEALED
DEV / SEALED              = SEALED
MASKING_POLICY_SELECTED    = NO
G5_MARGIN_SELECTED         = NO
TRAINING_OFF
```
