# Existing Graph-JEPA environment selection recommendation v1

Recommendation: clone `sea-ad-jepa` to `sea-ad-jepa-v3`, then install missing v3 optional/baseline packages into the clone.

Rationale: `sea-ad-jepa` imports torch and project runtime code, so it is the safest continuity base.

## Exact install strategy

Do not install into `base/current`. Prefer preserving the existing v2 runtime lineage.

- Install or validate `openTSNE` only after cloning/choosing the target v3 environment.
- Install or validate `phate` only after cloning/choosing the target v3 environment.
- Install or validate `pydiffmap` only after cloning/choosing the target v3 environment.
- Install or validate `scvi` only after cloning/choosing the target v3 environment.
- Install or validate `xgboost` only after cloning/choosing the target v3 environment.
- Install or validate `lightgbm` only after cloning/choosing the target v3 environment.
- Install or validate `dowhy` only after cloning/choosing the target v3 environment.
- Install or validate `econml` only after cloning/choosing the target v3 environment.

If cloning is selected, clone `sea-ad-jepa` first and install only missing v3 optional/baseline packages into the clone. If a fresh environment is selected, recreate the core v2 neural stack before adding optional benchmark packages.

## Boundaries

- No training was run.
- No benchmarks were run.
- No external validation was run.
- No evidence levels or conclusions were modified.
- This audit did not install packages.
- `sea-ad-jepa-v3` was already present at audit time. It should not be treated as the historical v2 runtime; use the `sea-ad-jepa` rows to decide whether cloning preserves continuity.
- Note: `sea-ad-jepa-v3` is included if present, but selection is based on audited compatibility rather than assuming the current/base interpreter represented the project runtime.
