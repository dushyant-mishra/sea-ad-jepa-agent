# Dataset Fidelity Review

**VERDICT: PASS**

## Three strongest findings

1. **Exact lawful cohort and firewall.** An independent streaming audit of all 42 gzip lineage shards found exactly 4,553,407 rows and exactly the 104 `reader_fit` donors, with zero overlap with the 45 reader-validation/oracle donors. Source donor composition independently resolves to HVS 41, NPH52 17, SEA_AD 46. Every row declares `LAWFUL_READER_FIT`, `reader_fit`, and `foundation/train`. This agrees with `FULL104_METADATA_RECONCILIATION.json` and the split enforcement in `scripts/v4/build_full104_production_adapter_metadata.py:122-146,212-221`.

2. **Exact operators, totals, and donor×operator parity.** The shards cover each operator exactly once (0–41), totaling HVS 198,718; NPH52 236,476; SEA_AD 4,118,213; overall 4,553,407. All 1,400 observed donor×matrix counts equal both `exports/foundation_corpus_discovery_v1/FOUNDATION_METADATA_DONOR_X_OPERATOR.csv` and an independent read-only aggregation of `foundation_metadata_rows.sqlite`; `FULL104_METADATA_MISMATCHES.csv` has no data rows. See `FULL104_ROW_LINEAGE.csv`, `FULL104_METADATA_RECONCILIATION.json`, and adapter lines 347–423.

3. **Rows are locator-derived, not aggregate-fabricated; provenance is intact.** HVS/SEA-AD rows are selected directly from H5AD `obs` vectors with physical row indices; NPH52 rows come from frozen disposition rows joined to the physical source-object manifest (adapter lines 253–338). Source rows are strictly increasing, row locators reconstruct exactly, shard-declared counts match streamed counts, and all 47 entries in `FULL104_ADAPTER_SHA256_MANIFEST.csv` plus every controlling-input hash in `FULL104_ADAPTER_PROVENANCE.json` verify. Static inspection found no expression-node access: H5AD access is restricted to `handle["obs"]` (lines 276–282); NPH physical files are existence-checked only. No pathology field is used to select rows; the controlling split is required to be pathology-blind (lines 131–143).

## Most important blocker / falsification

No present blocker. Falsify this PASS if runtime I/O tracing shows access to H5AD nodes outside `obs`, if any manifested hash changes, or if re-enumeration from immutable source metadata ceases to reproduce the exact 104 donors, 42 operators, 4,553,407 rows, or 1,400 donor×operator counts. The JSON firewall flags are declarations; confidence comes from the audited code path and row-level parity, not those flags alone.
