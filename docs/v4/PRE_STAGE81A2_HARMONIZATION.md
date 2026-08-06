# Pre-Stage81A2 Virtual Harmonization

This layer references frozen SEA-AD, normal-reference and perturbation assets
without rewriting or physically concatenating them. It registers source hashes,
matrix semantics, exact feature namespaces, donor/specimen/section fields,
duplicate groups and candidate roles.

Full feature mappings are deterministic gzip sidecars under ignored
`data/processed/v4/pre_stage81a2/mappings`. Source identifiers are preserved.
Canonical symbols or Ensembl identifiers are populated only when present
exactly in the source; no fuzzy aliases or donor matching are permitted.
Unresolved identifiers remain explicit.

The virtual-concat manifest is a future execution contract, not a merged atlas,
gene-vocabulary freeze, donor split, or training matrix. Pathology-bearing
columns may exist in authoritative sources, but this builder never reads their
values.

Run:

```powershell
conda run -n sea-ad-jepa-v3 python scripts/v4/build_pre_stage81a2_harmonization.py
```

Stage81A2 review remains blocked while exact spatial section identity is absent
for any spatial source intended for section-aware evaluation. That blocker must
not be resolved by parsing partial identifiers or making fuzzy assumptions.
