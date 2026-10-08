# FULL104 Metadata Adapter Red-Team Review

**VERDICT: PASS**

## Three strongest findings

1. **The materialized cohort is exact and firewall-clean.** An independent stream of all 42 shards found 4,553,407 rows (HVS 198,718; NPH52 236,476; SEA_AD 4,118,213), 104/104 `reader_fit` donors, no held donor, operators exactly 0–41, no duplicate `(source, canonical_cell_id)`, no malformed/duplicate/non-increasing source locators, and exact equality to all 1,400 donor×operator authority counts. All rows have `LAWFUL_READER_FIT`, `reader_fit`, and `foundation/train`. See `FULL104_ROW_LINEAGE.csv`, `FULL104_METADATA_RECONCILIATION.json`; enforcement is at `scripts/v4/build_full104_production_adapter_metadata.py:122-146,204-221,347-405`.

2. **Quarantines and provenance hold independently.** Recomputing NPH52 from the frozen disposition yielded 288,116 physical TRAIN rows, 265,401 lawful all-149 rows, exactly 22,715 quarantined, and 236,476 lawful fit-104 rows. All seven physical NPH source files match the size/SHA-256 pinned in `nph52_physical_split_source_manifest.csv`. No eligible SEA-AD asset or shard references an immune specialization. All 13 controlling-input hashes and all 47 adapter-manifest entries match; the 42×41,238 state authority has the exact three state names, and every row/shard state hash and operator reference recomputes exactly. See `FULL104_ADAPTER_PROVENANCE.json`, `FULL104_ADAPTER_SHA256_MANIFEST.csv`; checks are constructed at adapter lines 148-175, 253-338, 439-502.

3. **No row fabrication or expression read is evident.** Independent regeneration produced zero lineage mismatches: HVS/SEA-AD rows equal the physical H5AD `obs` donor/cell vectors at each emitted row index; NPH52 rows equal the frozen disposition order, whose builder derives that order directly from source-object `colnames` (`scripts/v4/stage81a3_rebuild_nph_disposition_cache.R:43-107`). The adapter opens H5AD only to `handle["obs"]` and never addresses `X`, `raw`, `layers`, or another expression node; NPH `.qs` objects are existence-checked only (`build_full104_production_adapter_metadata.py:253-282,302-338`). Aggregate authorities reconcile rows but do not generate them.

## Key falsification / blocker

No current blocker. Falsify this PASS if runtime I/O tracing observes any expression-node read, if any pinned input/physical-source/output hash changes, or if fresh source-metadata enumeration fails any exact row, donor, operator, state, quarantine, or uniqueness check above. The JSON `expression_read: false` flags are declarations; this verdict rests on static code inspection plus independent physical-metadata and hash parity.
