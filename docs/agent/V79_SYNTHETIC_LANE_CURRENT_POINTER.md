# V79 synthetic lane — current takeover pointer

Updated: 2026-10-12 16:07 UTC

Read first:

1. `docs/agent/V79_SYNTHETIC_LANE_AUDIT_HISTORY_20261012.md`
2. `results/v79/synthetic_lane_audit/V79_SYNTHETIC_LANE_AUDIT_INDEX_V1.json`
3. newest file under `results/v79/synthetic_lane_audit/deltas/`
4. `docs/agent/V79_SYNTHETIC_LANE_TAKEOVER_HANDOFF_20261012.md`

## Preferred live lineage

- PR #305 reconciled scorer/executor successor remains the last frozen all-green integration base: `e976d0c1a03f6a54dadcbf7fe3086f832fd319d8`.
- PR #306 scoring-orchestrator successor is the active engineering branch.
  - current head: `71273b3017c10811b6ddf4bccea78b2bf0f58c92`
  - scorer CI `38274937051`: Windows PASS, Linux PASS, static scorer firewall PASS.
  - executor CI `38274937118`: Windows PASS, Linux PASS, static fit-side firewall PASS.
  - newest completed milestone: frozen detection held-out descriptives now retain and validate 10-bin calibration plus predicted-vs-observed prevalence, while remaining explicitly non-gating.

Historical source lineages remain preserved:
- PR #300 campaign runner: `7172b201b13c61634b84b85254bf4406959b2b57`.
- PR #301 historical scorer: `7fe0204b2661f0d1492115c973a4da7a4a1646b6`.
Do not continue development on either historical branch by default.

## Immediate engineering action

Continue PR #306 under TDD:

1. implement controller-only planted-oracle held-out metrics;
2. use the frozen `truth/detection/prevalence.npy` for the planted `<0.05` subset;
3. use exact fitter design geometry and masks;
4. same-donor oracle uses planted donor effects;
5. new-donor oracle uses the frozen 40-node Gauss-Hermite integration convention over the planted donor-effect distribution;
6. include Q11 planted operator offsets in the oracle where present;
7. then build the physical controller-only scoring orchestrator.

The orchestrator must:
- require the exact completed 1,056-fit campaign receipt and verify every fit-record hash;
- require a separate post-campaign scoring authorization bound to exact campaign SHA, frozen Contract V2, realization authority, blinded-index SHA, and exact scorer Git head;
- load controller truth only in the scoring trust domain;
- construct exactly 1,056 controller-scored gene/part rows;
- evaluate exactly 292 frozen gates and preserve first-hard-fail terminal semantics;
- compute all five required descriptive families as explicitly non-gating;
- write hash-bound gate table, descriptive metrics, and immutable adjudication receipt once;
- refuse incomplete/mismatched/extra inputs and refuse overwrite;
- never authorize real TRAIN posterior, factorial science, external validation, or JEPA training.

## Current authority boundary

World regeneration is forbidden. Qualification fitting and scoring remain OFF. Benchmark authority remains the separate PR #299 path and must not be inferred from this handoff or PR #306.
