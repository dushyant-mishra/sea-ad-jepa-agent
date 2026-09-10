# T0 V20 replay equivalence: the run, and why it stopped

Terminal: **`STOP_T0_V20_REPLAY_NOT_EQUIVALENT_UNDER_FROZEN_POLICY`**

The reporting-only sensitivity recovery was run through the separately versioned
replay-equivalence path against the exact frozen Stage-3 inputs. Twelve of the
thirteen compared target-fit fields pass their frozen budgets. One stops. The
sensitivity statistics were therefore **not recovered**, and no budget was
revisited after the discrepancy was seen.

## What was preserved

- `verify_target_v2_against_raw` is untouched and still bit-exact.
- Zero frozen V20 files modified.
- No V21, no changed T0 conclusion, no training authority, no gate opened.
- Reconstructing the original numeric stack remains open in parallel; it did not
  block this run.

## The complete field report

Exact canonical input provenance matched (`provenance_exact: true`), so this is
a comparison of arithmetic on identical inputs.

| field | rule | verdict | observed |
| --- | --- | --- | --- |
| `beta` | tolerant array | PASS | max_rel 2.807e-12, max_abs 5.929e-21, 22286/28061 differ |
| `sigma` | tolerant array | PASS | max_rel 8.221e-16, max_abs 2.220e-16, 10447/28061 |
| `cv_mse_by_multiplier` | tolerant array | PASS | max_rel 2.585e-15, all 17 differ |
| `mu` | exact array | PASS | identical |
| `decision_gene_mask` | exact array | PASS | identical |
| `multiplier_exponents` | exact array | PASS | identical |
| `canonical_donor_order` | exact array | PASS | identical |
| `selected_multiplier_index` | exact scalar | PASS | 16 = 16 |
| `selected_multiplier_exponent` | exact scalar | PASS | 2.0 = 2.0 |
| `discovery_age_center` | exact scalar | PASS | 0 ULP |
| `final_lambda` | ≤1 ULP | PASS | 1 ULP |
| `response_residual_sd` | ≤1 ULP | PASS | 1 ULP |
| **`final_trace_scale`** | **exact scalar** | **STOP** | **1 ULP: 23607.64285714286 vs 23607.642857142862** |

Record: `outputs/t0_sensitivity_recovery_v2_20260910/T0_V20_REPLAY_EQUIVALENCE_REPORT.json`,
which also carries the numeric environment and the reporting-repair verification.

## Why this particular field stopping is worth a second look

Stated as a fact about the frozen code rather than as an argument for a looser
budget. In `t0_target_learner_v1.py:68-71`:

```python
s = float(np.trace(gram)/n)                     # final_trace_scale
lam = float((10.0**float(multiplier_exp))*s)    # final_lambda
```

`final_lambda` **is** `final_trace_scale` multiplied by an exact power of ten —
here 10² = 100.0, which is exactly representable. The two therefore drift
together: any last-bit movement in `s` reappears in `lam`. And `s` is the trace
of a Gram matrix divided by n, a BLAS-dependent reduction, which is exactly the
kind of accumulation an OpenBLAS thread count reorders.

The frozen policy permits 1 ULP on `lam` and requires 0 on `s`. As a pair those
cannot both be satisfied by any stack that drifts at all: the derived quantity is
allowed to move while the quantity it is derived from is not. Both observations
came in at 1 ULP, which is what that relationship predicts.

**The omission is mine, not the review's.** The budget table I published in
`T0_V20_REPRODUCIBILITY_FINDINGS.md` listed `final_lambda` and
`response_residual_sd` as one-ULP and listed the identical fields, but never
mentioned `final_trace_scale`, even though the diagnostic that produced those
numbers had measured it drifting. A policy frozen from that table had no
documented drift for the field and classified it as exact, reasonably.

## What is not being done here

The budget is not being changed. The authorization was explicit — a failed test
is a STOP, not an invitation to inspect the discrepancy and widen the
tolerance — and the fact that this looks like a clerical mis-assignment does not
make it mine to re-freeze. Measuring the discrepancy and reporting it is one
act; choosing the budget that would admit it is a different one.

The report records `tolerances_revisited_after_seeing_the_discrepancy: false`.

## The decision

Re-freezing the policy for `final_trace_scale` is the owner's call. The two
internally consistent options:

1. Move `final_trace_scale` into the ULP policy at `max_ulp: 1`, matching
   `final_lambda`, on the pre-existing evidence that it drifts by one ULP and
   the structural fact that `final_lambda` is derived from it.
2. Require 0 ULP on both, which makes the target-fit comparison bit-exact for
   the ridge scale and means no drifting stack can ever replay — i.e. the
   original blocker, deliberately retained until the original stack is
   reconstructed.

Either is defensible. Option 1 is a correction to a documentation gap that
predates the authorization; option 2 keeps the strict standard and waits for the
stack. What is not defensible is choosing between them on the basis that one of
them lets this run through.

Once re-frozen, the recovery re-runs unchanged — the routing, the dtype guard
and the reporting repair are all in place and tested, and the run reaches the
STOP in about thirty seconds.

## Hardenings applied before the run

- **dtype guard** across all four comparison classes, with float64 required for
  the budgeted and ULP fields. Nine adversarial tests, including a float32
  recomputation whose values fall inside the beta budget.
- **`null_t` crash fix.** It is an exact field, but the committed record holds a
  string and a live replay holds an ndarray, so `!=` evaluated elementwise and
  raised `ValueError: truth value of an array is ambiguous`. Both sides are now
  compared in the record's own form. The committed value is NumPy's *truncated*
  repr — five of 9,999 statistics — so that check covers the representation, not
  values the artifact never held; the null's effect stays pinned by `p_upper`,
  `p_lower` and `permutations`.
- **Routing completed.** The candidate bound the verifier only in the
  adjudicator namespace, covering step 9. The first call is at step 4, resolved
  through `t0_tail_authority_v1`'s own globals, and it still reached the
  bit-exact verifier — which is where the previous attempt died. The chain is
  now derived verbatim into namespaces where only the verifier name differs.
  Expected replay count 1 → 2, counted from the frozen call sites.
- **Numeric environment recorded**: Python 3.11.15, NumPy 2.4.6, SciPy 1.15.3,
  OpenBLAS 0.3.31.188.0 (pthreads, 16 threads), SIMD X86_V3. Thread count is
  included because it sets reduction order.
- **Suite made portable.** It imported the lane modules by bare name with no
  conftest, so it passed only under an ambient `PYTHONPATH` and reported
  collection errors from a clean clone. 19 → 32 passing, self-resolving.
