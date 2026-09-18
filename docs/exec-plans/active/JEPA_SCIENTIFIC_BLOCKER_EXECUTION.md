# JEPA Scientific Blocker Execution

Date: 2026-09-18

Status: `FULL104_MASKING_CURRENT_PREFLIGHT_VERIFIED__GPU_RUNTIME_RECEIPTS_AND_CONTROL_CALIBRATION_NEXT__TERMINAL_OUTCOMES_UNOPENED__TRAINING_OFF`

Working implementation branch:

`impl/v5-full104-masking-redteam2-20260918`

Scientific implementation anchor (source/test/data bytes):

`bd968ea4be40da649a443916197e2985b5c8749f`

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

Historical Stage81/T1/discovery files are support/provenance only and must never substitute for FULL104. A historical finding may motivate a prospective FULL104 hypothesis or model-shape candidate, but it cannot supply a FULL104 data root, target list, fold, burden, seed, row cap, selected policy, authority digest, or PASS state unless a current authority explicitly re-authorizes that exact role and binds current roots.

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
- burden-free TargetEvidenceBudgetTemplateAuthorityV1 + current builder
- MaskingQualificationDesignAuthorityV2 + current builder
- ControlCalibrationPrecisionPlanV2
- final NonlinearChallengeAuthorityV3 / RNG replay V2 builders
- final RunContract V4 schema + path-only current builder `scripts/agent/build_full104_masking_run_contract_v4_20260918.py`
- anti-spillover V2 plus exact-current semantic authority ingress pins

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

The focused FULL104 masking workflow is verified on the current scientific source/test/workflow anchor `bd968ea4be40da649a443916197e2985b5c8749f`.

GitHub Actions run `35384493193` completed SUCCESS. The full regression step and the explicit fail-closed-on-skips step both completed SUCCESS after adding the current two-mode FULL104 GPU preflight validator/wrapper and its anti-spillover behavior tests.

The verified predecessor anchors `ca643f5d...` (run `35374354706`) and `bdb779ce...` (run `35382450942`) remain historical implementation evidence only. The current anchor additionally canonically binds the no-extra-retained-floor policy and exact-current representation/teacher/support/registry semantic authorities at FULL104 ingress. The earlier collection failure `35373486676` was caused by a stale nonlinear-calibration V1 test reference and was narrowly repaired before the successful successor runs.

Historical green anchor `8ee5d0a5...` remains historical evidence only. Historical or smaller-run green status never substitutes for exact-current-head verification.

Exact-head focused CI is therefore `ALREADY_AUDITED__PASS_NO_SKIPS` at `bd968ea4...`.

## Immediate authoritative sequence

1. Re-fetch the live implementation branch and PR #20. If source/test/workflow/data bytes changed from `bd968ea4...`, classify the delta as `CHANGED_INPUT_REQUIRES_REQUALIFICATION`.
2. Exact-head focused CI at `bd968ea4...` is audited PASS/no-skips in run `35384493193`; rerun it after any source/test/workflow change.
3. Use the current two-mode preflight only: `scripts/agent/v5_full104_masking_gpu_preflight_20260918.ps1` plus `scripts/agent/validate_full104_masking_gpu_preflight_v1.py`. Calibration mode must not require terminal artifacts; terminal mode must reject the calibration cache as terminal input and must bind the final machine checkpoint and live execution-source hashes.
4. Build the explicit pre-FULL104 confirmation `MaskingQualificationParametersAuthorityV2` instance from the frozen discovery provenance. This is an explicit re-authorization of a pre-FULL104 candidate only; it does not authorize burden, targets, folds, seeds, row caps, outcomes, or training.
5. On the canonical GPU worktree, regenerate the census V2 summary, split, and target-eligibility receipts from the real authenticated `pass1.npz`, then build census authority V2.
6. Build the authenticated calibration-only cache once from current FULL104 Level-4 blocks plus the canonical registry. Verify hashes, role, all 104 donors, and full-donor sufficient-statistic closure. Never use this cache as terminal or training input.
7. Run the target-panel capacity ladder `128 -> 256 -> 512 -> 1024` from the authenticated cache with exact replay. Stop at the first qualifying rung. Build the target-selection receipt and TargetPanelAuthorityV3 from current receipts only.
8. Build OuterSplitAuthorityV1 from the current split receipt and PrecisionAuthorityV4 from current support + target panel + split.
9. Build nonlinear model-capacity authority V1 with historical evidence limited to model shape. Run the nonlinear row-cap ladder `64 -> 128 -> 256 -> 512 -> 1024` from the authenticated cache with exact replay and stop at the first qualifying cap.
10. Close every remaining final-freeze instance/builder gap without placeholder or historical-role substitution:
    - build the burden-free TargetEvidenceBudgetTemplateAuthorityV1 instance from exact current support/census/block-manifest/observation-state semantic authority;
    - build MaskingBurdenLadderAuthorityV2 from the current census;
    - build MaskingRngReplayAuthorityV2 from the current registry, outer split, target panel, and burden ladder;
    - build NonlinearChallengeAuthorityV3 from current parameters/panel/split plus the control-calibrated nonlinear plan/receipt and selected cap;
    - build MaskingQualificationDesignAuthorityV2 from exact current representation, teacher-target semantics, support, registry, evidence-budget template, burden ladder, precision, split, target panel, RNG, and live qualification-runner source;
    - add/build the final MaskingQualificationRunContractV4 instance from concrete current authority artifacts, the authenticated calibration provenance, final machine checkpoint semantic digest, and exact live source roles. The builder must not accept caller-entered role SHA strings.
    The older AddressUniverseLadderAuthorityV1 is not a final Design V2 role. Discovery universes 800/2,000/6,000 remain historical scale-stress evidence only and may not be manufactured into a FULL104 terminal authority.
11. Freeze the final V4 run-contract instance before inspecting terminal masking-policy outcomes.
12. Rebuild and validate `docs/agent/CURRENT_WORK_CHECKPOINT.json` on the final committed GPU worktree head and independently verify the package.
13. Only then execute terminal FULL104 masking at 5%. Do not inspect 10% if 5% fully qualifies. Continue upward only after explicit failure and stop at the first fully qualifying burden.
14. Masking PASS still does not authorize training. Continue healthy-current-teacher remaining-RNA necessity, measurement robustness, production geometry + geometry-specific memorization, runtime provenance, and final explicit training authority.

## Executability notes

Do not treat bare script names as commands. The builders require explicit runtime paths/receipts. Use `docs/agent/JEPA_NEW_CHAT_COMMANDS_20260918_V5_FULL104_MASKING_CURRENT.md` for the current complete argument templates. The 20260917 command document is superseded.

Both cache-capacity evaluators intentionally return exit code `3` after Run A once they have written replay matrices and a `REPLAY_REQUIRED_*` status. Treat exactly that combination as the expected handoff to Run B; any other nonzero code is a STOP. Run B must write to a different output directory and consume the unchanged Run-A matrices.

The 2026-09-17 preflight is stale/superseded and must not be used:

`scripts/agent/v5_full104_masking_gpu_preflight_20260917.ps1`

Current preflight authority is the tested 2026-09-18 wrapper + Python validator. Its calibration mode validates current FULL104/calibration roots; terminal mode additionally requires current final authorities, machine checkpoint, and live-source binding.

The following direct-stream calibration path is superseded by the authenticated cache route:

`scripts/agent/run_full104_target_panel_capacity_calibration_v1.py`

The following builder is V2 only and must not be used as final nonlinear authority:

`scripts/agent/build_full104_nonlinear_challenge_authority_v2_20260918.py`

## Hard boundaries

- `TRAINING_OFF`
- `NO_D_SHARED_OUTCOME_EXECUTION_OR_INSPECTION`
- `NO_PATHOLOGY_DEV_SEALED_OUTCOME_ACCESS_WHILE_DESIGN_OPEN`
- no smaller/historical/unauthenticated substitute for FULL104
- no historical or smaller-run hash may occupy a current FULL104 role merely because the historical finding remains scientifically informative
- no placeholder, synthetic digest, test-fixture root, stale-version authority, or path-name coincidence may satisfy a production authority role
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
