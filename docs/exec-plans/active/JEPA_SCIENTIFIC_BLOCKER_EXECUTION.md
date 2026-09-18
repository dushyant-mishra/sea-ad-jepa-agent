# JEPA Scientific Blocker Execution

Date: 2026-09-18

Status: `FULL104_MASKING_CONTROL_CALIBRATION_IMPLEMENTED__GPU_RUNTIME_RECEIPTS_AND_CAPACITY_CALIBRATION_NEXT__TERMINAL_OUTCOMES_UNOPENED__TRAINING_OFF`

Working implementation branch:

`impl/v5-full104-masking-redteam2-20260918`

Scientific implementation anchor (source/test/data bytes):

`86692cde7e61fe4beae7fff4070bd376a8090af2`

Draft implementation PR:

`#20` based on `impl/v5-full104-masking-redteam-freeze-20260918`

## Scientific invariant

The foundation objective is biological/cellular-state inference from partial RNA, including query-local state associated with a supplied canonical molecular address. It is not hidden-gene scalar reconstruction.

Expression ridge/correlation/nonlinear models are shortcut diagnostics only. Reducing expression predictability does not itself establish biological-state recovery.

Permanent order:

`DATA -> SUPPORT/ESTIMABILITY -> SCIENTIFIC ESTIMAND -> TARGET SEMANTICS -> PRODUCTION GEOMETRY -> MODEL`

`IF_CONFIRMATION_DATA_COULD_CHANGE_A_DESIGN_CHOICE_DO_NOT_LOOK`

## Current FULL104 substrate

- 4,553,407 cells
- 104 donors
- 42 operators
- 41,238 addresses
- 17,186 strict common-core addresses
- 8,915 authenticated Level-4 sparse blocks
- block-manifest SHA-256: `66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29`
- canonical registry SHA-256: `7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd`
- observation-state SHA-256: `852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537`
- GPU Level-4 root: `D:/Jepa project/outputs/full104_v014_20260826/03_phase2_state_derivation_v1/expression_level4/`

Historical Stage81/T1/discovery files are support/provenance only and must never substitute for FULL104.

## Changed-input census boundary

The corrected read-only census established:

- strict-core measured-zero frequency `0.832983`
- strict-core nonzeros `13,069,917,135`
- strict-core measured zeros `65,184,935,567`
- `17,053 / 17,186` strict-core addresses estimable in every donor-held-out fold
- 104 donors but Kish ESS about 42 donor-equivalents

Consequences:

- strict `MEASURED_SCALAR` support is required;
- measured zero remains measured evidence, not structural missingness;
- masking eligibility is value-independent over strictly measured non-target addresses;
- the discovery-era 15% burden from an 800-address universe is not terminal authority.

The GPU machine must still regenerate and hash-bind the actual V2 census summary/split/target-eligibility receipts from the real `pass1.npz`.

## Current implemented chain

Current Git implementation contains and must use:

- canonical reference: `src/sea_ad_jepa/v5/full104_masking_qualification_runner_v1.py`
- authenticated streaming executor: `src/sea_ad_jepa/v5/full104_masking_streaming_executor_v1.py`
- parameter authority V2: `src/sea_ad_jepa/v5/masking_qualification_parameters_authority_v2.py`
- burden authority V2 / ladder V2
- census receipt/builder V2
- calibration-only cache contract/builder/evaluator
- target-panel sizing V2, selector V2, TargetPanelAuthorityV3 builder
- OuterSplitAuthorityV1 builder
- PrecisionAuthorityV4 builder
- nonlinear model-capacity V1 + row-cap calibration V2 + cache evaluator
- masking decision V2
- masking execution authority V4
- final RunContract V4 schema
- anti-spillover V2

The calibration cache role is permanently:

`CONTROL_CALIBRATION_ONLY__FORBIDDEN_FOR_TERMINAL_MASKING_QUALIFICATION_V1`

Terminal masking input must be:

`AUTHENTICATED_FULL104_LEVEL4_BLOCK_STREAM_V1`

## Historical findings: correct role

The September 17 discovery lineage supports a candidate worth independent confirmation:

- targeted partner cap 8
- ridge candidate pool 64
- ridge score features 32
- ridge alpha `1/100`
- PREFIX inner folds 3
- PREFIX candidates 20
- PREFIX floor `1/20`
- PREFIX reduction `1/2`

Historical evidence may define the pre-FULL104 confirmation candidate and nonlinear model shape. It may not supply current data, target lists, folds, burden, seed, row cap, teacher health, or terminal PASS.

## Current exact-head verification status

Do not inherit old green status as verification of the latest successor bytes.

At the scientific implementation anchor `86692cde...`, GitHub records no workflow runs. The older independently green anchor `8ee5d0a5...` remains useful historical implementation evidence only.

First takeover action is focused CI on the exact current implementation bytes, fail closed on any skip/new failure.

## Immediate authoritative sequence

1. Re-fetch the live implementation branch and PR #20. If source/test/data bytes changed from `86692cde...`, classify the delta as `CHANGED_INPUT_REQUIRES_REQUALIFICATION`.
2. Run the focused FULL104 masking/calibration CI on the exact current implementation bytes; fail closed on skips.
3. Refresh/supersede `scripts/agent/v5_full104_masking_gpu_preflight_20260917.ps1`. It is stale for the V4/cache-calibrated chain and must not be used as final GPU authority.
4. Build the explicit pre-FULL104 confirmation `MaskingQualificationParametersAuthorityV2` instance with `scripts/agent/build_full104_masking_parameters_authority_v2_20260918.py`. This re-authorizes only the frozen discovery-defined candidate; it does not authorize a burden or training.
5. On the canonical GPU worktree, regenerate the census V2 summary, split, and target-eligibility receipts from the real `pass1.npz`, then build census authority V2.
6. Build the authenticated calibration-only cache once from current FULL104 Level-4 blocks plus the canonical registry. Verify hashes, role, all 104 donors, and full-donor closure. Never use this cache as terminal input.
7. Run the target-panel capacity ladder `128 -> 256 -> 512 -> 1024` from the authenticated cache with exact replay. Stop at the first qualifying rung.
8. Build the target-selection receipt, then TargetPanelAuthorityV3.
9. Build OuterSplitAuthorityV1 from the current split receipt and PrecisionAuthorityV4 from current support + target panel + split.
10. Build nonlinear model-capacity authority V1. Run the nonlinear row-cap ladder `64 -> 128 -> 256 -> 512 -> 1024` from the authenticated cache with exact replay; stop at first qualifying cap.
11. Close the currently missing final-authority builder gaps before terminal execution:
    - add/use a current builder for `NonlinearChallengeAuthorityV3` (the existing `build_full104_nonlinear_challenge_authority_v2_20260918.py` is V2 and is not final authority);
    - add/use a current builder for `MaskingRngReplayAuthorityV2`;
    - add/use a current builder for `MaskingQualificationRunContractV4`.
    Each builder must bind exact current roots/source hashes and have behavior tests plus independent review.
12. Freeze the final V4 run-contract instance before inspecting terminal masking-policy outcomes.
13. Rebuild and validate `docs/agent/CURRENT_WORK_CHECKPOINT.json` on the final committed GPU worktree head and independently verify the package.
14. Only then execute terminal FULL104 masking at 5%. Do not inspect 10% if 5% fully qualifies. Continue upward only after explicit failure and stop at the first fully qualifying burden.
15. Masking PASS still does not authorize training. Continue healthy-current-teacher remaining-RNA necessity, measurement robustness, production geometry + geometry-specific memorization, runtime provenance, and final explicit training authority.

## Executability notes

Do not treat bare script names as commands. The builders require explicit runtime paths/receipts. Use the current new-chat commands document for complete argument templates.

Both cache-capacity evaluators intentionally return exit code `3` after Run A once they have written replay matrices and a `REPLAY_REQUIRED_*` status. Treat exactly that combination as the expected handoff to Run B; any other nonzero code is a STOP. Run B must write to a different output directory and consume the unchanged Run-A matrices.

The following current script is stale and non-authoritative until refreshed:

`scripts/agent/v5_full104_masking_gpu_preflight_20260917.ps1`

The following direct-stream calibration path is superseded by the authenticated cache route:

`scripts/agent/run_full104_target_panel_capacity_calibration_v1.py`

The following builder is V2 only and must not be used as final nonlinear authority:

`scripts/agent/build_full104_nonlinear_challenge_authority_v2_20260918.py`

## Hard boundaries

- `TRAINING_OFF`
- `NO_D_SHARED_OUTCOME_EXECUTION_OR_INSPECTION`
- `NO_PATHOLOGY_DEV_SEALED_OUTCOME_ACCESS_WHILE_DESIGN_OPEN`
- no smaller/historical/unauthenticated substitute for FULL104
- no calibration cache as terminal masking input
- no placeholder hashes
- no free PASS strings without computed/bound evidence
- no post-outcome retuning
- no burden escalation after first full qualification
- no reopening settled T0/T1/QID/F1/Layer-2/Stage-A/streaming-parity work without changed input
- no historical T1 checkpoint as healthy-current-teacher authority

## Governance

`AGENTS.md` requires a validator-built machine checkpoint at `docs/agent/CURRENT_WORK_CHECKPOINT.json`.

`docs/agent/CURRENT_WORK_CHECKPOINT_STATE.json` is the tracked scientific-lane declaration. Its pinned authorities must be stable implementation-governance files. Docs-only handoffs may update `START_HERE.md`; therefore `START_HERE.md` must not be hard-pinned in the tracked checkpoint state in a way that invalidates every handoff commit.

This connector environment cannot truthfully generate the machine/worktree-bound checkpoint. The canonical GPU worktree must build and validate it after final source/authority freeze and again immediately before terminal execution.
