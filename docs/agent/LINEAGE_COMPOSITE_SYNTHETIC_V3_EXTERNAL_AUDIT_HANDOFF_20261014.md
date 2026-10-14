# External audit handoff — production synthetic V3

Date: 2026-10-14
Status: **EXTERNAL DESIGN REVIEW REQUEST — IMPLEMENTATION OFF**

## Mission

Independently audit PR #344 before implementation planning. Try to falsify the design: find overclaimed historical authority, leakage/circularity, mismatch with the real-TD/downstream lane, incomplete support semantics, or missing hostile controls.

Return exactly one design verdict:

- `APPROVE_V3_FOR_IMPLEMENTATION_PLANNING`
- `APPROVE_WITH_REQUIRED_AMENDMENTS`
- `REJECT_V3_DESIGN`

This review cannot grant real-TD, target-selection, representation-selection, Stage4, synthetic-training, or real-training authority.

Global authority remains:
`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

## Live custody to verify first

The original V3/cross-lane design state was at `dd5d801665d03a8c9fbdb4a416bc11be460c5a7c`, but that is **not** the final controlling design-content head. External hostile review then identified decision-bearing defects and commit `a6036b834c16f50bf2c8e4cf57e40b4de6f0228e` added the prospective corrections amendment. The combined R5 re-audit and corrected current-state surfaces culminated at design-content head `70503fe3dae3afe4cebeb8e2e0fdc71d1598c54f`.

Commits after `70503fe3...` on PR #344 are pre-implementation readiness/custody/navigation documentation only and do not alter the corrected V3 scientific semantics. Verify the live PR head and inspect any delta after `70503fe3...` before auditing.

Other expected custody identities at handoff preparation:
- PR #328 fixture base: exact head `25bbdbe18aa5ed3c8a39a7e4295bc36de1e328ec`
- V80 qualified executable source: `b840067e4c9439e4cb4aa9e8c649ef2f6064a142`
- V80 qualified receipt SHA-256: `346407af801a7fabc5dbd27136dcf5c9abe61e87d438018b98da192333eb9c32`

If a head moved, determine whether the delta changes science/code or only documentation/receipts before changing conclusions.

## Read order

### PR #344
1. `docs/superpowers/specs/2026-10-13-lineage-composite-production-synthetic-design-v2.md`
2. `docs/agent/LINEAGE_COMPOSITE_PRODUCTION_SYNTHETIC_V2_REVIEW_DELTA_20261014.md`
3. `docs/superpowers/specs/2026-10-14-lineage-composite-production-synthetic-design-v3-amendment.md`
4. `docs/superpowers/specs/2026-10-14-lineage-composite-production-synthetic-v3-crosslane-alignment-addendum.md`
5. `docs/superpowers/specs/2026-10-14-lineage-composite-production-synthetic-v3-external-audit-corrections-v1.md`
6. V3 self-audits R1-R4 under `docs/agent/`
7. `docs/agent/LINEAGE_COMPOSITE_PRODUCTION_SYNTHETIC_V3_SELF_AUDIT_R5_EXTERNAL_CORRECTIONS_20261014.md`
8. `docs/agent/LINEAGE_COMPOSITE_PRODUCTION_SYNTHETIC_V3_CURRENT_STATE_20261014.md`
9. companion checklist: `docs/agent/LINEAGE_COMPOSITE_SYNTHETIC_V3_EXTERNAL_AUDIT_CHECKLIST_20261014.md`

### Synthetic custody
Read PR #324 V4 handoff, cold-start checklist/action queue, then PR #325 historical audit/no-repeat/guardrails. Do not restart Stage81/V72/V79/V80 archaeology absent a valid reopen trigger.

### Real-TD/downstream alignment
Read PR #323 current successor handoff, PR #322 current operating protocol, then the current gate surfaces. In particular, use PR #349-or-explicit-successor for G11/G12 split-bound support semantics rather than stale #342 boolean support. Also inspect current G8, G6, G7, R1 and TargetPortfolio surfaces.

Human candidate outcomes remain unread and must not be opened to choose synthetic rules.

## What the corrected V3 design adds

1. Broad V79-style challenge geometry plus V80-style sparse-positive estimable/non-estimable regimes, while keeping V79 historically `NOT_QUALIFIED` and V80 frozen separately.
2. Authenticated real-distribution observation calibration with provenance and anti-circularity rules.
3. Biological-evidence response separated from measurement-depth response using fixed already-generated observation bundles.
4. Biological novelty separated from measurement-domain OOD.
5. Current real-lane compatibility, including the external-review corrections for R1, G11/G12, C4/C6, G6 and G8.
6. Current 41,238-address semantics fail-closed; V75's 96 anonymous synthetic features are not canonical biological identity.

## External-review corrections now controlling

- R1 relation identity is the anchor/comparison **cell triplet** `q(i;j,k)=sign(d(i,j)-d(i,k))`; repaired molecular addresses define the ruler/views, not the relation triplet.
- G11/G12 synthetic rehearsal targets PR #349-or-explicit-successor semantics with reader partition binding and `SUPPORTED | UNSUPPORTED_STRUCTURAL | BLOCKED_EVIDENCE_CONTRACT`.
- Full C4 TargetPortfolio rehearsal is blocked until downstream code requires independently qualified C6 as the C4 comparator/prerequisite.
- G6 full positive rehearsal requires a substantive separately defined reference margin where applicable; sign alone is insufficient.
- G8 same-code-path rehearsal pins current executor mechanics or an explicit successor, including 25/50/75 depth references, displacement/support endpoints, multiplicity correction and the 599-resolution / `NOT_ESTIMABLE` behavior.

## Historical authority that must remain scoped

- Stage81A3: incomplete mechanistic ancestor only.
- A3R global-state pilot: not frozen; A3R three-state support is reusable.
- V72-V75: scoped population/measurement mechanics; V75 100K measurement architecture only.
- V77: qualitative generative lesson only.
- V78, Stage70, Stage71: negative/falsified priors, not positive authority.
- V53-V58: nuisance/specificity lessons, not human thresholds.
- PR #163/#178: query-normalization leakage firewall.
- PR #199/#312: oracle/teacher/student/recoverability separation.
- PR #318-#321: sealed producer/fit/controller pattern.
- PR #328: mechanics/interface fixture only.
- V79: permanently `NOT_QUALIFIED`; 291/292 gates passed, Q08 failed.
- V80: benchmark/package/custody/adjudication qualified; successor estimator not qualified.

## What has not happened

No V3 implementation plan is approved. No production generator/world has been implemented or realized. No V3 target-discovery result exists. No successor estimator has been qualified on V79+V80. No target/representation winner exists. Training and Stage4 remain off.

Requested approval scope is only: **is the written V2 + V3 + cross-lane + corrections design sound enough to proceed to implementation planning?**

## Required audit return

Provide:
1. custody/head verification;
2. findings with severity `CRITICAL|MAJOR|MODERATE|MINOR`, exact surface, reason, and minimum repair;
3. historical-authority assessment;
4. real-TD/downstream alignment assessment;
5. leakage/circularity assessment;
6. one of the three verdicts above;
7. if approved, state whether the next lawful action is exactly `WRITE_IMPLEMENTATION_PLAN_ONLY`.

Until that verdict returns:
`LINEAGE_COMPOSITE_PRODUCTION_SYNTHETIC_DESIGN_V3__EXTERNAL_AUDIT_REQUESTED__IMPLEMENTATION_OFF__TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
