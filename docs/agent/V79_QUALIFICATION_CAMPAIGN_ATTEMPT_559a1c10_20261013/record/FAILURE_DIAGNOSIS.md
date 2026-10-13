# Failure diagnosis (read-only; nothing repaired, nothing retried)

**Observed failure.** The campaign runner was invoked once at 2026-10-13T02:37:12Z and exited 1 at 02:37:16Z. It
reported `REFUSED V2_CORE qualification run: world worker failed for opaque world 2ae1cb055fed with exit 1`.

**Worker's own error.** The world worker (`run_v79_v2_core_qualification_world.py`) raised:
`REFUSED V2_CORE runtime: JAX was imported before frozen runtime configuration`. This came from
`v79_v2_core_runtime.configure_before_jax_import`, called at line 124 of `execute_world`.

**Cause.** The worker imports `v79_v2_core_fit_predictive as P` at module level (line 18). That module imports
`v79_v2_core_fit_model` (its line 15), and loading `v79_v2_core_fit_model` imports JAX and numpyro. So JAX is already
in `sys.modules` before `execute_world` reaches the frozen pre-JAX configuration guard. The guard correctly refuses.

**Evidence.** Each worker dependency was imported alone in a fresh process (bytecode writing disabled, checkout still
clean), and the process then reported whether JAX was loaded:

| module | JAX/numpyro loaded at import |
|---|---|
| `v79_v2_core_fit_contract` | False |
| `v79_v2_core_fit_outputs` | False |
| `v79_v2_core_fit_predictive` | **True** |
| `v79_v2_core_fit_model` | **True** |
| `v79_v2_core_fit_runner` | False |
| `v79_v2_core_fit_surface` | False |
| `v79_v2_core_identified_summary` | False |
| `v79_v2_core_qualification_custody` | False |
| `v79_v2_core_resource_monitor` | False |
| `v79_v2_core_runtime` | False |
| `v79_v2_core_runtime_lock` | False |
| `run_v79_v2_core_qualification` | False |

**Scope of the defect.**
- It is deterministic: the world worker at `559a1c10` cannot reach its first fit in any process. Rerunning the same
  command would fail identically, so it is not an "ordinary interruption" under the resume policy.
- The engineering benchmark did not exercise this path. `run_v79_v2_core_benchmark.py` imports neither
  `fit_predictive` nor `fit_model` at module level.
- The import arrived with the held-out-predictive commits on the PR #300 lineage (`8b252a0a`, `75a9b768`). The
  qualification-runner tests evidently never ran the worker in a fresh process.

**State after the failure.**

| item | state |
|---|---|
| fits run | 0 |
| fit receipts | 0 |
| campaign receipt | none |
| `HEAVY_FIT.lock` | none (the worker refused before taking the lock) |
| result directory | exists, empty |
| custody receipt | `48581e7330020fd8c8e283fe95277bff6c9a585163c93920662d5fa9f6204d66`, unchanged |
| blinded custody digest | `76fe9e42…`, unchanged |
| execution checkout | clean |
| truth | not accessed |
| scoring | none |
| seeds | not modified |
| world bytes | not modified |

**What a repair would need (not applied; for the controller and the repair lane).**
1. Move the `v79_v2_core_fit_predictive` import (and anything else that loads `v79_v2_core_fit_model`) inside
   `execute_world`, after `RT.configure_before_jax_import(...)` and `import jax`, the same way `fit_model` is already
   imported there.
2. Add a fresh-subprocess test that imports the world worker and asserts JAX is not loaded.
3. Add an end-to-end subprocess test that drives `execute_world` through the runtime configuration on a minimal
   custody fixture.

A repaired head would need fresh custody. This custody is bound to `executor_code_head 559a1c10`, and the runner
refuses a different head.
