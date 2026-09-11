# JEPA new chat handoff — post-Claude review repairs current

Date: 2026-09-11
Repository: `dushyant-mishra/sea-ad-jepa-agent`
Status: `POST_CLAUDE_REVIEW_REPAIR_HANDOFF__NO_TRAINING_AUTHORITY`

## Non-negotiable startup order

1. Open `START_HERE.md` first.
2. Open `docs/agent/JEPA_LATEST_HANDOFF_POINTER.json`.
3. Open this file: `docs/agent/JEPA_NEW_CHAT_HANDOFF_20260911_POST_CLAUDE_REPAIR_CURRENT.md`.
4. Re-fetch live heads before doing any work. Do not trust branch heads recorded below without checking GitHub again.
5. Keep training OFF. No S0-S4 execution, no AT8 opening, no protected reader_validation/oracle opening, no production V5 training.

## Live heads from Claude review input

Claude reviewed the then-current heads:

| Branch | Reviewed head | Verdict |
|---|---:|---|
| `repair/t0-v21-authority-hardening-20260911` | `a36fd209b40aa9c28cd3d6790bda1fe5054a1923` | `PASS_WITH_MINOR_NOTES` |
| `repair/v5-qualified-target-guard-20260911` | `7a2bdfb051e0173c2a6d6bfa50cf57fd110278e0` | `MAJOR_REVISION` |
| `review/integrated-target-v5-repairs-20260911` | `f493e531402e8a1148e9abb7011641a7bbbdcda3` | `PASS` |

Claude also confirmed `3b5933f6` immutable, and disclosure said invariants 5-6 were tested only on a toy `nn.Linear` with an injected stub update function. The real `production_update` was not invoked. No production modules, checkpoints, EMA, S0-S4, power gate, AT8, reader_validation/oracle, or partitions were touched.

## What was fixed after Claude's review

### B2 / V5 optimizer-guard blocker

Branch updated: `repair/v5-qualified-target-guard-20260911`

New head after this chat's GitHub push: `a3427815b803382c939cd9741ab7332513ad4a9d`

Sequential commits pushed:

1. `a6b052c84b39db6e85f2bded23fcc8713af225a9` — `fix(v5): make optimizer guard resident and cursor-bound`
2. `4846f7f88247245eee8bdc0a8559785eac664e61` — `fix(v5): keep qualified guard active after update entrypoint`
3. `a3427815b803382c939cd9741ab7332513ad4a9d` — `test(v5): cover resident guard stale authorization and target binding`

Files changed on that branch:

- `src/sea_ad_jepa/v5/qualified_optimizer_guard_v1.py`
- `src/sea_ad_jepa/v5/qualified_teacher_student_runtime_v1.py`
- `tests/test_v5_qualified_target_optimizer_guard_v1.py`

Behavior now intended/covered locally:

- guard is resident on the optimizer rather than closed at the end of the entrypoint;
- direct post-entrypoint `optimizer.step()` remains denied by default;
- step authorization is cursor-bound at `optimizer.step` time using private kwarg `v5_guard_schedule_cursor`;
- stale authorization after a simulated AMP skip is burned/refused before mutation;
- AMP scaler path and direct step path both hit the same optimizer hook;
- `qualified_production_update` binds the observed target root actually installed on `modules` to the receipt target root before mutation;
- receipt remains 46-donor V21 target-bound;
- `production_training_authorized` remains false.

Local verification run before pushing:

```bash
cd /mnt/data/v5_patch
PYTHONPATH=src pytest -q tests/test_v5_qualified_target_optimizer_guard_v1.py
# 12 passed in 1.96s
```

Important caveat: this is still a toy/stub unit-level verification. It proves the guard mechanics on `torch.optim.SGD` and disabled CPU GradScaler path in this environment. It is not yet a full real V5 production-runtime proof.

### B1 / T0 V21 wrapper notes

Local patch directory in this chat: `/mnt/data/v21_patch`

Local verification:

```bash
cd /mnt/data/v21_patch
PYTHONPATH=scripts/v4 pytest -q scripts/v4/test_t0_v21_authority_v1.py scripts/v4/test_t0_v21_measurement_and_freeze_v1.py
# 23 passed in 0.15s
```

Local files containing the verified patch:

- `/mnt/data/v21_patch/scripts/v4/t0_v21_authority_v1.py`
- `/mnt/data/v21_patch/scripts/v4/test_t0_v21_authority_v1.py`
- `/mnt/data/v21_patch/scripts/v4/test_t0_v21_measurement_and_freeze_v1.py`

Patch substance:

1. `_validate_legacy_crossfit_structure` now derives ridge-exponent metadata from the 28 folds and requires declared cross-fit fields to agree:
   - `fold_ridge_exponents` must exist and have exactly 28 entries;
   - each declared exponent must match the corresponding per-fold `fold_ridge_exponent`;
   - `fold_ridge_exponents_recorded` must equal whether all fold exponents are present;
   - `fold_ridge_exponents_vary` must equal whether recorded fold exponents actually vary.
2. Power-calibration receipt `effect_estimand` is now enumerated:
   - allowed: `whole_pipeline_permutation_standardized_effect_v1`;
   - allowed: `prospective_conservative_geometry_envelope_effect_v1`;
   - forbidden token families include `hc3`, `t_over_sqrt_n`, `t/sqrt(n)`, `assembled_hc3`.
3. The HC3-SE-standardized quantity is explicitly excluded until a transport derivation exists.

Important caveat: this V21 patch was verified locally in this chat, but only V5 and handoff docs were pushed through the GitHub connector in this update. New chat should either reapply the local patch exactly from the handoff package or re-implement the two small source edits above, then push `repair/t0-v21-authority-hardening-20260911` and re-run the 23 focused tests.

## Claude issues now mapped

### Closed or locally closed

- B2 resident optimizer guard: pushed on V5 branch.
- B2 stale authorization after AMP skip: pushed on V5 branch.
- B2 target tensor/root binding gap: pushed on V5 branch as observed installed target root binding.
- B1 ridge metadata consistency: locally verified in `/mnt/data/v21_patch`, still needs GitHub source-branch push if not already applied by a later chat.
- B1 free-text/HC3 effect estimand: locally verified in `/mnt/data/v21_patch`, still needs GitHub source-branch push if not already applied by a later chat.

### Still open by design

- Confirmation-design roles are still single-actor/self-asserted unless external authority files are added for `discovery_only_design_envelope` and `pre_unblinding_demographics_authority`.
- Geometry transport and null/permutation evidence receipts remain assertions unless external producers recompute and bind them.
- QID paired-wrong vs matched-null authority gap remains unresolved. Historical producer at `dd078625c3537f5ff2c3f8c0b382ba2803b24ee2` passes matched-null-vs-true-teacher similarity as `paired_wrong_similarity`, but no frozen authority proves matched-null state intervention is equivalent to paired-wrong-query intervention.
- `src/sea_ad_jepa/v5/dimension_execution_firewall_v1.py` consuming `receipt.get("matched_null_preserves")` is related lineage-risk context, not itself a QID reference.
- FULL104 expression block store remains unresolved: `STOP_FULL104_PHASE2_BLOCK_STORE_LOCATION_BINDING_MISSING`.
- `/mnt/data/66e64913-959f-4a7c-bbfe-6ff906fb281d.npz` remains `PROVENANCE_MISMATCH_DO_NOT_USE`.

## Required next actions for the new chat

1. Re-fetch live heads for all branches, especially:
   - `repair/v5-qualified-target-guard-20260911`
   - `repair/t0-v21-authority-hardening-20260911`
   - `review/integrated-target-v5-repairs-20260911`
   - `main`
2. Verify V5 branch head is at or ahead of `a3427815b803382c939cd9741ab7332513ad4a9d`.
3. Re-run V5 focused tests on the live branch:
   ```bash
   PYTHONPATH=src pytest -q tests/test_v5_qualified_target_optimizer_guard_v1.py
   ```
4. Apply/push the V21 local patch if the live branch does not already contain:
   - `ALLOWED_EFFECT_ESTIMANDS` / `FORBIDDEN_EFFECT_ESTIMAND_TOKENS`;
   - ridge metadata cross-check in `_validate_legacy_crossfit_structure`;
   - tests rejecting forged ridge metadata and HC3/t-over-sqrt-n estimand.
5. Re-run V21 focused tests:
   ```bash
   PYTHONPATH=scripts/v4 pytest -q scripts/v4/test_t0_v21_authority_v1.py scripts/v4/test_t0_v21_measurement_and_freeze_v1.py
   ```
6. Ask Claude/external reviewer to re-review exact heads after V21 push and V5 push. The re-review should include reproductions for:
   - unguarded post-entrypoint step;
   - stale AMP-skip authorization;
   - target-root mismatch;
   - forged ridge metadata;
   - HC3/free-text effect-estimand acceptance.
7. Do not merge/delete branches until the exact post-repair heads receive independent PASS and governance index/supersession map are updated.

## Heavy/runtime assets visible in this chat

The following files exist in `/mnt/data` in this chat environment. They are not duplicated into repo docs or lightweight handoff commits.

- `/mnt/data/FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.part001`
- `/mnt/data/FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.part002`
- `/mnt/data/FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.parts.sha256.csv`
- `/mnt/data/FOUNDATION_CALIBRATION_BUNDLE_20260824.zip`
- `/mnt/data/checkpoints.zip`
- `/mnt/data/expression.zip`
- `/mnt/data/t1_checkpoint_u0200.zip`
- `/mnt/data/66e64913-959f-4a7c-bbfe-6ff906fb281d.npz` — do not use unless provenance is resolved.
- `/mnt/data/WSL execution issue.txt`
- `/mnt/data/Pasted markdown.md`
- `/mnt/data/Pasted text.txt`

## Current status summary

The project is closer after the V5 guard repair, but there is still no production training authority. V5 guard bypass blockers have been patched and pushed; V21 note fixes are locally verified and recorded for exact reapplication/push; integrated review branch has been given this handoff so a new chat can continue without restarting history.
