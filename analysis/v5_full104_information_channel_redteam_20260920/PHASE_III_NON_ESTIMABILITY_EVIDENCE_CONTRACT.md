# Phase III — non-estimability evidence contract

Date: 2026-09-21
Scope class: **`CURRENT_FULL104_RECONNAISSANCE`** (design + reference
implementation)
Determination: **contract proposed and tested. NO policy selected. The canonical
attacker is unchanged.**

```
BASE_SHA : ae5dc5c624fff341b8ef30c5359c55528383920a
```

This is a **prospective design**. It is deliberately not wired into the canonical
attacker, and nothing here is a retroactive filtering decision.

---

## 1. The defect being closed

```python
den = sqrt(max(rss_y, 0) * max(pred_ss, 0))
r   = 0.0 if den <= _EPS else cov / den
```

A term that is *mathematically undefined* becomes `r = 0`, hence `r² = 0` — the
**best attainable value**. Phase II measured the consequence on the authenticated
substrate: **30,451 of 1,773,512 held-out terms (1.7170%)**, affecting **39.01%**
of targets, with a wholly vacuous source guardrail for **202** targets.

## 2. The contract

A score term is a **tagged value**, not a float. Five states, none collapsible:

| state | meaning |
|---|---|
| `ESTIMABLE` | a finite correlation was computed |
| `TARGET_NON_VARIABLE` | `rss_y <= EPS`; the question could not be asked of this donor |
| `PREDICTION_NON_VARIABLE` | `pred_ss <= EPS`; the attacker produced nothing to correlate against |
| `MISSING` | the donor contributed no rows |
| `INVALID` | non-finite or otherwise unusable |

The two non-variable states are kept apart because they are **different
scientific failures**. Collapsing them would hide which one occurred.

**Representation.** Values and states travel together — `float64` values, `int8`
state codes. NaN alone is rejected as a representation: it cannot distinguish the
four non-estimable states from one another and propagates silently through most
reductions. Non-estimable values are `NaN` *and* carry their state; the state is
what is load-bearing.

**Serialization is part of the contract.** JSON and NPZ round-trips are tested,
and a test asserts that a non-estimable term serializes as `null` rather than
`0.0`, so no reader can mistake it for a measurement.

**Resampling carries states.** A bootstrap draw that happens to select only
undefined terms yields a non-estimable aggregate — not a zero, not a crash.

## 3. Aggregation fails closed

`aggregate()` **refuses** to return a number when non-estimable terms are present
unless a policy is named explicitly. There is **no default**.

That refusal is the entire point. The current defect is a silent default;
replacing it with a different silent default would not be an improvement.

## 4. Three policies, implemented and compared — none selected

### Structural consequences on the real authenticated geometry

No score was computed and no terminal outcome opened; these are counts over the
authenticated fold geometry.

| policy | what it discards | cost |
|---|---|---|
| **P1** `PROSPECTIVE_ELIGIBILITY` | whole targets with any undefined term | **6,653 targets excluded**; universe falls to **10,400 / 17,053 = 60.99%** |
| **P2** `ABSTAIN_AND_REWEIGHT` | individual undefined terms | **30,451 / 1,773,512 terms = 1.72%**; 98.28% retained |
| **P3** `REPORT_CONDITIONALITY` | nothing numerically | point estimate equals P2; what may be **claimed** is narrowed |

Retained term fraction by source under P2/P3:

| source | intended terms | abstaining | retained |
|---|---|---|---|
| HVS | 699,173 | 887 | 99.873% |
| NPH52 | 289,901 | 6,220 | 97.854% |
| SEA_AD | 784,438 | 23,344 | 97.024% |

Under P2/P3, **202 targets still have a wholly vacuous source** — abstention
does not rescue a source with no variable held-out donor at all.

### The choice is highly consequential

P1 discards **39% of the target universe**; P2/P3 discard **1.7% of terms**. That
is roughly a **23-fold** difference in how much evidence is set aside.

**No policy is selected here.** These numbers describe cost, not merit, and the
choice must not be made by observing which produces a preferred masking outcome.
Each is a different scientific position:

- **P1** keeps the estimand intact but changes the population the claim is about.
- **P2** keeps the population nominally intact but **changes the estimand** to a
  conditional mean over estimable donors.
- **P3** changes neither, and instead narrows what the result licenses.

P2 and P3 can coincide numerically while differing in what they permit to be
claimed. That is deliberate, is asserted by a test, and is the clearest
illustration that this is a **reporting** contract as much as an arithmetic one.

## 5. Controls

`tests/test_v5_score_term_evidence_contract_v1.py` — **19 tests, 0 skipped**,
organised around every way the collapse could still occur:

| risk | test |
|---|---|
| undefined becomes 0.0 at construction | `test_undefined_target_term_is_not_turned_into_zero` |
| two distinct failures merged | `test_target_and_prediction_failures_are_kept_distinct` |
| missing confused with non-variable | `test_missing_donor_is_distinct_from_non_variable` |
| a silent default policy | `test_aggregate_refuses_without_an_explicit_policy` |
| an arbitrary policy accepted | `test_unknown_policy_is_rejected` |
| states lost in JSON | `test_states_survive_json_round_trip` |
| zeros smuggled through JSON | `test_json_round_trip_does_not_smuggle_zeros` |
| states lost in NPZ | `test_states_survive_npz_round_trip` |
| states lost in resampling | `test_resampling_carries_states` |
| all-undefined resample scored | `test_resample_of_only_non_estimable_terms_is_non_estimable_not_zero` |
| a policy silently preferred | `test_compare_policies_reports_all_three_and_selects_none` |

One test is worth naming: `test_the_defect_would_have_produced_a_strictly_better_score`
constructs a fixture and asserts that the **current collapse scores strictly
cleaner** than any honest aggregate. That is the defect stated as an executable
assertion rather than an argument.

## 6. Red-team

| question | answer |
|---|---|
| Held-out data used to choose the method? | No. No score computed; the contract is a representation. |
| Reduced-pool or historical value promoted? | No. Consequences are counted over all 17,053 targets and all 4 authenticated folds. |
| Estimand silently changed? | **No — the opposite.** P2's estimand change is stated explicitly in its own note and asserted by test. |
| Undefined turned into zero? | The contract exists to prevent exactly this, and 11 tests check the boundaries where it could recur. |
| Population weighting where donor/source weighting intended? | Aggregation is group-balanced, matching the frozen two-level shape; the group axis is carried explicitly. |
| Cache with changed semantics reused? | Inputs came from the Phase I-qualified artifact. |
| Could the positive control pass with a wrong implementation? | No — the refusal test requires an exception, and the serialization tests require `null`, not a falsy number. |
| Threshold chosen after the result? | `EPS = 1e-12` is the frozen scorer's own constant. No new threshold exists. |
| Sealed information used? | No. |
| Second computation reproduces the headline? | The 30,451 / 1,773,512 figure was recomputed here from the C2 detail arrays, independently of the C2 summary JSON. |

## 7. What this establishes

A representation exists in which undefined, missing, invalid and measured-zero
score terms remain distinguishable through construction, aggregation,
serialization and bootstrap resampling — and in which producing a number from
non-estimable terms **requires naming a policy**.

The three candidate repairs are implemented, and their costs on the real geometry
differ by roughly 23×.

## 8. What this does NOT establish

- **No policy is chosen.** That is a scientific decision requiring its own
  justification, and it must not be made from masking outcomes.
- The contract is **not adopted** by the canonical attacker. Wiring it in is a
  separate, authorized change.
- Nothing here says the current masking verdict would change, or by how much.
- It does not address *why* targets are non-variable in particular donors — that
  is substrate biology and sparsity, not a representation question.

## 9. Status

```
EVIDENCE_CONTRACT_DESIGNED        = YES (reference implementation + 19 tests)
POLICY_SELECTED                   = NONE
CANONICAL_ATTACKER_CHANGED        = NO
ELIGIBILITY_SET_ALTERED           = NO
TERMINAL_MASKING_OUTCOMES         = UNOPENED
TRAINING_OFF
```

**Next dependent step:** Phase IV — production-aligned Audit B burden under the
real planning geometry, with a prospectively frozen target sample if exhaustive
execution is impractical.
