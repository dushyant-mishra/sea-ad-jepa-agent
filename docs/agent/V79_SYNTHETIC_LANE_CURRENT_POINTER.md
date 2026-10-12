# V79 synthetic lane — current takeover pointer

Updated: 2026-10-12 after repaired benchmark completion and rare-biology real-data assimilation.

## Read these first

1. `results/v79/synthetic_lane_audit/deltas/20261012_RARE_BIOLOGY_REALDATA_INTEGRATION_V1.md`
2. `docs/agent/V79_RARE_BIOLOGY_REALDATA_INTEGRATION_SPEC_20261012.md`
3. `results/v79/rare_biology_integration/V79_REALDATA_RARE_PROGRAM_ASSIMILATION_20261012.md`
4. `results/v79/rare_biology_integration/V79_RARE_BIOLOGY_DATASET_CAPABILITY_MATRIX_20261012.csv`
5. `results/v79/synthetic_lane_audit/deltas/20261012T1720Z_ARCHIVAL_CONSOLIDATION_AND_TAKEOVER_V1.md`
6. `results/v79/synthetic_lane_audit/V79_SYNTHETIC_LANE_AUDIT_INDEX_V1.json`
7. `results/v79/synthetic_lane_audit/V79_SYNTHETIC_LANE_CODE_DATA_RESULT_INDEX_20261012.csv`
8. `docs/agent/V79_SYNTHETIC_LANE_TAKEOVER_HANDOFF_20261012.md`

Do not repeat historical audits before frozen heads/hashes unless bytes changed or a concrete contradiction is found.

## Current state

### Q00-Q11 realization

Realized exactly once and byte-audited. Regeneration is forbidden.

- root manifest `84949723305dc2211ebcd451b64dd9adc8518f3580d2122f5600fcf4b38de0de`
- directory digest `40458efea66e62f3f39cb773641d29c24b80505529baa65bdab31d3975a2a286`
- blinded index `8ea3e0cb6637c97b3e940eac54476622bd4f790febb07abee2e8ccdeea751e40`
- 498-file ledger `4e65f213d2eeb2d66b8bd7a9031eeb47eadee5801a9bd0880bd3c78dae88cd65`

### Repaired engineering benchmark — COMPLETE

The one authorized repaired benchmark at PR #308 exact head `559a1c104c8f1f56d2c05509eecf6b9dc05846a5` was consumed successfully.

Evidence:
- evidence commit `586e5ea5af73bbc28637a4cbab0eb7c108c67d42`
- PR #308 comment `6129569599`
- prep receipt SHA-256 `ee89a67ba3919a6593b2f20e4cc4030904e4032ef78c28438fecdab0cfed8170`
- result receipt SHA-256 `3774cecbc10266ed9205fe3bd8f161faf119ab83c3625783b484c2412477316d`

Results:
- 4/4 fits COMPLETE on PRIMARY stage only
- 0 divergences
- worst R-hat 1.01
- worst bulk/tail ESS 1184 / 1343
- mean fit wall time 3.818 s
- projected 1,056-fit runtime 1.520 h including frozen settle term
- frozen ceiling 72 h
- `stop_required=false`
- qualification fits 0; scoring false; truth not accessed; training not authorized

This establishes engineering feasibility only. It does not by itself authorize Q00-Q11 fitting.

## Scientific scope correction

V79 Q00-Q11 are Layer A: observation/statistical qualification. They do **not** contain the project's required cell-level rare multimodal biological state.

Historical project work already required rare/private biology, donor recurrence, evidence-dependent recovery and uncertainty. That requirement is now restored as a separate additive workstream rather than modifying Q00-Q11.

New authority/design surfaces on the integration branch:
- `docs/agent/V79_RARE_BIOLOGY_REALDATA_INTEGRATION_SPEC_20261012.md`
- `results/v79/rare_biology_integration/V79_RARE_BIOLOGY_DATASET_CAPABILITY_MATRIX_20261012.csv`
- `results/v79/rare_biology_integration/V79_REALDATA_RARE_PROGRAM_ASSIMILATION_20261012.md`
- `docs/superpowers/plans/2026-10-12-v79-rare-biology-realdata-integration.md`

Important recovered fact: frozen `recurrent_5pct` and `recurrent_1pct` use the same molecular direction as `innovation_tail`; they are threshold roles, not distinct rare biological programs.

Important new read-only diagnostic: applying that historical direction to the existing authenticated 50K TRAIN discovery sample is strongly source-shifted. Therefore it must not define the new cross-source rare biological truth.

## Real-data assets already assimilated

Do not redo ETL. Existing authenticated/cached assets include:
- FOUNDATION 41K TRAIN/discovery expression and metadata;
- Morabito GSE174367 RNA/ATAC and microglia caches;
- GSE214979 paired same-nucleus multiome (conditional support);
- GSE272082 paired-multiome candidate with remaining authentication gaps;
- Stage75-79/cisTarget regulatory evidence;
- SCP2167 + eligible Fang STG spatial context evidence;
- GSE178317 perturbation assets.

Exact hashes/roles/limitations are in the capability matrix.

## Engineering topology

- historical campaign runner #300 `7172b201b13c61634b84b85254bf4406959b2b57`
- preferred reconciled base #305 `e976d0c1a03f6a54dadcbf7fe3086f832fd319d8`
- active controller-scorer engineering #306 `d4e10c821847078bac6d4043b18b09bdfb6c5ef1`
- physical scoring OFF

## Immediate work

1. Controller must separately decide whether the successful benchmark authorizes frozen Q00-Q11 qualification fitting.
2. In parallel, implement the real-data-matched rare-biology workstream from the new spec/plan.
3. Do not regenerate or modify Q00-Q11.
4. Do not use protected Morabito/pathology/DEV/SEALED/TEST outcomes for rare-program selection.
5. Rare biology must be independently gated; a V79 Layer-A PASS cannot substitute for it.

## Permissions

- regenerate Q00-Q11: **FORBIDDEN**
- repaired engineering benchmark: **SPENT SUCCESSFULLY**
- Q00-Q11 qualification fits: **OFF pending new controller authority**
- qualification scoring: **OFF**
- rare-biology synthetic implementation: **DESIGN/ENGINEERING ACTIVE; production realization not authorized**
- real TRAIN pathology-blind calibration from already-authorized caches: **allowed only under the new prospective contract; no pathology**
- TEST/Morabito outcome selection/pathology: **OFF**
- JEPA training: **OFF**
