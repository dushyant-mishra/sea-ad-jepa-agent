# V79 synthetic lane — current takeover pointer

Updated: 2026-10-12 after repaired benchmark completion and lane-boundary cleanup.

## Read first

1. `results/v79/synthetic_lane_audit/deltas/20261012_RARE_BIOLOGY_REALDATA_INTEGRATION_V1.md`
2. `docs/agent/V79_RARE_BIOLOGY_REALDATA_INTEGRATION_SPEC_20261012.md`
3. `results/v79/rare_biology_integration/V79_REALDATA_RARE_PROGRAM_ASSIMILATION_20261012.md`
4. `results/v79/rare_biology_integration/V79_RARE_BIOLOGY_DATASET_CAPABILITY_MATRIX_20261012.csv`
5. `results/v79/synthetic_lane_audit/deltas/20261012T1720Z_ARCHIVAL_CONSOLIDATION_AND_TAKEOVER_V1.md`
6. `results/v79/synthetic_lane_audit/V79_SYNTHETIC_LANE_AUDIT_INDEX_V1.json`
7. `docs/agent/V79_SYNTHETIC_LANE_TAKEOVER_HANDOFF_20261012.md`

## Lane boundary

This lane **may inspect and analyze real TRAIN biology** when needed to make synthetic worlds realistic. Allowed uses include prevalence ranges, donor recurrence, covariance/program shape, source/operator/depth effects, modality relationships, effect-size ranges, spatial structure and perturbational response geometry.

This lane **must not promote those analyses into project target-discovery authority**. It does not choose the real biological target, declare a real rare state as the project target, or overwrite the target-discovery lane. Any real-data observation that may matter for target discovery gets handed off separately.

No completed ETL should be repeated when authenticated caches/hashes already exist.

## Q00-Q11

Q00-Q11 remain immutable. Root manifest: `84949723305dc2211ebcd451b64dd9adc8518f3580d2122f5600fcf4b38de0de`; directory digest: `40458efea66e62f3f39cb773641d29c24b80505529baa65bdab31d3975a2a286`.

The repaired benchmark at PR #308 / evidence commit `586e5ea5af73bbc28637a4cbab0eb7c108c67d42` completed 4/4 fits, 0 divergences, worst R-hat 1.01, worst bulk/tail ESS 1184/1343, and projected the 1,056-fit campaign at 1.520 h versus the frozen 72 h ceiling. This is engineering feasibility only; qualification fitting still needs separate controller authority.

## Rare-biology synthetic work

The synthetic extension is separate from Q00-Q11 and should model real biological structure, including donor-recurrent rarity, donor-restricted legitimate biology, RNA/regulatory coupling, separate-nucleus versus same-nucleus multimodal structure, spatial context and perturbational response.

Real biology may be examined to inform those worlds. The key protection is that source/operator/depth or any single historical score must not silently become synthetic biological truth.

The historical `innovation_tail`, `recurrent_5pct` and `recurrent_1pct` share the same molecular direction. The read-only 50K TRAIN check showed that direction is strongly source-shifted; use that as a realism/shortcut warning, not as a real target declaration.

## Existing real-data assets

Reuse existing authenticated/cached FOUNDATION, Morabito, GSE214979, GSE272082, Stage75-79/cisTarget, spatial and perturbation assets. Exact roles and limitations are in the capability matrix.

## Permissions

- Q00-Q11 regeneration: **FORBIDDEN**
- Q00-Q11 qualification fits: **OFF pending controller authority**
- qualification scoring: **OFF**
- synthetic rare-biology design/engineering: **ACTIVE**
- TRAIN biology inspection/calibration for synthetic realism: **ALLOWED**
- real biological target selection/promotion: **TARGET-DISCOVERY LANE ONLY**
- pathology/DEV/SEALED/TEST outcome use for synthetic tuning: **OFF**
- JEPA training: **OFF**
