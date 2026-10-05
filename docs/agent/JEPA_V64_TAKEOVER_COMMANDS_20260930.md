# JEPA V64 takeover commands — 2026-09-30

## 1. Fetch and inspect current heads

```bash
git fetch --all --prune
git show 23255baaf81381d5c22c655a605642db27f2a173 --stat
git show fc3736d215c3d75eac9d31d181465771c2036503 --stat
```

Then resolve the **current** remote heads for:

- `chatgpt/v64-e2-single-source-successor-20260929`
- `claude/v64-nihcard-realism-design-20260929`
- `claude/v64-nihcard-e2-design-20260929` (historical frozen checkpoint)

Do not assume the recorded SHAs are still the latest if the branches advanced after handoff creation.

## 2. Read in this order

1. `docs/agent/JEPA_NEW_CHAT_HANDOFF_20260930_V64_TARGET_ARCHITECTURE_EXACT_CONTROLS.md`
2. `docs/agent/JEPA_HANDOFF_STATE_20260930_V64.json`
3. `chat_runtime_20260930/CHAT_RUNTIME_EXCLUSIVE_ASSET_CUSTODY_20260930_V2.json`
4. `results/v64/V64_NIH_CARD_STAGE3_PHASE_A_SUCCESSOR_CONTRACT_V2.json`
5. `results/v64/V64_NIH_CARD_STAGE3_FEATURE_ARTIFACT_CONTRACT_V2.json`
6. `results/v64/V64_NIH_CARD_STAGE3_PHASE_A_EXACT_SAMPLER_TEST_CONTRACT_V1.json`
7. `results/v64/V64_NIH_CARD_EXACT_CONTROL_SAMPLER_INDEPENDENT_AUDIT_V1.json`

Then inspect latest Claude exact-sampler implementation and any commits after `fc3736d2`.

## 3. Immediate execution order

1. Finish exact supplement for all candidate starts not proven safe under affine single-block mapping.
2. Run the full frozen exact-sampler qualification.
3. Rerun Phase A.
4. **STOP FOR AUDIT.**
5. Do not open Phase B matrix values until that audit passes.
6. Then perform Part-3 empirical metacell precision and Phase-B promoter/accessibility features.
7. Build the all-resource query-evidence atlas with **coverage and evidence-independence** as separate axes.
8. Only then run the factorized-target architecture tournament.

## 4. Hard stops

- TRAINING OFF.
- TD60 BLOCKED.
- Stage 4 NOT AUTHORIZED.
- Morabito PROTECTED.
- No post-hoc control search lattice or finite proposal budget.
- No CONTROL_B rescue of CONTROL_A.
- No zero-fill of NOT_MEASURED regulatory evidence.
- No use of remembered 15,758 as FULL104 gene denominator until committed authority is found.
- No claim that Nott+NIH-CARD are independent merely because they are separate resources.
