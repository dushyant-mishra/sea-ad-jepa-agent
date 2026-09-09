# Claude next actions — T0 real B2 authority

Base commit: `0f0076235b96691a04f56bc213f0280c68200e0c`

External-review branch containing this work order: `review/t0-r5-dataset-first-framework-20260909`

## Instruction

Stop treating synthetic fixtures as progress. Use them only for red tests and regressions. The next real progress is materializing and replaying the production B2 raw-source population authority over the actual frozen 20,804 accepted rows.

## Do not change these gates

```
DONOR_ROLE_GATE_SHUT
NUMERIC_CONFIRMATION_AT8_NOT_ACCESSED
real_execution_ready=False
NO_ELIGIBLE_DONOR_CONSTRUCTION
```

Only `PRODUCTION_B2_NOT_RUN` can change, and only after the real production artifact exists and independently replays.

## First commit the production harness

Do not run from a temp Claude scratchpad. Commit the production runner and replay verifier first.

Required committed files:

1. `scripts/v4/run_t0_b2_raw_source_population_authority_v1.py`
2. `scripts/v4/verify_t0_b2_raw_source_population_authority_v1.py`
3. `docs/agent/T0_REAL_B2_AUTHORITY_RUNBOOK_20260909.md`

The runner must accept explicit paths and expected hashes; no implicit temp paths, no scratchpad-only state.

Required runner inputs:

- source H5AD path;
- logical row authority path or JSON;
- expected logical row authority root;
- expected source SHA;
- expected source byte count;
- expected row count `20804`;
- output directory.

Required runner outputs:

- raw-source population authority artifact;
- run manifest;
- SHA-256 for every emitted file;
- population raw-source root;
- final counts: rows attempted, rows proven, skipped, duplicate logical indices, mismatches;
- explicit `pathology_values_read=false`.

## Then execute the real run

Required success conditions:

- exactly `20,804` rows attempted;
- exactly `20,804` rows proven;
- zero skipped rows;
- zero duplicate logical indices;
- zero donor mismatches;
- zero cell mismatches;
- zero expression-row mismatches;
- zero source-library mismatches;
- final root recorded;
- source SHA equals `e06000cb8fc83ebad88a52a0a7c772747c38fa92c97debcfe4f59de7cea60c79`;
- source byte count equals `32,978,570,763`;
- no pathology fields read or emitted.

## Replay before claiming closure

Run the verifier against only the emitted disk artifacts and externally supplied expected roots.

Required replay checks:

- stored population root == recomputed population root == expected root;
- stored package root == recomputed package root;
- every proof row matches the logical row authority;
- proof row count == 20,804;
- source digest and byte count match expected;
- emitted artifacts contain no pathology fields;
- `real_execution_ready=false` remains recorded.

## After raw-source authority

Only after the real raw-source population authority replays, run production technical completeness.

Technical completeness must consume:

- authenticated B2 closure;
- verified physical read plan;
- B1 35,076-position projection;
- real counts payload bytes;
- real raw-source population authority.

Do not construct eligible donors yet. Eligible donors are blocked until technical completeness has its own immutable production package and replay report.

## Final report required

Report exact artifact paths, byte sizes, SHA-256 hashes, package roots, population root, and replay verdict. Do not use only console logs as evidence.
