# V5 governance refresh — 2026-09-13

Status: `CURRENT_EXECUTION_POINTER_REFRESHED__HISTORICAL_POINTER_PRESERVED`

This refresh exists because the earlier Sept-13 entrypoint and blocker ledger predated the completed FULL104 hardened replay, sealed dimension-input artifact, prospective precision freeze, and FULL104↔precision pre-outcome cross-binding.

## Current execution pointer

Use:

`docs/agent/JEPA_LATEST_HANDOFF_POINTER_20260913_CURRENT.json`

for current execution state.

The older:

`docs/agent/JEPA_LATEST_HANDOFF_POINTER_20260913.json`

is preserved unchanged as historical provenance and must not be treated as the current execution pointer.

## Current blocker ledger

Use:

`docs/agent/V5_CURRENT_AUTHORITY_AND_BLOCKERS_20260913.md`

The older:

`docs/agent/V5_DIMENSION_NUMERIC_AUTHORITY_BLOCKERS_20260912.md`

remains historically useful but its statements that FULL104 rebinding and prospective precision authority are open are superseded by current evidence.

## External cohort governance

Use:

`docs/agent/V5_EXTERNAL_COHORT_ROLE_REGISTRY_20260913.json`

This freezes cohort roles before outcome access while leaving exact asset locators/hashes fail-closed and pending.

## Hard boundary

This documentation refresh creates no numeric-dimension authority and no training authority.
