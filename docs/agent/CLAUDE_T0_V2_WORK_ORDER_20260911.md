# Claude Work Order — Finish T0 V2 / V21-T1 Repair Candidate

Date: 2026-09-11
Status: `CLAUDE_READY_T0_V2_CONTINUATION__NO_TRAINING_AUTHORITY`

## Read first

This file is the immediate work order for Claude/Codex continuation. It is intentionally narrow: finish the repaired T0 V2/V21-T1 candidate and make it reviewable. Do **not** start V5 production training, open protected data, or add new biology/architecture while this work order is open.

Start from this branch:

`handoff/jepa-t0-v2-claude-ready-20260911`

This branch was created from the latest observed integrated/restored V21 repair head:

`repair/t0-v21-authority-restoration-20260911 @ 42efc55f0aae7770c485855be873cccba4abd732`

The older ASAP handoff branch exists and remains useful historical context:

`handoff/jepa-new-chat-20260911-asap-repair-status @ 5ee85fc84bdcf3fd3c5222bbf3c8c2ba27a3b8d9`

But that handoff was created from `93abcf50e89778585bda1e20f2eab824cc6bae77`. The active repair branch later advanced two commits to `42efc55f...`, adding branch-wide V21 guard coverage. Do not start from stale `93abcf50...` unless explicitly reviewing that historical state.

## Non-negotiable prohibitions

Until this work order closes and receives external review:

- no S0-S4 production selection run;
- no real power-gate verdict;
- no AT8 opening;
- no protected partition opening;
- no `reader_validation` opening;
- no oracle opening;
- no T0 freeze claim;
- no V5 production training;
- no training checkpoints or optimizer steps;
- no pathology-guided tuning.

Standing rule:

`IF_CONFIRMATION_DATA_COULD_CHANGE_A_DESIGN_CHOICE_DO_NOT_LOOK`

## Known live refs to re-fetch before acting

Re-fetch these before modifying anything:

- `main`
- `handoff/jepa-t0-v2-claude-ready-20260911`
- `repair/t0-v21-authority-restoration-20260911`
- `repair/t0-v21-integrated-authority-regression-20260911`
- `review/t0-v21-successor-20260911`
- `review/t0-v21-integrated-restored-20260911`
- `review/t0-v21-integrated-candidate-20260911`
- `t0/v20-pathology-blind-materialization-20260908`
- `planning/v5-full-population-cheat-proofing-20260909`

Observed anchors at this work-order creation:

- `main @ ba3f2a1200d0bbaf4b9ee0d7d16ddc17341d779f`
- `repair/t0-v21-authority-restoration-20260911 @ 42efc55f0aae7770c485855be873cccba4abd732`
- `review/t0-v21-integrated-restored-20260911 @ 93abcf50e89778585bda1e20f2eab824cc6bae77`
- `review/t0-v21-successor-20260911 @ 3a8c8e3e5ca84d38eb363e9791e1c86c854a55af`
- `repair/t0-v21-integrated-authority-regression-20260911 @ 9a861b41607b16cb40a8240ecda025c9447514ae`
- bad/truncated authority head: `repair/t0-v21-authority-hardening-20260911 @ 9f98320f03e19577527b2153159ea0df2c62babd`
- known-good authority source before truncation: `a36fd209b40aa9c28cd3d6790bda1fe5054a1923`

## What is already fixed on the latest restoration branch

The latest restoration branch is ahead of `review/t0-v21-successor-20260911`, so it should preserve the executor successor behavior:

- `EFFECT_TRANSPORT_STATUS = "OPEN"`;
- production verdict capability remains disabled;
- `decision_capable_power_gate()` must fail closed with `STOP_T0_V21_EFFECT_TRANSPORT_NOT_AUTHORITY_BOUND`;
- planning arithmetic must not return a `clears_gate` authorization key.

It also adds authority restoration/API-surface guards:

- preserved legacy authority source: `scripts/v4/t0_v21_authority_legacy_v1.py.txt`;
- active authority source: `scripts/v4/t0_v21_authority_v1.py`;
- API-surface guard: `scripts/v4/test_t0_v21_authority_api_surface_v1.py`;
- restoration guard: `scripts/v4/test_t0_v21_authority_restoration_v2.py`;
- workflow guard: `.github/workflows/v21-authority-restoration-tests.yml`.

Critical regression guard behavior expected:

```python
assert authority.EFFECT_TRANSPORT_STATUS == "OPEN"
with pytest.raises(RuntimeError, match="STOP_T0_V21_EFFECT_TRANSPORT_NOT_AUTHORITY_BOUND"):
    authority.decision_capable_power_gate()
```

The API-surface guard must parse the exact preserved legacy source without importing it and fail if any historical public symbol disappears from the active successor.

## Required verification sequence

Run from a clean checkout or clean git archive extraction. Do not use a locally reconstructed partial tree.

### 1. Confirm branch ancestry and no stale base

```bash
git fetch origin --prune
git checkout handoff/jepa-t0-v2-claude-ready-20260911
git rev-parse HEAD
git merge-base --is-ancestor 3a8c8e3e5ca84d38eb363e9791e1c86c854a55af HEAD
git merge-base --is-ancestor 93abcf50e89778585bda1e20f2eab824cc6bae77 HEAD
```

Expected: both `merge-base --is-ancestor` commands exit 0. If either fails, stop and report `STOP_T0_V2_CLAUDE_READY_BRANCH_NOT_INTEGRATED`.

### 2. Compile exact active modules

```bash
python -m py_compile \
  scripts/v4/t0_v21_authority_v1.py \
  scripts/v4/t0_v21_selection_and_power_v1.py \
  scripts/v4/t0_v21_measurement_artifact_v1.py \
  scripts/v4/t0_v21_target_freeze_v1.py
```

Expected: zero errors.

### 3. Run V21 authority/restoration/API-surface tests

```bash
python -m pytest -q \
  scripts/v4/test_t0_v21_authority_v1.py \
  scripts/v4/test_t0_v21_authority_restoration_v2.py \
  scripts/v4/test_t0_v21_authority_api_surface_v1.py
```

Expected: pass, zero skipped.

### 4. Run executor, selection/power, measurement/freeze tests

```bash
python -m pytest -q \
  scripts/v4/test_t0_v21_selection_and_power_v1.py \
  scripts/v4/test_t0_v21_measurement_and_freeze_v1.py
```

Expected: pass, zero skipped.

### 5. Run mutation audit if available on the branch

```bash
python scripts/v4/mutation_audit_t0_v21_selection_and_power_v1.py
```

Expected: no surviving executable mutations. If the script reports unreachable mutations, include the proofs in the report; do not count them as caught unless the audit does.

### 6. Confirm the bad branch would have failed the new guard

Use an isolated checkout or worktree. Do not modify the bad branch.

```bash
git checkout repair/t0-v21-authority-hardening-20260911
python -m pytest -q scripts/v4/test_t0_v21_authority_api_surface_v1.py
```

Expected: fail on missing historical public symbols or equivalent API truncation. If it passes on `9f98320f...`, stop and report `STOP_T0_V2_API_SURFACE_GUARD_NOT_SENSITIVE`.

Then return to the Claude-ready branch:

```bash
git checkout handoff/jepa-t0-v2-claude-ready-20260911
```

### 7. Produce a short exact-head verification report

Create:

`docs/agent/T0_V2_CLAUDE_READY_VERIFICATION_20260911.md`

The report must include:

- exact branch and HEAD SHA;
- exact command list;
- pass/fail/skip counts;
- mutation audit result;
- explicit statement that `EFFECT_TRANSPORT_STATUS` remains `OPEN`;
- explicit statement that production power verdict capability remains disabled;
- explicit statement that S0-S4, AT8, reader_validation, oracle and training remain unauthorized;
- diff summary against `repair/t0-v21-authority-restoration-20260911` if further changes were required.

## Acceptance terminal for this work order

The only acceptable terminal from this work order is a review-ready, not-frozen candidate:

```text
PASS_T0_V2_REPAIRED_CANDIDATE_CLEAN_EXACT_HEAD
V21_AUTHORITY_API_RESTORED = TRUE
EFFECT_TRANSPORT_STATUS = OPEN
POWER_GATE_PRODUCTION_VERDICT_CAPABILITY = DISABLED
S0_S4_EXECUTION_AUTHORITY = FALSE
FRESH_CONFIRMATION_AUTHORITY = FALSE
TRAINING_AUTHORITY = FALSE
```

Anything stronger is overclaiming.

## What comes after this, not during it

After the repaired candidate is clean and externally reviewed, the next scientific blocker is the effect-transport derivation/calibration. Do not solve it by reading a correction factor off observed null spread or by treating whole-pipeline permutation significance as a magnitude mapping.

The separate future architecture ideas — observation operators, basis stability, evidence/depth response curves, technology-held-out transfer, and biological-vs-measurement OOD — remain important but are not part of this emergency T0 V2 repair closure.
