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

PR #344 design-content state was completed at head `dd5d801665d03a8c9fbdb4a416bc11be460c5a7c`. Subsequent commits on the same branch are documentation/audit-packaging commits only. The exact current packaged head is recorded in PR #344 external-audit pointer comment `6160369417`; verify the live PR head before auditing and inspect any delta after that pointer.

Other expected custody identities at handoff preparation:
- PR #324 synthetic operational handoff: `bb5ca60c2c5ebe46e486116851174607490fb030`
- PR #325 synthetic historical audit/no-repeat: `bfeb2b868aa84cb94594869ef5cb196af286db90`
- PR #322 real-TD executable audit/custody: `9a3de06861f19b71ee3b1d7e2b1b15b85c811571`
- PR #323 real-TD navigation/handoff: `606ee8706692f202b8a44fe04008dbe95fcb71f4`
- PR #328 fixture base: exact head `25bbdbe18aa5ed3c8a39a7e4295bc36de1e328ec`
- V80 qualified executable source: `b840067e4c9439e4cb4aa9e8c649ef2f6064a142`
- V80 receipt: `346407af801a7fabc5dbd27136dcf5c9abe61e87d438018b98da192333eb9c32`

If a head moved, determine whether the delta changes science/code or only documentation/receipts before changing conclusions.

## Read order

### PR #344
1. `docs/superpowers/specs/2026-10-13-lineage-composite-production-synthetic-design-v2.md`
2. `docs/agent/LINEAGE_COMPOSITE_PRODUCTION_SYNTHETIC_V2_REVIEW_DELTA_20261014.md`
3. `docs/superpowers/specs/2026-10-14-lineage-composite-production-synthetic-design-v3-amendment.md`
4. `docs/superpowers/specs/2026-10-14-lineage-composite-production-synthetic-v3-crosslane-alignment-addendum.md`
5. V3 self-audits R1-R4 under `docs/agent/`
6. `docs/agent/LINEAGE_COMPOSITE_PRODUCTION_SYNTHETIC_V3_CURRENT_STATE_20261014.md`
7. companion checklist: `docs/agent/LINEAGE_COMPOSITE_SYNTHETIC_V3_EXTERNAL_AUDIT_CHECKLIST_20261014.md`

### Synthetic custody
Read PR #324 V4 handoff, cold-start checklist/action queue, then PR #325 historical audit/no-repeat/guardrails. Do not restart Stage81/V72/V79/V80 archaeology absent a valid reopen trigger.

### Real-TD/downstream alignment
Read PR #323 `JEPA_LANE_SUCCESSOR_HANDOFF_V4_20261014.md`, PR #322 `JEPA_SUCCESSOR_OPERATING_PROTOCOL_20261014.md`, then current gate surfaces PR #342 G11/G12, #343 G8, #345 G6, #346 G7, #347 R1, and #332 TargetPortfolio.

Human candidate outcomes remain unread and must not be opened to choose synthetic rules.

## What V3 added

1. Explicitly combines broad V79-style challenge geometry with V80-style sparse-positive estimable/non-estimable regimes, while keeping V79 historically `NOT_QUALIFIED` and V80 frozen separately.
2. Requires authenticated real-distribution observation calibration with provenance and anti-circularity rules.
3. Separates biological-evidence response from measurement-depth response. Evidence ladders reveal nested subsets of a fixed pre-generated observation bundle; count/depth/capture changes belong only to measurement robustness.
4. Separates biological novelty from measurement-domain OOD.
5. Adds explicit compatibility with current G7, G8, G11/G12, G6, R1 and TargetPortfolio mechanics without importing human thresholds or outcomes.
6. Makes current 41,238-address semantics fail-closed and explicitly prohibits treating V75's 96 anonymous synthetic features as canonical biological identity.

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

## Internal defects already found and repaired

- evidence-response language could be confused with count/depth thinning;
- evidence-level changes could regenerate modality/operator realizations;
- V75 96 anonymous features could be overextended to 41,238-address semantics;
- real-TD/downstream alignment was initially implicit rather than explicitly bound.

The auditor should look for additional defects, not merely confirm these repairs.

## What has not happened

No V3 implementation plan is approved. No production generator/world has been implemented or realized. No V3 target-discovery result exists. No successor estimator has been qualified on V79+V80. No target/representation winner exists. Training and Stage4 remain off.

Requested approval scope is only: **is the written V2 + V3 + cross-lane design sound enough to proceed to implementation planning?**

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
`LINEAGE_COMPOSITE_PRODUCTION_SYNTHETIC_DESIGN_V3__CROSSLANE_ALIGNED__EXTERNAL_AUDIT_REQUESTED__IMPLEMENTATION_OFF__TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
