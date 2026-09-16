# JEPA New-Chat Instructions — 2026-09-16

Continue the existing JEPA project. **Do not restart from scratch.**

## First actions
1. Read `START_HERE.md`.
2. Read `docs/agent/JEPA_LATEST_HANDOFF_POINTER.json`.
3. Read `docs/agent/JEPA_NEW_CHAT_HANDOFF_20260916_V5_CURRENT.md` completely.
4. Read `docs/agent/JEPA_NEW_CHAT_HANDOFF_STATE_20260916_V5_CURRENT.json`.
5. Read `docs/agent/JEPA_HISTORICAL_AUDITS_INDEX_20260915.md` at `main @ c8898923fc10ffa5ef0662b04908b0d94bcb158b`.
6. Re-fetch live heads for `main`, `impl/v5-current-target-authority-successors-20260915`, and the current handoff branch.
7. Inspect any commits newer than the recorded SHAs before doing work.

## Historical classification
Before new work use:
`ALREADY_AUDITED | SUPERSEDED | OPEN | CHANGED_INPUT_REQUIRES_REQUALIFICATION`

Do not rerun Layer 2, T0, T1/C2, base-estimand recovery, FULL104 lineage, or generic target-identity-shortcut discovery.

## Current job
Continue **target-address Stage-A structural qualification** on the current implementation.

Inspect exact current source/tests for:
- target-address/query authority
- target-identity shortcut gate
- teacher-target semantics
- EMA presentation/timescale
- teacher-target receipt
- preexecution contract
- authority closure
- protected registry
- checkpoint guard
- optimizer guard

Build a dependency map for student input, teacher target, target-address provider, query identity, observation state, stop-gradients, gradient reachability, teacher/EMA reachability, checkpoint/restart/replay, and shared versus leaked identity/context paths.

Run static/unit tests and carryover scans. Add fail-closed tests/repairs where possible. Do not force PASS when evidence is absent.

## Carryover firewall
Check literal and semantic inheritance of:
- fixed 6-block / 48-tensor assumptions
- 128x8 historical geometry
- EMA `.996`
- historical mask fractions
- old proposal/source/operator coefficients
- packing/horizon/affine choices
- old seeds
- historical widths/ranks as current geometry
- stale authority roots
- visibility/QC as molecular values
- target-specific lookup/identity leakage

## Protected data
Keep training OFF. Do not execute or inspect protected `D_shared` outcomes. Do not use confirmation data to choose open design.

## CPU-to-GPU boundary
Finish all feasible static/CPU/unit/governance work here before handing heavy execution to Claude.

Heavy FULL104 path:
`D:/Jepa project/outputs/full104_v014_20260826/03_phase2_state_derivation_v1/expression_level4/`

It is >30 GB and already accessible on the GPU machine. Do not ask for upload.

When GPU work is genuinely necessary, provide exact scripts/commands, input hashes, current source revision, fail-closed gates, and receipt fields. Never fabricate a heavy-run result.

## Completion standard
A receipt/file existing is not a PASS. Skipped/nonexecuted critical tests are not green. Verify actual executed evidence and preserve `training_authorized=false` until all required authorities/runtime conditions are satisfied.
