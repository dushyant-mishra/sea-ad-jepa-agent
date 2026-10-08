# Correction: the numerical environment was never broken

Date: 2026-09-20
Supersedes the `diagnosis` block of
`evidence/solver_environment/SOLVER_ENVIRONMENT_DIAGNOSIS_OLD.json`.

**The earlier receipt is kept byte-identical and is not rewritten.** What it
*observed* was real and reproducible. What it *concluded* was wrong, in two
specific and checkable ways. This document states the correct finding, shows the
evidence, and records the consequence — which is larger than the original claim,
not smaller.

---

## 1. What the old diagnosis asserted

| field | asserted | true? |
|---|---|---|
| `status` | `BROKEN__ALL_DENSE_LAPACK_PATHS_TERMINATE_THE_INTERPRETER` | **No** |
| `finding` | mixed conda/pip stack with two incompatible BLAS/LAPACK providers | **Not the cause** |
| `smoking_gun` | `libscipy_openblas-….dll` "is installed inside `site-packages/numpy.libs/`" | **False as stated** |
| `repair_rule` | replace the pip scipy with a conda-forge scipy | **Would have repaired a non-defect** |

The `smoking_gun` claim is the worst of the four, because it was a fabricated
detail rather than an over-reading. There is **no `numpy.libs/` directory** in
this environment. The OpenBLAS DLL lives in `site-packages/scipy.libs/`, which is
simply where a scipy pip wheel puts its own bundled library. Nothing had been
"placed in numpy's DLL directory". That sentence should never have been written.

## 2. What is actually true

The environment `sea-ad-jepa` is **fully functional**. Run with its native DLL
directory reachable, all fifteen probe combinations complete:

```
  method             n     ok     exit   residual
  numpy_solve        4/32/64      0      1.249e-16 / 2.307e-16 / 4.487e-16
  numpy_cholesky     4/32/64      0      1.249e-16 / 2.469e-16 / 4.100e-16
  numpy_lstsq        4/32/64      0      7.410e-16 / 1.251e-15 / 1.598e-15
  scipy_solve_pos    4/32/64      0      8.324e-17 / 2.326e-16 / 2.409e-16
  scipy_cho          4/32/64      0      8.324e-17 / 2.326e-16 / 2.409e-16
  methods that killed the process: none
```

## 3. The real mechanism

`0xC06D007F` is the Visual C++ delay-load/forwarder helper exception carrying
Win32 status **127 = `ERROR_PROC_NOT_FOUND`** — a module that *loaded* but did
not supply a required export. It is **not** `126 = ERROR_MOD_NOT_FOUND`. The old
diagnosis read it as a missing-DLL signature; it is a missing-**export**
signature. (Shells report it truncated to its low byte, as exit `127`.)

Read directly from the PE headers:

| DLL | exports | all forwarded to |
|---|---|---|
| `Library\bin\liblapack.dll` | 1,949 | `mkl_rt.3.dll` |
| `Library\bin\libblas.dll` | 151 | `mkl_rt.3.dll` |
| `Library\bin\libcblas.dll` | 174 | `mkl_rt.3.dll` |
| `Library\bin\mkl_rt.3.dll` | 49,684 direct exports, `dgesv_`/`dpotrf_`/`dgelsd_` all present | — |

So numpy's BLAS/LAPACK is reached entirely through **forwarder** DLLs. Forwarder
targets are resolved by the loader at **first call**, using the loader's own
search order — which does **not** consult directories registered through
`os.add_dll_directory`. Therefore:

* `import numpy` succeeds (its static imports of `libblas`/`libcblas`/`liblapack`
  resolve normally);
* the **first** BLAS or LAPACK call tries to bind `liblapack.dll!dgesv_ →
  mkl_rt.3.dll.dgesv_`, cannot find `mkl_rt.3.dll`, and the process is killed
  outright — no Python exception, no traceback, empty stderr.

Confirmed by controlled comparison on the same interpreter:

| condition | `np.dot` | `np.linalg.solve` | `scipy.linalg.solve` |
|---|---|---|---|
| `Library\bin` **not** on `PATH` | killed, 0xC06D007F | killed, 0xC06D007F | **works** |
| `Library\bin` on `PATH` | works | works | works |

`scipy.linalg` survives either way because the pip wheel carries its own
OpenBLAS and never needs `mkl_rt`. The coexistence of two BLAS providers is
genuine — and worth recording — but it is **not** what caused the failure. It is
in fact what made the failure look selective.

All conda-declared files are present on disk: `mkl` 27/27, `libblas` 2/2,
`liblapack` 2/2, `numpy` 1425/1425, zero missing.

## 4. Classification

```
INVOCATION_DEFECT__DLL_DIRECTORY_NOT_ON_PATH
```

The interpreter was launched by absolute path (`…\envs\sea-ad-jepa\python.exe`),
so conda activation never ran and `…\envs\sea-ad-jepa\Library\bin` was absent
from `PATH`.

**No environment succession is required.** `sea-ad-jepa-linalgfix-20260920` was
begun, never completed (7.8 GB copied, no `python.exe`, empty `conda-meta`,
unregistered with conda), and has been removed. Building it would have
"repaired" a defect that does not exist, and would have introduced an
unnecessary variable into the execution provenance.

## 5. Why this matters more than the original claim

The reproduction script, the runtime envelope, and the physical shakedown all
launch Python by absolute path. Every FULL104 estimator ends in a dense ridge
solve:

| module | line | call |
|---|---|---|
| `full104_masking_streaming_executor_v1.py` | 530 | `np.linalg.solve(regularized, rhs / scale)` |
| `full104_masking_qualification_runner_v1.py` | 278 | `np.linalg.solve(gram, features.T @ y)` |
| `full104_control_calibration_cache_evaluator_v1.py` | 248 | `np.linalg.solve(…)` |
| `masking_control_executor_v1.py` | 286 | `np.linalg.solve(…)` |
| `shortcut_predictability_v2.py` | 202, 263 | `np.linalg.solve(…)` |

A terminal masking run launched the way every previous run was launched would
have **died partway through with no traceback and no error message**. The pass1
build, the physical shakedown and the census all completed only because they use
sparse and elementwise numpy and never touch MKL — `np.dot` itself is killed
under this condition, not merely dense solves.

So the correct finding is not "one environment is broken" but "**every FULL104
entry point could silently lose a multi-hour run, and the failure would have
been unattributable.**"

## 6. Repairs actually made

1. `scripts/agent/prepare_full104_runtime_envelope_v1.py` — `require_dense_linear_algebra()`
   runs a child-process BLAS + LAPACK probe as a hard precondition of preparing
   or validating any runtime envelope, and refuses with an explanatory message.
2. `analysis/…/scripts/reproduce_full104_pass1_rebuild_20260920.ps1` — prepends
   the interpreter's `Library\bin` to `PATH` and verifies dense linear algebra
   before any stage runs.
3. `analysis/…/scripts/solver_backend_preflight_20260920.py` — records
   `library_bin_on_path`, decodes the Win32 status behind a fatal exit, and emits
   an explicit `classification`, so the determinant is never again separated from
   the result. Schema bumped to `…PREFLIGHT_V2`.
4. `tests/test_v5_dense_ridge_backend_equivalence_v1.py` — new; see below.

**No estimator was changed.** No production solver call was rewritten. The
mathematics is identical; only the conditions under which it is allowed to start
have been made explicit.

## 7. Standing lesson

An exit status is a *class* of failure, not a cause. The old diagnosis named a
specific mechanism, and even a specific file path, on the strength of a status
code plus a plausible story about package provenance — and the specific file
path was not checked. The preflight now records the determinant next to the
result so the inference step cannot be skipped again.
