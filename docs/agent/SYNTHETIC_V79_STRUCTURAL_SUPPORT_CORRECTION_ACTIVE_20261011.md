# Synthetic/V79 structural-support correction — ACTIVE — 2026-10-11

Standing lane: synthetic/V79 Bayesian geometry only. Target discovery remains separate.

Controller correction authority: PR #286 comment `6113874774`.

Current implementation branch:
`fix/v79-structural-support-replay-20261011`

Branch base:
`ae706096244b38e7691a3103fcb8dcd445745533` (PR #286 frozen-contract draft head).

Purpose: correct the cheap exact-S174 replay so structurally unmeasured cell-gene entries never enter detection/positive likelihoods or metrics. The correction must preserve the frozen replay panel/folds/seed/model nesting/operator-lambda grid/support logic.

Required TDD before physical replay:
- measured zero remains a real detection zero;
- structurally unmeasured is excluded;
- fully unmeasured source×gene is excluded;
- partial matrix-level NPH52-style support is handled exactly;
- poison-value invariance proves unmeasured values are never read;
- all-measured fixtures reproduce the legacy path;
- existing operator/fold/panel/support invariants remain green.

Planned output after implementation: corrected masked exact-S174 replay plus machine-readable old-vs-masked A-H delta report. Qualification world generation remains OFF until controller review of that corrected evidence.

Current terminal:
`STRUCTURAL_SUPPORT_CORRECTION_IMPLEMENTATION_ACTIVE__MASKED_S174_REPLAY_PENDING__QUALIFICATION_WORLD_GENERATION_OFF__REAL_TRAIN_POSTERIOR_OFF__FACTORIAL_SCIENCE_OFF__TRAINING_OFF`
