# V79 Detection-Geometry Localization Design

Date: 2026-10-09

Status: DESIGN APPROVED / IMPLEMENTATION IN PROGRESS / NON-TRAINING / NON-PROMOTING

Base: `impl/v78-signed-detection-marginals-20261009` @ `e959d9a732698ae9a41e8cb1f6c10052d7390326`

## 1. Purpose

Before selecting or implementing a new V79 synthetic mechanism, localize the causal origin of the real TRAIN signed-detection geometry that V78 attempted to reproduce.

The current headline signed statistic is computed from pooled binary gene-detection correlations across all corrected TRAIN cells. It is therefore compatible with several distinct causes: broad-class mixture, cell-depth heterogeneity, source/operator measurement effects, donor effects, residual within-class biology, or combinations of these.

This experiment does not attempt to make a synthetic arm pass. It determines which causal layer a future V79 mechanism must represent.

## 2. Scientific question

Where does the corrected TRAIN negative detection dependence survive after progressively controlling for known biological and measurement structure?

Decision targets:

- If negative topology largely disappears within broad class, prioritize richer latent biology or biological mixture structure.
- If it survives class but largely disappears after depth control, prioritize the measurement/capture process.
- If it survives class+depth but changes strongly by source/operator, prioritize an explicit observation operator.
- If it survives those controls and remains donor-structured, treat donor biology as a candidate source rather than nuisance.
- If substantial topology survives all supported controls, prioritize richer within-class latent biology or a coupled biology-observation mechanism.

No single scalar ratio is sufficient to make these rulings.

## 3. Hard boundaries

This work is TRAIN-only, pathology-blind, non-training-authorizing, and non-promoting.

Prohibited:

- JEPA training or checkpoint generation;
- TEST or Morabito access;
- E4 implementation;
- target-discovery replay, target ranks, target panels, SCENIC+/ATAC target evidence;
- pathology labels;
- 353 historical-ID repair;
- Stage4 / 500K work;
- production target or representation freeze;
- post-outcome V78 retuning;
- changing the frozen V78 tournament or scientific ruling;
- planting named real biological programs into synthetic truth.

Macha Bayesian geometry remains a separate sublane. Its returned results may be compared with this localization result only after independent custody/leakage/identity-scrubbing audit.

## 4. Canonical inputs

Use only the corrected S174 TRAIN substrate and authorities already authenticated by V78:

- repaired S174 lineage: `/Jepa project/s174_rebuilt_real_train_v1.rar`;
- repaired marginal authority: `/Jepa project/V78_MARGINAL_AUTHORITY_REPAIRED_V1.json`;
- corrected evaluation universe SHA-256 `e950e967dd593b253837017f8bda5c5a683d975074728f4b8fe20c27272b9763`;
- registry SHA-256 `7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd`;
- class authority SHA-256 `a4f5e325a54014d87d6380f81ce48922a6558f05ffafdaf7c59c1dc3ae705014`;
- authenticated shard→operator bridge from V78.

The design must fail closed if the repaired substrate or required authorities cannot be authenticated.

## 5. Gene-selection rule

The canonical analysis preserves the exact frozen V77/V78 selection rule:

1. use the corrected frozen evaluation universe;
2. choose the 3,000 genes by CPM-log1p expression variance;
3. calculate detection correlations on binary detection for that same selected set.

This canonical selection must not be changed after seeing localization outcomes.

A separate diagnostic prevalence-stratified view may be added prospectively, but it cannot replace, redefine, or retrospectively reinterpret the canonical 3K result.

## 6. Localization ladder

### L0 — pooled canonical reproduction

Exactly reproduce the existing corrected TRAIN signed-detection object using the frozen V78 scorer and selected genes.

Purpose: establish byte/semantic equivalence with the current real reference before any conditioning.

Required outputs include the existing strong-edge positive/negative ratio and full signed-topology diagnostics.

### L1 — broad-class localization

Compute detection geometry separately within each sufficiently supported broad class, using the same frozen selected genes.

Combine class-specific evidence using a prospectively fixed cell-count-weighted summary while retaining every per-class result separately.

Purpose: determine how much pooled signed topology is caused by mixing broad biological classes.

Do not infer that between-class structure is technical. A large L0→L1 change is evidence that class mixture contributes materially to the pooled statistic.

### L2 — depth localization within broad class

Within each supported broad class, control cell detection/depth without fitting a flexible gene-pair model.

Primary method: prospectively fixed quantile strata on detected-feature count, computed within class. Use five strata when support permits; merge adjacent strata only by a fixed minimum-cell rule declared before execution.

Secondary descriptive method: repeat with library-size strata as a sensitivity analysis.

Purpose: test whether signed detection structure persists among biologically similar cells with similar measurement depth.

Depth conditioning is diagnostic only; it does not claim that depth is purely technical.

### L3 — source/operator localization

Within the supported class+depth strata, compare geometry across authenticated observation source/operator strata.

Operator-level results require a prospectively fixed minimum cell count. Unsupported operators fall back to source-level descriptive grouping; they must not be pooled into a fabricated pseudo-operator.

Purpose: identify signed topology attributable to measurement regime rather than latent biological state.

Operator identity is read only through the authenticated shard→operator bridge, never inferred from `source_library`.

### L4 — donor localization

Where donor support is sufficient inside the preceding strata, measure donor-specific or donor-adjusted persistence of signed topology.

Purpose: determine whether residual dependence is associated with donor biology.

Donor variation is not automatically classified as nuisance. A donor-associated residual must be reported as biological/ambiguous unless independent evidence establishes a technical source.

### L5 — residual supported topology

Summarize the signed topology that remains stable across the supported class, depth, operator/source and donor views.

L5 is not a fitted residual covariance matrix and must not export gene identities or pairwise edge identities to the synthetic generator.

It is an identity-scrubbed statement of remaining geometry and uncertainty.

## 7. Metrics

For every supported localization level, report the same topology family:

- fraction of correlations > +0.3;
- fraction of correlations < -0.3;
- positive/negative strong-edge ratio;
- positive degree distribution;
- negative degree distribution;
- fraction of selected genes participating in at least one negative strong edge;
- unsigned median absolute correlation;
- unsigned strong-edge fraction;
- mean degree;
- transitivity;
- negative-edge participation within absolute-correlation communities.

The legacy threshold `|r| > 0.3` remains canonical for continuity.

Sensitivity analysis must also report the signed correlation distribution and threshold sweep at 0.1, 0.2, 0.3 and 0.4. These additional thresholds are diagnostic only and may not be selected post hoc as the new canonical threshold.

## 8. Uncertainty and support

Do not convert the old S159 20-resample intervals into binary pass/fail gates.

Localization outputs are descriptive until an independently justified uncertainty authority exists.

Every stratum must report:

- number of cells;
- number of selected genes with variable detection;
- number of pairwise correlations contributing;
- support/fallback status;
- whether the result is canonical or sensitivity-only.

Unsupported strata are omitted with an explicit reason rather than silently pooled.

## 9. Interpretation rules

No outcome promotes a synthetic arm or authorizes JEPA training.

The result selects only the next V79 mechanism family to design prospectively.

Interpretation hierarchy:

1. Large L0→L1 attenuation: prioritize richer biological mixture / within-class design before adding measurement complexity.
2. Persistent L1 but large L1→L2 attenuation: prioritize coupled depth/capture observation modeling.
3. Persistent L2 but strong L2→L3 operator/source dependence: prioritize a physically interpretable observation operator.
4. Persistent operator-conditioned signal with donor structure: preserve donor-linked biology in V79 rather than erase it.
5. Stable residual signal through L4: prioritize richer within-state biology or a coupled biological+measurement mechanism.
6. Mixed attenuation across levels: design V79 as a factorial synthetic tournament that isolates upstream biological hierarchy from downstream observation process; do not collapse the explanation into one flexible covariance layer.

These are mechanism-selection rules, not adequacy gates.

## 10. Required artifacts

Implementation should eventually produce:

- `results/v79_localization/V79_DETECTION_LOCALIZATION_PREEXECUTION_GATE_V1.json`
- `results/v79_localization/V79_DETECTION_LOCALIZATION_CANONICAL_V1.json`
- `results/v79_localization/V79_DETECTION_LOCALIZATION_SENSITIVITY_V1.json`
- `results/v79_localization/V79_DETECTION_LOCALIZATION_RULING_V1.json`

The ruling must include `training_authorized: false`, `v78_retuning_authorized: false`, and `synthetic_arm_promoted: null`.

## 11. Code boundaries

Prefer a new localization module rather than modifying frozen V78 scoring semantics.

Expected new surfaces:

- `scripts/v79/v79_detection_localization.py` — pure analysis helpers and stratum logic;
- `scripts/v79/run_v79_detection_localization.py` — authenticated execution/gate/receipt writer;
- `tests/test_v79_detection_localization_v1.py` — canonical reproduction, conditioning, fallback and fail-closed tests.

Reuse the frozen V78/V77 scorer for L0 and shared metric definitions where possible. Do not duplicate or alter frozen scoring code unless a separate bug is proven and adjudicated.

## 12. Success condition for this experiment

Success is not matching a preferred biological story.

Success means producing an authenticated, reproducible localization map that tells us which causal layer(s) must be represented by the next synthetic-world mechanism, while leaving V78 frozen and JEPA training unauthorized.
