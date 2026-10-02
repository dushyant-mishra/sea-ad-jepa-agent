# V72 takeover commands and operating instructions — 2026-10-02

## First reads

1. `docs/agent/JEPA_NEW_CHAT_HANDOFF_20261002_V72_SYNTHETIC_TWIN_STAGE4_SCENICPLUS.md`
2. `docs/agent/JEPA_NEW_CHAT_STATE_20261002_V72.json`
3. `docs/agent/archive/chat_runtime_20261001/CHAT_RUNTIME_CUSTODY_INDEX_20261001.md`

Read raw chat uploads only when chronology or exact historical wording matters.

## First GitHub checks

Re-query:

- `chatgpt/v64-privileged-information-recoverability-20260930`
- `claude/v64-exact-sampler-successor-20260930`
- `claude/v69-scenicplus-external-network-20261001`
- `handoff/jepa-20261001-chat-exclusive-custody`

Then enumerate commits newer than:

- Stage4 audited head: `759bf0f276307ad296e9a8669f39adccc1a7f83a`
- SCENIC+ audited head: `f8dc493516db079fd529e4a69f370d8b9db0dfad`

## Audit Macha before integration

For each new Macha commit:

1. inspect diff and changed paths;
2. open code + receipt + precommit + tests;
3. verify chronology;
4. verify claims against artifact bytes;
5. identify checks that cannot fail or cannot pass;
6. independently recompute a small subset if practical;
7. classify the result as VERIFIED / VERIFIED_WITH_LIMIT / SUPPORTING_ONLY / SUPERSEDED / RETRACTED / UNRESOLVED;
8. do not merge execution branches into Sol merely to simplify history.

## Sol implementation work to resume immediately

Start from:

`chatgpt/v64-privileged-information-recoverability-20260930 @ 4fd4305395c4da0c025f336006be7c9dbbe6dd70`

### First coding task

Close the V71 CI gap:

- add a test for `scripts/v64/validate_v71_synthetic_pipeline_readiness.py`;
- add V71 path triggers to `.github/workflows/v64-privileged-architecture-smoke.yml`;
- run `tests/test_v71_small_synthetic_etl_fixture.py`;
- run the new readiness-validator test;
- run the readiness validator itself;
- verify exact-head GitHub Actions;
- preserve any failures instead of rewriting history.

### Second coding task

Add post-V71 lessons into the synthetic twin:

- S99 faithful matched-control construction;
- overlapping Stage-4 windows/all-overlap logic;
- barcode→donor authority and suffix-collision failure;
- SCENIC+ ranking seed/thread pinning/sharding/merge invariants;
- raw Route-B fragments→pseudobulk→MACS→consensus path;
- S102 G2 semantics represented as unresolved, not silently frozen.

## Stage4 rule

Do not authorize real Stage 4.

Do not choose a G2 threshold from V2 or the pending K curve.

If a new G2 specification is proposed, require a prospective rationale independent of observed V2 outcomes.

## SCENIC+ rule

Do not call the network qualified until actual Route-A/Route-B eRegulon results, controls, donor stability and program-level crosswalks exist and are audited.

Before freezing Route-B region universe, explicitly resolve the blacklist amendment.

## Synthetic-twin rule

The full synthetic benchmark must reproduce:

- distributions;
- observation operators;
- structural missingness;
- raw formats;
- selection;
- matching;
- pairing;
- QC;
- control construction;
- route-specific ETL;
- failure modes;
- checkpoint pathologies.

One shared hidden truth must generate all synthetic modalities.

## Never silently repeat these superseded claims

- V1 technical FP 0.875/1.000 as Stage4 design calibration;
- Stage4 interval coverage 41.4%;
- “G2 definitely discards one-third of biology”;
- “C: SSD is faster for cisTarget”;
- “V71 passed CI”;
- “SCENIC+ eRegulon network is built/qualified”;
- “barcode suffix identifies donor”;
- “Stage75F is validated prior art.”

## Desired takeover outcome

The new chat should be able to say, with exact GitHub evidence:

- what Macha has pushed since the previous audit;
- what is verified vs still pending;
- what Sol changed in response;
- which tests/CI actually ran;
- what remains sealed;
- what the next executable synthetic-twin milestone is.
