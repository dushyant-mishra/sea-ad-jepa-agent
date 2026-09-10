# T0 V20: the recovered sensitivity statistics

Terminal: **PASS** under the frozen V2 replay-equivalence policy. Every gate
cleared, the sensitivity surfaces the committed decision omitted are recovered,
and the T0 V20 conclusion is unchanged by any of it.

Policy identity `JEPA_T0_V20_REPLAY_EQUIVALENCE_POLICY_V2`, digest
`0d08efd0b683f2565d2463aaba82d94bc2fd3ff3f39837c0199249827c076934`.
Artifact: `outputs/t0_sensitivity_recovery_v2final_20260910/T0_V20_RECOVERED_SENSITIVITY_STATISTICS_V2.json`.

## The numbers

The adjudication rule reaches `BROAD_IMMUNE_EXPRESSION_TARGET_SUPPORTED_INTERNAL`
only when the primary is positive at α = 0.025 **and** the composition
sensitivity and every measurement sensitivity are positive at
`sensitivity_directional_alpha` = 0.05. Until now the committed record showed
only the first of those three.

| model | β | HC3 SE | t | p_upper | n | residual df |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| primary (already published) | 124.945 | 65.489 | 1.9079 | 0.0210 | 18 | 13 |
| composition — nuisance + `IMMUNE_FRACTION` | 127.131 | 66.903 | 1.9002 | **0.0190** | 18 | 12 |
| measurement — nuisance + `Q_DEPTH` + `Q_DETECT` | 137.172 | 81.835 | 1.6762 | **0.0300** | 18 | 11 |

All three positive, all three inside their thresholds, 9,999 permutations each.
The terminal is now checkable against the numbers it was applied to rather than
taken on trust.

## Two things worth noticing, neither of which changes the result

**The measurement sensitivity is the weakest of the three.** p_upper = 0.030
against α = 0.05. It clears, and the frozen rule is a threshold rule, so the
terminal stands exactly as adjudicated. But a reader entitled to the primary's
p = 0.021 is also entitled to know the measurement-adjusted arm sits closer to
its boundary than either of the others.

**Its standard error is 25% larger than the primary's** — 81.835 against 65.489,
where the composition arm inflates by only 2.2%. That is consistent with the
Q_DEPTH/Q_DETECT collinearity measured earlier as a pathology-blind diagnostic
(Pearson r = 0.9232; each metric retaining roughly nine percent of its variance
once the other and the nuisance design are projected out; the design's condition
number rising from 310 to 37,671 when both are appended). That diagnostic
predicted inflated standard errors and therefore a *harder* test to pass, and
that is the direction observed. Consistent with, not proof of — one observation
does not establish the mechanism — but the prediction was made before these
numbers were visible and it held.

## Replay equivalence

Exact canonical input provenance matched at both call sites, so this compares
arithmetic on identical inputs. Thirteen target-fit fields, all PASS:

| field | rule | observed |
| --- | --- | --- |
| `beta` | tolerant array | max_rel 2.807e-12 |
| `sigma` | tolerant array | max_rel 8.221e-16 |
| `cv_mse_by_multiplier` | tolerant array | max_rel 2.585e-15 |
| `final_lambda` | ≤1 ULP | 1 ULP |
| `response_residual_sd` | ≤1 ULP | 1 ULP |
| `final_trace_scale` | ≤1 ULP *(the V2 change)* | 1 ULP |
| `mu`, `decision_gene_mask`, `multiplier_exponents`, `canonical_donor_order` | exact array | identical |
| `selected_multiplier_index`, `selected_multiplier_exponent`, `discovery_age_center` | exact scalar | identical |

Decision equivalence is stronger than the policy required. The tight 1e-12
relative rule on `state_primary` was never approached — β, HC3 SE and the
observed t all reproduced at **relative difference 0.000e+00**, bit for bit —
and both terminal strings matched exactly. So the last-bit drift in the target
fit did not propagate into the decision statistics at all. Reported as observed;
no mechanism is claimed for it here.

## Reproduced twice

The recovery was run twice: once materialising the confirmation matrix from the
verified block store, once from the cache that run produced. `state_primary`,
`state_composition`, `state_measurements` and both terminals are identical
across the two.

## What this does not do

- No V20 science conclusion, estimator, target, threshold, nuisance model,
  feature role, membership or adjudication rule changes.
- Reporting-only. `training_authorized: false`.
- The historical bit-exact `verify_target_v2_against_raw` is untouched, and zero
  frozen V20 files were modified.
- The V1 STOP artifact stands unchanged, and V1 remains the default policy.
- Only the stored **truncated** representation of `state_primary.null_t` is
  checked — five of 9,999 statistics with an elided middle. No full-null-array
  equality is claimed. The permutation count and every decision-relevant p-value
  are compared exactly.
- Reconstructing the original numeric stack remains open. V2 does not waive it;
  it makes the reporting recovery possible without it.

## Publication requirements

| # | requirement | where |
| --- | --- | --- |
| 1 | V1 STOP artifact unchanged | `outputs/t0_sensitivity_recovery_v2_20260910/…REPLAY_EQUIVALENCE_REPORT.json`, untouched since `5e8bee68` |
| 2 | exact V2 policy/implementation identity | `replay_equivalence_policy`, with digest and the single-authorized-change proof |
| 3 | complete target-fit results incl. abs/rel/ULP | `target_replay_equivalence.complete_field_reports`, both call sites |
| 4 | exact provenance result | `provenance_exact: true` |
| 5 | decision equivalence and terminal strings | `decision_replay_equivalence`, `terminals_exact: true` |
| 6 | numeric environment | Python 3.11.15, NumPy 2.4.6, SciPy 1.15.3, OpenBLAS 0.3.31.188.0 pthreads @ 16 threads, SIMD X86_V3 |
| 7 | sensitivities only if every gate passes | gated by `build_payload`; all gates passed |
| 8 | `training_authorized: false` | present |

Independent review is still required before this review policy is promoted into
project governance authority.
