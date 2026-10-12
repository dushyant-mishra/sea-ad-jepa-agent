# V79 synthetic lane — current takeover pointer

Updated: 2026-10-12 16:14 UTC

Read first:

1. `docs/agent/V79_SYNTHETIC_LANE_AUDIT_HISTORY_20261012.md`
2. `results/v79/synthetic_lane_audit/V79_SYNTHETIC_LANE_AUDIT_INDEX_V1.json`
3. newest file under `results/v79/synthetic_lane_audit/deltas/`
4. `docs/agent/V79_SYNTHETIC_LANE_TAKEOVER_HANDOFF_20261012.md`

## Preferred live lineage

- PR #305 reconciled scorer/executor successor remains the frozen integration base: `e976d0c1a03f6a54dadcbf7fe3086f832fd319d8`.
- PR #306 scoring-orchestrator successor is the active engineering branch.
  - current head: `045affc6e5f1c384f799661ced2db69acaa72ee3`.
  - scorer CI `38275752111`: Windows PASS, Linux PASS, static scorer firewall PASS.
  - executor CI `38275752308`: Windows PASS, Linux PASS, static fit-side firewall PASS.
  - completed PR306 milestones: detection calibration/prevalence descriptive contract; controller-only planted held-out oracle.

Historical source lineages remain preserved:
- PR #300 campaign runner: `7172b201b13c61634b84b85254bf4406959b2b57`.
- PR #301 historical scorer: `7fe0204b2661f0d1492115c973a4da7a4a1646b6`.
Do not continue development on either historical branch by default.

## Planted oracle now frozen structurally

`v79_v2_core_score_oracle.py` is controller-only and non-gating. It:
- cross-checks truth/blinded opaque identity and structural support;
- uses exact fit-model depth/Helmert/within-source donor geometry;
- uses realized planted donor effects for same-donor oracle;
- integrates planted donor SD with exact 40-node Gauss-Hermite for new-donor oracle;
- uses frozen `truth/detection/prevalence.npy` for planted prevalence;
- requires/applies Q11 operator x gene offsets;
- outputs same/new detection log-loss/calibration/prevalence and positive LPD oracle references.

## Immediate engineering action

Continue PR #306 under TDD by building the controller-only physical scoring orchestrator.

The orchestrator must:
- require exact completed 1,056-fit campaign receipt and verify every fit-record hash against the campaign ledger;
- require a separate post-campaign scoring authorization bound to campaign SHA, Contract V2, root manifest, blinded index, realization audit receipt, and exact scorer Git head;
- validate the physical frozen blinded package hashes before loading observations;
- load committed controller truth only after authorization passes;
- construct exactly 1,056 controller-scored rows;
- build planted oracle held-out references for every fit;
- evaluate exactly 292 frozen gates and preserve first-hard-fail terminal semantics;
- compute all five required descriptive families as explicitly non-gating;
- write canonical/hash-bound gate table, scored-row table, descriptive metrics and immutable adjudication receipt exactly once;
- refuse incomplete/mismatched/extra/tampered inputs and refuse overwrite;
- keep downstream authorities false.

Required RED tests should cover at least: missing/wrong authorization, campaign receipt SHA mismatch, individual fit-record tamper/missing/extra file, wrong scorer head, physical blinded root/index mismatch, truth mismatch, incomplete 1,056 rows, incomplete 292 gates, missing descriptive family, and write-once refusal.

## Current authority boundary

World regeneration is forbidden. Qualification fitting and scoring remain OFF. Benchmark authority remains separate PR #299 and must not be inferred from this handoff or PR #306.
