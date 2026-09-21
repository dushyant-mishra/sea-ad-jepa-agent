# Phase III — non-estimability evidence contract (V2)

Date: 2026-09-21
Scope class: **`CURRENT_FULL104_RECONNAISSANCE`** (design + reference
implementation)
Determination: **contract proposed and tested. NO terminal aggregation policy
selected. The canonical attacker is unchanged.**

```
BASE_SHA : ae5dc5c624fff341b8ef30c5359c55528383920a
```

> **V1 is superseded and removed.** Cross-review against an independently written
> GPT-lane contract found three real faults in V1, all confirmed empirically
> before this rewrite. They are recorded in §2 rather than quietly fixed, and
> each now has a regression test.

---

## 1. The defect being closed

```python
den = sqrt(max(rss_y, 0) * max(pred_ss, 0))
r   = 0.0 if den <= _EPS else cov / den
```

A term that is *mathematically undefined* becomes `r = 0`, hence `r² = 0` — the
**best attainable value**. Phase II measured it: **30,451 of 1,773,512 held-out
terms (1.7170%)**, affecting **39.01%** of targets, with a wholly vacuous source
guardrail for **202** targets.

## 2. What V1 got wrong

The two lanes agreed on the defect. They did **not** agree on safeguards, and the
diff is what found these:

| # | V1 fault | consequence | now |
|---|---|---|---|
| 1 | validated `ESTIMABLE ⇒ finite` but **never the inverse** | `ScoreTerms(values=[0.0], states=[TARGET_NON_VARIABLE])` was legal and serialized as the JSON number `0.0` — the exact collapse the contract forbids, reachable through the constructor *and* `from_json` | inverse invariant enforced at **every** entry point |
| 2 | claimed five irreducible states while mapping **six** conditions onto them | target took precedence when both target and prediction were non-variable; the prediction failure was erased | sixth state `TARGET_AND_PREDICTION_NON_VARIABLE` |
| 3 | no impossibility check | an `ESTIMABLE` term carrying `\|r\| = 1.7` was accepted | `\|r\| > 1` rejected; factory classifies as `INVALID_NUMERIC` |

Fault 1 is the serious one: the contract's central promise was reachable-around.
Each now has a regression test named for it.

**What each lane contributed.** This lane: fail-closed aggregation with no default
policy, policy-consequence comparison, JSON/NPZ round trips, state-carrying
resampling, group-balanced aggregation. GPT lane: the joint failure state, the
NaN invariant, the impossibility check, a content digest over scientific state,
immutable arrays. V2 is the union.

## 3. The contract

Six states, each irreducible:

| state | meaning |
|---|---|
| `ESTIMABLE` | a finite, admissible correlation |
| `TARGET_NON_VARIABLE` | `rss_y <= EPS`; the question could not be asked of this donor |
| `PREDICTION_NON_VARIABLE` | `pred_ss <= EPS`; the attacker produced nothing to correlate against |
| `TARGET_AND_PREDICTION_NON_VARIABLE` | both; neither failure may be erased |
| `MISSING` | the donor contributed no rows |
| `INVALID_NUMERIC` | non-finite, or `\|r\| > 1` |

**Invariants, enforced at every entry point** — constructor, both deserializers,
resampling — through a single validation routine:

* `ESTIMABLE` ⇒ finite and `|value| <= 1 + 1e-9`;
* **every** non-estimable term carries `NaN`, no exception;
* state codes known; arrays aligned, 1-D, **read-only** after validation.

A **content digest** over the scientific state makes tampering detectable, and a
smuggled zero changes the digest. Round trips through JSON and NPZ verify it.

## 4. Aggregation fails closed

`aggregate()` refuses to return a number when non-estimable terms are present
unless a policy is named. There is **no default**, because the defect being
repaired *is* a silent default.

## 5. Four policies — consequences on the real authenticated geometry

No score was computed and no terminal outcome opened. These are counts over the
authenticated fold geometry: 17,053 targets × 4 folds = 68,212 target-folds, and
1,773,512 held-out score terms.

| policy | universe kept | evidence discarded | vacuous guardrails still scored |
|---|---|---|---|
| **P1** prospective eligibility | **10,400 / 17,053 (60.99%)** | 6,653 targets | 0 |
| **P2** abstain + reweight | 17,053 | 30,451 terms (1.72%) | **202 targets / 531 guardrails** |
| **P3** conditional + mandatory coverage | 17,053 | same as P2 | **202 / 531** |
| **P4** coverage-guarded conditional | **17,053 (100%)** | **531 / 68,212 target-folds (0.78%)** | **0** |

### What that comparison shows

- **P1** eliminates the vacuous-guardrail problem but discards **39% of the
  scientific universe**, leaving a population selected toward ubiquitously
  variable targets.
- **P2** is cheap in terms but **changes the estimand** *and* still scores all
  531 vacuous guardrails — the worst failure survives.
- **P3** adds reporting discipline but, by itself, also does not stop a vacuous
  guardrail being scored.
- **P4** preserves the entire universe while refusing to score exactly the cases
  that cannot be scored: **0.78% of target-folds**, eliminating **100%** of the
  vacuous guardrails.

**No terminal policy is selected here.** These figures describe cost and
coverage, not merit, and the choice must not be made by observing which produces
a preferred masking outcome.

## 6. P3 semantics, corrected

V1 claimed P3 left "the estimand unchanged" while computing the point estimate on
the estimable subset. That was incoherent — a number computed on a subset does
not estimate the whole. V2 states it properly, and a test enforces it:

```
full intended estimand      = NOT point-estimated
conditional statistic       = reportable
coverage / conditionality   = mandatory
```

`full_estimand_point_estimated` is `False` for P1, P2, P3 **and** P4 whenever any
term is non-estimable. The quantity every non-P1 policy reports is named
explicitly: **"conditional predictability among estimable donors"**. None of them
may be described as estimating the unconditional all-donor quantity.

## 7. The P4 rule, stated prospectively

For each target × fold × source:

1. score only mathematically `ESTIMABLE` donors;
2. preserve the intended 17,053-target universe;
3. report donor coverage explicitly;
4. if a required source has **zero** estimable donors →
   `SOURCE_GUARDRAIL = NOT_ESTIMABLE`; **never PASS, never numeric zero**;
5. name the quantity "conditional predictability among estimable donors";
6. never claim it estimates the unconditional all-donor quantity;
7. carry coverage through every bootstrap/resample.

All seven are implemented and tested. Property 4 is the coverage guard, and
`test_p4_refuses_when_a_required_group_has_no_estimable_donor` pins it against
P2, which still returns a number in the same situation.

## 8. Controls

`tests/test_v5_score_term_evidence_contract_v2.py` — **30 tests, 0 skipped**.

Three are **V1 regressions**, named for the faults they re-check:
`test_non_estimable_term_may_not_carry_a_finite_value`,
`test_joint_target_and_prediction_failure_is_its_own_state`,
`test_impossible_correlation_is_rejected`.

Others cover: immutability; the digest changing when a state changes; a tampered
digest rejected; a **hand-edited JSON payload attaching a number to an undefined
term** rejected at deserialization; unknown state names and foreign schemas
rejected; resampling carrying states and coverage; an all-undefined resample
scoring `None` under every policy; and `test_the_defect_would_have_produced_a_strictly_better_score`,
which asserts the current collapse scores **strictly cleaner** than any honest
aggregate — the defect as an executable assertion rather than an argument.

A fixture error was found and fixed during this work: `_mixed()` originally left
group 1 with *zero* estimable terms, so P4 correctly refused and three tests
failed. The guard was right and the fixture was not genuinely mixed; the fixture
was corrected rather than the guard weakened.

## 9. Red-team

| question | answer |
|---|---|
| Held-out data used to choose the method? | No. No score computed. |
| Reduced-pool or historical value promoted? | No. Consequences counted over all 17,053 targets and all 4 authenticated folds. |
| Estimand silently changed? | **No — the opposite.** Every policy's estimand status is an explicit field, and no policy claims to point-estimate the full estimand. |
| Undefined turned into zero? | The contract exists to prevent it, and the V1 fault that allowed it is now a named regression test. |
| Population weighting where donor/source weighting intended? | Aggregation is group-balanced; the group axis is carried explicitly. |
| Cache with changed semantics reused? | Inputs came from the Phase I-qualified artifact. |
| Could the positive control pass with a wrong implementation? | No — V1 *did* pass its own positive controls while carrying three faults. That is precisely why the cross-lane diff was necessary and why the faults are now regressions. |
| Threshold chosen after the result? | `EPS = 1e-12` is the frozen scorer's own constant. `CORRELATION_TOL = 1e-9` is a floating-point admissibility bound, declared before use. |
| Sealed information used? | No. |
| Second computation reproduces the headline? | The 30,451 / 1,773,512 and 531 / 68,212 figures were recomputed from the C2 detail arrays, independently of the C2 summary JSON. |

## 10. What this establishes / does not establish

**Establishes.** A representation in which six distinct term states survive
construction, aggregation, serialization, digesting and bootstrap resampling; in
which producing a number from non-estimable terms requires naming a policy; and
in which one candidate rule (P4) eliminates all 531 vacuous guardrails at a cost
of 0.78% of target-folds while preserving the full target universe.

**Does not establish.** No terminal policy is chosen. The contract is not adopted
by the canonical attacker — wiring it in is a separate authorized change. Nothing
here says whether or how much a masking verdict would change. And it does not
address *why* targets are non-variable in particular donors, which is substrate
sparsity, not a representation question.

## 11. Status

```
EVIDENCE_CONTRACT_DESIGNED   = YES (V2 reference implementation + 30 tests)
V1                           = SUPERSEDED_AND_REMOVED (3 confirmed faults)
TERMINAL_POLICY_SELECTED     = NONE
CANONICAL_ATTACKER_CHANGED   = NO
ELIGIBILITY_SET_ALTERED      = NO
TERMINAL_MASKING_OUTCOMES    = UNOPENED
TRAINING_OFF
```
