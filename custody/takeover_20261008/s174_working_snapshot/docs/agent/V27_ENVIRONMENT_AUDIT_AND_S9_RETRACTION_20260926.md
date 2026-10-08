# Environment audit — S9 is retracted in full. The environment was never defective.

**Verdict: this is a false alarm that I raised, and correcting it is the whole
point of this document.** I reported that the `sea-ad-jepa` environment had a
broken NumPy BLAS and advised that earlier results computed there be re-checked.
That advice was wrong and is withdrawn. **No re-execution of any prior result is
required on these grounds.**

## What actually happened

I invoked the interpreter **without `<env>/Library/bin` on `PATH`**. NumPy's
`libblas`/`libcblas`/`liblapack` in that environment are *pure forwarder DLLs*
whose targets resolve at the first call, not at import. So `import numpy`
succeeds and the first BLAS or LAPACK call terminates the process with Win32
status 127 and no message.

That is not a discovery. It is documented, qualified and enforced in this
repository, dated **2026-09-20 — five days before I reported it as new**:

`analysis/v5_full104_pass1_rebuild_20260920/evidence/solver_environment/NUMERICAL_ENVIRONMENT_QUALIFICATION_8c1feae6.json`

```
schema                      V5_NUMERICAL_ENVIRONMENT_QUALIFICATION_V1
status                      QUALIFIED_FOR_PRETERMINAL_MASKING_CALCULATION
qualification_is_conditional True
what_is_qualified           the environment TOGETHER WITH its invocation
                            condition, not the environment alone
succession_performed        False
succession_reason           none required; the environment was never defective
required_invocation_condition
  condition                 <env>/Library/bin must be on PATH when the
                            interpreter runs
  if_violated               import numpy succeeds and the first BLAS or LAPACK
                            call terminates the process with Win32 status 127
```

The `if_violated` clause describes my observation exactly. The condition is
enforced in three places already:
`scripts/agent/prepare_full104_runtime_envelope_v1.py::require_dense_linear_algebra`,
the pass1 rebuild reproduction script, and
`tests/test_v5_dense_ridge_backend_equivalence_v1.py::test_blas_backend_is_reachable_in_a_c…`.

## Physical confirmation, both ways

Same interpreter, same machine, 2026-09-26:

| invocation | numpy | 3x3 matmul | solve | svd | scipy | exit |
|---|---|---|---|---|---|---|
| **without** `Library/bin` on PATH | 1.26.4 imports | — | — | — | — | **127, no output** |
| **with** `Library/bin` on PATH | 1.26.4 | **3.0** | **0.5** | **1.0** | 1.15.3 OK | **0** |

The earlier `0xC06D007F` I saw under pytest is the same failure class the prior
diagnosis recorded (`exit_code_hex 0xC06D007F`, `stderr empty on every probe`,
15/15 probes fatal). The prior work went further than I did and identified the
mechanism: a mixed conda/pip stack in which a pip scipy wheel placed
`libscipy_openblas-…dll` inside `site-packages/numpy.libs/`, giving one process
two LAPACK providers.

## Contamination inventory — empty, and for two independent reasons

**1. No committed receipt names that interpreter as its execution environment.**
A scan of every committed JSON found environment fields recorded in a handful of
files; the ones carrying a NumPy version are the 2026-09-20 solver-environment
evidence itself, plus WSL2/Linux runs (`glibc2.31`) which are a different
environment entirely. Receipts do not generally record the conda environment
name, so attribution from receipts alone is not possible — that is a gap worth
closing, but it is not evidence of contamination.

**2. More fundamentally, this failure mode cannot produce a wrong number.**
Measured per-operation on 2026-09-26, without the PATH condition:

| operation | result |
|---|---|
| elementwise add, `sum`, `mean` | correct |
| 1x1 matmul, 1-D `dot`, `einsum` | correct — these do not dispatch to BLAS |
| 2x2 / 3x3 matmul, `tensordot`, `linalg.svd` | **process dies, exit 127, no output** |
| 3x3 repeated five times | dies every time — deterministic, not intermittent |

So the process either takes a non-BLAS path and is correct, or it terminates and
writes nothing. **A crashed process produces no artifact to be wrong.** The
residual risk is a truncated output file, which is detectable as a missing or
incomplete receipt, never as a plausible-but-wrong value.

| classification | count | which |
|---|---|---|
| verified — no re-execution required | all | no result is impugned by this |
| requires re-execution | **0** | — |
| impossible to reproduce with available inputs | **0** | — |

## Why I got this wrong

I did not classify the observation against the existing audit record before
reporting it. This project's own rule is to read the historical audit index and
classify proposed work as `ALREADY_AUDITED`, `SUPERSEDED`, `OPEN` or
`CHANGED_INPUT_REQUIRES_REQUALIFICATION` **before** acting. Had I searched for a
prior diagnosis of `0xC06D007F` — a distinctive string, present in the
repository — I would have found the answer immediately instead of raising a false
alarm and advising unnecessary re-checking.

Correct classification: **`ALREADY_AUDITED`**. My contribution is limited to an
independent confirmation that the condition still holds six days later, plus the
per-operation fail-fast breakdown above, which the earlier diagnosis did not
record.

## One real consequence worth recording

Because I believed `sea-ad-jepa` was defective, I ran the V5 suite and the
mechanical diagnostic in **`sea-ad-jepa-v3`** (NumPy 2.4.6, torch 2.7.0+cu128).
That environment is healthy, and the mechanical diagnostic is torch-only with no
BLAS dependency — `tensor_fingerprint` converts tensors to bytes and performs no
linear algebra — so **those results stand**.

But it means the run happened in a **non-canonical numerical environment**, on a
different NumPy major version from the qualified one. For a synthetic
torch-only mechanics test that is immaterial; for anything touching the qualified
dense-solver path it would not be. Future runs on that path should use the
qualified environment **with its invocation condition satisfied**, not a
substitute chosen because the qualified one appeared broken.

## Status

```
PHYSICAL_EXECUTED : both-environment probe, per-operation BLAS breakdown,
                    with/without PATH confirmation, committed-receipt env scan
RETRACTED         : S9 "broken numpy BLAS / re-check earlier results"
NOT_EXECUTED      : nothing outstanding on this item
```

```
TRAINING=OFF · AUDIT_B_N1=UNOPENED · PROTECTED_FULL104_OUTCOMES=UNOPENED
D_SHARED_G5=UNOPENED · RARE_TAIL_MOLECULAR=UNOPENED · THERAPEUTIC_RANKING=OFF
```
