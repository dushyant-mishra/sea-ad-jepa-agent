# Existing Graph-JEPA environment selection recommendation v1

Recommendation: use `sea-ad-jepa-v3` for v3 evaluation/runtime.

Rationale: `sea-ad-jepa-v3` now imports the cloned v2 neural stack, torch/PyG with CUDA, project runtime modules, and the requested optional v3 baseline/causal packages.

## Exact install strategy

Do not install into `base/current`. Prefer preserving the existing v2 runtime lineage.

- No missing requested packages were detected in `sea-ad-jepa-v3`.

If cloning is selected, clone `sea-ad-jepa` first and install only missing v3 optional/baseline packages into the clone. If `sea-ad-jepa-v3` is complete, use it directly for no-training v3 evaluation/runtime checks.

## Boundaries

- No training was run.
- No benchmarks were run.
- No external validation was run.
- No evidence levels or conclusions were modified.
- The audit script did not install packages.
- `sea-ad-jepa-v3` is present and currently passes the requested v3 runtime import checks. It should be treated as the selected v3 runtime, not as the historical v2 runtime.
- Note: `sea-ad-jepa-v3` is included if present, but selection is based on audited compatibility rather than assuming the current/base interpreter represented the project runtime.
