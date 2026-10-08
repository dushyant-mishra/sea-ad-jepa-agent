# V77 class-propagation tournament audit — 2026-10-08

Status: **STRUCTURAL IMPLEMENTATION GREEN / SCIENTIFIC E0–E3 TOURNAMENT NOT EXECUTED / BLOCKED ON EXACT CORRECTED UNIVERSE BYTES**

## Bottom line

The preregistered ETL→synthetic class-propagation implementation is structurally complete through E3. The implementation has not produced or opened any E0–E3 corrected-S174 scientific tournament outcome, because the exact corrected frozen evaluation-universe NPZ is not available in this environment.

This distinction is mandatory. Structural GREEN does not imply that E2 or E3 improves T5, does not select a synthetic arm, and does not authorize training.

## Canonical implementation surface

- branch: `impl/v77-class-propagation-20261008`
- draft PR: #240 — `V77 synthetic class propagation E1-E3`
- design: `docs/superpowers/specs/2026-10-08-synthetic-etl-propagation-design.md`
- implementation plan: `docs/superpowers/plans/2026-10-08-synthetic-etl-propagation.md`
- prospective full-scale amendment: `docs/superpowers/specs/2026-10-08-synthetic-etl-propagation-fullscale-amendment.md`

The full-scale amendment and World-B E0 baseline freeze were written before any class-propagation tournament result existed.

## What is implemented

### Class-composition authority

`scripts/v77/build_v77_class_composition_authority.py`

The authority:

- consumes only corrected pathology-blind TRAIN calibration class counts;
- freezes 24 ordered broad-class labels across 4,726 corrected calibration cells;
- uses exact largest-remainder quotas;
- assigns classes shard-invariantly from global cell identity + seed + authority only;
- rejects pathology-like metadata;
- carries no real gene program content;
- canonicalizes in-repository provenance paths so the committed authority is machine-portable.

Committed authority:

`results/v77/V77_CLASS_COMPOSITION_AUTHORITY_V1.json`

Corrected calibration SHA-256:

`f6ba2c725a5437cc8455fff418027d36efe9ea9430fbd0a5765df62dedca6068`

### E1 — class composition only

`scripts/v77/build_v77_class_aware_truth.py`

E1 adds `broad_class_index` only. Focused integration tests prove that all pre-existing truth arrays remain identical and that observable arrays remain identical to E0 under identical seeds/settings.

### E2 — class-shared random-content biology

Structural 96-gene observer:

`scripts/v77/build_v77_class_aware_rna_observer.py`

Full-scale registry bridge:

`scripts/v77/build_v77_class_aware_fullscale_rna_observer.py`

E2 adds one class-shared dense random-content program at the prospectively frozen scale `0.55`. Loadings depend only on synthetic RNG streams, class index and synthetic/canonical registry position. Real marker genes, regulatory edges, donor, source and operator are not inputs.

### E3 — class-shared + continuous within-class biology

E3 preserves E2 and adds two shard-invariant continuous within-class coordinates. Each dimension uses the prospectively frozen scale:

`0.55 / sqrt(2)`

The coordinates and loading construction do not key on donor, source or operator. Focused tests prove non-zero within-class variance and nuisance independence.

### E4

E4 donor×class interaction remains fail-closed and unauthorized.

## Full-scale scoring bridge

An implementation-time dimensional incompatibility was discovered before scientific outcomes were read:

- the historical extended observer materializes 96 genes;
- corrected S174 matched scoring operates on a 14,417-address subset of the canonical 41,238-address registry.

Therefore the corrected tournament uses a successor wrapper over `build_v77_fullscale_rna_observer_v2.py`, not the 96-gene structural observer.

Prospectively frozen for the first tournament:

- E0 biological baseline: existing V77 World-B preset `B1,B2,B3,B4,B5,B6`;
- full-scale background: `v1`;
- observer/counting mechanics: inherited unchanged from the full-scale observer;
- E2 class scale: `0.55`;
- E3 dimensions: 2 at `0.55/sqrt(2)` each;
- no post-outcome parameter tuning.

## Tournament runner

`scripts/v77/run_v77_class_propagation_tournament.py`

The runner is deliberately fail-closed. It:

- exposes only E0–E3;
- rejects E4;
- authenticates the corrected evaluation-universe SHA before generating scientific worlds;
- requires the corrected universe to contain exactly 14,417 canonical addresses;
- uses existing `v77_matched_scoring.score_matched` rather than reimplementing scoring;
- scores expression geometry, detection topology, T5, abundance and depth together;
- labels corrected real points descriptive only;
- sets `s159_binary_gate=false`;
- forbids recentering and post-outcome retuning;
- binds executor/source digests and class authority SHA;
- checks the 2K population retains 42/42 observation operators with minimum support >=1;
- requires E1 matched scores to equal E0 exactly.

## Fresh GitHub CI evidence

Workflow:

`.github/workflows/v77-synthetic-class-propagation.yml`

Run:

`37834915423`

Audited implementation head:

`0cd8e2d1748087895193f5247c1ac19a2c190063`

Focused result:

`21 passed`

Historical structural spillover result:

- `RAW_IDS_MODEL_VISIBLE`: PASS
- `OLD_RUNTIME_CLASSES`: PASS
- `ZERO_QUOTA_OPERATOR_LOSS`: PASS
- `structural_pass`: true

The spillover audit also reports historical text candidates for manual interpretation; those are not execution failures and were not promoted to scientific conclusions here.

## Exact scientific blocker

The corrected frozen evaluation-universe authority records:

- canonical registry addresses: 41,238;
- corrected evaluation universe: 14,417 addresses;
- legacy universe label: `TRAIN_PREVALENCE05_19569`;
- expected file name: `frozen_evaluation_universe.npz`;
- expected SHA-256:

`e950e967dd593b253837017f8bda5c5a683d975074728f4b8fe20c27272b9763`

Historical local path recorded by the corrected S174 replay:

`D:/jepa_v77_synthetic_custody_20261005/s174_replay/frozen_evaluation_universe.npz`

The exact bytes were searched for in:

- current conversation/project uploads;
- available Library/project search surfaces;
- ordinary Git repository history/snapshot surfaces available to this agent;
- the preserved S174 takeover snapshot;
- the accessible S174 GitHub Actions artifact;
- the mounted calibration, expression and checkpoint ZIPs.

They were not recovered. The discovery 41K expression bundle is not a lawful substitute: it is a different custody object and has not been proven to reproduce the exact corrected 14,417-address universe SHA.

The tournament therefore must remain unexecuted until the exact NPZ is supplied or independently reconstructed to the exact expected SHA.

## What has NOT been claimed

No claim is made that:

- E2 or E3 improves T5;
- any arm brackets the corrected real T5 value ~0.7435;
- any arm is selected;
- the corrected S159 intervals are valid qualification gates;
- E4 is authorized;
- JEPA mutation or training is authorized;
- real-data training is authorized;
- production target, representation or EMA choices are frozen.

## Next executable action

Once `frozen_evaluation_universe.npz` is available and verifies to the exact expected SHA, run the already-frozen E0–E3 tournament without changing:

- World-B E0 component preset;
- background `v1`;
- seed protocol;
- E2/E3 effect scales;
- scoring implementation;
- corrected real references;
- interpretation/falsification rules.

Until then, PR #240 should remain draft and the scientific result should be reported as **BLOCKED ON EXACT CORRECTED UNIVERSE CUSTODY**, not as incomplete tuning.
