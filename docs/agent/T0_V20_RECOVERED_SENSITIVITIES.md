# T0 V20: the recovered sensitivity statistics

Terminal: **PASS of the frozen V2 replay-equivalence gates** — a statement about
the replay, not a scientific verdict. Every gate cleared and the sensitivity
surfaces the committed decision omitted are recovered. No T0 V20 terminal
changes: the state terminal is the one already published, and the rare tail
remains `RARE_TAIL_UNDERDETERMINED_MEASUREMENT`.

**Scope, stated up front because the word PASS invites the wrong reading.** What
was recovered is the *state* composition and measurement sensitivities. Nothing
here bears on the rare-tail QC veto, which is a different test on different data
at a different level, and which this replay reproduced rather than challenged.
See "What this says about the rare tail" below.

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


## What this says about the rare tail: nothing, and it could not have

The recovered state sensitivities do not bear on the rare-tail QC veto. That is
settled by the frozen control flow, not by interpretation.

### The tail evidence was never computed

In `t0_adjudicator_v1.adjudicate_donor_table_non_authoritative`, `comp` and
`measurements` -- the state sensitivities -- are built at line 63, before any
tail logic. The QC gate sits at line 77:

```python
if not tail_preflight['qc_ok']:
    return {... 'tail_terminal':'RARE_TAIL_UNDERDETERMINED_MEASUREMENT',
            'tail_primary':None, 'tail_disease_test_run':False, ...}
```

Everything tail-specific -- `tail_donors`, `tail_primary`, `tail_comp`,
`tail_meas`, and the `decide_tail` call itself -- lives at lines 79-103,
downstream of that return. The run exits at 78 and never reaches any of it.

The replayed decision confirms this rather than leaving it to be inferred:
`tail_disease_test_run: false`, `tail_primary: null`, and no `tail_composition`,
`tail_measurements` or `tail_inference_donors` keys exist at all. There is no
tail measurement evidence in this run because none was produced.

### The veto is a different test from the state measurement sensitivity

The two share the names Q_DEPTH and Q_DETECT and nothing else.

| | state measurement sensitivity | tail QC veto |
| --- | --- | --- |
| level | donor (n = 18) | cell, within donor |
| data | donor-level pseudobulk summaries | every confirmation cell |
| question | is the AT8-state association explained by donor sequencing effort? | are the cells called "rare tail" selected in a QC-dependent way inside each donor? |
| statistic | HC3 t on AT8 ~ nuisance + state, with QC appended | max over the 2 metrics of the mean across donors of the absolute standardized tail-vs-rest contrast |
| null | 9,999 permutations | 999 within-donor reassignments of the tail label, hash-seeded per cell |
| result | p_upper = 0.030, clears alpha 0.05 | p_upper = 0.018, **vetoes** at alpha 0.05 |
| reads pathology | yes, AT8 | no, pathology-blind |

Clearing the first says nothing about the second. One asks whether a donor-level
association survives adjusting for donor-level QC; the other asks whether a
cell-level label is confounded with cell-level QC. A design can pass either and
fail the other.

### The veto reproduced exactly, and is not marginal

The entire `tail_preflight` object is **bit-identical** between the committed run
and this replay. The replay confirms the veto; it does not contest it.

```
max_mean_abs_standardized_qc_contrast : 0.2947
p_upper                               : 0.018   (999 replicates)
veto                                  : true    ->  qc_ok: false
```

With 999 replicates the test computes `p = (1 + ge)/1000`, so p = 0.018 means the
observed contrast was matched or exceeded by 17 of 1,000 null reassignments. For
the veto not to fire it would need 50 or more. It sits at rank 18 of 1,000 --
inside the veto region by a factor of about 2.8, not on a knife edge.

Worth reading alongside it: support and coherence both **passed**, and coherence
passed decisively -- `support_ok: true`, `coherence_ok: true`, mean pairwise
cosine 0.1042 with an exact sign-test p of 7.63e-06 over 131,072 configurations.
So the tail is not being called absent. It is coherent and supported, and blocked
specifically because the cells carrying it differ from their donor's other cells
in sequencing depth or detection more than chance allows. That is precisely what
`RARE_TAIL_UNDERDETERMINED_MEASUREMENT` is meant to say.

### So T0 stands where it stood

**Broad state supported, rare tail underdetermined.** The state arm is now fully
evidenced rather than partly asserted; the tail arm is unchanged, and cannot be
moved by any reporting or replay action.

### What would actually move the tail

None of these is a reporting or replay step, and each needs a new prospective
freeze and owner authorization:

1. **A tail definition that is not QC-confounded.** The veto is a property of the
   tail mask relative to the QC metrics. Changing how tail cells are called --
   depth-matched selection, or residualising the per-cell tail score on per-cell
   QC before thresholding -- attacks the cause. It is a change to the estimand.
2. **A QC-adjusted tail estimand** that carries the confound explicitly rather
   than attempting to be free of it.
3. **Deeper or more uniform data** for the confirmation donors, which would
   shrink the within-donor QC contrast on its own.

What would not be legitimate is relaxing `QC_ALPHA`, or reading the passing state
measurement sensitivity as evidence that the tail QC concern is unfounded. They
are different tests, and the frozen rule reaches `decide_tail` only through
`qc_ok`.

### One cheap diagnostic that is missing

The record stores the **max** across the two QC metrics but not which metric
attained it, nor the per-metric values. Knowing whether depth or detection drives
the 0.2947 would directly inform any remediation design, and it is computable
pathology-blind from confirmation cells already materialised. Not run here: it is
new analysis rather than part of this recovery.
