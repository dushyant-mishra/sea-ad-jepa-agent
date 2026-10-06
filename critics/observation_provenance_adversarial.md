# Observation/Provenance + Adversarial Critic

VERDICT: STOP

## Three strongest findings

1. **The decomposition was not executed through the claimed production loader.** `run_decomposition.py:97-115` instantiates `ProductionTrainLoader` only to generate its manifest and compare 3 cells per operator against the prior adapter; line 116 then calls `fg.main()`, which runs the decomposition through the imported qualification adapter. This is confirmed by `provenance.json`, whose `cache_adapter` identifies `exports/real_production_forward_target_gate_20260821/run_forward_gate.py`, and by `production_pipeline_report.json`, which still states that no immutable production loader exists. The package therefore establishes representative adapter equivalence, not provenance of the reported 1,575-cell decomposition through the new loader.

2. **Three-state semantics are explicit and the sampled equivalence is exact, but equivalence is incomplete.** `production_train_loader.py` emits separate `uint8` states for `STRUCTURALLY_UNMEASURED`, `MEASURED_SCALAR`, and `MEASURED_COLLISION_UNRESOLVED`, rejects nonzero values outside `MEASURED_SCALAR`, and preserves measured zeros. `loader_equivalence.json` reports byte-equal values, equal scalar masks, zero maximum error, and 2,611,723 measured-zero instances across 126 cells/42 operators. However, it compares only three deterministically selected cells per operator and only the binary scalar mask (`new_states == MEASURED_SCALAR`); it does not independently compare the full three-state arrays, exhaustively compare every cached cell, or exercise collision-unresolved rows as an explicit equivalence stratum.

3. **TRAIN-only closure is demonstrated for the bounded audit, not enforced by the loader.** All 1,575 unique `audit_cells.csv` rows cover 42 operators and 149 donors and carry `split_domain=foundation`, `split=train`, and the hashed-support observation-state source; `evidence_semantics_audit.json` reports zero DEV/SEALED donors. But those fields/checks are added by the old adapter using the split registry. `ProductionTrainLoader._inventory()` never reads or validates `stage81a2_split_registry.csv`; it trusts files under a directory named `corrected_real_train`, discovers operator membership through `stage81a2_canonical_asset_registry.csv` and `stage81a3_nph_sample_manifest.csv`, and does not pin/hash either discovery input. Its `manifest()` hashes the current shards but the loader does not validate them against an immutable expected manifest before loading. Thus source closure can drift while still producing a newly self-consistent manifest.

## Most important blocker/falsification

Rerun the complete decomposition with `ProductionTrainLoader` as the sole value/state source, after making it fail closed against a pinned manifest and the hashed foundation split registry. Require exhaustive per-cell equality of values and all three state codes against the qualification source (including collision-unresolved strata), plus hashed operator-inventory inputs. Any mismatch, DEV/SEALED donor, unpinned shard, or continued fallback to `fg.main()`/the prior adapter falsifies production-loader provenance.

## Exact artifact references

- `exports/static_context_decomposition_v4_20260821/run_decomposition.py`
- `exports/static_context_decomposition_v4_20260821/production_train_loader.py`
- `exports/static_context_decomposition_v4_20260821/production_loader_manifest.json`
- `exports/static_context_decomposition_v4_20260821/loader_equivalence.json`
- `exports/static_context_decomposition_v4_20260821/evidence_semantics_audit.json`
- `exports/static_context_decomposition_v4_20260821/audit_cells.csv`
- `exports/static_context_decomposition_v4_20260821/provenance.json`
- `exports/static_context_decomposition_v4_20260821/production_pipeline_report.json`
- `exports/static_context_decomposition_v4_20260821/provenance_hash_manifest.csv`
