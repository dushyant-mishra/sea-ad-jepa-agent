# Claude action items now — 2026-09-09

## 1. Pull the dataset-first review branch

`review/t0-r5-dataset-first-framework-20260909`

Read these first:

- `docs/agent/CLAUDE_NEXT_ACTIONS_T0_REAL_B2_AUTHORITY_20260909.md`
- `docs/agent/T0_REAL_B2_ACCEPTANCE_CHECKLIST_20260909.md`
- `docs/agent/OPEN_REVIEW_ATTACKS_AFTER_R5_20260909.md`

## 2. Commit the production harness

Do not run from scratchpad.

Commit:

- `scripts/v4/run_t0_b2_raw_source_population_authority_v1.py`
- `scripts/v4/verify_t0_b2_raw_source_population_authority_v1.py`

## 3. Resolve the execution permission blocker

The previous production command was denied by Claude Code auto mode. Ask for permission or run through an allowed explicit production command path. Do not disguise the production run as a test.

## 4. Run the real 20,804-row authority

Required final line must include:

- rows attempted `20804`
- rows proven `20804`
- skipped `0`
- duplicates `0`
- mismatches `0`
- population root
- artifact package root

## 5. Replay from disk

Verifier must read only disk artifacts plus external expected roots.

## 6. Report back

Report exact artifact paths, bytes, SHA-256, package roots, stored roots, recomputed roots, expected roots, replay verdict, and unchanged downstream gates.
