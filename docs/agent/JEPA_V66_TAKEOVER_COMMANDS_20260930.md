# JEPA V66 takeover commands — 2026-09-30

## 1. Refresh live branches

```bash
git fetch --all --prune

git log -1 --oneline origin/chatgpt/v64-privileged-information-recoverability-20260930
git log -1 --oneline origin/claude/v64-exact-sampler-successor-20260930
```

Last audited Claude head at handoff creation:

`6c265d9c5eb53ac705be60e08b0fac771d2159f4`

If Claude is ahead, inspect the delta before accepting any new status.

## 2. Switch to primary ChatGPT audit/architecture branch

```bash
git switch chatgpt/v64-privileged-information-recoverability-20260930
git pull --ff-only
```

## 3. Read current handoff

```bash
cat docs/agent/JEPA_LATEST_HANDOFF_POINTER.json
cat docs/agent/JEPA_NEW_CHAT_HANDOFF_20260930_V66_CURRENT_SUCCESSOR.md
cat docs/agent/JEPA_HANDOFF_STATE_20260930_V66.json
cat results/v64/V64_PHASE_B_B6_AVAILABILITY_INDEPENDENT_AUDIT_V1.json
cat docs/agent/V66_CLAUDE_NEXT_INSTRUCTIONS_20260930.md
cat docs/agent/archive/chat_runtime_20260930_v3/README.md
cat docs/agent/archive/chat_runtime_20260930_v3/CHAT_RUNTIME_EXCLUSIVE_ASSET_CUSTODY_20260930_V3.json
```

## 4. Current hard state

Do not downgrade these without contradictory evidence:

- Phase A V3 = ACCEPTED, retained N=13,175.
- Phase-B measurement substrate = ACCEPTED as contract-complete.
- Phase-B aggregate binding = `2a5404842ec64028789ef2b9cdc13604d80e4aee39298faa8faba70071894f52`.
- B6 v2 availability = ACCEPTED.
- Stage 4 = NOT AUTHORIZED.
- correspondence = UNOPENED.
- TRAINING = OFF.
- multimodal training = OFF.
- Morabito = PROTECTED.
- TD60 = BLOCKED.

## 5. Audit any Claude advancement

```bash
git diff --stat 6c265d9c5eb53ac705be60e08b0fac771d2159f4..origin/claude/v64-exact-sampler-successor-20260930
git log --oneline 6c265d9c5eb53ac705be60e08b0fac771d2159f4..origin/claude/v64-exact-sampler-successor-20260930
```

For each changed file:

- inspect source, receipts and tests;
- distinguish scientific/statistical/provenance/schema/test/prose defects;
- independently recompute structural identities;
- do not accept execution just because a commit says PASS.

## 6. If Claude proposes Stage 4

Do **not** run correspondence immediately.

First require a prospective Stage-4 execution authority that binds:

- accepted Phase-B shard/T5/availability digests;
- exact metacell partition;
- exact T3/T4/T5 consumer schema;
- frozen state vocabulary;
- GENE_BALANCED primary;
- PROMOTER_EQUAL mandatory companion;
- EDGE_EQUAL sensitivity;
- donor bootstrap only;
- 4,000 replicates;
- seed 20260929;
- frozen R1/R2/R3 semantics;
- no post-outcome nuisance/weight/rank/metacell changes.

Then STOP FOR AUDIT.

## 7. Recoverability lane

Read:

```bash
cat docs/agent/V65_PRIVILEGED_RECOVERABILITY_PRECISION_DECISION_CONTRACT_V2_20260930.md
cat docs/agent/V65_PRIVILEGED_RECOVERABILITY_EXECUTION_MECHANICS_CONTRACT_20260930.md
cat docs/agent/V65_PRIVILEGED_RECOVERABILITY_TRAIN_VALIDATION_EXECUTOR_CONTRACT_20260930.md
cat results/v64/V65_PRIVILEGED_RECOVERABILITY_TRAIN_VALIDATION_PREFLIGHT_RECEIPT_V1.json
```

Real TRAIN+VALIDATION execution remains authorization-gated.

TEST remains sealed.

## 8. Multimodal architecture lane

Safe current work is synthetic/no-claim only.

Read:

```bash
cat docs/agent/V65_NESTED_RNA_MULTIMODAL_STUDENT_ARCHITECTURE_CONTRACT_20260930.md
cat results/v64/V65_FULL104_LIKE_NESTED_STUDENT_TEACHER_SYNTHETIC_QUALIFICATION_V1.json
cat results/v64/V65_NESTED_STUDENT_TEACHER_SYNTHETIC_TRAINING_MECHANICS_QUALIFICATION_V1.json
```

Do not interpret synthetic R² values as biological evidence or production thresholds.

## 9. Do not redo

Do not repeat:

- S50 / exact supplement;
- 64/64 sampler qualification;
- Phase-A funnel/provenance;
- Phase-B B1-B6;
- 32,174 vs 32,153 interval investigation;
- T6/T7 audit;
- promoter ledger source-byte/interval repair;
- canonical donor split;
- u0 compatibility smoke;

unless an input digest materially changes.
