# Project File Map

This map is the first phase of repository organization for the v4 transition. It is deliberately non-destructive: existing v1/v2/v3 paths remain stable so old scripts, manifests, hashes, and documentation links do not break.

## Current Organization Policy

| Area | Meaning | Move Policy |
|---|---|---|
| `archive/v1/` | Placeholder for future v1 reference notes | Do not move files here until references are audited. |
| `archive/v2/` | Placeholder for future v2 reference notes | Do not move files here until references are audited. |
| `archive/v3/` | Placeholder for v3 frozen checkpoint notes | Prefer indexes over moving frozen artifacts. |
| `configs/v4/` | v4 planning and training configs | Active v4 configs belong here. |
| `docs/v4/` | v4 design notes and milestone plans | Active v4 docs belong here. |
| `scripts/v4/` | v4-only helper scripts and inventory tools | Use for v4-specific scripts unless shared. |
| `results/v4/` | local v4 results namespace | Ignored by default; freeze selected summaries only after review. |
| `runs/v4/`, `logs/v4/`, `outputs/v4/`, `checkpoints/` | local v4 training products | Ignored; never commit checkpoints or raw training dumps. |

## Version Buckets

- `v1`: early hypothesis, discovery, and proof-of-concept artifacts.
- `v2`: graph-foundation, external-support, and second-generation benchmark artifacts.
- `v3`: Graph-JEPA v3, Stage C disease-state geometry, rare microglia/PVM work, Stage75-79 regulatory evidence and control simulation artifacts.
- `v4`: regulatory-aware Graph-JEPA planning and future training artifacts.
- `unclassified`: files that need human review before moving or relabeling.

## Tracked Inventory

The tracked file inventory is written to:

`results/tables/project_file_inventory_v1.csv`

Regenerate it with:

```powershell
cd "D:\Jepa project"
conda run -n sea-ad-jepa-v3 python scripts\v4\build_project_file_inventory.py
```

## Rule For Physical Moves

Do not move scripts, configs, or frozen results merely to make the tree prettier. Move only after an inventory confirms:

- no hard-coded path will break;
- docs and configs can be updated in the same commit;
- frozen hashes/manifests either remain valid or are intentionally re-frozen;
- the move improves v4 usability more than it harms v3 reproducibility.
