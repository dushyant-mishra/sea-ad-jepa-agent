# Source Manifest

Authority commit for all repository paths below:

`76fe7d63efe81451ef0fae3ef3eaf116be14f6be`

Fetch files at that exact ref. Do not silently substitute branch-tip bytes.

| Role | Exact repository path |
|---|---|
| Current IPB encoder / KernelLinearAttention / historical BlockPredictor | `src/sea_ad_jepa/v4/ipb_jepa.py` |
| Historical production one-update mechanics path / Phase-E gradient aggregation | `scripts/v4/stage81a3_prod41k_engineering_smoke.py` |
| Historical PROD41K T1 training/evaluation/checkpoint path | `scripts/v4/stage81a3_prod41k_teacher_t1.py` |
| Query-local parameter-free target construction | `src/sea_ad_jepa/v4/contextual_query_local.py` |
| Current F1 u0 loader / lean query-local forward | `scripts/v4/contextual_target_f1_preflight_core_v1.py` |
| F1 decision code | `scripts/v4/contextual_target_f1_decision_v4.py` |
| F1 integration | `scripts/v4/contextual_target_f1_decision_integration_v4.py` |
| F1 query design / aggregation | `scripts/v4/contextual_target_f1_querydesign_decision_v2.py` |
| Provisional successor mechanics currently in src | `src/sea_ad_jepa/v4/successor_candidate.py` |
| Public architecture claim / singleton head description | `README.md` |
| Current controlling state | `docs/agent/memory-os/ACTIVE_STATE.md` |
| Current authority index | `docs/agent/CURRENT_AUTHORITY_INDEX.md` |
| Stage81 architecture/mechanics history | `docs/v4/STAGE81A3_CALIBRATION_AND_SYNTHETIC_MECHANICS_READOUT.md` |

Known frozen SHA-256 values from the T1 contract:

- `src/sea_ad_jepa/v4/ipb_jepa.py`: `732ea46f72384f29d503de1e0cc9d853315e2493cace054cced74849aa77485a`
- `scripts/v4/stage81a3_prod41k_engineering_smoke.py`: `11b381762787aaae8920cfced3e245dbc8579b335ee2576ffcc21cc0253d4cd6`
- `scripts/v4/stage81a3_prod41k_teacher_t1.py`: `40c004474edd5355b358dcd4a5aba47e4479c55917949ea316ae5202aa06d241`

Large/local authorities Claude should use if present in the working environment:

- `t1_checkpoint_u0000.pt` — historical u0 SHA-256 `19fb0c25d9f7549c37de39285807d5b6a6e828ced94af63927e83fa3c5c6b7c4`
- `t1_checkpoint_u0205.pt` — historical u205 SHA-256 `f8b1ad572391d38db474b4de95c56314bcff89086df6e42e86db259940a504fa`
- recovered u10/u25/u50/u100/u200 checkpoint bundle
- frozen 84-cell × 41,238-address technical truth-table fixture
- 42-operator observation-state authority
- frozen sampler/split/T1 contracts
- program weight authority SHA-256 `001375ec77c5b606ad0972073c1daa6ad14b0e517f05ea23c6c9b3110203ff70`

## Historical source missing from GitHub

Required exact historical local file:

`full104_model_components_v2.py`

It is named by the authoritative handoff but is not present on current GitHub main or this packet.

Recover exact local bytes by filename, compute SHA-256, and add a manifest entry. Do not reconstruct from descriptions.

Expected symbols, for identity checking only:

- `DirectResidualStateHead`
- `SingletonQueryPredictor`
- `state_block_loss`
- `directional_pair_context_loss`
- `Full104HeadConfig`

Also search for `DIRECT_INIT_MANIFEST.json`. Current audit reports it absent; absence must be verified, not filled in.