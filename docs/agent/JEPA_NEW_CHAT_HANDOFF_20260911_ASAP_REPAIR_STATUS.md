# JEPA New Chat Handoff — ASAP Repair Status

Date: 2026-09-11 17:58 America/New_York
Status: CURRENT_POST_ASAP_REPAIR_HANDOFF__NO_TRAINING_AUTHORITY
Branch carrying this handoff: `handoff/jepa-new-chat-20260911-asap-repair-status`
Source repair head used for this handoff branch: `repair/t0-v21-authority-restoration-20260911 @ 93abcf50e89778585bda1e20f2eab824cc6bae77`

## 0. Read this first

This handoff records the state after the V21 authority-truncation incident and its immediate repair/restoration work. It is intentionally conservative. Do not treat any branch name, test count, or prose PASS as scientific authority unless the exact code/evidence path below is verified.

Training remains OFF. No S0-S4 production run, no AT8 opening, no protected partition opening, no `reader_validation`, no oracle, and no V5 training is authorized by this handoff.

## 1. Immediate live-branch refs to re-fetch before doing anything

Before editing or executing, re-fetch these exact branches from GitHub:

- `main`
- `repair/t0-v21-authority-hardening-20260911`
- `repair/t0-v21-authority-restoration-20260911`
- `review/t0-v21-successor-20260911`
- `review/t0-v21-integrated-candidate-20260911`
- `repair/t0-v21-integrated-authority-regression-20260911`
- `repair/v5-qualified-target-guard-20260911`
- `repair/v5-executable-power-authority-20260911`
- `t0/v20-pathology-blind-materialization-20260908`
- `planning/v5-full-population-cheat-proofing-20260909`

Known refs observed during this handoff creation:

- `repair/t0-v21-authority-restoration-20260911 @ 93abcf50e89778585bda1e20f2eab824cc6bae77`
- `repair/t0-v21-integrated-authority-regression-20260911 @ 9a861b41607b16cb40a8240ecda025c9447514ae`
- Claude-reported combined candidate: `review/t0-v21-integrated-candidate-20260911 @ c8a1947ea109e11f20277917410ebc1992ae400f`
- Claude-reported executor successor: `review/t0-v21-successor-20260911 @ 3a8c8e3e5ca84d38eb363e9791e1c86c854a55af`
- Bad/truncated authority hardening head: `repair/t0-v21-authority-hardening-20260911 @ 9f98320f03e19577527b2153159ea0df2c62babd`
- Known good pre-truncation authority head: `a36fd209b40aa9c28cd3d6790bda1fe5054a1923`

## 2. Incident summary — what went wrong

The regression was not caused by Git and not by Claude's merge. It was caused by promoting an incomplete locally reconstructed `scripts/v4/t0_v21_authority_v1.py` onto `repair/t0-v21-authority-hardening-20260911`.

Failure chain:

1. The handoff package available in the ChatGPT environment was incomplete.
2. Dependencies were reconstructed only far enough to run a focused 23-test surface.
3. That focused surface did not exercise the full V21 authority API.
4. The locally tested `t0_v21_authority_v1.py` was promoted byte-for-byte to `9f98320f...`.
5. That local file was truncated relative to the earlier good `a36fd209...` version.
6. The commit deleted the seal/validate functions and `decision_capable_power_gate`.
7. Claude's broader integrated test suite caught the regression: 18 failed / 4 passed in the upstream authority tests.

Principle now recorded by Claude: a documented limitation that the code does not enforce is a comment, not a limitation. The same principle applies to API preservation: a focused test that does not cover the exported authority surface is not a promotion gate.

## 3. V21 authority restoration status

A restoration branch now exists:

`repair/t0-v21-authority-restoration-20260911 @ 93abcf50e89778585bda1e20f2eab824cc6bae77`

Commit metadata observed:

- latest commit message: `ci(v21): include dedicated restoration regressions`
- parent: `b4ae2319f736b4dbeb7debea2400eac171e5a1b7`
- tree: `a2a66999cd8b49a8eb519e2dc72b2cded04b6dad`

Required verification before accepting this branch:

- Confirm `scripts/v4/t0_v21_authority_v1.py` restored the deleted API from `a36fd209...`.
- Confirm it retained the newer hardening from `9f98320f...`:
  - ridge metadata binding against all fold records;
  - enumerated `ALLOWED_EFFECT_ESTIMANDS`;
  - forbidden estimand token handling for HC3 / `t_over_sqrt_n` transport claims.
- Confirm newly added restoration/API regression tests fail on the truncated `9f98320f...` branch and pass on restoration.
- Run full authority + measurement test surface, not just focused tests.

Do not merge or freeze based only on the branch name.

## 4. V21 executor successor status

Claude's executor successor is a real improvement and should be preserved, but it is not a power authority.

Claude-reported executor successor:

`review/t0-v21-successor-20260911 @ 3a8c8e3e5ca84d38eb363e9791e1c86c854a55af`

Core result:

- `EFFECT_TRANSPORT = OPEN`
- `POWER_GATE_PRODUCTION_VERDICT_CAPABILITY = DISABLED`

Important behavior:

- `power_gate` refuses production verdict capability with `STOP_T0_V21_EFFECT_TRANSPORT_NOT_AUTHORITY_BOUND` while module-level effect transport status remains OPEN.
- A caller-supplied receipt cannot re-enable the gate; owner/module status controls enablement.
- Arithmetic formerly used by the power gate survives only as `planning_power_projection`.
- `planning_power_projection` returns no `clears_gate` key, so accidental use as authorization raises rather than silently authorizing.
- The transport receipt schema refuses:
  - `assembled_hc3_t_over_sqrt_n`;
  - whole-pipeline permutation significance as a transport substitute;
  - correction factors read off the measured null spread.
- No correction factor was invented from null-spread measurements 1.304 / 1.477.

Executor evidence reported by Claude:

- executor tests: 124 passed
- mutation audit: 50 mutations, 47 caught, 3 unreachable by construction with proofs, 0 survived
- calibration evidence committed at `docs/agent/evidence/t0_v21_crossfit_null_calibration_20260911.json`
- manifest records invocation, seed, replicate count, output SHA, producing script SHA and git blob

Meaning:

The V21 executor has been made fail-closed around the major scientific blocker. This does not close effect transport. It only prevents an invalid power verdict while transport remains unresolved.

## 5. V21 integrated candidate status

Claude-reported combined candidate:

`review/t0-v21-integrated-candidate-20260911 @ c8a1947ea109e11f20277917410ebc1992ae400f`

Claude reported this combined candidate inherited the authority regression from `9f98320f...` and therefore had:

- executor suite: 124 passed
- upstream authority/measurement surface: 18 failed, 4 passed
- combined: 128 passed, 18 failed, 0 skipped

The failures were reported as identical to `9f98320f...` alone and caused by deleted functions in `scripts/v4/t0_v21_authority_v1.py`.

Therefore `c8a1947e...` is not merge-ready and should be superseded by a combined candidate that integrates:

1. restored authority wrapper from `repair/t0-v21-authority-restoration-20260911`, and
2. effect-transport-disabled executor successor from `review/t0-v21-successor-20260911`.

## 6. Immediate V21 next action

Build or verify a new combined candidate, without altering the source branches:

- base from restored authority branch `repair/t0-v21-authority-restoration-20260911 @ 93abcf50...`
- merge/cherry-pick Claude executor successor `3a8c8e3e...`
- keep effect transport OPEN and production verdict disabled
- run from a clean archive extraction containing only tracked bytes:
  - `tests/v4/test_t0_v21_selection_and_power_v1.py`
  - `tests/v4/test_t0_v21_authority_v1.py`
  - `tests/v4/test_t0_v21_measurement_and_freeze_v1.py`
  - any restoration/API-surface regression tests
  - mutation audit for executor and authority-surface guard if present
- zero skipped tests are required
- explicitly report exported-symbol/API surface preservation against `a36fd209...`

Expected terminal for V21 after that candidate, if clean:

- `V21_AUTHORITY_API_RESTORED = TRUE`
- `EFFECT_TRANSPORT = OPEN`
- `POWER_GATE_PRODUCTION_VERDICT_CAPABILITY = DISABLED`
- `S0_S4_EXECUTION_AUTHORITY = FALSE`
- `TRAINING_AUTHORITY = FALSE`

## 7. Effect transport remains the major scientific blocker

Do not confuse fail-closed behavior with solved transport.

The current architectural rule is:

```text
whole-pipeline permutation -> evidence of association under the discovery procedure
cross-fitted HC3 t         -> descriptive/studentized statistic
effect transported to n=12 -> NOT AUTHORIZED until separately derived/calibrated
```

The 1.304 / 1.477 null spread findings are evidence that the old `t/sqrt(n)` transport is invalid. They are not themselves a replacement correction factor.

A valid future solution must provide an authority-bound effect quantity or mapping from the nested discovery procedure to the prospective confirmation design without looking at protected validation/oracle donors.

Potential future route:

- define an injected-effect calibration on the 28 discovery donors;
- rerun the full nested discovery procedure under controlled known effects;
- estimate a conservative mapping from known injected effect to the frozen discovery statistic;
- red-team that mapping for stability, nuisance dependence, donor imbalance, and shortcut leakage;
- only then consider re-enabling a production power verdict.

Until then, power remains planning-only.

## 8. V5 status and remaining here-work

Completed here previously:

- Same-cell cosine defect found and repaired on V5 guard branch.
- Old `_cosine_rows` behavior treated `(nonzero, zero)` and `(zero, nonzero)` as cosine `1.0`.
- Added adversarial tests for asymmetric zero, zero-zero, near-zero, finite extreme scale, NaN/Inf behavior.
- Repaired behavior distinguishes asymmetric zero from true zero-zero and avoids finite overflow/underflow issues.
- Reproduced focused optimizer guard suite after reconstructing missing handoff dependencies: 12/12 passed.

Executable-power successor status:

- branch: `repair/v5-executable-power-authority-20260911`
- successor files introduced:
  - executable-power V4 receipt;
  - postqualification dependency closure V2;
  - postqualification bundle V3.
- legacy report-only V3 power artifact is structurally insufficient for the successor path.
- focused authority-chain tests previously passed 5/5, including legacy-V3 rejection, raw-output tampering, stale child substitution and mixed-context rejection.

Remaining V5 blocker:

Finish reachability audit: prove whether any active/prospective entrypoint can still call the old chain:

```text
report-only power V3 -> dependency closure V1 -> postqualification V2 -> production_training_eligible=True
```

If reachable, cut the path with a versioned selector/entrypoint repair so only the executable-power successor can produce eligibility. Do not rewrite historical V1/V2 artifacts silently.

## 9. FULL104 / B2 expression closure status

Do not restart this from scratch.

Historical project state shows the substrate and verifier were already heavily closed:

- production authority population: 4,553,407 cells
- donors: 104
- operators/matrices: 42
- molecular addresses: 41,238
- measured-core addresses: 17,186
- complete Phase2 manifest: 8,915 blocks / 42 operators

Known historical distinction:

- FULL104 population/substrate/verifier identity work was largely done.
- The remaining question is whether the one-shot production B2 oracle/verifier was actually executed after definition and whether its receipt was committed/recoverable.

Do not phrase this as “find the dataset.” The corrected task is:

1. Search current/later history for the terminal receipt, expected marker like `PASS_FULL104_4553407_EXPRESSION_BLOCK_AND_IDENTITY_CLOSURE` or equivalent.
2. If found, audit counts, hashes, manifest, row identity, block-local/source coordinates, donor identity and anti-splice provenance.
3. If not found, Claude should run the already-built verifier against the known hard-drive substrate and return the receipt.

## 10. Protected data and execution prohibitions

The following remain prohibited until authority explicitly changes:

- no S0-S4 production run
- no real power gate verdict
- no AT8 opening
- no opening of protected partitions
- no `reader_validation`
- no oracle
- no training
- no production V5 execution
- no deriving/tuning design decisions from fresh validation/oracle donors

Standing rule:

`IF_CONFIRMATION_DATA_COULD_CHANGE_A_DESIGN_CHOICE_DO_NOT_LOOK`

## 11. What the next ChatGPT session should do first

1. Open `START_HERE.md`.
2. Open `docs/agent/JEPA_LATEST_HANDOFF_POINTER.json`.
3. Open this handoff: `docs/agent/JEPA_NEW_CHAT_HANDOFF_20260911_ASAP_REPAIR_STATUS.md`.
4. Re-fetch live heads listed in section 1.
5. Verify `repair/t0-v21-authority-restoration-20260911 @ 93abcf50...` really restores the deleted exported API and includes regression guards.
6. Verify or create the new combined V21 candidate using restored authority + disabled-production executor.
7. Finish the V5 legacy eligibility reachability audit.
8. Recover or request the B2 one-shot production receipt only as a receipt-status task.

## 12. What Claude should do next

Claude should not rerun old work or open protected data.

Recommended Claude tasks:

1. If not already done, produce a clean integrated V21 candidate combining:
   - restored authority branch `93abcf50...`;
   - executor successor `3a8c8e3e...`;
   - effect transport OPEN;
   - production power verdict disabled.
2. Run all combined V21 tests from a clean git archive extraction and report exact counts/zero skipped.
3. Run/refresh mutation audit and API-surface preservation guard.
4. Search hard-drive/repo history for the B2/FULL104 one-shot production receipt.
5. If absent, run the existing B2 verifier and return the receipt.
6. Do not run S0-S4 or protected confirmation/oracle data.

## 13. What is considered done vs not done

Done / likely closed pending final verification:

- V21 executor no longer allows production power verdict while effect transport is open.
- V21 authority deletion has a dedicated restoration branch.
- V21 design stale collinearity prose has reportedly been reconciled in executor successor.
- V21 calibration evidence is committed/recoverable.
- V5 same-cell cosine defect has been repaired.

Not done:

- final integrated V21 clean candidate accepted after restoration + executor merge;
- V21 effect-transport derivation;
- S0-S4 measurement/producer layer and executable review;
- V5 legacy eligibility reachability closure;
- final B2/FULL104 one-shot receipt recovery/audit if not already present;
- any training authority.

## 14. Current bottom line

The project is no longer blocked by mystery data access or generic framework design. The live blockers are specific:

1. repair/verify V21 authority API restoration in the integrated candidate;
2. keep V21 power fail-closed until effect transport is solved;
3. finish V5 legacy eligibility reachability closure;
4. recover/audit B2 production receipt status;
5. only later proceed to S0-S4 executable review and discovery-only execution.

Until those are closed:

`NO_PRODUCTION_TRAINING_AUTHORITY`
