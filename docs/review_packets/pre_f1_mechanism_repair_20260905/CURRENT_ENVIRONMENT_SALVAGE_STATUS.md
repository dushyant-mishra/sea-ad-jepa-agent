# Current-environment salvage status

Verified on 2026-09-05.

## Salvage bundle

- file: `JEPA_CURRENT_ENVIRONMENT_MISSED_FILES_20260905.zip`
- bytes: `8668589`
- SHA-256: `54b34daba313c920455ed8cbd6648af15754bdadbbb06e394c1cc025f5cfc3d7`
- internal manifest entries: `17`
- internal manifest verification: `17/17 PASS`

## Protected-program weight authority

- file: `program_weights.npz`
- bytes: `1531109`
- SHA-256: `001375ec77c5b606ad0972073c1daa6ad14b0e517f05ea23c6c9b3110203ff70`

NPZ header inspection confirms 21 arrays:
- ordered `molecular_address_id` of length 41,238;
- raw and L2 vectors for:
  - broad_common
  - weak_distributed
  - local
  - local_core
  - local_halo
  - core_halo
  - sparse_marker_like
  - innovation_tail
  - recurrent_5pct
  - recurrent_1pct

The binary authority is included in the complete local Claude handoff. It is not duplicated into this GitHub text-only review directory.

## Missing historical source

Exact bytes of `full104_model_components_v2.py` remain unrecovered.

Do not reconstruct from prose. Run the included PowerShell recovery script on the local JEPA workspace and preserve the exact SHA-256 if found.

Reported historical path:
`exports/jepa_codex_adaptive_handoff_v014_20260826/.../codex/code/full104_model_components_v2.py`

Expected symbols are identity hints only:
- `Full104HeadConfig`
- `DirectResidualStateHead`
- `SingletonQueryPredictor`
- `state_block_loss`
- `directional_pair_context_loss`

Also verify whether `DIRECT_INIT_MANIFEST.json` exists. Do not fabricate it if absent.
